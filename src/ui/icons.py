"""Asset path resolution and shared QSS stylesheets for the UI."""

from __future__ import annotations

import os
import sys

if hasattr(sys, "_MEIPASS"):
    _ASSETS_DIR = os.path.join(sys._MEIPASS, "assets")
else:
    _ASSETS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "assets"))


def asset(name: str) -> str:
    """Return a filesystem path to a bundled/development asset."""
    return os.path.join(_ASSETS_DIR, name).replace("\\", "/")


STYLESHEET: str = f"""
QWidget {{
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
    color: #344054;
}}
QTabWidget::pane {{
    border: 1px solid rgba(74, 124, 249, 0.22);
    border-radius: 10px;
    background: rgba(255, 255, 255, 0.45);
    top: -1px;
}}
QTabBar::tab {{
    background: transparent;
    color: #667085;
    padding: 9px 20px;
    border: none;
    border-bottom: 2px solid transparent;
    font-size: 12px;
    min-width: 110px;
}}
QTabBar::tab:selected {{
    color: #4A7CF9;
    border-bottom: 2px solid #4A7CF9;
    background: rgba(74, 124, 249, 0.07);
    font-weight: 600;
}}
QTabBar::tab:hover:!selected {{
    color: #4A7CF9;
    background: rgba(74, 124, 249, 0.03);
}}
QLineEdit {{
    background: rgba(255, 255, 255, 0.92);
    border: 1.5px solid #D0D5DD;
    border-radius: 7px;
    padding: 6px 10px;
    selection-background-color: #4A7CF9;
    color: #101828;
    min-width: 180px;
}}
QLineEdit:focus {{
    border: 1.5px solid #4A7CF9;
    background: white;
}}
QComboBox {{
    background: rgba(255, 255, 255, 0.92);
    border: 1.5px solid #D0D5DD;
    border-radius: 7px;
    padding: 6px 10px;
    min-width: 90px;
    color: #101828;
}}
QComboBox:focus {{
    border: 1.5px solid #4A7CF9;
}}
QComboBox::drop-down {{
    border: none;
    width: 26px;
}}
QComboBox::down-arrow {{
    image: url({asset('caret-down.svg')});
    width: 14px;
    height: 14px;
}}
QComboBox QAbstractItemView {{
    background: white;
    border: 1px solid #D0D5DD;
    border-radius: 7px;
    selection-background-color: #4A7CF9;
    selection-color: white;
    outline: 0;
    padding: 2px;
    color: #101828;
}}
QComboBox QAbstractItemView::item {{
    padding: 4px 8px;
    color: #101828;
}}
QComboBox QAbstractItemView::item:selected {{
    color: white;
}}
QCheckBox {{
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1.5px solid #D0D5DD;
    background: rgba(255, 255, 255, 0.92);
}}
QCheckBox::indicator:checked {{
    background: #4A7CF9;
    border: 1.5px solid #4A7CF9;
    image: url({asset('check.svg')});
}}
QCheckBox::indicator:hover {{
    border: 1.5px solid #4A7CF9;
}}
QPushButton {{
    background: #4A7CF9;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 9px 22px;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton:hover {{
    background: #5A8BFA;
}}
QPushButton:pressed {{
    background: #3A6CE8;
}}
QPushButton#reset_btn {{
    background: rgba(255, 255, 255, 0.75);
    color: #4A7CF9;
    border: 1.5px solid rgba(74, 124, 249, 0.45);
}}
QPushButton#reset_btn:hover {{
    background: rgba(74, 124, 249, 0.08);
    border: 1.5px solid #4A7CF9;
}}
QPushButton#reset_btn:pressed {{
    background: rgba(74, 124, 249, 0.15);
}}
QToolButton {{
    background: transparent;
    border: none;
    border-radius: 12px;
    padding: 2px;
    color: #98A2B3;
}}
QToolButton:hover {{
    background: rgba(74, 124, 249, 0.1);
    color: #4A7CF9;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: rgba(74, 124, 249, 0.35);
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: rgba(74, 124, 249, 0.6);
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
"""

__all__ = ["asset", "STYLESHEET", "_ASSETS_DIR"]
