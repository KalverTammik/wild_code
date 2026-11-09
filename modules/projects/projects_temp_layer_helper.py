from __future__ import annotations

from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsField, QgsFields, QgsWkbTypes

from ...utils.layers.module_temp_layer_helper import ModuleTempLayerHelper
from ...utils.url_manager import Module


class ProjectsTempLayerHelper(ModuleTempLayerHelper):
    MODULE = Module.PROJECT
    EVENT_PREFIX = "projects"
    DEFAULT_LAYER_NAME = "Projects_Temp"
    GEOMETRY_TYPE = QgsWkbTypes.Polygon

    @staticmethod
    def _build_fields() -> QgsFields:
        fields = QgsFields()

        fields.append(QgsField("ext_project_id", QVariant.String))
        fields.append(QgsField("ext_system", QVariant.String))
        fields.append(QgsField("ext_project_name", QVariant.String))
        fields.append(QgsField("ext_project_number", QVariant.String))
        fields.append(QgsField("detailed", QVariant.String))
        fields.append(QgsField("active", QVariant.Bool))
        fields.append(QgsField("added_by", QVariant.String))
        fields.append(QgsField("added_date", QVariant.DateTime))
        fields.append(QgsField("updated_by", QVariant.String))
        fields.append(QgsField("update_date", QVariant.DateTime))
        return fields
