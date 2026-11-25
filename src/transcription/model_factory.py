from __future__ import annotations

import gc
import logging
import threading

from faster_whisper import WhisperModel

from core.config import ConfigManager

logger = logging.getLogger("whisperwriter.utils")


def _load_model():
    """Load the local model onto the configured device (whisper.cpp/Vulkan or faster-whisper)."""
    ConfigManager.console_print("Creating local model...")
    local_model_options = ConfigManager.get_config_section("model_options")["local"]
    compute_type = local_model_options["compute_type"]
    model_path = local_model_options.get("model_path")

    if local_model_options["device"] == "vulkan":
        # whisper.cpp + Vulkan: GPU acceleration on AMD (and Intel/NVIDIA) GPUs.
        from transcription.whispercpp import create_whispercpp_model

        model = create_whispercpp_model(model_path or local_model_options["model"])
        ConfigManager.console_print("Local model created.")
        return model

    if compute_type == "int8":
        device = "cpu"
        ConfigManager.console_print("Using int8 quantization, forcing CPU usage.")
    else:
        device = local_model_options["device"]

    try:
        if model_path:
            ConfigManager.console_print(f"Loading model from: {model_path}")
            model = WhisperModel(
                model_path, device=device, compute_type=compute_type, download_root=None
            )
        else:
            model = WhisperModel(
                local_model_options["model"], device=device, compute_type=compute_type
            )
    except Exception as e:
        ConfigManager.console_print(f"Error initializing WhisperModel: {e}")
        ConfigManager.console_print("Falling back to CPU.")
        model = WhisperModel(
            model_path or local_model_options["model"],
            device="cpu",
            compute_type=compute_type,
            download_root=None if model_path else None,
        )

    ConfigManager.console_print("Local model created.")
    return model

class ManagedModel:
    """A local model that is loaded on demand and can be unloaded to free (V)RAM.

    All access is serialised by one lock, so ``unload()`` waits for an in-flight
    transcription and ``transcribe()`` transparently reloads after an unload.
    """

    def __init__(self, loader=_load_model):
        self._loader = loader
        self._model = None
        self._lock = threading.RLock()

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def load(self) -> None:
        with self._lock:
            if self._model is None:
                try:
                    self._model = self._loader()
                except Exception:
                    logger.exception("Failed to load the local model")
                    raise

    def unload(self) -> None:
        with self._lock:
            model, self._model = self._model, None
            if model is None:
                return
            close = getattr(model, "close", None)
            if close:
                close()
            del model
            gc.collect()
            ConfigManager.console_print("Local model unloaded (VRAM freed).")

    def transcribe(self, *args, **kwargs):
        with self._lock:
            self.load()
            segments, info = self._model.transcribe(*args, **kwargs)
            # faster-whisper yields segments lazily: consume them while the model is loaded
            return list(segments), info


def create_local_model() -> ManagedModel:
    """Create the managed local model. It is loaded now, or lazily if unload_when_idle is on."""
    model = ManagedModel()
    if not ConfigManager.get_config_section("model_options")["local"].get("unload_when_idle", True):
        model.load()
    return model


__all__ = ["ManagedModel", "create_local_model"]
