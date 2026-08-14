"""
src/bot/features/moderation/service.py
-----------------------------------------
Moderation Service

Contains all moderation business logic. Separated from the cog so that:
    1. Logic can be tested without Discord interactions.
    2. Other parts of Kairo (e.g. automod) can trigger moderation actions
       programmatically without going through a slash command.

The service applies the Discord action, records a ModerationCase,
and sends a response using discord.ui.LayoutView (Components V2).
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Optional

import discord

from ...core.bot import KairoBot
from ...core.logging import get_logger
from ...database.models.moderation import CaseType
from ...database.repositories.moderation import ModerationRepository
from ...database.repositories.user import UserRepository
from ...database.repositories.guild import GuildRepository
from ...components import send_layout, send_layout_to_channel

log = get_logger(__name__)

# Duration string regex: e.g. "10m", "2h", "1d", "30s"
_DURATION_RE = re.compile(r"^(\d+)(s|m|h|d|w)$", re.IGNORECASE)
_DURATION_MAP = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}


def _parse_duration(duration_str: str) -> Optional[int]:
    """
    Parse a human-readable duration string into seconds.

    Args:
        duration_str: Duration string like "10m", "2h", "1d".

    Returns:
        Duration in seconds, or None if the string is invalid.
    """
    match = _DURATION_RE.match(duration_str.strip())
    if not match:
        return None
    amount, unit = int(match.group(1)), match.group(2).lower()
    return amount * _DURATION_MAP[unit]


def _result_view(text: str) -> discord.ui.LayoutView:
    """Build a simple single-container LayoutView for a moderation result."""
    view = discord.ui.LayoutView()
    view.add_item(discord.ui.Container(discord.ui.TextDisplay(text)))
    return view


class ModerationService:
    """
    Executes moderation actions and records them in the database.

    Args:
        bot: The KairoBot instance, used to access the database.
    """

    def __init__(self, bot: KairoBot) -> None:
        self.bot = bot
        # Repositories are created per-call once the database is attached to the bot.
        # TODO: Attach db to bot and inject repositories in Phase 2.

    def _mod_repo(self) -> ModerationRepository:
        """Return the moderation repository. Requires db to be attached to bot."""
        return ModerationRepository(self.bot.db)  # type: ignore[attr-defined]

    def _user_repo(self) -> UserRepository:
        """Return the user repository."""
        return UserRepository(self.bot.db)  # type: ignore[attr-defined]

    def _guild_repo(self) -> GuildRepository:
        """Return the guild repository."""
        return GuildRepository(self.bot.db)  # type: ignore[attr-defined]

    # ------------------------------------------------------------------ #
    # Actions                                                              #
    # ------------------------------------------------------------------ #

    async def ban(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: Optional[str] = None,
        delete_days: int = 0,
    ) -> None:
        """
        Ban a member and record a case.

        Args:
            interaction: The slash command interaction.
            member:      The member to ban.
            reason:      Optional ban reason.
            delete_days: Days of messages to delete (0–7).
        """
        assert interaction.guild is not None
        try:
            await member.ban(reason=reason, delete_message_days=delete_days)
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I do not have permission to ban that member.",
                ephemeral=True,
            )
            return
        except discord.HTTPException as e:
            log.error("Ban failed for %s: %s", member, e)
            await interaction.response.send_message(
                "❌ An error occurred while trying to ban that member.",
                ephemeral=True,
            )
            return

        # TODO: Record case in database once db is wired up (Phase 2).

        # Record case in database
        case = await self._mod_repo().create_case(
            guild_id=interaction.guild.id,
            target_id=member.id,
            target_username=str(member),
            moderator_id=interaction.user.id,
            moderator_username=str(interaction.user),
            case_type=CaseType.BAN,
            reason=reason,
            resolved=False,
        )

        view = _result_view(
            f"✅ **{member}** has been banned.\n"
            f"**Case:** #{case.id}\n"
            f"**Reason:** {reason or 'No reason provided.'}"
        )
        await send_layout(interaction, view, ephemeral=True)
        
        # Send to mod log channel
        await self._send_mod_log(interaction.guild, case, member)
        
        log.info("Banned %s from guild %d (%s) - Case #%d", member, interaction.guild.id, reason, case.id)

    async def kick(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: Optional[str] = None,
    ) -> None:
        """Kick a member and record a case."""
        assert interaction.guild is not None
        try:
            await member.kick(reason=reason)
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I do not have permission to kick that member.",
                ephemeral=True,
            )
            return

        # Record case in database
        case = await self._mod_repo().create_case(
            guild_id=interaction.guild.id,
            target_id=member.id,
            target_username=str(member),
            moderator_id=interaction.user.id,
            moderator_username=str(interaction.user),
            case_type=CaseType.KICK,
            reason=reason,
            resolved=False,
        )

        view = _result_view(
            f"✅ **{member}** has been kicked.\n"
            f"**Case:** #{case.id}\n"
            f"**Reason:** {reason or 'No reason provided.'}"
        )
        await send_layout(interaction, view, ephemeral=True)
        
        # Send to mod log channel
        await self._send_mod_log(interaction.guild, case, member)
        
        log.info("Kicked %s from guild %d (%s) - Case #%d", member, interaction.guild.id, reason, case.id)

    async def timeout(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        duration: str,
        reason: Optional[str] = None,
    ) -> None:
        """Apply a timeout to a member and record a case."""
        assert interaction.guild is not None
        seconds = _parse_duration(duration)
        if not seconds:
            await interaction.response.send_message(
                "❌ Invalid duration. Use formats like `10m`, `2h`, `1d`.",
                ephemeral=True,
            )
            return

        until = datetime.now(timezone.utc) + timedelta(seconds=seconds)
        try:
            await member.timeout(until, reason=reason)
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I do not have permission to timeout that member.",
                ephemeral=True,
            )
            return

        # Record case in database
        case = await self._mod_repo().create_case(
            guild_id=interaction.guild.id,
            target_id=member.id,
            target_username=str(member),
            moderator_id=interaction.user.id,
            moderator_username=str(interaction.user),
            case_type=CaseType.TIMEOUT,
            reason=reason,
            duration=seconds,
            resolved=False,
        )

        view = _result_view(
            f"✅ **{member}** has been timed out for **{duration}**.\n"
            f"**Case:** #{case.id}\n"
            f"**Reason:** {reason or 'No reason provided.'}"
        )
        await send_layout(interaction, view, ephemeral=True)
        
        # Send to mod log channel
        await self._send_mod_log(interaction.guild, case, member)
        
        log.info("Timed out %s for %ds in guild %d (%s) - Case #%d", member, seconds, interaction.guild.id, reason, case.id)

    async def warn(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: Optional[str] = None,
    ) -> None:
        """Issue a warning to a member and record a case + warning entry."""
        assert interaction.guild is not None

        # Record case in database
        case = await self._mod_repo().create_case(
            guild_id=interaction.guild.id,
            target_id=member.id,
            target_username=str(member),
            moderator_id=interaction.user.id,
            moderator_username=str(interaction.user),
            case_type=CaseType.WARN,
            reason=reason,
            resolved=False,
        )
        
        # Create warning entry
        await self._mod_repo().create_warning(case)

        view = _result_view(
            f"⚠️ **{member}** has been warned.\n"
            f"**Case:** #{case.id}\n"
            f"**Reason:** {reason or 'No reason provided.'}"
        )
        await send_layout(interaction, view, ephemeral=True)
        
        # Send to mod log channel
        await self._send_mod_log(interaction.guild, case, member)
        
        log.info("Warned %s in guild %d (%s) - Case #%d", member, interaction.guild.id, reason, case.id)

    async def show_history(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
    ) -> None:
        """Display a member's moderation history."""
        assert interaction.guild is not None
        
        # Get cases for this user
        cases = await self._mod_repo().get_cases_for_user(
            guild_id=interaction.guild.id,
            user_id=member.id
        )
        
        if not cases:
            view = discord.ui.LayoutView()
            view.add_item(discord.ui.Container(
                discord.ui.TextDisplay(f"## Moderation History — {member}"),
                discord.ui.Separator(visible=True),
                discord.ui.TextDisplay("*No moderation history found.*"),
            ))
            await send_layout(interaction, view, ephemeral=True)
            return
        
        # Build pages for pagination
        pages = []
        for case in cases:
            case_container = discord.ui.Container(
                discord.ui.TextDisplay(f"### Case #{case.id}"),
                discord.ui.TextDisplay(f"**Type:** {case.case_type}"),
                discord.ui.TextDisplay(f"**Target:** {case.target_username}"),
                discord.ui.TextDisplay(f"**Moderator:** {case.moderator_username}"),
                discord.ui.TextDisplay(f"**Reason:** {case.reason or 'No reason provided.'}"),
                discord.ui.TextDisplay(f"**Created:** {case.created_at}"),
                discord.ui.Separator(visible=True),
            )
            pages.append(case_container)
        
        # Create pagination view
        from ...components import Paginator
        view = Paginator(pages, ephemeral=True)
        await send_layout(interaction, view, ephemeral=True)

    async def show_case(
        self,
        interaction: discord.Interaction,
        case_id: int,
    ) -> None:
        """Display a specific moderation case."""
        assert interaction.guild is not None
        
        # Get the case by ID
        case = await self._mod_repo().get_case(case_id, interaction.guild.id)
        
        if case is None:
            view = discord.ui.LayoutView()
            view.add_item(discord.ui.Container(
                discord.ui.TextDisplay(f"## Case #{case_id}"),
                discord.ui.Separator(visible=True),
                discord.ui.TextDisplay("*Case not found.*"),
            ))
            await send_layout(interaction, view, ephemeral=True)
            return
        
        view = discord.ui.LayoutView()
        view.add_item(discord.ui.Container(
            discord.ui.TextDisplay(f"## Case #{case.id}"),
            discord.ui.Separator(visible=True),
            discord.ui.TextDisplay(f"**Type:** {case.case_type}"),
            discord.ui.TextDisplay(f"**Target:** {case.target_username} ({case.target_id})"),
            discord.ui.TextDisplay(f"**Moderator:** {case.moderator_username} ({case.moderator_id})"),
            discord.ui.TextDisplay(f"**Reason:** {case.reason or 'No reason provided.'}"),
            discord.ui.TextDisplay(f"**Created:** {case.created_at}"),
            discord.ui.TextDisplay(f"**Status:** {'Resolved' if case.resolved else 'Active'}"),
        ))
        await send_layout(interaction, view, ephemeral=True)

    # ------------------------------------------------------------------ #
    # Logging                                                               #
    # ------------------------------------------------------------------ #

    async def _send_mod_log(
        self, 
        guild: discord.Guild, 
        case: object, 
        member: Optional[discord.Member] = None
    ) -> None:
        """
        Send a moderation log entry to the configured mod-log channel.
        
        Args:
            guild: The Discord guild where the action occurred.
            case: The ModerationCase object with action details.
            member: Optional Discord member who was moderated.
        """
        try:
            # Get guild configuration
            guild_config = await self._guild_repo().get_or_create(guild.id, guild.name)
            
            if guild_config.mod_log_channel is None:
                # No mod log channel configured
                return
            
            # Get the channel
            mod_log_channel = guild.get_channel(guild_config.mod_log_channel)
            if mod_log_channel is None or not hasattr(mod_log_channel, 'send'):
                # Channel not found or not a text channel
                log.warning("Mod log channel %d not found in guild %d", guild_config.mod_log_channel, guild.id)
                return
            
            # Build the log message with Components V2
            case_type_icons = {
                CaseType.BAN: "🔨",
                CaseType.KICK: "👢", 
                CaseType.TIMEOUT: "⏰",
                CaseType.WARN: "⚠️",
            }
            icon = case_type_icons.get(case.case_type, "📋")
            
            # Create the layout
            view = discord.ui.LayoutView()
            view.add_item(discord.ui.Container(
                discord.ui.TextDisplay(f"{icon} **Moderation Case #{case.id}**"),
                discord.ui.Separator(visible=True),
                discord.ui.TextDisplay(f"**Action:** {case.case_type}"),
                discord.ui.TextDisplay(f"**Target:** {case.target_username}"),
                discord.ui.TextDisplay(f"**Moderator:** {case.moderator_username}"),
            ))
            
            if case.reason:
                view.add_item(discord.ui.Container(
                    discord.ui.TextDisplay(f"**Reason:** {case.reason}"),
                ))
            
            if case.duration:
                view.add_item(discord.ui.Container(
                    discord.ui.TextDisplay(f"**Duration:** {case.duration} seconds"),
                ))
                
            view.add_item(discord.ui.Container(
                discord.ui.TextDisplay(f"**Time:** {case.created_at}"),
                discord.ui.Separator(visible=True),
            ))
            
            await send_layout_to_channel(mod_log_channel, view)
            
        except Exception as e:
            log.error("Failed to send mod log: %s", e)
