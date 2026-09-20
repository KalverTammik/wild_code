from __future__ import annotations

from typing import Callable

from PyQt5.QtCore import Qt
from qgis.gui import QgsMapTool


class SingleClickMapTool(QgsMapTool):
    """Captures one left-click on the canvas as a map point; right-click/Escape cancels."""

    def __init__(
        self,
        canvas,
        on_selected: Callable[[object], None],
        on_cancel: Callable[[], None],
        *,
        cursor: Qt.CursorShape = Qt.CrossCursor,
    ) -> None:
        super().__init__(canvas)
        self.canvas = canvas
        self._on_selected = on_selected
        self._on_cancel = on_cancel
        self.setCursor(cursor)

    def canvasReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            point = self.canvas.getCoordinateTransform().toMapCoordinates(event.pos())
            self._on_selected(point)
            return
        if event.button() == Qt.RightButton:
            self._on_cancel()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key_Escape:
            self._on_cancel()
