from __future__ import annotations

from PyQt5.QtCore import QEvent, QEasingCurve, QPoint, QPropertyAnimation, QSize, Qt
from PyQt5.QtWidgets import QFrame, QPushButton, QVBoxLayout, QWidget
from qgis.utils import iface

from ..constants.module_icons import IconNames
from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys
from ..Logs.python_fail_logger import PythonFailLogger
from ..module_manager import ModuleManager
from .moduleSwitchHelper import ModuleSwitchHelper
from ..utils.url_manager import Module
from .MapTools.module_identify_tool import ModuleIdentifyToolController
from .map_canvas_glass_style import MapCanvasGlassStyle
from ..utils.messagesHelper import ModernMessageDialog
from ..widgets.theme_manager import ThemeManager


class MapCanvasGlassActionBar(QWidget):
    """Small fixed-position input action over the QGIS map canvas."""

    _active_instance = None

    TARGET_MARGIN = QPoint(18, 18)
    SEARCH_BAR_SIZE = (300, 46)
    BELOW_SEARCH_GAP = 6
    START_OFFSET = QPoint(18, -88)
    SIZE = (54, 88)

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
        self._position_at_start()
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
            (
                self._lang.translate(TranslationKeys.WORKS_CREATE_ON_MAP_BUTTON),
                self._start_new_work,
                IconNames.ICON_WORK_EMERGENCY,
            ),
            (
                self._lang.translate(TranslationKeys.MAP_IDENTIFY_BUTTON),
                self._start_identify_tool,
                IconNames.ICON_MAP_IDENTIFY,
            ),
        )

        for tooltip, handler, icon_name in actions:
            button = QPushButton("", frame)
            button.setObjectName("MapCanvasGlassActionButton")
            button.setAutoDefault(False)
            button.setDefault(False)
            button.setToolTip(tooltip)
            button.setIcon(ThemeManager.get_qicon(icon_name))
            button.setIconSize(QSize(24, 24))
            button.clicked.connect(lambda _checked=False, callback=handler: callback())
            layout.addWidget(button)

        root.addWidget(frame)

    def eventFilter(self, watched, event) -> bool:
        if watched is self._canvas and event.type() in (QEvent.Resize, QEvent.Show):
            if self.isVisible():
                self.move(self._target_pos())
            else:
                self._position_at_start()
        return super().eventFilter(watched, event)

    def _target_pos(self) -> QPoint:
        if self._canvas is not None:
            search_right = self._canvas.width() - self.TARGET_MARGIN.x()
            return QPoint(
                max(0, search_right - self.width()),
                self.TARGET_MARGIN.y() + self.SEARCH_BAR_SIZE[1] + self.BELOW_SEARCH_GAP,
            )

        screen = self.screen()
        if screen is None:
            return self.TARGET_MARGIN
        geometry = screen.availableGeometry()
        search_right = geometry.right() - self.TARGET_MARGIN.x()
        return QPoint(
            search_right - self.width(),
            geometry.top() + self.TARGET_MARGIN.y() + self.SEARCH_BAR_SIZE[1] + self.BELOW_SEARCH_GAP,
        )

    def _position_at_start(self) -> None:
        target = self._target_pos()
        self.move(target.x(), self.START_OFFSET.y())

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

    def _start_identify_tool(self) -> None:
        try:
            from ..dialog import PluginDialog

            ModuleIdentifyToolController.start_for_active_module(
                parent_window=PluginDialog.get_instance(),
                lang_manager=self._lang,
            )
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=ModuleManager().getActiveModuleName() or "map",
                event="map_canvas_action_bar_identify_failed",
            )
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.MAP_IDENTIFY_OPEN_FAILED),
                parent=self,
            )

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
    def show_for_session(cls) -> None:
        if cls._active_instance is not None:
            try:
                cls._active_instance.raise_()
                cls._active_instance.move(cls._active_instance._target_pos())
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
