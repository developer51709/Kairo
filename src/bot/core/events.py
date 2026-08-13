"""
src/bot/core/events.py
----------------------
Kairo Internal Event Bus

Provides a lightweight publish/subscribe event system for internal
communication between Kairo's subsystems. This is distinct from discord.py's
own event dispatching — it exists so that features can react to each other
without creating direct imports between modules (decoupled architecture).

Examples of internal events:
    - "guild_config_updated"  → automod reloads its cache
    - "moderation_action"     → logging feature records the action
    - "feature_loaded"        → dashboard updates its feature registry

Design decisions:
    - Listeners are regular async coroutines. Synchronous callables are not
      supported to keep the design uniform and avoid threading issues.
    - Errors in individual listeners are caught and logged rather than
      propagated, so one broken listener cannot silently kill others.
    - The EventBus is typically stored on the KairoBot instance and passed
      to features/cogs via dependency injection.

Usage:
    # Setup (in bot.py):
    bus = EventBus()

    # Subscribing:
    @bus.on("guild_config_updated")
    async def handle_config_update(guild_id: int) -> None:
        await reload_cache(guild_id)

    # Emitting (fire-and-forget; all listeners run concurrently):
    await bus.emit("guild_config_updated", guild_id=123456)

    # One-time listener:
    @bus.once("bot_ready")
    async def on_first_ready() -> None:
        print("Bot is ready for the first time.")

    # Removing a listener:
    bus.off("guild_config_updated", handle_config_update)
"""

import asyncio
from collections import defaultdict
from typing import Any, Awaitable, Callable

from .logging import get_logger

log = get_logger(__name__)

# Type alias for async event handlers.
AsyncHandler = Callable[..., Awaitable[None]]


class EventBus:
    """
    Async publish/subscribe event bus.

    Attributes:
        _listeners: Maps event name → list of registered handlers.
        _once:      Set of (event_name, handler) pairs that should only fire once.
    """

    def __init__(self) -> None:
        self._listeners: dict[str, list[AsyncHandler]] = defaultdict(list)
        self._once: set[tuple[str, AsyncHandler]] = set()

    # ------------------------------------------------------------------ #
    # Subscription                                                         #
    # ------------------------------------------------------------------ #

    def on(self, event: str) -> Callable[[AsyncHandler], AsyncHandler]:
        """
        Decorator that registers a persistent async listener for an event.

        Args:
            event: The event name to listen for.

        Returns:
            A decorator that registers the function and returns it unchanged.

        Example:
            @bus.on("guild_config_updated")
            async def handler(guild_id: int) -> None:
                ...
        """
        def decorator(func: AsyncHandler) -> AsyncHandler:
            self.subscribe(event, func)
            return func
        return decorator

    def once(self, event: str) -> Callable[[AsyncHandler], AsyncHandler]:
        """
        Decorator that registers a one-time listener for an event.

        The handler is automatically removed after its first invocation.

        Args:
            event: The event name to listen for.

        Example:
            @bus.once("bot_ready")
            async def handler() -> None:
                ...
        """
        def decorator(func: AsyncHandler) -> AsyncHandler:
            self.subscribe(event, func)
            self._once.add((event, func))
            return func
        return decorator

    def subscribe(self, event: str, handler: AsyncHandler) -> None:
        """
        Register a listener for an event.

        Args:
            event:   Event name.
            handler: Async callable to invoke when the event is emitted.
        """
        if handler not in self._listeners[event]:
            self._listeners[event].append(handler)
            log.debug("Subscribed '%s' to event '%s'.", handler.__qualname__, event)

    def off(self, event: str, handler: AsyncHandler) -> None:
        """
        Remove a previously registered listener.

        Args:
            event:   Event name.
            handler: The handler to remove.
        """
        try:
            self._listeners[event].remove(handler)
            self._once.discard((event, handler))
            log.debug("Unsubscribed '%s' from event '%s'.", handler.__qualname__, event)
        except ValueError:
            log.warning(
                "Attempted to unsubscribe '%s' from event '%s', but it was not registered.",
                handler.__qualname__,
                event,
            )

    # ------------------------------------------------------------------ #
    # Emission                                                             #
    # ------------------------------------------------------------------ #

    async def emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        """
        Emit an event, invoking all registered listeners concurrently.

        Errors raised by individual listeners are caught and logged so that
        one failing handler does not prevent others from running.

        Args:
            event:  Event name.
            *args:  Positional arguments forwarded to each listener.
            **kwargs: Keyword arguments forwarded to each listener.
        """
        listeners = list(self._listeners.get(event, []))
        if not listeners:
            log.debug("Event '%s' emitted with no listeners.", event)
            return

        log.debug("Emitting event '%s' to %d listener(s).", event, len(listeners))

        async def _safe_call(handler: AsyncHandler) -> None:
            try:
                await handler(*args, **kwargs)
            except Exception:  # noqa: BLE001
                log.exception(
                    "Unhandled exception in event listener '%s' for event '%s'.",
                    handler.__qualname__,
                    event,
                )
            finally:
                # Clean up one-time listeners after invocation.
                if (event, handler) in self._once:
                    self.off(event, handler)

        await asyncio.gather(*(_safe_call(h) for h in listeners))

    # ------------------------------------------------------------------ #
    # Introspection                                                        #
    # ------------------------------------------------------------------ #

    def listeners(self, event: str) -> list[AsyncHandler]:
        """Return a copy of the listener list for an event."""
        return list(self._listeners.get(event, []))

    def events(self) -> list[str]:
        """Return a list of all events that have at least one listener."""
        return [e for e, ls in self._listeners.items() if ls]

    def clear(self) -> None:
        """Remove all listeners from all events. Primarily useful in tests."""
        self._listeners.clear()
        self._once.clear()
