from typing.base import InputSimulator
from typing.dotool_sim import DotoolSimulator
from typing.pynput_sim import PynputInputSimulator
from typing.ydotool_sim import YdotoolSimulator


class InputSimulator:
    """Factory class that creates the appropriate simulator based on config."""

    def __init__(self):
        from core.config import ConfigManager
        self.input_method = ConfigManager.get_config_value("post_processing", "input_method")
        if self.input_method == "pynput":
            self._simulator = PynputInputSimulator()
        elif self.input_method == "dotool":
            self._simulator = DotoolSimulator()
        elif self.input_method == "ydotool":
            self._simulator = YdotoolSimulator()
        else:
            self._simulator = PynputInputSimulator()

    def typewrite(self, text: str):
        self._simulator.typewrite(text)

    def cleanup(self):
        self._simulator.cleanup()


__all__ = ["InputSimulator"]
