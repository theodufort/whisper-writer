# Whisper Writer

**Press a hotkey, speak, and your words are typed into whatever app has focus.**
Speech recognition runs **locally on your graphics card**, so nothing leaves your PC, there is no
subscription, and it works with **AMD, NVIDIA and Intel GPUs** (through Vulkan).

![Whisper Writer demo](assets/ww-demo-image.gif)

* **Fast and private** – [OpenAI Whisper](https://github.com/openai/whisper) running through
  [whisper.cpp](https://github.com/ggml-org/whisper.cpp) on the GPU. A few seconds of speech take a fraction of a second.
* **Types where your cursor is** – any editor, browser, chat, terminal.
* **Optional AI tidy-up** – a small local LLM (1–4 B parameters, also on the GPU) fixes misheard words,
  punctuation and filler words before the text is typed. See [Transcript cleanup](docs/transcript-cleanup.md).
* **Gentle on your GPU memory** – models are loaded only while you are dictating and released afterwards.
* **Tray app with a settings window**, four recording modes, and an optional standalone `.exe`.
* **Cloud option** – can instead use the OpenAI API (or any compatible server) if you prefer.

> Based on [WhisperWriter by savbell](https://github.com/savbell/whisper-writer), reworked for GPU-accelerated
> local transcription. Licensed under GPL-3.0.

---

## Contents

* [Requirements](#requirements)
* [Install](#install)
* [Use it](#use-it)
* [Settings](#settings)
* [Transcript cleanup](#transcript-cleanup-optional)
* [Build a standalone .exe](#build-a-standalone-exe)
* [Troubleshooting](#troubleshooting)
* [Project layout](#project-layout)
* [Documentation index](#documentation)

---

## Requirements

| | |
|---|---|
| **OS** | Windows 10 or 11 (64-bit). The GPU build scripts are Windows-only; see [GPU acceleration](docs/gpu-acceleration.md#other-platforms). |
| **GPU** | Any GPU with a Vulkan driver: AMD Radeon, NVIDIA GeForce, Intel Arc/Xe. Current graphics drivers include Vulkan. With no usable GPU the app still works, on the CPU, only slower. |
| **GPU memory** | ~0.3 GB for the default `base` model, ~0.7 GB for `small`; **+2.2 GB** if you enable the cleanup model. See [sizing](docs/gpu-acceleration.md#how-much-gpu-memory-do-i-need). |
| **Disk** | ~1 GB for the app and Python packages, plus the models you download (150 MB – 3 GB for Whisper, ~2 GB for the cleanup model). |
| **Build tools** (one-time) | `uv`, Visual Studio C++ build tools and the Vulkan SDK. The setup script can install them for you. Only needed to **install from source**; a built `.exe` needs none of them. |
| **Internet** | For the install, and the first download of each model. Afterwards everything works offline. |

## Install

Open **PowerShell** and run:

```powershell
git clone https://github.com/theodufort/whisper-writer.git
cd whisper-writer
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1 -InstallPrerequisites
```

That single script:

1. installs anything missing (`uv`, Visual Studio C++ build tools, Vulkan SDK) via `winget` – Windows may ask for permission;
2. **compiles the GPU versions of whisper.cpp and llama.cpp once** (about 10 minutes; PyPI only offers CPU-only builds for Windows);
3. installs Python and all dependencies into `.venv` with `uv sync`.

Already have the tools? Drop `-InstallPrerequisites`. If a tool is missing, the script tells you exactly what to
install and the command to do it. Nothing is installed system-wide except those tools; the app itself lives in the folder.

**Check that the GPU is found** (takes a second, downloads nothing):

```powershell
uv run python scripts/check_gpu.py
```

You should see a line like `ggml_vulkan: 0 = AMD Radeon RX 6700 XT …` naming your graphics card.

**Start the app:**

```powershell
uv run python src/main.py
```

On the very first start no settings exist yet, so the **Settings** window opens. Review the defaults and save.
The first dictation then downloads the Whisper model (a few hundred MB, once). If it seems stuck on
“transcribing”, that is the download: see [Troubleshooting](docs/troubleshooting.md#transcribing-never-ends-the-first-time).

## Use it

1. Put the cursor where you want text, in any application.
2. Press the **activation hotkey** (default **`Ctrl+Shift+Space`**) and speak.
3. The text is typed for you. Press the hotkey again to stop (in *continuous* mode).

The **recording mode** (Settings → Recording options) decides when recording ends:

| Mode | Behaviour |
|---|---|
| `continuous` *(default)* | Keeps listening: after each pause in your speech the text is typed and recording restarts, until you press the hotkey again. |
| `voice_activity_detection` | Records until you pause, types the text, then waits for the next hotkey press. |
| `press_to_toggle` | Hotkey starts recording; pressing it again stops and types. |
| `hold_to_record` | Records while the hotkey is held down. |

A small status window shows *recording / transcribing / error*, and the app lives in the system tray
(right-click the icon for settings or **Exit**). Command-line flags: `--tray` (start hidden in the tray),
`--startup` (silent start for auto-launch), `--show` (force the main window).

## Settings

Everything is configurable in the Settings window and saved to `config.yaml` (created on first save, ignored by git).
The most useful options:

| Setting | What it does |
|---|---|
| `model_options.local.model` | Whisper model size: `tiny` / `base` / `small` / `medium` / `large-v3`, plus English-only `.en` variants. Bigger is more accurate and slower. |
| `model_options.local.device` | `vulkan` (default, any GPU), `cpu`, or `cuda` (NVIDIA via faster-whisper). |
| `model_options.common.language` | Language code such as `en`, `fr`, `de`; leave empty to auto-detect. |
| `model_options.local.unload_when_idle` | Free the GPU memory between dictations (default `true`). |
| `model_options.cleanup.enabled` | Turn the AI tidy-up on. |
| `recording_options.activation_key` / `recording_mode` | The hotkey and how recording ends. |
| `model_options.use_api` | Use the OpenAI API (or a compatible server) instead of the local model. |

All settings, with defaults and descriptions, are in the **[configuration reference](docs/configuration.md)**.

## Transcript cleanup (optional)

Whisper sometimes mishears a word or leaves out punctuation. With cleanup enabled, each transcript passes
through a small instruction-following model that fixes it before typing:

| What you said (as transcribed) | What gets typed |
|---|---|
| `hey can ou send me the report by friday thanks` | `Hey, can you send me the report by Friday? Thanks` |
| `i want you to create a web app in next js with type script` | `I want you to create a web app in Next.js with TypeScript.` |

It is **off by default**. Enable it in Settings (`model_options.cleanup.enabled`); the model (Qwen2.5-3B,
about 2 GB) downloads on first use and runs on the GPU. If it ever fails or produces something odd, your
original text is typed instead. Details, model choices and safety checks: **[docs/transcript-cleanup.md](docs/transcript-cleanup.md)**.

## Build a standalone .exe

To get a double-clickable app with no Python installed:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build.ps1
```

The result is `dist\whisper-writer\whisper-writer.exe` (keep the `_internal` folder next to it). **Re-running the
script replaces the program but keeps your `config.yaml`.** The `.exe` includes the GPU libraries, so it runs on any
Windows PC with a Vulkan graphics driver, with no build tools needed there. More in
**[docs/building-the-exe.md](docs/building-the-exe.md)**.

## Troubleshooting

| Problem | Where to look |
|---|---|
| Setup says a tool is missing | Re-run with `-InstallPrerequisites`, or follow the printed command. |
| Stuck on “transcribing” the first time | It is downloading the model; check `whisperwriter.log`. |
| It is slow / I think the GPU is not used | `uv run python scripts/check_gpu.py`, then [Troubleshooting](docs/troubleshooting.md#the-gpu-is-not-being-used). |
| Nothing is typed / hotkey does nothing | [Troubleshooting](docs/troubleshooting.md#the-hotkey-does-nothing-or-text-is-not-typed). |
| Where are the logs? | `whisperwriter.log`, in the folder you started the app from. |

The full list is in **[docs/troubleshooting.md](docs/troubleshooting.md)**.

## Project layout

```
src/                     The application (Python, PyQt5)
  main.py                App start-up, tray, windows, ties hotkey → recording → transcription → typing
  result_thread.py       One dictation: record the microphone, transcribe, hand the text back
  transcription/         Speech-to-text and text clean-up (see docs/architecture.md)
  audio/  input/  ui/    Microphone capture · hotkey listening and typing · windows
  core/config/           Settings: schema + config.yaml
  config_schema.yaml     Every setting, its default and description (single source of truth)
scripts/                 setup.ps1, build.ps1, GPU wheel builders, check_gpu.py, docs generator
docs/                    Documentation
vendor/                  Locally built GPU wheels (created by setup.ps1, not committed)
whisper-writer.spec      PyInstaller recipe for the .exe
```

## Documentation

| Page | For |
|---|---|
| [Configuration reference](docs/configuration.md) | Every setting, default and meaning (generated from the schema). |
| [GPU acceleration](docs/gpu-acceleration.md) | How the GPU build works, sizing, VRAM lifecycle, model cache, rebuilding. |
| [Transcript cleanup](docs/transcript-cleanup.md) | The optional local LLM that polishes transcripts. |
| [Building the .exe](docs/building-the-exe.md) | Packaging and distributing the app. |
| [Troubleshooting](docs/troubleshooting.md) | Symptoms, causes and fixes. |
| [Architecture](docs/architecture.md) | How the code fits together – for contributors. |
| [Audio capture](docs/audio-processing.md) · [Dictation flow](docs/real-time-transcription.md) | The recording pipeline in detail. |
| [Changelog](CHANGELOG.md) | What changed. |

## Contributing

Issues and pull requests are welcome. For development, run `scripts\setup.ps1` once, then
`uv run ruff check src` before submitting. After changing `src/config_schema.yaml`, regenerate the settings
reference with `uv run python scripts/generate_config_docs.py`. There is no automated test suite yet.

## License

The code is [GPL-3.0](LICENSE). Models are downloaded separately and keep their own licences: Whisper
(OpenAI) is MIT. The optional default cleanup model, Qwen2.5-3B-Instruct, is under the **`qwen-research`
licence**, so check its terms before using it commercially; the 1.5B model is Apache-2.0. See
[Transcript cleanup → Licences](docs/transcript-cleanup.md#licences).
