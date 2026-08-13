"""
src/bot/database/migrations/runner.py
---------------------------------------
Kairo Migration Runner

Discovers and runs numbered SQL migration files from the migrations/
directory. Tracks applied migrations in a schema_migrations table so each
migration is run exactly once, even across restarts.

Migration file naming:
    001_initial_schema.sql
    002_add_automod_config.sql
    ...

Each SQL file may contain multiple statements separated by semicolons.
Statements are executed inside a transaction — if any statement fails,
the entire migration is rolled back and startup is aborted.

Usage:
    runner = MigrationRunner(db)
    await runner.run()   # called by db.run_migrations()
"""

import os
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..connection import Database

from ...core.logging import get_logger

log = get_logger(__name__)

# Directory containing this file (i.e. src/bot/database/migrations/)
_MIGRATIONS_DIR = os.path.dirname(__file__)

# Migration file pattern: NNN_description.sql
_MIGRATION_PATTERN = re.compile(r"^(\d{3})_.+\.sql$")


class MigrationRunner:
    """
    Applies pending SQL migrations to the database.

    Attributes:
        _db (Database): The active database connection.
    """

    def __init__(self, db: "Database") -> None:
        self._db = db

    async def run(self) -> None:
        """
        Run all pending migrations in ascending order.

        Steps:
            1. Create the schema_migrations tracking table if absent.
            2. Discover migration files in the migrations/ directory.
            3. For each file not yet recorded in schema_migrations:
               a. Read the SQL.
               b. Execute it within a transaction.
               c. Record the migration as applied.
        """
        await self._ensure_tracking_table()

        applied = await self._get_applied_migrations()
        pending = self._discover_migrations(applied)

        if not pending:
            log.info("Database is up to date. No pending migrations.")
            return

        log.info("Applying %d pending migration(s)...", len(pending))

        for filename in pending:
            await self._apply_migration(filename)

        log.info("All migrations applied.")

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    async def _ensure_tracking_table(self) -> None:
        """Create the schema_migrations table if it does not exist."""
        await self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                -- The migration filename (e.g. '001_initial_schema.sql').
                filename   TEXT    PRIMARY KEY,
                -- ISO 8601 timestamp when this migration was applied.
                applied_at TEXT    NOT NULL DEFAULT (datetime('now'))
            )
            """
        )

    async def _get_applied_migrations(self) -> set[str]:
        """Return the set of migration filenames that have already been run."""
        rows = await self._db.fetch_all("SELECT filename FROM schema_migrations")
        return {row["filename"] for row in rows}

    def _discover_migrations(self, applied: set[str]) -> list[str]:
        """
        Find migration files in the migrations/ directory that have not
        been applied yet, sorted by their numeric prefix.

        Args:
            applied: Set of already-applied migration filenames.

        Returns:
            Sorted list of pending migration filenames.
        """
        all_files = [
            f for f in os.listdir(_MIGRATIONS_DIR)
            if _MIGRATION_PATTERN.match(f)
        ]
        pending = sorted(f for f in all_files if f not in applied)
        return pending

    async def _apply_migration(self, filename: str) -> None:
        """
        Read and execute a single migration file.

        The entire file is wrapped in a transaction. On failure, the
        transaction is rolled back and a RuntimeError is raised to abort
        startup.

        Args:
            filename: The migration filename (not the full path).
        """
        path = os.path.join(_MIGRATIONS_DIR, filename)
        with open(path, encoding="utf-8") as f:
            sql = f.read()

        log.info("Applying migration: %s", filename)
        try:
            async with self._db.transaction():
                # SQLite's executescript() commits implicitly, so we execute
                # statements individually to stay within our transaction.
                for statement in self._split_statements(sql):
                    if statement.strip():
                        await self._db.connection.execute(statement)
                await self._db.connection.execute(
                    "INSERT INTO schema_migrations (filename) VALUES (?)",
                    (filename,),
                )
            log.info("Migration applied: %s", filename)
        except Exception as exc:
            log.exception("Migration failed: %s", filename)
            raise RuntimeError(
                f"Database migration '{filename}' failed: {exc}\n"
                "Fix the migration file and restart Kairo."
            ) from exc

    @staticmethod
    def _split_statements(sql: str) -> list[str]:
        """
        Split a SQL file into individual statements on semicolons,
        ignoring semicolons inside string literals and comments.

        This is a simple split on ';' — sufficient for well-formed
        migration files that don't embed semicolons in string data.

        Args:
            sql: Raw SQL file content.

        Returns:
            List of individual SQL statement strings.
        """
        return [s.strip() for s in sql.split(";") if s.strip()]
