"""
src/bot/components/config_panel.py
---------------------------------
Configuration Panel Helper

A reusable configuration panel framework for building settings UIs.

Provides a structured way to create configuration interfaces with
sections, options, and automatic save/cancel functionality.

Usage:
    class ServerConfigPanel(ConfigPanel):
        def __init__(self):
            super().__init__(
                title="Server Configuration",
                description="Configure your server settings.",
                timeout=300.0
            )
            
            # Add configuration sections
            self.add_section("General", [
                ToggleOption("Welcome Messages", "enable_welcome", default=True),
                TextOption("Welcome Channel", "welcome_channel", placeholder="#welcome"),
            ])
            
            self.add_section("Moderation", [
                ChannelOption("Mod Log", "mod_log_channel"),
                RoleOption("Mod Role", "mod_role"),
            ])
        
        async def on_save(self, interaction: discord.Interaction, changes: dict) -> None:
            # Handle saving configuration
            await self.save_to_database(interaction.guild_id, changes)
            await interaction.followup.send("Configuration saved!", ephemeral=True)
    
    # In your command:
    panel = ServerConfigPanel()
    await panel.send(interaction)
"""

from __future__ import annotations

import asyncio
from typing import List, Optional, Dict, Any, Callable, TYPE_CHECKING
from dataclasses import dataclass, field

import discord

from ..core.logging import get_logger

if TYPE_CHECKING:
    from typing import Awaitable

log = get_logger(__name__)


@dataclass
class ConfigOption:
    """
    Base class for configuration options.
    
    Args:
        label: Display label for the option.
        key: Internal key used to store/access the value.
        description: Help text shown below the option.
        required: Whether this option must be set.
        default: Default value for this option.
    """
    label: str
    key: str
    description: Optional[str] = None
    required: bool = False
    default: Any = None


@dataclass
class ToggleOption(ConfigOption):
    """
    A boolean toggle option.
    
    Args:
        on_label: Label for the ON state. Defaults to "Enabled".
        off_label: Label for the OFF state. Defaults to "Disabled".
    """
    on_label: str = "Enabled"
    off_label: str = "Disabled"


@dataclass
class TextOption(ConfigOption):
    """
    A text input option.
    
    Args:
        placeholder: Placeholder text for the input.
        max_length: Maximum length of input.
        min_length: Minimum length of input.
    """
    placeholder: str = ""
    max_length: int = 255
    min_length: int = 0


@dataclass
class NumberOption(ConfigOption):
    """
    A numeric input option.
    
    Args:
        min_value: Minimum allowed value.
        max_value: Maximum allowed value.
        allow_float: Whether to allow floating-point numbers.
    """
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allow_float: bool = False


@dataclass
class ChannelOption(ConfigOption):
    """
    A channel selection option.
    
    Args:
        channel_types: List of allowed channel types.
        allow_none: Whether to allow None/clear selection.
    """
    channel_types: List[discord.ChannelType] = field(default_factory=lambda: [
        discord.ChannelType.text, 
        discord.ChannelType.announcement,
        discord.ChannelType.public_thread,
        discord.ChannelType.private_thread,
    ])
    allow_none: bool = True


@dataclass
class RoleOption(ConfigOption):
    """
    A role selection option.
    
    Args:
        allow_none: Whether to allow None/clear selection.
        allow_multiple: Whether to allow multiple role selection.
    """
    allow_none: bool = True
    allow_multiple: bool = False


@dataclass
class SelectOption(ConfigOption):
    """
    A select menu option with predefined choices.
    
    Args:
        choices: List of (value, label) tuples for the select menu.
        allow_multiple: Whether to allow multiple selection.
    """
    choices: List[tuple[str, str]] = field(default_factory=list)
    allow_multiple: bool = False


@dataclass
class ConfigSection:
    """
    A section in a configuration panel.
    
    Args:
        title: Title of the section.
        description: Description shown at the top of the section.
        options: List of ConfigOption objects in this section.
        custom_id: Optional custom ID for this section.
    """
    title: str
    description: Optional[str] = None
    options: List[ConfigOption] = field(default_factory=list)
    custom_id: Optional[str] = None


