"""
src/bot/features/utility/cog.py
----------------------------------
Utility Cog

General purpose information and utility slash commands.
Uses discord.ui.LayoutView (Components V2) for rich, formatted responses.

Commands:
    /help       — Show all available commands grouped by category
    /ping       — Check Kairo's response latency
    /botinfo    — Display information about Kairo
    /userinfo   — Display information about a user
    /serverinfo — Display information about this server
    /avatar     — Display a user's avatar
"""

from __future__ import annotations

from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from ...core.bot import KairoBot
from ...core.logging import get_logger
from ...components import send_layout

log = get_logger(__name__)

# Emoji icons for known cog categories.
_CATEGORY_ICONS: dict[str, str] = {
    "Utility":    "🔧",
    "Moderation": "🔨",
    "AutoMod":    "🤖",
    "Logging":    "📋",
}


def _simple_view(*items: discord.ui.Item) -> discord.ui.LayoutView:
    """Build a LayoutView from a flat list of top-level items."""
    view = discord.ui.LayoutView()
    for item in items:
        view.add_item(item)
    return view


class UtilityCog(commands.Cog, name="Utility"):
    """
    General utility commands for Kairo.
    """

    def __init__(self, bot: KairoBot) -> None:
        self.bot = bot

    # ------------------------------------------------------------------ #
    # Help                                                                 #
    # ------------------------------------------------------------------ #

    @app_commands.command(name="help", description="Show all available Kairo commands.")
    @app_commands.describe(category="Optional: show commands for a specific category only.")
    async def help(
        self,
        interaction: discord.Interaction,
        category: Optional[str] = None,
    ) -> None:
        """
        Display all registered slash commands grouped by cog/category.

        When *category* is provided, only commands belonging to that cog are
        shown. The lookup is case-insensitive.
        """
        # Build {cog_name: [Command, ...]} from the bot's command tree.
        grouped: dict[str, list[app_commands.Command]] = {}
        for cmd in self.bot.tree.get_commands():
            if not isinstance(cmd, app_commands.Command):
                continue
            cog_name = cmd.binding.qualified_name if cmd.binding else "Other"
            grouped.setdefault(cog_name, []).append(cmd)

        sorted_categories = sorted(grouped.keys())

        # ---- Category filter ----
        if category:
            match = next(
                (n for n in sorted_categories if n.lower() == category.lower()),
                None,
            )
            if match is None:
                available = ", ".join(f"`{n}`" for n in sorted_categories)
                view = _simple_view(
                    discord.ui.Container(
                        discord.ui.TextDisplay(
                            f"❌ Category **{category}** not found.\n"
                            f"**Available categories:** {available}"
                        ),
                    )
                )
                await send_layout(interaction, view, ephemeral=True)
                return
            sorted_categories = [match]

        # ---- Build the view ----
        view = discord.ui.LayoutView()

        # Header
        if category:
            header = f"## 📖 Kairo Help — {sorted_categories[0]}"
            subtext = f"Showing commands in the **{sorted_categories[0]}** category."
        else:
            total = sum(len(c) for c in grouped.values())
            header = "## 📖 Kairo Help"
            subtext = f"**{total}** commands across **{len(sorted_categories)}** categories."

        view.add_item(discord.ui.Container(
            discord.ui.TextDisplay(header),
            discord.ui.TextDisplay(subtext),
        ))

        # One container per category
        for cat_name in sorted_categories:
            icon = _CATEGORY_ICONS.get(cat_name, "📦")
            cmds = sorted(grouped[cat_name], key=lambda c: c.name)
            lines = "\n".join(f"`/{cmd.name}` — {cmd.description}" for cmd in cmds)
            view.add_item(discord.ui.Container(
                discord.ui.TextDisplay(f"**{icon} {cat_name}**"),
                discord.ui.Separator(visible=False),
                discord.ui.TextDisplay(lines),
            ))

        # Footer
        view.add_item(discord.ui.Container(
            discord.ui.Separator(visible=True),
            discord.ui.TextDisplay("Use `/help category:<name>` to filter by category."),
        ))

        await send_layout(interaction, view, ephemeral=True)
        log.debug(
            "Help panel sent to %s (category=%r, categories=%d).",
            interaction.user,
            category,
            len(sorted_categories),
        )

    # ------------------------------------------------------------------ #
    # Ping                                                                 #
    # ------------------------------------------------------------------ #

    @app_commands.command(name="ping", description="Check Kairo's response latency.")
    async def ping(self, interaction: discord.Interaction) -> None:
        """Respond with the current WebSocket heartbeat latency."""
        latency_ms = round(self.bot.latency * 1000)
        view = _simple_view(
            discord.ui.Container(
                discord.ui.TextDisplay(f"🏓 **Pong!** Latency: **{latency_ms}ms**"),
            )
        )
        await send_layout(interaction, view, ephemeral=True)

    # ------------------------------------------------------------------ #
    # Bot Info                                                             #
    # ------------------------------------------------------------------ #

    @app_commands.command(name="botinfo", description="Display information about Kairo.")
    async def botinfo(self, interaction: discord.Interaction) -> None:
        """Display Kairo's version, statistics, and uptime."""
        assert self.bot.user is not None
        guild_count = len(self.bot.guilds)
        latency_ms = round(self.bot.latency * 1000)

        view = _simple_view(
            discord.ui.Container(
                discord.ui.TextDisplay("# Kairo"),
                discord.ui.TextDisplay("A modern, self-hostable Discord platform."),
                discord.ui.Separator(visible=True),
                discord.ui.TextDisplay(
                    f"**Guilds:** {guild_count}\n"
                    f"**Latency:** {latency_ms}ms\n"
                    f"**discord.py:** 2.7.1\n"
                    f"**Phase:** 1 — Foundation"
                ),
            )
        )
        await send_layout(interaction, view, ephemeral=True)

    # ------------------------------------------------------------------ #
    # User Info                                                            #
    # ------------------------------------------------------------------ #

    @app_commands.command(name="userinfo", description="Display information about a user.")
    @app_commands.describe(member="The member to look up. Defaults to yourself.")
    @app_commands.guild_only()
    async def userinfo(
        self,
        interaction: discord.Interaction,
        member: Optional[discord.Member] = None,
    ) -> None:
        """Display detailed information about a guild member."""
        target = member or interaction.user
        assert isinstance(target, discord.Member)

        created = discord.utils.format_dt(target.created_at, "R")
        joined = discord.utils.format_dt(target.joined_at, "R") if target.joined_at else "Unknown"

        roles = [r.mention for r in reversed(target.roles) if r.name != "@everyone"]
        role_str = " ".join(roles[:10]) if roles else "None"
        if len(roles) > 10:
            role_str += f" (+{len(roles) - 10} more)"

        view = _simple_view(
            discord.ui.Container(
                discord.ui.Section(
                    discord.ui.TextDisplay(f"## {target.display_name}"),
                    discord.ui.TextDisplay(f"`{target}` • {target.mention}"),
                    accessory=discord.ui.Thumbnail(
                        target.display_avatar.url,
                        description=f"{target.display_name}'s avatar",
                    ),
                ),
                discord.ui.Separator(visible=True),
                discord.ui.TextDisplay(
                    f"**ID:** `{target.id}`\n"
                    f"**Account created:** {created}\n"
                    f"**Joined server:** {joined}\n"
                    f"**Top role:** {target.top_role.mention}\n"
                    f"**Roles:** {role_str}"
                ),
            )
        )
        await send_layout(interaction, view, ephemeral=True)

    # ------------------------------------------------------------------ #
    # Server Info                                                          #
    # ------------------------------------------------------------------ #

    @app_commands.command(name="serverinfo", description="Display information about this server.")
    @app_commands.guild_only()
    async def serverinfo(self, interaction: discord.Interaction) -> None:
        """Display information about the current guild."""
        guild = interaction.guild
        assert guild is not None

        created = discord.utils.format_dt(guild.created_at, "R")

        # Build Section with optional thumbnail
        section_items: list[discord.ui.Item] = [
            discord.ui.TextDisplay(f"## {guild.name}"),
            discord.ui.TextDisplay(f"ID: `{guild.id}`"),
        ]
        section = discord.ui.Section(
            *section_items,
            accessory=discord.ui.Thumbnail(
                guild.icon.url if guild.icon else "https://cdn.discordapp.com/embed/avatars/0.png",
                description=f"{guild.name} icon",
            ),
        )

        view = _simple_view(
            discord.ui.Container(
                section,
                discord.ui.Separator(visible=True),
                discord.ui.TextDisplay(
                    f"**Owner:** <@{guild.owner_id}>\n"
                    f"**Created:** {created}\n"
                    f"**Members:** {guild.member_count}\n"
                    f"**Channels:** {len(guild.channels)}\n"
                    f"**Roles:** {len(guild.roles)}\n"
                    f"**Boost level:** {guild.premium_tier}"
                ),
            )
        )
        await send_layout(interaction, view, ephemeral=True)

    # ------------------------------------------------------------------ #
    # Avatar                                                               #
    # ------------------------------------------------------------------ #

    @app_commands.command(name="avatar", description="Display a user's avatar.")
    @app_commands.describe(member="The member whose avatar to show. Defaults to yourself.")
    @app_commands.guild_only()
    async def avatar(
        self,
        interaction: discord.Interaction,
        member: Optional[discord.Member] = None,
    ) -> None:
        """Display a user's avatar in full size."""
        target = member or interaction.user
        assert isinstance(target, discord.Member)
        avatar_url = target.display_avatar.url

        view = _simple_view(
            discord.ui.Container(
                discord.ui.TextDisplay(f"## {target.display_name}'s Avatar"),
                discord.ui.TextDisplay(f"[Open in browser]({avatar_url})"),
            )
        )
        await send_layout(interaction, view, ephemeral=True)


async def setup(bot: KairoBot) -> None:
    """Called by discord.py when this extension is loaded."""
    await bot.add_cog(UtilityCog(bot))
