"""
src/bot/features/automod/__init__.py
--------------------------------------
AutoMod Feature

Automated rule enforcement that monitors messages and member activity
and takes configurable actions without requiring manual moderator intervention.

Planned rules:
    - Spam detection (message rate limiting)
    - Mention spam (too many @mentions in one message)
    - Duplicate message detection
    - Invite link filtering
    - External link filtering
    - Blocked word/phrase filtering
    - Excessive caps filtering
    - Raid protection (mass join detection)

Each rule produces an automod event that can trigger one or more actions:
    - Delete the offending message
    - Warn the user
    - Timeout the user
    - Kick the user
    - Ban the user
    - Log to the mod-log channel

Configuration is per-guild and stored in the database. Rules can be
enabled/disabled individually and exemptions can be set per role/channel.
"""

from .cog import AutoModCog


async def setup(bot) -> None:
    """Called by discord.py when this extension is loaded."""
    await bot.add_cog(AutoModCog(bot))
