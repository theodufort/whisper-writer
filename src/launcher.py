"""CLI entry point for WhisperWriter.

Parses command-line flags and launches the application.

Usage:
    WhisperWriter.exe              Tray icon + main window
    WhisperWriter.exe --tray       Tray icon only (no main window)
    WhisperWriter.exe --startup    Silent tray launch (auto-start mode)
    WhisperWriter.exe --help       Show this help message
"""

from __future__ import annotations

import argparse
import logging

logger = logging.getLogger("whisperwriter.launcher")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Argument list (defaults to sys.argv[1:]).

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        prog="WhisperWriter",
        description="Auto-transcribe speech to text via system tray.",
    )
    parser.add_argument(
        "--tray",
        action="store_true",
        help="Run in tray-only mode (no main window visible).",
    )
    parser.add_argument(
        "--startup",
        action="store_true",
        help="Run silently in tray (for Windows auto-start).",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Force show main window on startup.",
    )
    return parser.parse_args(argv)


def main() -> None:
    """Entry point for the frozen EXE."""
    args = parse_args()
    logger.info("WhisperWriter starting (tray=%s, startup=%s, show=%s)", args.tray, args.startup, args.show)

    # Import here to allow clean exit before PyQt initialization
    from main import WhisperWriterApp

    app = WhisperWriterApp()
    app.set_tray_only(getattr(args, "tray", False) or getattr(args, "startup", False))
    app.set_force_show(getattr(args, "show", False))
    app.run()


if __name__ == "__main__":
    main()
