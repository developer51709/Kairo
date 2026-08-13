"""
src/bot/database/connection.py
------------------------------
Kairo Database Connection

Wraps aiosqlite to provide an async SQLite connection that can be shared
across the application. A single Database instance is created at startup
and stored on KairoBot; all repository classes receive it via dependency
injection.

Design decisions:
    - aiosqlite runs SQLite I/O in a background thread, keeping the
      asyncio event loop (and therefore the Discord gateway) unblocked.
    - Row factory is set to aiosqlite.Row so results can be accessed both
      by index and by column name (row["guild_id"] or row[0]).
    - WAL (Write-Ahead Log) mode is enabled for better concurrent read
      performance and resilience against crashes mid-write.
    - Foreign key enforcement is enabled at the connection level.

Usage:
    db = Database(path="data/kairo.db")
    await db.connect()

    async with db.transaction():
        await db.execute("INSERT INTO guilds (id) VALUES (?)", (guild_id,))

    await db.close()

The Database object also exposes the migration runner so startup only
needs to call db.run_migrations() once.
"""

import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Optional, Sequence

import aiosqlite

from ..core.logging import get_logger

log = get_logger(__name__)


class DatabaseError(Exception):
    """Raised when a database operation fails in a recoverable way."""


class Database:
    """
    Async SQLite wrapper for Kairo.

    Attributes:
        path (str): Path to the SQLite database file.
    """

    def __init__(self, path: str) -> None:
        """
        Initialise the database wrapper.

        Args:
            path: File path for the SQLite database.
                  The parent directory is created if it does not exist.
        """
        self.path = path
        self._connection: Optional[aiosqlite.Connection] = None

    # ------------------------------------------------------------------ #
    # Lifecycle                                                            #
    # ------------------------------------------------------------------ #

    async def connect(self) -> None:
        """
        Open the database connection and apply pragmas.

        Creates the database file and its parent directory if they do not
        exist yet. Should be called once during bot startup (in setup_hook).
        """
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        self._connection = await aiosqlite.connect(self.path)
        self._connection.row_factory = aiosqlite.Row

        # Performance and safety pragmas
        await self._connection.execute("PRAGMA journal_mode = WAL")
        await self._connection.execute("PRAGMA foreign_keys = ON")
        await self._connection.execute("PRAGMA synchronous = NORMAL")

        log.info("Database connected: %s", self.path)

    async def close(self) -> None:
        """Close the database connection gracefully."""
        if self._connection:
            await self._connection.close()
            self._connection = None
            log.info("Database connection closed.")

    @property
    def connection(self) -> aiosqlite.Connection:
        """Return the active connection, raising if not connected."""
        if self._connection is None:
            raise DatabaseError("Database is not connected. Call connect() first.")
        return self._connection

    # ------------------------------------------------------------------ #
    # Core query helpers                                                   #
    # ------------------------------------------------------------------ #

    async def execute(
        self,
        sql: str,
        parameters: Sequence[Any] = (),
    ) -> aiosqlite.Cursor:
        """
        Execute a single SQL statement.

        Use for INSERT, UPDATE, DELETE, or DDL statements.

        Args:
            sql:        Parameterised SQL string. Use '?' placeholders.
            parameters: Sequence of values to bind to the placeholders.

        Returns:
            The resulting cursor (useful for lastrowid on INSERT).
        """
        cursor = await self.connection.execute(sql, parameters)
        await self.connection.commit()
        return cursor

    async def execute_many(
        self,
        sql: str,
        parameters: Sequence[Sequence[Any]],
    ) -> None:
        """
        Execute a SQL statement with multiple parameter sets.

        Use for bulk INSERT / UPDATE operations.
        """
        await self.connection.executemany(sql, parameters)
        await self.connection.commit()

    async def fetch_one(
        self,
        sql: str,
        parameters: Sequence[Any] = (),
    ) -> Optional[aiosqlite.Row]:
        """
        Execute a query and return the first row, or None if no rows match.

        Args:
            sql:        SELECT statement with '?' placeholders.
            parameters: Bind parameters.

        Returns:
            An aiosqlite.Row (accessible by column name or index), or None.
        """
        async with self.connection.execute(sql, parameters) as cursor:
            return await cursor.fetchone()

    async def fetch_all(
        self,
        sql: str,
        parameters: Sequence[Any] = (),
    ) -> list[aiosqlite.Row]:
        """
        Execute a query and return all matching rows.

        Args:
            sql:        SELECT statement with '?' placeholders.
            parameters: Bind parameters.

        Returns:
            List of aiosqlite.Row objects (may be empty).
        """
        async with self.connection.execute(sql, parameters) as cursor:
            return await cursor.fetchall()

    # ------------------------------------------------------------------ #
    # Transaction                                                          #
    # ------------------------------------------------------------------ #

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        """
        Async context manager that wraps multiple statements in a transaction.

        If an exception is raised inside the block the transaction is rolled
        back; otherwise it is committed.

        Usage:
            async with db.transaction():
                await db.execute("INSERT INTO ...")
                await db.execute("UPDATE ...")
        """
        await self.connection.execute("BEGIN")
        try:
            yield
            await self.connection.commit()
        except Exception:
            await self.connection.rollback()
            raise

    # ------------------------------------------------------------------ #
    # Migrations                                                           #
    # ------------------------------------------------------------------ #

    async def run_migrations(self) -> None:
        """
        Run all pending database migrations.

        Delegates to the MigrationRunner which discovers migration files in
        src/bot/database/migrations/ and applies any that have not been run yet.
        """
        from .migrations.runner import MigrationRunner
        runner = MigrationRunner(self)
        await runner.run()
