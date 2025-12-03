from __future__ import annotations

from typing import Callable, List, Optional

from PyQt5.QtCore import QObject, pyqtSignal
from qgis.core import QgsFeature, QgsVectorLayer
from qgis.utils import iface

from .MapHelpers import MapHelpers

SelectionCallback = Callable[[QgsVectorLayer, List[QgsFeature]], None]


class MapSelectionController(QObject):
    """Reusable controller for single-feature map selection workflows."""

    selection_started = pyqtSignal(object)
    selection_completed = pyqtSignal(object, list)
    selection_cancelled = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._layer: Optional[QgsVectorLayer] = None
        self._callback: Optional[SelectionCallback] = None
        self._restore_pan = True
        self._selection_tool = "rectangle"

    def start_single_selection(
        self,
        layer: Optional[QgsVectorLayer],
        *,
        on_selected: SelectionCallback,
        selection_tool: str = "rectangle",
        restore_pan: bool = True,
    ) -> bool:
        """Prepare the given layer for a one-off selection and activate the map tool."""
        if not layer or not layer.isValid():
            return False
        self.cancel_selection()
        MapHelpers.ensure_layer_visible(layer)
        layer.removeSelection()

        self._layer = layer
        self._callback = on_selected
        self._restore_pan = restore_pan
        self._selection_tool = selection_tool

        layer.selectionChanged.connect(self._handle_selection_changed)
        iface.setActiveLayer(layer)
        self._activate_selection_tool(selection_tool)
        self.selection_started.emit(layer)
        return True

    def cancel_selection(self) -> None:
        """Stop listening for selections on the active layer if any."""
        if not self._layer:
            return
        try:
            self._layer.selectionChanged.disconnect(self._handle_selection_changed)
        except Exception:
            pass
        finally:
            self._layer = None
            self._callback = None
            self.selection_cancelled.emit()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _handle_selection_changed(self):
        if not self._layer:
            return
        selected = self._layer.selectedFeatures()
        if len(selected) != 1:
            return
        features = list(selected)
        try:
            self._layer.selectionChanged.disconnect(self._handle_selection_changed)
        except Exception:
            pass

        if self._restore_pan:
            try:
                iface.actionPan().trigger()
            except Exception:
                pass

        callback = self._callback
        layer = self._layer
        self._layer = None
        self._callback = None

        if callback and layer:
            callback(layer, features)
        self.selection_completed.emit(layer, features)

    def _activate_selection_tool(self, tool_name: str) -> None:
        tools = {
            "rectangle": getattr(iface, "actionSelectRectangle", None),
            "freehand": getattr(iface, "actionSelectFreehand", None),
            "polygon": getattr(iface, "actionSelectPolygon", None),
            "radius": getattr(iface, "actionSelectRadius", None),
        }
        action = tools.get(tool_name) or tools["rectangle"]
        if action:
            try:
                action().trigger()
            except Exception:
                pass
