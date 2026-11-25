# Building and distributing the standalone .exe

The packaged app is a normal Windows program: no Python, no `uv`, no build tools needed on the PC that runs it.

## Build

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1     # once: environment + GPU libraries
powershell -ExecutionPolicy Bypass -File scripts\build.ps1     # every time you want a new .exe
```

Output: `dist\whisper-writer\`

```
dist\whisper-writer\
  whisper-writer.exe     the program
  _internal\             Python runtime, libraries, GPU DLLs (must stay next to the exe)
  config.yaml            your settings (created by the app, kept across builds)
  whisperwriter.log      log file (when started from this folder)
```

Takes 2–3 minutes. **Exit the app first**: Windows cannot replace a running exe (the script stops with a message
if it is running).

### What the script does for you

`build.ps1` runs PyInstaller (recipe: [`whisper-writer.spec`](../whisper-writer.spec)) into a staging folder
(`build\stage`) and then **mirrors it over `dist\whisper-writer`**, replacing the exe and `_internal\` but
**keeping `config.yaml` and the logs**. Plain `pyinstaller whisper-writer.spec` would delete the whole output
folder, settings included, which is why the script exists.

## What is bundled

* Python, PyQt5 and all dependencies.
* The **GPU libraries**: the Vulkan builds of whisper.cpp and llama.cpp that `setup.ps1` compiled (these are
  listed explicitly in the spec, because PyInstaller cannot discover them itself). The build **fails with a clear
  message** instead of silently producing a CPU-only app if they are missing.
* A current `msvcp140.dll` C++ runtime. PyQt5 ships an old one that, once loaded, breaks llama.cpp (the spec removes
  Qt's copy), so the app does not depend on a Visual C++ redistributable being installed.

**Not bundled:** the Whisper and cleanup models. They are downloaded on first use into
`%LOCALAPPDATA%\whisper-writer\models` and shared by every copy of the app on that PC.

## Giving it to someone else

Zip the whole `dist\whisper-writer` folder (**without** your `config.yaml` and `.log` files, which are yours).
On the other PC:

1. unzip anywhere and run `whisper-writer.exe`;
2. the Settings window opens on first start; save, and dictate. The first dictation downloads the model
   (internet needed once).

Requirements there: Windows 10/11 64-bit and a graphics driver with Vulkan (without a GPU it runs on the CPU).
Windows SmartScreen or an antivirus may warn about an unsigned program built with PyInstaller: that is a false
positive common to such executables; only the author can fix it by code-signing.

## Start with Windows

Right-click the tray icon and tick **Auto-start**. This puts a `WhisperWriter` shortcut to the exe in your Startup
folder (`shell:startup`); untick it to remove it. It is meant for the packaged `.exe`. The shortcut starts the
app normally; if you prefer it to start hidden in the tray, edit the shortcut and add `--startup` (or `--tray`)
to its *Target*. Other flag: `--show` forces the main window.

## Logs

The log is written to `whisperwriter.log` **in the folder the program was started from** (the exe's folder when you
start it by double-click or from the Startup shortcut; the current directory when started from a terminal). The
file rotates at 5 MB and the three previous files are kept. Configuration:
`src/logging.conf`.

## Troubleshooting a build

| Message | Fix |
|---|---|
| `Vulkan DLLs not found` / `llama.cpp Vulkan DLLs not found` | Run `scripts\setup.ps1` (the GPU wheels are missing from the environment). |
| `No .venv yet` | Run `scripts\setup.ps1` first. |
| `whisper-writer is running from …` | Exit the app (tray icon → Exit) and run the script again. |
| Build works but the app crashes when loading the cleanup model | See [Troubleshooting](troubleshooting.md#the-app-crashes-or-hangs-only-in-the-packaged-exe). |
