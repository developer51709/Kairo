"""
src/bot/components/modal.py
----------------------------
Modal Dialog Component

Modals are pop-up forms that collect text input from users. They are
triggered in response to a button or select menu interaction.

Discord API reference:
    Modal         — top-level response type (9)
    TextInput     — type: 4 (inside a modal)

Usage:
    modal = Modal(
        title="Report a User",
        custom_id="report:submit",
        inputs=[
            TextInput(
                label="Reason",
                custom_id="report:reason",
                placeholder="Describe the issue...",
                style=TextInputStyle.PARAGRAPH,
                max_length=1000,
            ),
        ],
    )
    await interaction.response.send_modal(modal.to_discord_modal())
"""

from __future__ import annotations

from enum import IntEnum
from typing import Any, Optional

import discord


class TextInputStyle(IntEnum):
    """
    Discord text input style.

    SHORT     — Single-line text field.
    PARAGRAPH — Multi-line text area.
    """
    SHORT     = 1
    PARAGRAPH = 2


class TextInput:
    """
    A single text field within a modal.

    Attributes:
        label       (str):              Label shown above the input.
        custom_id   (str):              Identifier for the value in the response.
        style       (TextInputStyle):   SHORT (one line) or PARAGRAPH (multi-line).
        placeholder (str | None):       Hint text shown when the field is empty.
        value       (str | None):       Pre-filled default value.
        required    (bool):             Whether the field must be filled.
        min_length  (int | None):       Minimum allowed input length.
        max_length  (int | None):       Maximum allowed input length.
    """

    def __init__(
        self,
        label: str,
        custom_id: str,
        style: TextInputStyle = TextInputStyle.SHORT,
        placeholder: Optional[str] = None,
        value: Optional[str] = None,
        required: bool = True,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
    ) -> None:
        self.label = label
        self.custom_id = custom_id
        self.style = style
        self.placeholder = placeholder
        self.value = value
        self.required = required
        self.min_length = min_length
        self.max_length = max_length

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": 4,
            "label": self.label,
            "custom_id": self.custom_id,
            "style": int(self.style),
            "required": self.required,
        }
        if self.placeholder:
            payload["placeholder"] = self.placeholder
        if self.value is not None:
            payload["value"] = self.value
        if self.min_length is not None:
            payload["min_length"] = self.min_length
        if self.max_length is not None:
            payload["max_length"] = self.max_length
        return payload


class Modal:
    """
    A modal dialog that collects text input from users.

    Modals are sent as interaction responses (not as messages). They can
    contain up to 5 TextInput components.

    Attributes:
        title     (str):             Title bar text of the modal (max 45 chars).
        custom_id (str):             Identifier for the modal submission interaction.
        inputs    (list[TextInput]): Text fields shown in the modal.
    """

    def __init__(
        self,
        title: str,
        custom_id: str,
        inputs: list[TextInput],
    ) -> None:
        if len(inputs) > 5:
            raise ValueError("A modal can contain at most 5 TextInput components.")
        self.title = title
        self.custom_id = custom_id
        self.inputs = inputs

    def to_discord_modal(self) -> discord.ui.Modal:
        """
        Build a discord.py Modal object from this Kairo Modal.

        Returns:
            A discord.ui.Modal instance that can be passed to
            interaction.response.send_modal().

        Note:
            This method dynamically builds the discord.py modal. The
            returned modal does not have an on_submit handler — you are
            expected to subclass KairoModal (below) for handler logic.
        """
        # Build a dynamic discord.ui.Modal subclass with the given fields.
        fields: dict[str, discord.ui.TextInput] = {}
        for inp in self.inputs:
            fields[inp.custom_id] = discord.ui.TextInput(
                label=inp.label,
                custom_id=inp.custom_id,
                style=discord.TextStyle.short if inp.style == TextInputStyle.SHORT else discord.TextStyle.paragraph,
                placeholder=inp.placeholder,
                default=inp.value,
                required=inp.required,
                min_length=inp.min_length,
                max_length=inp.max_length,
            )

        # Dynamically create a discord.ui.Modal subclass
        modal_cls = type(
            "DynamicModal",
            (discord.ui.Modal,),
            {**fields, "title": self.title},
        )
        return modal_cls(title=self.title, custom_id=self.custom_id)
