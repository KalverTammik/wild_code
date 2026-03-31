from __future__ import annotations

from typing import Optional

from qgis.core import QgsVectorLayer

from ...constants.settings_keys import SettingsService
from ...Logs.python_fail_logger import PythonFailLogger
from ...utils.url_manager import Module
from .MapHelpers import MapHelpers


class ModuleItemFocusService:
    @staticmethod
    def layer_id_field_candidates(module_name: Optional[str]) -> tuple[str, ...]:
        normalized = str(module_name or "").strip().lower()
        if not normalized:
            return tuple()

        candidates = [f"ext_{normalized}_id"]
        if normalized in (Module.WORKS.value, Module.ASBUILT.value):
            candidates.append("ext_job_id")
        candidates.extend(("ext_id", "external_id"))

        deduped: list[str] = []
        seen: set[str] = set()
        for candidate in candidates:
            key = str(candidate or "").strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            deduped.append(str(candidate))
        return tuple(deduped)

    @staticmethod
    def supports_layer_focus(module_name: Optional[str]) -> bool:
        normalized = str(module_name or "").strip().lower()
        return normalized in {Module.PROJECT.value, Module.WORKS.value, Module.ASBUILT.value, Module.EASEMENT.value}

    @classmethod
    def focus_item_on_map(cls, module_name: Optional[str], item_id: Optional[str]) -> bool:
        normalized = str(module_name or "").strip().lower()
        item_id_text = str(item_id or "").strip()
        if not normalized or not item_id_text or not cls.supports_layer_focus(normalized):
            return False

        layer_identifier = SettingsService().module_main_layer_name(normalized) or ""
        layer = MapHelpers.resolve_layer(layer_identifier)
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return False

        try:
            field_map = {field.name().lower(): field.name() for field in layer.fields()}
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=normalized,
                event="module_item_focus_field_map_failed",
            )
            return False

        identity_field = None
        for candidate in cls.layer_id_field_candidates(normalized):
            identity_field = field_map.get(candidate.lower())
            if identity_field:
                break
        if not identity_field:
            return False

        try:
            target_feature = None
            for feature in layer.getFeatures():
                current_id = str(feature.attribute(identity_field) or "").strip()
                if current_id == item_id_text:
                    target_feature = feature
                    break
            if target_feature is None:
                return False

            MapHelpers.ensure_layer_visible(layer, make_active=True)
            MapHelpers.select_features_by_ids(layer, [int(target_feature.id())], zoom=True)
            return True
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=normalized,
                event="module_item_focus_failed",
                extra={"item_id": item_id_text, "field": identity_field},
            )
            return False