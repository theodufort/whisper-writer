from __future__ import annotations

import sounddevice as sd


def query_device_rate(device) -> int:
    """Return the native sample rate for the given device index (or system default)."""
    try:
        info = (
            sd.query_devices(device, "input")
            if device is not None
            else sd.query_devices(kind="input")
        )
        return int(info["default_samplerate"])
    except Exception:
        return 16000

__all__ = ["query_device_rate"]
