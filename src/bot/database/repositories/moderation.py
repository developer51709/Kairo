"""
src/bot/database/repositories/moderation.py
---------------------------------------------
Moderation Repository

Provides all database operations for moderation cases and warnings.
The moderation feature cog should use this repository exclusively —
never write moderation SQL elsewhere.

Usage:
    repo = ModerationRepository(db)

    # Create a warn case + warning
    case = await repo.create_case(
        guild_id=..., target_id=..., moderator_id=...,
        case_type=CaseType.WARN, reason="Spamming"
    )
    warning = await repo.create_warning(case)

    # Look up a user's history
    cases = await repo.get_cases_for_user(guild_id=..., user_id=...)
"""

from typing import Optional

from ..connection import Database
from ..models.moderation import CaseType, ModerationCase, Warning
from ...core.logging import get_logger

log = get_logger(__name__)


class ModerationRepository:
    """
    Data access object for the moderation_cases and warnings tables.

    Attributes:
        _db (Database): The shared database connection.
    """

    def __init__(self, db: Database) -> None:
        self._db = db

    # ------------------------------------------------------------------ #
    # Cases — Read                                                         #
    # ------------------------------------------------------------------ #

    async def get_case(self, case_id: int, guild_id: int) -> Optional[ModerationCase]:
        """
        Retrieve a specific case by ID.

        Args:
            case_id:  The case number.
            guild_id: Guild scope (prevents cross-guild case lookup).

        Returns:
            ModerationCase if found, None otherwise.
        """
        row = await self._db.fetch_one(
            "SELECT * FROM moderation_cases WHERE id = ? AND guild_id = ?",
            (case_id, guild_id),
        )
        return ModerationCase.from_row(row) if row else None

    async def get_cases_for_user(
        self,
        guild_id: int,
        user_id: int,
        limit: int = 50,
    ) -> list[ModerationCase]:
        """
        Return moderation cases for a specific user in a guild.

        Args:
            guild_id: Discord snowflake ID of the guild.
            user_id:  Discord snowflake ID of the target user.
            limit:    Maximum number of cases to return (most recent first).

        Returns:
            List of ModerationCase instances.
        """
        rows = await self._db.fetch_all(
            """
            SELECT * FROM moderation_cases
            WHERE guild_id = ? AND target_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (guild_id, user_id, limit),
        )
        return [ModerationCase.from_row(r) for r in rows]

    async def get_recent_cases(
        self,
        guild_id: int,
        limit: int = 20,
    ) -> list[ModerationCase]:
        """
        Return the most recent moderation cases in a guild.

        Args:
            guild_id: Discord snowflake ID of the guild.
            limit:    Maximum number of cases to return.

        Returns:
            List of ModerationCase instances (newest first).
        """
        rows = await self._db.fetch_all(
            """
            SELECT * FROM moderation_cases
            WHERE guild_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (guild_id, limit),
        )
        return [ModerationCase.from_row(r) for r in rows]

    # ------------------------------------------------------------------ #
    # Cases — Write                                                        #
    # ------------------------------------------------------------------ #

    async def create_case(
        self,
        guild_id: int,
        target_id: int,
        moderator_id: int,
        case_type: CaseType,
        reason: Optional[str] = None,
        duration: Optional[int] = None,
        target_username: str = "",
        moderator_username: str = "",
    ) -> ModerationCase:
        """
        Insert a new moderation case.

        Args:
            guild_id:           Discord snowflake ID of the guild.
            target_id:          Discord snowflake ID of the actioned user.
            moderator_id:       Discord snowflake ID of the acting moderator.
            case_type:          The type of moderation action.
            reason:             Human-readable reason (optional).
            duration:           Timeout duration in seconds (optional).
            target_username:    Cached display name of the target.
            moderator_username: Cached display name of the moderator.

        Returns:
            The newly created ModerationCase with its assigned ID.
        """
        cursor = await self._db.execute(
            """
            INSERT INTO moderation_cases
                (guild_id, target_id, target_username, moderator_id,
                 moderator_username, case_type, reason, duration)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                guild_id,
                target_id,
                target_username,
                moderator_id,
                moderator_username,
                case_type.value,
                reason,
                duration,
            ),
        )
        case = await self.get_case(cursor.lastrowid, guild_id)
        assert case is not None
        log.info(
            "Moderation case #%d created: %s on user %d in guild %d",
            case.id,
            case_type.value,
            target_id,
            guild_id,
        )
        return case

    async def update_case(self, case: ModerationCase) -> None:
        """
        Persist changes to an existing case (e.g. add a note, mark resolved).

        Args:
            case: A modified ModerationCase instance.
        """
        await self._db.execute(
            """
            UPDATE moderation_cases SET
                reason     = ?,
                resolved   = ?,
                note       = ?,
                updated_at = datetime('now')
            WHERE id = ? AND guild_id = ?
            """,
            (case.reason, int(case.resolved), case.note, case.id, case.guild_id),
        )

    # ------------------------------------------------------------------ #
    # Warnings — Read                                                      #
    # ------------------------------------------------------------------ #

    async def get_warnings_for_user(
        self,
        guild_id: int,
        user_id: int,
    ) -> list[Warning]:
        """
        Return all warnings for a user in a guild.

        Args:
            guild_id: Discord snowflake ID of the guild.
            user_id:  Discord snowflake ID of the warned user.

        Returns:
            List of Warning instances (newest first).
        """
        rows = await self._db.fetch_all(
            """
            SELECT * FROM warnings
            WHERE guild_id = ? AND user_id = ?
            ORDER BY created_at DESC
            """,
            (guild_id, user_id),
        )
        return [Warning.from_row(r) for r in rows]

    async def get_active_warn_count(self, guild_id: int, user_id: int) -> int:
        """
        Count unpardoned warnings for a user in a guild.

        Args:
            guild_id: Discord snowflake ID of the guild.
            user_id:  Discord snowflake ID of the user.

        Returns:
            Integer count of active (unpardoned) warnings.
        """
        row = await self._db.fetch_one(
            """
            SELECT COUNT(*) AS cnt FROM warnings
            WHERE guild_id = ? AND user_id = ? AND pardoned = 0
            """,
            (guild_id, user_id),
        )
        return row["cnt"] if row else 0

    # ------------------------------------------------------------------ #
    # Warnings — Write                                                     #
    # ------------------------------------------------------------------ #

    async def create_warning(self, case: ModerationCase) -> Warning:
        """
        Insert a warning record linked to a case.

        Args:
            case: The ModerationCase (must be of type CaseType.WARN).

        Returns:
            The newly created Warning.
        """
        cursor = await self._db.execute(
            """
            INSERT INTO warnings (case_id, guild_id, user_id, reason)
            VALUES (?, ?, ?, ?)
            """,
            (case.id, case.guild_id, case.target_id, case.reason),
        )
        row = await self._db.fetch_one(
            "SELECT * FROM warnings WHERE id = ?",
            (cursor.lastrowid,),
        )
        assert row is not None
        return Warning.from_row(row)

    async def pardon_warning(self, warning_id: int, guild_id: int) -> None:
        """
        Mark a warning as pardoned.

        Pardoned warnings remain in the database for audit purposes but are
        excluded from active warn counts and threshold checks.

        Args:
            warning_id: The ID of the warning to pardon.
            guild_id:   Guild scope check.
        """
        await self._db.execute(
            "UPDATE warnings SET pardoned = 1 WHERE id = ? AND guild_id = ?",
            (warning_id, guild_id),
        )
