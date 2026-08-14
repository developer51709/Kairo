"""
src/bot/components/interactive.py
-----------------------------------
Interactive Components — re-exported from discord.ui

Buttons, select menus, action rows, and thumbnails are all provided
natively by discord.py 2.6+.
Import directly from discord.ui in new code; this module
exists only as a compatibility shim during the transition.
"""

from discord.ui import (  # noqa: F401
    Button,
    Select,
    UserSelect,
    RoleSelect,
    ChannelSelect,
    MentionableSelect,
    ActionRow,
    Thumbnail,
)
from discord import ButtonStyle  # noqa: F401

__all__ = [
    "Button",
    "Select",
    "UserSelect",
    "RoleSelect",
    "ChannelSelect",
    "MentionableSelect",
    "ActionRow",
    "Thumbnail",
    "ButtonStyle",
]
