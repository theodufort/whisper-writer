from __future__ import annotations

from abc import ABC, abstractmethod


class InputSimulator(ABC):
    """Abstract base class for input simulators."""

    @abstractmethod
    def typewrite(self, text: str):
        pass

    @abstractmethod
    def cleanup(self):
        pass


__all__ = ["InputSimulator"]
