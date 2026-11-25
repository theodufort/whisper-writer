# Troubleshooting

First stop for any problem: the log file **`whisperwriter.log`**, in the folder you started the app from
(for the `.exe`, the folder containing it). It names the model being loaded, downloads in progress, and the reason
for any failure. Run the app from a terminal to see the same messages live.

## Contents

* [Setup and build](#setup-and-build)
* [Transcribing never ends (the first time)](#transcribing-never-ends-the-first-time)
* [The GPU is not being used](#the-gpu-is-not-being-used)
* [The hotkey does nothing, or text is not typed](#the-hotkey-does-nothing-or-text-is-not-typed)
* [The wrong microphone is used](#the-wrong-microphone-is-used)
* [Odd or missing words in the output](#odd-or-missing-words-in-the-output)
* [Out of GPU memory](#out-of-gpu-memory)
* [The app crashes or hangs only in the packaged exe](#the-app-crashes-or-hangs-only-in-the-packaged-exe)
* [Starting over](#starting-over)

## Setup and build

**`Missing prerequisites: …` when running `scripts\setup.ps1`**
It lists what is missing and the command to install each. Run
`scripts\setup.ps1 -InstallPrerequisites` to let it do that with `winget`, or run the printed commands yourself, then re-run.
Visual Studio Build Tools is a large download (several GB); it must include the *Desktop development with C++* workload.

**`winget` is not recognised**
Install *App Installer* from the Microsoft Store, or install the three tools by hand:
[uv](https://docs.astral.sh/uv/getting-started/installation/), [Visual Studio Build Tools](https://visualstudio.microsoft.com/downloads/)
(C++ workload) and the [Vulkan SDK](https://vulkan.lunarg.com/sdk/home#windows).

**Build fails with errors about a path being too long / `exceeds the OS max path limit`**
The build must run in a short folder. The scripts use `<system drive>\ww-build`; if you passed `-Work` to a build
script, choose a shorter path. Do not run the builds from inside a deeply nested folder or the pip cache.

**`Vulkan SDK not found` even though it is installed**
Open a **new** PowerShell window (installers set environment variables for new windows only) or set `VULKAN_SDK` to the
SDK folder (the one containing `Bin\glslc.exe`). The scripts also look in `C:\VulkanSDK\*` and the scoop location.

**`uv sync` says it cannot find `pywhispercpp` or `llama-cpp-python`**
The GPU wheels in `vendor\` are missing (they are built locally, not downloaded). Run `scripts\setup.ps1`.

**`uv sync` changed `uv.lock` after I cloned**
Expected: the lock file records where the local `vendor/` index is on your machine. It does no harm.

**The build runs but PyInstaller reports missing Vulkan DLLs**
Run `scripts\setup.ps1` so the GPU wheels are installed in `.venv`, then `scripts\build.ps1` again.

## Transcribing never ends (the first time)

The first dictation with a model downloads it (Whisper `small`: ~490 MB; the cleanup model: ~2 GB). Until that finishes
the status window stays on *transcribing*. Check `whisperwriter.log` for lines such as
`Downloading 'small.en': 40%`. Wait for `Model downloaded to …`. It is only needed once.

If the log shows an error instead (for example a network failure), the next dictation retries. A partly downloaded file
is never used. If the download keeps failing, download the model yourself and point the app to it:

* Whisper: set `model_options.local.model_path` to the downloaded `ggml-*.bin` file
  ([models](https://huggingface.co/ggerganov/whisper.cpp/tree/main)).
* Cleanup model: set `model_options.cleanup.model_path` to a `.gguf` file.

## The GPU is not being used

1. Run `uv run python scripts/check_gpu.py`. You should see a `ggml_vulkan: … Found 1 Vulkan devices` line naming your
   card, and `[ok]` for both libraries.
   * `[FAIL] pywhispercpp` / `llama-cpp-python`: run `scripts\setup.ps1`.
   * `GPU offload NOT supported`: a CPU-only llama.cpp got installed. Run `scripts\setup.ps1 -Rebuild`.
   * No `ggml_vulkan` line: update your graphics driver; confirm with `vulkaninfo` (installed with the Vulkan SDK / drivers).
2. Check the setting: `model_options.local.device` must be `vulkan` (the log shows `Loading whisper.cpp model … (Vulkan GPU)`).
   With `auto`, `cpu` or `cuda` the app uses faster-whisper instead.
3. Watch Task Manager → Performance → GPU → *Dedicated GPU memory* while dictating. With `unload_when_idle: true` it
   rises when you start and falls when the session ends.
4. Laptops with two GPUs: Windows may run the app on the integrated one. In *Settings → System → Display → Graphics*
   set the app (`python.exe` or `whisper-writer.exe`) to *High performance*. Note that both libraries use the first
   Vulkan device.

## The hotkey does nothing, or text is not typed

* Make sure the app is running (tray icon) and the activation key in Settings is what you press
  (default `Ctrl+Shift+Space`). Some applications reserve that combination; try another.
* Text is typed by simulating the keyboard, so the target window must have focus. **Applications running as
  administrator ignore input from a normal-privilege program**: start Whisper Writer as administrator too if you
  dictate into such windows.
* Some games and secure fields block simulated typing.
* If the log says `Discarded due to being too short`, hold the key / speak a little longer
  (`recording_options.min_duration`).

## The wrong microphone is used

Settings → Recording options → *sound device*, or leave it empty for the Windows default. If the chosen device
cannot be opened (for example another app has exclusive access) the log says
`Failed to open device N … Falling back to system default`.

## Odd or missing words in the output

* `[BLANK_AUDIO]`, `[MUSIC]` and similar markers are removed automatically. A lone "you" or "thanks" typed after
  silence is a known Whisper behaviour with noise; a larger model or a quieter background reduces it.
* Mis-heard words: use a larger `model_options.local.model` (`small` or `medium`), the `.en` variant for English,
  set `common.language` instead of auto-detect, or turn on [transcript cleanup](transcript-cleanup.md).
* Text is cut at pauses in `continuous` mode: raise `recording_options.silence_duration` (milliseconds of silence that
  end an utterance, default 900).

## Out of GPU memory

Use a smaller Whisper model, the 1.5B cleanup model, or lower `cleanup.gpu_layers` (see the table in
[GPU acceleration](gpu-acceleration.md#how-much-gpu-memory-do-i-need)). Keep `unload_when_idle: true` so memory is held only
while dictating. If a model fails to load, the log says so and a transcript without cleanup is typed.

## The app crashes or hangs only in the packaged exe

Everything that works from `uv run python src/main.py` should work in the exe. If the exe misbehaves, look at its
`whisperwriter.log` first. A real example that was fixed: loading the cleanup model crashed with
`access violation reading 0x0` because PyQt5 ships an outdated C++ runtime (`msvcp140.dll`) that Windows then reused for
the newer GPU libraries. `whisper-writer.spec` removes Qt's copies and bundles a current one; if you edit the spec,
keep that block. Rebuild with `scripts\build.ps1` (not plain `pyinstaller`).

## Starting over

* **Reset settings:** delete `config.yaml` (next to the exe, or `src\config.yaml`); the Settings window reopens with defaults.
* **Free disk space / re-download models:** delete files in `%LOCALAPPDATA%\whisper-writer\models`.
* **Rebuild the environment:** delete `.venv`, then run `scripts\setup.ps1`.
* **Rebuild the GPU libraries:** `scripts\setup.ps1 -Rebuild`; build leftovers are in `<system drive>\ww-build` and can be deleted.
