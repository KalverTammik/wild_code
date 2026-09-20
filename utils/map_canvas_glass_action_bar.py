from __future__ import annotations

from PyQt5.QtCore import QPoint, QSize
from PyQt5.QtWidgets import QFrame, QPushButton, QVBoxLayout

from ..constants.module_icons import IconNames
from ..languages.translation_keys import TranslationKeys
from ..Logs.python_fail_logger import PythonFailLogger
from ..module_manager import ModuleManager
from .moduleSwitchHelper import ModuleSwitchHelper
from ..utils.url_manager import Module
from .MapTools.module_identify_tool import ModuleIdentifyToolController
from .map_canvas_glass_overlay import MapCanvasGlassOverlayBase
from .map_canvas_glass_style import MapCanvasGlassStyle
from .map_canvas_search_bar import MapCanvasSearchBar
from ..utils.messagesHelper import ModernMessageDialog
from ..widgets.theme_manager import ThemeManager


class MapCanvasGlassActionBar(MapCanvasGlassOverlayBase):
    """Small fixed-position action bar over the QGIS map canvas."""

    SIZE = (54, 121)
    START_Y = -118
    BELOW_SEARCH_GAP = 6

    def __init__(self, *, parent=None) -> None:
        super().__init__(object_name="MapCanvasGlassActionBar", parent=parent)
        self._finish_init()

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
            (
                self._lang.translate(TranslationKeys.WORKS_PENDING_GIS_ACTION),
                self._start_pending_gis_review,
                IconNames.ICON_WORKS_PENDING,
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
            button.clicked.connect(lambda _checked=False, callback=handler, source=button: callback(source))
            layout.addWidget(button)

        root.addWidget(frame)

    def _target_pos(self) -> QPoint:
        # Sits directly below MapCanvasSearchBar, so it tracks that bar's real height
        # instead of duplicating it as a separate constant that could drift out of sync.
        search_bar_height = MapCanvasSearchBar.SIZE[1]
        if self._canvas is not None:
            search_right = self._canvas.width() - self.TARGET_MARGIN.x()
            return QPoint(
                max(0, search_right - self.width()),
                self.TARGET_MARGIN.y() + search_bar_height + self.BELOW_SEARCH_GAP,
            )

        screen = self.screen()
        if screen is None:
            return self.TARGET_MARGIN
        geometry = screen.availableGeometry()
        search_right = geometry.right() - self.TARGET_MARGIN.x()
        return QPoint(
            search_right - self.width(),
            geometry.top() + self.TARGET_MARGIN.y() + search_bar_height + self.BELOW_SEARCH_GAP,
        )

    def _start_new_work(self, _source_button=None) -> None:
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

    def _start_identify_tool(self, _source_button=None) -> None:
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

    def _start_pending_gis_review(self, source_button=None) -> None:
        try:
            from ..dialog import PluginDialog

            dialog = PluginDialog.get_instance()
            ModuleSwitchHelper.switch_module(Module.WORKS.name, dialog=dialog)
            works_module = ModuleManager().getActiveModuleInstance(Module.WORKS.value)
            review_pending = getattr(works_module, "review_pending_gis_works", None)
            if callable(review_pending):
                review_pending(progress_anchor=source_button)
                return

            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.WORKS_PENDING_GIS_START_FAILED),
                parent=self,
            )
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="map_canvas_action_bar_pending_gis_failed",
            )
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.WORKS_PENDING_GIS_START_FAILED),
                parent=self,
            )
