"""What the module layer services (works, as-built, projects, easements) have in common."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from qgis.core import QgsFeature, QgsMapLayer, QgsProject, QgsVectorLayer
from qgis.utils import iface

from ..MapTools.MapHelpers import MapHelpers


class ModuleLayerServiceBase:
    """Helpers shared by the module layer services.

    A service supplies `_field_map` and `coerce_value_for_field`, whose copies still differ between modules.
    """

    @staticmethod
    def _field_map(layer: Optional[QgsVectorLayer]) -> dict[str, str]:
        raise NotImplementedError

    @staticmethod
    def coerce_value_for_field(field, value):
        raise NotImplementedError

    @staticmethod
    def _configured_layers(identifier: str) -> list[QgsMapLayer]:
        cleaned = str(identifier or "").strip()
        if not cleaned:
            return []

        direct = MapHelpers.find_layer_by_id(cleaned)
        if direct is not None:
            return [direct]

        project = QgsProject.instance()
        if project is None:
            return []

        target = cleaned.lower()
        matches: list[QgsMapLayer] = []
        for layer in project.mapLayers().values():
            try:
                candidate = str(layer.name() or "").strip()
            except Exception:
                continue
            if candidate and candidate.lower() == target:
                matches.append(layer)
        return matches

    @staticmethod
    def _layer_target_label(layer: Optional[QgsMapLayer]) -> str:
        if layer is None:
            return ""
        try:
            return str(layer.name() or "").strip()
        except Exception:
            return ""

    @classmethod
    def _resolve_first_field_name(cls, layer: Optional[QgsVectorLayer], candidates: tuple[str, ...]) -> Optional[str]:
        field_map = cls._field_map(layer)
        for candidate in candidates:
            actual = field_map.get(str(candidate).lower())
            if actual:
                return actual
        return None

    @classmethod
    def _set_attr_if_present(cls, feature: QgsFeature, *, layer: QgsVectorLayer, candidates: tuple[str, ...], value) -> None:
        actual = cls._resolve_first_field_name(layer, candidates)
        if not actual:
            return
        field_index = layer.fields().indexFromName(actual)
        field = layer.fields()[field_index] if field_index >= 0 else None
        feature.setAttribute(actual, cls.coerce_value_for_field(field, value))

    @staticmethod
    def parse_backend_datetime(value) -> Optional[datetime]:
        text = str(value or "").strip()
        if not text:
            return None
        normalized = text.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except Exception:
            parsed = None
        if parsed is None:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    parsed = datetime.strptime(text, fmt)
                    break
                except Exception:
                    continue
        if parsed is None:
            return None
        if parsed.tzinfo is not None:
            try:
                parsed = parsed.astimezone().replace(tzinfo=None)
            except Exception:
                parsed = parsed.replace(tzinfo=None)
        return parsed

    @staticmethod
    def coerce_optional_int(value) -> Optional[int]:
        text = str(value or "").strip()
        if not text:
            return None
        try:
            return int(text)
        except Exception:
            return None

    @staticmethod
    def _refresh_saved_layer(layer: Optional[QgsVectorLayer]) -> None:
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return
        try:
            layer.updateExtents()
        except Exception:
            pass
        try:
            if not layer.isEditable():
                layer.reload()
        except Exception:
            pass
        try:
            layer.triggerRepaint()
        except Exception:
            pass
        try:
            if iface is not None and iface.mapCanvas() is not None:
                iface.mapCanvas().refresh()
        except Exception:
            pass
