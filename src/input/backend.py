from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from input.events import InputEvent, KeyCode


class InputBackend(ABC):
    """Abstract base class for input backends. This class defines the interface that all input backends must implement."""

    @classmethod
    @abstractmethod
    def is_available(cls) -> bool:
        """Check if this input backend is available on the current system.

        Returns:
            bool: True if the backend is available, False otherwise.
        """
        pass

    @abstractmethod
    def start(self):
        """Start the input backend. This method should initialize any necessary resources and begin listening for input events."""
        pass

    @abstractmethod
    def stop(self):
        """Stop the input backend. This method should clean up any resources and stop listening for input events."""
        pass

    @abstractmethod
    def on_input_event(self, event: tuple[KeyCode, InputEvent]):
        """Handle an input event. This method is called when an input event is detected.

        :param event: A tuple containing the key code and the type of event.
        """
        pass


__all__ = ["InputBackend"]
