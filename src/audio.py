from __future__ import annotations

import numpy as np
import sounddevice as sd

from utils import ConfigManager


def resample(audio: np.ndarray, from_rate: int, to_rate: int) -> np.ndarray:
    """Resample audio from from_rate to to_rate using linear interpolation."""
    if from_rate == to_rate:
        return audio
    target_len = int(len(audio) * to_rate / from_rate)
    return np.interp(
        np.linspace(0, len(audio) - 1, target_len),
        np.arange(len(audio)),
        audio.astype(np.float32),
    ).astype(np.int16)


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
