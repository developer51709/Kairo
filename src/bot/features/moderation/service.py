"""
src/bot/features/moderation/service.py
-----------------------------------------
Moderation Service

Contains all moderation business logic. Separated from the cog so that:
    1. Logic can be tested without Discord interactions.
    2. Other parts of Kairo (e.g. automod) can trigger moderation actions
       programmatically without going through a slash command.

The service applies the Discord action, records a ModerationCase,
and sends a response panel.
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
from ...components import Panel, Container, Text, Separator

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

        # Record in database
        # case = await self._mod_repo().create_case(
        #     guild_id=interaction.guild.id,
        #     target_id=member.id,
        #     moderator_id=interaction.user.id,
        #     case_type=CaseType.BAN,
        #     reason=reason,
        #     target_username=str(member),
        #     moderator_username=str(interaction.user),
        # )

        panel = Panel(
            Container(
                Text(f"✅ **{member}** has been banned."),
                Text(f"**Reason:** {reason or 'No reason provided.'}"),
            ),
            ephemeral=True,
        )
        await panel.send(interaction)
        log.info("Banned %s from guild %d (%s)", member, interaction.guild.id, reason)

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

        panel = Panel(
            Container(
                Text(f"✅ **{member}** has been kicked."),
                Text(f"**Reason:** {reason or 'No reason provided.'}"),
            ),
            ephemeral=True,
        )
        await panel.send(interaction)
        log.info("Kicked %s from guild %d (%s)", member, interaction.guild.id, reason)

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

        panel = Panel(
            Container(
                Text(f"✅ **{member}** has been timed out for **{duration}**."),
                Text(f"**Reason:** {reason or 'No reason provided.'}"),
            ),
            ephemeral=True,
        )
        await panel.send(interaction)
        log.info("Timed out %s for %ds in guild %d", member, seconds, interaction.guild.id)

    async def warn(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: Optional[str] = None,
    ) -> None:
        """Issue a warning to a member and record a case + warning entry."""
        assert interaction.guild is not None

        # TODO: Create case and warning in database once db is wired up.
        # case = await self._mod_repo().create_case(...)
        # warning = await self._mod_repo().create_warning(case)

        panel = Panel(
            Container(
                Text(f"⚠️ **{member}** has been warned."),
                Text(f"**Reason:** {reason or 'No reason provided.'}"),
            ),
            ephemeral=True,
        )
        await panel.send(interaction)
        log.info("Warned %s in guild %d (%s)", member, interaction.guild.id, reason)

    async def show_history(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
    ) -> None:
        """Display a member's moderation history (placeholder)."""
        panel = Panel(
            Container(
                Text(f"## Moderation History — {member}"),
                Separator(divider=True),
                Text("*No moderation history found.*"),
            ),
            ephemeral=True,
        )
        await panel.send(interaction)

    async def show_case(
        self,
        interaction: discord.Interaction,
        case_id: int,
    ) -> None:
        """Display a specific moderation case (placeholder)."""
        panel = Panel(
            Container(
                Text(f"## Case #{case_id}"),
                Separator(divider=True),
                Text("*Case lookup is not yet implemented.*"),
            ),
            ephemeral=True,
        )
        await panel.send(interaction)
