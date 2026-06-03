from __future__ import annotations

import numpy as np

from core.config import ConfigManager
from transcription.model_factory import create_local_model


def transcribe_local(audio_data, local_model=None):
    """Transcribe an audio file using a local model."""
    if not local_model:
        local_model = create_local_model()
    model_options = ConfigManager.get_config_section("model_options")

    audio_data_float = audio_data.astype(np.float32) / 32768.0

    response = local_model.transcribe(
        audio=audio_data_float,
        language=model_options["common"]["language"],
        initial_prompt=model_options["common"]["initial_prompt"],
        condition_on_previous_text=model_options["local"]["condition_on_previous_text"],
        temperature=model_options["common"]["temperature"],
        vad_filter=model_options["local"]["vad_filter"],
    )
    return "".join([segment.text for segment in list(response[0])])

__all__ = ["transcribe_local"]
