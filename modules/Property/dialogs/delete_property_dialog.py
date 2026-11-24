from ....languages.translation_keys import TranslationKeys
from ....languages.language_manager import LanguageManager
from ....ui.theme_manager import ThemeManager
from ....constants.file_paths import QssPaths

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from ....ui.messages_helper import ModernMessageDialog
from ..FlowControllers.property_delete import deleteProperty
from ....constants.module_names import Module
from ....Logs.python_fail_logger import PythonFailLogger


class DeletePropertyUI(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.lang_manager = LanguageManager()

        self.setWindowTitle(
            self.lang_manager.translate(TranslationKeys.REMOVE_PROPERTY)
        )
        self.setModal(True)
        self.setFixedSize(420, 160)

        ThemeManager.set_initial_theme(
            self,
            None,
            qss_files=[QssPaths.MAIN, QssPaths.SETUP_CARD, QssPaths.COMBOBOX],
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        title = QLabel(
            self.lang_manager.translate(TranslationKeys.REMOVE_PROPERTY)
        )
        title.setObjectName("FilterTitle")
        layout.addWidget(title)

        self._id_input = QLineEdit(self)
        self._id_input.setPlaceholderText(
            self.lang_manager.translate(TranslationKeys.PROPERTY_ID_PLACEHOLDER)
        )
        self._id_input.setClearButtonEnabled(True)
        self._id_input.setObjectName("PropertyIdInput")
        layout.addWidget(self._id_input)

        btns = QHBoxLayout()
        btns.addStretch(1)

        self._btn_cancel = QPushButton(
            self.lang_manager.translate(TranslationKeys.CANCEL_BUTTON),
            self,
        )
        self._btn_cancel.setObjectName("ConfirmButton")
        self._btn_cancel.clicked.connect(self.reject)
        btns.addWidget(self._btn_cancel)

        self._btn_confirm = QPushButton(
            self.lang_manager.translate(TranslationKeys.CONFIRM),
            self,
        )
        self._btn_confirm.setObjectName("ConfirmButton")
        self._btn_confirm.clicked.connect(self._on_confirm_clicked)
        btns.addWidget(self._btn_confirm)

        layout.addLayout(btns)

        self.show()
        self.exec_()

    def _on_confirm_clicked(self) -> None:
        # A Qt slot: an escaping exception would abort QGIS.
        try:
            self._confirm_and_delete()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.PROPERTY.value,
                event="property_delete_by_id_failed",
            )
            self._btn_confirm.setEnabled(True)
            self._btn_cancel.setEnabled(True)

    def _confirm_and_delete(self) -> None:
        property_id = (self._id_input.text() or "").strip()
        if not property_id:
            ModernMessageDialog.show_warning(
                self.lang_manager.translate(TranslationKeys.MISSING_PROPERTY_ID_TITLE),
                self.lang_manager.translate(TranslationKeys.MISSING_PROPERTY_ID_BODY),
            )
            return

        self._btn_confirm.setEnabled(False)
        self._btn_cancel.setEnabled(False)
        ok = False
        try:
            # The user must see which record the ID points to before anything is deleted.
            status, preview = deleteProperty.load_preview(property_id)
            if status == deleteProperty.PREVIEW_NOT_FOUND:
                ModernMessageDialog.show_warning(
                    self.lang_manager.translate(TranslationKeys.PROPERTY_DELETE_FAILED),
                    self.lang_manager.translate(TranslationKeys.PROPERTY_DELETE_BY_ID_NOT_FOUND).format(
                        id=property_id),
                )
                return
            if status != deleteProperty.PREVIEW_OK:
                ModernMessageDialog.show_warning(
                    self.lang_manager.translate(TranslationKeys.PROPERTY_DELETE_FAILED),
                    self.lang_manager.translate(TranslationKeys.PROPERTY_DELETE_BY_ID_PREVIEW_FAILED).format(
                        error=preview.get("error") or ""),
                )
                return

            delete_label = self.lang_manager.translate(TranslationKeys.PROPERTY_DELETE_BY_ID_DELETE_BUTTON)
            cancel_label = self.lang_manager.translate(TranslationKeys.CANCEL_BUTTON)
            confirmed = ModernMessageDialog.ask_yes_no(
                self.lang_manager.translate(TranslationKeys.PROPERTY_DELETE_BY_ID_CONFIRM_TITLE),
                self.lang_manager.translate(TranslationKeys.PROPERTY_DELETE_BY_ID_CONFIRM_BODY).format(
                    id=property_id,
                    number=preview.get("number") or "—",
                    address=preview.get("address") or "—",
                ),
                yes_label=delete_label,
                no_label=cancel_label,
                default=cancel_label,
            )
            if not confirmed:
                return

            ok, message = deleteProperty.delete_single_item(property_id)

            if not ok:
                ModernMessageDialog.show_warning(
                    self.lang_manager.translate(TranslationKeys.PROPERTY_DELETE_FAILED),
                    message,
                )
        finally:
            self._btn_confirm.setEnabled(True)
            self._btn_cancel.setEnabled(True)

        if ok:
            ModernMessageDialog.show_info(
                self.lang_manager.translate(TranslationKeys.PROPERTY_DELETED_TITLE),
                self.lang_manager.translate(TranslationKeys.PROPERTY_DELETED_MESSAGE),
            )
            self.accept()
            return
