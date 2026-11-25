from __future__ import annotations

import re

from core.config import ConfigManager

# Whisper emits non-speech markers such as "[BLANK_AUDIO]", sometimes mangled ("BBLANK_AUDIO]").
_BLANK_AUDIO = re.compile(r"\[?\s*B+LANK_AUDIO\s*\]?", re.IGNORECASE)
_NOISE_WORDS = (
    "music|silence|noise|applause|laughter|laughs|inaudible|crosstalk|background noise|"
    "no audio|unintelligible|speaking foreign language|coughing|sighs?|typing|clicking"
)
# [MUSIC], (silence), [ Music ], *applause*, plus any ALL_CAPS tag like [SOME_TAG]
_NOISE_TAG = re.compile(
    rf"\[\s*(?:{_NOISE_WORDS})\s*\]|\(\s*(?:{_NOISE_WORDS})\s*\)|\*\s*(?:{_NOISE_WORDS})\s*\*"
    r"|\[[A-Z]+(?:_[A-Z]+)+\]",
    re.IGNORECASE,
)


def clean_transcription(text: str) -> str:
    """Remove Whisper's non-speech markers and tidy the whitespace they leave behind."""
    text = _BLANK_AUDIO.sub(" ", text)
    text = _NOISE_TAG.sub(" ", text)
    text = re.sub(r"\s+([,.!?;:])", r"", text)  # no space before punctuation
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def post_process_transcription(transcription: str) -> str:
    """Apply post-processing to the transcription."""
    transcription = clean_transcription(transcription)
    if not transcription:
        return ""  # silence/noise only: type nothing (not even the trailing space)
    post_processing = ConfigManager.get_config_section("post_processing")
    if post_processing["remove_trailing_period"] and transcription.endswith("."):
        transcription = transcription[:-1]
    if post_processing["add_trailing_space"]:
        transcription += " "
    if post_processing["remove_capitalization"]:
        transcription = transcription.lower()
    return transcription

__all__ = ["clean_transcription", "post_process_transcription"]
