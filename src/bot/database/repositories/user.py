"""
src/bot/database/repositories/user.py
---------------------------------------
User Repository

Provides all database operations for the users table. User records are
scoped to a guild — one row per (user_id, guild_id) pair.

Usage:
    repo = UserRepository(db)
    record = await repo.get_or_create(user_id=123, guild_id=456, username="Alice")
    record.xp += 10
    await repo.update(record)
"""

from datetime import datetime
from typing import Optional

from ..connection import Database
from ..models.user import UserRecord
from ...core.logging import get_logger

log = get_logger(__name__)


class UserRepository:
    """
    Data access object for the users table.

    Attributes:
        _db (Database): The shared database connection.
    """

    def __init__(self, db: Database) -> None:
        self._db = db

    # ------------------------------------------------------------------ #
    # Read                                                                 #
    # ------------------------------------------------------------------ #

    async def get(self, user_id: int, guild_id: int) -> Optional[UserRecord]:
        """
        Retrieve a user record for a specific guild.

        Args:
            user_id:  Discord snowflake ID of the user.
            guild_id: Discord snowflake ID of the guild.

        Returns:
            UserRecord if found, None otherwise.
        """
        row = await self._db.fetch_one(
            "SELECT * FROM users WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id),
        )
        return UserRecord.from_row(row) if row else None

    async def get_all_for_guild(self, guild_id: int) -> list[UserRecord]:
        """
        Return all user records for a guild.

        Args:
            guild_id: Discord snowflake ID of the guild.

        Returns:
            List of UserRecord instances, ordered by user_id.
        """
        rows = await self._db.fetch_all(
            "SELECT * FROM users WHERE guild_id = ? ORDER BY user_id",
            (guild_id,),
        )
        return [UserRecord.from_row(r) for r in rows]

    async def get_top_xp(self, guild_id: int, limit: int = 10) -> list[UserRecord]:
        """
        Return the top users by XP in a guild (leaderboard).

        Args:
            guild_id: Discord snowflake ID of the guild.
            limit:    Maximum number of records to return.

        Returns:
            List of UserRecord instances sorted by XP descending.
        """
        rows = await self._db.fetch_all(
            "SELECT * FROM users WHERE guild_id = ? ORDER BY xp DESC LIMIT ?",
            (guild_id, limit),
        )
        return [UserRecord.from_row(r) for r in rows]

    # ------------------------------------------------------------------ #
    # Write                                                                #
    # ------------------------------------------------------------------ #

    async def create(self, user_id: int, guild_id: int, username: str = "") -> UserRecord:
        """
        Insert a new user record with default values.

        Args:
            user_id:  Discord snowflake ID of the user.
            guild_id: Discord snowflake ID of the guild.
            username: Current Discord username (cached for display).

        Returns:
            The newly created UserRecord.
        """
        await self._db.execute(
            """
            INSERT INTO users (user_id, guild_id, username)
            VALUES (?, ?, ?)
            """,
            (user_id, guild_id, username),
        )
        record = await self.get(user_id, guild_id)
        assert record is not None
        return record

    async def update(self, record: UserRecord) -> None:
        """
        Persist changes to an existing UserRecord.

        Args:
            record: A modified UserRecord instance.
        """
        await self._db.execute(
            """
            UPDATE users SET
                username   = ?,
                muted      = ?,
                warn_count = ?,
                xp         = ?,
                last_seen  = datetime('now')
            WHERE user_id = ? AND guild_id = ?
            """,
            (
                record.username,
                int(record.muted),
                record.warn_count,
                record.xp,
                record.user_id,
                record.guild_id,
            ),
        )

    async def get_or_create(
        self,
        user_id: int,
        guild_id: int,
        username: str = "",
    ) -> UserRecord:
        """
        Return an existing record or create one with defaults.

        Also updates the username and last_seen timestamp if the record exists.

        Args:
            user_id:  Discord snowflake ID of the user.
            guild_id: Discord snowflake ID of the guild.
            username: Current Discord username.

        Returns:
            Existing or newly created UserRecord.
        """
        record = await self.get(user_id, guild_id)
        if record is None:
            record = await self.create(user_id, guild_id, username=username)
        elif username and record.username != username:
            record.username = username
            await self.update(record)
        return record

    async def increment_xp(self, user_id: int, guild_id: int, amount: int = 1) -> None:
        """
        Increment a user's XP by the given amount.

        Args:
            user_id:  Discord snowflake ID of the user.
            guild_id: Discord snowflake ID of the guild.
            amount:   Number of XP points to add.
        """
        await self._db.execute(
            """
            UPDATE users SET xp = xp + ?, last_seen = datetime('now')
            WHERE user_id = ? AND guild_id = ?
            """,
            (amount, user_id, guild_id),
        )
