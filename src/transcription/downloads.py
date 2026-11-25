"""Model cache folder and a console-safe file downloader (no tqdm: it crashes without stderr)."""

from __future__ import annotations

import os
from pathlib import Path

from core.config import ConfigManager


def models_dir() -> Path:
    """Persistent model cache: config `model_dir`, else %LOCALAPPDATA%/whisper-writer/models.

    It lives outside the app folder, so rebuilding or replacing the exe never re-downloads models.
    """
    configured = ConfigManager.get_config_value("model_options", "local", "model_dir")
    if configured:
        return Path(os.path.expandvars(str(configured))).expanduser()
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / ".cache")
    return Path(base) / "whisper-writer" / "models"


def download_file(url: str, target: Path, label: str) -> Path:
    """Download `url` to `target` atomically (via a .part file) and log progress."""
    import requests

    target.parent.mkdir(parents=True, exist_ok=True)
    part = target.with_name(target.name + ".part")
    ConfigManager.console_print(f"Downloading model '{label}' from {url} ...")
    try:
        with requests.get(url, stream=True, timeout=(15, 60)) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("content-length", 0))
            done = 0
            next_report = 10
            with part.open("wb") as fh:
                for chunk in resp.iter_content(chunk_size=1024 * 1024):
                    fh.write(chunk)
                    done += len(chunk)
                    if total and done * 100 // total >= next_report:
                        ConfigManager.console_print(f"Downloading '{label}': {next_report}%")
                        next_report += 10
        part.replace(target)  # a half-downloaded file is never used as a model
    except Exception:
        part.unlink(missing_ok=True)
        raise
    ConfigManager.console_print(f"Model downloaded to {target}")
    return target


__all__ = ["download_file", "models_dir"]
