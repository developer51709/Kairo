"""
src/bot/features/moderation/__init__.py
-----------------------------------------
Moderation Feature

Provides server moderation commands and case management.

Commands:
    /ban     — Ban a member from the server
    /unban   — Unban a previously banned user
    /kick    — Kick a member from the server
    /timeout — Temporarily mute a member
    /warn    — Issue a warning to a member
    /case    — View a specific moderation case
    /history — View a member's moderation history
    /note    — Add a note to a moderation case

Planned:
    /cases   — List recent moderation cases (paginated)
    /pardon  — Pardon a warning
    /purge   — Bulk delete messages

All moderation actions are recorded as ModerationCase records and
can be reviewed in the web dashboard.
"""

from .cog import ModerationCog


async def setup(bot) -> None:
    """Called by discord.py when this extension is loaded."""
    await bot.add_cog(ModerationCog(bot))
