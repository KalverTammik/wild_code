from __future__ import annotations

from qgis.PyQt.QtCore import QMetaType
from qgis.core import QgsField, QgsFields, QgsWkbTypes

from ...utils.layers.module_temp_layer_helper import ModuleTempLayerHelper
from ...constants.module_names import Module


class WorksTempLayerHelper(ModuleTempLayerHelper):
    MODULE = Module.WORKS
    EVENT_PREFIX = "works"
    DEFAULT_LAYER_NAME = "Works_Temp"
    GEOMETRY_TYPE = QgsWkbTypes.Type.Point

    @staticmethod
    def _build_fields() -> QgsFields:
        fields = QgsFields()
        integer_type = QMetaType.Type.LongLong

        fields.append(QgsField("ext_job_id", integer_type))
        fields.append(QgsField("ext_job_name", QMetaType.Type.QString))
        fields.append(QgsField("ext_job_type", integer_type))
        fields.append(QgsField("ext_job_state", integer_type))
        fields.append(QgsField("detailed", QMetaType.Type.QString))
        fields.append(QgsField("active", QMetaType.Type.Bool))
        fields.append(QgsField("begin_date", QMetaType.Type.QDateTime))
        fields.append(QgsField("end_date", QMetaType.Type.QDateTime))
        fields.append(QgsField("added_by", QMetaType.Type.QString))
        fields.append(QgsField("added_date", QMetaType.Type.QDateTime))
        fields.append(QgsField("updated_by", QMetaType.Type.QString))
        fields.append(QgsField("update_date", QMetaType.Type.QDateTime))
        return fields
