from __future__ import annotations

import os
import signal
from typing.base import InputSimulator

from core.config import ConfigManager


def run_command_or_exit_on_failure(command):
    """Run a shell command and exit if it fails."""
    import subprocess
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        exit(1)


class DotoolSimulator(InputSimulator):
    def __init__(self):
        self.dotool_process = None
        self._initialize_dotool()

    def _initialize_dotool(self):
        import subprocess
        self.dotool_process = subprocess.Popen("dotool", stdin=subprocess.PIPE, text=True)
        assert self.dotool_process.stdin is not None

    def _terminate_dotool(self):
        if self.dotool_process:
            os.kill(self.dotool_process.pid, signal.SIGINT)
            self.dotool_process = None

    def typewrite(self, text: str):
        interval = ConfigManager.get_config_value("post_processing", "writing_key_press_delay")
        assert self.dotool_process and self.dotool_process.stdin
        self.dotool_process.stdin.write(f"typedelay {interval * 1000}\n")
        self.dotool_process.stdin.write(f"type {text}\n")
        self.dotool_process.stdin.flush()

    def cleanup(self):
        self._terminate_dotool()


__all__ = ["DotoolSimulator"]
