"""
src/bot/components/flow.py
---------------------------
Interactive Multi-Step Flow Helper

A stateful multi-step flow builder for creating guided user experiences
like onboarding wizards, configuration panels, or any multi-step process.

Each step can have its own layout, and navigation between steps is handled
automatically with Previous/Next buttons.

Usage:
    class OnboardingFlow(MultiStepFlow):
        def __init__(self):
            super().__init__(
                steps=[
                    Step(
                        title="Welcome",
                        content="Welcome to Kairo! Let's get started.",
                        layout_builder=self._build_welcome_step
                    ),
                    Step(
                        title="Configuration",
                        content="Configure your server settings.",
                        layout_builder=self._build_config_step
                    ),
                    Step(
                        title="Finish",
                        content="Setup complete! Thanks for using Kairo.",
                        layout_builder=self._build_finish_step
                    ),
                ],
                timeout=300.0
            )
        
        async def _build_welcome_step(self, step: Step) -> discord.ui.Container:
            return discord.ui.Container(
                discord.ui.TextDisplay(f"# {step.title}"),
                discord.ui.TextDisplay(step.content),
                discord.ui.Separator(visible=True),
            )
        
        # ... other step builders
    
    # In your command:
    flow = OnboardingFlow()
    await flow.start(interaction)
"""

from __future__ import annotations

from typing import List, Optional, Callable, Any, TYPE_CHECKING
from dataclasses import dataclass, field

import discord

from ..core.logging import get_logger

if TYPE_CHECKING:
    from typing import Awaitable

log = get_logger(__name__)


@dataclass
class Step:
    """
    Represents a single step in a multi-step flow.
    
    Args:
        title: The title of this step (displayed in the UI).
        content: The main content text for this step.
        layout_builder: Optional callable that builds the layout for this step.
                       Receives the Step instance and should return a Container or list of items.
        on_enter: Optional async callback when this step is entered.
        on_exit: Optional async callback when this step is exited.
        custom_id: Optional custom ID for this step (used for state management).
        skip_label: Optional label for skip button (if step can be skipped).
        required: Whether this step must be completed. Defaults to True.
    """
    title: str
    content: str
    layout_builder: Optional[Callable[["Step"], discord.ui.Container]] = None
    on_enter: Optional[Callable[["MultiStepFlow", int], Awaitable[Any]]] = None
    on_exit: Optional[Callable[["MultiStepFlow", int], Awaitable[Any]]] = None
    custom_id: Optional[str] = None
    skip_label: Optional[str] = None
    required: bool = True


