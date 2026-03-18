from __future__ import annotations

from typing import Iterable, Optional

from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from ...constants.button_props import ButtonVariant
from ...constants.file_paths import QssPaths
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...utils.FilterHelpers.FilterHelper import FilterHelper
from ...utils.messagesHelper import ModernMessageDialog
from ...utils.url_manager import Module, ModuleSupports
from ...widgets.theme_manager import ThemeManager
from .works_layer_service import WorksLayerService


class WorksCreateDialog(QDialog):
    def __init__(
        self,
        *,
        point,
        property_feature=None,
        allowed_type_ids: Optional[Iterable[str]] = None,
        type_options: Optional[Iterable[dict]] = None,
        assignable_users: Optional[Iterable[dict]] = None,
        priority_options: Optional[Iterable[dict]] = None,
        default_priority: str = "",
        default_responsible_id: str = "",
        lang_manager=None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._lang = lang_manager or LanguageManager()
        self._point = point
        self._property_feature = property_feature
        self._allowed_type_ids = {str(item_id) for item_id in (allowed_type_ids or []) if item_id}
        self._type_options = list(type_options or [])
        self._assignable_users = list(assignable_users or [])
        self._priority_options = list(priority_options or [])
        self._default_priority = str(default_priority or "").strip().upper()
        self._default_responsible_id = str(default_responsible_id or "").strip()
        self._title_touched = False

        self.setModal(True)
        self.setObjectName("WorksCreateDialog")
        self.setWindowTitle(self._lang.translate(TranslationKeys.WORKS_CREATE_DIALOG_TITLE))
        self.resize(620, 420)

        self._build_ui()
        self._populate_priorities()
        self._populate_types()
        self._populate_responsibles()
        self._apply_initial_title()

        ThemeManager.apply_module_style(self, [QssPaths.MAIN, QssPaths.BUTTONS, QssPaths.MODULE_INFO])

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        intro = QLabel(self._lang.translate(TranslationKeys.WORKS_CREATE_DIALOG_INTRO), self)
        intro.setWordWrap(True)
        root.addWidget(intro)

        info_frame = QFrame(self)
        info_layout = QGridLayout(info_frame)
        info_layout.setContentsMargins(8, 8, 8, 8)
        info_layout.setHorizontalSpacing(10)
        info_layout.setVerticalSpacing(6)

        property_title = QLabel(self._lang.translate(TranslationKeys.WORKS_CREATE_PROPERTY_LABEL), info_frame)
        self._property_value = QLabel(
            WorksLayerService.property_display_text(self._property_feature, lang_manager=self._lang),
            info_frame,
        )
        self._property_value.setWordWrap(True)

        coordinates_title = QLabel(self._lang.translate(TranslationKeys.WORKS_CREATE_COORDINATES_LABEL), info_frame)
        self._coordinates_value = QLabel(
            f"{self._point.x():.2f}, {self._point.y():.2f}",
            info_frame,
        )

        info_layout.addWidget(property_title, 0, 0)
        info_layout.addWidget(self._property_value, 0, 1)
        info_layout.addWidget(coordinates_title, 1, 0)
        info_layout.addWidget(self._coordinates_value, 1, 1)
        root.addWidget(info_frame)

        form = QGridLayout()
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(8)

        type_label = QLabel(self._lang.translate(TranslationKeys.WORKS_CREATE_TYPE_LABEL), self)
        self._type_combo = QComboBox(self)
        self._type_combo.currentIndexChanged.connect(self._update_suggested_title)

        title_label = QLabel(self._lang.translate(TranslationKeys.WORKS_CREATE_TITLE_LABEL), self)
        self._title_edit = QLineEdit(self)
        self._title_edit.setPlaceholderText(
            self._lang.translate(TranslationKeys.WORKS_CREATE_TITLE_PLACEHOLDER)
        )
        self._title_edit.textEdited.connect(self._mark_title_touched)

        description_label = QLabel(self._lang.translate(TranslationKeys.WORKS_CREATE_DESCRIPTION_LABEL), self)
        self._description_edit = QTextEdit(self)
        self._description_edit.setAcceptRichText(False)
        self._description_edit.setMinimumHeight(120)

        priority_label = QLabel(self._lang.translate(TranslationKeys.WORKS_CREATE_PRIORITY_LABEL), self)
        self._priority_combo = QComboBox(self)

        responsible_label = QLabel(self._lang.translate(TranslationKeys.WORKS_CREATE_RESPONSIBLE_LABEL), self)
        self._responsible_combo = QComboBox(self)

        form.addWidget(type_label, 0, 0)
        form.addWidget(self._type_combo, 0, 1)
        form.addWidget(title_label, 1, 0)
        form.addWidget(self._title_edit, 1, 1)
        form.addWidget(responsible_label, 2, 0)
        form.addWidget(self._responsible_combo, 2, 1)
        form.addWidget(priority_label, 3, 0)
        form.addWidget(self._priority_combo, 3, 1)
        form.addWidget(description_label, 4, 0)
        form.addWidget(self._description_edit, 4, 1)
        root.addLayout(form)

        self._types_hint = QLabel("", self)
        self._types_hint.setWordWrap(True)
        self._types_hint.setVisible(False)
        root.addWidget(self._types_hint)

        buttons = QHBoxLayout()
        buttons.setContentsMargins(0, 0, 0, 0)
        buttons.setSpacing(8)
        buttons.addStretch(1)

        self._cancel_btn = QPushButton(self._lang.translate(TranslationKeys.CANCEL_BUTTON), self)
        self._cancel_btn.setProperty("variant", ButtonVariant.GHOST)
        self._cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(self._cancel_btn)

        self._create_btn = QPushButton(self._lang.translate(TranslationKeys.WORKS_CREATE_ON_MAP_BUTTON), self)
        self._create_btn.setProperty("variant", ButtonVariant.SUCCESS)
        self._create_btn.clicked.connect(self._validate_and_accept)
        buttons.addWidget(self._create_btn)

        for button in (self._cancel_btn, self._create_btn):
            button.setAutoDefault(False)
            button.setDefault(False)

        root.addLayout(buttons)

    def _populate_priorities(self) -> None:
        self._priority_combo.clear()
        for option in self._priority_options:
            if not isinstance(option, dict):
                continue

            value = str(option.get("value") or "").strip().upper()
            label = str(option.get("label") or value or "").strip()
            if not label:
                continue
            self._priority_combo.addItem(label, value)

        if self._priority_combo.count() <= 0:
            self._priority_combo.addItem(self._lang.translate(TranslationKeys.WORKS_PRIORITY_NONE), "")

        if self._default_priority:
            index = self._priority_combo.findData(self._default_priority)
            if index >= 0:
                self._priority_combo.setCurrentIndex(index)

    def _populate_types(self) -> None:
        self._type_combo.clear()
        self._type_combo.addItem(self._lang.translate(TranslationKeys.SELECT), "")

        entries = list(self._type_options)
        if not entries:
            try:
                entries = FilterHelper.get_filter_edges_by_key_and_module(
                    ModuleSupports.TYPES.value,
                    Module.WORKS.value,
                )
            except Exception:
                entries = []

        visible_entries = []
        for entry in entries or []:
            type_id = str((entry or {}).get("id") or "").strip()
            label = str((entry or {}).get("label") or "").strip()
            if not type_id or not label:
                continue
            if self._allowed_type_ids and type_id not in self._allowed_type_ids:
                continue
            visible_entries.append((label, type_id))

        for label, type_id in visible_entries:
            self._type_combo.addItem(label, type_id)

        has_types = len(visible_entries) > 0
        self._create_btn.setEnabled(has_types)
        if has_types:
            self._types_hint.setVisible(False)
            return

        self._types_hint.setText(self._lang.translate(TranslationKeys.WORKS_CREATE_NO_TYPES))
        self._types_hint.setVisible(True)

    def _populate_responsibles(self) -> None:
        self._responsible_combo.clear()
        seen: set[str] = set()

        for user in self._assignable_users:
            if not isinstance(user, dict):
                continue
            user_id = str(user.get("id") or "").strip()
            display_name = str(user.get("displayName") or user.get("name") or "").strip()
            if not user_id or not display_name or user_id in seen:
                continue
            self._responsible_combo.addItem(display_name, user_id)
            seen.add(user_id)

        if self._responsible_combo.count() <= 0:
            self._responsible_combo.setEnabled(False)
            return

        self._responsible_combo.setEnabled(True)
        if self._default_responsible_id:
            index = self._responsible_combo.findData(self._default_responsible_id)
            if index >= 0:
                self._responsible_combo.setCurrentIndex(index)

    def _apply_initial_title(self) -> None:
        self._update_suggested_title()

    def _mark_title_touched(self, _text: str) -> None:
        self._title_touched = True

    def _update_suggested_title(self) -> None:
        if self._title_touched and self._title_edit.text().strip():
            return

        property_text = WorksLayerService.property_display_text(
            self._property_feature,
            lang_manager=self._lang,
        )
        type_text = self.selected_type_label()
        parts = []
        if property_text and property_text != self._lang.translate(TranslationKeys.WORKS_CREATE_PROPERTY_NONE):
            parts.append(property_text)
        if type_text:
            parts.append(type_text)

        suggestion = " - ".join(parts).strip()
        self._title_edit.setText(suggestion)

    def _validate_and_accept(self) -> None:
        if not self.selected_type_id():
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.WORKS_CREATE_VALIDATE_TYPE),
            )
            self._type_combo.setFocus()
            return

        if not self.title_text():
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.WORKS_CREATE_VALIDATE_TITLE),
            )
            self._title_edit.setFocus()
            return

        self.accept()

    def selected_type_id(self) -> str:
        return str(self._type_combo.currentData() or "").strip()

    def selected_type_label(self) -> str:
        return str(self._type_combo.currentText() or "").strip()

    def title_text(self) -> str:
        return str(self._title_edit.text() or "").strip()

    def description_text(self) -> str:
        return str(self._description_edit.toPlainText() or "").strip()

    def priority_value(self) -> str:
        return str(self._priority_combo.currentData() or "").strip()

    def selected_responsible_id(self) -> str:
        return str(self._responsible_combo.currentData() or "").strip()

    def selected_responsible_label(self) -> str:
        return str(self._responsible_combo.currentText() or "").strip()