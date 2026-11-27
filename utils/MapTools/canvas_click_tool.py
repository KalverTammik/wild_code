from __future__ import annotations

from typing import Callable

from qgis.PyQt import sip
from qgis.PyQt.QtCore import Qt, QTimer
from qgis.gui import QgsMapTool


class SingleClickMapTool(QgsMapTool):
    """Captures one left-click on the canvas as a map point.

    Right-click, Escape or choosing another map tool cancels: the caller then restores its window, which a
    plain tool change used to leave minimised with the flow waiting.
    """

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
        self._finished = False
        self.setCursor(cursor)

    def canvasReleaseEvent(self, event) -> None:  # noqa: N802
        if self._finished:
            return
        if event.button() == Qt.LeftButton:
            point = self.canvas.getCoordinateTransform().toMapCoordinates(event.pos())
            # A caller that is done removes the tool while handling the click; one that keeps it (nothing found
            # at the point, try again) gets further clicks.
            self._finished = True
            self._on_selected(point)
            if self.canvas.mapTool() is self:
                self._finished = False
            return
        if event.button() == Qt.RightButton:
            self._cancel()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key_Escape:
            self._cancel()

    def deactivate(self) -> None:
        # Another map tool was chosen before a point was: that ends the flow like Escape does. Checked on the
        # next event-loop turn, not here: QGIS also deactivates the tool while the canvas is being destroyed.
        super().deactivate()
        if not self._finished:
            QTimer.singleShot(0, self._cancel_if_replaced)

    def _cancel_if_replaced(self) -> None:
        if sip.isdeleted(self) or self._finished:
            return
        try:
            if self.canvas.mapTool() is self:
                return  # activated again meanwhile
        except RuntimeError:  # the canvas is gone, and with it the flow
            return
        self._cancel()

    def _cancel(self) -> None:
        if self._finished:
            return
        self._finished = True
        self._on_cancel()
