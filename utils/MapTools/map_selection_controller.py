from __future__ import annotations

from time import perf_counter
from typing import Callable, List, Optional

from qgis.PyQt.QtCore import QEvent, QObject, Qt, QTimer, pyqtSignal
from qgis.core import QgsFeature, QgsFeatureRequest, QgsVectorLayer
from qgis.utils import iface

from .MapHelpers import MapHelpers
from ...Logs.python_fail_logger import PythonFailLogger

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
        self._lightweight_fetch = False
        self._fetch_geometry = True
        self._fetch_field_names: Optional[list[str]] = None
        self._on_abandoned: Optional[Callable[[], None]] = None
        self._canvas = None
        self._selection_map_tool = None

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
        lightweight_fetch: bool = False,
        fetch_geometry: bool = True,
        fetch_field_names: Optional[list[str]] = None,
        on_abandoned: Optional[Callable[[], None]] = None,
    ) -> bool:
        """Prepare the given layer for a one-off selection and activate the map tool.

        Completes once the selection meets the requested size constraints. Escape, a right-click or another
        map tool ends a selection that is still waiting; `on_abandoned` is then called, so the caller can
        restore the window it minimised.
        """
        if not layer or not layer.isValid():
            return False
        self.cancel_selection()
        MapHelpers.ensure_layer_visible(layer)

        if clear_filter:
            try:
                # Clear any subset string (layer filter / definition query) so selections behave as expected.
                if layer.subsetString():
                    layer.setSubsetString("")
                    try:
                        layer.triggerRepaint()
                    except Exception as exc:
                        PythonFailLogger.log_exception(
                            exc,
                            module="map",
                            event="map_selection_repaint_failed",
                        )
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="map",
                    event="map_selection_clear_filter_failed",
                )

        self._baseline_selection_ids = set(layer.selectedFeatureIds() or []) if keep_existing_selection else set()
        if not keep_existing_selection:
            layer.removeSelection()

        self._layer = layer
        self._callback = on_selected
        self._restore_pan = restore_pan
        self._selection_tool = selection_tool
        self._min_selected = max(1, int(min_selected))
        self._max_selected = max_selected
        self._lightweight_fetch = bool(lightweight_fetch)
        self._fetch_geometry = bool(fetch_geometry)
        normalized_fields = [str(name).strip() for name in (fetch_field_names or []) if str(name).strip()]
        self._fetch_field_names = normalized_fields or None

        layer.selectionChanged.connect(self._handle_selection_changed)
        iface.setActiveLayer(layer)
        self._activate_selection_tool(selection_tool)
        self._on_abandoned = on_abandoned
        self._watch_for_abandon()
        self.selection_started.emit(layer)
        return True

    def _watch_for_abandon(self) -> None:
        canvas = iface.mapCanvas() if iface is not None else None
        if canvas is None:
            return
        self._canvas = canvas
        self._selection_map_tool = canvas.mapTool()
        canvas.mapToolSet.connect(self._on_map_tool_set)
        canvas.installEventFilter(self)
        canvas.viewport().installEventFilter(self)

    def _stop_watching(self) -> None:
        canvas, self._canvas = self._canvas, None
        self._selection_map_tool = None
        if canvas is None:
            return
        try:
            canvas.mapToolSet.disconnect(self._on_map_tool_set)
        except (TypeError, RuntimeError):  # not connected, or the canvas is gone
            pass
        try:
            canvas.removeEventFilter(self)
            canvas.viewport().removeEventFilter(self)
        except RuntimeError:  # the canvas is gone
            pass

    def _on_map_tool_set(self, new_tool, _old_tool=None) -> None:
        if self._layer is not None and new_tool is not self._selection_map_tool:
            self._abandon(restore_pan=False)  # the user chose that tool; leave it active

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        if self._layer is not None:
            kind = event.type()
            if kind == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Escape:
                self._abandon(restore_pan=True)
            elif kind == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.RightButton:
                self._abandon(restore_pan=True)
        return False

    def _abandon(self, *, restore_pan: bool) -> None:
        callback = self._on_abandoned
        PythonFailLogger.log("map_selection_abandoned", module="map")
        self.cancel_selection()
        if restore_pan and self._restore_pan:
            try:
                iface.actionPan().trigger()
            except (AttributeError, RuntimeError):  # no pan action, or it was deleted
                pass
        if callable(callback):
            try:
                callback()
            except Exception as exc:  # Qt event callback: nothing may escape
                PythonFailLogger.log_exception(exc, module="map", event="map_selection_abandon_callback_failed")

    def cancel_selection(self) -> None:
        """Stop listening for selections on the active layer if any."""
        self._stop_watching()
        self._on_abandoned = None
        try:
            if self._debounce_timer is not None:
                self._debounce_timer.stop()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="map",
                event="map_selection_stop_timer_failed",
            )
        self._debounce_timer = None

        if not self._layer:
            return
        try:
            self._layer.selectionChanged.disconnect(self._handle_selection_changed)
        except (TypeError, RuntimeError) as exc:
            PythonFailLogger.log_exception(
                exc,
                module="map",
                event="map_selection_disconnect_failed",
            )
        finally:
            self._layer = None
            self._callback = None
            self._baseline_selection_ids = set()
            self._lightweight_fetch = False
            self._fetch_geometry = True
            self._fetch_field_names = None
            self.selection_cancelled.emit()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _handle_selection_changed(self):
        """Debounced handler.

        QGIS can emit multiple selectionChanged signals during a single user selection
        gesture (e.g., rectangle selection), causing us to capture only the first
        partial selection. Debounce and read selected IDs once stable.
        """

        if not self._layer:
            return

        if self._debounce_timer is None:
            self._debounce_timer = QTimer(self)
            self._debounce_timer.setSingleShot(True)
            self._debounce_timer.timeout.connect(self._finalize_selection_if_valid)

        try:
            self._debounce_timer.stop()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="map",
                event="map_selection_stop_timer_failed",
            )

        self._debounce_timer.start(int(self._debounce_ms))

    def _finalize_selection_if_valid(self) -> None:
        layer = self._layer
        if not layer:
            return

        selected_ids = list(layer.selectedFeatureIds() or [])
        baseline_ids = self._baseline_selection_ids
        filtered_ids = [fid for fid in selected_ids if fid not in baseline_ids]
        count = len(filtered_ids)
        if count < (self._min_selected or 1):
            return
        if self._max_selected is not None and count > self._max_selected:
            return

        # Done: the pan tool set below is not an abandoned selection.
        self._stop_watching()
        self._on_abandoned = None
        started = perf_counter()
        features = self._fetch_selected_features(layer, filtered_ids)
        elapsed_ms = int((perf_counter() - started) * 1000)
        if self._lightweight_fetch:
            PythonFailLogger.log(
                "map_selection_features_fetched",
                module="map",
                extra={
                    "count": len(features),
                    "ms": elapsed_ms,
                    "with_geometry": bool(self._fetch_geometry),
                },
            )

        try:
            layer.selectionChanged.disconnect(self._handle_selection_changed)
        except (TypeError, RuntimeError) as exc:
            PythonFailLogger.log_exception(
                exc,
                module="map",
                event="map_selection_disconnect_failed",
            )

        if self._restore_pan:
            try:
                iface.actionPan().trigger()
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="map",
                    event="map_selection_restore_pan_failed",
                )

        callback = self._callback
        self._layer = None
        self._callback = None
        self._baseline_selection_ids = set()
        self._lightweight_fetch = False
        self._fetch_geometry = True
        self._fetch_field_names = None

        if callback and layer:
            callback(layer, features)
        self.selection_completed.emit(layer, features)

    def _fetch_selected_features(self, layer: QgsVectorLayer, feature_ids: list[int]) -> List[QgsFeature]:
        if not feature_ids:
            return []

        if not self._lightweight_fetch:
            selected = list(layer.selectedFeatures() or [])
            allowed_ids = set(feature_ids)
            return [f for f in selected if f.id() in allowed_ids]

        request = QgsFeatureRequest()
        request.setFilterFids(feature_ids)

        if not self._fetch_geometry:
            request.setFlags(QgsFeatureRequest.Flag.NoGeometry)

        if self._fetch_field_names:
            idxs = []
            for field_name in self._fetch_field_names:
                try:
                    idx = layer.fields().lookupField(field_name)
                except Exception as exc:
                    PythonFailLogger.log_exception(
                        exc,
                        module="map",
                        event="map_selection_lookup_field_failed",
                        extra={"field": field_name},
                    )
                    idx = -1
                if idx >= 0:
                    idxs.append(idx)
            if idxs:
                request.setSubsetOfAttributes(idxs)

        try:
            return list(layer.getFeatures(request))
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="map",
                event="map_selection_fetch_features_failed",
            )
            return []

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
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="map",
                    event="map_selection_trigger_tool_failed",
                )
