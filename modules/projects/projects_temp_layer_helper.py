from __future__ import annotations

from qgis.PyQt.QtCore import QMetaType
from qgis.core import QgsField, QgsFields, QgsWkbTypes

from ...utils.layers.module_temp_layer_helper import ModuleTempLayerHelper
from ...constants.module_names import Module


class ProjectsTempLayerHelper(ModuleTempLayerHelper):
    MODULE = Module.PROJECT
    EVENT_PREFIX = "projects"
    DEFAULT_LAYER_NAME = "Projects_Temp"
    GEOMETRY_TYPE = QgsWkbTypes.Type.Polygon

    @staticmethod
    def _build_fields() -> QgsFields:
        fields = QgsFields()

        fields.append(QgsField("ext_project_id", QMetaType.Type.QString))
        fields.append(QgsField("ext_system", QMetaType.Type.QString))
        fields.append(QgsField("ext_project_name", QMetaType.Type.QString))
        fields.append(QgsField("ext_project_number", QMetaType.Type.QString))
        fields.append(QgsField("detailed", QMetaType.Type.QString))
        fields.append(QgsField("active", QMetaType.Type.Bool))
        fields.append(QgsField("added_by", QMetaType.Type.QString))
        fields.append(QgsField("added_date", QMetaType.Type.QDateTime))
        fields.append(QgsField("updated_by", QMetaType.Type.QString))
        fields.append(QgsField("update_date", QMetaType.Type.QDateTime))
        return fields
