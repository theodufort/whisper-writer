from __future__ import annotations

import sounddevice as sd

from audio.device import query_device_rate
from core.config import ConfigManager


def open_input_stream(device, rate: int, frame_size: int, callback):
    """
    Try to open an InputStream for *device* at *rate*.
    If that fails, warn and fall back to the system default device.
    Returns (stream, actual_device, actual_rate).
    """
    try:
        stream = sd.InputStream(
            samplerate=rate,
            channels=1,
            dtype="int16",
            blocksize=frame_size,
            device=device,
            callback=callback,
        )
        stream.start()
        return stream, device, rate
    except sd.PortAudioError as exc:
        ConfigManager.console_print(
            f"Failed to open device {device} ({exc}). Falling back to system default."
        )
        fallback_rate = query_device_rate(None)
        stream = sd.InputStream(
            samplerate=fallback_rate,
            channels=1,
            dtype="int16",
            blocksize=int(fallback_rate * 0.030),
            device=None,
            callback=callback,
        )
        stream.start()
        return stream, None, fallback_rate

__all__ = ["open_input_stream"]
