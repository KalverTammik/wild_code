from __future__ import annotations

import json
from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QHeaderView, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout

from ...Logs.python_fail_logger import PythonFailLogger
from ...languages.translation_keys import TranslationKeys
from ...python.api_actions import APIModuleActions
from ...utils.messagesHelper import ModernMessageDialog
from ...utils.url_manager import Module
from ..easements.easement_layer_service import EasementLayerService


class EasementStatusMappingDialog(QDialog):
    def __init__(self, *, lang_manager, stored_value: str = "", parent=None):
        super().__init__(parent)
        self._lang = lang_manager
        self._stored_value = str(stored_value or "")
        self._status_options = APIModuleActions.get_module_status_options(Module.EASEMENT.value)
        self._layer = EasementLayerService.resolve_main_layer(lang_manager=self._lang, silent=True)
        self._status_field_name = EasementLayerService.resolve_status_field_name(self._layer)
        self._layer_values = EasementLayerService.layer_status_value_options(self._layer)
        self._existing_rows = EasementLayerService.parse_status_mapping_rows(self._stored_value)
        self._existing_by_id = {
            str(row.get("statusId") or "").strip(): str(row.get("layerStatus") or "").strip()
            for row in self._existing_rows
            if str(row.get("statusId") or "").strip()
        }
        self._existing_by_name = {
            str(row.get("statusName") or "").strip().upper(): str(row.get("layerStatus") or "").strip()
            for row in self._existing_rows
            if str(row.get("statusName") or "").strip()
        }
        self._combo_by_status_id: dict[str, QComboBox] = {}
        self._table: Optional[QTableWidget] = None
        self.setWindowTitle(self._lang.translate(TranslationKeys.EASEMENT_STATUS_MAPPING_TITLE))
        self.resize(760, 520)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        description = QLabel(
            self._lang.translate(TranslationKeys.EASEMENT_STATUS_MAPPING_DESCRIPTION).format(
                layer=getattr(self._layer, "name", lambda: "")() if self._layer is not None else "-",
                field=self._status_field_name or "-",
            )
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        field_label = QLabel(
            self._lang.translate(TranslationKeys.EASEMENT_STATUS_MAPPING_LAYER_FIELD).format(
                field=self._status_field_name or "-"
            )
        )
        field_label.setWordWrap(True)
        layout.addWidget(field_label)

        self._table = QTableWidget(len(self._status_options), 2, self)
        self._table.setHorizontalHeaderLabels(
            [
                self._lang.translate(TranslationKeys.EASEMENT_STATUS_MAPPING_BACKEND_HEADER),
                self._lang.translate(TranslationKeys.EASEMENT_STATUS_MAPPING_LAYER_HEADER),
            ]
        )
        header = self._table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.verticalHeader().setVisible(False)

        for row_index, status in enumerate(self._status_options):
            status_id = str(status.get("id") or "").strip()
            status_name = str(status.get("name") or "").strip()
            status_description = str(status.get("description") or "").strip()

            item = QTableWidgetItem(status_name)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            if status_description:
                item.setToolTip(status_description)
            self._table.setItem(row_index, 0, item)

            combo = QComboBox(self._table)
            combo.addItem(self._lang.translate(TranslationKeys.EASEMENT_STATUS_MAPPING_NONE_OPTION), "")
            for layer_value in self._layer_values:
                combo.addItem(layer_value, layer_value)

            existing_value = self._existing_by_id.get(status_id) or self._existing_by_name.get(status_name.upper()) or ""
            if existing_value and combo.findData(existing_value) < 0:
                combo.addItem(existing_value, existing_value)
            if existing_value:
                combo.setCurrentIndex(max(0, combo.findData(existing_value)))

            self._table.setCellWidget(row_index, 1, combo)
            if status_id:
                self._combo_by_status_id[status_id] = combo

        layout.addWidget(self._table)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def serialized_mapping(self) -> str:
        rows: list[dict[str, str]] = []
        for status in self._status_options:
            status_id = str(status.get("id") or "").strip()
            if not status_id:
                continue
            combo = self._combo_by_status_id.get(status_id)
            if combo is None:
                continue
            layer_value = str(combo.currentData() or "").strip()
            if not layer_value:
                continue
            rows.append(
                {
                    "statusId": status_id,
                    "statusName": str(status.get("name") or "").strip(),
                    "layerStatus": layer_value,
                }
            )
        return json.dumps(rows, ensure_ascii=False)

    @classmethod
    def edit_mapping(cls, *, lang_manager, stored_value: str = "", parent=None) -> Optional[str]:
        layer = EasementLayerService.resolve_main_layer(lang_manager=lang_manager, silent=True)
        if layer is None:
            ModernMessageDialog.show_warning(
                lang_manager.translate(TranslationKeys.ERROR),
                lang_manager.translate(TranslationKeys.EASEMENT_STATUS_MAPPING_NO_MAIN_LAYER),
            )
            return None

        status_field_name = EasementLayerService.resolve_status_field_name(layer)
        if not status_field_name:
            ModernMessageDialog.show_warning(
                lang_manager.translate(TranslationKeys.ERROR),
                lang_manager.translate(TranslationKeys.EASEMENT_STATUS_MAPPING_NO_STATUS_FIELD),
            )
            return None

        layer_values = EasementLayerService.layer_status_value_options(layer)
        if not layer_values:
            ModernMessageDialog.show_warning(
                lang_manager.translate(TranslationKeys.ERROR),
                lang_manager.translate(TranslationKeys.EASEMENT_STATUS_MAPPING_NO_LAYER_VALUES).format(field=status_field_name),
            )
            return None

        statuses = APIModuleActions.get_module_status_options(Module.EASEMENT.value)
        if not statuses:
            ModernMessageDialog.show_warning(
                lang_manager.translate(TranslationKeys.ERROR),
                lang_manager.translate(TranslationKeys.EASEMENT_STATUS_MAPPING_NO_BACKEND_STATUSES),
            )
            return None

        dialog = cls(lang_manager=lang_manager, stored_value=stored_value, parent=parent)
        try:
            if dialog.exec_() == QDialog.Accepted:
                return dialog.serialized_mapping()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.SETTINGS.value,
                event="easement_status_mapping_dialog_failed",
            )
        return None
