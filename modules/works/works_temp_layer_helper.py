from __future__ import annotations

from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsField, QgsFields, QgsWkbTypes

from ...utils.layers.module_temp_layer_helper import ModuleTempLayerHelper
from ...utils.url_manager import Module


class WorksTempLayerHelper(ModuleTempLayerHelper):
    MODULE = Module.WORKS
    EVENT_PREFIX = "works"
    DEFAULT_LAYER_NAME = "Works_Temp"
    GEOMETRY_TYPE = QgsWkbTypes.Point

    @staticmethod
    def _build_fields() -> QgsFields:
        fields = QgsFields()
        integer_type = QVariant.LongLong

        fields.append(QgsField("ext_job_id", integer_type))
        fields.append(QgsField("ext_job_name", QVariant.String))
        fields.append(QgsField("ext_job_type", integer_type))
        fields.append(QgsField("ext_job_state", integer_type))
        fields.append(QgsField("detailed", QVariant.String))
        fields.append(QgsField("active", QVariant.Bool))
        fields.append(QgsField("begin_date", QVariant.DateTime))
        fields.append(QgsField("end_date", QVariant.DateTime))
        fields.append(QgsField("added_by", QVariant.String))
        fields.append(QgsField("added_date", QVariant.DateTime))
        fields.append(QgsField("updated_by", QVariant.String))
        fields.append(QgsField("update_date", QVariant.DateTime))
        return fields