class MultiStepFlow(discord.ui.LayoutView):
    """
    A stateful multi-step flow with automatic navigation controls.
    
    Manages a sequence of steps with Previous/Next navigation and optional
    Skip functionality. State is maintained within the flow instance.
    
    Args:
        steps: List of Step objects that define the flow.
        timeout: Timeout in seconds for the entire flow. Defaults to 600 (10 minutes).
        ephemeral: Whether the flow messages are ephemeral. Defaults to True.
        show_progress: Whether to show step progress (e.g., "Step 2 of 5"). Defaults to True.
        show_step_titles: Whether to show step titles in the navigation. Defaults to True.
        next_label: Label for the Next button. Defaults to "Next →".
        prev_label: Label for the Previous button. Defaults to "← Previous".
        skip_label: Label for the Skip button. Defaults to "Skip".
        finish_label: Label for the Finish button (last step). Defaults to "Finish".
    """
    
    def __init__(
        self,
        steps: List[Step],
        timeout: float = 600.0,
        ephemeral: bool = True,
        show_progress: bool = True,
        show_step_titles: bool = True,
        next_label: str = "Next →",
        prev_label: str = "← Previous",
        skip_label: str = "Skip",
        finish_label: str = "Finish",
    ) -> None:
        super().__init__(timeout=timeout)
        
        if not steps:
            raise ValueError("MultiStepFlow requires at least one step")
        
        self.steps = steps
        self.ephemeral = ephemeral
        self.show_progress = show_progress
        self.show_step_titles = show_step_titles
        
        # Navigation button labels
        self.next_label = next_label
        self.prev_label = prev_label
        self.skip_label = skip_label
        self.finish_label = finish_label
        
        # State
        self._current_step: int = 0
        self._completed_steps: set = set()
        self._user_data: dict = {}
        
        # Buttons
        self._prev_button = discord.ui.Button(
            label=prev_label,
            style=discord.ButtonStyle.secondary,
            custom_id="flow:prev",
            disabled=True,
        )
        self._next_button = discord.ui.Button(
            label=next_label,
            style=discord.ButtonStyle.primary,
            custom_id="flow:next",
        )
        self._skip_button: Optional[discord.ui.Button] = None
        self._finish_button = discord.ui.Button(
            label=finish_label,
            style=discord.ButtonStyle.success,
            custom_id="flow:finish",
        )
        
        # Set callbacks
        self._prev_button.callback = self._on_prev  # type: ignore[method-assign]
        self._next_button.callback = self._on_next  # type: ignore[method-assign]
        self._finish_button.callback = self._on_finish  # type: ignore[method-assign]
        
        # Render initial state
        self._render()
    
    def _get_current_step(self) -> Step:
        """Get the current Step object."""
        return self.steps[self._current_step]
    
    def _is_first_step(self) -> bool:
        """Check if currently on the first step."""
        return self._current_step == 0
    
    def _is_last_step(self) -> bool:
        """Check if currently on the last step."""
        return self._current_step == len(self.steps) - 1
    
    def _can_skip_current_step(self) -> bool:
        """Check if the current step can be skipped."""
        current_step = self._get_current_step()
        return not current_step.required and current_step.skip_label
    
    def _render(self) -> None:
        """Render the current step with navigation controls."""
        self.clear_items()
        
        current_step = self._get_current_step()
        
        # Build step content
        if current_step.layout_builder:
            step_content = current_step.layout_builder(current_step)
        else:
            step_content = self._build_default_step_content(current_step)
        
        self.add_item(step_content)
        
        # Navigation controls
        nav_container = self._build_navigation_container()
        self.add_item(nav_container)
    
    def _build_default_step_content(self, step: Step) -> discord.ui.Container:
        """Build default content container for a step."""
        items = []
        
        if self.show_step_titles:
            items.append(discord.ui.TextDisplay(f"# {step.title}"))
            items.append(discord.ui.Separator(visible=True))
        
        items.append(discord.ui.TextDisplay(step.content))
        items.append(discord.ui.Separator(visible=True))
        
        if self.show_progress:
            progress_text = f"Step {self._current_step + 1} of {len(self.steps)}"
            items.append(discord.ui.TextDisplay(progress_text))
            items.append(discord.ui.Separator(visible=True))
        
        return discord.ui.Container(*items)
    
    def _build_navigation_container(self) -> discord.ui.Container:
        """Build the navigation button container."""
        buttons = []
        
        # Previous button (disabled on first step)
        self._prev_button.disabled = self._is_first_step()
        buttons.append(self._prev_button)
        
        # Skip button (only if current step can be skipped)
        if self._can_skip_current_step():
            if self._skip_button is None:
                self._skip_button = discord.ui.Button(
                    label=self.skip_label,
                    style=discord.ButtonStyle.secondary,
                    custom_id="flow:skip",
                )
                self._skip_button.callback = self._on_skip  # type: ignore[method-assign]
            buttons.append(self._skip_button)
        
        # Next or Finish button
        if self._is_last_step():
            buttons.append(self._finish_button)
        else:
            self._next_button.disabled = self._get_current_step().required and False
            buttons.append(self._next_button)
        
        # Organize buttons into action row(s)
        action_row = discord.ui.ActionRow(*buttons)
        
        return discord.ui.Container(action_row)
    
    async def _on_prev(self, interaction: discord.Interaction) -> None:
        """Handle Previous button click."""
        if self._current_step > 0:
            # Exit current step
            await self._call_step_callback(self._get_current_step().on_exit, self._current_step, False)
            
            self._current_step -= 1
            
            # Enter new step
            await self._call_step_callback(self._get_current_step().on_enter, self._current_step, True)
            
            self._render()
            await interaction.response.edit_message(view=self)
    
    async def _on_next(self, interaction: discord.Interaction) -> None:
        """Handle Next button click."""
        if self._current_step < len(self.steps) - 1:
            # Exit current step
            await self._call_step_callback(self._get_current_step().on_exit, self._current_step, False)
            
            self._current_step += 1
            
            # Enter new step
            await self._call_step_callback(self._get_current_step().on_enter, self._current_step, True)
            
            self._render()
            await interaction.response.edit_message(view=self)
    
    async def _on_skip(self, interaction: discord.Interaction) -> None:
        """Handle Skip button click."""
        if self._can_skip_current_step():
            # Mark as completed (even though skipped)
            self._completed_steps.add(self._current_step)
            
            # Exit current step
            await self._call_step_callback(self._get_current_step().on_exit, self._current_step, False)
            
            self._current_step += 1
            
            # Enter new step
            await self._call_step_callback(self._get_current_step().on_enter, self._current_step, True)
            
            self._render()
            await interaction.response.edit_message(view=self)
    
    async def _on_finish(self, interaction: discord.Interaction) -> None:
        """Handle Finish button click (end of flow)."""
        # Exit current step
        await self._call_step_callback(self._get_current_step().on_exit, self._current_step, False)
        
        # Disable all buttons
        self._prev_button.disabled = True
        self._next_button.disabled = True
        if self._skip_button:
            self._skip_button.disabled = True
        self._finish_button.disabled = True
        self._render()
        
        await interaction.response.edit_message(view=self)
        
        # Emit completion event
        log.info("Multi-step flow completed")
    
    async def _call_step_callback(
        self, 
        callback: Optional[Callable[["MultiStepFlow", int], Awaitable[Any]]], 
        step_index: int,
        is_enter: bool
    ) -> None:
        """Safely call a step callback if it exists."""
        if callback:
            try:
                if is_enter:
                    await callback(self, step_index)
                else:
                    await callback(self, step_index)
            except Exception as e:
                log.error(f"Error in step callback: {e}")
    
    async def start(self, interaction: discord.Interaction, **kwargs: Any) -> None:
        """
        Start the multi-step flow.
        
        Args:
            interaction: The interaction to respond to.
            **kwargs: Additional arguments passed to send_message.
        """
        # Initialize state
        self._current_step = 0
        self._completed_steps = set()
        self._user_data = {}
        
        # Call on_enter for first step
        await self._call_step_callback(self._get_current_step().on_enter, self._current_step, True)
        
        # Send initial view
        kwargs.setdefault("ephemeral", self.ephemeral)
        await interaction.response.send_message(view=self, **kwargs)
        
        log.debug("Multi-step flow started with %d steps", len(self.steps))
    
    async def go_to_step(self, step_index: int, interaction: discord.Interaction) -> None:
        """
        Navigate to a specific step by index.
        
        Args:
            step_index: The index of the step to navigate to.
            interaction: The interaction to use for editing the message.
        """
        if 0 <= step_index < len(self.steps):
            # Exit current step
            await self._call_step_callback(self._get_current_step().on_exit, self._current_step, False)
            
            self._current_step = step_index
            
            # Enter new step
            await self._call_step_callback(self._get_current_step().on_enter, self._current_step, True)
            
            self._render()
            await interaction.response.edit_message(view=self)
    
    def get_user_data(self, key: str, default: Any = None) -> Any:
        """Get user data stored during the flow."""
        return self._user_data.get(key, default)
    
    def set_user_data(self, key: str, value: Any) -> None:
        """Set user data to be stored during the flow."""
        self._user_data[key] = value
    
    @property
    def current_step_index(self) -> int:
        """Get the current step index."""
        return self._current_step
    
    @property
    def is_complete(self) -> bool:
        """Check if the flow is complete (reached the last step)."""
        return self._current_step == len(self.steps) - 1


