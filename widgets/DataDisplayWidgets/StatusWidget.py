from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QProgressBar, QVBoxLayout, QWidget
try:
    import sip
except ImportError:  # pragma: no cover - depends on runtime packaging
    sip = None

from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...Logs.python_fail_logger import PythonFailLogger
from ...python.api_actions import APIModuleActions
from ...python.workers import FunctionWorker, start_worker
from ...python.responses import DataDisplayExtractors, StatusInfo
from ...ui.window_state.popup_helpers import PopupHelpers
from ...ui.messages_helper import ModernMessageDialog
from ...utils.status_color_helper import StatusColorHelper
from ...constants.module_names import Module, backend_module


def _change_status(module_name: str, item_id: str, status_id: str) -> dict:
    """Runs on a worker thread: the status change, and for a task section the card read again."""
    updated = APIModuleActions.update_item_status(module_name, item_id, status_id)
    refreshed = None
    if isinstance(updated, dict) and backend_module(module_name) == Module.TASK.value:
        refreshed = APIModuleActions.get_task_data(item_id)
    return {"updated": updated, "refreshed": refreshed}


class _StatusSavingDialog(QDialog):
    """Shown only when a status change takes longer than StatusWidget.SAVING_DIALOG_DELAY_MS; it cannot be closed by hand."""

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(text)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.setMinimumWidth(320)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(text, self))
        bar = QProgressBar(self)
        bar.setRange(0, 0)
        layout.addWidget(bar)
        ModernMessageDialog.style_as_message(self)

    def reject(self) -> None:
        """Escape must not hide a write that is still running."""


class _ClickableStatusLabel(QLabel):
    clicked = pyqtSignal()

    def mousePressEvent(self, event) -> None:  # noqa: N802 - Qt override
        if event.button() == Qt.LeftButton and self.isEnabled():
            self.clicked.emit()
            event.accept()
            return
        super().mousePressEvent(event)


class _StatusOptionRow(QFrame):
    clicked = pyqtSignal(object)

    def __init__(self, option: dict, *, is_current: bool, parent=None):
        super().__init__(parent)
        self._option = dict(option or {})
        self.setObjectName("StatusOptionRow")
        self.setCursor(Qt.PointingHandCursor)

        status_name = str(self._option.get("name") or "-")
        status_color = str(self._option.get("color") or "cccccc")
        bg, fg, border = StatusColorHelper.upgrade_status_color(status_color)
        fill_alpha = "0.20" if is_current else "0.00"
        border_alpha = "0.42" if is_current else "0.00"

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        name_label = QLabel(status_name, self)
        name_label.setObjectName("Value")
        name_label.setStyleSheet(
            "QLabel#Value {"
            f"color: rgb({fg[0]},{fg[1]},{fg[2]});"
            "font-weight: 600;"
            "}"
        )
        layout.addWidget(name_label, 1)

        self.setStyleSheet(
            "QFrame#StatusOptionRow {"
            f"background-color: rgba({bg[0]},{bg[1]},{bg[2]}, {fill_alpha});"
            f"border: 1px solid rgba({border[0]},{border[1]},{border[2]}, {border_alpha});"
            "border-radius: 6px;"
            "}"
            "QFrame#StatusOptionRow:hover {"
            f"background-color: rgba({bg[0]},{bg[1]},{bg[2]}, 0.24);"
            f"border: 1px solid rgba({border[0]},{border[1]},{border[2]}, 0.52);"
            "}"
        )

    def mousePressEvent(self, event) -> None:  # noqa: N802 - Qt override
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self._option)
            event.accept()
            return
        super().mousePressEvent(event)


class _StatusOptionsPopup(QWidget):
    optionSelected = pyqtSignal(object)

    def __init__(self, options: list[dict], current_status_id: str, parent=None):
        super().__init__(parent, flags=Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.NoFocus)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        self.frame = QFrame(self)
        self.frame.setObjectName("PopupFrame")
        self.frame.setProperty("popupKind", "status-menu")
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(6, 6, 6, 6)
        frame_layout.setSpacing(4)

        for option in options:
            row = _StatusOptionRow(
                option,
                is_current=str(option.get("id") or "") == current_status_id,
                parent=self.frame,
            )
            row.clicked.connect(self.optionSelected.emit)
            frame_layout.addWidget(row)

        outer_layout.addWidget(self.frame)
        PopupHelpers.apply_popup_style(self.frame)


