"""
src/bot/features/logging/__init__.py
--------------------------------------
Logging Feature

Records Discord server events to configured log channels.
This is distinct from Kairo's internal Python logging (src/bot/core/logging.py)
— this feature sends Discord messages about server activity.

Planned logged events:
    Member events:
        - Member join / leave
        - Member ban / unban
        - Nickname change
        - Role assignment / removal

    Message events:
        - Message edit (before/after)
        - Message delete
        - Bulk message delete

    Channel events:
        - Channel create / delete / update

    Role events:
        - Role create / delete / update

    Moderation events:
        - All moderation cases (from ModerationService)
        - AutoMod actions

    Voice events:
        - Voice channel join / leave / move

Configuration is per-guild. Each event category can be routed to a
separate channel or disabled entirely.
"""

from .cog import LoggingCog


async def setup(bot) -> None:
    """Called by discord.py when this extension is loaded."""
    await bot.add_cog(LoggingCog(bot))
