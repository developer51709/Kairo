"""
src/bot/components/modal.py
-----------------------------
Modal and TextInput — re-exported from discord.ui

Modals are provided natively by discord.py.
Use discord.ui.Modal and discord.ui.TextInput directly in new code.

Example:
    class MyModal(discord.ui.Modal, title="Configure"):
        name = discord.ui.TextInput(label="Name", placeholder="Enter a name...")

        async def on_submit(self, interaction: discord.Interaction) -> None:
            await interaction.response.send_message(
                f"Hello, {self.name.value}!", ephemeral=True
            )
"""

from discord.ui import Modal, TextInput  # noqa: F401

__all__ = ["Modal", "TextInput"]
