#!/usr/bin/env python3
"""
ProgressDialogModern - Modern Progress Dialog for QGIS

A modern, responsive progress dialog with cancellation support
for long-running operations in QGIS plugins.

Author: Wild Code Plugin Team
Date: September 5, 2025
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QPushButton, QWidget, QFrame
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor, QKeySequence

try:
    from ..languages.language_manager import LanguageManager
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from languages.language_manager import LanguageManager


class ProgressDialogModern(QDialog):
    """
    Modern progress dialog with cancellation support and responsive UI.

    Features:
    - Modern styling with QSS
    - Real-time progress updates
    - Cancellation support
    - Multiple text fields for status
    - Responsive UI that doesn't block
    """

    # Signals
    canceled = pyqtSignal()

    def __init__(self, title="Progress", maximum=100, parent=None):
        """
        Initialize the progress dialog.

        Args:
            title: Dialog title
            maximum: Maximum progress value
            parent: Parent widget
        """
        super().__init__(parent)
        self.lang_manager = LanguageManager()
        self.maximum = maximum
        self.current_value = 0
        self.is_cancelled = False

        # Use window-modal instead of app-modal
        self.setWindowModality(Qt.WindowModal)

        self.setWindowTitle(title)
        # Allow resizing - remove fixed size
        self.setMinimumSize(400, 250)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # Delete on close for memory management
        self.setAttribute(Qt.WA_DeleteOnClose)

        self._setup_ui()
        self._apply_theme()

        # ESC key to cancel
        self.cancel_button.setShortcut(QKeySequence.Cancel)

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title section
        title_frame = QFrame()
        title_frame.setObjectName("ProgressTitleFrame")
        title_layout = QVBoxLayout(title_frame)
        title_layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel(self.windowTitle())
        self.title_label.setObjectName("ProgressTitle")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(self.title_label)

        layout.addWidget(title_frame)

        # Progress section
        progress_frame = QFrame()
        progress_frame.setObjectName("ProgressFrame")
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setContentsMargins(10, 10, 10, 10)

        # Progress bar with indeterminate support
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("ProgressBar")
        if self.maximum > 0:
            self.progress_bar.setRange(0, self.maximum)
            self.progress_bar.setValue(0)
        else:
            # Indeterminate mode for unknown workload
            self.progress_bar.setRange(0, 0)
        self.progress_bar.setTextVisible(False)  # Remove duplicate text
        progress_layout.addWidget(self.progress_bar)

        # Single percentage label (remove duplication)
        self.percentage_label = QLabel("0%")
        self.percentage_label.setObjectName("ProgressPercentage")
        self.percentage_label.setAlignment(Qt.AlignCenter)
        percent_font = QFont()
        percent_font.setPointSize(12)
        self.percentage_label.setFont(percent_font)
        progress_layout.addWidget(self.percentage_label)

        layout.addWidget(progress_frame)

        # Status section
        status_frame = QFrame()
        status_frame.setObjectName("StatusFrame")
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(10, 10, 10, 10)

        # Primary status
        self.status_label1 = QLabel(self.lang_manager.translate("Initializing...") or "Initializing...")
        self.status_label1.setObjectName("StatusLabel1")
        status_layout.addWidget(self.status_label1)

        # Secondary status
        self.status_label2 = QLabel("")
        self.status_label2.setObjectName("StatusLabel2")
        status_layout.addWidget(self.status_label2)

        layout.addWidget(status_frame)

        # Button section
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_button = QPushButton(self.lang_manager.translate("Cancel") or "Cancel")
        self.cancel_button.setObjectName("CancelButton")
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        # Connect progress bar value changed
        self.progress_bar.valueChanged.connect(self._update_percentage)

    def _apply_styling(self):
        """Apply modern QSS styling."""
        self.setStyleSheet("""
            ProgressDialogModern {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
            }

            #ProgressTitleFrame {
                background-color: #e3f2fd;
                border: 1px solid #bbdefb;
                border-radius: 6px;
                padding: 5px;
            }

            #ProgressTitle {
                color: #1976d2;
                border: none;
            }

            #ProgressFrame {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
            }

            #ProgressBar {
                border: 1px solid #ccc;
                border-radius: 3px;
                text-align: center;
                background-color: #f0f0f0;
            }

            #ProgressBar::chunk {
                background-color: #4caf50;
                border-radius: 2px;
            }

            #ProgressPercentage {
                color: #2e7d32;
                font-weight: bold;
                margin-top: 5px;
            }

            #StatusFrame {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
            }

            #StatusLabel1 {
                color: #424242;
                font-weight: bold;
            }

            #StatusLabel2 {
                color: #666666;
                font-size: 11px;
            }

            #CancelButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 80px;
            }

            #CancelButton:hover {
                background-color: #d32f2f;
            }

            #CancelButton:pressed {
                background-color: #b71c1c;
            }
        """)

    def update(self, value=None, text1=None, text2=None):
        """
        Update progress dialog.

        Args:
            value: Progress value (0-maximum)
            text1: Primary status text
            text2: Secondary status text
        """
        if value is not None:
            self.current_value = value
            if self.maximum > 0:
                self.progress_bar.setValue(value)
            # Handle indeterminate to determinate transition
            elif value > 0 and self.maximum == 0:
                self.setMaximum(value)  # Assume value is the new maximum
                self.progress_bar.setRange(0, value)
                self.progress_bar.setValue(value)

        if text1 is not None:
            self.status_label1.setText(text1)

        if text2 is not None:
            self.status_label2.setText(text2)

        # Removed QApplication.processEvents() to avoid re-entrancy issues

    def _update_percentage(self, value):
        """Update percentage label when progress bar changes."""
        if self.maximum > 0 and value >= 0:
            percentage = min(int((value / self.maximum) * 100), 100)
            self.percentage_label.setText(f"{percentage}%")
        elif self.maximum == 0:
            # Indeterminate mode
            self.percentage_label.setText(self.lang_manager.translate("Working...") or "Working...")

    def _on_cancel_clicked(self):
        """Handle cancel button click."""
        self.is_cancelled = True
        self.cancel_button.setText(self.lang_manager.translate("Cancelling...") or "Cancelling...")
        self.cancel_button.setEnabled(False)
        self.canceled.emit()

    def wasCanceled(self):
        """
        Check if operation was cancelled.

        Returns:
            bool: True if cancelled
        """
        return self.is_cancelled

    def setTitle(self, title):
        """Set dialog title."""
        self.setWindowTitle(title)
        self.title_label.setText(title)

    def setMaximum(self, maximum):
        """Set maximum progress value."""
        self.maximum = maximum
        if maximum > 0:
            self.progress_bar.setRange(0, maximum)
        else:
            # Indeterminate mode
            self.progress_bar.setRange(0, 0)
        self._update_percentage(self.current_value)

    def reset(self):
        """Reset progress dialog."""
        self.current_value = 0
        self.is_cancelled = False
        self.progress_bar.setValue(0)
        self.status_label1.setText(self.lang_manager.translate("Initializing...") or "Initializing...")
        self.status_label2.setText("")
        self.percentage_label.setText("0%")
        self.cancel_button.setText(self.lang_manager.translate("Cancel") or "Cancel")
        self.cancel_button.setEnabled(True)

    def setPhase(self, title, subtitle=""):
        """Convenience method to set phase with title and subtitle."""
        self.setTitle(title)
        self.status_label1.setText(subtitle)

    def _apply_theme(self):
        """Apply theme using ThemeManager."""
        try:
            from .theme_manager import ThemeManager
            from ..constants.file_paths import StylePaths, QssPaths

            # Get current theme
            theme = ThemeManager.load_theme_setting()
            theme_dir = StylePaths.DARK if theme == "dark" else StylePaths.LIGHT

            # Apply theme with our custom QSS file
            qss_files = [QssPaths.MAIN, "ProgressDialogModern.qss"]
            ThemeManager.apply_theme(self, theme_dir, qss_files)
        except Exception as e:
            # Fallback to basic styling if theme loading fails
            self._apply_fallback_styling()

    def _apply_fallback_styling(self):
        """Fallback styling if theme loading fails."""
        self.setStyleSheet("""
            ProgressDialogModern {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
            }
            QLabel {
                color: #212529;
            }
            QProgressBar {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #007bff;
                border-radius: 3px;
            }
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #545b62;
            }
            QTextEdit {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #dee2e6;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #007bff;
                border-color: #007bff;
            }
        """)

    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key_Escape:
            if self.cancel_button.isEnabled():
                self._on_cancel_clicked()
        super().keyPressEvent(event)

    def showEvent(self, event):
        """Handle dialog show event."""
        super().showEvent(event)
        # Ensure dialog stays on top
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        """Handle dialog close event."""
        if self.is_cancelled:
            self.reject()  # Cancelled
        else:
            self.accept()  # Completed
        super().closeEvent(event)
