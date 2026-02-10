"""Centralized dialog/window coordination.

Provides safe, reusable window operations for dialogs and popups, including
focus/raise reliability, modal/non-modal opens, and map-selection minimize/
restore flows. Safe for primary dialogs (minimize instead of hide) and light
popups alike.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QWidget


@dataclass
class _WindowStateSnapshot:
    was_minimized: bool = False
    was_maximized: bool = False
    was_visible: bool = True
    window_state: Qt.WindowStates | None = None
    geometry: bytes | None = None


class DialogCoordinator:
    def __init__(self, iface):
        self.iface = iface
        self._map_selection_state: dict[int, _WindowStateSnapshot] = {}

    def bring_to_front(self, widget: QWidget, *, retries: int = 1, delay_ms: int = 50) -> None:
        widget = self._as_window(widget)
        if widget is None:
            return
        self._show_or_restore(widget)
        self._raise_activate_focus(widget)

        if retries > 0:
            QTimer.singleShot(
                delay_ms,
                lambda w=widget, r=retries - 1, d=delay_ms: self.bring_to_front(
                    w,
                    retries=r,
                    delay_ms=d,
                ),
            )

    def open_modal(self, dialog: QWidget, *, parent: QWidget | None = None) -> int:
        if dialog is None:
            return 0
        self.ensure_parent(dialog, parent=parent)
        try:
            if hasattr(dialog, "exec_"):
                return int(dialog.exec_())
        except Exception:
            try:
                dialog.show()
                self.bring_to_front(dialog)
            except Exception:
                return 0
            return 0
        return 0

    def open_non_modal(
        self,
        dialog: QWidget,
        *,
        parent: QWidget | None = None,
        bring_front: bool = True,
    ) -> None:
        if dialog is None:
            return
        self.ensure_parent(dialog, parent=parent)
        try:
            dialog.show()
        except Exception:
            return
        if bring_front:
            self.bring_to_front(dialog)

    def enter_map_selection_mode(
        self,
        *,
        parent: QWidget | None = None,
        dialogs: Iterable[QWidget] | None = None,
    ) -> None:
        widgets = self._collect_widgets(parent, dialogs)
        for widget in widgets:
            self._snapshot_and_minimize(widget)

    def exit_map_selection_mode(
        self,
        *,
        parent: QWidget | None = None,
        dialogs: Iterable[QWidget] | None = None,
        bring_front: bool = True,
    ) -> None:
        widgets = self._collect_widgets(parent, dialogs)
        for widget in widgets:
            self._restore_from_snapshot(widget)

        if bring_front:
            top = self._pick_focus_widget(parent, dialogs)
            if top is not None:
                self.bring_to_front(top)

    def ensure_parent(self, widget: QWidget, parent: QWidget | None = None) -> None:
        if widget is None:
            return
        if parent is None:
            parent = self._get_main_window()
        try:
            if widget.isVisible():
                return
            current_parent = widget.parent()
            if parent is not None and current_parent is None:
                widget.setParent(parent)
        except Exception:
            return

    def is_minimized(self, widget: QWidget) -> bool:
        widget = self._as_window(widget)
        if widget is None:
            return False
        try:
            return bool(widget.isMinimized())
        except Exception:
            return False

    def restore_if_minimized(self, widget: QWidget) -> None:
        widget = self._as_window(widget)
        if widget is None:
            return
        if self.is_minimized(widget):
            try:
                widget.showNormal()
            except Exception:
                return

    def _get_main_window(self) -> QWidget | None:
        try:
            if self.iface is None:
                return None
            return self.iface.mainWindow()
        except Exception:
            return None

    def _show_or_restore(self, widget: QWidget) -> None:
        try:
            if self.is_minimized(widget):
                widget.showNormal()
            else:
                widget.show()
        except Exception:
            return

    def _raise_activate_focus(self, widget: QWidget) -> None:
        try:
            widget.raise_()
        except Exception:
            pass
        try:
            widget.activateWindow()
        except Exception:
            pass
        try:
            widget.setFocus(Qt.ActiveWindowFocusReason)
        except Exception:
            pass

    def _snapshot_and_minimize(self, widget: QWidget) -> None:
        widget = self._as_window(widget)
        if widget is None:
            return
        key = int(widget.winId()) if widget.winId() else id(widget)
        try:
            self._map_selection_state[key] = _WindowStateSnapshot(
                was_minimized=self.is_minimized(widget),
                was_maximized=bool(widget.isMaximized()),
                was_visible=bool(widget.isVisible()),
                window_state=widget.windowState(),
                geometry=bytes(widget.saveGeometry()) if hasattr(widget, "saveGeometry") else None,
            )
        except Exception:
            self._map_selection_state[key] = _WindowStateSnapshot()
        try:
            widget.showMinimized()
        except Exception:
            return

    def _restore_from_snapshot(self, widget: QWidget) -> None:
        widget = self._as_window(widget)
        if widget is None:
            return
        key = int(widget.winId()) if widget.winId() else id(widget)
        snapshot = self._map_selection_state.pop(key, None)
        if snapshot is None:
            return
        if not snapshot.was_visible:
            try:
                if widget.isVisible():
                    widget.hide()
            except Exception:
                return
            return
        if snapshot.was_minimized:
            try:
                widget.showMinimized()
            except Exception:
                return
            return
        if snapshot.was_maximized:
            try:
                widget.showMaximized()
            except Exception:
                return
            return
        try:
            widget.showNormal()
            if snapshot.geometry and hasattr(widget, "restoreGeometry"):
                widget.restoreGeometry(snapshot.geometry)
        except Exception:
            return

    def _collect_widgets(
        self,
        parent: QWidget | None,
        dialogs: Iterable[QWidget] | None,
    ) -> list[QWidget]:
        widgets: list[QWidget] = []
        seen: set[int] = set()
        if parent is not None:
            parent_window = self._as_window(parent)
            if parent_window is not None:
                key = int(parent_window.winId()) if parent_window.winId() else id(parent_window)
                if key not in seen:
                    seen.add(key)
                    widgets.append(parent_window)
        if dialogs:
            for dialog in dialogs:
                dialog_window = self._as_window(dialog)
                if dialog_window is None:
                    continue
                key = int(dialog_window.winId()) if dialog_window.winId() else id(dialog_window)
                if key not in seen:
                    seen.add(key)
                    widgets.append(dialog_window)
        return widgets

    def _pick_focus_widget(
        self,
        parent: QWidget | None,
        dialogs: Iterable[QWidget] | None,
    ) -> QWidget | None:
        if dialogs:
            for dialog in dialogs:
                dialog_window = self._as_window(dialog)
                if dialog_window is not None:
                    return dialog_window
        return self._as_window(parent) if parent is not None else None

    def _as_window(self, widget: QWidget | None) -> QWidget | None:
        if widget is None:
            return None
        try:
            if widget.isWindow():
                return widget
            window = widget.window()
            return window if window is not None else None
        except Exception:
            return None


_dialog_coordinator_singleton: DialogCoordinator | None = None


def get_dialog_coordinator(iface) -> DialogCoordinator:
    global _dialog_coordinator_singleton
    if _dialog_coordinator_singleton is None:
        _dialog_coordinator_singleton = DialogCoordinator(iface)
    elif _dialog_coordinator_singleton.iface is not iface:
        _dialog_coordinator_singleton = DialogCoordinator(iface)
    return _dialog_coordinator_singleton
