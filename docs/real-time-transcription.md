# Dictation flow: from audio to typed text

How a finished recording becomes text on your screen. Source: `src/transcription/` and `src/main.py`.

> "Real time" here means *fast*, not *streaming*: the app waits for you to finish a phrase (a pause, or the hotkey)
> and then transcribes that whole phrase, typically in a fraction of a second on a GPU. It does not show words
> while you are still speaking, and it does not do timestamps or speaker separation.

## Steps

1. **Transcribe** (`transcription/base.py → transcribe`)
   * `model_options.use_api: false` (default): the local model. With `local.device: vulkan` that is
     whisper.cpp on the GPU; other devices use faster-whisper. Audio is converted to 32-bit floats and passed with the
     language (`common.language`, empty = auto-detect), an optional `initial_prompt`, and the temperature.
   * `use_api: true`: the audio is sent as a WAV file to an OpenAI-compatible endpoint (`api.base_url`, `api.model`,
     `api.api_key`). The key is read from the **`OPENAI_API_KEY` environment variable**; set it in Windows before
     starting the app. (The Settings window also writes it to a `.env` file, but the app does not currently load that
     file.) **This is the only path where audio leaves your PC.**
2. **Remove markers.** Whisper sometimes emits non-speech tags (`[BLANK_AUDIO]`, `[MUSIC]`, `(silence)`, even mangled
   forms like `BBLANK_AUDIO]`). They are stripped by `postprocess.clean_transcription`; whisper.cpp is also told not to
   produce them (`suppress_nst`). A recording that is only silence/noise yields an empty string, and **nothing is typed**.
3. **Optional cleanup** by the local LLM (see [Transcript cleanup](transcript-cleanup.md)).
4. **Post-processing** (`post_processing.*`): remove trailing period, lowercase everything, add a trailing space (default
   on, so consecutive dictations do not run together).
5. **Typing** (`input_simulation.py`) using `post_processing.input_method` (`pynput` on Windows) with
   `writing_key_press_delay` seconds between key presses. If a target application drops characters, raise that delay.

## Models in this flow

Models are loaded when a recording starts (in the background, while you speak) and released when the session ends;
see [GPU acceleration](gpu-acceleration.md#when-models-are-loaded-and-unloaded).

## Recording modes in terms of this flow

* `continuous`: steps 1–5 repeat automatically after each pause; the session lasts until you press the hotkey again,
  and models stay loaded in between.
* `voice_activity_detection`, `press_to_toggle`, `hold_to_record`: one pass per hotkey press; models unload afterwards
  (unless `unload_when_idle` is `false`).
