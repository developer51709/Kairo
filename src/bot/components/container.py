"""
src/bot/components/container.py
---------------------------------
Container and Section Components

Containers are the top-level component that wraps all other components
in a Components V2 message. A message may contain one or more containers.

Sections group related content within a container and can optionally
include a thumbnail accessory on the right side.

Discord API references:
    Container — type: 17
    Section   — type: 9

Usage:
    container = Container(
        Text("Hello world"),
        Separator(),
        ActionRow(Button(label="Click me", custom_id="example")),
        accent_colour=0x5865F2,   # Discord blurple
    )

    section = Section(
        Text("User Info"),
        Text("Username: Alice"),
        thumbnail_url="https://cdn.discordapp.com/avatars/..."
    )
"""

from __future__ import annotations

from typing import Any, Optional

from .base import KairoComponent


class Container(KairoComponent):
    """
    A top-level container for Components V2 messages.

    A container groups components visually with an optional left-side
    accent colour bar. Discord renders containers as a distinct visual block.

    Attributes:
        children       (list[KairoComponent]): Nested components.
        accent_colour  (int | None):           Left accent bar colour as an integer (RGB).
        spoiler        (bool):                 Whether to hide the container behind a spoiler.
    """

    def __init__(
        self,
        *children: KairoComponent,
        accent_colour: Optional[int] = None,
        spoiler: bool = False,
    ) -> None:
        """
        Args:
            *children:     Components to include inside this container.
            accent_colour: Optional left-side accent bar colour (0xRRGGBB).
            spoiler:       If True, contents are hidden until revealed.
        """
        self.children: list[KairoComponent] = list(children)
        self.accent_colour: Optional[int] = accent_colour
        self.spoiler: bool = spoiler

    def add(self, *components: KairoComponent) -> Container:
        """
        Append one or more components to this container.

        Returns self for chaining.
        """
        self.children.extend(components)
        return self

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": 17,
            "components": [c.to_dict() for c in self.children],
        }
        if self.accent_colour is not None:
            payload["accent_color"] = self.accent_colour
        if self.spoiler:
            payload["spoiler"] = True
        return payload


class Section(KairoComponent):
    """
    A section groups related content inside a container.

    A section can have an optional thumbnail accessory (image) that
    Discord renders on the right side.

    Attributes:
        children      (list[KairoComponent]): Content components.
        thumbnail_url (str | None):           URL of the thumbnail image.
        thumbnail_alt (str):                  Alt text for the thumbnail.
    """

    def __init__(
        self,
        *children: KairoComponent,
        thumbnail_url: Optional[str] = None,
        thumbnail_alt: str = "",
    ) -> None:
        """
        Args:
            *children:     Components to include in this section.
            thumbnail_url: URL of a thumbnail image displayed on the right.
            thumbnail_alt: Accessibility alt text for the thumbnail.
        """
        self.children: list[KairoComponent] = list(children)
        self.thumbnail_url: Optional[str] = thumbnail_url
        self.thumbnail_alt: str = thumbnail_alt

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": 9,
            "components": [c.to_dict() for c in self.children],
        }
        if self.thumbnail_url:
            payload["accessory"] = {
                "type": 11,  # Thumbnail
                "media": {"url": self.thumbnail_url},
                "description": self.thumbnail_alt,
            }
        return payload
