"""
src/bot/database/repositories/__init__.py
------------------------------------------
Kairo Repository Package

Repositories are the only layer of the application that writes SQL.
Each repository class is responsible for one domain entity and exposes
typed async methods (get, create, update, delete, list).

Feature cogs and services receive repository instances via dependency
injection through the Database object on KairoBot.

Available repositories:
    GuildRepository       — CRUD for guild configuration
    UserRepository        — CRUD for per-guild user records
    ModerationRepository  — CRUD for moderation cases and warnings
"""

from .guild import GuildRepository
from .user import UserRepository
from .moderation import ModerationRepository
from .automod import AutoModRepository

__all__ = [
    "GuildRepository",
    "UserRepository",
    "ModerationRepository",
    "AutoModRepository",
]
