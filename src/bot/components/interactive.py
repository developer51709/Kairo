"""
src/bot/components/interactive.py
-----------------------------------
Interactive Components — Buttons, Select Menus, Action Rows

Interactive components accept user input. They must be placed inside
an ActionRow, and ActionRows must be inside a Container.

Discord API references:
    ActionRow   — type: 1
    Button      — type: 2
    SelectMenu  — type: 3 (string), 5 (user), 6 (role), 7 (mentionable), 8 (channel)

Usage:
    ActionRow(
        Button(label="Approve", custom_id="mod:approve", style=ButtonStyle.SUCCESS),
        Button(label="Deny", custom_id="mod:deny", style=ButtonStyle.DANGER),
    )

    ActionRow(
        SelectMenu(
            custom_id="config:feature",
            placeholder="Select a feature...",
            options=[
                SelectOption(label="Moderation", value="moderation"),
                SelectOption(label="AutoMod", value="automod"),
            ],
        )
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Optional

from .base import KairoComponent


class ButtonStyle(IntEnum):
    """
    Discord button style values.

    PRIMARY   — Blue. Use for the main action.
    SECONDARY — Grey. Use for secondary or neutral actions.
    SUCCESS   — Green. Use for confirmations or positive actions.
    DANGER    — Red. Use for destructive or irreversible actions.
    LINK      — Grey link button that opens a URL (no custom_id).
    PREMIUM   — Premium subscription upsell button.
    """
    PRIMARY   = 1
    SECONDARY = 2
    SUCCESS   = 3
    DANGER    = 4
    LINK      = 5
    PREMIUM   = 6


class Button(KairoComponent):
    """
    A clickable button component.

    Buttons trigger interactions that your bot handles via on_interaction
    or app_commands interaction checks.

    Attributes:
        label      (str):              Visible button label (max 80 chars).
        custom_id  (str | None):       Identifier sent with the interaction.
                                       Required for all styles except LINK.
        style      (ButtonStyle):      Visual style of the button.
        url        (str | None):       URL for LINK-style buttons.
        emoji      (str | None):       Optional emoji shown before the label.
        disabled   (bool):             Whether the button is non-interactive.
    """

    def __init__(
        self,
        label: str,
        custom_id: Optional[str] = None,
        style: ButtonStyle = ButtonStyle.SECONDARY,
        url: Optional[str] = None,
        emoji: Optional[str] = None,
        disabled: bool = False,
    ) -> None:
        if style != ButtonStyle.LINK and not custom_id:
            raise ValueError("Button requires a custom_id unless style is ButtonStyle.LINK.")
        if style == ButtonStyle.LINK and not url:
            raise ValueError("LINK-style Button requires a url.")

        self.label: str = label
        self.custom_id: Optional[str] = custom_id
        self.style: ButtonStyle = style
        self.url: Optional[str] = url
        self.emoji: Optional[str] = emoji
        self.disabled: bool = disabled

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": 2,
            "style": int(self.style),
            "label": self.label,
            "disabled": self.disabled,
        }
        if self.custom_id:
            payload["custom_id"] = self.custom_id
        if self.url:
            payload["url"] = self.url
        if self.emoji:
            # Support both Unicode emoji strings and custom emoji notation
            payload["emoji"] = {"name": self.emoji}
        return payload


@dataclass
class SelectOption:
    """
    A single option in a SelectMenu.

    Attributes:
        label       (str):         Visible option label.
        value       (str):         Value sent with the interaction.
        description (str | None):  Short description shown below the label.
        emoji       (str | None):  Optional emoji shown before the label.
        default     (bool):        Whether this option is pre-selected.
    """
    label: str
    value: str
    description: Optional[str] = None
    emoji: Optional[str] = None
    default: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"label": self.label, "value": self.value}
        if self.description:
            payload["description"] = self.description
        if self.emoji:
            payload["emoji"] = {"name": self.emoji}
        if self.default:
            payload["default"] = True
        return payload


class SelectMenu(KairoComponent):
    """
    A dropdown select menu component.

    Attributes:
        custom_id   (str):                  Identifier sent with the interaction.
        options     (list[SelectOption]):   Options presented to the user.
        placeholder (str | None):          Hint text shown when nothing is selected.
        min_values  (int):                  Minimum number of selections required.
        max_values  (int):                  Maximum number of selections allowed.
        disabled    (bool):                 Whether the menu is non-interactive.
    """

    def __init__(
        self,
        custom_id: str,
        options: list[SelectOption],
        placeholder: Optional[str] = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
    ) -> None:
        self.custom_id: str = custom_id
        self.options: list[SelectOption] = options
        self.placeholder: Optional[str] = placeholder
        self.min_values: int = min_values
        self.max_values: int = max_values
        self.disabled: bool = disabled

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": 3,  # String select
            "custom_id": self.custom_id,
            "options": [o.to_dict() for o in self.options],
            "min_values": self.min_values,
            "max_values": self.max_values,
            "disabled": self.disabled,
        }
        if self.placeholder:
            payload["placeholder"] = self.placeholder
        return payload


class ActionRow(KairoComponent):
    """
    An action row that holds interactive components (buttons or a select menu).

    Discord limits:
        - An ActionRow can hold up to 5 buttons OR 1 select menu.
        - A message can have up to 5 ActionRows.

    Attributes:
        components (list[KairoComponent]): Buttons or a single SelectMenu.
    """

    def __init__(self, *components: KairoComponent) -> None:
        self.components: list[KairoComponent] = list(components)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": 1,
            "components": [c.to_dict() for c in self.components],
        }
