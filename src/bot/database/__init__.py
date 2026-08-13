"""
src/bot/database/__init__.py
-----------------------------
Kairo Database Package

Provides the database connection, models (table definitions), repositories
(typed data access), and migration system.

All database interaction in Kairo flows through repository classes. Feature
cogs should never import sqlite3 or write raw SQL — they call repository
methods instead. This keeps SQL centralised, testable, and easy to audit.

Package layout:
    connection.py     — SQLite connection pool and async wrapper
    models/           — Table schema definitions (not an ORM, just constants + dataclasses)
    repositories/     — One repository class per domain entity
    migrations/       — Ordered SQL migration files and migration runner

Exports:
    Database          — Async database wrapper (the main entry point)
"""

from .connection import Database

__all__ = ["Database"]
