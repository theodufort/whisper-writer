import argparse
import sys

from audioplayer import AudioPlayer
from PyQt5.QtCore import QObject, QProcess
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QApplication, QMenu, QMessageBox, QSystemTrayIcon

from input_simulation import InputSimulator
from keylistener import KeyListener
from model import create_local_model
from result_thread import ResultThread
from tray_launcher import TrayService
from ui.main_window import MainWindow
from ui.settings_window import SettingsWindow
from ui.status_window import StatusWindow
from core.config import ConfigManager
from utils import resource_path


class WhisperWriterApp(QObject):
    def __init__(self, tray_only: bool = False, force_show: bool = False):
        """
        Initialize the application, opening settings window if no configuration file is found.

        Args:
            tray_only: If True, only create the tray icon (no main window).
            force_show: If True, force-show the main window on startup.
        """
        super().__init__()
        self.app = QApplication(sys.argv)
        self.app.setWindowIcon(QIcon(resource_path("assets/ww-logo.png")))

        # Pre-initialize component references so cleanup() is always safe
        self.key_listener = None
        self.input_simulator = None
        self.result_thread = None
        self.local_model = None
        self.main_window = None
        self.status_window = None
        self.tray_service: TrayService | None = None

        self._tray_only = tray_only
        self._force_show = force_show

        ConfigManager.initialize()

        self.settings_window = SettingsWindow()
        self.settings_window.settings_closed.connect(self.on_settings_closed)
        self.settings_window.settings_saved.connect(self.restart_app)

        # Always create tray icon first (before main window)
        self._create_tray()

        if ConfigManager.config_file_exists():
            self.initialize_components()
        else:
            print("No valid configuration file found. Opening settings window...")
            self.settings_window.show()

    def initialize_components(self):
        """
        Initialize the components of the application.
        """
        self.input_simulator = InputSimulator()

        self.key_listener = KeyListener()
        self.key_listener.add_callback("on_activate", self.on_activation)
        self.key_listener.add_callback("on_deactivate", self.on_deactivation)

        model_options = ConfigManager.get_config_section("model_options")
        self.local_model = create_local_model() if not model_options.get("use_api") else None

        self.result_thread = None

        self.main_window = MainWindow()
        self.main_window.openSettings.connect(self.settings_window.show)
        self.main_window.startListening.connect(self.key_listener.start)
        self.main_window.closeApp.connect(self.exit_app)

        if not ConfigManager.get_config_value("misc", "hide_status_window"):
            self.status_window = StatusWindow()

        # Show main window unless tray-only mode
        if self._tray_only and not self._force_show:
            self.main_window.hide()
        else:
            self.main_window.show()

    def _create_tray(self) -> None:
        """Create the system tray icon using TrayService."""
        self.tray_service = TrayService(
            app_ref=self.app,
            on_show_main=self._show_main,
            on_open_settings=self.settings_window.show,
            on_exit=self.exit_app,
        )
        self.tray_service.create()

    def _show_main(self) -> None:
        """Show the main window and bring it to focus."""
        if self.main_window:
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()

    def set_tray_only(self, value: bool) -> None:
        """Set tray-only mode (tray icon only, no main window)."""
        self._tray_only = value

    def set_force_show(self, value: bool) -> None:
        """Force show main window on startup."""
        self._force_show = value

    def cleanup(self):
        if self.result_thread and self.result_thread.isRunning():
            self.result_thread.stop()
        if self.key_listener:
            self.key_listener.stop()
        if self.input_simulator:
            self.input_simulator.cleanup()

    def exit_app(self):
        """
        Exit the application.
        """
        self.cleanup()
        QApplication.quit()

    def restart_app(self):
        """Restart the application to apply the new settings."""
        self.cleanup()
        QApplication.quit()
        QProcess.startDetached(sys.executable, sys.argv)

    def on_settings_closed(self):
        """
        If settings is closed without saving on first run,
        initialize the components with default values.
        """
        if not ConfigManager.config_file_exists():
            QMessageBox.information(
                self.settings_window,
                "Using Default Values",
                "Settings closed without saving. Default values are being used.",
            )
            self.initialize_components()

    def on_activation(self):
        """
        Called when the activation key combination is pressed.
        """
        if self.result_thread and self.result_thread.isRunning():
            recording_mode = ConfigManager.get_config_value("recording_options", "recording_mode")
            if recording_mode == "press_to_toggle":
                self.result_thread.stop_recording()
            elif recording_mode == "continuous":
                self.stop_result_thread()
            return

        self.start_result_thread()

    def on_deactivation(self):
        """
        Called when the activation key combination is released.
        """
        recording_mode = ConfigManager.get_config_value("recording_options", "recording_mode")
        if recording_mode == "hold_to_record":
            if self.result_thread and self.result_thread.isRunning():
                self.result_thread.stop_recording()

    def start_result_thread(self):
        """
        Start the result thread to record audio and transcribe it.
        """
        if self.result_thread and self.result_thread.isRunning():
            return

        self.result_thread = ResultThread(self.local_model)
        if not ConfigManager.get_config_value("misc", "hide_status_window"):
            self.result_thread.statusSignal.connect(self.status_window.updateStatus)
            self.status_window.closeSignal.connect(self.stop_result_thread)
        self.result_thread.resultSignal.connect(self.on_transcription_complete)
        self.result_thread.start()

    def stop_result_thread(self):
        """
        Stop the result thread.
        """
        if self.result_thread and self.result_thread.isRunning():
            self.result_thread.stop()

    def on_transcription_complete(self, result):
        """
        When the transcription is complete, type the result
        and start listening for the activation key again.
        """
        self.input_simulator.typewrite(result)

        if ConfigManager.get_config_value("misc", "noise_on_completion"):
            AudioPlayer(resource_path("assets/beep.wav")).play(block=True)

        if ConfigManager.get_config_value("recording_options", "recording_mode") == "continuous":
            self.start_result_thread()
        else:
            self.key_listener.start()

    def run(self):
        """
        Start the application.
        """
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    app = WhisperWriterApp()
    app.run()
