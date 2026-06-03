from __future__ import annotations

from faster_whisper import WhisperModel

from core.config import ConfigManager


def create_local_model():
    """Create a local model using the faster-whisper library."""
    ConfigManager.console_print("Creating local model...")
    local_model_options = ConfigManager.get_config_section("model_options")["local"]
    compute_type = local_model_options["compute_type"]
    model_path = local_model_options.get("model_path")

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

__all__ = ["create_local_model"]
