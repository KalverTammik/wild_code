from __future__ import annotations

from PyQt5.QtCore import QRect
from PyQt5.QtWidgets import QWidget
from qgis.utils import iface

from .DialogCoordinator import get_dialog_coordinator


class WindowManagerMinMax:
    def __init__(self, window: QWidget) -> None:
        self.window: QWidget = window
        self.is_maximized: bool = False
        self.is_minimized: bool = False
        self.original_geometry: QRect = window.geometry()

    def _minimize_window(self) -> None:
        if not self.is_minimized:
            # Update original geometry so restore brings us back to the latest normal position
            self.original_geometry = self.window.geometry()
            coordinator = get_dialog_coordinator(iface)
            coordinator.enter_map_selection_mode(parent=self.window)
            self.is_minimized = True
            self.is_maximized = False

    def _maximize_window(self) -> None:
        if not self.is_maximized:
            self.window.showMaximized()
            self.is_maximized = True
            self.is_minimized = False

    def _restore_window(self) -> None:
        coordinator = get_dialog_coordinator(iface)
        coordinator.exit_map_selection_mode(parent=self.window)
        try:
            self.window.setGeometry(self.original_geometry)
        except Exception:
            pass
        self.is_maximized = False
        self.is_minimized = False

    def _toggle_maximize(self) -> None:
        if self.is_maximized:
            self._restore_window()
        else:
            self._maximize_window()