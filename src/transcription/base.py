from __future__ import annotations

from core.config import ConfigManager
from transcription.api import transcribe_api
from transcription.cleanup import get_cleaner
from transcription.local import transcribe_local
from transcription.postprocess import clean_transcription, post_process_transcription


def transcribe(audio_data, local_model=None):
    """Transcribe audio data using the OpenAI API or a local model, depending on config."""
    if audio_data is None:
        return ""

    if ConfigManager.get_config_value("model_options", "use_api"):
        transcription = transcribe_api(audio_data)
    else:
        transcription = transcribe_local(audio_data, local_model)

    # Drop Whisper's markers first so the LLM never sees them, then optionally let it tidy the text.
    transcription = clean_transcription(transcription)
    transcription = get_cleaner().clean(transcription)
    return post_process_transcription(transcription)

__all__ = ["transcribe"]
