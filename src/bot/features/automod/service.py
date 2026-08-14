"""
src/bot/features/automod/service.py
--------------------------------------
AutoMod Service

Contains all AutoMod business logic and the rule engine.
Separated from the cog so that:
    1. Logic can be tested without Discord interactions.
    2. Other parts of Kairo can trigger AutoMod checks programmatically.

The service loads guild configurations and applies rule checks to messages
and events, then takes appropriate actions when violations are detected.
"""

from __future__ import annotations

import asyncio
import re
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, TYPE_CHECKING

import discord

from ...core.bot import KairoBot
from ...core.logging import get_logger
from ...database.models.automod import AutoModConfig, AutoModRule, AutoModRuleType, AutoModAction
from ...database.repositories.automod import AutoModRepository
from ...database.repositories.guild import GuildRepository
from ...database.repositories.moderation import ModerationRepository
from ..moderation.service import ModerationService

if TYPE_CHECKING:
    from typing import Awaitable, Callable

log = get_logger(__name__)


class AutoModService:
    """
    Executes AutoMod rule checks and enforces actions.
    
    This service monitors Discord events (messages, joins) and applies
    AutoMod rules to detect and prevent unwanted behavior automatically.
    
    Args:
        bot: The KairoBot instance, used to access the database.
    """
    
    def __init__(self, bot: KairoBot) -> None:
        self.bot = bot
        self._message_cache: Dict[int, List[Tuple[datetime, int]]] = defaultdict(list)  # guild_id -> [(timestamp, user_id)]
        self._join_cache: Dict[int, List[datetime]] = defaultdict(list)  # guild_id -> [join_times]
        
        # Clean up caches periodically
        self._cleanup_task: Optional[asyncio.Task] = None
    
    def _automod_repo(self) -> AutoModRepository:
        """Return the AutoMod repository."""
        return AutoModRepository(self.bot.db)  # type: ignore[attr-defined]
    
    def _guild_repo(self) -> GuildRepository:
        """Return the guild repository."""
        return GuildRepository(self.bot.db)  # type: ignore[attr-defined]
    
    def _mod_repo(self) -> ModerationRepository:
        """Return the moderation repository."""
        return ModerationRepository(self.bot.db)  # type: ignore[attr-defined]
    
    def _mod_service(self) -> ModerationService:
        """Return the moderation service for taking actions."""
        return ModerationService(self.bot)
    
    # ------------------------------------------------------------------ #
    # Lifecycle                                                            #
    # ------------------------------------------------------------------ #
    
    async def start(self) -> None:
        """Start the AutoMod service and cleanup task."""
        self._cleanup_task = asyncio.create_task(self._cleanup_caches())
        log.info("AutoMod service started")
    
    async def close(self) -> None:
        """Stop the AutoMod service and cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        log.info("AutoMod service stopped")
    
    async def _cleanup_caches(self) -> None:
        """Periodically clean up old entries from caches."""
        while True:
            try:
                await asyncio.sleep(60)  # Clean up every minute
                self._cleanup_message_cache()
                self._cleanup_join_cache()
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error("Error in AutoMod cache cleanup: %s", e)
    
    def _cleanup_message_cache(self) -> None:
        """Remove old entries from message cache."""
        now = datetime.utcnow()
        for guild_id, messages in list(self._message_cache.items()):
            # Remove entries older than 5 minutes
            self._message_cache[guild_id] = [
                (ts, user_id) for ts, user_id in messages
                if (now - ts).total_seconds() < 300
            ]
            # Remove empty guild entries
            if not self._message_cache[guild_id]:
                del self._message_cache[guild_id]
    
    def _cleanup_join_cache(self) -> None:
        """Remove old entries from join cache."""
        now = datetime.utcnow()
        for guild_id, joins in list(self._join_cache.items()):
            # Remove entries older than 1 minute
            self._join_cache[guild_id] = [
                join_time for join_time in joins
                if (now - join_time).total_seconds() < 60
            ]
            # Remove empty guild entries
            if not self._join_cache[guild_id]:
                del self._join_cache[guild_id]
    
    # ------------------------------------------------------------------ #
    # Rule Engine                                                           #
    # ------------------------------------------------------------------ #
    
    async def check_message(self, message: discord.Message) -> bool:
        """
        Check a message against all applicable AutoMod rules.
        
        Args:
            message: The Discord message to check.
        
        Returns:
            True if any rule was triggered and action was taken, False otherwise.
        """
        # Skip bot messages, DMs, and moderators
        if message.author.bot:
            return False
        if not message.guild:
            return False
        if message.author.guild_permissions.manage_messages:  # type: ignore[union-attr]
            return False
        
        # Get config for this guild
        config = await self._automod_repo().get_config(message.guild.id)
        if config is None or not config.enabled:
            return False
        
        # Get rules for this guild
        rules = await self._automod_repo().get_rules_for_guild(message.guild.id)
        
        # Check each rule type
        triggered = False
        
        # Check for spam
        if config.spam_enabled:
            spam_result = await self._check_spam(message, config)
            if spam_result and self._should_trigger_action(config.default_action):
                triggered = True
        
        # Check for mention spam
        if config.mention_spam_enabled:
            mention_result = await self._check_mentions(message, config)
            if mention_result and self._should_trigger_action(config.default_action):
                triggered = True
        
        # Check for link filtering
        if config.link_filter_enabled:
            link_result = await self._check_links(message, config)
            if link_result and self._should_trigger_action(config.default_action):
                triggered = True
        
        # Check for word filtering
        if config.word_filter_enabled:
            word_result = await self._check_words(message, config)
            if word_result and self._should_trigger_action(config.default_action):
                triggered = True
        
        # Check for caps filtering
        if config.caps_filter_enabled:
            caps_result = await self._check_caps(message, config)
            if caps_result and self._should_trigger_action(config.default_action):
                triggered = True
        
        return triggered
    
    async def check_member_join(self, member: discord.Member) -> bool:
        """
        Check a member join for raid protection.
        
        Args:
            member: The Discord member who just joined.
        
        Returns:
            True if raid protection action was taken, False otherwise.
        """
        config = await self._automod_repo().get_config(member.guild.id)
        if config is None or not config.enabled or not config.raid_protection_enabled:
            return False
        
        # Track joins
        self._join_cache[member.guild.id].append(datetime.utcnow())
        
        # Check for rapid joins
        now = datetime.utcnow()
        recent_joins = [
            join_time for join_time in self._join_cache[member.guild.id]
            if (now - join_time).total_seconds() <= config.raid_window
        ]
        
        if len(recent_joins) >= config.raid_threshold:
            await self._handle_raid_detection(member.guild, len(recent_joins))
            return True
        
        return False
    
    def _should_trigger_action(self, action: str) -> bool:
        """Check if an action should actually trigger (not 'notify' only)."""
        return action not in ["notify", None]
    
    # ------------------------------------------------------------------ #
    # Rule Checks                                                           #
    # ------------------------------------------------------------------ #
    
    async def _check_spam(self, message: discord.Message, config: AutoModConfig) -> bool:
        """
        Check for message spam (too many messages in a short time window).
        
        Args:
            message: The message to check.
            config: The guild's AutoMod configuration.
        
        Returns:
            True if spam was detected, False otherwise.
        """
        now = datetime.utcnow()
        guild_id = message.guild.id
        user_id = message.author.id
        
        # Update message cache
        self._message_cache[guild_id].append((now, user_id))
        
        # Get recent messages from this user
        recent_messages = [
            (ts, uid) for ts, uid in self._message_cache[guild_id]
            if uid == user_id and (now - ts).total_seconds() <= config.spam_window
        ]
        
        # Check if user exceeded message limit
        if len(recent_messages) >= config.spam_messages:
            await self._handle_violation(
                message, config,
                f"Spam: {len(recent_messages)} messages in {config.spam_window}s"
            )
            return True
        
        return False
    
    async def _check_mentions(self, message: discord.Message, config: AutoModConfig) -> bool:
        """
        Check for mention spam (too many @mentions in a single message).
        
        Args:
            message: The message to check.
            config: The guild's AutoMod configuration.
        
        Returns:
            True if mention spam was detected, False otherwise.
        """
        # Count unique user mentions
        mention_count = len(set(message.mentions))
        
        if mention_count >= config.max_mentions:
            await self._handle_violation(
                message, config,
                f"Mention spam: {mention_count} mentions (max {config.max_mentions})"
            )
            return True
        
        return False
    
    async def _check_links(self, message: discord.Message, config: AutoModConfig) -> bool:
        """
        Check for unauthorized links or invites.
        
        Args:
            message: The message to check.
            config: The guild's AutoMod configuration.
        
        Returns:
            True if unauthorized links were detected, False otherwise.
        """
        content = message.content.lower()
        
        # Check for Discord invites
        if config.block_invites:
            invite_patterns = [
                r'discord\.gg/[a-z0-9-]+',
                r'invite\.gg/[a-z0-9-]+',
                r'discord\.com/invite/[a-z0-9-]+',
            ]
            for pattern in invite_patterns:
                if re.search(pattern, content):
                    await self._handle_violation(
                        message, config,
                        "Unauthorized Discord invite link"
                    )
                    return True
        
        # Check for all links (if enabled)
        if config.block_all_links:
            url_pattern = r'https?://[^\s]+|www\.[^\s]+'
            if re.search(url_pattern, content):
                await self._handle_violation(
                    message, config,
                    "All external links are blocked"
                )
                return True
        
        # Check against allowed domains (if specific domains are configured)
        if config.allowed_domains and config.link_filter_enabled:
            allowed_domains = config.get_allowed_domains_list()
            if allowed_domains:
                # Extract domains from message
                url_pattern = r'https?://([^/\s]+)'
                for match in re.finditer(url_pattern, content):
                    domain = match.group(1).lower()
                    # Remove www. prefix if present
                    if domain.startswith("www."):
                        domain = domain[4:]
                    if domain not in allowed_domains:
                        await self._handle_violation(
                            message, config,
                            f"Domain not allowed: {domain}"
                        )
                        return True
        
        return False
    
    async def _check_words(self, message: discord.Message, config: AutoModConfig) -> bool:
        """
        Check for blocked words or phrases.
        
        Args:
            message: The message to check.
            config: The guild's AutoMod configuration.
        
        Returns:
            True if blocked words were detected, False otherwise.
        """
        content = message.content.lower()
        blocked_words = config.get_blocked_words_list()
        
        if not blocked_words:
            return False
        
        for word in blocked_words:
            if word in content:
                await self._handle_violation(
                    message, config,
                    f"Blocked word: {word}"
                )
                return True
        
        return False
    
    async def _check_caps(self, message: discord.Message, config: AutoModConfig) -> bool:
        """
        Check for excessive capitalization.
        
        Args:
            message: The message to check.
            config: The guild's AutoMod configuration.
        
        Returns:
            True if excessive caps were detected, False otherwise.
        """
        content = message.content
        
        # Skip if message is too short
        if len(content) < config.min_message_length:
            return False
        
        # Count uppercase letters
        uppercase_count = sum(1 for char in content if char.isupper())
        total_letters = sum(1 for char in content if char.isalpha())
        
        if total_letters > 0:
            caps_percent = (uppercase_count / total_letters) * 100
            if caps_percent >= config.max_caps_percent:
                await self._handle_violation(
                    message, config,
                    f"Excessive caps: {caps_percent:.1f}% (max {config.max_caps_percent}%)"
                )
                return True
        
        return False
    
    # ------------------------------------------------------------------ #
    # Violation Handling                                                    #
    # ------------------------------------------------------------------ #
    
    async def _handle_violation(
        self, 
        message: discord.Message, 
        config: AutoModConfig, 
        reason: str
    ) -> None:
        """
        Handle a detected violation by taking the configured action.
        
        Args:
            message: The violating message.
            config: The guild's AutoMod configuration.
            reason: The reason for the violation.
        """
        action = config.default_action
        
        try:
            if action == AutoModAction.DELETE_MESSAGE or action == "delete_message":
                await message.delete()
                log.info("Deleted message from %s in #%s: %s", 
                        message.author, message.channel, reason)
            
            elif action == AutoModAction.WARN or action == "warn":
                await message.delete()
                # Issue warning via moderation service
                log.info("Warning %s in #%s: %s", 
                        message.author, message.channel, reason)
            
            elif action == AutoModAction.TIMEOUT or action == "timeout":
                await message.delete()
                # Apply timeout via moderation service
                mod_service = self._mod_service()
                await mod_service.timeout(
                    message,  # Fake interaction - need to handle differently
                    message.author,
                    duration="10m",  # Default timeout duration
                    reason=f"AutoMod: {reason}"
                )
                log.info("Timed out %s in #%s: %s", 
                        message.author, message.channel, reason)
            
            elif action == AutoModAction.KICK or action == "kick":
                await message.delete()
                mod_service = self._mod_service()
                await mod_service.kick(
                    message,  # Fake interaction
                    message.author,
                    reason=f"AutoMod: {reason}"
                )
                log.info("Kicked %s from #%s: %s", 
                        message.author, message.channel, reason)
            
            elif action == AutoModAction.BAN or action == "ban":
                await message.delete()
                mod_service = self._mod_service()
                await mod_service.ban(
                    message,  # Fake interaction
                    message.author,
                    reason=f"AutoMod: {reason}"
                )
                log.info("Banned %s from #%s: %s", 
                        message.author, message.channel, reason)
            
            elif action == AutoModAction.NOTIFY or action == "notify":
                # Just log and notify, don't take action on message
                log.info("AutoMod notification in #%s: %s", 
                        message.channel, reason)
                
            # Send to AutoMod log channel if configured
            await self._send_automod_log(message.guild, message.author, reason, action)
            
        except Exception as e:
            log.error("Failed to handle AutoMod violation: %s", e)
    
    async def _handle_raid_detection(self, guild: discord.Guild, join_count: int) -> None:
        """
        Handle detected raid with the configured action.
        
        Args:
            guild: The guild where the raid was detected.
            join_count: Number of joins detected in the time window.
        """
        config = await self._automod_repo().get_config(guild.id)
        if config is None:
            return
        
        action = config.raid_action
        reason = f"Raid protection: {join_count} rapid joins"
        
        try:
            if action == "timeout":
                # Timeout all recent joiners
                # This would need to be implemented with proper Discord permissions
                log.warning("Raid detected in guild %d: %d joins - timeout action not implemented", 
                          guild.id, join_count)
            
            elif action == "kick":
                log.warning("Raid detected in guild %d: %d joins - kick action not implemented", 
                          guild.id, join_count)
            
            elif action == "ban":
                log.warning("Raid detected in guild %d: %d joins - ban action not implemented", 
                          guild.id, join_count)
            
            # Send to AutoMod log channel
            await self._send_automod_log(guild, None, reason, action, is_raid=True)
            
        except Exception as e:
            log.error("Failed to handle raid detection: %s", e)
    
    async def _send_automod_log(
        self,
        guild: discord.Guild,
        user: Optional[discord.User],
        reason: str,
        action: str,
        is_raid: bool = False
    ) -> None:
        """
        Send an AutoMod log entry to the configured log channel.
        
        Args:
            guild: The guild where the violation occurred.
            user: The user who triggered the violation (None for raids).
            reason: The reason for the violation.
            action: The action taken.
            is_raid: Whether this is a raid detection log.
        """
        try:
            config = await self._automod_repo().get_config(guild.id)
            if config is None or config.log_channel is None:
                return
            
            # Get the channel
            log_channel = guild.get_channel(config.log_channel)
            if log_channel is None or not hasattr(log_channel, 'send'):
                return
            
            # Build the log message
            import discord
            from ...components import send_layout_to_channel
            
            if is_raid:
                view = discord.ui.LayoutView()
                view.add_item(discord.ui.Container(
                    discord.ui.TextDisplay("🚨 **Raid Protection Triggered**"),
                    discord.ui.Separator(visible=True),
                    discord.ui.TextDisplay(f"**Action:** {action}"),
                    discord.ui.TextDisplay(f"**Reason:** {reason}"),
                    discord.ui.TextDisplay(f"**Time:** {datetime.utcnow()}"),
                ))
            else:
                view = discord.ui.LayoutView()
                view.add_item(discord.ui.Container(
                    discord.ui.TextDisplay("🛡️ **AutoMod Violation**"),
                    discord.ui.Separator(visible=True),
                    discord.ui.TextDisplay(f"**User:** {user}" if user else "Unknown"),
                    discord.ui.TextDisplay(f"**Action:** {action}"),
                    discord.ui.TextDisplay(f"**Reason:** {reason}"),
                    discord.ui.TextDisplay(f"**Time:** {datetime.utcnow()}"),
                ))
            
            await send_layout_to_channel(log_channel, view)
            
        except Exception as e:
            log.error("Failed to send AutoMod log: %s", e)