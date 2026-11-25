## Whisper Writer

A Python application for transcription and audio processing with a GUI.

### Features
- Real-time transcription
- Audio file processing
- Customizable settings
- Keyboard shortcuts
- Logging and debugging

### Installation
GPU acceleration (AMD/Intel/NVIDIA via Vulkan) uses a locally built `pywhispercpp` wheel that is
not committed to git. Prerequisites: Visual Studio 2022 C++ tools, the Vulkan SDK
(`scoop install vulkan`) and `uv`. Then:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
```
This builds the wheel into `vendor/` on first run (~5-10 min) and runs `uv sync`.
Set `model_options.local.device: vulkan` in `config.yaml` (the default).

### Configuration
Edit `src/config.yaml` to customize:
- Model settings
- Audio input/output paths
- UI preferences

### Key Components
- `main.py`: Application entry point
- `audio.py`: Audio processing logic
- `transcription.py`: Speech-to-text functionality
- `model.py`: Machine learning model integration
- `ui/`: Graphical user interface components

### Usage
1. Run `src/main.py`
2. Use keyboard shortcuts (see `keylistener.py`)
3. Configure settings via `Settings Window`

### Logging
Configured via `src/logging.conf` for debugging

### Building
To build a standalone executable:
```bash
pyinstaller whisper-writer.spec
```
The output will be in `dist/whisper-writer/`.

### Contributing
1. Clone repository
2. Install dependencies
3. Run tests (not yet implemented)
4. Submit pull requests