class StatusWidget(QWidget):
    """Status menu and status change of one card item, for every module that has a status change.

    MainStatusWidget (the card's status rail) drives it; this widget itself stays hidden.
    """

    # module name -> {key: hook(item_id, item_payload)}, run after a status change
    # was saved. Modules register them (ui/modules_registry.py); this widget package never
    # imports modules/. Registering the same key again replaces the hook.
    _status_change_hooks: dict[str, dict] = {}

    # A status change runs in the background and the card shows it inline. Only a change that is still
    # running after this long gets a dialog of its own.
    SAVING_DIALOG_DELAY_MS = 1000

    status_change_finished = pyqtSignal(bool)

    @classmethod
    def register_status_change_hook(cls, module_names, key: str, hook) -> None:
        for name in module_names:
            cls._status_change_hooks.setdefault(name, {})[key] = hook

    def __init__(self, item_data, module_name: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.setObjectName("LegacyStatusWidget")
        self._item_data = dict(item_data or {}) if isinstance(item_data, dict) else dict(item_data or {})
        self._module_name = str(module_name or "").strip().lower()
        self._lang = LanguageManager()
        self._is_updating = False
        self._previous_status: Optional[StatusInfo] = None
        self._selected_option: dict = {}
        self._saving_dialog: Optional[_StatusSavingDialog] = None
        self._saving_timer = QTimer(self)
        self._saving_timer.setSingleShot(True)
        self._saving_timer.timeout.connect(self._show_saving_dialog)
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.timeout.connect(self._perform_scheduled_card_refresh)
        self._pending_refresh_payload: Optional[dict] = None
        self._status_popup: Optional[_StatusOptionsPopup] = None

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
        return bool(item_id and APIModuleActions.can_update_status(self._module_name))

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

    def _show_status_menu(self, anchor_widget=None) -> None:
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
        if self._status_popup is not None and self._status_popup.isVisible():
            self._close_status_popup()
            return

        popup_anchor = anchor_widget or self.status_label

        popup = _StatusOptionsPopup(status_options, current_status_id, self.window())
        popup.optionSelected.connect(self._handle_status_option_selected)
        popup.destroyed.connect(lambda _obj=None: setattr(self, "_status_popup", None))
        PopupHelpers.position_popup(popup, popup_anchor, placement="below_left")
        popup.show()
        popup.raise_()
        self._status_popup = popup

    def _close_status_popup(self) -> None:
        if self._status_popup is None:
            return
        self._status_popup.close()
        self._status_popup = None

    def _handle_status_option_selected(self, selected_option: dict) -> None:
        self._close_status_popup()
        new_status_id = str(selected_option.get("id") or "").strip()
        current_status_id = DataDisplayExtractors.extract_status(self._item_data).id
        if not new_status_id or new_status_id == current_status_id:
            return

        self._update_status(selected_option)

    def _update_status(self, selected_option: dict) -> None:
        item_id = str(self._item_data.get("id") or "").strip()
        new_status_id = str(selected_option.get("id") or "").strip()
        if not item_id or not new_status_id or self._is_updating:
            return

        self._previous_status = DataDisplayExtractors.extract_status(self._item_data)
        self._selected_option = dict(selected_option)
        self._is_updating = True
        self._apply_status_info(self._previous_status, loading=True)

        worker = FunctionWorker(_change_status, self._module_name, item_id, new_status_id)
        worker.finished.connect(self._on_status_change_done)
        worker.error.connect(self._on_status_change_error)
        self._saving_timer.start(self.SAVING_DIALOG_DELAY_MS)
        start_worker(worker)

    def _show_saving_dialog(self) -> None:
        if not self._is_updating or self._saving_dialog is not None:
            return
        dialog = _StatusSavingDialog(self._lang.translate(TranslationKeys.API_REQUEST_RUNNING), self)
        window = self.window()
        if window is not None and window is not self:
            dialog.adjustSize()
            dialog.move(window.geometry().center() - dialog.rect().center())
        self._saving_dialog = dialog
        dialog.show()

    def _finish_saving(self) -> None:
        self._saving_timer.stop()
        dialog, self._saving_dialog = self._saving_dialog, None
        if dialog is not None:
            dialog.hide()
            dialog.deleteLater()
        self._is_updating = False

    def _on_status_change_error(self, _message: str = "") -> None:
        """The worker failed outright; the change itself logged its own failure."""
        self._on_status_change_done({"updated": None, "refreshed": None})

    def _on_status_change_done(self, result: dict) -> None:
        self._finish_saving()
        updated_item = result.get("updated") if isinstance(result, dict) else None
        if not isinstance(updated_item, dict):
            self._apply_status_info(self._previous_status or DataDisplayExtractors.extract_status(self._item_data))
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.STATUS_WIDGET_UPDATE_FAILED),
            )
            self.status_change_finished.emit(False)
            return

        # A task section shows more than the status, so its card was read again; any other module's
        # card takes what the change returned.
        refreshed_item = result.get("refreshed")
        if not isinstance(refreshed_item, dict):
            refreshed_item = dict(self._item_data)
            status_payload = updated_item.get("status") if isinstance(updated_item.get("status"), dict) else None
            if not status_payload:
                status_payload = self._status_payload_from_option(self._selected_option)
            refreshed_item["status"] = status_payload
            if updated_item.get("updatedAt") is not None:
                refreshed_item["updatedAt"] = updated_item.get("updatedAt")

        self._item_data = dict(refreshed_item)
        self._apply_status_info(DataDisplayExtractors.extract_status(self._item_data))
        self._run_status_change_hooks(refreshed_item)
        self._schedule_card_refresh(refreshed_item)
        self.status_change_finished.emit(True)

    @staticmethod
    def _status_payload_from_option(option: dict) -> dict[str, str]:
        return {
            "id": str(option.get("id") or "").strip(),
            "name": str(option.get("name") or "").strip(),
            "color": str(option.get("color") or "cccccc").strip() or "cccccc",
            "type": str(option.get("type") or "").strip().upper(),
        }

    def _run_status_change_hooks(self, item_payload: Optional[dict] = None) -> None:
        hooks = list((StatusWidget._status_change_hooks.get(self._module_name) or {}).values())
        if not hooks:
            return

        item_id = str(self._item_data.get("id") or "").strip()
        if not item_id:
            return

        for hook in hooks:
            try:
                hook(item_id, item_payload)
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module=str(self._module_name or ""),
                    event="status_widget_status_change_hook_failed",
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
        except TypeError:  # not a sip wrapper
            return widget is None

    def _replace_current_card(self, item_data: dict) -> None:
        if self._is_deleted(self):
            return
        card = self._find_parent_card()
        if self._is_deleted(card):
            return

        # Managed lists update all occurrences and recalculate grouping/order.
        update_handler = getattr(card, "_item_update_handler", None)
        if callable(update_handler):
            update_handler(item_data)
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

