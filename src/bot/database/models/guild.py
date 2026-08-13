"""
src/bot/database/models/guild.py
---------------------------------
Guild Configuration Model

Defines the data shape and SQL schema for per-guild configuration.
Each Discord server that uses Kairo gets one row in the guilds table.
Feature-specific configuration (moderation, automod, etc.) is stored in
separate tables that reference this row via a foreign key.

Table: guilds
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# SQL used by the migration system to create this table.
# Kept alongside the model so schema and dataclass stay in sync.
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS guilds (
    -- Discord snowflake ID of the guild. Primary key.
    id              INTEGER PRIMARY KEY,

    -- Human-readable guild name. Updated when the bot sees the guild.
    name            TEXT    NOT NULL DEFAULT '',

    -- Unix timestamp (seconds) of when Kairo first joined this guild.
    joined_at       INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),

    -- Whether Kairo is currently a member of this guild.
    -- Set to 0 when the bot is removed; data is retained for re-joins.
    active          INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),

    -- The channel ID where Kairo sends mod-log messages. NULL = disabled.
    mod_log_channel INTEGER,

    -- The channel ID for general bot logging. NULL = disabled.
    log_channel     INTEGER,

    -- The role ID that grants moderator access to Kairo commands. NULL = server admins only.
    mod_role        INTEGER,

    -- The role ID granted to new members (auto-role). NULL = disabled.
    auto_role       INTEGER,

    -- The locale used for bot messages in this guild. Default: 'en'.
    locale          TEXT    NOT NULL DEFAULT 'en',

    -- ISO 8601 timestamp of the last configuration change.
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""


@dataclass
class GuildConfig:
    """
    Represents one row of the guilds table.

    Attributes:
        id              (int)            Discord guild snowflake ID.
        name            (str)            Guild display name.
        joined_at       (int)            Unix timestamp when Kairo joined.
        active          (bool)           Whether the bot is still in the guild.
        mod_log_channel (int | None)     Channel ID for mod-log messages.
        log_channel     (int | None)     Channel ID for general logs.
        mod_role        (int | None)     Role ID that grants moderator access.
        auto_role       (int | None)     Role ID auto-assigned to new members.
        locale          (str)            Locale code (e.g. 'en', 'fr').
        updated_at      (datetime)       Last modification time.
    """

    id: int
    name: str = ""
    joined_at: int = field(default_factory=lambda: int(datetime.utcnow().timestamp()))
    active: bool = True
    mod_log_channel: Optional[int] = None
    log_channel: Optional[int] = None
    mod_role: Optional[int] = None
    auto_role: Optional[int] = None
    locale: str = "en"
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def from_row(cls, row: object) -> GuildConfig:
        """
        Construct a GuildConfig from an aiosqlite.Row.

        Args:
            row: An aiosqlite.Row returned by the guilds repository.

        Returns:
            A populated GuildConfig instance.
        """
        return cls(
            id=row["id"],
            name=row["name"],
            joined_at=row["joined_at"],
            active=bool(row["active"]),
            mod_log_channel=row["mod_log_channel"],
            log_channel=row["log_channel"],
            mod_role=row["mod_role"],
            auto_role=row["auto_role"],
            locale=row["locale"],
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
