"""
src/bot/components/pagination.py
----------------------------------
Pagination Helper

A simple paginator built on discord.ui.LayoutView and discord.ui.Button.

Usage:
    pages = [
        discord.ui.Container(discord.ui.TextDisplay("Page 1 content")),
        discord.ui.Container(discord.ui.TextDisplay("Page 2 content")),
    ]
    view = Paginator(pages, ephemeral=True)
    await interaction.response.send_message(view=view, ephemeral=True)
"""

from __future__ import annotations

from typing import List

import discord


class Paginator(discord.ui.LayoutView):
    """
    A multi-page LayoutView with Previous / Next navigation buttons.

    Each page is a discord.ui.Container. The paginator wraps the current
    page in a parent Container that also holds the navigation ActionRow.

    Args:
        pages:    A list of Container objects, one per page.
        ephemeral: Whether the view was sent ephemerally (informational only).
        timeout:  Interaction timeout in seconds. Defaults to 120.
    """

    def __init__(
        self,
        pages: List[discord.ui.Container],
        *,
        ephemeral: bool = False,
        timeout: float = 120.0,
    ) -> None:
        super().__init__(timeout=timeout)
        if not pages:
            raise ValueError("Paginator requires at least one page.")

        self.pages = pages
        self.ephemeral = ephemeral
        self._index = 0

        # Navigation buttons
        self._prev = discord.ui.Button(
            label="← Previous",
            style=discord.ButtonStyle.secondary,
            custom_id="paginator:prev",
            disabled=True,
        )
        self._next = discord.ui.Button(
            label="Next →",
            style=discord.ButtonStyle.secondary,
            custom_id="paginator:next",
            disabled=len(pages) <= 1,
        )
        self._prev.callback = self._on_prev  # type: ignore[method-assign]
        self._next.callback = self._on_next  # type: ignore[method-assign]

        self._render()

    def _render(self) -> None:
        """Rebuild the view for the current page index."""
        self.clear_items()

        # Current page container
        self.add_item(self.pages[self._index])

        # Navigation row
        nav = discord.ui.ActionRow(self._prev, self._next)
        footer = discord.ui.Container(
            discord.ui.TextDisplay(
                f"Page {self._index + 1} of {len(self.pages)}"
            ),
            nav,
        )
        self.add_item(footer)

    async def _on_prev(self, interaction: discord.Interaction) -> None:
        self._index = max(0, self._index - 1)
        self._prev.disabled = self._index == 0
        self._next.disabled = self._index >= len(self.pages) - 1
        self._render()
        await interaction.response.edit_message(view=self)

    async def _on_next(self, interaction: discord.Interaction) -> None:
        self._index = min(len(self.pages) - 1, self._index + 1)
        self._prev.disabled = self._index == 0
        self._next.disabled = self._index >= len(self.pages) - 1
        self._render()
        await interaction.response.edit_message(view=self)
