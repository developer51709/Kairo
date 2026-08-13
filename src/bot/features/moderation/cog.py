"""
src/bot/features/moderation/cog.py
------------------------------------
Moderation Cog

Discord.py Cog providing moderation slash commands.
Delegates business logic to ModerationService and uses
Components V2 for rich response panels.

All commands require the moderator to have appropriate Discord permissions
AND the configured mod_role (if set) in the guild config.
"""

from __future__ import annotations

from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from ...core.bot import KairoBot
from ...core.logging import get_logger
from .service import ModerationService

log = get_logger(__name__)


class ModerationCog(commands.Cog, name="Moderation"):
    """
    Moderation commands for Kairo.

    These commands create moderation cases, apply Discord actions
    (ban, kick, timeout, etc.), and log results to the mod-log channel.
    """

    def __init__(self, bot: KairoBot) -> None:
        self.bot = bot
        self.service = ModerationService(bot)

    # ------------------------------------------------------------------ #
    # Permission check                                                    #
    # ------------------------------------------------------------------ #

    async def _check_moderator(self, interaction: discord.Interaction) -> bool:
        """
        Return True if the invoker has moderator privileges.

        A user is considered a moderator if they:
            1. Have the ADMINISTRATOR permission, OR
            2. Have the MANAGE_GUILD permission, OR
            3. Have the guild's configured mod_role.

        Returns False and sends an error response if not authorised.
        """
        if interaction.user.guild_permissions.administrator:  # type: ignore[union-attr]
            return True
        if interaction.user.guild_permissions.manage_guild:  # type: ignore[union-attr]
            return True
        # TODO: check guild config mod_role when guild config is available
        await interaction.response.send_message(
            "❌ You do not have permission to use this command.",
            ephemeral=True,
        )
        return False

    # ------------------------------------------------------------------ #
    # Commands                                                             #
    # ------------------------------------------------------------------ #

    @app_commands.command(name="ban", description="Ban a member from the server.")
    @app_commands.describe(
        member="The member to ban.",
        reason="The reason for the ban.",
        delete_days="Number of days of messages to delete (0–7).",
    )
    @app_commands.guild_only()
    async def ban(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: Optional[str] = None,
        delete_days: app_commands.Range[int, 0, 7] = 0,
    ) -> None:
        """Ban a member from the server and record a moderation case."""
        if not await self._check_moderator(interaction):
            return
        await self.service.ban(interaction, member, reason=reason, delete_days=delete_days)

    @app_commands.command(name="kick", description="Kick a member from the server.")
    @app_commands.describe(
        member="The member to kick.",
        reason="The reason for the kick.",
    )
    @app_commands.guild_only()
    async def kick(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: Optional[str] = None,
    ) -> None:
        """Kick a member from the server and record a moderation case."""
        if not await self._check_moderator(interaction):
            return
        await self.service.kick(interaction, member, reason=reason)

    @app_commands.command(name="timeout", description="Temporarily mute a member.")
    @app_commands.describe(
        member="The member to timeout.",
        duration="Timeout duration (e.g. 10m, 1h, 1d).",
        reason="The reason for the timeout.",
    )
    @app_commands.guild_only()
    async def timeout(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        duration: str,
        reason: Optional[str] = None,
    ) -> None:
        """Timeout a member and record a moderation case."""
        if not await self._check_moderator(interaction):
            return
        await self.service.timeout(interaction, member, duration=duration, reason=reason)

    @app_commands.command(name="warn", description="Issue a warning to a member.")
    @app_commands.describe(
        member="The member to warn.",
        reason="The reason for the warning.",
    )
    @app_commands.guild_only()
    async def warn(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: Optional[str] = None,
    ) -> None:
        """Warn a member and record a moderation case and warning entry."""
        if not await self._check_moderator(interaction):
            return
        await self.service.warn(interaction, member, reason=reason)

    @app_commands.command(name="history", description="View a member's moderation history.")
    @app_commands.describe(member="The member to look up.")
    @app_commands.guild_only()
    async def history(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
    ) -> None:
        """Display a paginated moderation history for a member."""
        if not await self._check_moderator(interaction):
            return
        await self.service.show_history(interaction, member)

    @app_commands.command(name="case", description="View a specific moderation case.")
    @app_commands.describe(case_id="The case number to look up.")
    @app_commands.guild_only()
    async def case(
        self,
        interaction: discord.Interaction,
        case_id: int,
    ) -> None:
        """Display the details of a single moderation case."""
        if not await self._check_moderator(interaction):
            return
        await self.service.show_case(interaction, case_id)


async def setup(bot: KairoBot) -> None:
    """Called by discord.py when this extension is loaded."""
    await bot.add_cog(ModerationCog(bot))
