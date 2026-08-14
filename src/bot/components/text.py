"""
src/bot/components/text.py
---------------------------
TextDisplay and Separator — re-exported from discord.ui

These types are provided natively by discord.py 2.6+.
Import directly from discord.ui in new code; this module
exists only as a compatibility shim during the transition.

Note: discord.py's Separator uses ``visible=`` (not ``divider=``)
and ``spacing=discord.SeparatorSpacing.small/large``.
"""

from discord.ui import TextDisplay, Separator  # noqa: F401
from discord import SeparatorSpacing  # noqa: F401

__all__ = ["TextDisplay", "Separator", "SeparatorSpacing"]
