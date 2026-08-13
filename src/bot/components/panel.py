"""
src/bot/components/panel.py
-----------------------------
Panel — High-Level Interface Builder

Panel is the main entry point for building and sending Components V2
interfaces. It wraps one or more Containers and handles sending the
message with the correct Discord flags.

Think of a Panel as the entire message — it owns the containers and
knows how to send, edit, or defer-update an interaction.

Usage:
    panel = Panel(
        Container(
            Text("# Server Configuration"),
            Separator(),
            Text("Choose a category to configure."),
            ActionRow(
                Button(label="Moderation", custom_id="config:moderation"),
                Button(label="AutoMod", custom_id="config:automod"),
                Button(label="Logging", custom_id="config:logging"),
            ),
        )
    )

    # Send as an interaction response:
    await panel.send(interaction)

    # Edit an existing interaction response:
    await panel.edit(interaction)

    # Send as a regular channel message:
    await panel.send_to_channel(channel)
"""

from __future__ import annotations

from typing import Optional

import discord

from .container import Container
from ..core.logging import get_logger

log = get_logger(__name__)

# Discord message flag: IS_COMPONENTS_V2 (1 << 15)
_COMPONENTS_V2_FLAG = 1 << 15


class Panel:
    """
    A complete Components V2 message panel.

    A Panel wraps one or more Container components and manages sending
    them to Discord with the required message flags.

    Attributes:
        containers (list[Container]):  The top-level containers in this panel.
        ephemeral  (bool):             Whether the panel is visible only to the invoker.
    """

    def __init__(
        self,
        *containers: Container,
        ephemeral: bool = False,
    ) -> None:
        """
        Args:
            *containers: One or more Container objects to include in the panel.
            ephemeral:   If True, the message is only visible to the user who triggered it.
        """
        if not containers:
            raise ValueError("A Panel must contain at least one Container.")
        self.containers: list[Container] = list(containers)
        self.ephemeral: bool = ephemeral

    def add(self, container: Container) -> Panel:
        """
        Append a container to this panel.

        Returns self for chaining.
        """
        self.containers.append(container)
        return self

    def _build_payload(self) -> list[dict]:
        """Build the component payload list for Discord."""
        return [c.to_dict() for c in self.containers]

    # ------------------------------------------------------------------ #
    # Sending                                                              #
    # ------------------------------------------------------------------ #

    async def send(self, interaction: discord.Interaction) -> None:
        """
        Send this panel as the primary response to an interaction.

        Must be called before any other response is sent for the interaction.

        Args:
            interaction: The discord.Interaction to respond to.
        """
        flags = discord.MessageFlags._from_value(_COMPONENTS_V2_FLAG)  # type: ignore[attr-defined]
        if self.ephemeral:
            flags.value |= 1 << 6  # EPHEMERAL flag

        await interaction.response.send_message(
            components=self._build_payload(),
            flags=flags,
        )
        log.debug(
            "Panel sent as interaction response (ephemeral=%s, containers=%d).",
            self.ephemeral,
            len(self.containers),
        )

    async def edit(self, interaction: discord.Interaction) -> None:
        """
        Edit the original interaction response with this panel.

        Use this when handling button or select-menu interactions to update
        the existing message in place.

        Args:
            interaction: The component interaction to respond to.
        """
        await interaction.response.edit_message(
            components=self._build_payload(),
        )
        log.debug(
            "Panel used to edit interaction response (containers=%d).",
            len(self.containers),
        )

    async def followup(self, interaction: discord.Interaction) -> None:
        """
        Send this panel as a followup to an already-responded interaction.

        Use this after you have already sent a response (e.g. deferred) and
        want to send additional message(s).

        Args:
            interaction: The interaction whose followup webhook to use.
        """
        flags = _COMPONENTS_V2_FLAG
        if self.ephemeral:
            flags |= 1 << 6

        await interaction.followup.send(
            components=self._build_payload(),
            flags=flags,
        )

    async def send_to_channel(
        self,
        channel: discord.abc.Messageable,
    ) -> discord.Message:
        """
        Send this panel as a regular message to a channel.

        This is not an interaction response — use it for proactive messages
        such as mod-log entries or welcome messages.

        Args:
            channel: Any messageable Discord channel.

        Returns:
            The sent discord.Message object.
        """
        return await channel.send(
            components=self._build_payload(),
            flags=_COMPONENTS_V2_FLAG,
        )
