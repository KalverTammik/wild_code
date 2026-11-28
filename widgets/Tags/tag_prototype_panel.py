"""Development prototype on the home page: the grouped tag selector with real tags, and a made-up
record that shows how its tags could look on a card. Nothing is saved to Kavitro."""
from __future__ import annotations

from typing import Optional

from qgis.PyQt.QtCore import Qt, pyqtSlot
from qgis.PyQt.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from ...constants.file_paths import QssPaths
from ...constants.module_names import Module
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...python.api_actions import APIModuleActions
from ...python.latest_request import LatestRequest
from ...python.tag_catalog import TagCatalog
from ...ui.theme_manager import ThemeManager
from ...utils.api_error_handling import user_message
from .grouped_tag_picker import GroupedTagPicker
from .tag_chips import SEPARATOR_KEYS, Look, TagChipsView

_MODULES = (Module.PROJECT.value, Module.CONTRACT.value, Module.COORDINATION.value)


class TagPrototypePanel(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("TagPrototypePanel")
        self._lang = LanguageManager()
        self._request = LatestRequest(self)
        self._request.finished.connect(self._on_loaded)
        self._request.error.connect(self._on_failed)
        self._loaded_module = ""

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)
        root.addWidget(self._build_selector(), 0, Qt.AlignmentFlag.AlignTop)
        root.addWidget(self._build_record(), 1, Qt.AlignmentFlag.AlignTop)
        self.retheme()

    def _text(self, key: str) -> str:
        return self._lang.translate(key)

    def _box(self, title_key: str) -> tuple[QFrame, QVBoxLayout]:
        box = QFrame(self)
        box.setObjectName("ModuleInfoCard")
        layout = QVBoxLayout(box)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)
        title = QLabel(self._text(title_key), box)
        title.setObjectName("ProjectNameLabel")
        layout.addWidget(title)
        return box, layout

    def _build_selector(self) -> QFrame:
        box, layout = self._box(TranslationKeys.TAG_PROTOTYPE_FILTER_TITLE)
        box.setFixedWidth(320)

        self.module_combo = QComboBox(box)
        for module in _MODULES:
            self.module_combo.addItem(self._lang.translate_module_name(module), module)
        layout.addWidget(self.module_combo)

        status_row = QHBoxLayout()
        self.status_label = QLabel(box)
        self.status_label.setWordWrap(True)
        status_row.addWidget(self.status_label, 1)
        self.reload_button = QPushButton(self._text(TranslationKeys.TAG_PROTOTYPE_RELOAD), box)
        self.reload_button.setAutoDefault(False)
        self.reload_button.clicked.connect(self.reload)
        status_row.addWidget(self.reload_button, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(status_row)

        self.filter_picker = GroupedTagPicker(box)
        layout.addWidget(self.filter_picker)
        self.filter_chips = TagChipsView(box)
        self.filter_picker.selectionChanged.connect(self._show_filter_choice)
        layout.addWidget(self.filter_chips)

        self.module_combo.currentIndexChanged.connect(lambda _index: self.reload())
        return box

    def _build_record(self) -> QFrame:
        box, layout = self._box(TranslationKeys.TAG_PROTOTYPE_RECORD_TITLE)

        hint = QLabel(self._text(TranslationKeys.TAG_PROTOTYPE_RECORD_HINT), box)
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.record_picker = GroupedTagPicker(box)
        self.record_picker.setMaximumWidth(320)
        self.record_picker.selectionChanged.connect(self._show_record_tags)
        layout.addWidget(self.record_picker)

        layout.addLayout(self._build_free_controls(box))
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
        self.record_chips = TagChipsView(card)
        card_layout.addWidget(self.record_chips)
        layout.addWidget(card)
        return box

    def _build_free_controls(self, box: QFrame) -> QHBoxLayout:
        """Try other measures on the sample record; real cards use the defaults."""
        row = QHBoxLayout()
        row.setSpacing(6)
        start = Look()
        self.look_spins: dict[str, QSpinBox] = {}
        for field, key, top in (
            ("radius", TranslationKeys.TAG_LOOK_RADIUS, 14), ("height", TranslationKeys.TAG_LOOK_HEIGHT, 6),
            ("tag_gap", TranslationKeys.TAG_LOOK_TAG_GAP, 16), ("capsule_gap", TranslationKeys.TAG_LOOK_CAPSULE_GAP, 20),
            ("tag_pad", TranslationKeys.TAG_LOOK_TAG_PAD, 24), ("name_pad", TranslationKeys.TAG_LOOK_NAME_PAD, 24),
        ):
            row.addWidget(QLabel(self._text(key), box))
            spin = QSpinBox(box)
            spin.setRange(0, top)
            spin.setValue(getattr(start, field))
            spin.setFixedWidth(56)
            spin.valueChanged.connect(self._apply_free_look)
            self.look_spins[field] = spin
            row.addWidget(spin)
        row.addWidget(QLabel(self._text(TranslationKeys.TAG_LOOK_SEPARATOR), box))
        self.separator_combo = QComboBox(box)
        for value, key in SEPARATOR_KEYS.items():
            self.separator_combo.addItem(self._text(key), value)
        self.separator_combo.setCurrentIndex(self.separator_combo.findData(start.separator))
        self.separator_combo.currentIndexChanged.connect(self._apply_free_look)
        row.addWidget(self.separator_combo)
        row.addStretch(1)
        return row

    def _apply_free_look(self, *_args) -> None:
        look = Look(separator=self.separator_combo.currentData(),
                    **{field: spin.value() for field, spin in self.look_spins.items()})
        self.record_chips.set_look(look)

    def activate(self) -> None:
        if self.module_combo.currentData() != self._loaded_module:
            self.reload()

    def deactivate(self) -> None:
        self._request.invalidate()
        self.filter_picker.close_popup()
        self.record_picker.close_popup()

    def reload(self) -> None:
        self._loaded_module = ""
        for picker in (self.filter_picker, self.record_picker):
            picker.set_selected_ids([])
        self._apply_catalog(TagCatalog())
        self.status_label.setText(self._text(TranslationKeys.LOADING))
        self._requested_module = self.module_combo.currentData()
        self._request.submit(APIModuleActions.get_module_tag_catalog, self._requested_module)

    @pyqtSlot(object)
    def _on_loaded(self, catalog: TagCatalog) -> None:
        self._loaded_module = self._requested_module
        self._apply_catalog(catalog)
        self.status_label.setText(self._text(TranslationKeys.TAG_PROTOTYPE_LOADED).format(
            tags=len(catalog), groups=len(catalog.groups)))
        # A few tags of every kind to start with, so the styles have something to show.
        sample = [tag.id for _group, tags in catalog.groups for tag in tags[:3]]
        self.record_picker.set_selected_ids(sample + [tag.id for tag in catalog.ungrouped[:8]], emit=True)  # enough to wrap

    @pyqtSlot(str)
    def _on_failed(self, message: str) -> None:
        self.status_label.setText(f"{self._text(TranslationKeys.ERROR)}: {user_message(message)}")

    def _apply_catalog(self, catalog: TagCatalog) -> None:
        self.filter_picker.set_catalog(catalog)
        self.record_picker.set_catalog(catalog)
        self._show_filter_choice()
        self._show_record_tags()

    def _show_filter_choice(self, *_args) -> None:
        self.filter_chips.show_tags(self.filter_picker.catalog(), self.filter_picker.selected_ids())

    def _show_record_tags(self, *_args) -> None:
        self.record_chips.show_tags(self.record_picker.catalog(), self.record_picker.selected_ids())

    def retheme(self) -> None:
        ThemeManager.apply_module_style(self, [QssPaths.MAIN, QssPaths.BUTTONS, QssPaths.MODULE_CARD, QssPaths.PILLS])
        ThemeManager.apply_form_combo_popup_style(self.module_combo)
        ThemeManager.apply_form_combo_popup_style(self.separator_combo)
        self.filter_picker.retheme()
        self.record_picker.retheme()
        self.record_chips.retheme()
        self.filter_chips.retheme()
