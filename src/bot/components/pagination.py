"""
src/bot/components/pagination.py
----------------------------------
Paginator Component

Provides a reusable multi-page interface using Components V2.
Useful for displaying long lists (moderation cases, warnings, leaderboards)
that do not fit in a single message.

The Paginator manages page state and builds Previous/Next buttons
automatically. Page content is provided by a callable that receives the
current page number and returns a list of KairoComponent objects.

Usage:
    async def build_page(page: int, total_pages: int) -> list[KairoComponent]:
        cases = cases_on_page[page]
        return [
            Text(f"## Moderation Cases — Page {page + 1}/{total_pages}"),
            Separator(),
            *[Text(f"**Case #{c.id}** — {c.case_type.value}") for c in cases],
        ]

    paginator = Paginator(
        items=all_cases,
        page_size=5,
        build_page=build_page,
        custom_id_prefix="modcases",
    )
    await paginator.send(interaction)
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Generic, TypeVar

import discord

from .container import Container
from .interactive import ActionRow, Button, ButtonStyle
from .text import Text, Separator

T = TypeVar("T")


class Paginator(Generic[T]):
    """
    A multi-page interactive interface.

    Attributes:
        items            (list[T]):            Full list of items to paginate.
        page_size        (int):                Number of items per page.
        build_page       (callable):           Async function that builds page content.
        custom_id_prefix (str):                Prefix for button custom_ids.
        current_page     (int):                Currently displayed page (0-indexed).
    """

    def __init__(
        self,
        items: list[T],
        page_size: int,
        build_page: Callable[[list[T], int, int], Awaitable[list[Any]]],
        custom_id_prefix: str = "paginator",
    ) -> None:
        """
        Args:
            items:            The full dataset to paginate.
            page_size:        Number of items to show per page.
            build_page:       Async callable(page_items, page_num, total_pages)
                              that returns a list of KairoComponent objects.
            custom_id_prefix: Prefix used to build unique button custom_ids.
                              Should be unique per paginator instance to avoid
                              conflicts in multi-paginator messages.
        """
        self.items = items
        self.page_size = page_size
        self.build_page = build_page
        self.custom_id_prefix = custom_id_prefix
        self.current_page = 0

    @property
    def total_pages(self) -> int:
        """Total number of pages (minimum 1)."""
        return max(1, -(-len(self.items) // self.page_size))  # ceil division

    @property
    def page_items(self) -> list[T]:
        """Items for the current page."""
        start = self.current_page * self.page_size
        return self.items[start : start + self.page_size]

    async def build_container(self) -> Container:
        """
        Build the Container for the current page.

        Returns:
            A Container with page content and navigation buttons.
        """
        content = await self.build_page(self.page_items, self.current_page, self.total_pages)

        nav = ActionRow(
            Button(
                label="◀ Previous",
                custom_id=f"{self.custom_id_prefix}:prev",
                style=ButtonStyle.SECONDARY,
                disabled=self.current_page == 0,
            ),
            Button(
                label=f"Page {self.current_page + 1} / {self.total_pages}",
                custom_id=f"{self.custom_id_prefix}:page",
                style=ButtonStyle.SECONDARY,
                disabled=True,  # Info-only, not clickable
            ),
            Button(
                label="Next ▶",
                custom_id=f"{self.custom_id_prefix}:next",
                style=ButtonStyle.SECONDARY,
                disabled=self.current_page >= self.total_pages - 1,
            ),
        )

        return Container(*content, Separator(), nav)

    async def send(self, interaction: discord.Interaction) -> None:
        """
        Send the first page as an interaction response.

        Args:
            interaction: The discord.py Interaction to respond to.
        """
        container = await self.build_container()
        await interaction.response.send_message(
            components=[container.to_dict()],
            flags=discord.MessageFlags.is_components_v2,  # type: ignore[attr-defined]
        )

    def go_to(self, page: int) -> None:
        """
        Navigate to a specific page (clamped to valid range).

        Args:
            page: Target page number (0-indexed).
        """
        self.current_page = max(0, min(page, self.total_pages - 1))

    def next_page(self) -> None:
        """Advance to the next page, if one exists."""
        self.go_to(self.current_page + 1)

    def prev_page(self) -> None:
        """Go back to the previous page, if one exists."""
        self.go_to(self.current_page - 1)
