from __future__ import annotations

from ...constants.button_props import ButtonVariant
from ...constants.file_paths import QssPaths
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ..theme_manager import ThemeManager


def prompt_backend_action_dialog(*, parent=None, table_frame, table, title: str = "Choose backend action") -> str | None:
    """Show the shared backend action prompt and return the chosen action."""

    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

    lang_manager = LanguageManager()
    dialog = QDialog(parent)
    action: str | None = None

    def choose(selected_action: str) -> None:
        nonlocal action
        action = selected_action
        dialog.accept()

    dialog.setWindowTitle(title)
    dialog.setModal(True)

    ThemeManager.apply_module_style(dialog, [QssPaths.MAIN])

    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(12, 12, 12, 12)
    layout.setSpacing(10)

    header = QLabel(title)
    header.setObjectName("FilterTitle")
    layout.addWidget(header)

    layout.addWidget(table_frame, 1)

    btn_row = QHBoxLayout()
    btn_row.addStretch(1)

    cancel_text = lang_manager.translate(TranslationKeys.CANCEL_BUTTON) or "Cancel"
    archive_text = lang_manager.translate(TranslationKeys.ARCHIVE) or "Archive"
    unarchive_text = lang_manager.translate(TranslationKeys.UNARCHIVE) or "Unarchive"
    delete_text = lang_manager.translate(TranslationKeys.DELETE) or "Delete"

    btn_cancel = QPushButton(cancel_text)
    btn_cancel.clicked.connect(dialog.reject)
    btn_row.addWidget(btn_cancel)

    btn_archive = QPushButton(archive_text)
    btn_archive.setProperty("variant", ButtonVariant.DANGER)
    btn_archive.clicked.connect(lambda: choose("archive"))
    btn_row.addWidget(btn_archive)

    btn_unarchive = QPushButton(unarchive_text)
    btn_unarchive.setProperty("variant", ButtonVariant.DANGER)
    btn_unarchive.clicked.connect(lambda: choose("unarchive"))
    btn_row.addWidget(btn_unarchive)

    btn_delete = QPushButton(delete_text)
    btn_delete.setProperty("variant", ButtonVariant.DANGER)
    btn_delete.clicked.connect(lambda: choose("delete"))
    btn_row.addWidget(btn_delete)

    layout.addLayout(btn_row)

    table.setSelectionMode(table.NoSelection)
    table.setFocusPolicy(Qt.NoFocus)

    ok = dialog.exec_()
    if not ok:
        return None
    return action
