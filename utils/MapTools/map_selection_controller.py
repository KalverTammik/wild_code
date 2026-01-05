from __future__ import annotations

from typing import Callable, List, Optional

from PyQt5.QtCore import QObject, QTimer, pyqtSignal
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
        self._min_selected = 1
        self._max_selected: Optional[int] = 1
        self._debounce_timer: Optional[QTimer] = None
        self._debounce_ms: int = 75
        self._baseline_selection_ids = set()

    def start_selection(
        self,
        layer: Optional[QgsVectorLayer],
        *,
        on_selected: SelectionCallback,
        selection_tool: str = "rectangle",
        restore_pan: bool = True,
        min_selected: int = 1,
        max_selected: Optional[int] = None,
        clear_filter: bool = False,
        keep_existing_selection: bool = False,
    ) -> bool:
        """Prepare the given layer for a one-off selection and activate the map tool.

        Completes once the selection meets the requested size constraints.
        """
        if not layer or not layer.isValid():
            return False
        self.cancel_selection()
        MapHelpers.ensure_layer_visible(layer)

        if clear_filter:
            try:
                # Clear any subset string (layer filter / definition query) so selections behave as expected.
                if hasattr(layer, "subsetString") and hasattr(layer, "setSubsetString"):
                    current = layer.subsetString() or ""
                    if current:
                        layer.setSubsetString("")
                        try:
                            layer.triggerRepaint()
                        except Exception:
                            pass
            except Exception:
                pass

        self._baseline_selection_ids = set(layer.selectedFeatureIds() or []) if keep_existing_selection else set()
        if not keep_existing_selection:
            layer.removeSelection()

        self._layer = layer
        self._callback = on_selected
        self._restore_pan = restore_pan
        self._selection_tool = selection_tool
        self._min_selected = max(1, int(min_selected))
        self._max_selected = max_selected

        layer.selectionChanged.connect(self._handle_selection_changed)
        iface.setActiveLayer(layer)
        self._activate_selection_tool(selection_tool)
        self.selection_started.emit(layer)
        return True

    def start_single_selection(
        self,
        layer: Optional[QgsVectorLayer],
        *,
        on_selected: SelectionCallback,
        selection_tool: str = "rectangle",
        restore_pan: bool = True,
        clear_filter: bool = False,
    ) -> bool:
        """Prepare the given layer for a one-off single-feature selection."""
        return self.start_selection(
            layer,
            on_selected=on_selected,
            selection_tool=selection_tool,
            restore_pan=restore_pan,
            min_selected=1,
            max_selected=1,
            clear_filter=clear_filter,
        )

    def cancel_selection(self) -> None:
        """Stop listening for selections on the active layer if any."""
        try:
            if self._debounce_timer is not None:
                self._debounce_timer.stop()
        except Exception:
            pass
        self._debounce_timer = None

        if not self._layer:
            return
        try:
            self._layer.selectionChanged.disconnect(self._handle_selection_changed)
        except Exception:
            pass
        finally:
            self._layer = None
            self._callback = None
            self._baseline_selection_ids = set()
            self.selection_cancelled.emit()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _handle_selection_changed(self):
        """Debounced handler.

        QGIS can emit multiple selectionChanged signals during a single user selection
        gesture (e.g., rectangle selection), causing us to capture only the first
        partial selection. Debounce and read selectedFeatures() once stable.
        """

        if not self._layer:
            return

        if self._debounce_timer is None:
            self._debounce_timer = QTimer(self)
            self._debounce_timer.setSingleShot(True)
            self._debounce_timer.timeout.connect(self._finalize_selection_if_valid)

        try:
            self._debounce_timer.stop()
        except Exception:
            pass

        self._debounce_timer.start(int(self._debounce_ms))

    def _finalize_selection_if_valid(self) -> None:
        layer = self._layer
        if not layer:
            return

        selected = layer.selectedFeatures()
        filtered = [f for f in selected if f.id() not in getattr(self, "_baseline_selection_ids", set())]
        count = len(filtered)
        if count < (self._min_selected or 1):
            return
        if self._max_selected is not None and count > self._max_selected:
            return

        features = list(filtered)

        try:
            layer.selectionChanged.disconnect(self._handle_selection_changed)
        except Exception:
            pass

        if self._restore_pan:
            try:
                iface.actionPan().trigger()
            except Exception:
                pass

        callback = self._callback
        self._layer = None
        self._callback = None
        self._baseline_selection_ids = set()

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
