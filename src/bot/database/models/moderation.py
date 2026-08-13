"""
src/bot/database/models/moderation.py
---------------------------------------
Moderation Models

Defines data shapes and SQL schemas for moderation cases and warnings.

Each moderation action (ban, kick, timeout, warn) creates a ModerationCase.
Warnings are a subtype of case that also get a dedicated Warning row for
quick lookups and warn-count aggregation.

Tables:
    moderation_cases  — One row per moderation action
    warnings          — One row per warning (linked to a case)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class CaseType(str, Enum):
    """The type of moderation action recorded in a case."""
    BAN = "ban"
    UNBAN = "unban"
    KICK = "kick"
    TIMEOUT = "timeout"
    UNTIMEOUT = "untimeout"
    WARN = "warn"
    MUTE = "mute"
    UNMUTE = "unmute"
    NOTE = "note"


CREATE_CASES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS moderation_cases (
    -- Auto-incremented case ID. Displayed to moderators as "#42".
    id              INTEGER PRIMARY KEY AUTOINCREMENT,

    -- The guild this case belongs to.
    guild_id        INTEGER NOT NULL REFERENCES guilds(id) ON DELETE CASCADE,

    -- The Discord user who was actioned.
    target_id       INTEGER NOT NULL,
    target_username TEXT    NOT NULL DEFAULT '',

    -- The moderator who performed the action.
    moderator_id    INTEGER NOT NULL,
    moderator_username TEXT NOT NULL DEFAULT '',

    -- The type of action (see CaseType enum).
    case_type       TEXT    NOT NULL,

    -- Human-readable reason for the action.
    reason          TEXT,

    -- For timeouts: the duration in seconds. NULL for permanent or non-timed actions.
    duration        INTEGER,

    -- Whether this case has been resolved (e.g. ban lifted, timeout expired).
    resolved        INTEGER NOT NULL DEFAULT 0 CHECK (resolved IN (0, 1)),

    -- Optional moderator note added after the fact.
    note            TEXT,

    -- ISO 8601 timestamp when the action was taken.
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),

    -- ISO 8601 timestamp when this case was last modified.
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

CREATE_WARNINGS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS warnings (
    -- Auto-incremented warning ID.
    id          INTEGER PRIMARY KEY AUTOINCREMENT,

    -- The case that generated this warning.
    case_id     INTEGER NOT NULL REFERENCES moderation_cases(id) ON DELETE CASCADE,

    -- The guild and user this warning belongs to (denormalised for fast queries).
    guild_id    INTEGER NOT NULL REFERENCES guilds(id) ON DELETE CASCADE,
    user_id     INTEGER NOT NULL,

    -- The warning reason (copied from the case for convenience).
    reason      TEXT,

    -- Whether a moderator has pardoned this specific warning.
    pardoned    INTEGER NOT NULL DEFAULT 0 CHECK (pardoned IN (0, 1)),

    -- ISO 8601 timestamp of the warning.
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""


@dataclass
class ModerationCase:
    """
    Represents one row of the moderation_cases table.

    Attributes:
        id                 (int)              Auto-assigned case number.
        guild_id           (int)              Guild this case belongs to.
        target_id          (int)              Discord ID of the actioned user.
        target_username    (str)              Cached username of the target.
        moderator_id       (int)              Discord ID of the moderator.
        moderator_username (str)              Cached username of the moderator.
        case_type          (CaseType)         Type of action taken.
        reason             (str | None)       Reason provided by the moderator.
        duration           (int | None)       Timeout duration in seconds, or None.
        resolved           (bool)             Whether this case is closed.
        note               (str | None)       Moderator note (added post-action).
        created_at         (datetime)         When the action was taken.
        updated_at         (datetime)         Last modification time.
    """

    guild_id: int
    target_id: int
    moderator_id: int
    case_type: CaseType
    id: int = 0
    target_username: str = ""
    moderator_username: str = ""
    reason: Optional[str] = None
    duration: Optional[int] = None
    resolved: bool = False
    note: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def from_row(cls, row: object) -> ModerationCase:
        """Construct a ModerationCase from an aiosqlite.Row."""
        return cls(
            id=row["id"],
            guild_id=row["guild_id"],
            target_id=row["target_id"],
            target_username=row["target_username"],
            moderator_id=row["moderator_id"],
            moderator_username=row["moderator_username"],
            case_type=CaseType(row["case_type"]),
            reason=row["reason"],
            duration=row["duration"],
            resolved=bool(row["resolved"]),
            note=row["note"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )


@dataclass
class Warning:
    """
    Represents one row of the warnings table.

    Attributes:
        id         (int)           Auto-assigned warning ID.
        case_id    (int)           The case that created this warning.
        guild_id   (int)           Guild this warning belongs to.
        user_id    (int)           Discord ID of the warned user.
        reason     (str | None)    Warning reason.
        pardoned   (bool)          Whether this warning has been pardoned.
        created_at (datetime)      When the warning was issued.
    """

    case_id: int
    guild_id: int
    user_id: int
    id: int = 0
    reason: Optional[str] = None
    pardoned: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def from_row(cls, row: object) -> Warning:
        """Construct a Warning from an aiosqlite.Row."""
        return cls(
            id=row["id"],
            case_id=row["case_id"],
            guild_id=row["guild_id"],
            user_id=row["user_id"],
            reason=row["reason"],
            pardoned=bool(row["pardoned"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
