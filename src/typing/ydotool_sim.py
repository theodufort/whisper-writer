from __future__ import annotations

from typing.base import InputSimulator

from core.config import ConfigManager


def _run_cmd(cmd):
    """Run a shell command and exit if it fails."""
    import subprocess
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        exit(1)


class YdotoolSimulator(InputSimulator):
    def __init__(self):
        self.input_method = "ydotool"

    def typewrite(self, text: str):
        interval = ConfigManager.get_config_value("post_processing", "writing_key_press_delay")
        _run_cmd([
            "ydotool",
            "type",
            "--key-delay",
            str(interval * 1000),
            "--",
            text,
        ])

    def cleanup(self):
        pass


__all__ = ["YdotoolSimulator"]
