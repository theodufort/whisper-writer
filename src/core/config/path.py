from __future__ import annotations

import sys
from pathlib import Path

_SRC_DIR = Path(__file__).parent.parent
if hasattr(sys, "_MEIPASS"):
    _BUNDLE_DIR = Path(sys._MEIPASS)
    _DATA_DIR = Path(sys.executable).parent
else:
    _BUNDLE_DIR = _SRC_DIR
    _DATA_DIR = _SRC_DIR
_LOGGING_CONF = _BUNDLE_DIR / "logging.conf"
_DEFAULT_CONFIG_PATH = _DATA_DIR / "config.yaml"

def resource_path(relative_path: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        return str(Path(sys._MEIPASS) / relative_path)
    return str(_SRC_DIR.parent / relative_path)

__all__ = ["resource_path", "_BUNDLE_DIR", "_DATA_DIR", "_DEFAULT_CONFIG_PATH", "_LOGGING_CONF"]
