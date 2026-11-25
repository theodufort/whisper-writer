# Configuration reference

> This file is generated from [`src/config_schema.yaml`](../src/config_schema.yaml) by
> `scripts/generate_config_docs.py`. Do not edit it by hand.

All settings can be changed in the app (**Settings** window) and are stored in `config.yaml`:

* running from source: `src/config.yaml`
* the packaged app: `config.yaml` next to `whisper-writer.exe`

`config.yaml` is created the first time you save settings. Any setting missing from it uses the
default listed below, so the file may contain only the values you changed. It is ignored by git.


## `model_options`

Which speech-to-text engine to use and how it behaves.

Setting names are paths inside the `model_options:` section of `config.yaml`.

| Setting | Default | Description |
|---|---|---|
| `use_api` | `false` | Toggle to choose whether to use the OpenAI API or a local Whisper model for transcription. |
| `common.language` | *(empty)* | The language code for the transcription in ISO-639-1 format. |
| `common.temperature` | `0.0` | Controls the randomness of the transcription output. Lower values make the output more focused and deterministic. |
| `common.initial_prompt` | *(empty)* | A string used as an initial prompt to condition the transcription. More info: https://platform.openai.com/docs/guides/speech-to-text/prompting |
| `api.model` | `whisper-1` | The model to use for transcription. Currently only 'whisper-1' is available. |
| `api.base_url` | `https://api.openai.com/v1` | The base URL for the API. Can be changed to use a local API endpoint. |
| `api.api_key` | *(empty)* | Your API key for the OpenAI API. Required for non-local API usage. |
| `local.model` | `base` | Which Whisper model to run locally. Larger models are more accurate but slower and use more GPU memory (tiny ~75 MB, base ~150 MB, small ~490 MB, medium ~1.5 GB, large ~3 GB). Names ending in .en are English-only and a little more accurate for English. Downloaded automatically on first use. Options: `base`, `base.en`, `tiny`, `tiny.en`, `small`, `small.en`, `medium`, `medium.en`, `large`, `large-v1`, `large-v2`, `large-v3`. |
| `local.device` | `vulkan` | Where the local Whisper model runs. vulkan = any GPU with a Vulkan driver (AMD, NVIDIA, Intel) via whisper.cpp, the recommended default; cuda = NVIDIA GPU via faster-whisper; cpu = processor only; auto = let faster-whisper choose (CPU on non-NVIDIA PCs). Options: `auto`, `cuda`, `vulkan`, `cpu`. |
| `local.compute_type` | `default` | Numeric precision for the local model. Only used by the faster-whisper devices (cuda, cpu, auto); ignored when device is vulkan. Options: `default`, `float32`, `float16`, `int8`. |
| `local.condition_on_previous_text` | `true` | Set to true to use the previously transcribed text as a prompt for the next transcription request. |
| `local.vad_filter` | `false` | Set to true to use a voice activity detection (VAD) filter to remove silence from the recording. Only used by the faster-whisper devices (cuda, cpu, auto); ignored when device is vulkan. |
| `local.model_dir` | *(empty)* | Folder where downloaded models are cached. Leave empty to use %LOCALAPPDATA%/whisper-writer/models. Models are downloaded only once. |
| `local.unload_when_idle` | `true` | Load the model into (V)RAM when a recording starts and unload it when recording stops, freeing GPU memory while idle. Set to false to keep the model loaded for the lifetime of the app (fastest response, uses VRAM constantly). |
| `local.model_path` | *(empty)* | The path to the local Whisper model. If not specified, the default model will be downloaded. |
| `cleanup.enabled` | `false` | Run the transcript through a small local LLM (1-4B) that fixes misheard words, punctuation and filler words before typing. Uses the GPU, and loads and unloads together with the Whisper model. The model (about 2 GB) is downloaded on first use. |
| `cleanup.model_repo` | `Qwen/Qwen2.5-3B-Instruct-GGUF` | Hugging Face repository of the GGUF cleanup model. Any 1-4B instruct model works, for example Qwen/Qwen2.5-1.5B-Instruct-GGUF (smaller, faster) or Qwen/Qwen2.5-3B-Instruct-GGUF. |
| `cleanup.model_file` | `qwen2.5-3b-instruct-q4_k_m.gguf` | GGUF file inside the repository above. |
| `cleanup.model_path` | *(empty)* | Path to a local GGUF file. If set, the repository settings above are ignored. |
| `cleanup.gpu_layers` | `-1` | Number of model layers to run on the GPU. -1 means all layers; 0 runs on the CPU. |
| `cleanup.min_words` | `3` | Transcripts shorter than this many words are typed as-is, without cleanup. |
| `cleanup.custom_instructions` | *(empty)* | Optional extra rules for the cleanup model, for example: Always write Whisper Writer with capitals. |


## `recording_options`

How recording is started and stopped.

Setting names are paths inside the `recording_options:` section of `config.yaml`.

| Setting | Default | Description |
|---|---|---|
| `activation_key` | `ctrl+shift+space` | The keyboard shortcut to activate the recording and transcribing process. Separate keys with a '+'. |
| `input_backend` | `auto` | The input backend to use for detecting key presses. 'auto' will try to use the best available backend. Options: `auto`, `evdev`, `pynput`. |
| `recording_mode` | `continuous` | The recording mode to use. Options include continuous (auto-restart recording after pause in speech until activation key is pressed again), voice_activity_detection (stop recording after pause in speech), press_to_toggle (stop recording when activation key is pressed again), hold_to_record (stop recording when activation key is released). Options: `continuous`, `voice_activity_detection`, `press_to_toggle`, `hold_to_record`. |
| `sound_device` | *(empty)* | The audio input device to use for recording. Select 'System default' to use your system's default microphone. |
| `sample_rate` | `16000` | The sample rate in Hz to use for recording. |
| `silence_duration` | `900` | The duration in milliseconds to wait for silence before stopping the recording. |
| `min_duration` | `100` | The minimum duration in milliseconds for a recording to be processed. Recordings shorter than this will be discarded. |


## `post_processing`

What happens to the text after it has been transcribed.

Setting names are paths inside the `post_processing:` section of `config.yaml`.

| Setting | Default | Description |
|---|---|---|
| `writing_key_press_delay` | `0.005` | The delay in seconds between each key press when writing the transcribed text. |
| `remove_trailing_period` | `false` | Set to true to remove the trailing period from the transcribed text. |
| `add_trailing_space` | `true` | Set to true to add a space to the end of the transcribed text. |
| `remove_capitalization` | `false` | Set to true to convert the transcribed text to lowercase. |
| `input_method` | `pynput` | The method to use for simulating keyboard input. Options: `pynput`, `ydotool`, `dotool`. |


## `misc`

Everything else.

Setting names are paths inside the `misc:` section of `config.yaml`.

| Setting | Default | Description |
|---|---|---|
| `print_to_terminal` | `true` | Set to true to print the script status and transcribed text to the terminal. |
| `hide_status_window` | `false` | Set to true to hide the status window during operation. |
| `noise_on_completion` | `false` | Set to true to play a noise after the transcription has been typed out. |
