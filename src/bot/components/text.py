"""
src/bot/components/text.py
---------------------------
Text and Separator Components

Text displays markdown-formatted content. Separators add visual spacing
between components.

Discord API references:
    Text Display — type: 10
    Separator    — type: 14

Usage:
    Text("# Header")
    Text("Regular paragraph with **bold** and `code`.")
    Separator()
    Separator(divider=True, spacing="large")
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from .base import KairoComponent


class Text(KairoComponent):
    """
    A text display component that renders markdown content.

    Discord renders this as formatted text (headings, bold, code, etc.)
    using standard Discord markdown rules.

    Attributes:
        content (str): The markdown text to display.
    """

    def __init__(self, content: str) -> None:
        """
        Args:
            content: Markdown-formatted text. Supports standard Discord markdown.
                     Use # for headings, ** for bold, ` for inline code, etc.
        """
        self.content: str = content

    def to_dict(self) -> dict[str, Any]:
        return {"type": 10, "content": self.content}


class Separator(KairoComponent):
    """
    A visual separator that adds spacing between components.

    Can optionally render as a horizontal divider line.

    Attributes:
        divider (bool):                       Render as a visible line.
        spacing (Literal["small", "large"]):  Vertical spacing size.
    """

    def __init__(
        self,
        divider: bool = False,
        spacing: Literal["small", "large"] = "small",
    ) -> None:
        """
        Args:
            divider: If True, renders as a visible horizontal rule.
            spacing: Controls the vertical space around the separator.
        """
        self.divider: bool = divider
        self.spacing: str = spacing

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": 14,
            "divider": self.divider,
            "spacing": self.spacing,
        }
