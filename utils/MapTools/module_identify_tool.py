from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import Qt
from qgis.core import (
    QgsCoordinateTransform,
    QgsFeature,
    QgsFeatureRequest,
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    QgsRectangle,
    QgsVectorLayer,
    QgsWkbTypes,
)
from qgis.gui import QgsMapTool
from qgis.utils import iface

from ...constants.settings_keys import SettingsService
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...Logs.python_fail_logger import PythonFailLogger
from ...module_manager import ModuleManager
from ...ui.window_state.dialog_helpers import DialogHelpers
from ...utils.messagesHelper import ModernMessageDialog
from ...utils.moduleSwitchHelper import ModuleSwitchHelper
from ...utils.url_manager import Module
from .MapHelpers import MapHelpers
from .module_item_focus_service import ModuleItemFocusService


class _ModuleIdentifyClickTool(QgsMapTool):
    def __init__(self, canvas, controller: "ModuleIdentifyToolController") -> None:
        super().__init__(canvas)
        self.canvas = canvas
        self._controller = controller
        self.setCursor(Qt.WhatsThisCursor)

    def canvasReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            point = self.canvas.getCoordinateTransform().toMapCoordinates(event.pos())
            self._controller.handle_map_click(point)
            return
        if event.button() == Qt.RightButton:
            self._controller.cancel()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key_Escape:
            self._controller.cancel()


