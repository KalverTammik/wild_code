"""Development prototype on the home page: six ways to show a record's contacts, with settings."""
from __future__ import annotations

from typing import Optional

from qgis.PyQt.QtWidgets import QCheckBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QSpinBox, QVBoxLayout, QWidget

from ...constants.file_paths import QssPaths
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...ui.theme_manager import ThemeManager
from ..DataDisplayWidgets.ContactsWidget import ContactLook
from .contact_styles import IDEAS, SAMPLE_CONTACTS


class ContactPrototypePanel(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("ContactPrototypePanel")
        self._lang = LanguageManager()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        box = QFrame(self)
        box.setObjectName("ModuleInfoCard")
        outer.addWidget(box)
        layout = QVBoxLayout(box)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)
        title = QLabel(self._text(TranslationKeys.CONTACT_PROTO_TITLE), box)
        title.setObjectName("ProjectNameLabel")
        layout.addWidget(title)
        layout.addLayout(self._build_controls(box))

        grid = QGridLayout()
        grid.setSpacing(10)
        self.views = []
        for index, (title_key, view_class) in enumerate(IDEAS):
            column = QVBoxLayout()
            column.setSpacing(3)
            column.addWidget(QLabel(f"{index + 1} · {self._text(title_key)}", box))
            card = QFrame(box)
            card.setObjectName("GroupedTagRecord")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 8, 12, 10)
            card_layout.setSpacing(6)
            name_row = QHBoxLayout()
            number = QLabel("2026-001", card)
            number.setObjectName("ProjectNumberBadge")
            name_row.addWidget(number)
            name = QLabel(self._text(TranslationKeys.TAG_PROTOTYPE_RECORD_NAME), card)
            name.setObjectName("ProjectNameLabel")
            name_row.addWidget(name, 1)
            card_layout.addLayout(name_row)
            view = view_class(card)
            card_layout.addWidget(view)
            self.views.append(view)
            column.addWidget(card)
            column.addStretch(1)
            grid.addLayout(column, index // 2, index % 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)
        self._apply()
        self.retheme()

    def _text(self, key: str) -> str:
        return self._lang.translate(key)

    def _build_controls(self, box: QFrame) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(6)
        start = ContactLook()
        self.spins: dict[str, QSpinBox] = {}
        for field, key, low, high, value in (
            ("count", TranslationKeys.CONTACT_PROTO_COUNT, 0, len(SAMPLE_CONTACTS), 5),
            ("shown", TranslationKeys.CONTACT_PROTO_SHOWN, 0, len(SAMPLE_CONTACTS), start.shown),
            ("gap", TranslationKeys.TAG_LOOK_TAG_GAP_CONTACTS, 0, 24, start.gap),
            ("radius", TranslationKeys.TAG_LOOK_RADIUS, 0, 14, start.radius),
        ):
            row.addWidget(QLabel(self._text(key), box))
            spin = QSpinBox(box)
            spin.setRange(low, high)
            if field == "shown":
                spin.setSpecialValueText("–")  # no cap: the width decides
            spin.setValue(value)
            spin.setFixedWidth(56)
            spin.valueChanged.connect(self._apply)
            self.spins[field] = spin
            row.addWidget(spin)
        self.roles_check = QCheckBox(self._text(TranslationKeys.CONTACT_PROTO_ROLES), box)
        self.roles_check.setChecked(start.roles)
        self.roles_check.toggled.connect(self._apply)
        row.addWidget(self.roles_check)
        row.addStretch(1)
        return row

    def _apply(self, *_args) -> None:
        look = ContactLook(
            shown=self.spins["shown"].value(), roles=self.roles_check.isChecked(),
            gap=self.spins["gap"].value(), radius=self.spins["radius"].value())
        contacts = SAMPLE_CONTACTS[: self.spins["count"].value()]
        for view in self.views:
            view.show_contacts(contacts, look)

    def retheme(self) -> None:
        ThemeManager.apply_module_style(self, [QssPaths.MAIN, QssPaths.BUTTONS, QssPaths.MODULE_CARD, QssPaths.PILLS])
        for view in self.views:
            view.retheme()
