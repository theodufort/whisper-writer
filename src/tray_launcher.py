"""System tray service for WhisperWriter.

Provides a persistent tray icon with menu actions (Show, Settings, Exit)
and Windows auto-start management via the Startup folder.
"""

from __future__ import annotations

import logging
import sys
from functools import partial
from pathlib import Path
from typing import Callable

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMenu, QSystemTrayIcon

from utils import resource_path

logger = logging.getLogger("whisperwriter.tray")

# ─── Auto-start helpers ────────────────────────────────────────────────


def _get_startup_folder() -> Path:
    """Return the Windows Startup folder path."""
    if hasattr(sys, "_MEIPASS"):
        # Frozen: use user's appdata
        return Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    # Dev mode: use user's appdata (config lives in user data dir)
    return Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def _get_exe_path() -> str:
    """Return the path to the current executable."""
    if hasattr(sys, "_MEIPASS"):
        return sys.executable
    return str(Path(__file__).parent / "run.py")


def is_auto_start_enabled() -> bool:
    """Check if WhisperWriter is registered in Windows Startup."""
    startup = _get_startup_folder()
    return (startup / "WhisperWriter.lnk").exists()


def enable_auto_start() -> bool:
    """Register WhisperWriter in Windows Startup folder.

    Returns True on success, False if it failed.
    """
    try:
        startup = _get_startup_folder()
        startup.mkdir(parents=True, exist_ok=True)

        import win32com.client

        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(str(startup / "WhisperWriter.lnk"))
        shortcut.Targetpath = _get_exe_path()
        shortcut.WorkingDirectory = str(Path(_get_exe_path()).parent)
        shortcut.IconLocation = resource_path("assets/ww-logo.ico")
        shortcut.Description = "WhisperWriter - Auto-transcribe speech to text"
        shortcut.save()
        logger.info("Auto-start enabled (Startup folder)")
        return True
    except Exception:
        logger.exception("Failed to enable auto-start")
        return False


def disable_auto_start() -> bool:
    """Remove WhisperWriter from Windows Startup folder.

    Returns True on success, False if it failed.
    """
    try:
        lnk = _get_startup_folder() / "WhisperWriter.lnk"
        if lnk.exists():
            lnk.unlink()
            logger.info("Auto-start disabled")
            return True
        return False
    except Exception:
        logger.exception("Failed to disable auto-start")
        return False


# ─── Tray icon ─────────────────────────────────────────────────────────


class TrayService:
    """Manages the system tray icon and its context menu."""

    def __init__(
        self,
        app_ref: object,
        on_show_main: Callable[[], None],
        on_open_settings: Callable[[], None],
        on_exit: Callable[[], None],
    ) -> None:
        """
        Args:
            app_ref: Reference to the QApplication instance.
            on_show_main: Callback to show the main window.
            on_open_settings: Callback to open the settings window.
            on_exit: Callback to exit the application.
        """
        self.app_ref = app_ref
        self.on_show_main = on_show_main
        self.on_open_settings = on_open_settings
        self.on_exit = on_exit
        self._tray: QSystemTrayIcon | None = None

    def create(self) -> QSystemTrayIcon:
        """Create the tray icon and return it."""
        icon = QIcon(resource_path("assets/ww-logo.png"))
        menu = QMenu()

        show_action = menu.addAction("Show")
        show_action.triggered.connect(self.on_show_main)

        settings_action = menu.addAction("Settings")
        settings_action.triggered.connect(self.on_open_settings)

        menu.addSeparator()

        startup_action = menu.addAction("Auto-start")
        startup_action.setCheckable(True)
        startup_action.setChecked(is_auto_start_enabled())
        startup_action.triggered.connect(self._toggle_auto_start)

        menu.addSeparator()

        exit_action = menu.addAction("Exit")
        exit_action.triggered.connect(self.on_exit)

        self._tray = QSystemTrayIcon(icon, self.app_ref)
        self._tray.setToolTip("WhisperWriter")
        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

        logger.info("System tray icon created")
        return self._tray

    def _toggle_auto_start(self, checked: bool) -> None:
        """Toggle auto-start registration."""
        if checked:
            enable_auto_start()
        else:
            disable_auto_start()
        # Sync check state after potential failure
        self._tray.menu().actions()[2].setChecked(is_auto_start_enabled())

    def _on_tray_activated(self, reason: int) -> None:
        """Show main window on tray icon double-click."""
        # QSystemTrayIcon.DoubleClick == 3
        if reason == 3:
            self.on_show_main()

    def hide(self) -> None:
        """Hide the tray icon."""
        if self._tray:
            self._tray.hide()

    def show(self) -> None:
        """Show the tray icon."""
        if self._tray:
            self._tray.show()
