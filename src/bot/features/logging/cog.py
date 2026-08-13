"""
src/bot/features/logging/cog.py
----------------------------------
Logging Cog

Listens for Discord gateway events and posts formatted log messages to
the guild's configured log channels. Uses Components V2 for rich formatting.

Phase 1: Scaffold only (listeners registered, no output yet).
Phase 3: Full implementation with configurable channels and event filtering.
"""

from __future__ import annotations

import discord
from discord.ext import commands

from ...core.bot import KairoBot
from ...core.logging import get_logger

log = get_logger(__name__)


class LoggingCog(commands.Cog, name="Logging"):
    """
    Server event logging cog.

    Posts structured log messages to Discord channels when server events
    occur. Each event type is independently configurable per guild.
    """

    def __init__(self, bot: KairoBot) -> None:
        self.bot = bot
        log.info("Logging cog initialised.")

    # ------------------------------------------------------------------ #
    # Member events                                                        #
    # ------------------------------------------------------------------ #

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """Log a member joining the server."""
        log.debug("Member joined: %s (%d) in guild %d", member, member.id, member.guild.id)
        # TODO: Fetch guild log channel from config and post a join panel.

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        """Log a member leaving the server."""
        log.debug("Member left: %s (%d) in guild %d", member, member.id, member.guild.id)
        # TODO: Post a leave log panel.

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User) -> None:
        """Log a member being banned."""
        log.debug("Member banned: %s (%d) in guild %d", user, user.id, guild.id)
        # TODO: Post a ban log panel.

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User) -> None:
        """Log a member being unbanned."""
        log.debug("Member unbanned: %s (%d) in guild %d", user, user.id, guild.id)
        # TODO: Post an unban log panel.

    # ------------------------------------------------------------------ #
    # Message events                                                       #
    # ------------------------------------------------------------------ #

    @commands.Cog.listener()
    async def on_message_edit(
        self,
        before: discord.Message,
        after: discord.Message,
    ) -> None:
        """Log a message being edited."""
        if before.author.bot:
            return
        if before.content == after.content:
            return  # Pin/embed suppression; not a real edit
        log.debug(
            "Message edited by %s in channel %s (guild %d)",
            before.author,
            before.channel,
            before.guild.id if before.guild else 0,
        )
        # TODO: Post an edit log panel showing before/after content.

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        """Log a message being deleted."""
        if message.author.bot:
            return
        log.debug(
            "Message deleted by %s in channel %s (guild %d)",
            message.author,
            message.channel,
            message.guild.id if message.guild else 0,
        )
        # TODO: Post a delete log panel with the original content (if cached).


async def setup(bot: KairoBot) -> None:
    """Called by discord.py when this extension is loaded."""
    await bot.add_cog(LoggingCog(bot))
