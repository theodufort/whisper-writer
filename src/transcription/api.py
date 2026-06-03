from __future__ import annotations

import io
import os

import soundfile as sf
from openai import OpenAI

from core.config import ConfigManager


def transcribe_api(audio_data):
    """Transcribe an audio file using the OpenAI API."""
    model_options = ConfigManager.get_config_section("model_options")
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY") or None,
        base_url=model_options["api"]["base_url"] or "https://api.openai.com/v1",
    )

    byte_io = io.BytesIO()
    sample_rate = ConfigManager.get_config_section("recording_options").get("sample_rate") or 16000
    sf.write(byte_io, audio_data, sample_rate, format="wav")
    byte_io.seek(0)

    response = client.audio.transcriptions.create(
        model=model_options["api"]["model"],
        file=("audio.wav", byte_io, "audio/wav"),
        language=model_options["common"]["language"],
        prompt=model_options["common"]["initial_prompt"],
        temperature=model_options["common"]["temperature"],
    )
    return response.text

__all__ = ["transcribe_api"]
