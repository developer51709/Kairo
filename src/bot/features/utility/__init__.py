"""
src/bot/features/utility/__init__.py
--------------------------------------
Utility Feature

General-purpose information and utility commands.

Commands:
    /userinfo   — Display detailed information about a user
    /serverinfo — Display information about the current server
    /roleinfo   — Display information about a role
    /avatar     — Display a user's avatar in full size
    /botinfo    — Display information about Kairo
    /ping       — Show bot latency

Planned:
    /permissions  — Show a user's permissions in a channel
    /channelinfo  — Display information about a channel
    /embed        — Build and send a custom embed
    /remind       — Set a personal reminder
"""

from .cog import UtilityCog


async def setup(bot) -> None:
    """Called by discord.py when this extension is loaded."""
    await bot.add_cog(UtilityCog(bot))
