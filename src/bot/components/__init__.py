"""
src/bot/components/__init__.py
-------------------------------
Kairo Components Package

Provides high-level, reusable abstractions over Discord Components V2.
Rather than constructing raw discord.py component objects everywhere,
Kairo features use this package to build consistent, styled interfaces.

This abstraction layer serves two purposes:
    1. Consistency — all interactive UIs share the same style and behaviour.
    2. Simplicity   — feature cogs describe *what* to show, not *how* to build it.

Components V2 context:
    Discord Components V2 allows sending messages composed of structured
    component objects (containers, sections, buttons, etc.) instead of
    traditional embeds. It requires the IS_COMPONENTS_V2 message flag (1 << 15)
    and is only available in bots with the required access level.

Package layout:
    base.py       — Base class and shared utilities
    container.py  — Container and layout components
    text.py       — Text display components
    interactive.py— Buttons, select menus, and action rows
    modal.py      — Modal dialog builder
    pagination.py — Multi-page interface helper
    panel.py      — High-level panel builder (the main entry point)

Quick example:
    from src.bot.components import Panel, Container, Text, Separator, Button, ActionRow

    panel = Panel(
        Container(
            Text("# Server Configuration"),
            Separator(),
            Text("Manage your server settings below."),
            ActionRow(
                Button(label="Moderation", custom_id="config:moderation"),
                Button(label="Logging", custom_id="config:logging"),
            ),
        )
    )
    await panel.send(interaction)

See docs/components.md for full documentation.
"""

from .panel import Panel
from .container import Container, Section
from .text import Text, Separator
from .interactive import Button, ButtonStyle, SelectMenu, ActionRow
from .modal import Modal, TextInput
from .pagination import Paginator

__all__ = [
    "Panel",
    "Container",
    "Section",
    "Text",
    "Separator",
    "Button",
    "ButtonStyle",
    "SelectMenu",
    "ActionRow",
    "Modal",
    "TextInput",
    "Paginator",
]
