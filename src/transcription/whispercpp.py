"""whisper.cpp backend (Vulkan GPU acceleration, works on AMD/Intel/NVIDIA on Windows).

Wraps ``pywhispercpp`` so it exposes the same ``transcribe(...)`` signature and
return shape as ``faster_whisper.WhisperModel``: ``(segments, info)``.
"""

from __future__ import annotations

import os
from types import SimpleNamespace

from core.config import ConfigManager

# faster-whisper style names -> whisper.cpp ggml model names
_MODEL_ALIASES = {
    "large": "large-v3",
}


class WhisperCppModel:
    def __init__(self, model: str, use_gpu: bool = True):
        from pywhispercpp.model import Model  # imported lazily: optional dependency

        model = _MODEL_ALIASES.get(model, model)
        self._model = Model(
            model,
            context_params={"use_gpu": use_gpu, "flash_attn": use_gpu},
            n_threads=max(1, (os.cpu_count() or 4) // 2),
            print_realtime=False,
            print_progress=False,
            print_timestamps=False,
            print_special=False,
        )

    def transcribe(
        self,
        audio,
        language=None,
        initial_prompt=None,
        condition_on_previous_text=True,
        temperature=0.0,
        vad_filter=False,
    ):
        params = {"temperature": float(temperature or 0.0)}
        if language:
            params["language"] = language
        if initial_prompt:
            params["initial_prompt"] = initial_prompt
        # whisper.cpp: no_context=True == do not condition on previous text
        params["no_context"] = not condition_on_previous_text

        segments = self._model.transcribe(audio, **params)
        return [SimpleNamespace(text=s.text) for s in segments], None

    def close(self) -> None:
        """Free the whisper.cpp context now (this releases its VRAM)."""
        model, self._model = self._model, None
        ctx = getattr(model, "_ctx", None)
        if ctx is not None:
            import _pywhispercpp as pw

            pw.whisper_free(ctx)
            model._ctx = None  # Model.__del__ must not free it a second time


def create_whispercpp_model(model_name_or_path: str) -> WhisperCppModel:
    ConfigManager.console_print(f"Loading whisper.cpp model '{model_name_or_path}' (Vulkan GPU)...")
    return WhisperCppModel(model_name_or_path, use_gpu=True)


__all__ = ["WhisperCppModel", "create_whispercpp_model"]
