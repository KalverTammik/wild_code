
# Standard PyQt5 imports
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt
# Project-specific imports below violate utils/ dependency direction
from ..constants.module_icons import IconNames
from ..widgets.theme_manager import ThemeManager  # TODO: Move to ui/ or refactor out of utils/
from ..constants.file_paths import QssPaths
from ..constants.button_props import ButtonVariant, ButtonSize
from ..Logs.python_fail_logger import PythonFailLogger
from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys



class ModernMessageDialog:
    """Custom styled message dialog that integrates with the theme system."""

    @staticmethod
    def Info_messages_modern(title: str, message: str):
        """Show an information message dialog with modern styling."""
        dialog = ModernMessageDialog._create_dialog(title, message, IconNames.INFO)
        dialog.exec_()

    @staticmethod
    def Warning_messages_modern(title: str, message: str, *, with_cancel: bool = False):
        """Show a warning message dialog with modern styling."""
        dialog = ModernMessageDialog._create_dialog(
            title, message, IconNames.WARNING, with_cancel=with_cancel
        )
        dialog.exec_()

    @staticmethod
    def Error_messages_modern(title: str, message: str):
        """Show an error message dialog with modern styling."""
        dialog = ModernMessageDialog._create_dialog(title, message, IconNames.CRITICAL)
        dialog.exec_()

    @staticmethod
    def Message_messages_modern(title: str, message: str):
        """Show a general message dialog with modern styling."""
        dialog = ModernMessageDialog._create_dialog(title, message, IconNames.QUESTION)
        dialog.exec_()

    # Convenience wrappers for consistency across codebase
    @staticmethod
    def show_info(title: str, message: str) -> None:
        ModernMessageDialog.Info_messages_modern(title, message)

    @staticmethod
    def show_warning(title: str, message: str, *, with_cancel: bool = False) -> bool:
        dialog = ModernMessageDialog._create_dialog(
            title, message, IconNames.WARNING, with_cancel=with_cancel
        )
        return bool(dialog.exec_())

    @staticmethod
    def show_error(title: str, message: str) -> None:
        ModernMessageDialog.Error_messages_modern(title, message)

    @staticmethod
    def ask_yes_no(
        title: str,
        message: str,
        *,
        yes_label: str = "Yes",
        no_label: str = "No",
        default: str | None = None,
    ) -> bool:
        choice = ModernMessageDialog.ask_choice_modern(
            title,
            message,
            buttons=[yes_label, no_label],
            default=default or yes_label,
            cancel=no_label,
            icon_name=IconNames.QUESTION,
        )
        return choice == yes_label

    @staticmethod
    def ask_choice_modern(
        title: str,
        message: str,
        *,
        buttons: list[str],
        default: str | None = None,
        cancel: str | None = None,
        icon_name: str = IconNames.QUESTION,
        button_variants: list[ButtonVariant | str | None] | None = None,
    ) -> str | None:
        """Show a modal dialog with custom buttons and return the clicked label.

        Args:
            buttons: Visible labels for buttons.
            button_variants: Optional per-button variants (fallbacks: primary, cancel→ghost).
        """

        dialog, result_box = ModernMessageDialog._create_choice_dialog(
            title,
            message,
            icon_name,
            buttons=buttons,
            default=default,
            cancel=cancel,
            button_variants=button_variants,
        )
        dialog.exec_()
        return result_box.get("choice")

    @staticmethod
    def get_text_modern(
        title: str,
        label: str,
        *,
        text: str = "",
        placeholder: str = "",
        icon_name: str = IconNames.QUESTION,
    ) -> tuple[str, bool]:
        """Prompt for a single line of text. Returns (value, ok)."""

        dialog, input_box, result_box = ModernMessageDialog._create_text_input_dialog(
            title,
            label,
            icon_name,
            text=text,
            placeholder=placeholder,
        )
        dialog.exec_()
        ok = bool(result_box.get("ok"))
        if not ok:
            return "", False
        return (input_box.text() or ""), True

    @staticmethod
    def _create_dialog(
        title: str,
        message: str,
        icon_name: str,
        *,
        with_cancel: bool = False,
    ) -> QDialog:
        """Create a custom styled dialog."""
        dialog = QDialog()
        dialog.setWindowTitle(title)
        dialog.setModal(True)
        dialog.setMinimumWidth(380)
        dialog.setObjectName("ModernMessageDialog")  # For QSS targeting

        # Determine message type for styling
        message_type = "message"
        if icon_name == IconNames.INFO:
            message_type = "info"
        elif icon_name == IconNames.WARNING:
            message_type = "warning"
        elif icon_name == IconNames.CRITICAL:
            message_type = "error"
        elif icon_name == IconNames.QUESTION:
            message_type = "message"

        # Set property for QSS styling variants
        dialog.setProperty("messageType", message_type)


        ThemeManager.apply_module_style(dialog, [QssPaths.MESSAGE_BOX, QssPaths.BUTTONS])

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
        icon = ThemeManager.get_qicon(icon_name)
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
            cancel_button = QPushButton(
                LanguageManager().translate(TranslationKeys.CANCEL_BUTTON) or "Cancel"
            )
            cancel_button.setProperty("variant", ButtonVariant.GHOST)
            cancel_button.setProperty("btnSize", ButtonSize.SMALL)
            cancel_button.clicked.connect(dialog.reject)
            button_layout.addWidget(cancel_button)

        # OK button
        ok_button = QPushButton(LanguageManager().translate(TranslationKeys.OK) or "OK")
        ok_button.setProperty("variant", ButtonVariant.PRIMARY)
        ok_button.clicked.connect(dialog.accept)
        ok_button.setDefault(True)
        ok_button.setFocus()
        button_layout.addWidget(ok_button)

        layout.addLayout(button_layout)

        dialog.setSizeGripEnabled(True)
        dialog.adjustSize()
        return dialog

    @staticmethod
    def _create_choice_dialog(
        title: str,
        message: str,
        icon_name: str,
        *,
        buttons: list[str],
        default: str | None = None,
        cancel: str | None = None,
        button_variants: list[ButtonVariant | str | None] | None = None,
    ) -> tuple[QDialog, dict]:
        """Create a custom dialog with multiple action buttons."""

        dialog = ModernMessageDialog._create_dialog(title, message, icon_name, with_cancel=False)
        result_box: dict = {"choice": None}

        layout = dialog.layout()
        if layout is None:
            return dialog, result_box

        # Replace the last button row created by _create_dialog.
        # _create_dialog appends the button layout as the last item.
        try:
            last_item = layout.takeAt(layout.count() - 1)
            if last_item is not None:
                old = last_item.layout()
                if old is not None:
                    while old.count():
                        it = old.takeAt(0)
                        w = it.widget() if it else None
                        if w is not None:
                            w.setParent(None)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="ui",
                event="message_dialog_replace_buttons_failed",
            )

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        def _set_choice_and_close(choice: str, accepted: bool) -> None:
            result_box["choice"] = choice
            dialog.accept() if accepted else dialog.reject()

        btn_texts = [str(b) for b in (buttons or []) if str(b).strip()]
        if not btn_texts:
            btn_texts = ["OK"]

        default_norm = (default or "").strip()
        cancel_norm = (cancel or "").strip()

        for idx, text in enumerate(btn_texts):
            b = QPushButton(text)
            is_cancel = bool(cancel_norm and text == cancel_norm)
            # Allow callers to override button variant while keeping sensible defaults.
            variant = None
            if button_variants and idx < len(button_variants):
                variant = button_variants[idx]

            if variant:
                b.setProperty("variant", str(variant))
            else:
                if is_cancel:
                    b.setProperty("variant", ButtonVariant.GHOST)
                    b.setProperty("btnSize", ButtonSize.SMALL)
                else:
                    b.setProperty("variant", ButtonVariant.PRIMARY)

            # Re-polish so variant takes effect even when stylesheet already applied.
            try:
                style = b.style()
                style.unpolish(b)
                style.polish(b)
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="ui",
                    event="message_dialog_repolish_failed",
                )

            b.clicked.connect(lambda _=False, t=text, c=is_cancel: _set_choice_and_close(t, not c))
            if default_norm and text == default_norm:
                b.setDefault(True)
                b.setFocus()
            button_layout.addWidget(b)

        # Ensure something is default-focused.
        if not default_norm:
            try:
                w0 = button_layout.itemAt(1).widget()
                if w0 is not None:
                    w0.setDefault(True)
                    w0.setFocus()
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="ui",
                    event="message_dialog_default_focus_failed",
                )

        layout.addLayout(button_layout)
        # Ensure new buttons pick up theme rules even if styles were applied earlier.
        try:
            ThemeManager.apply_module_style(dialog, [QssPaths.BUTTONS])
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="ui",
                event="message_dialog_apply_theme_failed",
            )

        # Widen if needed so button text is not cramped.
        try:
            min_w = max(dialog.minimumWidth(), layout.sizeHint().width() + 20)
            dialog.setMinimumWidth(min_w)
            dialog.resize(dialog.sizeHint())
        except Exception:
            dialog.adjustSize()
        else:
            dialog.adjustSize()
        return dialog, result_box

    @staticmethod
    def _create_text_input_dialog(
        title: str,
        label: str,
        icon_name: str,
        *,
        text: str = "",
        placeholder: str = "",
    ) -> tuple[QDialog, QLineEdit, dict]:
        """Create a themed dialog with a single QLineEdit input."""

        dialog = QDialog()
        dialog.setWindowTitle(title)
        dialog.setModal(True)
        dialog.setObjectName("ModernMessageDialog")
        dialog.setProperty("messageType", "message")
        ThemeManager.apply_module_style(dialog, [QssPaths.MESSAGE_BOX, QssPaths.BUTTONS])

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Header row (icon + label)
        header = QHBoxLayout()
        header.setSpacing(12)

        icon_label = QLabel()
        icon_label.setObjectName("iconLabel")
        icon = ThemeManager.get_qicon(icon_name)
        icon_label.setPixmap(icon.pixmap(32, 32))
        icon_label.setFixedSize(36, 36)
        icon_label.setAlignment(Qt.AlignTop)
        header.addWidget(icon_label)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(6)

        title_label = QLabel(title)
        title_label.setObjectName("titleLabel")
        title_font = title_label.font()
        title_font.setBold(True)
        title_font.setPointSize(title_font.pointSize() + 1)
        title_label.setFont(title_font)
        text_layout.addWidget(title_label)

        label_widget = QLabel(label)
        label_widget.setWordWrap(True)
        text_layout.addWidget(label_widget)

        header.addLayout(text_layout)
        layout.addLayout(header)

        input_box = QLineEdit(dialog)
        input_box.setText(text or "")
        if placeholder:
            input_box.setPlaceholderText(placeholder)
        layout.addWidget(input_box)

        layout.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

        result_box: dict = {"ok": False}

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)

        cancel_btn = QPushButton(LanguageManager().translate(TranslationKeys.CANCEL_BUTTON) or "Cancel")
        cancel_btn.setProperty("variant", ButtonVariant.GHOST)
        cancel_btn.setProperty("btnSize", ButtonSize.SMALL)
        ok_btn = QPushButton(LanguageManager().translate(TranslationKeys.OK) or "OK")
        ok_btn.setProperty("variant", ButtonVariant.PRIMARY)
        ok_btn.setProperty("btnSize", ButtonSize.SMALL)
        ok_btn.setDefault(True)

        def _ok():
            result_box["ok"] = True
            dialog.accept()

        def _cancel():
            result_box["ok"] = False
            dialog.reject()

        ok_btn.clicked.connect(_ok)
        cancel_btn.clicked.connect(_cancel)
        input_box.returnPressed.connect(_ok)

        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)

        input_box.setFocus()
        input_box.selectAll()

        return dialog, input_box, result_box