from __future__ import annotations

from core.config import ConfigManager


def post_process_transcription(transcription: str) -> str:
    """Apply post-processing to the transcription."""
    transcription = transcription.strip()
    post_processing = ConfigManager.get_config_section("post_processing")
    if post_processing["remove_trailing_period"] and transcription.endswith("."):
        transcription = transcription[:-1]
    if post_processing["add_trailing_space"]:
        transcription += " "
    if post_processing["remove_capitalization"]:
        transcription = transcription.lower()
    return transcription

__all__ = ["post_process_transcription"]
