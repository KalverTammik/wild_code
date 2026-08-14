from __future__ import annotations

import gc
import os
from dataclasses import dataclass
from typing import Optional

from PyQt5.QtCore import QVariant
from qgis.core import QgsField, QgsFields, QgsProject, QgsVectorLayer, QgsWkbTypes

from ...constants.file_paths import QmlPaths
from ...constants.layer_constants import PROPERTY_TAG
from ...constants.settings_keys import SettingsService
from ...engines.LayerCreationEngine import MailablGroupFolders, get_layer_engine
from ...Logs.python_fail_logger import PythonFailLogger
from ...utils.maa_amet.Maa_amet_field_comparer import MaaAmetFieldComparer
from ...utils.url_manager import Module
from .ArchiveLayerHandler import ArchiveLayerHandler, GPKGHelpers


@dataclass(frozen=True)
class PropertyLayerBootstrapResult:
    main_layer: Optional[QgsVectorLayer] = None
    archive_layer: Optional[QgsVectorLayer] = None
    error_code: str = ""
    details: str = ""

    @property
    def ok(self) -> bool:
        return bool(
            self.main_layer is not None
            and self.main_layer.isValid()
            and self.archive_layer is not None
            and self.archive_layer.isValid()
        )


class PropertyLayerBootstrapService:
    DEFAULT_MAIN_LAYER_NAME = "Kinnistud"
    DEFAULT_ARCHIVE_LAYER_NAME = "Arhiveeritud kinnistud"
    DEFAULT_FILE_NAME = "kinnistud.gpkg"

    ERROR_INVALID_SOURCE = "invalid_source"
    ERROR_MISSING_FIELDS = "missing_fields"
    ERROR_INVALID_GEOMETRY = "invalid_geometry"
    ERROR_INVALID_CRS = "invalid_crs"
    ERROR_LAYER_NAME_IN_USE = "layer_name_in_use"
    ERROR_GPKG_LAYER_EXISTS = "gpkg_layer_exists"
    ERROR_CREATE_MAIN = "create_main"
    ERROR_LOAD_MAIN = "load_main"
    ERROR_CREATE_ARCHIVE = "create_archive"
    ERROR_SAVE_SETTINGS = "save_settings"

    _EVENT_CREATE_FAILED = "property_layer_bootstrap_create_failed"
    _EVENT_CLEANUP_FAILED = "property_layer_bootstrap_cleanup_failed"
    _EVENT_SETTINGS_RESTORE_FAILED = "property_layer_bootstrap_settings_restore_failed"
    _EVENT_STYLE_FAILED = "property_layer_bootstrap_style_failed"

    @classmethod
    def create_layers(
        cls,
        source_layer: QgsVectorLayer,
        gpkg_path: str,
    ) -> PropertyLayerBootstrapResult:
        validation_result = cls._validate_source_layer(source_layer)
        if validation_result is not None:
            return validation_result

        normalized_path = cls._normalize_gpkg_path(gpkg_path)
        if not normalized_path:
            return PropertyLayerBootstrapResult(
                error_code=cls.ERROR_CREATE_MAIN,
                details="GeoPackage path is empty",
            )

        name_conflict = cls._loaded_name_conflict()
        if name_conflict:
            return PropertyLayerBootstrapResult(
                error_code=cls.ERROR_LAYER_NAME_IN_USE,
                details=name_conflict,
            )

        for layer_name in (cls.DEFAULT_MAIN_LAYER_NAME, cls.DEFAULT_ARCHIVE_LAYER_NAME):
            if GPKGHelpers.gpkg_layer_exists(normalized_path, layer_name):
                return PropertyLayerBootstrapResult(
                    error_code=cls.ERROR_GPKG_LAYER_EXISTS,
                    details=layer_name,
                )

        file_existed = os.path.exists(normalized_path)
        main_created = False
        main_layer = None
        archive_layer = None
        settings = SettingsService()
        previous_main = settings.module_main_layer_name(Module.PROPERTY.value) or ""
        previous_archive = settings.module_archive_layer_name(Module.PROPERTY.value) or ""
        error_code = cls.ERROR_CREATE_MAIN

        try:
            main_fields = cls._main_fields_for_layer(source_layer)
            main_created = GPKGHelpers.create_empty_gpkg_layer(
                gpkg_path=normalized_path,
                layer_name=cls.DEFAULT_MAIN_LAYER_NAME,
                geometry_type=source_layer.wkbType(),
                crs=source_layer.crs(),
                fields=main_fields,
                overwrite=False,
            )
            if not main_created:
                raise RuntimeError("Main GeoPackage layer writer returned an error")

            error_code = cls.ERROR_LOAD_MAIN
            engine = get_layer_engine()
            engine.ensure_mailabl_structure_exists()
            main_layer = GPKGHelpers.load_layer_from_gpkg(
                normalized_path,
                cls.DEFAULT_MAIN_LAYER_NAME,
                group_name=MailablGroupFolders.MAILABL_MAIN,
            )
            if main_layer is None or not main_layer.isValid():
                raise RuntimeError("Created main layer could not be loaded")

            main_layer.setCustomProperty(PROPERTY_TAG, "true")
            cls._apply_style(main_layer, QmlPaths.PROPERTIES_BACKGROUND)

            error_code = cls.ERROR_CREATE_ARCHIVE
            archive_layer = ArchiveLayerHandler.resolve_or_create_archive_layer(
                main_layer,
                cls.DEFAULT_ARCHIVE_LAYER_NAME,
            )
            if archive_layer is None or not archive_layer.isValid():
                raise RuntimeError("Archive GeoPackage layer could not be created or loaded")
            cls._apply_style(archive_layer, QmlPaths.PROPERTIES_ARCHIVED)

            error_code = cls.ERROR_SAVE_SETTINGS
            settings.module_main_layer_name(
                Module.PROPERTY.value,
                value=cls.DEFAULT_MAIN_LAYER_NAME,
            )
            settings.module_archive_layer_name(
                Module.PROPERTY.value,
                value=cls.DEFAULT_ARCHIVE_LAYER_NAME,
            )

            return PropertyLayerBootstrapResult(
                main_layer=main_layer,
                archive_layer=archive_layer,
            )
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.PROPERTY.value,
                event=cls._EVENT_CREATE_FAILED,
                extra={"path": normalized_path, "stage": error_code},
            )
            cls._restore_settings(settings, previous_main, previous_archive)
            project = QgsProject.instance()
            for layer in (archive_layer, main_layer):
                if layer is not None:
                    project.removeMapLayer(layer.id())
            main_layer = None
            archive_layer = None
            gc.collect()
            cls._cleanup_failed_creation(
                gpkg_path=normalized_path,
                file_existed=file_existed,
            )
            return PropertyLayerBootstrapResult(
                error_code=error_code,
                details=str(exc),
            )

    @classmethod
    def _validate_source_layer(
        cls,
        source_layer: QgsVectorLayer,
    ) -> Optional[PropertyLayerBootstrapResult]:
        if not isinstance(source_layer, QgsVectorLayer) or not source_layer.isValid():
            return PropertyLayerBootstrapResult(error_code=cls.ERROR_INVALID_SOURCE)

        required_fields, _optional_fields = MaaAmetFieldComparer.logical_fields()
        actual_fields = {
            str(field.name() or "").strip().lower()
            for field in source_layer.fields()
        }
        missing_fields = [
            field_name
            for field_name in required_fields
            if field_name.lower() not in actual_fields
        ]
        if missing_fields:
            return PropertyLayerBootstrapResult(
                error_code=cls.ERROR_MISSING_FIELDS,
                details=", ".join(missing_fields),
            )

        if source_layer.geometryType() != QgsWkbTypes.PolygonGeometry:
            return PropertyLayerBootstrapResult(error_code=cls.ERROR_INVALID_GEOMETRY)

        if not source_layer.crs().isValid():
            return PropertyLayerBootstrapResult(error_code=cls.ERROR_INVALID_CRS)

        return None

    @classmethod
    def _main_fields_for_layer(cls, source_layer: QgsVectorLayer) -> QgsFields:
        fields = QgsFields()
        for field in source_layer.fields():
            fields.append(QgsField(field))

        existing_names = {field.name().strip().lower() for field in fields}
        if "search_field" not in existing_names:
            fields.append(QgsField("search_field", QVariant.String, len=512))
        return fields

    @classmethod
    def _loaded_name_conflict(cls) -> str:
        project = QgsProject.instance()
        for layer_name in (cls.DEFAULT_MAIN_LAYER_NAME, cls.DEFAULT_ARCHIVE_LAYER_NAME):
            if project.mapLayersByName(layer_name):
                return layer_name
        return ""

    @staticmethod
    def _normalize_gpkg_path(gpkg_path: str) -> str:
        path = str(gpkg_path or "").strip()
        if not path:
            return ""
        if os.path.splitext(path)[1].lower() != ".gpkg":
            path = f"{path}.gpkg"
        return os.path.normcase(os.path.abspath(path))

    @classmethod
    def _apply_style(cls, layer: QgsVectorLayer, style_path: str) -> None:
        if get_layer_engine().apply_qml_style(layer, style_path):
            return
        PythonFailLogger.log(
            cls._EVENT_STYLE_FAILED,
            module=Module.PROPERTY.value,
            extra={"layer": layer.name(), "style": style_path},
        )

    @classmethod
    def _restore_settings(
        cls,
        settings: SettingsService,
        previous_main: str,
        previous_archive: str,
    ) -> None:
        try:
            if previous_main:
                settings.module_main_layer_name(Module.PROPERTY.value, value=previous_main)
            else:
                settings.module_main_layer_name(Module.PROPERTY.value, clear=True)
            if previous_archive:
                settings.module_archive_layer_name(Module.PROPERTY.value, value=previous_archive)
            else:
                settings.module_archive_layer_name(Module.PROPERTY.value, clear=True)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.PROPERTY.value,
                event=cls._EVENT_SETTINGS_RESTORE_FAILED,
            )

    @classmethod
    def _cleanup_failed_creation(
        cls,
        *,
        gpkg_path: str,
        file_existed: bool,
    ) -> None:
        try:
            if not file_existed:
                if os.path.exists(gpkg_path):
                    os.remove(gpkg_path)
                return

            archive_exists = GPKGHelpers.gpkg_layer_exists(
                gpkg_path,
                cls.DEFAULT_ARCHIVE_LAYER_NAME,
            )
            if archive_exists:
                GPKGHelpers.delete_layer_from_gpkg(
                    gpkg_path,
                    cls.DEFAULT_ARCHIVE_LAYER_NAME,
                )
            main_exists = GPKGHelpers.gpkg_layer_exists(
                gpkg_path,
                cls.DEFAULT_MAIN_LAYER_NAME,
            )
            if main_exists:
                GPKGHelpers.delete_layer_from_gpkg(
                    gpkg_path,
                    cls.DEFAULT_MAIN_LAYER_NAME,
                )
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.PROPERTY.value,
                event=cls._EVENT_CLEANUP_FAILED,
                extra={"path": gpkg_path},
            )
