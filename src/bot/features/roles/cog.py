"""
src/bot/features/roles/cog.py
----------------------------------
Roles Cog

Provides role management functionality including:
- Button roles (get roles by clicking buttons)
- Select menu roles (get roles from dropdown menus)
- Simple role assignment via slash commands

This is a Phase 3 implementation that provides basic button and select menu
role functionality without requiring complex database storage.
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


class RolesCog(commands.Cog, name="Roles"):
    """
    Role management commands and interactive role buttons/menus.
    """

    def __init__(self, bot: KairoBot) -> None:
        self.bot = bot
        log.info("Roles cog initialised.")

    # ------------------------------------------------------------------ #
    # Button Role Creation                                                #
    # ------------------------------------------------------------------ #

    @app_commands.command(name="role_button", description="Create a role button message.")
    @app_commands.describe(
        role="The role to assign with the button",
        label="Button label (default: role name)",
        emoji="Button emoji (optional)",
        description="Message description",
    )
    @app_commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def role_button(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
        label: Optional[str] = None,
        emoji: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        """Create a message with a button that assigns a role when clicked."""
        try:
            # Check if bot has permission to manage roles
            if not interaction.guild.me.guild_permissions.manage_roles:  # type: ignore[union-attr]
                await interaction.response.send_message(
                    "❌ I don't have permission to manage roles!",
                    ephemeral=True
                )
                return
            
            # Use role name as default label
            button_label = label or role.name
            
            # Create the button
            button = discord.ui.Button(
                label=button_label,
                style=discord.ButtonStyle.secondary,
                emoji=discord.utils.get(interaction.guild.emojis, name=emoji) if emoji else None,
                custom_id=f"role_button:{role.id}",
            )
            
            # Set the callback
            button.callback = self._handle_role_button  # type: ignore[method-assign]
            
            # Build the view
            view = discord.ui.LayoutView()
            
            # Add header
            header_container = discord.ui.Container(
                discord.ui.TextDisplay(f"## {description or 'Get Roles'}"),
                discord.ui.Separator(visible=True),
            )
            view.add_item(header_container)
            
            # Add button in action row
            action_row = discord.ui.ActionRow(button)
            button_container = discord.ui.Container(action_row)
            view.add_item(button_container)
            
            # Send the message
            message = await interaction.response.send_message(
                view=view,
                content="Click the button below to get the role!"
            )
            
            log.info("Created role button for role %s in guild %d", role, interaction.guild.id)
            
        except Exception as e:
            log.error("Failed to create role button: %s", e)
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"❌ Error creating role button: {e}",
                    ephemeral=True
                )

    async def _handle_role_button(self, interaction: discord.Interaction) -> None:
        """Handle role button clicks."""
        try:
            # Extract role ID from custom ID
            custom_id = interaction.data.get("custom_id", "")
            if not custom_id.startswith("role_button:"):
                return
            
            role_id = int(custom_id.replace("role_button:", ""))
            role = interaction.guild.get_role(role_id)
            
            if role is None:
                await interaction.response.send_message(
                    "❌ Role not found!",
                    ephemeral=True
                )
                return
            
            # Check if user already has the role (toggle behavior)
            member = interaction.user
            if isinstance(member, discord.Member):
                if role in member.roles:
                    # Remove the role
                    await member.remove_roles(role, reason="Role button toggle")
                    await interaction.response.send_message(
                        f"✅ Removed role: {role}",
                        ephemeral=True
                    )
                else:
                    # Add the role
                    await member.add_roles(role, reason="Role button click")
                    await interaction.response.send_message(
                        f"✅ Added role: {role}",
                        ephemeral=True
                    )
            else:
                await interaction.response.send_message(
                    "❌ Error: Could not process role assignment.",
                    ephemeral=True
                )
                
        except Exception as e:
            log.error("Failed to handle role button: %s", e)
            await interaction.response.send_message(
                f"❌ Error: {e}",
                ephemeral=True
            )

    # ------------------------------------------------------------------ #
    # Select Menu Role Creation                                           #
    # ------------------------------------------------------------------ #

    @app_commands.command(name="role_menu", description="Create a role selection menu.")
    @app_commands.describe(
        roles="Roles to include in the menu (comma separated @role mentions)",
        title="Menu title",
        description="Menu description",
        placeholder="Select menu placeholder",
        max_values="Maximum roles user can select (1-25)",
    )
    @app_commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def role_menu(
        self,
        interaction: discord.Interaction,
        roles: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        placeholder: Optional[str] = None,
        max_values: app_commands.Range[int, 1, 25] = 1,
    ) -> None:
        """Create a message with a select menu for role assignment."""
        try:
            # Check if bot has permission to manage roles
            if not interaction.guild.me.guild_permissions.manage_roles:  # type: ignore[union-attr]
                await interaction.response.send_message(
                    "❌ I don't have permission to manage roles!",
                    ephemeral=True
                )
                return
            
            # Parse role mentions from the roles parameter
            role_mentions = roles.split(",")
            role_objects = []
            
            for mention in role_mentions:
                mention = mention.strip()
                if mention.startswith("<@&") and mention.endswith(">"):
                    role_id = int(mention[3:-1])
                    role = interaction.guild.get_role(role_id)
                    if role:
                        role_objects.append(role)
            
            if not role_objects:
                await interaction.response.send_message(
                    "❌ No valid roles found. Use @role mentions separated by commas.",
                    ephemeral=True
                )
                return
            
            # Create select options
            options = []
            for role in role_objects:
                options.append(discord.SelectOption(
                    label=role.name[:25],  # Max 25 chars for label
                    value=str(role.id),
                    description=f"Click to get {role.name}"[:50],  # Max 50 chars for description
                    emoji=discord.utils.get(interaction.guild.emojis, name=role.name.lower()) if role.name.lower() in [e.name for e in interaction.guild.emojis] else None,
                ))
            
            # Create the select menu
            select_menu = discord.ui.Select(
                custom_id=f"role_menu:{interaction.id}",
                placeholder=placeholder or "Select roles",
                min_values=1 if max_values == 1 else 0,
                max_values=max_values,
                options=options[:25],  # Max 25 options
            )
            
            # Set the callback
            select_menu.callback = self._handle_role_menu  # type: ignore[method-assign]
            
            # Build the view
            view = discord.ui.LayoutView()
            
            # Add header
            header_title = title or "Role Selection"
            header_container = discord.ui.Container(
                discord.ui.TextDisplay(f"## {header_title}"),
            )
            if description:
                header_container.add_item(discord.ui.TextDisplay(description))
                header_container.add_item(discord.ui.Separator(visible=True))
            else:
                header_container.add_item(discord.ui.Separator(visible=True))
            view.add_item(header_container)
            
            # Add select menu in action row
            action_row = discord.ui.ActionRow(select_menu)
            select_container = discord.ui.Container(action_row)
            view.add_item(select_container)
            
            # Send the message
            message = await interaction.response.send_message(
                view=view,
                content="Select roles from the menu below!"
            )
            
            log.info("Created role menu with %d roles in guild %d", len(role_objects), interaction.guild.id)
            
        except Exception as e:
            log.error("Failed to create role menu: %s", e)
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"❌ Error creating role menu: {e}",
                    ephemeral=True
                )

    async def _handle_role_menu(self, interaction: discord.Interaction) -> None:
        """Handle role menu selections."""
        try:
            # Get selected values
            selected_values = interaction.data.get("values", [])
            
            if not selected_values:
                await interaction.response.send_message(
                    "❌ No roles selected!",
                    ephemeral=True
                )
                return
            
            # Get the roles
            roles_to_add = []
            roles_to_remove = []
            
            member = interaction.user
            if isinstance(member, discord.Member):
                # Check which roles user already has vs doesn't have
                current_role_ids = {role.id for role in member.roles}
                
                for role_id_str in selected_values:
                    role_id = int(role_id_str)
                    role = interaction.guild.get_role(role_id)
                    if role:
                        if role_id in current_role_ids:
                            roles_to_remove.append(role)
                        else:
                            roles_to_add.append(role)
                
                # Apply role changes
                if roles_to_add:
                    await member.add_roles(*roles_to_add, reason="Role menu selection")
                if roles_to_remove:
                    await member.remove_roles(*roles_to_remove, reason="Role menu toggle")
                
                # Send confirmation
                added_names = [role.name for role in roles_to_add]
                removed_names = [role.name for role in roles_to_remove]
                
                message_parts = []
                if added_names:
                    message_parts.append(f"✅ Added: {', '.join(added_names)}")
                if removed_names:
                    message_parts.append(f"❌ Removed: {', '.join(removed_names)}")
                
                await interaction.response.send_message(
                    "\n".join(message_parts),
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "❌ Error: Could not process role assignment.",
                    ephemeral=True
                )
                
        except Exception as e:
            log.error("Failed to handle role menu: %s", e)
            await interaction.response.send_message(
                f"❌ Error: {e}",
                ephemeral=True
            )

    # ------------------------------------------------------------------ #
    # Multi-Button Role Panel                                             #
    # ------------------------------------------------------------------ #

    @app_commands.command(name="role_panel", description="Create a panel with multiple role buttons.")
    @app_commands.describe(
        title="Panel title",
        description="Panel description",
    )
    @app_commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def role_panel(
        self,
        interaction: discord.Interaction,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        """Create a role panel with multiple role buttons."""
        # This is a modal-based command that will open a setup interface
        modal = RolePanelModal(title or "Role Panel", description)
        await interaction.response.send_modal(modal)

    # ------------------------------------------------------------------ #
    # Simple Role Commands                                                #
    # ------------------------------------------------------------------ #

    @app_commands.command(name="addrole", description="Add a role to a member.")
    @app_commands.describe(
        member="The member to add the role to",
        role="The role to add",
        reason="Reason for adding the role",
    )
    @app_commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def addrole(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        role: discord.Role,
        reason: Optional[str] = None,
    ) -> None:
        """Add a role to a member."""
        try:
            await member.add_roles(role, reason=reason or "Manual role assignment")
            await interaction.response.send_message(
                f"✅ Added role {role} to {member}",
                ephemeral=True
            )
            log.info("Added role %s to %s in guild %d", role, member, interaction.guild.id)
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to add role: {e}",
                ephemeral=True
            )

    @app_commands.command(name="removerole", description="Remove a role from a member.")
    @app_commands.describe(
        member="The member to remove the role from",
        role="The role to remove",
        reason="Reason for removing the role",
    )
    @app_commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def removerole(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        role: discord.Role,
        reason: Optional[str] = None,
    ) -> None:
        """Remove a role from a member."""
        try:
            await member.remove_roles(role, reason=reason or "Manual role removal")
            await interaction.response.send_message(
                f"✅ Removed role {role} from {member}",
                ephemeral=True
            )
            log.info("Removed role %s from %s in guild %d", role, member, interaction.guild.id)
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to remove role: {e}",
                ephemeral=True
            )


class RolePanelModal(discord.ui.Modal, title="Create Role Panel"):
    """Modal for creating a role panel with multiple buttons."""
    
    title_input = discord.ui.TextInput(
        label="Panel Title",
        placeholder="Role Selection",
        max_length=100,
        required=True,
    )
    
    description_input = discord.ui.TextInput(
        label="Description",
        placeholder="Choose your roles from the buttons below",
        max_length=500,
        required=False,
    )
    
    roles_input = discord.ui.TextInput(
        label="Roles (comma-separated @mentions)",
        placeholder="@Role1, @Role2, @Role3",
        max_length=500,
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Handle modal submission to create the role panel."""
        try:
            # Parse roles from input
            roles_str = self.roles_input.value
            role_mentions = [m.strip() for m in roles_str.split(",")]
            
            role_objects = []
            for mention in role_mentions:
                if mention.startswith("<@&") and mention.endswith(">"):
                    role_id = int(mention[3:-1])
                    role = interaction.guild.get_role(role_id)
                    if role:
                        role_objects.append(role)
            
            if not role_objects:
                await interaction.response.send_message(
                    "❌ No valid roles found. Please use @role mentions.",
                    ephemeral=True
                )
                return
            
            # Create buttons for each role
            buttons = []
            for role in role_objects:
                button = discord.ui.Button(
                    label=role.name[:80],  # Max 80 chars
                    style=discord.ButtonStyle.secondary,
                    custom_id=f"panel_role:{role.id}",
                )
                button.callback = lambda i, r=role: self._handle_panel_role_button(i, r)  # type: ignore[method-assign]
                buttons.append(button)
            
            # Split buttons into action rows (max 5 per row)
            action_rows = []
            for i in range(0, len(buttons), 5):
                row_buttons = buttons[i:i+5]
                action_rows.append(discord.ui.ActionRow(*row_buttons))
            
            # Build the view
            view = discord.ui.LayoutView()
            
            # Add title and description
            title_container = discord.ui.Container(
                discord.ui.TextDisplay(f"## {self.title_input.value}"),
            )
            if self.description_input.value:
                title_container.add_item(discord.ui.TextDisplay(self.description_input.value))
                title_container.add_item(discord.ui.Separator(visible=True))
            else:
                title_container.add_item(discord.ui.Separator(visible=True))
            view.add_item(title_container)
            
            # Add action rows with buttons
            for action_row in action_rows:
                view.add_item(discord.ui.Container(action_row))
            
            # Send the message
            message = await interaction.response.send_message(
                view=view,
                content="Click a button below to get the corresponding role!"
            )
            
            log.info("Created role panel with %d roles in guild %d", len(role_objects), interaction.guild.id)
            
        except Exception as e:
            log.error("Failed to create role panel from modal: %s", e)
            await interaction.response.send_message(
                f"❌ Error creating role panel: {e}",
                ephemeral=True
            )
    
    async def _handle_panel_role_button(self, interaction: discord.Interaction, role: discord.Role) -> None:
        """Handle role button clicks from a panel."""
        try:
            member = interaction.user
            if isinstance(member, discord.Member):
                # Toggle role
                if role in member.roles:
                    await member.remove_roles(role, reason="Panel role toggle")
                    await interaction.response.send_message(
                        f"✅ Removed role: {role}",
                        ephemeral=True
                    )
                else:
                    await member.add_roles(role, reason="Panel role click")
                    await interaction.response.send_message(
                        f"✅ Added role: {role}",
                        ephemeral=True
                    )
            else:
                await interaction.response.send_message(
                    "❌ Error: Could not process role assignment.",
                    ephemeral=True
                )
        except Exception as e:
            log.error("Failed to handle panel role button: %s", e)
            await interaction.response.send_message(
                f"❌ Error: {e}",
                ephemeral=True
            )


async def setup(bot: KairoBot) -> None:
    """Called by discord.py when this extension is loaded."""
    await bot.add_cog(RolesCog(bot))