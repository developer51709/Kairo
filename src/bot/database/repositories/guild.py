"""
src/bot/database/repositories/guild.py
----------------------------------------
Guild Repository

Provides all database operations for the guilds table. Feature cogs should
use this repository rather than writing guild-related SQL themselves.

Usage:
    repo = GuildRepository(db)
    config = await repo.get(guild_id)
    if config is None:
        config = await repo.create(guild_id, name="My Server")
"""

from datetime import datetime
from typing import Optional

from ..connection import Database
from ..models.guild import GuildConfig
from ...core.logging import get_logger

log = get_logger(__name__)


class GuildRepository:
    """
    Data access object for the guilds table.

    All methods accept and return GuildConfig dataclass instances rather
    than raw database rows, providing type safety and IDE support.

    Attributes:
        _db (Database): The shared database connection.
    """

    def __init__(self, db: Database) -> None:
        self._db = db

    # ------------------------------------------------------------------ #
    # Read                                                                 #
    # ------------------------------------------------------------------ #

    async def get(self, guild_id: int) -> Optional[GuildConfig]:
        """
        Retrieve the configuration for a guild.

        Args:
            guild_id: Discord snowflake ID of the guild.

        Returns:
            GuildConfig if found, None otherwise.
        """
        row = await self._db.fetch_one(
            "SELECT * FROM guilds WHERE id = ?",
            (guild_id,),
        )
        return GuildConfig.from_row(row) if row else None

    async def get_all_active(self) -> list[GuildConfig]:
        """
        Return all guilds where Kairo is currently active.

        Returns:
            List of GuildConfig instances (may be empty).
        """
        rows = await self._db.fetch_all(
            "SELECT * FROM guilds WHERE active = 1 ORDER BY id",
        )
        return [GuildConfig.from_row(r) for r in rows]

    # ------------------------------------------------------------------ #
    # Write                                                                #
    # ------------------------------------------------------------------ #

    async def create(self, guild_id: int, name: str = "") -> GuildConfig:
        """
        Insert a new guild row with default configuration.

        If a row for this guild already exists (e.g. the bot rejoined),
        it is reactivated and its name updated rather than duplicated.

        Args:
            guild_id: Discord snowflake ID of the guild.
            name:     Current guild display name.

        Returns:
            The newly created or reactivated GuildConfig.
        """
        await self._db.execute(
            """
            INSERT INTO guilds (id, name, active)
            VALUES (?, ?, 1)
            ON CONFLICT(id) DO UPDATE SET
                name     = excluded.name,
                active   = 1,
                updated_at = datetime('now')
            """,
            (guild_id, name),
        )
        config = await self.get(guild_id)
        assert config is not None
        log.info("Guild created/reactivated in database: %d (%s)", guild_id, name)
        return config

    async def update(self, config: GuildConfig) -> None:
        """
        Persist changes to an existing GuildConfig.

        Args:
            config: A modified GuildConfig instance (must already exist in DB).
        """
        await self._db.execute(
            """
            UPDATE guilds SET
                name            = ?,
                active          = ?,
                mod_log_channel = ?,
                log_channel     = ?,
                mod_role        = ?,
                auto_role       = ?,
                locale          = ?,
                updated_at      = datetime('now')
            WHERE id = ?
            """,
            (
                config.name,
                int(config.active),
                config.mod_log_channel,
                config.log_channel,
                config.mod_role,
                config.auto_role,
                config.locale,
                config.id,
            ),
        )

    async def deactivate(self, guild_id: int) -> None:
        """
        Mark a guild as inactive (bot was removed).

        Data is retained so it can be restored if the bot is re-added.

        Args:
            guild_id: Discord snowflake ID of the guild.
        """
        await self._db.execute(
            "UPDATE guilds SET active = 0, updated_at = datetime('now') WHERE id = ?",
            (guild_id,),
        )
        log.info("Guild deactivated in database: %d", guild_id)

    async def get_or_create(self, guild_id: int, name: str = "") -> GuildConfig:
        """
        Return the config for a guild, creating it if it does not exist.

        This is the preferred method for feature cogs that need guild config
        and should work regardless of whether the guild was seen before.

        Args:
            guild_id: Discord snowflake ID of the guild.
            name:     Current guild display name (used if creating).

        Returns:
            Existing or newly created GuildConfig.
        """
        config = await self.get(guild_id)
        if config is None:
            config = await self.create(guild_id, name=name)
        return config
