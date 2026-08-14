"""
src/bot/components/__init__.py
-------------------------------
Kairo Components Package

All CV2 components are provided directly by discord.py 2.6+.
This package re-exports them from discord.ui so the rest of Kairo
can import from one consistent location, and adds Kairo-specific
send helpers.

CV2 Component Types:
    discord.ui.LayoutView  — Top-level view, passed as ``view=`` to send_message.
    discord.ui.Container   — Top-level layout block (can nest all other CV2 items).
    discord.ui.Section     — Content group with a required accessory (Button/Thumbnail).
    discord.ui.TextDisplay — Markdown text content.
    discord.ui.Separator   — Visual spacing or divider line.
    discord.ui.Thumbnail   — Image accessory, used inside Section.
    discord.ui.ActionRow   — Holds buttons or a single select menu.
    discord.ui.Button      — Clickable button.
    discord.ui.Select      — String select dropdown.
    discord.SeparatorSpacing — Enum: small / large spacing for Separator.

Kairo Helpers:
    send_layout            — Send a LayoutView as an interaction response.
    edit_layout            — Edit an existing interaction response with a LayoutView.
    followup_layout        — Send a LayoutView as an interaction followup.
    send_layout_to_channel — Send a LayoutView as a proactive channel message.
    Paginator              — Multi-page LayoutView with Previous/Next buttons.

Quick example:
    import discord
    from src.bot.components import send_layout

    view = discord.ui.LayoutView()
    view.add_item(discord.ui.Container(
        discord.ui.TextDisplay("# Server Configuration"),
        discord.ui.Separator(visible=True),
        discord.ui.TextDisplay("Manage your server settings below."),
    ))
    await send_layout(interaction, view, ephemeral=True)

See docs/components.md for full documentation.
"""

# Native discord.py CV2 types — re-exported for convenient imports.
from discord.ui import (
    LayoutView,
    Container,
    Section,
    TextDisplay,
    Separator,
    Thumbnail,
    ActionRow,
    Button,
    Select,
    UserSelect,
    RoleSelect,
    ChannelSelect,
    MentionableSelect,
    Modal,
    TextInput,
)
from discord import ButtonStyle, SeparatorSpacing

# Kairo helpers
from .panel import (
    send_layout,
    edit_layout,
    followup_layout,
    send_layout_to_channel,
)
from .pagination import Paginator
from .confirmation import ConfirmationDialog, ConfirmationView
from .flow import MultiStepFlow, Step, StepBuilder
from .config_panel import (
    ConfigPanel,
    QuickConfigPanel,
    ConfigOption,
    ToggleOption,
    TextOption,
    NumberOption,
    ChannelOption,
    RoleOption,
    SelectOption,
    ConfigSection,
)

__all__ = [
    # discord.ui CV2 types
    "LayoutView",
    "Container",
    "Section",
    "TextDisplay",
    "Separator",
    "Thumbnail",
    "ActionRow",
    "Button",
    "Select",
    "UserSelect",
    "RoleSelect",
    "ChannelSelect",
    "MentionableSelect",
    "Modal",
    "TextInput",
    "ButtonStyle",
    "SeparatorSpacing",
    # Kairo send helpers
    "send_layout",
    "edit_layout",
    "followup_layout",
    "send_layout_to_channel",
    "Paginator",
    # Kairo component helpers
    "ConfirmationDialog",
    "ConfirmationView",
    "MultiStepFlow",
    "Step",
    "StepBuilder",
    # Configuration panel
    "ConfigPanel",
    "QuickConfigPanel",
    "ConfigOption",
    "ToggleOption",
    "TextOption",
    "NumberOption",
    "ChannelOption",
    "RoleOption",
    "SelectOption",
    "ConfigSection",
]
