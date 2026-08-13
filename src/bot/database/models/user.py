"""
src/bot/database/models/user.py
--------------------------------
User Record Model

Defines the data shape and SQL schema for per-user-per-guild records.
User data is scoped to a guild — the same Discord user can have different
records in different guilds.

Table: users
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS users (
    -- Composite primary key: one record per (user, guild) pair.
    user_id         INTEGER NOT NULL,
    guild_id        INTEGER NOT NULL REFERENCES guilds(id) ON DELETE CASCADE,

    -- Cached Discord username at the time of last interaction.
    username        TEXT    NOT NULL DEFAULT '',

    -- Whether this user has been globally muted in this guild via Kairo.
    muted           INTEGER NOT NULL DEFAULT 0 CHECK (muted IN (0, 1)),

    -- Total number of warnings the user has received in this guild.
    warn_count      INTEGER NOT NULL DEFAULT 0,

    -- XP for the leveling system (Phase 3).
    xp              INTEGER NOT NULL DEFAULT 0,

    -- ISO 8601 timestamp of the first time Kairo saw this user in this guild.
    first_seen      TEXT    NOT NULL DEFAULT (datetime('now')),

    -- ISO 8601 timestamp of the most recent interaction.
    last_seen       TEXT    NOT NULL DEFAULT (datetime('now')),

    PRIMARY KEY (user_id, guild_id)
);
"""


@dataclass
class UserRecord:
    """
    Represents one row of the users table.

    Attributes:
        user_id    (int)       Discord user snowflake ID.
        guild_id   (int)       Discord guild snowflake ID.
        username   (str)       Cached Discord username.
        muted      (bool)      Whether the user is currently muted.
        warn_count (int)       Total number of warnings in this guild.
        xp         (int)       Experience points (leveling system).
        first_seen (datetime)  When Kairo first saw this user in this guild.
        last_seen  (datetime)  Most recent interaction timestamp.
    """

    user_id: int
    guild_id: int
    username: str = ""
    muted: bool = False
    warn_count: int = 0
    xp: int = 0
    first_seen: datetime = field(default_factory=datetime.utcnow)
    last_seen: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def from_row(cls, row: object) -> UserRecord:
        """Construct a UserRecord from an aiosqlite.Row."""
        return cls(
            user_id=row["user_id"],
            guild_id=row["guild_id"],
            username=row["username"],
            muted=bool(row["muted"]),
            warn_count=row["warn_count"],
            xp=row["xp"],
            first_seen=datetime.fromisoformat(row["first_seen"]),
            last_seen=datetime.fromisoformat(row["last_seen"]),
        )
