"""
src/bot/components/panel.py
-----------------------------
Layout View Send Helpers

Thin wrappers around discord.ui.LayoutView that handle the ephemeral flag
and the three sending modes (interaction response, followup, channel message).

Rather than constructing raw payloads, Kairo now passes LayoutView subclasses
directly to discord.py — which is the correct CV2 API.

Usage:
    view = discord.ui.LayoutView()
    view.add_item(discord.ui.Container(
        discord.ui.TextDisplay("# Hello"),
    ))
    await send_layout(interaction, view, ephemeral=True)
"""

from __future__ import annotations

from typing import Optional

import discord

from ..core.logging import get_logger

log = get_logger(__name__)


async def send_layout(
    interaction: discord.Interaction,
    view: discord.ui.LayoutView,
    *,
    ephemeral: bool = False,
    allowed_mentions: discord.AllowedMentions = discord.AllowedMentions.none(),
) -> None:
    """
    Send a LayoutView as the primary response to a slash-command interaction.

    Must be called before any other response method on the interaction.

    Args:
        interaction: The discord.Interaction to respond to.
        view:        A populated discord.ui.LayoutView instance.
        ephemeral:   If True the message is only visible to the invoker.
    """
    await interaction.response.send_message(view=view, ephemeral=ephemeral, allowed_mentions=allowed_mentions)
    log.debug("LayoutView sent as interaction response (ephemeral=%s).", ephemeral)


async def edit_layout(
    interaction: discord.Interaction,
    view: discord.ui.LayoutView,
    allowed_mentions: discord.AllowedMentions = discord.AllowedMentions.none(),
) -> None:
    """
    Edit the original interaction response with a new LayoutView.

    Use this when handling button/select interactions to update the message.

    Args:
        interaction: The component interaction to respond to.
        view:        The new LayoutView to replace the current message with.
    """
    await interaction.response.edit_message(view=view, allowed_mentions=allowed_mentions)
    log.debug("LayoutView used to edit interaction response.")


async def followup_layout(
    interaction: discord.Interaction,
    view: discord.ui.LayoutView,
    *,
    ephemeral: bool = False,
) -> None:
    """
    Send a LayoutView as a followup after an already-responded interaction.

    Args:
        interaction: The interaction whose followup webhook to use.
        view:        A populated discord.ui.LayoutView instance.
        ephemeral:   If True the followup is only visible to the invoker.
    """
    await interaction.followup.send(view=view, ephemeral=ephemeral)
    log.debug("LayoutView sent as interaction followup (ephemeral=%s).", ephemeral)


async def send_layout_to_channel(
    channel: discord.abc.Messageable,
    view: discord.ui.LayoutView,
) -> discord.Message:
    """
    Send a LayoutView as a proactive channel message (not an interaction response).

    Use this for mod-log entries, welcome messages, and other bot-initiated
    messages that are not triggered by a slash command.

    Args:
        channel: Any messageable Discord channel.
        view:    A populated discord.ui.LayoutView instance.

    Returns:
        The sent discord.Message.
    """
    message = await channel.send(view=view)
    log.debug("LayoutView sent to channel %r.", channel)
    return message
