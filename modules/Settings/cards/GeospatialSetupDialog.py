from __future__ import annotations

from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout

from ....languages.translation_keys import TranslationKeys


class GeospatialSetupDialog(QDialog):
    def __init__(self, *, lang_manager, parent=None):
        super().__init__(parent)
        self._lang = lang_manager
        self.setWindowTitle(self._lang.translate(TranslationKeys.SETTINGS_GEOSPATIAL_DIALOG_TITLE))
        self.resize(560, 260)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        body = QLabel(self._lang.translate(TranslationKeys.SETTINGS_GEOSPATIAL_DIALOG_BODY), self)
        body.setWordWrap(True)
        layout.addWidget(body)

        scope = QLabel(self._lang.translate(TranslationKeys.SETTINGS_GEOSPATIAL_DIALOG_SCOPE), self)
        scope.setWordWrap(True)
        layout.addWidget(scope)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
