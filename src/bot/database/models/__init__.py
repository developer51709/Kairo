"""
src/bot/database/models/__init__.py
------------------------------------
Kairo Database Models

This package defines the data shapes (Python dataclasses) and SQL schema
strings for each table in the Kairo database.

These are not an ORM. There is no magic mapping layer — models are plain
Python dataclasses used for type safety and IDE completion. Repository
classes handle the actual SQL.

Exports:
    GuildConfig   — Per-guild configuration record
    UserRecord    — Per-user (per-guild) record
    ModerationCase — A single moderation action (ban, kick, warn, etc.)
    Warning       — A single warning entry linked to a case
"""

from .guild import GuildConfig
from .user import UserRecord
from .moderation import ModerationCase, Warning

__all__ = [
    "GuildConfig",
    "UserRecord",
    "ModerationCase",
    "Warning",
]
