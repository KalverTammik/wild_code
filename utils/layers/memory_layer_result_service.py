from __future__ import annotations

from typing import Optional

from qgis.core import QgsCoordinateReferenceSystem, QgsFields, QgsLayerTreeGroup, QgsProject, QgsVectorLayer

from ...engines.LayerCreationEngine import MailablGroupFolders, get_layer_engine
from ...Logs.python_fail_logger import PythonFailLogger
from ..MapTools.MapHelpers import MapHelpers


class MemoryLayerResultService:
    """Reusable helper for disposable preview/result memory layers."""

    @staticmethod
    def _project() -> QgsProject:
        return QgsProject.instance()

    @staticmethod
    def _group(group_name: str) -> Optional[QgsLayerTreeGroup]:
        engine = get_layer_engine()
        try:
            engine.ensure_mailabl_structure_exists()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="layers",
                event="memory_layer_ensure_structure_failed",
            )

        subgroup_names = {
            MailablGroupFolders.NEW_PROPERTIES,
            MailablGroupFolders.SANDBOXING,
            MailablGroupFolders.IMPORT,
            MailablGroupFolders.SYNC,
            MailablGroupFolders.ARCHIVE,
        }

        if group_name in subgroup_names:
            main_group = engine.layer_tree_root.findGroup(MailablGroupFolders.MAILABL_MAIN)
            if main_group is None:
                main_group = engine.get_or_create_group(MailablGroupFolders.MAILABL_MAIN)
            return main_group.findGroup(group_name) or engine.get_or_create_subgroup(main_group, group_name)

        return engine.get_or_create_group(group_name)

    @classmethod
    def remove_existing(cls, layer_name: str, *, only_memory: bool = True) -> int:
        removed = 0
        project = cls._project()
        for layer in list(project.mapLayersByName(str(layer_name or "").strip())):
            try:
                if only_memory and getattr(layer, "providerType", lambda: "")() != "memory":
                    continue
                project.removeMapLayer(layer.id())
                removed += 1
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="layers",
                    event="memory_layer_remove_existing_failed",
                    extra={"layer": layer_name},
                )
        return removed

    @classmethod
    def create_empty(
        cls,
        *,
        layer_name: str,
        template_layer: Optional[QgsVectorLayer] = None,
        fields: Optional[QgsFields] = None,
        crs: Optional[QgsCoordinateReferenceSystem] = None,
        geometry_type: str = "Polygon",
        group_name: str = MailablGroupFolders.SANDBOXING,
        style_path: Optional[str] = None,
        replace_existing: bool = True,
        custom_properties: Optional[dict[str, str]] = None,
    ) -> Optional[QgsVectorLayer]:
        if replace_existing:
            cls.remove_existing(layer_name)

        engine = get_layer_engine()
        layer = engine.create_memory_layer_from_template(
            layer_name=layer_name,
            template_layer=template_layer,
            fields=fields,
            crs=crs,
            geometry_type=geometry_type,
        )
        if layer is None or not layer.isValid():
            return None
        return cls.prepare_result_layer(
            layer,
            layer_name=layer_name,
            group_name=group_name,
            style_path=style_path,
            replace_existing=False,
            custom_properties=custom_properties,
        )

    @classmethod
    def prepare_result_layer(
        cls,
        layer: Optional[QgsVectorLayer],
        *,
        layer_name: str,
        group_name: str = MailablGroupFolders.SANDBOXING,
        style_path: Optional[str] = None,
        replace_existing: bool = True,
        custom_properties: Optional[dict[str, str]] = None,
        make_visible: bool = True,
        make_active: bool = False,
    ) -> Optional[QgsVectorLayer]:
        if layer is None or not layer.isValid():
            return None

        if replace_existing:
            cls.remove_existing(layer_name)

        layer.setName(layer_name)
        for key, value in (custom_properties or {}).items():
            try:
                layer.setCustomProperty(str(key), value)
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="layers",
                    event="memory_layer_set_property_failed",
                    extra={"layer": layer_name, "property": str(key)},
                )

        project = cls._project()
        try:
            if project.mapLayer(layer.id()) is None:
                project.addMapLayer(layer, False)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="layers",
                event="memory_layer_add_project_failed",
                extra={"layer": layer_name},
            )
            return None

        group = cls._group(group_name)
        if group is not None:
            try:
                group.addLayer(layer)
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="layers",
                    event="memory_layer_add_group_failed",
                    extra={"layer": layer_name, "group": group_name},
                )

        if style_path:
            try:
                get_layer_engine().apply_qml_style(layer, style_path)
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="layers",
                    event="memory_layer_apply_style_failed",
                    extra={"layer": layer_name, "style": style_path},
                )

        if make_visible:
            try:
                MapHelpers.ensure_layer_visible(layer, make_active=make_active)
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="layers",
                    event="memory_layer_make_visible_failed",
                    extra={"layer": layer_name},
                )

        try:
            layer.triggerRepaint()
        except Exception:
            pass
        return layer

    @classmethod
    def move_layer_to_group_end(cls, layer: Optional[QgsVectorLayer], *, group_name: Optional[str] = None) -> bool:
        if layer is None or not layer.isValid():
            return False

        project = cls._project()
        root = project.layerTreeRoot()
        node = root.findLayer(layer.id())
        if node is None:
            return False

        parent = node.parent()
        if parent is None:
            return False

        if group_name:
            group = cls._group(group_name)
            if group is None or parent != group:
                return False

        try:
            clone = node.clone()
            parent.insertChildNode(len(parent.children()), clone)
            parent.removeChildNode(node)
            return True
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="layers",
                event="memory_layer_move_to_group_end_failed",
                extra={"layer": layer.name(), "group": group_name or ""},
            )
            return False

    @classmethod
    def clear_tagged_empty_layers(cls, property_tag: str) -> int:
        try:
            return int(MapHelpers.cleanup_empty_import_layers(property_tag) or 0)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="layers",
                event="memory_layer_cleanup_tagged_failed",
                extra={"tag": property_tag},
            )
            return 0
