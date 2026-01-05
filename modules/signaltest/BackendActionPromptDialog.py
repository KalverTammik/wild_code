from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...widgets.theme_manager import ThemeManager
from ...constants.file_paths import QssPaths
from ...constants.button_props import ButtonVariant


class BackendActionPromptDialog(QDialog):
    """Modal prompt to choose an action for selected rows.

    Keeps UX simple: show the same table snapshot + buttons for actions.
    """

    def __init__(
        self,
        *,
        parent=None,
        table_frame,
        table,
        title: str = "Choose backend action",
    ) -> None:
        super().__init__(parent)

        self.lang_manager = LanguageManager()

        self._action: Optional[str] = None

        self.setWindowTitle(title)
        self.setModal(True)

        try:
            ThemeManager.apply_module_style(self, [QssPaths.MAIN])
        except Exception:
            pass

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        header = QLabel(title)
        header.setObjectName("FilterTitle")
        layout.addWidget(header)

        # Reuse the same table UI (frame + widget) from PropertyTableWidget factory.
        layout.addWidget(table_frame, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)

        cancel_text = self.lang_manager.translate(TranslationKeys.CANCEL) or "Cancel"
        archive_text = self.lang_manager.translate(TranslationKeys.ARCHIVE) or "Archive"
        unarchive_text = self.lang_manager.translate(TranslationKeys.UNARCHIVE) or "Unarchive"
        delete_text = self.lang_manager.translate(TranslationKeys.DELETE) or "Delete"

        self._btn_cancel = QPushButton(cancel_text)
        self._btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(self._btn_cancel)

        self._btn_archive = QPushButton(archive_text)
        self._btn_archive.setProperty("variant", ButtonVariant.DANGER)
        self._btn_archive.clicked.connect(lambda: self._choose("archive"))
        btn_row.addWidget(self._btn_archive)

        self._btn_unarchive = QPushButton(unarchive_text)
        self._btn_unarchive.setProperty("variant", ButtonVariant.DANGER)
        self._btn_unarchive.clicked.connect(lambda: self._choose("unarchive"))
        btn_row.addWidget(self._btn_unarchive)

        self._btn_delete = QPushButton(delete_text)
        self._btn_delete.setProperty("variant", ButtonVariant.DANGER)
        self._btn_delete.clicked.connect(lambda: self._choose("delete"))
        btn_row.addWidget(self._btn_delete)

        layout.addLayout(btn_row)

        try:
            table.setSelectionMode(table.NoSelection)
            table.setFocusPolicy(Qt.NoFocus)
        except Exception:
            pass

    def _choose(self, action: str) -> None:
        self._action = action
        self.accept()

    @property
    def action(self) -> Optional[str]:
        return self._action
