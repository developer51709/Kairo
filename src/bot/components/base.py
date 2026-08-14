"""
src/bot/components/base.py
---------------------------
Base component types — replaced by discord.ui

The KairoComponent base class has been removed. All components now
use discord.ui natively:

    discord.ui.LayoutView  — top-level view (passed as view= kwarg)
    discord.ui.Container   — top-level layout block
    discord.ui.Section     — grouped content with an accessory
    discord.ui.TextDisplay — markdown text
    discord.ui.Separator   — visual spacing / divider
    discord.ui.ActionRow   — holds buttons or a select menu
    discord.ui.Button      — clickable button
    discord.ui.Select      — string select menu
    discord.ui.Thumbnail   — image accessory for Section

This file is kept as a documentation stub.
"""
