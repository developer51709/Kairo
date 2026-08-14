"""
src/bot/components/confirmation.py
----------------------------------
Confirmation Dialog Helper

A reusable confirmation dialog built on discord.ui.LayoutView.

Provides a standard Yes/No confirmation pattern for destructive actions
or any operation that requires user confirmation before proceeding.

Usage:
    class DeleteMessageCog(commands.Cog):
        async def delete_callback(self, interaction: discord.Interaction) -> None:
            view = ConfirmationDialog(
                title="Delete Message",
                message="Are you sure you want to delete this message?",
                confirm_label="Delete",
                cancel_label="Cancel",
                confirm_style=discord.ButtonStyle.danger,
                timeout=60.0
            )
            
            # Wait for user decision
            confirmed = await view.wait_for_decision(interaction)
            if confirmed:
                await interaction.message.delete()
                await interaction.followup.send("Message deleted!", ephemeral=True)
            else:
                await interaction.followup.send("Delete cancelled.", ephemeral=True)
"""

from __future__ import annotations

from typing import Callable, Optional, Awaitable, Any

import discord

from ..core.logging import get_logger

log = get_logger(__name__)


class ConfirmationDialog(discord.ui.LayoutView):
    """
    A reusable confirmation dialog with Yes/No buttons.
    
    Creates a LayoutView with a title, message, and two buttons (Confirm/Cancel).
    The dialog waits for the user to click one of the buttons and returns the result.
    
    Args:
        title: Title displayed at the top of the dialog.
        message: The confirmation message.
        confirm_label: Text for the confirm button. Defaults to "Confirm".
        cancel_label: Text for the cancel button. Defaults to "Cancel".
        confirm_style: Button style for confirm button. Defaults to success (green).
        cancel_style: Button style for cancel button. Defaults to secondary (gray).
        timeout: Interaction timeout in seconds. Defaults to 120.
        ephemeral: Whether the dialog is ephemeral. Defaults to True.
        confirm_emoji: Optional emoji for confirm button.
        cancel_emoji: Optional emoji for cancel button.
    """
    
    def __init__(
        self,
        title: str,
        message: str,
        confirm_label: str = "Confirm",
        cancel_label: str = "Cancel",
        confirm_style: discord.ButtonStyle = discord.ButtonStyle.success,
        cancel_style: discord.ButtonStyle = discord.ButtonStyle.secondary,
        timeout: float = 120.0,
        ephemeral: bool = True,
        confirm_emoji: Optional[str] = None,
        cancel_emoji: Optional[str] = None,
    ) -> None:
        super().__init__(timeout=timeout)
        
        self.title = title
        self.message = message
        self.confirm_label = confirm_label
        self.cancel_label = cancel_label
        self.ephemeral = ephemeral
        
        # Result storage
        self._confirmed: Optional[bool] = None
        self._interaction: Optional[discord.Interaction] = None
        self._decision_event: Optional[asyncio.Event] = None
        
        # Create buttons
        self._confirm_button = discord.ui.Button(
            label=confirm_label,
            style=confirm_style,
            emoji=confirm_emoji,
            custom_id="confirmation:confirm",
        )
        self._cancel_button = discord.ui.Button(
            label=cancel_label,
            style=cancel_style,
            emoji=cancel_emoji,
            custom_id="confirmation:cancel",
        )
        
        # Set callbacks
        self._confirm_button.callback = self._on_confirm  # type: ignore[method-assign]
        self._cancel_button.callback = self._on_cancel  # type: ignore[method-assign]
        
        # Build the view
        self._render()
    
    def _render(self) -> None:
        """Render the dialog layout."""
        self.clear_items()
        
        # Title container
        title_container = discord.ui.Container(
            discord.ui.TextDisplay(f"# {self.title}"),
            discord.ui.Separator(visible=True),
        )
        self.add_item(title_container)
        
        # Message container
        message_container = discord.ui.Container(
            discord.ui.TextDisplay(self.message),
            discord.ui.Separator(visible=True),
        )
        self.add_item(message_container)
        
        # Button row
        button_row = discord.ui.ActionRow(
            self._cancel_button,
            self._confirm_button,
        )
        self.add_item(button_row)
    
    async def _on_confirm(self, interaction: discord.Interaction) -> None:
        """Handle confirm button click."""
        self._confirmed = True
        self._interaction = interaction
        
        # Disable buttons to prevent multiple clicks
        self._confirm_button.disabled = True
        self._cancel_button.disabled = True
        self._render()
        
        try:
            await interaction.response.edit_message(view=self)
        except discord.errors.InteractionResponded:
            # If already responded, try to edit the original message
            if hasattr(interaction, 'message') and interaction.message:
                await interaction.message.edit(view=self)
        
        # Signal that decision is made
        if self._decision_event:
            self._decision_event.set()
    
    async def _on_cancel(self, interaction: discord.Interaction) -> None:
        """Handle cancel button click."""
        self._confirmed = False
        self._interaction = interaction
        
        # Disable buttons to prevent multiple clicks
        self._confirm_button.disabled = True
        self._cancel_button.disabled = True
        self._render()
        
        try:
            await interaction.response.edit_message(view=self)
        except discord.errors.InteractionResponded:
            # If already responded, try to edit the original message
            if hasattr(interaction, 'message') and interaction.message:
                await interaction.message.edit(view=self)
        
        # Signal that decision is made
        if self._decision_event:
            self._decision_event.set()
    
    async def wait_for_decision(
        self, 
        interaction: discord.Interaction, 
        *,
        send_method: str = "response",
        **send_kwargs: Any
    ) -> bool:
        """
        Send the confirmation dialog and wait for user decision.
        
        Args:
            interaction: The interaction to respond to.
            send_method: How to send the view ('response' for send_message, 
                        'followup' for followup.send, 'edit' for edit_message).
            **send_kwargs: Additional kwargs passed to the send method.
        
        Returns:
            True if user confirmed, False if cancelled or timed out.
        """
        import asyncio
        
        self._decision_event = asyncio.Event()
        self._confirmed = None
        
        # Send the view based on the method
        if send_method == "response":
            default_kwargs = {"ephemeral": self.ephemeral}
            default_kwargs.update(send_kwargs)
            await interaction.response.send_message(
                view=self, 
                **default_kwargs
            )
        elif send_method == "followup":
            default_kwargs = {"ephemeral": self.ephemeral}
            default_kwargs.update(send_kwargs)
            await interaction.followup.send(view=self, **default_kwargs)
        elif send_method == "edit":
            await interaction.response.edit_message(view=self, **send_kwargs)
        else:
            raise ValueError(f"Unknown send_method: {send_method}")
        
        # Wait for decision or timeout
        try:
            await asyncio.wait_for(self._decision_event.wait(), timeout=self.timeout)
        except asyncio.TimeoutError:
            log.debug("Confirmation dialog timed out")
            self._confirmed = False
        
        return self._confirmed or False


