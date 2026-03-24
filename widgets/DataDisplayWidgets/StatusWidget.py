from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QMenu, QVBoxLayout, QWidget
try:
    import sip
except Exception:  # pragma: no cover - depends on runtime packaging
    sip = None

from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...Logs.python_fail_logger import PythonFailLogger
from ...python.api_actions import APIModuleActions
from ...python.responses import DataDisplayExtractors, StatusInfo
from ...utils.messagesHelper import ModernMessageDialog
from ...utils.status_color_helper import StatusColorHelper
from ...utils.url_manager import Module


class _ClickableStatusLabel(QLabel):
    clicked = pyqtSignal()

    def mousePressEvent(self, event) -> None:  # noqa: N802 - Qt override
        if event.button() == Qt.LeftButton and self.isEnabled():
            self.clicked.emit()
            event.accept()
            return
        super().mousePressEvent(event)


class StatusWidget(QWidget):
    _EDITABLE_MODULES = {Module.WORKS.value, Module.ASBUILT.value, Module.TASK.value}

    def __init__(self, item_data, module_name: Optional[str] = None, parent=None, lang_manager=None):
        super().__init__(parent)
        self._item_data = dict(item_data or {}) if isinstance(item_data, dict) else dict(item_data or {})
        self._module_name = str(module_name or "").strip().lower()
        self._lang = lang_manager or LanguageManager()
        self._is_updating = False
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.timeout.connect(self._perform_scheduled_card_refresh)
        self._pending_refresh_payload: Optional[dict] = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addStretch(1)

        self.status_label = _ClickableStatusLabel(self)
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFixedWidth(136)

        if self._can_edit_status():
            self.status_label.setCursor(Qt.PointingHandCursor)
            self.status_label.setToolTip(
                self._lang.translate(TranslationKeys.STATUS_WIDGET_CHANGE_TOOLTIP)
            )
            self.status_label.clicked.connect(self._show_status_menu)

        row.addWidget(self.status_label, 0, Qt.AlignRight | Qt.AlignVCenter)
        main_layout.addLayout(row)
        self._apply_status_info(DataDisplayExtractors.extract_status(self._item_data))

    def _can_edit_status(self) -> bool:
        item_id = str(self._item_data.get("id") or "").strip()
        return bool(item_id and self._module_name in self._EDITABLE_MODULES)

    def _apply_status_info(self, status_info: StatusInfo, *, loading: bool = False) -> None:
        base_name = str(status_info.name or "-").strip() or "-"
        display_name = self._lang.translate(TranslationKeys.LOADING) if loading else base_name
        if self._can_edit_status() and not loading:
            display_name = f"{display_name} ▾"

        hex_color = str(status_info.color or "cccccc").strip() or "cccccc"
        bg, fg, border = StatusColorHelper.upgrade_status_color(hex_color)

        self.status_label.setText(display_name)
        self.status_label.setStyleSheet(
            "QLabel#StatusLabel {"
            f"background-color: rgba({bg[0]},{bg[1]},{bg[2]}, 0.95);"
            f"color: rgb({fg[0]},{fg[1]},{fg[2]});"
            f"border: 1px solid rgba({border[0]},{border[1]},{border[2]}, 0.85);"
            "border-radius: 6px;"
            "padding: 3px 10px;"
            "font-weight: 500;"
            "font-size: 11px;"
            "}"
            "QLabel#StatusLabel:hover {"
            f"background-color: rgba({bg[0]},{bg[1]},{bg[2]}, 1.0);"
            "}"
        )

    def _show_status_menu(self) -> None:
        if not self._can_edit_status() or self._is_updating:
            return

        status_options = APIModuleActions.get_module_status_options(self._module_name)
        if not status_options:
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.WARNING),
                self._lang.translate(TranslationKeys.STATUS_WIDGET_NO_OPTIONS),
            )
            return

        current_status_id = DataDisplayExtractors.extract_status(self._item_data).id
        menu = QMenu(self)
        menu.setObjectName("StatusMenu")

        for option in status_options:
            action = menu.addAction(str(option.get("name") or "-"))
            action.setData(option)
            action.setCheckable(True)
            action.setChecked(str(option.get("id") or "") == current_status_id)

        selected_action = menu.exec_(self.status_label.mapToGlobal(self.status_label.rect().bottomLeft()))
        if selected_action is None:
            return

        selected_option = selected_action.data() or {}
        new_status_id = str(selected_option.get("id") or "").strip()
        if not new_status_id or new_status_id == current_status_id:
            return

        self._update_status(selected_option)

    def _update_status(self, selected_option: dict) -> None:
        item_id = str(self._item_data.get("id") or "").strip()
        new_status_id = str(selected_option.get("id") or "").strip()
        if not item_id or not new_status_id:
            return

        previous_status = DataDisplayExtractors.extract_status(self._item_data)
        self._is_updating = True
        self._apply_status_info(previous_status, loading=True)
        QApplication.processEvents()
        QApplication.setOverrideCursor(Qt.WaitCursor)

        try:
            updated_task = APIModuleActions.update_task_status(item_id, new_status_id)
        finally:
            QApplication.restoreOverrideCursor()
            self._is_updating = False

        if not isinstance(updated_task, dict):
            self._apply_status_info(previous_status)
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.STATUS_WIDGET_UPDATE_FAILED),
            )
            return

        refreshed_item = APIModuleActions.get_task_data(item_id)
        if not isinstance(refreshed_item, dict):
            refreshed_item = dict(self._item_data)
            status_payload = updated_task.get("status") if isinstance(updated_task.get("status"), dict) else None
            if not status_payload:
                status_payload = self._status_payload_from_option(selected_option)
            refreshed_item["status"] = status_payload
            if updated_task.get("updatedAt") is not None:
                refreshed_item["updatedAt"] = updated_task.get("updatedAt")

        self._item_data = dict(refreshed_item)
        self._apply_status_info(DataDisplayExtractors.extract_status(self._item_data))
        self._sync_works_layer_if_needed(task_payload=refreshed_item)
        self._schedule_card_refresh(refreshed_item)

    @staticmethod
    def _status_payload_from_option(option: dict) -> dict[str, str]:
        return {
            "id": str(option.get("id") or "").strip(),
            "name": str(option.get("name") or "").strip(),
            "color": str(option.get("color") or "cccccc").strip() or "cccccc",
            "type": str(option.get("type") or "").strip().upper(),
        }

    def _sync_works_layer_if_needed(self, *, task_payload: Optional[dict] = None) -> None:
        if self._module_name not in {Module.WORKS.value, Module.ASBUILT.value, Module.TASK.value}:
            return

        item_id = str(self._item_data.get("id") or "").strip()
        if not item_id:
            return

        try:
            from ...modules.works.works_sync_service import WorksSyncService

            sync_service = WorksSyncService(lang_manager=self._lang)
            sync_service.sync_task_from_backend(item_id, task=task_payload)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="status_widget_sync_works_layer_failed",
                extra={"source_module": self._module_name},
            )

    def _schedule_card_refresh(self, item_data: Optional[dict]) -> None:
        if not isinstance(item_data, dict) or not item_data:
            return
        self._pending_refresh_payload = dict(item_data)
        self._refresh_timer.start(0)

    def _perform_scheduled_card_refresh(self) -> None:
        payload = dict(self._pending_refresh_payload or {})
        self._pending_refresh_payload = None
        if not payload:
            return
        if self._is_deleted(self):
            return
        self._replace_current_card(payload)

    @staticmethod
    def _is_deleted(widget) -> bool:
        try:
            return bool(widget is None or (sip and sip.isdeleted(widget)))
        except Exception:
            return widget is None

    def _replace_current_card(self, item_data: dict) -> None:
        if self._is_deleted(self):
            return
        card = self._find_parent_card()
        if self._is_deleted(card):
            return

        container = card.parentWidget()
        if self._is_deleted(container):
            return
        layout = container.layout() if container is not None else None
        insert_widget = getattr(layout, "insertWidget", None)
        remove_widget = getattr(layout, "removeWidget", None)
        index_of = getattr(layout, "indexOf", None)
        if not callable(insert_widget) or not callable(remove_widget) or not callable(index_of):
            return

        index = index_of(card)
        if index < 0:
            return

        try:
            from ...ui.module_card_factory import ModuleCardFactory

            replacement = ModuleCardFactory.create_item_card(
                item_data,
                module_name=self._module_name,
                lang_manager=self._lang,
            )
            container.setUpdatesEnabled(False)
            remove_widget(card)
            card.hide()
            card.setParent(None)
            insert_widget(index, replacement)
            card.deleteLater()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=str(self._module_name or ""),
                event="status_widget_replace_card_failed",
                extra={"item_id": str(item_data.get("id") or "")},
            )
        finally:
            if not self._is_deleted(container):
                container.setUpdatesEnabled(True)

    def _find_parent_card(self) -> Optional[QFrame]:
        current = self.parentWidget()
        while current is not None:
            if isinstance(current, QFrame) and current.objectName() == "ModuleInfoCard":
                return current
            current = current.parentWidget()
        return None

