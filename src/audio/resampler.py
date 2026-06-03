from __future__ import annotations

import numpy as np


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

__all__ = ["resample"]
