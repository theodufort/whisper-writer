"""Base window with shared Qt styling and asset resolution."""

from __future__ import annotations

import os

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

from ui.icons import _ASSETS_DIR, STYLESHEET

# Backward-compatible alias
_asset = lambda name: f"{_ASSETS_DIR}/{name}".replace("\\", "/")


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
