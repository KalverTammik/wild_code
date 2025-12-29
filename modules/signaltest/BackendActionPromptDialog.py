from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from ...widgets.theme_manager import ThemeManager
from ...constants.file_paths import QssPaths


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

        self._btn_cancel = QPushButton("Cancel")
        self._btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(self._btn_cancel)

        self._btn_archive = QPushButton("Archive")
        self._btn_archive.setProperty("variant", "danger")
        self._btn_archive.clicked.connect(lambda: self._choose("archive"))
        btn_row.addWidget(self._btn_archive)

        self._btn_unarchive = QPushButton("Unarchive")
        self._btn_unarchive.setProperty("variant", "danger")
        self._btn_unarchive.clicked.connect(lambda: self._choose("unarchive"))
        btn_row.addWidget(self._btn_unarchive)

        self._btn_delete = QPushButton("Delete")
        self._btn_delete.setProperty("variant", "danger")
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
