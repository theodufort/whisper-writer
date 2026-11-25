# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]
### Added
- **GPU-accelerated local transcription on AMD, NVIDIA and Intel GPUs** through whisper.cpp and Vulkan
  (`model_options.local.device: vulkan`, now the default). See `docs/gpu-acceleration.md`.
- **Optional transcript cleanup** with a small local LLM (1-4B, llama.cpp on the GPU) that fixes mis-heard words,
  punctuation and filler words (`model_options.cleanup.*`, off by default). See `docs/transcript-cleanup.md`.
- Models are loaded into GPU memory when a recording starts and unloaded when the session ends
  (`model_options.local.unload_when_idle`).
- Models are downloaded once into a persistent cache (`%LOCALAPPDATA%\whisper-writer\models`, configurable with
  `model_options.local.model_dir`) by a downloader that works in the windowed `.exe`.
- `scripts/setup.ps1` (one-step install that builds the GPU libraries and can install the prerequisites),
  `scripts/build.ps1` (builds the `.exe` and keeps `config.yaml`), `scripts/check_gpu.py` and
  `scripts/generate_config_docs.py`.
- Documentation: rewritten README, configuration reference, GPU, cleanup, packaging, troubleshooting and architecture guides.

### Fixed
- Whisper's `[BLANK_AUDIO]`, `[MUSIC]` and similar markers are no longer typed; silence produces no output.
- The first dictation hung on "transcribing" in the packaged `.exe` because the model downloader needed a console.
- The packaged `.exe` crashed when loading a llama.cpp model because PyQt5's outdated C++ runtime shadowed the current one.
- Errors during recording/transcription are written to the log file instead of a console that does not exist in the `.exe`.
- `whisper-writer.spec` was excluded from git by the generic `*.spec` ignore rule, so a fresh clone could not build the `.exe`. It is now tracked.

### Changed
- The Python version is pinned to 3.13 and dependencies are managed with `uv` (`pyproject.toml` / `uv.lock`).
  The outdated `requirements.txt` was removed.
- `src/model.py` now re-exports `transcription.model_factory.create_local_model`.

_Earlier unreleased changes:_
### Added
- New settings window to configure WhisperWriter.
- New main window to either start the keyboard listener or open the settings window.
- New continuous recording mode ([Issue #40](https://github.com/savbell/whisper-writer/issues/40)).
- New option to play a sound when transcription finishes ([Issue #40](https://github.com/savbell/whisper-writer/issues/40)).

### Changed
- Migrated status window from using `tkinter` to `PyQt5`.
- Migrated from using JSON to using YAML to store configuration settings.
- Upgraded to latest versions of `openai` and `faster-whisper`, including support for local API ([Issue #32](https://github.com/savbell/whisper-writer/issues/32)).

### Removed
- No longer using `keyboard` package to listen for key presses.

## [1.0.1] - 2024-01-28
### Added
- New message to identify whether Whisper was being called using the API or running locally.
- Additional hold-to-talk ([PR #28](https://github.com/savbell/whisper-writer/pull/28)) and press-to-toggle recording methods ([Issue #21](https://github.com/savbell/whisper-writer/issues/21)).
- New configuration options to:
  - Choose recording method (defaulting to voice activity detection).
  - Choose which sound device and sample rate to use.
  - Hide the status window ([PR #28](https://github.com/savbell/whisper-writer/pull/28)).

### Changed
- Migrated from `whisper` to `faster-whisper` ([Issue #11](https://github.com/savbell/whisper-writer/issues/11)).
- Migrated from `pyautogui` to `pynput` ([PR #10](https://github.com/savbell/whisper-writer/pull/10)).
- Migrated from `webrtcvad` to `webrtcvad-wheels` ([PR #17](https://github.com/savbell/whisper-writer/pull/17)).
- Changed default activation key combo from `ctrl+alt+space` to `ctrl+shift+space`.
- Changed to using a local model rather than the API by default.
- Revamped README.md, including new Roadmap, Contributing, and Credits sections.

### Fixed
- Local model is now only loaded once at start-up, rather than every time the activation key combo was pressed.
- Default configuration now auto-chooses compute type for the local model to avoid warnings.
- Graceful degradation to CPU if CUDA isn't available ([PR #30](https://github.com/savbell/whisper-writer/pull/30)).
- Removed long prefix of spaces in transcription ([PR #19](https://github.com/savbell/whisper-writer/pull/19)).

## [1.0.0] - 2023-05-29
### Added
- Initial release of WhisperWriter.
- Added CHANGELOG.md.
- Added Versioning and Known Issues to README.md.

### Changed
- Updated Whisper Python package; the local model is now compatible with Python 3.11.

[Unreleased]: https://github.com/savbell/whisper-writer/compare/v1.0.1...HEAD
[1.0.1]: https://github.com/savbell/whisper-writer/releases/tag/v1.0.0...v1.0.1
[1.0.0]: https://github.com/savbell/whisper-writer/releases/tag/v1.0.0
