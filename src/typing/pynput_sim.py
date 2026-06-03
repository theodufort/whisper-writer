from __future__ import annotations

import time
from typing.base import InputSimulator

from core.config import ConfigManager


class PynputInputSimulator(InputSimulator):
    def __init__(self):
        from pynput.keyboard import Controller as PynputController
        self.keyboard = PynputController()
        self.input_method = "pynput"

    def typewrite(self, text: str):
        interval = ConfigManager.get_config_value("post_processing", "writing_key_press_delay")
        for char in text:
            self.keyboard.press(char)
            self.keyboard.release(char)
            time.sleep(interval)

    def cleanup(self):
        pass


__all__ = ["PynputInputSimulator"]
