#!/usr/bin/env python3


from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QPushButton, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QKeySequence
from qgis.utils import iface


from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys
from ..constants.button_props import ButtonVariant, ButtonSize
from ..ui.window_state.DialogCoordinator import get_dialog_coordinator



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
        self.status_label1 = QLabel(
            self.lang_manager.translate(TranslationKeys.INITIALIZING) or "Initializing..."
        )
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

        self.cancel_button = QPushButton(
            self.lang_manager.translate(TranslationKeys.CANCEL_BUTTON) or "Cancel"
        )
        self.cancel_button.setObjectName("CancelButton")
        self.cancel_button.setProperty("variant", ButtonVariant.GHOST)
        self.cancel_button.setProperty("btnSize", ButtonSize.SMALL)
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        # Connect progress bar value changed
        self.progress_bar.valueChanged.connect(self._update_percentage)

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
        self.status_label1.setText(self.lang_manager.translate(TranslationKeys.INITIALIZING))
        self.status_label2.clear()
        self.percentage_label.setText(self.lang_manager.translate(TranslationKeys.PROGRESS_DIALOG_MODERN_PERCENT))
        self.cancel_button.setText(self.lang_manager.translate(TranslationKeys.CANCEL_BUTTON))
        self.cancel_button.setEnabled(True)

    def setPhase(self, title, subtitle=""):
        """Convenience method to set phase with title and subtitle."""
        self.setTitle(title)
        self.status_label1.setText(subtitle)

    def _apply_theme(self):
        """Apply theme using ThemeManager."""
        try:
            from .theme_manager import ThemeManager
            from ..constants.file_paths import QssPaths

            # Apply theme using centralized QSS files
            ThemeManager.apply_module_style(self, [QssPaths.PROGRESS_DIALOG])
        except Exception as e:
            # Theme loading failed - widget will use default Qt styling
            pass

    def retheme(self):
        """Re-apply theme styling for dynamic theme switching."""
        self._apply_theme()

    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key_Escape:
            if self.cancel_button.isEnabled():
                self._on_cancel_clicked()
        super().keyPressEvent(event)

    def showEvent(self, event):
        """Handle dialog show event."""
        super().showEvent(event)
        coordinator = get_dialog_coordinator(iface)
        coordinator.bring_to_front(self)

    def closeEvent(self, event):
        """Handle dialog close event."""
        if self.is_cancelled:
            self.reject()  # Cancelled
        else:
            self.accept()  # Completed
        super().closeEvent(event)
