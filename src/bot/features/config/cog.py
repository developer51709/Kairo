"""
src/bot/features/config/cog.py
----------------------------------
Configuration Cog

Provides centralized server configuration commands for Kairo.

This cog allows server administrators to configure all bot features
through a unified interface including:
- Mod-log channel configuration
- Language/locale settings
- Feature toggles
- Server-specific settings
"""

from __future__ import annotations

from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from ...core.bot import KairoBot
from ...core.logging import get_logger
from ...database.repositories.guild import GuildRepository
from ...components import send_layout, ConfirmationDialog

log = get_logger(__name__)


class ConfigCog(commands.Cog, name="Config"):
    """
    Server configuration commands for Kairo.
    """

    def __init__(self, bot: KairoBot) -> None:
        self.bot = bot
        log.info("Config cog initialised.")

    def _guild_repo(self) -> GuildRepository:
        """Return the guild repository."""
        return GuildRepository(self.bot.db)  # type: ignore[attr-defined]

    # ------------------------------------------------------------------ #
    # General Server Configuration                                         #
    # ------------------------------------------------------------------ #

    @app_commands.command(name="setup", description="Initial server setup for Kairo.")
    @app_commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction) -> None:
        """
        Run initial setup for Kairo in this server.
        
        This guides the administrator through basic configuration.
        """
        guild_config = await self._guild_repo().get_or_create(
            interaction.guild.id,
            interaction.guild.name
        )
        
        # Show current configuration status
        view = discord.ui.LayoutView()
        view.add_item(discord.ui.Container(
            discord.ui.TextDisplay("# Kairo Server Setup"),
            discord.ui.Separator(visible=True),
        ))
        
        # Configuration status
        status_items = [
            discord.ui.TextDisplay("**✅ Guild Configuration**"),
            discord.ui.TextDisplay(f"Server: {interaction.guild.name}"),
            discord.ui.TextDisplay(f"Mod-Log Channel: {'Set' if guild_config.mod_log_channel else 'Not set'}"),
            discord.ui.TextDisplay(f"Welcome Channel: {'Set' if guild_config.welcome_channel else 'Not set'}"),
            discord.ui.TextDisplay(f"Auto-Role: {'Set' if guild_config.auto_role else 'Not set'}"),
            discord.ui.TextDisplay(f"Locale: {guild_config.locale}"),
            discord.ui.Separator(visible=True),
        ]
        
        view.add_item(discord.ui.Container(*status_items))
        
        # Quick setup options
        action_row = discord.ui.ActionRow(
            discord.ui.Button(
                label="Set Mod-Log Channel",
                style=discord.ButtonStyle.primary,
                custom_id="setup_modlog",
            ),
            discord.ui.Button(
                label="Configure Welcome",
                style=discord.ButtonStyle.primary,
                custom_id="setup_welcome",
            ),
            discord.ui.Button(
                label="Set Auto-Role",
                style=discord.ButtonStyle.primary,
                custom_id="setup_autorole",
            ),
        )
        
        view.add_item(discord.ui.Container(action_row))
        
        await send_layout(interaction, view, ephemeral=True)

    @app_commands.command(name="set_modlog", description="Set the mod-log channel.")
    @app_commands.describe(
        channel="The channel where moderation actions will be logged",
    )
    @app_commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def set_modlog(
        self, 
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ) -> None:
        """Set the channel where moderation actions are logged."""
        guild_config = await self._guild_repo().get_or_create(
            interaction.guild.id,
            interaction.guild.name
        )
        
        guild_config.mod_log_channel = channel.id
        await self._guild_repo().update(guild_config)
        
        await interaction.response.send_message(
            f"✅ Mod-log channel set to #{channel}",
            ephemeral=True
        )

    @app_commands.command(name="set_locale", description="Set the server locale for bot messages.")
    @app_commands.describe(
        locale="Language code (e.g., 'en', 'fr', 'de')",
    )
    @app_commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def set_locale(
        self, 
        interaction: discord.Interaction,
        locale: str,
    ) -> None:
        """Set the locale for bot messages in this server."""
        guild_config = await self._guild_repo().get_or_create(
            interaction.guild.id,
            interaction.guild.name
        )
        
        guild_config.locale = locale
        await self._guild_repo().update(guild_config)
        
        await interaction.response.send_message(
            f"✅ Server locale set to '{locale}'",
            ephemeral=True
        )

    @app_commands.command(name="set_modrole", description="Set the moderator role.")
    @app_commands.describe(
        role="The role that grants moderator access to Kairo commands",
    )
    @app_commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def set_modrole(
        self, 
        interaction: discord.Interaction,
        role: discord.Role,
    ) -> None:
        """Set the role that grants moderator access to Kairo commands."""
        guild_config = await self._guild_repo().get_or_create(
            interaction.guild.id,
            interaction.guild.name
        )
        
        guild_config.mod_role = role.id
        await self._guild_repo().update(guild_config)
        
        await interaction.response.send_message(
            f"✅ Moderator role set to {role}",
            ephemeral=True
        )

    @app_commands.command(name="config_show", description="Show current server configuration.")
    @app_commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def config_show(self, interaction: discord.Interaction) -> None:
        """Display the current server configuration."""
        guild_config = await self._guild_repo().get_or_create(
            interaction.guild.id,
            interaction.guild.name
        )
        
        # Build configuration display
        view = discord.ui.LayoutView()
        view.add_item(discord.ui.Container(
            discord.ui.TextDisplay("# Server Configuration"),
            discord.ui.Separator(visible=True),
        ))
        
        # Basic info
        view.add_item(discord.ui.Container(
            discord.ui.TextDisplay("**🏢 Basic Information**"),
            discord.ui.Separator(visible=True),
            discord.ui.TextDisplay(f"Server Name: {interaction.guild.name}"),
            discord.ui.TextDisplay(f"Server ID: {interaction.guild.id}"),
            discord.ui.TextDisplay(f"Member Count: {len(interaction.guild.members)}"),
            discord.ui.TextDisplay(f"Locale: {guild_config.locale}"),
            discord.ui.Separator(visible=True),
        ))
        
        # Channel configuration
        channels_info = [
            discord.ui.TextDisplay("**📋 Channel Configuration**"),
            discord.ui.Separator(visible=True),
        ]
        
        if guild_config.mod_log_channel:
            mod_log_channel = interaction.guild.get_channel(guild_config.mod_log_channel)
            channels_info.append(discord.ui.TextDisplay(f"Mod-Log Channel: {mod_log_channel or 'Unknown'}"))
        else:
            channels_info.append(discord.ui.TextDisplay("Mod-Log Channel: Not set"))
        
        if guild_config.log_channel:
            log_channel = interaction.guild.get_channel(guild_config.log_channel)
            channels_info.append(discord.ui.TextDisplay(f"Log Channel: {log_channel or 'Unknown'}"))
        else:
            channels_info.append(discord.ui.TextDisplay("Log Channel: Not set"))
            
        if guild_config.welcome_channel:
            welcome_channel = interaction.guild.get_channel(guild_config.welcome_channel)
            channels_info.append(discord.ui.TextDisplay(f"Welcome Channel: {welcome_channel or 'Unknown'}"))
        else:
            channels_info.append(discord.ui.TextDisplay("Welcome Channel: Not set"))
            
        if guild_config.leave_channel:
            leave_channel = interaction.guild.get_channel(guild_config.leave_channel)
            channels_info.append(discord.ui.TextDisplay(f"Leave Channel: {leave_channel or 'Unknown'}"))
        else:
            channels_info.append(discord.ui.TextDisplay("Leave Channel: Not set"))
        
        channels_info.append(discord.ui.Separator(visible=True))
        view.add_item(discord.ui.Container(*channels_info))
        
        # Role configuration
        roles_info = [
            discord.ui.TextDisplay("**👥 Role Configuration**"),
            discord.ui.Separator(visible=True),
        ]
        
        if guild_config.mod_role:
            mod_role = interaction.guild.get_role(guild_config.mod_role)
            roles_info.append(discord.ui.TextDisplay(f"Moderator Role: {mod_role or 'Unknown'}"))
        else:
            roles_info.append(discord.ui.TextDisplay("Moderator Role: Not set (Admins only)"))
        
        if guild_config.auto_role:
            auto_role = interaction.guild.get_role(guild_config.auto_role)
            roles_info.append(discord.ui.TextDisplay(f"Auto-Role: {auto_role or 'Unknown'}"))
        else:
            roles_info.append(discord.ui.TextDisplay("Auto-Role: Not set"))
        
        roles_info.append(discord.ui.Separator(visible=True))
        view.add_item(discord.ui.Container(*roles_info))
        
        # Feature status
        features_info = [
            discord.ui.TextDisplay("**⚙️ Feature Status**"),
            discord.ui.Separator(visible=True),
            discord.ui.TextDisplay(f"Welcome Messages: {'Enabled' if guild_config.welcome_enabled else 'Disabled'}"),
            discord.ui.TextDisplay(f"Leave Messages: {'Enabled' if guild_config.leave_enabled else 'Disabled'}"),
            discord.ui.TextDisplay(f"Active: {'Yes' if guild_config.active else 'No'}"),
            discord.ui.Separator(visible=True),
        ]
        
        view.add_item(discord.ui.Container(*features_info))
        
        await send_layout(interaction, view, ephemeral=True)

    @app_commands.command(name="config_reset", description="Reset server configuration to defaults.")
    @app_commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def config_reset(self, interaction: discord.Interaction) -> None:
        """Reset server configuration to default values."""
        # Ask for confirmation
        dialog = ConfirmationDialog(
            title="Reset Configuration",
            message="Are you sure you want to reset all Kairo configuration for this server to defaults?",
            confirm_label="Reset",
            cancel_label="Cancel",
            confirm_style=discord.ButtonStyle.danger,
            timeout=60.0
        )
        
        confirmed = await dialog.wait_for_decision(interaction)
        if confirmed:
            guild_config = await self._guild_repo().get_or_create(
                interaction.guild.id,
                interaction.guild.name
            )
            
            # Reset to defaults
            guild_config.mod_log_channel = None
            guild_config.log_channel = None
            guild_config.mod_role = None
            guild_config.auto_role = None
            guild_config.welcome_channel = None
            guild_config.welcome_message = "Welcome {member} to {server}!"
            guild_config.welcome_enabled = True
            guild_config.leave_channel = None
            guild_config.leave_message = "{member} has left {server}."
            guild_config.leave_enabled = False
            guild_config.locale = "en"
            
            await self._guild_repo().update(guild_config)
            await interaction.followup.send("✅ Configuration reset to defaults!", ephemeral=True)
            
            log.info("Reset configuration for guild %d", interaction.guild.id)
        else:
            await interaction.followup.send("Configuration reset cancelled.", ephemeral=True)

    # ------------------------------------------------------------------ #
    # Feature Toggles                                                     #
    # ------------------------------------------------------------------ #

    @app_commands.command(name="toggle_welcome", description="Toggle welcome messages on/off.")
    @app_commands.describe(
        enable="Whether to enable welcome messages",
    )
    @app_commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def toggle_welcome(
        self, 
        interaction: discord.Interaction,
        enable: bool,
    ) -> None:
        """Enable or disable welcome messages."""
        guild_config = await self._guild_repo().get_or_create(
            interaction.guild.id,
            interaction.guild.name
        )
        
        guild_config.welcome_enabled = enable
        await self._guild_repo().update(guild_config)
        
        status = "enabled" if enable else "disabled"
        await interaction.response.send_message(
            f"✅ Welcome messages {status}",
            ephemeral=True
        )

    @app_commands.command(name="toggle_leave", description="Toggle leave messages on/off.")
    @app_commands.describe(
        enable="Whether to enable leave messages",
    )
    @app_commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def toggle_leave(
        self, 
        interaction: discord.Interaction,
        enable: bool,
    ) -> None:
        """Enable or disable leave messages."""
        guild_config = await self._guild_repo().get_or_create(
            interaction.guild.id,
            interaction.guild.name
        )
        
        guild_config.leave_enabled = enable
        await self._guild_repo().update(guild_config)
        
        status = "enabled" if enable else "disabled"
        await interaction.response.send_message(
            f"✅ Leave messages {status}",
            ephemeral=True
        )


async def setup(bot: KairoBot) -> None:
    """Called by discord.py when this extension is loaded."""
    await bot.add_cog(ConfigCog(bot))