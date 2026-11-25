# -*- mode: python ; coding: utf-8 -*-

import glob
import importlib.util
import os
import sys
import tempfile

# ---------------------------------------------------------------------------------------------
# GPU libraries (Windows). PyInstaller cannot discover these native DLLs on its own, so they are
# listed explicitly. Prerequisite: `scripts/setup.ps1` (it builds and installs the Vulkan wheels).
# ---------------------------------------------------------------------------------------------
gpu_binaries = []
_OLD_QT_RUNTIME = {"msvcp140.dll", "vcruntime140.dll", "vcruntime140_1.dll"}

if sys.platform == "win32":
    # whisper.cpp (pywhispercpp): its DLLs (whisper, ggml, ggml-vulkan, vulkan-1, MSVC runtime) sit next
    # to the package in site-packages and must be at the bundle root, which the package's loader
    # registers as a DLL directory.
    _site = os.path.dirname(os.path.dirname(importlib.util.find_spec("pywhispercpp").origin))
    for _pattern in ("whisper-*.dll", "ggml*.dll", "vulkan-1-*.dll", "msvcp140-*.dll", "vcomp140-*.dll"):
        gpu_binaries += [(path, ".") for path in glob.glob(os.path.join(_site, _pattern))]
    assert any("ggml-vulkan" in src for src, _ in gpu_binaries), (
        "whisper.cpp Vulkan DLLs not found - run scripts/setup.ps1 (it builds and installs the GPU wheel)."
    )

    # llama.cpp (llama-cpp-python, used by the optional cleanup model): it loads <package>/lib/*.dll.
    _llama_lib = os.path.join(os.path.dirname(importlib.util.find_spec("llama_cpp").origin), "lib")
    _llama_dlls = glob.glob(os.path.join(_llama_lib, "*.dll"))
    assert any("ggml-vulkan" in path for path in _llama_dlls), (
        "llama.cpp Vulkan DLLs not found - run scripts/setup.ps1 (it builds and installs the GPU wheel)."
    )
    gpu_binaries += [(path, "llama_cpp/lib") for path in _llama_dlls]

    # Both libraries are built with a current MSVC and need a current msvcp140.dll. PyQt5 ships an OLD
    # copy (14.26); once Qt is loaded Windows would reuse it for them and llama.cpp would crash with an
    # access violation. So drop Qt's copies (see _is_old_qt_runtime below) and ship a current one at the
    # bundle root. This also removes the need for the Visual C++ redistributable on the target PC.
    _msvcp = os.path.join(os.environ["SystemRoot"], "System32", "msvcp140.dll")
    if os.path.isfile(_msvcp):
        gpu_binaries.append((_msvcp, "."))


def _is_old_qt_runtime(entry):
    dest = entry[0].replace("\\", "/").lower()
    return dest.startswith("pyqt5/qt5/bin/") and os.path.basename(dest) in _OLD_QT_RUNTIME


app_name = "whisper-writer"
app_version = "1.0.1"
logo_icon = "assets/ww-logo.ico"

a = Analysis(
    ["src/launcher.py"],
    pathex=["src"],
    binaries=gpu_binaries,
    datas=[
        ("src/logging.conf", "."),
        ("src/config_schema.yaml", "."),
        ("assets/microphone.png", "assets"),
        ("assets/pencil.png", "assets"),
        ("assets/check.svg", "assets"),
        ("assets/caret-down.svg", "assets"),
        ("assets/ww-logo.png", "assets"),
        ("assets/ww-logo.ico", "assets"),
        ("assets/ww-settings-demo.gif", "assets"),
        ("assets/beep.wav", "assets"),
    ],
    hiddenimports=[
        "PyQt5.QtCore",
        "PyQt5.QtGui",
        "PyQt5.QtWidgets",
        "PyQt5.QtSvg",
        "pynput._util",
        "pynput.keyboard._win32",
        "pynput.keyboard._xorg",
        "pynput.keyboard._darwin",
        "faster_whisper",
        "pywhispercpp",
        "llama_cpp",
        "_pywhispercpp",
        "ctranslate2",
        "tokenizers",
        "dotenv",
        "comtypes",
        "win32com",
        "win32com.client",
        "tray_launcher",
    ],
    hookspath=["hooks"],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

a.binaries = [e for e in a.binaries if not _is_old_qt_runtime(e)]
a.datas = [e for e in a.datas if not _is_old_qt_runtime(e)]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=tempfile.gettempdir(),
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=logo_icon,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=app_name,
)
