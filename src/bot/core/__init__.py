"""
src/bot/core/__init__.py
------------------------
Kairo Core Package

The core package provides the foundational infrastructure that all other
parts of Kairo depend on. It is intentionally kept minimal and free of
feature-specific logic.

Exports:
    KairoBot     — The main bot class (extends discord.ext.commands.Bot)
    Config       — Configuration loader and accessor
    get_logger   — Factory function for named loggers
    EventBus     — Internal pub/sub event dispatcher
"""

from .bot import KairoBot
from .config import Config
from .logging import get_logger
from .events import EventBus

__all__ = [
    "KairoBot",
    "Config",
    "get_logger",
    "EventBus",
]