class ConfirmationView:
    """
    Alternative simple confirmation helper that uses a callback pattern.
    
    This is a simpler interface for cases where you want to use a callback
    instead of await/async for the decision.
    
    Usage:
        view = ConfirmationView(
            title="Delete",
            message="Delete this item?",
            on_confirm=lambda i: delete_item(i),
            on_cancel=lambda i: i.response.send_message("Cancelled", ephemeral=True)
        )
        await interaction.response.send_message(view=view, ephemeral=True)
    """
    
    def __init__(
        self,
        title: str,
        message: str,
        on_confirm: Callable[[discord.Interaction], Awaitable[Any]],
        on_cancel: Callable[[discord.Interaction], Awaitable[Any]],
        confirm_label: str = "Confirm",
        cancel_label: str = "Cancel",
        confirm_style: discord.ButtonStyle = discord.ButtonStyle.success,
        cancel_style: discord.ButtonStyle = discord.ButtonStyle.secondary,
        timeout: float = 120.0,
    ) -> None:
        self.view = ConfirmationDialog(
            title=title,
            message=message,
            confirm_label=confirm_label,
            cancel_label=cancel_label,
            confirm_style=confirm_style,
            cancel_style=cancel_style,
            timeout=timeout,
            ephemeral=True,
        )
        
        # Override callbacks with provided ones
        self.view._confirm_button.callback = lambda i: self._wrap_callback(on_confirm, i)  # type: ignore[method-assign]
        self.view._cancel_button.callback = lambda i: self._wrap_callback(on_cancel, i)  # type: ignore[method-assign]
        
        self._on_confirm = on_confirm
        self._on_cancel = on_cancel
    
    async def _wrap_callback(
        self, 
        callback: Callable[[discord.Interaction], Awaitable[Any]], 
        interaction: discord.Interaction
    ) -> None:
        """Wrap the callback to handle interaction response."""
        try:
            await callback(interaction)
        except Exception as e:
            log.error(f"Error in confirmation callback: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "An error occurred.", ephemeral=True
                )
    
    def __call__(self) -> discord.ui.LayoutView:
        """Return the underlying LayoutView."""
        return self.view