from __future__ import annotations

import json
from typing import Optional

from PyQt5.QtCore import QByteArray
from qgis.core import QgsGeometry

from ..Logs.python_fail_logger import PythonFailLogger


class GeometryPayloadService:
    @staticmethod
    def from_qgs_geometry(
        geometry: Optional[QgsGeometry],
        *,
        module: str,
        error_event: str,
        normalize_single_multipolygon: bool = True,
    ) -> Optional[dict[str, object]]:
        if not isinstance(geometry, QgsGeometry) or geometry.isEmpty():
            return None

        try:
            geometry_text = geometry.asJson()
            if not geometry_text:
                return None
            payload = json.loads(str(geometry_text))
            if not isinstance(payload, dict):
                return None
            if normalize_single_multipolygon:
                return GeometryPayloadService.normalize_backend_payload(payload)
            return payload
        except Exception as exc:
            PythonFailLogger.log_exception(exc, module=module, event=error_event)
            return None

    @staticmethod
    def normalize_backend_payload(payload: dict[str, object]) -> dict[str, object]:
        geometry_type = str(payload.get("type") or "").strip()
        coordinates = payload.get("coordinates")
        if geometry_type == "MultiPolygon" and isinstance(coordinates, list) and len(coordinates) == 1:
            return {
                "type": "Polygon",
                "coordinates": coordinates[0],
            }
        return payload

    @staticmethod
    def with_style(
        geometry_payload: Optional[dict[str, object]],
        *,
        icon: object = None,
        color: object = None,
        icon_color: object = None,
    ) -> Optional[dict[str, object]]:
        if not isinstance(geometry_payload, dict):
            return None

        payload = dict(geometry_payload)
        if icon is not None:
            payload["icon"] = icon
        if color is not None:
            payload["color"] = color
        if icon_color is not None:
            payload["iconColor"] = icon_color
        return payload

    @staticmethod
    def geometry_only(payload: dict) -> dict:
        geometry_type = str(payload.get("type") or "").strip()
        if not geometry_type:
            return payload

        cleaned = {"type": geometry_type}
        if "coordinates" in payload:
            cleaned["coordinates"] = payload.get("coordinates")
        return cleaned

    @staticmethod
    def to_qgs_geometry(
        geometry_payload,
        *,
        module: str,
        error_event: str,
    ) -> Optional[QgsGeometry]:
        if geometry_payload is None:
            return None

        payload = geometry_payload
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except Exception:
                return None

        if not isinstance(payload, dict):
            return None

        try:
            payload_text = json.dumps(GeometryPayloadService.geometry_only(payload), ensure_ascii=False)
            geometry = QgsGeometry.fromJson(QByteArray(payload_text.encode("utf-8")))
            if not isinstance(geometry, QgsGeometry) or geometry.isEmpty():
                return None
            return geometry
        except Exception as exc:
            PythonFailLogger.log_exception(exc, module=module, event=error_event)
            return None
