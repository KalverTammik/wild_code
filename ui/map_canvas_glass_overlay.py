from __future__ import annotations

from typing import Callable, Optional

from qgis.PyQt.QtCore import QEasingCurve, QEvent, QPoint, QPropertyAnimation, Qt
from qgis.PyQt.QtWidgets import QWidget
from qgis.utils import iface

from ..languages.language_manager import LanguageManager
from ..Logs.python_fail_logger import PythonFailLogger


class MapCanvasGlassOverlayBase(QWidget):
    """Shared lifecycle for fixed-position "glass" overlays on the QGIS map canvas.

    Subclasses provide SIZE, START_Y, _build_ui() and _target_pos(); positioning,
    the show/hide animation and the one-instance-per-session bookkeeping live here
    so MapCanvasGlassActionBar and MapCanvasSearchBar don't each reimplement them.
    """

    _active_instance = None

    TARGET_MARGIN = QPoint(18, 18)
    SIZE: tuple[int, int] = (0, 0)
    START_Y: int = 0

    def __init__(self, *, object_name: str, parent=None) -> None:
        canvas = iface.mapCanvas() if iface is not None else None
        parent = parent or canvas
        super().__init__(parent)
        self._canvas = canvas
        self._animation = None
        self._lang = LanguageManager()

        self.setObjectName(object_name)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        if parent is None:
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setFixedSize(*self.SIZE)

    def _finish_init(self) -> None:
        """Subclasses call this last, once their own state is ready for `_build_ui`."""
        self._build_ui()
        self._position_at_start()
        if self._canvas is not None:
            self._canvas.installEventFilter(self)

    def _build_ui(self) -> None:
        raise NotImplementedError

    def _target_pos(self) -> QPoint:
        raise NotImplementedError

    def _position_at_start(self) -> None:
        target = self._target_pos()
        self.move(target.x(), self.START_Y)

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        if watched is self._canvas and event.type() in (QEvent.Type.Resize, QEvent.Type.Show):
            if self.isVisible():
                self.move(self._target_pos())
            else:
                self._position_at_start()
        return super().eventFilter(watched, event)

    def show_animated(self) -> None:
        self._position_at_start()
        self.show()
        self.raise_()

        self._animation = QPropertyAnimation(self, b"pos", self)
        self._animation.setDuration(240)
        self._animation.setStartValue(self.pos())
        self._animation.setEndValue(self._target_pos())
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._animation.start()

    @classmethod
    def show_for_session(cls, *, on_ready: Optional[Callable[["MapCanvasGlassOverlayBase"], None]] = None) -> None:
        bar = cls._active_instance
        if bar is not None:
            try:
                bar.raise_()
                bar.move(bar._target_pos())
            except RuntimeError as exc:  # C++ overlay already deleted: build a fresh one
                PythonFailLogger.log_exception(exc, module="map", event="map_overlay_reuse_failed")
                cls._active_instance = bar = None

        if bar is None:
            bar = cls()
            cls._active_instance = bar
            bar.destroyed.connect(lambda *_: setattr(cls, "_active_instance", None))
            bar.show_animated()

        if on_ready is None:
            return
        try:
            on_ready(bar)
        except Exception as exc:
            # Caller callback from a timer slot: a bug there must not drop or rebuild a working overlay.
            PythonFailLogger.log_exception(exc, module="map", event="map_overlay_on_ready_failed")

    @classmethod
    def close_active(cls) -> None:
        if cls._active_instance is None:
            return
        try:
            cls._active_instance.close()
        except RuntimeError:  # overlay already deleted
            pass
        cls._active_instance = None
