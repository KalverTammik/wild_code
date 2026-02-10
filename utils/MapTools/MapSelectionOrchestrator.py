from __future__ import annotations

from typing import Callable, Optional

from PyQt5.QtCore import QObject

from .map_selection_controller import MapSelectionController, SelectionCallback
from .MapHelpers import MapHelpers
from ...Logs.python_fail_logger import PythonFailLogger


class MapSelectionOrchestrator(QObject):
    """Thin orchestration layer around MapSelectionController.

    Sits next to Map helpers (stateful controller vs static helpers).

    Responsibilities:
    - ensure layer is visible/active
    - optionally run pre-start UI actions
    - start the map selection tool
    """

    def __init__(self, parent: Optional[QObject] = None, *, controller: Optional[MapSelectionController] = None) -> None:
        super().__init__(parent)
        self._controller = controller or MapSelectionController()

    def cancel(self) -> None:
        try:
            self._controller.cancel_selection()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="map",
                event="map_selection_cancel_failed",
            )

    def start_selection_for_layer(
        self,
        layer,
        *,
        on_selected: SelectionCallback,
        selection_tool: str = "rectangle",
        restore_pan: bool = True,
        min_selected: int = 1,
        max_selected: Optional[int] = None,
        clear_filter: bool = False,
        before_start: Optional[Callable[[], None]] = None,
    ) -> bool:
        if not layer:
            return False

        try:
            MapHelpers.ensure_layer_visible(layer, make_active=True)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="map",
                event="map_selection_ensure_visible_failed",
            )

        if before_start is not None:
            try:
                before_start()
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="map",
                    event="map_selection_before_start_failed",
                )

        try:
            return bool(
                self._controller.start_selection(
                    layer,
                    on_selected=on_selected,
                    selection_tool=selection_tool,
                    restore_pan=restore_pan,
                    min_selected=min_selected,
                    max_selected=max_selected,
                    clear_filter=clear_filter,
                )
            )
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="map",
                event="map_selection_start_failed",
            )
            return False

    def start_selection_for_layer_tag(
        self,
        layer_tag: str,
        *,
        on_selected: SelectionCallback,
        selection_tool: str = "rectangle",
        restore_pan: bool = True,
        min_selected: int = 1,
        max_selected: Optional[int] = None,
        clear_filter: bool = False,
        before_start: Optional[Callable[[], None]] = None,
    ) -> bool:
        layer = None
        try:
            layer = MapHelpers._get_layer_by_tag(layer_tag)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="map",
                event="map_selection_get_layer_by_tag_failed",
            )
            layer = None

        return self.start_selection_for_layer(
            layer,
            on_selected=on_selected,
            selection_tool=selection_tool,
            restore_pan=restore_pan,
            min_selected=min_selected,
            max_selected=max_selected,
            clear_filter=clear_filter,
            before_start=before_start,
        )
