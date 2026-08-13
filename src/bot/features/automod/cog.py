"""
src/bot/features/automod/cog.py
----------------------------------
AutoMod Cog

Listens for Discord events (on_message, on_member_join, etc.) and runs
each incoming event through the registered automod rules. When a rule
triggers, it delegates the action to the ModerationService.

This cog is intentionally minimal in Phase 1. The full rule engine,
per-guild configuration, and action system will be implemented in Phase 3.
"""

from __future__ import annotations

import discord
from discord.ext import commands

from ...core.bot import KairoBot
from ...core.logging import get_logger

log = get_logger(__name__)


class AutoModCog(commands.Cog, name="AutoMod"):
    """
    Automated moderation rule engine.

    Monitors message and member events and enforces configured rules
    automatically.
    """

    def __init__(self, bot: KairoBot) -> None:
        self.bot = bot
        log.info("AutoMod cog initialised.")

    # ------------------------------------------------------------------ #
    # Event listeners                                                      #
    # ------------------------------------------------------------------ #

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """
        Check every new message against active automod rules.

        Skips:
            - Messages from bots (including Kairo itself)
            - DMs (automod only applies in guilds)
            - Messages from users with MANAGE_MESSAGES permission (moderators)
        """
        if message.author.bot:
            return
        if not message.guild:
            return
        if message.author.guild_permissions.manage_messages:  # type: ignore[union-attr]
            return

        # TODO: Run message through rule engine in Phase 3.
        # await self._check_spam(message)
        # await self._check_mentions(message)
        # await self._check_links(message)
        # await self._check_words(message)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """
        Check new member joins for raid protection.

        Rapid mass joins can indicate a raid attempt. When the join rate
        exceeds a configured threshold, Kairo can automatically slow-mode
        the server or notify moderators.
        """
        # TODO: Implement raid detection in Phase 3.
        pass

    # ------------------------------------------------------------------ #
    # Rule stubs (to be implemented in Phase 3)                           #
    # ------------------------------------------------------------------ #

    async def _check_spam(self, message: discord.Message) -> None:
        """
        Detect message spam (too many messages in a short time window).

        Uses a sliding window rate limiter per (user, channel) pair.
        Configurable: max_messages, window_seconds, action.
        """
        # TODO: Implement sliding window rate limiter.
        pass

    async def _check_mentions(self, message: discord.Message) -> None:
        """
        Detect mention spam (too many @mentions in a single message).

        Configurable: max_mentions, action.
        """
        # TODO: Count unique mentions and compare against guild config.
        pass

    async def _check_links(self, message: discord.Message) -> None:
        """
        Detect unauthorised invite links or external URLs.

        Configurable: block_invites (bool), block_links (bool),
                      allowed_domains (list[str]).
        """
        # TODO: Regex-scan message content for invite/link patterns.
        pass

    async def _check_words(self, message: discord.Message) -> None:
        """
        Detect blocked words or phrases.

        Configurable: blocked_words (list[str]), action.
        """
        # TODO: Check message content against guild blocked word list.
        pass


async def setup(bot: KairoBot) -> None:
    """Called by discord.py when this extension is loaded."""
    await bot.add_cog(AutoModCog(bot))
