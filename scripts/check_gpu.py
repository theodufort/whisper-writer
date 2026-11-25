"""Check that the GPU-accelerated parts are installed and can see a GPU.

Usage:  uv run python scripts/check_gpu.py

It does not load any model, so it runs in a second and downloads nothing. Lines starting with
"ggml_vulkan" come straight from the native libraries and name the GPU they will use.
"""

from __future__ import annotations

import os
import platform
import sys
from pathlib import Path


def main() -> int:
    print(f"Python {platform.python_version()} on {platform.system()} {platform.release()}")
    ok = True

    try:
        import _pywhispercpp  # noqa: F401
        import pywhispercpp  # noqa: F401

        print("[ok]   pywhispercpp (whisper.cpp) is installed")
    except ImportError as exc:
        ok = False
        print(f"[FAIL] pywhispercpp: {exc}")
        print("       Run scripts\\setup.ps1 to build and install the GPU version.")

    try:
        import llama_cpp

        offload = bool(llama_cpp.llama_supports_gpu_offload())
        print(f"[{'ok' if offload else 'WARN'}]   llama.cpp {llama_cpp.__version__}: "
              f"GPU offload {'supported' if offload else 'NOT supported (CPU-only build)'}")
        if not offload:
            print("       The cleanup model will run on the CPU.")
            print("       Run scripts\\setup.ps1 -Rebuild to get the GPU build.")
    except ImportError as exc:
        ok = False
        print(f"[FAIL] llama-cpp-python: {exc}")
        print("       Run scripts\\setup.ps1 to build and install the GPU version.")

    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / ".cache")
    print(f"Models are cached in: {Path(base) / 'whisper-writer' / 'models'}")
    print(
        "If no 'ggml_vulkan: ... Found N Vulkan devices' line appeared above, update your "
        "GPU driver (Vulkan ships with AMD, NVIDIA and Intel graphics drivers)."
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
