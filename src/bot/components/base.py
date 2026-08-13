"""
src/bot/components/base.py
---------------------------
Components Base Classes

Defines the abstract base classes and shared utilities used by all
Kairo component types.

All renderable components inherit from KairoComponent and implement
to_dict() which returns the raw discord.py-compatible component payload.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class KairoComponent(ABC):
    """
    Abstract base class for all Kairo UI components.

    Each component represents one element in a Discord Components V2
    message payload. Components can be nested (a Container holds other
    components) or leaf nodes (a Text element contains only a string).

    All subclasses must implement to_dict() which returns the component
    in the format expected by discord.py's component system.
    """

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """
        Serialise the component to a discord.py-compatible dict.

        Returns:
            A dict conforming to the Discord Components V2 API spec.
        """

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"
