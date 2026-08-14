"""
src/bot/features/automod/cog.py
----------------------------------
AutoMod Cog

Listens for Discord events (on_message, on_member_join, etc.) and runs
each incoming event through the registered automod rules. When a rule
triggers, it delegates the action to the AutoModService.

This cog implements Phase 3 AutoMod functionality with configurable
rules and actions for spam, links, words, and raid protection.
"""

from __future__ import annotations

import discord
from discord.ext import commands

from ...core.bot import KairoBot
from ...core.logging import get_logger
from .service import AutoModService

log = get_logger(__name__)


class AutoModCog(commands.Cog, name="AutoMod"):
    """
    Automated moderation rule engine.

    Monitors message and member events and enforces configured rules
    automatically.
    """

    def __init__(self, bot: KairoBot) -> None:
        self.bot = bot
        self.service = AutoModService(bot)
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

        # Run message through AutoMod rule engine
        await self.service.check_message(message)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """
        Check new member joins for raid protection.

        Rapid mass joins can indicate a raid attempt. When the join rate
        exceeds a configured threshold, Kairo can automatically slow-mode
        the server or notify moderators.
        """
        await self.service.check_member_join(member)

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

    # ------------------------------------------------------------------ #
    # Slash Commands                                                       #
    # ------------------------------------------------------------------ #

    @commands.hybrid_command(name="automod", description="Configure AutoMod settings.")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def automod_config(self, ctx: commands.Context) -> None:
        """Configure AutoMod settings for this server."""
        # TODO: Implement AutoMod configuration commands in Phase 3
        await ctx.send("AutoMod configuration commands coming soon in Phase 3!")


async def setup(bot: KairoBot) -> None:
    """Called by discord.py when this extension is loaded."""
    cog = AutoModCog(bot)
    await bot.add_cog(cog)
    # Start the AutoMod service
    await cog.service.start()