class StepBuilder:
    """
    Helper class for building steps with a fluent interface.
    
    Usage:
        builder = StepBuilder()
        flow = MultiStepFlow(
            steps=[
                builder.step("Welcome", "Welcome message")
                    .layout(self.build_welcome)
                    .on_enter(self.on_welcome_enter)
                    .required()
                    .build(),
                builder.step("Config", "Config message")
                    .skippable("Skip Setup")
                    .build(),
            ]
        )
    """
    
    def __init__(self) -> None:
        self._title: Optional[str] = None
        self._content: Optional[str] = None
        self._layout_builder: Optional[Callable[[Step], discord.ui.Container]] = None
        self._on_enter: Optional[Callable[[MultiStepFlow, int], Awaitable[Any]]] = None
        self._on_exit: Optional[Callable[[MultiStepFlow, int], Awaitable[Any]]] = None
        self._custom_id: Optional[str] = None
        self._skip_label: Optional[str] = None
        self._required: bool = True
    
    def step(self, title: str, content: str) -> "StepBuilder":
        """Start building a new step."""
        self._title = title
        self._content = content
        return self
    
    def layout(self, builder: Callable[[Step], discord.ui.Container]) -> "StepBuilder":
        """Set the layout builder for this step."""
        self._layout_builder = builder
        return self
    
    def on_enter(self, callback: Callable[[MultiStepFlow, int], Awaitable[Any]]) -> "StepBuilder":
        """Set the on_enter callback for this step."""
        self._on_enter = callback
        return self
    
    def on_exit(self, callback: Callable[[MultiStepFlow, int], Awaitable[Any]]) -> "StepBuilder":
        """Set the on_exit callback for this step."""
        self._on_exit = callback
        return self
    
    def custom_id(self, custom_id: str) -> "StepBuilder":
        """Set a custom ID for this step."""
        self._custom_id = custom_id
        return self
    
    def skippable(self, skip_label: Optional[str] = None) -> "StepBuilder":
        """Make this step skippable."""
        self._required = False
        self._skip_label = skip_label
        return self
    
    def required(self, required: bool = True) -> "StepBuilder":
        """Set whether this step is required."""
        self._required = required
        return self
    
    def build(self) -> Step:
        """Build and return the Step object."""
        if not self._title or not self._content:
            raise ValueError("Step must have title and content")
        
        return Step(
            title=self._title,
            content=self._content,
            layout_builder=self._layout_builder,
            on_enter=self._on_enter,
            on_exit=self._on_exit,
            custom_id=self._custom_id,
            skip_label=self._skip_label,
            required=self._required,
        )