class ConfigPanel(discord.ui.LayoutView):
    """
    A reusable configuration panel for server settings.
    
    Provides a structured interface for configuring multiple options
    with automatic Save and Cancel buttons.
    
    Args:
        title: Title of the configuration panel.
        description: Description shown at the top.
        timeout: Timeout in seconds. Defaults to 600.
        ephemeral: Whether the panel is ephemeral. Defaults to True.
        save_label: Label for the Save button. Defaults to "Save".
        cancel_label: Label for the Cancel button. Defaults to "Cancel".
    """
    
    def __init__(
        self,
        title: str,
        description: str = "",
        timeout: float = 600.0,
        ephemeral: bool = True,
        save_label: str = "Save",
        cancel_label: str = "Cancel",
    ) -> None:
        super().__init__(timeout=timeout)
        
        self.title = title
        self.description = description
        self.ephemeral = ephemeral
        self.save_label = save_label
        self.cancel_label = cancel_label
        
        # State
        self._sections: List[ConfigSection] = []
        self._values: Dict[str, Any] = {}
        self._original_values: Dict[str, Any] = {}
        self._changes: Dict[str, Any] = {}
        self._initialized: bool = False
        
        # Callbacks
        self._on_save: Optional[Callable[[discord.Interaction, Dict[str, Any]], Awaitable[Any]]] = None
        self._on_cancel: Optional[Callable[[discord.Interaction], Awaitable[Any]]] = None
        
        # Buttons
        self._save_button = discord.ui.Button(
            label=save_label,
            style=discord.ButtonStyle.success,
            custom_id="config:save",
        )
        self._cancel_button = discord.ui.Button(
            label=cancel_label,
            style=discord.ButtonStyle.secondary,
            custom_id="config:cancel",
        )
        
        # Set callbacks
        self._save_button.callback = self._on_save_click  # type: ignore[method-assign]
        self._cancel_button.callback = self._on_cancel_click  # type: ignore[method-assign]
        
        # Render the panel
        self._render()
    
    def add_section(self, title: str, options: List[ConfigOption], description: str = "") -> None:
        """
        Add a configuration section to the panel.
        
        Args:
            title: Title of the section.
            options: List of ConfigOption objects in this section.
            description: Optional description for the section.
        """
        section = ConfigSection(
            title=title,
            description=description,
            options=options,
        )
        self._sections.append(section)
        
        # Initialize default values
        for option in options:
            self._values[option.key] = option.default
            self._original_values[option.key] = option.default
    
    def set_value(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: The option key.
            value: The value to set.
        """
        if key in self._values:
            old_value = self._values[key]
            self._values[key] = value
            
            # Track changes if different from original
            if not self._initialized:
                self._original_values[key] = value
            elif old_value != value:
                self._changes[key] = value
    
    def get_value(self, key: str) -> Any:
        """Get a configuration value by key."""
        return self._values.get(key)
    
    def get_changes(self) -> Dict[str, Any]:
        """Get all changed values (different from original)."""
        changes = {}
        for key in self._values:
            if self._values[key] != self._original_values.get(key):
                changes[key] = self._values[key]
        return changes
    
    def initialize_from_dict(self, data: Dict[str, Any]) -> None:
        """
        Initialize panel values from a dictionary.
        
        Args:
            data: Dictionary of key-value pairs.
        """
        for key, value in data.items():
            if key in self._values:
                self._values[key] = value
                self._original_values[key] = value
        self._initialized = True
    
    def _render(self) -> None:
        """Render the configuration panel."""
        self.clear_items()
        
        # Header
        header_container = discord.ui.Container(
            discord.ui.TextDisplay(f"# {self.title}"),
            discord.ui.Separator(visible=True),
        )
        if self.description:
            header_container.add_item(discord.ui.TextDisplay(self.description))
            header_container.add_item(discord.ui.Separator(visible=True))
        self.add_item(header_container)
        
        # Render each section
        for section in self._sections:
            section_container = self._render_section(section)
            self.add_item(section_container)
        
        # Navigation/Action buttons
        action_row = discord.ui.ActionRow(
            self._cancel_button,
            self._save_button,
        )
        action_container = discord.ui.Container(action_row)
        self.add_item(action_container)
    
    def _render_section(self, section: ConfigSection) -> discord.ui.Container:
        """Render a configuration section."""
        items = []
        
        # Section title
        items.append(discord.ui.TextDisplay(f"## {section.title}"))
        if section.description:
            items.append(discord.ui.TextDisplay(section.description))
        items.append(discord.ui.Separator(visible=True))
        
        # Render options
        for option in section.options:
            option_item = self._render_option(option)
            items.append(option_item)
        
        return discord.ui.Container(*items)
    
    def _render_option(self, option: ConfigOption) -> discord.ui.Container:
        """Render a configuration option."""
        current_value = self._values.get(option.key, option.default)
        
        items = [
            discord.ui.TextDisplay(f"**{option.label}**"),
        ]
        
        if option.description:
            items.append(discord.ui.TextDisplay(option.description))
        
        # Render different option types
        if isinstance(option, ToggleOption):
            items.append(self._render_toggle(option, current_value))
        elif isinstance(option, TextOption):
            items.append(self._render_text_input(option, current_value))
        elif isinstance(option, NumberOption):
            items.append(self._render_number_input(option, current_value))
        elif isinstance(option, ChannelOption):
            items.append(self._render_channel_select(option, current_value))
        elif isinstance(option, RoleOption):
            items.append(self._render_role_select(option, current_value))
        elif isinstance(option, SelectOption):
            items.append(self._render_select(option, current_value))
        else:
            # Default text display for unknown types
            items.append(discord.ui.TextDisplay(str(current_value)))
        
        return discord.ui.Container(*items)
    
    def _render_toggle(self, option: ToggleOption, value: bool) -> discord.ui.ActionRow:
        """Render a toggle button."""
        button = discord.ui.Button(
            label=option.on_label if value else option.off_label,
            style=discord.ButtonStyle.success if value else discord.ButtonStyle.secondary,
            custom_id=f"config:toggle:{option.key}",
        )
        button.callback = self._create_toggle_callback(option.key)  # type: ignore[method-assign]
        return discord.ui.ActionRow(button)
    
    def _render_text_input(self, option: TextOption, value: str) -> discord.ui.ActionRow:
        """Render a text input."""
        text_input = discord.ui.TextInput(
            label=option.label,
            custom_id=f"config:text:{option.key}",
            placeholder=option.placeholder,
            max_length=option.max_length,
            min_length=option.min_length,
            value=str(value or ""),
        )
        return discord.ui.ActionRow(text_input)
    
    def _render_number_input(self, option: NumberOption, value: Any) -> discord.ui.ActionRow:
        """Render a number input."""
        text_input = discord.ui.TextInput(
            label=option.label,
            custom_id=f"config:number:{option.key}",
            placeholder="Enter a number",
            value=str(value or ""),
        )
        return discord.ui.ActionRow(text_input)
    
    def _render_channel_select(self, option: ChannelOption, value: Any) -> discord.ui.ActionRow:
        """Render a channel select menu."""
        select = discord.ui.ChannelSelect(
            custom_id=f"config:channel:{option.key}",
            channel_types=option.channel_types,
        )
        if value:
            # Set default selection if possible
            pass  # discord.py doesn't support default values for selects yet
        return discord.ui.ActionRow(select)
    
    def _render_role_select(self, option: RoleOption, value: Any) -> discord.ui.ActionRow:
        """Render a role select menu."""
        select = discord.ui.RoleSelect(
            custom_id=f"config:role:{option.key}",
        )
        return discord.ui.ActionRow(select)
    
    def _render_select(self, option: SelectOption, value: Any) -> discord.ui.ActionRow:
        """Render a string select menu."""
        select = discord.ui.Select(
            custom_id=f"config:select:{option.key}",
            options=[discord.SelectOption(label=label, value=val) for val, label in option.choices],
            multi=option.allow_multiple,
        )
        return discord.ui.ActionRow(select)
    
    def _create_toggle_callback(self, key: str) -> Callable:
        """Create a callback for toggle buttons."""
        async def callback(interaction: discord.Interaction) -> None:
            current_value = self._values.get(key, False)
            self._values[key] = not current_value
            self._render()
            await interaction.response.edit_message(view=self)
        return callback
    
    async def _on_save_click(self, interaction: discord.Interaction) -> None:
        """Handle Save button click."""
        changes = self.get_changes()
        
        # Disable buttons to prevent multiple clicks
        self._save_button.disabled = True
        self._cancel_button.disabled = True
        self._render()
        await interaction.response.edit_message(view=self)
        
        # Call save callback if provided
        if self._on_save:
            try:
                await self._on_save(interaction, changes)
            except Exception as e:
                log.error(f"Error in save callback: {e}")
                # Re-enable buttons on error
                self._save_button.disabled = False
                self._cancel_button.disabled = False
                self._render()
                await interaction.followup.edit_message(view=self)
    
    async def _on_cancel_click(self, interaction: discord.Interaction) -> None:
        """Handle Cancel button click."""
        # Disable buttons
        self._save_button.disabled = True
        self._cancel_button.disabled = True
        self._render()
        await interaction.response.edit_message(view=self)
        
        # Call cancel callback if provided
        if self._on_cancel:
            try:
                await self._on_cancel(interaction)
            except Exception as e:
                log.error(f"Error in cancel callback: {e}")
    
    def on_save(self, callback: Callable[[discord.Interaction, Dict[str, Any]], Awaitable[Any]]) -> "ConfigPanel":
        """Set the save callback."""
        self._on_save = callback
        return self
    
    def on_cancel(self, callback: Callable[[discord.Interaction], Awaitable[Any]]) -> "ConfigPanel":
        """Set the cancel callback."""
        self._on_cancel = callback
        return self
    
    async def send(self, interaction: discord.Interaction, **kwargs: Any) -> None:
        """
        Send the configuration panel.
        
        Args:
            interaction: The interaction to respond to.
            **kwargs: Additional arguments passed to send_message.
        """
        kwargs.setdefault("ephemeral", self.ephemeral)
        await interaction.response.send_message(view=self, **kwargs)
        self._initialized = True
    
    async def update(self, interaction: discord.Interaction) -> None:
        """Update the panel after a value change."""
        self._render()
        await interaction.response.edit_message(view=self)


class QuickConfigPanel:
    """
    A simplified configuration panel for quick single-purpose settings.
    
    Use this when you need a simple configuration interface without
    the complexity of sections and options.
    
    Usage:
        panel = QuickConfigPanel(
            title="Server Settings",
            options={
                "welcome_enabled": {"type": "bool", "label": "Welcome Messages", "default": True},
                "welcome_channel": {"type": "channel", "label": "Welcome Channel", "default": None},
            }
        )
        await panel.send(interaction)
    """
    
    def __init__(
        self,
        title: str,
        options: Dict[str, Dict[str, Any]],
        description: str = "",
        timeout: float = 300.0,
        ephemeral: bool = True,
    ) -> None:
        self.panel = ConfigPanel(
            title=title,
            description=description,
            timeout=timeout,
            ephemeral=ephemeral,
        )
        
        # Add all options to a single section
        config_options = []
        for key, config in options.items():
            option_type = config.get("type", "text")
            label = config.get("label", key)
            default = config.get("default")
            description = config.get("description", "")
            
            if option_type == "bool":
                config_options.append(ToggleOption(
                    label=label,
                    key=key,
                    description=description,
                    default=default,
                ))
            elif option_type == "channel":
                config_options.append(ChannelOption(
                    label=label,
                    key=key,
                    description=description,
                    default=default,
                ))
            elif option_type == "role":
                config_options.append(RoleOption(
                    label=label,
                    key=key,
                    description=description,
                    default=default,
                ))
            elif option_type == "select":
                choices = config.get("choices", [])
                config_options.append(SelectOption(
                    label=label,
                    key=key,
                    description=description,
                    default=default,
                    choices=choices,
                ))
            else:  # text or number
                config_options.append(TextOption(
                    label=label,
                    key=key,
                    description=description,
                    default=default,
                    placeholder=config.get("placeholder", ""),
                ))
        
        self.panel.add_section(title, config_options)
    
    def on_save(self, callback: Callable[[discord.Interaction, Dict[str, Any]], Awaitable[Any]]) -> "QuickConfigPanel":
        """Set the save callback."""
        self.panel.on_save(callback)
        return self
    
    def on_cancel(self, callback: Callable[[discord.Interaction], Awaitable[Any]]) -> "QuickConfigPanel":
        """Set the cancel callback."""
        self.panel.on_cancel(callback)
        return self
    
    async def send(self, interaction: discord.Interaction, **kwargs: Any) -> None:
        """Send the configuration panel."""
        await self.panel.send(interaction, **kwargs)
    
    def __call__(self) -> ConfigPanel:
        """Return the underlying ConfigPanel."""
        return self.panel