from __future__ import annotations

from typing import Callable, Optional

from PyQt5.QtCore import QEasingCurve, QEvent, QPoint, QPropertyAnimation, Qt
from PyQt5.QtWidgets import QWidget
from qgis.utils import iface

from ..languages.language_manager import LanguageManager


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
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        if parent is None:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
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
        if watched is self._canvas and event.type() in (QEvent.Resize, QEvent.Show):
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
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self._animation.start()

    @classmethod
    def show_for_session(cls, *, on_ready: Optional[Callable[["MapCanvasGlassOverlayBase"], None]] = None) -> None:
        if cls._active_instance is not None:
            try:
                cls._active_instance.raise_()
                cls._active_instance.move(cls._active_instance._target_pos())
                if on_ready is not None:
                    on_ready(cls._active_instance)
                return
            except Exception:
                cls._active_instance = None

        bar = cls()
        cls._active_instance = bar
        bar.destroyed.connect(lambda *_: setattr(cls, "_active_instance", None))
        if on_ready is not None:
            on_ready(bar)
        bar.show_animated()

    @classmethod
    def close_active(cls) -> None:
        if cls._active_instance is None:
            return
        try:
            cls._active_instance.close()
        except Exception:
            pass
        cls._active_instance = None
