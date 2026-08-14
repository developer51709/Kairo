"""
src/bot/features/welcome/cog.py
----------------------------------
Welcome Cog

Handles welcome messages, leave messages, and auto-role assignment
for server members.

Features:
- Welcome messages when new members join
- Leave messages when members leave
- Auto-role assignment to new members
- Message templates with variable substitution
- Configurable per-guild via database
"""

from __future__ import annotations

import discord
from discord.ext import commands

from ...core.bot import KairoBot
from ...core.logging import get_logger
from ...database.repositories.guild import GuildRepository
from ...components import send_layout_to_channel

log = get_logger(__name__)


class WelcomeCog(commands.Cog, name="Welcome"):
    """
    Welcome and leave message handling for servers.
    
    Automatically sends welcome messages when members join and 
    leave messages when members leave. Also handles auto-role assignment.
    """

    def __init__(self, bot: KairoBot) -> None:
        self.bot = bot
        self._member_count_cache: dict[int, int] = {}  # guild_id -> member_count
        log.info("Welcome cog initialised.")

    def _guild_repo(self) -> GuildRepository:
        """Return the guild repository."""
        return GuildRepository(self.bot.db)  # type: ignore[attr-defined]

    def _format_message(
        self, 
        template: str, 
        member: discord.Member, 
        guild: discord.Guild
    ) -> str:
        """
        Format a message template with variable substitution.
        
        Args:
            template: The message template with variables like {member}, {server}, {count}.
            member: The Discord member the message is about.
            guild: The Discord guild/server.
        
        Returns:
            The formatted message with variables replaced.
        """
        # Get member count (use cached value or fetch)
        member_count = self._member_count_cache.get(guild.id, len(guild.members))
        
        return template.replace(
            "{member}", str(member)
        ).replace(
            "{server}", guild.name
        ).replace(
            "{count}", str(member_count)
        ).replace(
            "{mention}", member.mention
        ).replace(
            "{user}", str(member)
        )

    async def _update_member_count_cache(self, guild: discord.Guild) -> None:
        """Update the cached member count for a guild."""
        self._member_count_cache[guild.id] = len(guild.members)

    # ------------------------------------------------------------------ #
    # Event Listeners                                                     #
    # ------------------------------------------------------------------ #

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """
        Handle new member joins.
        
        Sends welcome message and assigns auto-role if configured.
        """
        try:
            # Update member count cache
            await self._update_member_count_cache(member.guild)
            
            # Get guild configuration
            guild_config = await self._guild_repo().get_or_create(
                member.guild.id, 
                member.guild.name
            )
            
            # Handle auto-role
            if guild_config.auto_role:
                await self._assign_auto_role(member, guild_config.auto_role)
            
            # Handle welcome message
            if guild_config.welcome_enabled and guild_config.welcome_channel:
                await self._send_welcome_message(member, guild_config)
                
        except Exception as e:
            log.error("Error in member join handler: %s", e)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        """
        Handle member leaves.
        
        Sends leave message if configured.
        """
        try:
            # Update member count cache
            await self._update_member_count_cache(member.guild)
            
            # Get guild configuration
            guild_config = await self._guild_repo().get_or_create(
                member.guild.id, 
                member.guild.name
            )
            
            # Handle leave message
            if guild_config.leave_enabled and guild_config.leave_channel:
                await self._send_leave_message(member, guild_config)
                
        except Exception as e:
            log.error("Error in member remove handler: %s", e)

    # ------------------------------------------------------------------ #
    # Message Sending                                                      #
    # ------------------------------------------------------------------ #

    async def _send_welcome_message(
        self, 
        member: discord.Member, 
        config: object
    ) -> None:
        """
        Send a welcome message to the configured channel.
        
        Args:
            member: The new member who joined.
            config: The guild configuration with welcome settings.
        """
        try:
            # Get the welcome channel
            channel = member.guild.get_channel(config.welcome_channel)
            if channel is None or not hasattr(channel, 'send'):
                log.warning("Welcome channel %d not found in guild %d", 
                          config.welcome_channel, member.guild.id)
                return
            
            # Format the message
            message_content = self._format_message(
                config.welcome_message, 
                member, 
                member.guild
            )
            
            # Send using Components V2 for rich formatting
            view = discord.ui.LayoutView()
            view.add_item(discord.ui.Container(
                discord.ui.TextDisplay(message_content),
            ))
            
            await send_layout_to_channel(channel, view)
            log.info("Welcome message sent for %s in #%s", member, channel)
            
        except Exception as e:
            log.error("Failed to send welcome message: %s", e)

    async def _send_leave_message(
        self, 
        member: discord.Member, 
        config: object
    ) -> None:
        """
        Send a leave message to the configured channel.
        
        Args:
            member: The member who left.
            config: The guild configuration with leave settings.
        """
        try:
            # Get the leave channel
            channel = member.guild.get_channel(config.leave_channel)
            if channel is None or not hasattr(channel, 'send'):
                log.warning("Leave channel %d not found in guild %d", 
                          config.leave_channel, member.guild.id)
                return
            
            # Format the message
            message_content = self._format_message(
                config.leave_message, 
                member, 
                member.guild
            )
            
            # Send using Components V2 for rich formatting
            view = discord.ui.LayoutView()
            view.add_item(discord.ui.Container(
                discord.ui.TextDisplay(message_content),
            ))
            
            await send_layout_to_channel(channel, view)
            log.info("Leave message sent for %s in #%s", member, channel)
            
        except Exception as e:
            log.error("Failed to send leave message: %s", e)

    # ------------------------------------------------------------------ #
    # Auto-Role Assignment                                                 #
    # ------------------------------------------------------------------ #

    async def _assign_auto_role(
        self, 
        member: discord.Member, 
        role_id: int
    ) -> None:
        """
        Assign the configured auto-role to a new member.
        
        Args:
            member: The new member to assign the role to.
            role_id: The Discord role ID to assign.
        """
        try:
            # Get the role
            role = member.guild.get_role(role_id)
            if role is None:
                log.warning("Auto-role %d not found in guild %d", role_id, member.guild.id)
                return
            
            # Check if bot has permission to manage roles
            if not member.guild.me.guild_permissions.manage_roles:  # type: ignore[union-attr]
                log.warning("No permission to assign roles in guild %d", member.guild.id)
                return
            
            # Assign the role
            await member.add_roles(role, reason="Auto-role assignment")
            log.info("Assigned role %s to %s in %s", role, member, member.guild)
            
        except discord.Forbidden:
            log.warning("No permission to assign role %d to %s in %s", 
                       role_id, member, member.guild)
        except Exception as e:
            log.error("Failed to assign auto-role: %s", e)

    # ------------------------------------------------------------------ #
    # Slash Commands                                                       #
    # ------------------------------------------------------------------ #

    @commands.hybrid_group(name="welcome", description="Configure welcome settings.")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def welcome_group(self, ctx: commands.Context) -> None:
        """Configure welcome and leave message settings."""
        if not ctx.invoked_subcommand:
            await ctx.send("Use subcommands to configure welcome settings.")

    @welcome_group.command(name="set", description="Set welcome message and channel.")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def welcome_set(
        self, 
        ctx: commands.Context,
        channel: discord.TextChannel,
        message: str
    ) -> None:
        """Set the welcome message and channel."""
        guild_config = await self._guild_repo().get_or_create(ctx.guild.id, ctx.guild.name)
        guild_config.welcome_channel = channel.id
        guild_config.welcome_message = message
        guild_config.welcome_enabled = True
        
        await self._guild_repo().update(guild_config)
        await ctx.send(f"✅ Welcome message set for #{channel}: {message}")

    @welcome_group.command(name="disable", description="Disable welcome messages.")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def welcome_disable(self, ctx: commands.Context) -> None:
        """Disable welcome messages."""
        guild_config = await self._guild_repo().get_or_create(ctx.guild.id, ctx.guild.name)
        guild_config.welcome_enabled = False
        
        await self._guild_repo().update(guild_config)
        await ctx.send("✅ Welcome messages disabled.")

    @welcome_group.command(name="leave", description="Configure leave messages.")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def welcome_leave(
        self, 
        ctx: commands.Context,
        channel: discord.TextChannel,
        message: str,
        enable: bool = True
    ) -> None:
        """Configure leave messages."""
        guild_config = await self._guild_repo().get_or_create(ctx.guild.id, ctx.guild.name)
        guild_config.leave_channel = channel.id
        guild_config.leave_message = message
        guild_config.leave_enabled = enable
        
        await self._guild_repo().update(guild_config)
        status = "enabled" if enable else "disabled"
        await ctx.send(f"✅ Leave messages {status} for #{channel}: {message}")

    @commands.hybrid_group(name="autorole", description="Configure auto-role settings.")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def autorole_group(self, ctx: commands.Context) -> None:
        """Configure auto-role settings."""
        if not ctx.invoked_subcommand:
            await ctx.send("Use subcommands to configure auto-role settings.")

    @autorole_group.command(name="set", description="Set the role to auto-assign to new members.")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def autorole_set(self, ctx: commands.Context, role: discord.Role) -> None:
        """Set the auto-role for new members."""
        guild_config = await self._guild_repo().get_or_create(ctx.guild.id, ctx.guild.name)
        guild_config.auto_role = role.id
        
        await self._guild_repo().update(guild_config)
        await ctx.send(f"✅ Auto-role set to {role}")

    @autorole_group.command(name="clear", description="Clear the auto-role.")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def autorole_clear(self, ctx: commands.Context) -> None:
        """Clear the auto-role."""
        guild_config = await self._guild_repo().get_or_create(ctx.guild.id, ctx.guild.name)
        guild_config.auto_role = None
        
        await self._guild_repo().update(guild_config)
        await ctx.send("✅ Auto-role cleared.")


async def setup(bot: KairoBot) -> None:
    """Called by discord.py when this extension is loaded."""
    await bot.add_cog(WelcomeCog(bot))