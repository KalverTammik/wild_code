from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox,  QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt
from ..constants.module_icons import IconNames
from ..widgets.theme_manager import ThemeManager
from ..constants.file_paths import QssPaths



class ModernMessageDialog:
    """Custom styled message dialog that integrates with the theme system."""

    @staticmethod
    def Info_messages_modern(title: str, message: str):
        """Show an information message dialog with modern styling."""
        dialog = ModernMessageDialog._create_dialog(title, message, ThemeManager.get_qicon(IconNames.INFO))
        dialog.exec_()

    @staticmethod
    def Warning_messages_modern(title: str, message: str, *, with_cancel: bool = False):
        """Show a warning message dialog with modern styling."""
        dialog = ModernMessageDialog._create_dialog(
            title, message, ThemeManager.get_qicon(IconNames.WARNING), with_cancel=with_cancel
        )
        dialog.exec_()

    @staticmethod
    def Error_messages_modern(title: str, message: str):
        """Show an error message dialog with modern styling."""
        dialog = ModernMessageDialog._create_dialog(title, message, ThemeManager.get_qicon(IconNames.CRITICAL))
        dialog.exec_()

    @staticmethod
    def Message_messages_modern(title: str, message: str):
        """Show a general message dialog with modern styling."""
        dialog = ModernMessageDialog._create_dialog(title, message, ThemeManager.get_qicon(IconNames.QUESTION))
        dialog.exec_()

    @staticmethod
    def _create_dialog(
        title: str,
        message: str,
        icon_type: QMessageBox.Icon,
        *,
        with_cancel: bool = False,
    ) -> QDialog:
        """Create a custom styled dialog."""
        dialog = QDialog()
        dialog.setWindowTitle(title)
        dialog.setModal(True)
        dialog.setFixedWidth(400)
        dialog.setObjectName("ModernMessageDialog")  # For QSS targeting

        # Determine message type for styling
        message_type = "info"
        if icon_type == ThemeManager.get_qicon(IconNames.WARNING):
            message_type = "warning"
        elif icon_type == ThemeManager.get_qicon(IconNames.CRITICAL):
            message_type = "error"
        elif icon_type == ThemeManager.get_qicon(IconNames.INFO):
            message_type = "message"

        # Set property for QSS styling variants
        dialog.setProperty("messageType", message_type)


        ThemeManager.apply_module_style(dialog, [QssPaths.MESSAGE_BOX])

        # Main layout
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Content layout (icon + text)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)

        # Icon
        icon_label = QLabel()
        icon_label.setObjectName("iconLabel")  # For QSS targeting
        
        # Load and scale the icon
        icon = ThemeManager.get_qicon(icon_type)
        pixmap = icon.pixmap(32, 32)  # Scale to 32x32
        icon_label.setPixmap(pixmap)


        icon_label.setFixedSize(32, 32)
        icon_label.setAlignment(Qt.AlignTop)
        content_layout.addWidget(icon_label)

        # Text content
        text_layout = QVBoxLayout()
        text_layout.setSpacing(5)

        # Title
        title_label = QLabel(title)
        title_label.setObjectName("titleLabel")  # For QSS targeting
        title_font = title_label.font()
        title_font.setBold(True)
        title_font.setPointSize(title_font.pointSize() + 1)
        title_label.setFont(title_font)
        text_layout.addWidget(title_label)

        # Message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        text_layout.addWidget(message_label)

        content_layout.addLayout(text_layout)
        layout.addLayout(content_layout)

        # Spacer
        layout.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # Optional Cancel button
        cancel_button = None
        if with_cancel:
            cancel_button = QPushButton("Cancel")
            cancel_button.clicked.connect(dialog.reject)
            button_layout.addWidget(cancel_button)

        # OK button
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(dialog.accept)
        ok_button.setDefault(True)
        ok_button.setFocus()
        button_layout.addWidget(ok_button)

        layout.addLayout(button_layout)

        return dialog, ok_button, cancel_button