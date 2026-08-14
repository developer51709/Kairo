"""
src/bot/features/utility/cog.py
----------------------------------
Utility Cog

General purpose information and utility slash commands.
Uses Components V2 panels for rich, formatted responses.

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
from ...components import Panel, Container, Section, Text, Separator

log = get_logger(__name__)

# Emoji icons for known cog categories.
_CATEGORY_ICONS: dict[str, str] = {
    "Utility":    "🔧",
    "Moderation": "🔨",
    "AutoMod":    "🤖",
    "Logging":    "📋",
}


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
        shown.  The lookup is case-insensitive.
        """
        # Build a mapping of {cog_name: [app_commands.Command, ...]} from the
        # bot's command tree.  We iterate over the tree's global commands so
        # that commands registered by every loaded cog are included.
        grouped: dict[str, list[app_commands.Command]] = {}

        for cmd in self.bot.tree.get_commands():
            # Only handle leaf commands (not groups) for now.
            if not isinstance(cmd, app_commands.Command):
                continue
            cog_name = cmd.binding.qualified_name if cmd.binding else "Other"
            grouped.setdefault(cog_name, []).append(cmd)

        # Sort categories alphabetically so the output is stable.
        sorted_categories = sorted(grouped.keys())

        # ---- Category filter ----
        if category:
            # Case-insensitive match against the category name.
            match = next(
                (name for name in sorted_categories if name.lower() == category.lower()),
                None,
            )
            if match is None:
                available = ", ".join(f"`{n}`" for n in sorted_categories)
                panel = Panel(
                    Container(
                        Text(f"❌ Category **{category}** not found."),
                        Separator(divider=True),
                        Text(f"**Available categories:** {available}"),
                    ),
                    ephemeral=True,
                )
                await panel.send(interaction)
                return
            sorted_categories = [match]

        # ---- Build the panel ----
        # One Container per category keeps each section visually distinct.
        containers: list[Container] = []

        # Header container.
        header_text = (
            f"## 📖 Kairo Help — {sorted_categories[0]}"
            if category
            else "## 📖 Kairo Help"
        )
        if not category:
            total = sum(len(cmds) for cmds in grouped.values())
            subtext = f"**{total}** commands across **{len(sorted_categories)}** categories."
        else:
            subtext = f"Showing commands in the **{sorted_categories[0]}** category."

        containers.append(
            Container(
                Text(header_text),
                Text(subtext),
            )
        )

        for cat_name in sorted_categories:
            icon = _CATEGORY_ICONS.get(cat_name, "📦")
            cmds = sorted(grouped[cat_name], key=lambda c: c.name)

            # Build a formatted string: `/name` — description
            lines = "\n".join(
                f"`/{cmd.name}` — {cmd.description}" for cmd in cmds
            )

            containers.append(
                Container(
                    Text(f"**{icon} {cat_name}**"),
                    Separator(divider=False),
                    Text(lines),
                )
            )

        # Footer hint.
        containers.append(
            Container(
                Separator(divider=True),
                Text("Use `/help category:<name>` to filter by category."),
            )
        )

        panel = Panel(*containers, ephemeral=True)
        await panel.send(interaction)
        log.debug(
            "Help panel sent to %s (category=%r, categories=%d).",
            interaction.user,
            category,
            len(sorted_categories),
        )

    @app_commands.command(name="ping", description="Check Kairo's response latency.")
    async def ping(self, interaction: discord.Interaction) -> None:
        """Respond with the current WebSocket heartbeat latency."""
        latency_ms = round(self.bot.latency * 1000)
        panel = Panel(
            Container(
                Text(f"🏓 **Pong!** Latency: **{latency_ms}ms**"),
            ),
            ephemeral=True,
        )
        await panel.send(interaction)

    @app_commands.command(name="botinfo", description="Display information about Kairo.")
    async def botinfo(self, interaction: discord.Interaction) -> None:
        """Display Kairo's version, statistics, and uptime."""
        assert self.bot.user is not None
        guild_count = len(self.bot.guilds)
        latency_ms = round(self.bot.latency * 1000)

        panel = Panel(
            Container(
                Text("# Kairo"),
                Text("A modern, self-hostable Discord platform."),
                Separator(divider=True),
                Text(
                    f"**Guilds:** {guild_count}\n"
                    f"**Latency:** {latency_ms}ms\n"
                    f"**discord.py:** 2.7.1\n"
                    f"**Phase:** 1 — Foundation"
                ),
            ),
            ephemeral=True,
        )
        await panel.send(interaction)

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

        panel = Panel(
            Container(
                Section(
                    Text(f"## {target.display_name}"),
                    Text(f"`{target}` • {target.mention}"),
                    thumbnail_url=target.display_avatar.url,
                    thumbnail_alt=f"{target.display_name}'s avatar",
                ),
                Separator(divider=True),
                Text(
                    f"**ID:** `{target.id}`\n"
                    f"**Account created:** {created}\n"
                    f"**Joined server:** {joined}\n"
                    f"**Top role:** {target.top_role.mention}\n"
                    f"**Roles:** {role_str}"
                ),
            ),
            ephemeral=True,
        )
        await panel.send(interaction)

    @app_commands.command(name="serverinfo", description="Display information about this server.")
    @app_commands.guild_only()
    async def serverinfo(self, interaction: discord.Interaction) -> None:
        """Display information about the current guild."""
        guild = interaction.guild
        assert guild is not None

        created = discord.utils.format_dt(guild.created_at, "R")

        panel = Panel(
            Container(
                Section(
                    Text(f"## {guild.name}"),
                    Text(f"ID: `{guild.id}`"),
                    thumbnail_url=guild.icon.url if guild.icon else None,
                    thumbnail_alt=f"{guild.name} icon",
                ),
                Separator(divider=True),
                Text(
                    f"**Owner:** <@{guild.owner_id}>\n"
                    f"**Created:** {created}\n"
                    f"**Members:** {guild.member_count}\n"
                    f"**Channels:** {len(guild.channels)}\n"
                    f"**Roles:** {len(guild.roles)}\n"
                    f"**Boost level:** {guild.premium_tier}"
                ),
            ),
            ephemeral=True,
        )
        await panel.send(interaction)

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

        panel = Panel(
            Container(
                Text(f"## {target.display_name}'s Avatar"),
                # TODO: Use MediaGallery component when available in discord.py
                Text(f"[Open in browser]({avatar_url})"),
            ),
            ephemeral=True,
        )
        await panel.send(interaction)


async def setup(bot: KairoBot) -> None:
    """Called by discord.py when this extension is loaded."""
    await bot.add_cog(UtilityCog(bot))
