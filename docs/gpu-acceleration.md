# GPU acceleration

Whisper Writer runs speech recognition (and the optional cleanup model) **on your graphics card** through
[Vulkan](https://www.vulkan.org/), the cross-vendor graphics/compute API. One build works on **AMD, NVIDIA and
Intel** GPUs, with nothing vendor-specific to install beyond your normal graphics driver.

## Contents

* [How it works](#how-it-works)
* [Why the setup script compiles things](#why-the-setup-script-compiles-things)
* [Requirements](#requirements)
* [How much GPU memory do I need?](#how-much-gpu-memory-do-i-need)
* [When models are loaded and unloaded](#when-models-are-loaded-and-unloaded)
* [Where models are stored](#where-models-are-stored)
* [Verifying the GPU is used](#verifying-the-gpu-is-used)
* [Rebuilding or upgrading the GPU libraries](#rebuilding-or-upgrading-the-gpu-libraries)
* [Choosing a different device](#choosing-a-different-device)
* [Other platforms](#other-platforms)

## How it works

| Job | Library | Why this one |
|---|---|---|
| Speech → text | [whisper.cpp](https://github.com/ggml-org/whisper.cpp) via the `pywhispercpp` Python binding | Runs the Whisper model on any Vulkan GPU. (The popular `faster-whisper` library only accelerates NVIDIA cards.) |
| Transcript cleanup | [llama.cpp](https://github.com/ggml-org/llama.cpp) via `llama-cpp-python` | Runs small GGUF language models on any Vulkan GPU. |

Both use the same underlying tensor library (`ggml`) and its Vulkan backend. They are loaded **inside the app's
own process**: no server, no extra window, no ports.

The setting that selects this is `model_options.local.device: vulkan` (the default). With `cpu` the same
whisper.cpp code runs on the processor; with `cuda` or `auto` the app falls back to `faster-whisper`.

## Why the setup script compiles things

The Python Package Index only provides **CPU-only** Windows builds of `pywhispercpp` and `llama-cpp-python`.
For GPU support they have to be compiled with Vulkan enabled. `scripts/setup.ps1` does that **once**, producing
two wheel files in `vendor/` (git-ignored):

```
vendor/pywhispercpp-<version>-cp313-cp313-win_amd64.whl
vendor/llama_cpp_python-<version>-py3-none-win_amd64.whl
```

`pyproject.toml` declares `vendor/` as a local package index for those two packages on Windows, so a normal
`uv sync` always installs the GPU builds and can never silently replace them with CPU ones.
Build time is roughly 10 minutes in total, mostly compiling the Vulkan shaders.

Two details the scripts handle for you (useful if you ever build by hand):

* **Short build folder.** The Vulkan shader sub-build creates paths close to Windows' 260-character limit, so
  building happens in `<system drive>\ww-build\…` rather than inside the repository or the pip cache.
* **Ninja + the Visual Studio compiler.** The default Visual Studio generator trips over that path limit; Ninja does not.

## Requirements

* **To run:** a GPU with a Vulkan driver (1.2 or newer is recommended). Current AMD, NVIDIA and Intel graphics
  drivers include one; if `vulkaninfo` runs and lists your GPU, you are set.
* **To build the GPU libraries (source install only):**
  [`uv`](https://docs.astral.sh/uv/), the *Desktop development with C++* tools of Visual Studio 2022
  (Build Tools is enough), and the [Vulkan SDK](https://vulkan.lunarg.com/) (for `glslc`, the shader compiler).
  `scripts\setup.ps1 -InstallPrerequisites` installs whatever is missing with `winget`.
* **To run the packaged `.exe`:** only the graphics driver.

## How much GPU memory do I need?

Values include working buffers. `base`, `small` and the 3B cleanup model were measured on an AMD Radeon RX 6700 XT; the rest are estimates from model size, so treat them as approximate.

| Component | Download | GPU memory |
|---|---|---|
| Whisper `tiny` | 75 MB | ~0.15 GB |
| Whisper `base` *(default)* | 150 MB | ~0.3 GB |
| Whisper `small` / `small.en` | 490 MB | ~0.7 GB |
| Whisper `medium` | 1.5 GB | ~2 GB |
| Whisper `large-v3` | 3 GB | ~4 GB |
| Cleanup model Qwen2.5-3B (Q4) | 2.1 GB | ~2.2 GB |
| Cleanup model Qwen2.5-1.5B (Q4) | 1.1 GB | ~1.3 GB |

Example: `small.en` + the 3B cleanup model used **2.95 GB** in total. If the GPU is short of memory, pick a
smaller Whisper model, use the 1.5B cleanup model, or set `model_options.cleanup.gpu_layers` to a lower number to
keep part of the cleanup model on the CPU.

## When models are loaded and unloaded

With `model_options.local.unload_when_idle: true` (default) **nothing sits in GPU memory while you are not dictating**:

```
app starts ........................ no model loaded (0 MB)
you press the hotkey .............. Whisper (and the cleanup model, if enabled) start loading in the background,
                                    while you are still speaking, so the wait is hidden
you finish speaking ............... transcribe → (clean up) → type
dictation session ends ............ models are unloaded, GPU memory is returned
```

In `continuous` recording mode the models stay loaded between the segments of one session and are unloaded when
you press the hotkey to stop. They are always released when the app exits.

Set `unload_when_idle: false` to keep them resident for the shortest possible response time, at the cost of
holding the memory permanently. Loading from the disk cache takes about 1–2 s for the models above.

## Where models are stored

Models are downloaded **once** and cached outside the application folder, so rebuilding, updating or deleting
the app never re-downloads them:

```
%LOCALAPPDATA%\whisper-writer\models\            Whisper models   (ggml-small.en.bin, …)
%LOCALAPPDATA%\whisper-writer\models\llm\        cleanup models   (*.gguf)
```

Change the location with `model_options.local.model_dir` (for example to a bigger drive). A model that already
exists in `pywhispercpp`'s own default cache is reused rather than downloaded again. Downloads are written to a
temporary `.part` file and only renamed when complete, so an interrupted download can never be mistaken for a
model. To free disk space just delete a file; it is fetched again when next needed.

## Verifying the GPU is used

```powershell
uv run python scripts/check_gpu.py
```

It reports whether both libraries are installed with GPU support, and the native library prints the GPU it found:

```
ggml_vulkan: Found 1 Vulkan devices:
ggml_vulkan: 0 = AMD Radeon RX 6700 XT (AMD proprietary driver) | …
[ok]   pywhispercpp (whisper.cpp) is installed
[ok]   llama.cpp 0.3.38: GPU offload supported
```

While dictating, Task Manager → Performance → GPU shows the *Dedicated GPU memory* rise by the amounts above.
With several GPUs both libraries use the first Vulkan device; to pick another for Whisper, add
`"gpu_device": N` to `context_params` in `src/transcription/whispercpp.py`.

## Rebuilding or upgrading the GPU libraries

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1 -Rebuild
```

Do this after changing the Python version or to move to newer library versions
(`scripts\build_pywhispercpp_vulkan.ps1 -Version X` / `build_llama_cpp_vulkan.ps1 -Version X`; also update the
version in `pyproject.toml` if you raise the minimum). The scripts download the source from PyPI and verify its SHA-256 before building.

## Choosing a different device

| `local.device` | Engine | Notes |
|---|---|---|
| `vulkan` *(default)* | whisper.cpp | Any GPU with a Vulkan driver. whisper.cpp runs on the CPU if it finds no usable GPU (not tested on a PC without a GPU). |
| `cpu` | faster-whisper | No GPU use. Slowest. |
| `cuda` | faster-whisper | NVIDIA only; needs the CUDA 12 and cuDNN libraries installed separately. Usually unnecessary: Vulkan is fast on NVIDIA too. |
| `auto` | faster-whisper | Lets faster-whisper choose; on AMD/Intel this means CPU. |

`compute_type` and `vad_filter` only apply to the faster-whisper devices.

## Other platforms

The application code is cross-platform in principle (upstream supports Linux input backends), but this fork's
GPU build tooling and packaging are **Windows-only and tested on Windows 11 only**. On Linux or macOS,
`scripts/setup.ps1` just runs `uv sync`, which installs the regular PyPI packages of both libraries. Those are not
tuned or tested by this project; for GPU use on Linux you would compile them yourself with Vulkan enabled
(`CMAKE_ARGS="-DGGML_VULKAN=on"`). Contributions that add and test other platforms are welcome.
