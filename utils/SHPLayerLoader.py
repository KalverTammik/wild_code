#!/usr/bin/env python3

import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from PyQt5.QtWidgets import QFileDialog
from qgis.core import QgsVectorLayer
from qgis.PyQt.QtCore import QCoreApplication

from ..constants.file_paths import QmlPaths
from ..constants.layer_constants import IMPORT_PROPERTY_TAG
from ..engines.LayerCreationEngine import MailablGroupFolders, get_layer_engine
from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys
from ..Logs.python_fail_logger import PythonFailLogger
from .MapTools.MapHelpers import ActiveLayersHelper
from .mapandproperties.property_layer_bootstrap_service import (
    PropertyLayerBootstrapResult,
    PropertyLayerBootstrapService,
)
from .messagesHelper import ModernMessageDialog


class SHPLoadStatus(Enum):
    SUCCESS = "success"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass(frozen=True)
class SHPLoadResult:
    status: SHPLoadStatus
    layer: Optional[QgsVectorLayer] = None
    bootstrap_created: bool = False
    error_title: str = ""
    error_message: str = ""

    @property
    def success(self) -> bool:
        return self.status == SHPLoadStatus.SUCCESS


class SHPLayerLoader:
    """Load a Shapefile into the canonical property import memory layer."""

    def __init__(self, parent_widget=None, target_group=None):
        self.parent = parent_widget
        self.target_group = target_group or MailablGroupFolders.NEW_PROPERTIES
        self.lang_manager = LanguageManager()
        self.engine = get_layer_engine()

    def load_shp_layer(self) -> SHPLoadResult:
        print("[SHPLayerLoader] Starting load_shp_layer")
        PythonFailLogger.log("shp_loader_start", module="property")

        file_path = self._get_shp_file_path()
        if not file_path:
            print("[SHPLayerLoader] No file selected (cancelled)")
            PythonFailLogger.log("shp_loader_cancelled", module="property")
            return SHPLoadResult(SHPLoadStatus.CANCELLED)

        layer_name = os.path.splitext(os.path.basename(file_path))[0]
        shp_layer = QgsVectorLayer(file_path, layer_name, "ogr")
        if not shp_layer.isValid():
            print("[SHPLayerLoader] QgsVectorLayer is not valid")
            PythonFailLogger.log(
                "shp_loader_invalid_source_layer",
                module="property",
                extra={"file": file_path},
            )
            return SHPLoadResult(
                SHPLoadStatus.FAILED,
                error_title=self.lang_manager.translate(TranslationKeys.INVALID_SHAPEFILE),
                error_message=self.lang_manager.translate(TranslationKeys.INVALID_SHAPEFILE_MESSAGE),
            )

        bootstrap_cancelled, bootstrap_path = self._choose_bootstrap_path(file_path)
        if bootstrap_cancelled:
            return SHPLoadResult(SHPLoadStatus.CANCELLED)

        print("[SHPLayerLoader] Importing shapefile to memory layer")
        memory_layer = self.engine.import_shapefile_to_memory_layer(
            shp_layer=shp_layer,
            layer_name=layer_name,
            group_name=self.target_group,
            parent_widget=self.parent,
        )
        print(f"[SHPLayerLoader] Import result layer: {memory_layer}")
        PythonFailLogger.log(
            "shp_loader_import_result",
            module="property",
            extra={"result_type": type(memory_layer).__name__},
        )

        memory_layer = self._resolve_import_result(memory_layer, layer_name)
        if memory_layer is None:
            print("[SHPLayerLoader] Import did not return a valid memory layer")
            PythonFailLogger.log(
                "shp_loader_memory_layer_missing",
                module="property",
                extra={"expected_name": f"{layer_name}_memory"},
            )
            return SHPLoadResult(
                SHPLoadStatus.FAILED,
                error_title=self.lang_manager.translate(TranslationKeys.SHAPEFILE_LOAD_FAILED),
                error_message=self.lang_manager.translate(TranslationKeys.SHAPEFILE_LOAD_FAILED_MESSAGE),
            )

        print(
            "[SHPLayerLoader] Memory layer found; setting tag and applying style. "
            f"Feature count pre-style: {memory_layer.featureCount()}"
        )
        memory_layer.setCustomProperty(IMPORT_PROPERTY_TAG, "true")
        if memory_layer.isEditable():
            memory_layer.commitChanges()
        self.engine.apply_qml_style(memory_layer, QmlPaths.MAAMET_IMPORT)

        bootstrap_result = None
        if bootstrap_path:
            bootstrap_result = PropertyLayerBootstrapService.create_layers(
                memory_layer,
                bootstrap_path,
            )
            if not bootstrap_result.ok:
                self.engine.project.removeMapLayer(memory_layer.id())
                return SHPLoadResult(
                    SHPLoadStatus.FAILED,
                    error_title=self.lang_manager.translate(
                        TranslationKeys.PROPERTY_BOOTSTRAP_FAILED_TITLE
                    ),
                    error_message=self._bootstrap_error_message(bootstrap_result),
                )

        feature_count = memory_layer.featureCount()
        print(f"[SHPLayerLoader] Final feature_count={feature_count}")
        PythonFailLogger.log(
            "shp_loader_success",
            module="property",
            extra={"layer": memory_layer.name(), "feature_count": feature_count},
        )

        if feature_count > 0:
            message = self.lang_manager.translate(
                TranslationKeys.SHAPEFILE_LOADED_WITH_DATA_MESSAGE
            ).format(name=layer_name, count=feature_count)
        else:
            message = self.lang_manager.translate(
                TranslationKeys.SHAPEFILE_LOADED_MESSAGE
            ).format(name=layer_name)

        if bootstrap_result is not None:
            message = "{}\n\n{}".format(
                message,
                self.lang_manager.translate(
                    TranslationKeys.PROPERTY_BOOTSTRAP_READY_BODY
                ).format(
                    main=bootstrap_result.main_layer.name(),
                    archive=bootstrap_result.archive_layer.name(),
                    path=bootstrap_path,
                ),
            )

        ModernMessageDialog.show_info(
            self.lang_manager.translate(TranslationKeys.SHAPEFILE_LOADED_SUCCESSFULLY),
            message,
        )
        return SHPLoadResult(
            SHPLoadStatus.SUCCESS,
            layer=memory_layer,
            bootstrap_created=bootstrap_result is not None,
        )

    def _choose_bootstrap_path(self, shp_path: str) -> tuple[bool, str]:
        if ActiveLayersHelper.resolve_main_property_layer(silent=True) is not None:
            return False, ""

        create_label = self.lang_manager.translate(TranslationKeys.PROPERTY_BOOTSTRAP_CREATE)
        continue_label = self.lang_manager.translate(
            TranslationKeys.PROPERTY_BOOTSTRAP_CONTINUE_SHP
        )
        cancel_label = self.lang_manager.translate(TranslationKeys.CANCEL_BUTTON)
        choice = ModernMessageDialog.ask_choice_modern(
            self.lang_manager.translate(TranslationKeys.PROPERTY_BOOTSTRAP_REQUIRED_TITLE),
            self.lang_manager.translate(TranslationKeys.PROPERTY_BOOTSTRAP_REQUIRED_BODY),
            buttons=[create_label, continue_label, cancel_label],
            parent=self.parent,
            default=create_label,
            cancel=cancel_label,
        )
        if choice in (None, cancel_label):
            return True, ""
        if choice == continue_label:
            return False, ""

        selected_path = self._get_bootstrap_gpkg_path(shp_path)
        if not selected_path:
            return True, ""
        if not os.path.exists(selected_path):
            return False, selected_path

        use_existing = ModernMessageDialog.ask_yes_no(
            self.lang_manager.translate(TranslationKeys.PROPERTY_BOOTSTRAP_EXISTING_GPKG_TITLE),
            self.lang_manager.translate(TranslationKeys.PROPERTY_BOOTSTRAP_EXISTING_GPKG_BODY).format(
                path=selected_path,
            ),
            yes_label=self.lang_manager.translate(TranslationKeys.PROPERTY_BOOTSTRAP_ADD_TO_GPKG),
            no_label=cancel_label,
            default=self.lang_manager.translate(TranslationKeys.PROPERTY_BOOTSTRAP_ADD_TO_GPKG),
        )
        return (False, selected_path) if use_existing else (True, "")

    def _resolve_import_result(self, memory_layer, layer_name: str):
        if isinstance(memory_layer, str):
            layers = self.engine.project.mapLayersByName(memory_layer)
            memory_layer = layers[0] if layers else None

        if memory_layer is None:
            for _ in range(3):
                QCoreApplication.processEvents()
            candidates = self.engine.project.mapLayersByName(f"{layer_name}_memory")
            if candidates:
                memory_layer = candidates[-1]

        if memory_layer is not None:
            return memory_layer

        tagged_layers = [
            layer
            for layer in self.engine.project.mapLayers().values()
            if layer.customProperty(IMPORT_PROPERTY_TAG)
        ]
        return tagged_layers[-1] if tagged_layers else None

    def _bootstrap_error_message(self, result: PropertyLayerBootstrapResult) -> str:
        if result.error_code == PropertyLayerBootstrapService.ERROR_MISSING_FIELDS:
            return self.lang_manager.translate(
                TranslationKeys.PROPERTY_BOOTSTRAP_MISSING_FIELDS_BODY
            ).format(fields=result.details)
        if result.error_code == PropertyLayerBootstrapService.ERROR_INVALID_GEOMETRY:
            return self.lang_manager.translate(
                TranslationKeys.PROPERTY_BOOTSTRAP_INVALID_GEOMETRY_BODY
            )
        if result.error_code == PropertyLayerBootstrapService.ERROR_INVALID_CRS:
            return self.lang_manager.translate(
                TranslationKeys.PROPERTY_BOOTSTRAP_INVALID_CRS_BODY
            )
        if result.error_code in (
            PropertyLayerBootstrapService.ERROR_LAYER_NAME_IN_USE,
            PropertyLayerBootstrapService.ERROR_GPKG_LAYER_EXISTS,
        ):
            return self.lang_manager.translate(
                TranslationKeys.PROPERTY_BOOTSTRAP_LAYER_EXISTS_BODY
            ).format(name=result.details)
        if result.error_code == PropertyLayerBootstrapService.ERROR_INVALID_SOURCE:
            return self.lang_manager.translate(
                TranslationKeys.PROPERTY_BOOTSTRAP_INVALID_SOURCE_BODY
            )
        stage_key = {
            PropertyLayerBootstrapService.ERROR_CREATE_MAIN:
                TranslationKeys.PROPERTY_BOOTSTRAP_STAGE_CREATE_MAIN,
            PropertyLayerBootstrapService.ERROR_LOAD_MAIN:
                TranslationKeys.PROPERTY_BOOTSTRAP_STAGE_LOAD_MAIN,
            PropertyLayerBootstrapService.ERROR_CREATE_ARCHIVE:
                TranslationKeys.PROPERTY_BOOTSTRAP_STAGE_CREATE_ARCHIVE,
            PropertyLayerBootstrapService.ERROR_SAVE_SETTINGS:
                TranslationKeys.PROPERTY_BOOTSTRAP_STAGE_SAVE_SETTINGS,
        }.get(
            result.error_code,
            TranslationKeys.PROPERTY_BOOTSTRAP_STAGE_CREATE_MAIN,
        )
        return self.lang_manager.translate(
            TranslationKeys.PROPERTY_BOOTSTRAP_CREATE_FAILED_BODY
        ).format(stage=self.lang_manager.translate(stage_key))

    def _get_shp_file_path(self) -> Optional[str]:
        file_path, _selected_filter = QFileDialog.getOpenFileName(
            self.parent,
            self.lang_manager.translate(TranslationKeys.SELECT_SHAPEFILE),
            "",
            "SHP files (*.shp);;All files (*.*)",
        )
        return file_path or None

    def _get_bootstrap_gpkg_path(self, shp_path: str) -> Optional[str]:
        default_path = os.path.join(
            os.path.dirname(os.path.abspath(shp_path)),
            PropertyLayerBootstrapService.DEFAULT_FILE_NAME,
        )
        file_path, _selected_filter = QFileDialog.getSaveFileName(
            self.parent,
            self.lang_manager.translate(TranslationKeys.PROPERTY_BOOTSTRAP_SAVE_DIALOG_TITLE),
            default_path,
            "GeoPackage (*.gpkg)",
            options=QFileDialog.DontConfirmOverwrite,
        )
        if not file_path:
            return None
        if os.path.splitext(file_path)[1].lower() != ".gpkg":
            file_path = f"{file_path}.gpkg"
        return os.path.normcase(os.path.abspath(file_path))
