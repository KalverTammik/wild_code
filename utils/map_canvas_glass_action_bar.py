from __future__ import annotations

from PyQt5.QtCore import QEvent, QEasingCurve, QPoint, QPropertyAnimation, Qt
from PyQt5.QtWidgets import QFrame, QPushButton, QVBoxLayout, QWidget
from qgis.utils import iface

from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys
from ..Logs.python_fail_logger import PythonFailLogger
from ..module_manager import ModuleManager
from .moduleSwitchHelper import ModuleSwitchHelper
from ..utils.url_manager import Module
from .map_canvas_glass_style import MapCanvasGlassStyle
from ..utils.messagesHelper import ModernMessageDialog


class MapCanvasGlassActionBar(QWidget):
    """Small fixed-position test toolbar over the QGIS map canvas."""

    _active_instance = None

    TARGET_OFFSET = QPoint(18, 18)
    START_OFFSET = QPoint(18, -144)
    SIZE = (124, 132)

    def __init__(self, *, parent=None) -> None:
        canvas = iface.mapCanvas() if iface is not None else None
        parent = parent or canvas
        super().__init__(parent)
        self._canvas = canvas
        self._animation = None
        self._lang = LanguageManager()

        self.setObjectName("MapCanvasGlassActionBar")
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        if parent is None:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setFixedSize(*self.SIZE)

        self._build_ui()
        self._position_at(self.START_OFFSET)
        if self._canvas is not None:
            self._canvas.installEventFilter(self)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        frame = QFrame(self)
        frame.setObjectName("MapCanvasGlassActionBarFrame")
        frame.setStyleSheet(MapCanvasGlassStyle.action_bar_stylesheet())
        MapCanvasGlassStyle.apply_shadow(frame)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(7)

        actions = (
            (self._lang.translate(TranslationKeys.WORKS_CREATE_ON_MAP_BUTTON), self._start_new_work),
            ("Joonista", lambda: self._show_test_dialog("Joonista")),
            ("Kinnita", lambda: self._show_test_dialog("Kinnita")),
        )

        for label, handler in actions:
            button = QPushButton(label, frame)
            button.setObjectName("MapCanvasGlassActionButton")
            button.setAutoDefault(False)
            button.setDefault(False)
            button.clicked.connect(lambda _checked=False, callback=handler: callback())
            layout.addWidget(button)

        root.addWidget(frame)

    def eventFilter(self, watched, event) -> bool:
        if watched is self._canvas and event.type() in (QEvent.Resize, QEvent.Show):
            self._position_at(self.TARGET_OFFSET if self.isVisible() else self.START_OFFSET)
        return super().eventFilter(watched, event)

    def _position_at(self, offset: QPoint) -> None:
        if self._canvas is not None:
            self.move(offset)
            return

        screen = self.screen()
        if screen is None:
            self.move(offset)
            return
        geometry = screen.availableGeometry()
        self.move(geometry.left() + offset.x(), geometry.top() + offset.y())

    def _show_test_dialog(self, action: str) -> None:
        ModernMessageDialog.show_info(
            "Glass action bar",
            f"Testnupp: {action}",
            parent=self,
        )

    def _start_new_work(self) -> None:
        try:
            from ..dialog import PluginDialog

            dialog = PluginDialog.get_instance()
            ModuleSwitchHelper.switch_module(Module.WORKS.name, dialog=dialog)
            works_module = ModuleManager().getActiveModuleInstance(Module.WORKS.value)
            start_create = getattr(works_module, "start_create_on_map", None)
            if callable(start_create):
                start_create()
                return

            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.WORKS_CREATE_START_FAILED),
                parent=self,
            )
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="map_canvas_action_bar_works_create_failed",
            )
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.WORKS_CREATE_START_FAILED),
                parent=self,
            )

    def show_animated(self) -> None:
        self._position_at(self.START_OFFSET)
        self.show()
        self.raise_()

        self._animation = QPropertyAnimation(self, b"pos", self)
        self._animation.setDuration(240)
        self._animation.setStartValue(self.pos())
        self._animation.setEndValue(self.TARGET_OFFSET)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self._animation.start()

    @classmethod
    def show_for_session(cls) -> None:
        if cls._active_instance is not None:
            try:
                cls._active_instance.raise_()
                cls._active_instance._position_at(cls.TARGET_OFFSET)
                return
            except Exception:
                cls._active_instance = None

        bar = cls()
        cls._active_instance = bar
        bar.destroyed.connect(lambda *_: setattr(cls, "_active_instance", None))
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