class ModuleIdentifyToolController:
    """Identify a feature from the active module layer and open it in Kavitro."""

    _active_instance: Optional["ModuleIdentifyToolController"] = None

    SUPPORTED_MODULES = {
        Module.PROPERTY.value,
        Module.PROJECT.value,
        Module.WORKS.value,
        Module.ASBUILT.value,
        Module.EASEMENT.value,
    }

    def __init__(self, *, parent_window=None, lang_manager=None) -> None:
        self._parent_window = self._safe_parent_window(parent_window)
        self._lang = lang_manager or LanguageManager()
        self._module_key = ""
        self._layer: Optional[QgsVectorLayer] = None
        self._tool: Optional[_ModuleIdentifyClickTool] = None

    @classmethod
    def start_for_active_module(cls, *, parent_window=None, lang_manager=None) -> bool:
        if cls._active_instance is not None:
            cls._active_instance.cancel(bring_front=False)

        controller = cls(parent_window=parent_window, lang_manager=lang_manager)
        if controller.start():
            cls._active_instance = controller
            return True
        return False

    def start(self) -> bool:
        module_key = self._active_module_key()
        if module_key not in self.SUPPORTED_MODULES:
            self._show_warning(
                self._lang.translate(TranslationKeys.MAP_IDENTIFY_UNSUPPORTED_MODULE).format(
                    module=self._lang.translate_module_name(module_key or "-")
                )
            )
            return False

        layer = self._resolve_module_layer(module_key)
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            self._show_warning(
                self._lang.translate(TranslationKeys.MAP_IDENTIFY_LAYER_MISSING).format(
                    module=self._lang.translate_module_name(module_key)
                )
            )
            return False

        canvas = iface.mapCanvas() if iface is not None else None
        if canvas is None:
            self._show_warning(self._lang.translate(TranslationKeys.MAP_IDENTIFY_LAYER_MISSING).format(module=module_key))
            return False

        self._module_key = module_key
        self._layer = layer

        try:
            MapHelpers.ensure_layer_visible(layer, make_active=True)
            layer.removeSelection()
        except Exception as exc:
            PythonFailLogger.log_exception(exc, module=module_key, event="module_identify_prepare_layer_failed")

        DialogHelpers.enter_map_selection_mode(iface_obj=iface, parent_window=self._parent_window)

        self._tool = _ModuleIdentifyClickTool(canvas, self)
        canvas.setMapTool(self._tool)
        return True

    def handle_map_click(self, point: QgsPointXY) -> None:
        layer = self._layer
        module_key = self._module_key
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid() or not module_key:
            self.cancel()
            return

        feature = self._feature_at_point(layer, point)
        if feature is None:
            self._show_warning(self._lang.translate(TranslationKeys.MAP_IDENTIFY_FEATURE_MISSING))
            return

        identity_field = self._identity_field(layer, module_key)
        if not identity_field:
            self._show_warning(
                self._lang.translate(TranslationKeys.MAP_IDENTIFY_ID_FIELD_MISSING).format(layer=layer.name())
            )
            return

        item_id = str(feature.attribute(identity_field) or "").strip()
        if not item_id:
            self._show_warning(
                self._lang.translate(TranslationKeys.MAP_IDENTIFY_ID_FIELD_MISSING).format(layer=layer.name())
            )
            return

        try:
            MapHelpers.select_features_by_ids(layer, [int(feature.id())], zoom=False)
        except Exception:
            pass

        self._open_item(module_key, item_id, self._feature_title(feature, identity_field))
        self.cancel(bring_front=True)

    def cancel(self, *, bring_front: bool = True) -> None:
        canvas = iface.mapCanvas() if iface is not None else None
        if canvas is not None and self._tool is not None:
            try:
                if canvas.mapTool() is self._tool:
                    canvas.unsetMapTool(self._tool)
            except Exception as exc:
                PythonFailLogger.log_exception(exc, module=self._module_key or "map", event="module_identify_unset_failed")
        try:
            if iface is not None:
                iface.actionPan().trigger()
        except Exception:
            pass
        DialogHelpers.exit_map_selection_mode(
            iface_obj=iface,
            parent_window=self._parent_window,
            bring_front=bring_front,
        )
        self._tool = None
        self._layer = None
        self._module_key = ""
        if ModuleIdentifyToolController._active_instance is self:
            ModuleIdentifyToolController._active_instance = None

    @staticmethod
    def _active_module_key() -> str:
        try:
            return str(ModuleManager().getActiveModuleName() or "").strip().lower()
        except Exception:
            return ""

    @staticmethod
    def _safe_parent_window(parent_window):
        try:
            qgis_main = iface.mainWindow() if iface is not None else None
        except Exception:
            qgis_main = None

        if parent_window is not None and parent_window is not qgis_main:
            return parent_window

        try:
            from ...dialog import PluginDialog

            dialog = PluginDialog.get_instance()
            if dialog is not qgis_main:
                return dialog
        except Exception:
            pass

        return None

    @staticmethod
    def _resolve_module_layer(module_key: str) -> Optional[QgsVectorLayer]:
        identifier = SettingsService().module_main_layer_name(module_key) or ""
        layer = MapHelpers.resolve_layer(identifier)
        return layer if isinstance(layer, QgsVectorLayer) and layer.isValid() else None

    @classmethod
    def _identity_field_candidates(cls, module_key: str) -> tuple[str, ...]:
        normalized = str(module_key or "").strip().lower()
        base = list(ModuleItemFocusService.layer_id_field_candidates(normalized))
        if normalized == Module.PROPERTY.value:
            base = ["id", "ext_property_id", "property_id", "ext_id", "external_id", "tunnus"]
        deduped: list[str] = []
        seen: set[str] = set()
        for candidate in base:
            key = str(candidate or "").strip().lower()
            if key and key not in seen:
                seen.add(key)
                deduped.append(str(candidate))
        return tuple(deduped)

    @classmethod
    def _identity_field(cls, layer: QgsVectorLayer, module_key: str) -> Optional[str]:
        try:
            field_map = {field.name().lower(): field.name() for field in layer.fields()}
        except Exception as exc:
            PythonFailLogger.log_exception(exc, module=module_key, event="module_identify_field_map_failed")
            return None
        for candidate in cls._identity_field_candidates(module_key):
            actual = field_map.get(str(candidate).lower())
            if actual:
                return actual
        return None

    @staticmethod
    def _point_in_layer_crs(point: QgsPointXY, layer: QgsVectorLayer) -> QgsPointXY:
        try:
            canvas = iface.mapCanvas() if iface is not None else None
            if canvas is None:
                return point
            source_crs = canvas.mapSettings().destinationCrs()
            target_crs = layer.crs()
            if source_crs == target_crs:
                return point
            transformer = QgsCoordinateTransform(source_crs, target_crs, QgsProject.instance())
            return transformer.transform(point)
        except Exception:
            return point

    def _feature_at_point(self, layer: QgsVectorLayer, point: QgsPointXY) -> Optional[QgsFeature]:
        canvas = iface.mapCanvas() if iface is not None else None
        if canvas is None:
            return None

        try:
            search_radius = max(canvas.mapUnitsPerPixel() * 5.0, 1.0)
        except Exception:
            search_radius = 2.0

        layer_point = self._point_in_layer_crs(point, layer)
        search_rect = QgsRectangle(
            layer_point.x() - search_radius,
            layer_point.y() - search_radius,
            layer_point.x() + search_radius,
            layer_point.y() + search_radius,
        )

        try:
            request = QgsFeatureRequest().setFilterRect(search_rect)
            point_geometry = QgsGeometry.fromPointXY(layer_point)
            closest_feature = None
            closest_distance = float("inf")

            for feature in layer.getFeatures(request):
                geometry = feature.geometry()
                if geometry is None or geometry.isEmpty():
                    continue
                if layer.geometryType() == QgsWkbTypes.PointGeometry:
                    try:
                        distance = geometry.distance(point_geometry)
                    except Exception:
                        continue
                    if distance <= search_radius and distance < closest_distance:
                        closest_feature = feature
                        closest_distance = distance
                    continue

                try:
                    if geometry.contains(point_geometry) or geometry.intersects(point_geometry):
                        return feature
                except Exception:
                    continue
            return closest_feature
        except Exception as exc:
            PythonFailLogger.log_exception(exc, module=self._module_key or "map", event="module_identify_feature_at_point_failed")
            return None

    @staticmethod
    def _feature_title(feature: QgsFeature, identity_field: str) -> str:
        for candidate in ("number", "title", "name", "Objekt", "objekt", identity_field):
            try:
                value = feature.attribute(candidate)
            except Exception:
                continue
            text = str(value or "").strip()
            if text:
                return text
        return ""

    def _open_item(self, module_key: str, item_id: str, title: str) -> None:
        try:
            from ...dialog import PluginDialog

            dialog = PluginDialog.get_instance()
            ModuleSwitchHelper.switch_module(module_key, dialog=dialog)
            module = ModuleManager().getActiveModuleInstance(module_key)
            opener = getattr(module, "open_item_from_search", None)
            if not callable(opener):
                self._show_warning(self._lang.translate(TranslationKeys.MAP_IDENTIFY_OPEN_FAILED))
                return
            opener(module_key, item_id, title or item_id)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=module_key,
                event="module_identify_open_item_failed",
                extra={"item_id": item_id},
            )
            self._show_warning(self._lang.translate(TranslationKeys.MAP_IDENTIFY_OPEN_FAILED))

    def _show_warning(self, message: str) -> None:
        ModernMessageDialog.show_warning(
            self._lang.translate(TranslationKeys.ERROR),
            message,
            parent=self._parent_window,
        )
