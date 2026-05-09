import os
import sys

from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QFont,
    QGuiApplication,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

if hasattr(sys, "_MEIPASS"):
    # Frozen: assets are bundled at the root of sys._MEIPASS
    _ASSETS_DIR = os.path.join(sys._MEIPASS, "assets")
else:
    # Development: two levels up from src/ui/ reaches the project root
    _ASSETS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "assets"))


def _asset(name):
    return os.path.join(_ASSETS_DIR, name).replace("\\", "/")


STYLESHEET = f"""
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
    image: url({_asset("caret-down.svg")});
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
    image: url({_asset("check.svg")});
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


class BaseWindow(QMainWindow):
    def __init__(self, title, width, height):
        """
        Initialize the base window.
        """
        super().__init__()
        self.initUI(title, width, height)
        self.setWindowPosition()
        self.is_dragging = False

    def initUI(self, title, width, height):
        """
        Initialize the user interface.
        """
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(width, height)
        self.setStyleSheet(STYLESHEET)

        self.main_widget = QWidget(self)
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(14, 8, 14, 14)
        self.main_layout.setSpacing(8)

        # Title bar
        title_bar = QWidget()
        title_bar.setFixedHeight(44)
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(4, 0, 4, 0)
        title_bar_layout.setSpacing(6)

        # Logo + title centered
        center_widget = QWidget()
        center_layout = QHBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(8)

        logo_path = os.path.join(_ASSETS_DIR, "ww-logo.png")
        if os.path.exists(logo_path):
            logo_label = QLabel()
            logo_pixmap = QPixmap(logo_path).scaled(
                22, 22, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            logo_label.setPixmap(logo_pixmap)
            center_layout.addWidget(logo_label)

        title_label = QLabel("WhisperWriter")
        title_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        title_label.setStyleSheet("color: #4A7CF9; background: transparent;")
        center_layout.addWidget(title_label)

        # Close button
        close_button = QPushButton("×")
        close_button.setFixedSize(28, 28)
        close_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #98A2B3;
                font-size: 18px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.12);
                color: #EF4444;
            }
            QPushButton:pressed {
                background: rgba(239, 68, 68, 0.22);
                color: #DC2626;
            }
        """)
        close_button.clicked.connect(self.handleCloseButton)

        title_bar_layout.addWidget(QWidget(), 1)
        title_bar_layout.addWidget(center_widget, 3, Qt.AlignCenter)
        title_bar_layout.addWidget(close_button, 0, Qt.AlignRight | Qt.AlignVCenter)

        # Separator line below title bar
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFixedHeight(1)
        separator.setStyleSheet("background: rgba(74, 124, 249, 0.18); border: none;")

        self.main_layout.addWidget(title_bar)
        self.main_layout.addWidget(separator)
        self.setCentralWidget(self.main_widget)

    def setWindowPosition(self):
        """
        Set the window position to the center of the screen.
        """
        center_point = QGuiApplication.primaryScreen().availableGeometry().center()
        frame_geometry = self.frameGeometry()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

    def handleCloseButton(self):
        """
        Close the window.
        """
        self.close()

    def mousePressEvent(self, event):
        """
        Allow the window to be moved by clicking and dragging anywhere on the window.
        """
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.start_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """
        Move the window when dragging.
        """
        if Qt.LeftButton and self.is_dragging:
            self.move(event.globalPos() - self.start_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """
        Stop dragging the window.
        """
        self.is_dragging = False

    def paintEvent(self, event):
        """
        Create a rounded rectangle with a modern gradient background and subtle border.
        """
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 16, 16)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Gradient background
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QColor(245, 248, 255, 245))
        gradient.setColorAt(1.0, QColor(235, 241, 255, 245))
        painter.setBrush(QBrush(gradient))

        # Subtle border
        painter.setPen(QPen(QColor(74, 124, 249, 55), 1.2))
        painter.drawPath(path)
