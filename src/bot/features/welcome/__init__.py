"""
src/bot/features/welcome/__init__.py
-----------------------------------
Welcome Feature Package

Provides welcome messages, leave messages, and auto-role functionality
for new members joining servers.

This feature handles:
- Welcome messages in configured channels
- Leave messages in configured channels  
- Auto-role assignment to new members
- Template variables in messages ({member}, {server}, {count})
"""

from .cog import WelcomeCog