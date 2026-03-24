from __future__ import annotations

import json
import re
from typing import Dict, Optional

from qgis.core import QgsMapLayer, QgsProject

from .MapTools.MapHelpers import MapHelpers


_UNSET = object()


class ProjectBaseLayerKeys:
    SECTION = "kavitro/project_base_layers"

    EVEL_ENABLED = "evel_enabled"
    WATERPIPES = "waterpipes"
    SEWERPIPES = "sewerpipes"
    PRESSURE_SEWERPIPES = "pressure_sewerpipes"
    RAINWATERPIPES = "rainwaterpipes"
    SEWER_MAPPING_ENABLED = "sewer_mapping_enabled"
    SEWER_MAPPING_FIELD = "sewer_mapping_field"
    SEWER_MAPPING_ROWS = "sewer_mapping_rows"
    SEWER_MAPPING_SEWER_IDS = "sewer_mapping_sewer_ids"
    SEWER_MAPPING_PRESSURE_IDS = "sewer_mapping_pressure_ids"
    SEWER_MAPPING_RAINWATER_IDS = "sewer_mapping_rainwater_ids"

    SEWER_KIND_SEWER = "sewer"
    SEWER_KIND_SEWER_PRESSURE = "sewer_pressure"
    SEWER_KIND_COMBINED = "combined"
    SEWER_KIND_COMBINED_PRESSURE = "combined_pressure"
    SEWER_KIND_RAINWATER = "rainwater"
    SEWER_KIND_RAINWATER_PRESSURE = "rainwater_pressure"
    SEWER_KIND_DRAINAGE = "drainage"
    SEWER_KIND_OTHER = "other"

    ORDER = (
        WATERPIPES,
        SEWERPIPES,
        PRESSURE_SEWERPIPES,
        RAINWATERPIPES,
    )

    SEWER_TYPE_ORDER = (
        SEWERPIPES,
        PRESSURE_SEWERPIPES,
        RAINWATERPIPES,
    )

    SEWER_MAPPING_ID_KEY_BY_LAYER = {
        SEWERPIPES: SEWER_MAPPING_SEWER_IDS,
        PRESSURE_SEWERPIPES: SEWER_MAPPING_PRESSURE_IDS,
        RAINWATERPIPES: SEWER_MAPPING_RAINWATER_IDS,
    }

    SEWER_MAPPING_KIND_ORDER = (
        SEWER_KIND_SEWER,
        SEWER_KIND_SEWER_PRESSURE,
        SEWER_KIND_COMBINED,
        SEWER_KIND_COMBINED_PRESSURE,
        SEWER_KIND_RAINWATER,
        SEWER_KIND_RAINWATER_PRESSURE,
        SEWER_KIND_DRAINAGE,
        SEWER_KIND_OTHER,
    )

    LEGACY_KIND_BY_LAYER = {
        SEWERPIPES: SEWER_KIND_SEWER,
        PRESSURE_SEWERPIPES: SEWER_KIND_SEWER_PRESSURE,
        RAINWATERPIPES: SEWER_KIND_RAINWATER,
    }

    DEFAULT_IDS_BY_KIND = {
        SEWER_KIND_SEWER: "10",
        SEWER_KIND_SEWER_PRESSURE: "11",
        SEWER_KIND_COMBINED: "20",
        SEWER_KIND_COMBINED_PRESSURE: "21",
        SEWER_KIND_RAINWATER: "00",
        SEWER_KIND_RAINWATER_PRESSURE: "01",
        SEWER_KIND_DRAINAGE: "60",
        SEWER_KIND_OTHER: "",
    }


class ProjectBaseLayersService:
    """Store project-scoped base-layer identifiers with legacy fallback resolution."""

    LEGACY_LAYER_ALIASES: Dict[str, tuple[str, ...]] = {
        ProjectBaseLayerKeys.WATERPIPES: (
            "veetorud",
            "TVV_veetorud",
            "waterpipes",
        ),
        ProjectBaseLayerKeys.SEWERPIPES: (
            "kanalisatsioonitorud",
            "TVV_kanalisatsioonitorud",
            "sewerpipes",
        ),
        ProjectBaseLayerKeys.PRESSURE_SEWERPIPES: (
            "survekanalisatsioonitorud",
            "pressure_sewerpipes",
            "pressure sewerpipes",
            "survetorud",
        ),
        ProjectBaseLayerKeys.RAINWATERPIPES: (
            "sademeveetorud",
            "sademevesi",
            "rainwaterpipes",
        ),
    }

    @staticmethod
    def _project() -> QgsProject:
        return QgsProject.instance()

    @staticmethod
    def _read_entry(key: str, default: str = "") -> str:
        value, _ok = ProjectBaseLayersService._project().readEntry(ProjectBaseLayerKeys.SECTION, key, default)
        return str(value or default or "").strip()

    @staticmethod
    def _write_entry(key: str, value: str) -> None:
        ProjectBaseLayersService._project().writeEntry(ProjectBaseLayerKeys.SECTION, key, str(value or "").strip())

    @staticmethod
    def _remove_entry(key: str) -> None:
        ProjectBaseLayersService._project().removeEntry(ProjectBaseLayerKeys.SECTION, key)

    def evel_enabled(self, value=_UNSET, *, clear: bool = False) -> bool:
        if clear:
            self._remove_entry(ProjectBaseLayerKeys.EVEL_ENABLED)
            return False
        if value is _UNSET:
            stored = self._read_entry(ProjectBaseLayerKeys.EVEL_ENABLED, "false").lower()
            return stored in {"1", "true", "yes", "on"}
        self._write_entry(ProjectBaseLayerKeys.EVEL_ENABLED, "true" if bool(value) else "false")
        return bool(value)

    def layer_identifier(self, key: str, value=_UNSET, *, clear: bool = False) -> str:
        if clear:
            self._remove_entry(key)
            return ""
        if value is _UNSET:
            return self._read_entry(key, "")
        self._write_entry(key, str(value or "").strip())
        return str(value or "").strip()

    def get_state(self) -> dict:
        layers = {key: self.layer_identifier(key) for key in ProjectBaseLayerKeys.ORDER}
        return {
            "evel_enabled": self.evel_enabled(),
            "layers": layers,
            "sewer_mapping": self.get_sewer_mapping_state(),
        }

    def save_state(self, *, evel_enabled: bool, layers: Dict[str, str], sewer_mapping: Optional[Dict[str, object]] = None) -> None:
        self.evel_enabled(evel_enabled)
        for key in ProjectBaseLayerKeys.ORDER:
            value = str((layers or {}).get(key) or "").strip()
            if value:
                self.layer_identifier(key, value=value)
            else:
                self.layer_identifier(key, clear=True)
        if sewer_mapping is not None:
            self.save_sewer_mapping_state(sewer_mapping)

    def clear(self) -> None:
        self.evel_enabled(clear=True)
        for key in ProjectBaseLayerKeys.ORDER:
            self.layer_identifier(key, clear=True)
        self.clear_sewer_mapping_state()

    def sewer_mapping_enabled(self, value=_UNSET, *, clear: bool = False) -> bool:
        if clear:
            self._remove_entry(ProjectBaseLayerKeys.SEWER_MAPPING_ENABLED)
            return False
        if value is _UNSET:
            stored = self._read_entry(ProjectBaseLayerKeys.SEWER_MAPPING_ENABLED, "false").lower()
            return stored in {"1", "true", "yes", "on"}
        self._write_entry(ProjectBaseLayerKeys.SEWER_MAPPING_ENABLED, "true" if bool(value) else "false")
        return bool(value)

    def sewer_mapping_field(self, value=_UNSET, *, clear: bool = False) -> str:
        if clear:
            self._remove_entry(ProjectBaseLayerKeys.SEWER_MAPPING_FIELD)
            return ""
        if value is _UNSET:
            return self._read_entry(ProjectBaseLayerKeys.SEWER_MAPPING_FIELD, "")
        self._write_entry(ProjectBaseLayerKeys.SEWER_MAPPING_FIELD, str(value or "").strip())
        return str(value or "").strip()

    def sewer_mapping_rows(self, value=_UNSET, *, clear: bool = False) -> list[dict[str, str]]:
        if clear:
            self._remove_entry(ProjectBaseLayerKeys.SEWER_MAPPING_ROWS)
            return []
        if value is _UNSET:
            raw = self._read_entry(ProjectBaseLayerKeys.SEWER_MAPPING_ROWS, "")
            if raw:
                try:
                    parsed = json.loads(raw)
                except Exception:
                    parsed = []
                normalized = self.normalize_mapping_rows(parsed)
                if normalized:
                    return normalized
            return self._legacy_rows_from_ids()

        normalized = self.normalize_mapping_rows(value)
        if normalized:
            self._write_entry(
                ProjectBaseLayerKeys.SEWER_MAPPING_ROWS,
                json.dumps(normalized, ensure_ascii=False),
            )
        else:
            self._remove_entry(ProjectBaseLayerKeys.SEWER_MAPPING_ROWS)
        return normalized

    def sewer_mapping_ids(self, layer_key: str, value=_UNSET, *, clear: bool = False) -> str:
        entry_key = ProjectBaseLayerKeys.SEWER_MAPPING_ID_KEY_BY_LAYER.get(layer_key)
        if not entry_key:
            return ""
        if clear:
            self._remove_entry(entry_key)
            return ""
        if value is _UNSET:
            return self._read_entry(entry_key, "")
        self._write_entry(entry_key, str(value or "").strip())
        return str(value or "").strip()

    def get_sewer_mapping_state(self) -> dict:
        rows = self.sewer_mapping_rows()
        ids = self.legacy_ids_from_rows(rows)
        return {
            "enabled": self.sewer_mapping_enabled(),
            "field": self.sewer_mapping_field(),
            "ids": ids,
            "rows": rows,
        }

    def save_sewer_mapping_state(self, mapping: Optional[Dict[str, object]]) -> None:
        snapshot = mapping or {}
        self.sewer_mapping_enabled(bool(snapshot.get("enabled")))
        field_name = str(snapshot.get("field") or "").strip()
        if field_name:
            self.sewer_mapping_field(field_name)
        else:
            self.sewer_mapping_field(clear=True)

        rows_snapshot = snapshot.get("rows") if isinstance(snapshot.get("rows"), list) else None
        if rows_snapshot is not None:
            self.sewer_mapping_rows(rows_snapshot)
            for key in ProjectBaseLayerKeys.SEWER_TYPE_ORDER:
                self.sewer_mapping_ids(key, clear=True)
            return

        ids_snapshot = snapshot.get("ids") if isinstance(snapshot.get("ids"), dict) else {}
        for key in ProjectBaseLayerKeys.SEWER_TYPE_ORDER:
            raw_value = str((ids_snapshot or {}).get(key) or "").strip()
            if raw_value:
                self.sewer_mapping_ids(key, value=raw_value)
            else:
                self.sewer_mapping_ids(key, clear=True)
        self.sewer_mapping_rows(self._legacy_rows_from_ids())

    def clear_sewer_mapping_state(self) -> None:
        self.sewer_mapping_enabled(clear=True)
        self.sewer_mapping_field(clear=True)
        self.sewer_mapping_rows(clear=True)
        for key in ProjectBaseLayerKeys.SEWER_TYPE_ORDER:
            self.sewer_mapping_ids(key, clear=True)

    @staticmethod
    def parse_mapping_ids(value: object) -> list[str]:
        return [token.strip() for token in re.split(r"[;,|]", str(value or "")) if token.strip()]

    @classmethod
    def detect_evel_layer_ids(cls) -> Dict[str, str]:
        detected: Dict[str, str] = {}
        snapshot = {
            "evel_enabled": True,
            "layers": {},
        }
        for key in ProjectBaseLayerKeys.ORDER:
            layer = cls.resolve_layer(key, state=snapshot, include_legacy=True)
            detected[key] = layer.id() if layer is not None else ""
        return detected

    @classmethod
    def default_evel_sewer_mapping_state(cls) -> dict:
        return {
            "enabled": True,
            "field": "",
            "ids": {
                ProjectBaseLayerKeys.SEWERPIPES: "",
                ProjectBaseLayerKeys.PRESSURE_SEWERPIPES: "",
                ProjectBaseLayerKeys.RAINWATERPIPES: "",
            },
            "rows": [],
        }

    @classmethod
    def normalize_mapping_rows(cls, rows: object) -> list[dict[str, str]]:
        normalized: list[dict[str, str]] = []
        for row in rows or []:
            if not isinstance(row, dict):
                continue
            kind = str(row.get("kind") or "").strip()
            if kind not in ProjectBaseLayerKeys.SEWER_MAPPING_KIND_ORDER:
                continue
            ids_text = str(row.get("ids") or "").strip()
            if kind == ProjectBaseLayerKeys.SEWER_KIND_OTHER:
                ids_text = ""
            normalized.append({"kind": kind, "ids": ids_text})
        return normalized

    @classmethod
    def legacy_ids_from_rows(cls, rows: object) -> dict[str, str]:
        normalized = cls.normalize_mapping_rows(rows)
        kind_to_ids = {row["kind"]: row.get("ids", "") for row in normalized}
        return {
            ProjectBaseLayerKeys.SEWERPIPES: str(
                kind_to_ids.get(ProjectBaseLayerKeys.SEWER_KIND_SEWER) or ""
            ).strip(),
            ProjectBaseLayerKeys.PRESSURE_SEWERPIPES: str(
                kind_to_ids.get(ProjectBaseLayerKeys.SEWER_KIND_SEWER_PRESSURE) or ""
            ).strip(),
            ProjectBaseLayerKeys.RAINWATERPIPES: str(
                kind_to_ids.get(ProjectBaseLayerKeys.SEWER_KIND_RAINWATER) or ""
            ).strip(),
        }

    def _legacy_rows_from_ids(self) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for layer_key, kind in ProjectBaseLayerKeys.LEGACY_KIND_BY_LAYER.items():
            raw_value = self.sewer_mapping_ids(layer_key)
            if raw_value:
                rows.append({"kind": kind, "ids": raw_value})
        return rows

    @classmethod
    def resolve_layer(
        cls,
        key: str,
        *,
        state: Optional[dict] = None,
        include_legacy: Optional[bool] = None,
    ) -> Optional[QgsMapLayer]:
        snapshot = state or cls().get_state()
        layers = snapshot.get("layers") if isinstance(snapshot, dict) else {}
        evel_enabled = bool(snapshot.get("evel_enabled")) if isinstance(snapshot, dict) else False
        use_legacy = evel_enabled if include_legacy is None else bool(include_legacy)
        identifier = str((layers or {}).get(key) or "").strip()

        layer = MapHelpers.resolve_layer(identifier)
        if layer is not None:
            return layer

        if not use_legacy:
            return None

        if key in (ProjectBaseLayerKeys.PRESSURE_SEWERPIPES, ProjectBaseLayerKeys.RAINWATERPIPES):
            sewer_identifier = str((layers or {}).get(ProjectBaseLayerKeys.SEWERPIPES) or "").strip()
            sewer_layer = MapHelpers.resolve_layer(sewer_identifier)
            if sewer_layer is not None:
                return sewer_layer

        for alias in cls.LEGACY_LAYER_ALIASES.get(key, ()):
            layer = MapHelpers.find_layer_by_name(alias)
            if layer is not None:
                return layer

        if key in (ProjectBaseLayerKeys.PRESSURE_SEWERPIPES, ProjectBaseLayerKeys.RAINWATERPIPES):
            for alias in cls.LEGACY_LAYER_ALIASES.get(ProjectBaseLayerKeys.SEWERPIPES, ()):
                layer = MapHelpers.find_layer_by_name(alias)
                if layer is not None:
                    return layer

        return None

    @classmethod
    def resolve_layer_config(
        cls,
        key: str,
        *,
        state: Optional[dict] = None,
        include_legacy: Optional[bool] = None,
    ) -> dict:
        snapshot = state or cls().get_state()
        mapping_snapshot = snapshot.get("sewer_mapping") if isinstance(snapshot, dict) else {}
        mapping_enabled = bool((mapping_snapshot or {}).get("enabled"))
        mapping_field = str((mapping_snapshot or {}).get("field") or "").strip()
        mapping_ids_raw = (mapping_snapshot or {}).get("ids") if isinstance(mapping_snapshot, dict) else {}
        mapping_rows = cls.normalize_mapping_rows((mapping_snapshot or {}).get("rows"))
        if not mapping_rows:
            mapping_rows = cls.normalize_mapping_rows(
                [
                    {
                        "kind": ProjectBaseLayerKeys.LEGACY_KIND_BY_LAYER.get(layer_key, ""),
                        "ids": (mapping_ids_raw or {}).get(layer_key, ""),
                    }
                    for layer_key in ProjectBaseLayerKeys.SEWER_TYPE_ORDER
                ]
            )

        if mapping_enabled and key in ProjectBaseLayerKeys.SEWER_TYPE_ORDER:
            base_layer = cls.resolve_layer(
                ProjectBaseLayerKeys.SEWERPIPES,
                state=snapshot,
                include_legacy=include_legacy,
            )
            row_kind = ProjectBaseLayerKeys.LEGACY_KIND_BY_LAYER.get(key, "")
            raw_ids = ""
            if row_kind:
                for row in mapping_rows:
                    if str(row.get("kind") or "").strip() == row_kind:
                        raw_ids = str(row.get("ids") or "").strip()
                        break
            if not raw_ids:
                raw_ids = str((mapping_ids_raw or {}).get(key) or "").strip()
            return {
                "layer": base_layer,
                "field": mapping_field,
                "ids": cls.parse_mapping_ids(raw_ids),
                "raw_ids": raw_ids,
                "rows": mapping_rows,
                "uses_shared_layer": True,
            }

        layer = cls.resolve_layer(key, state=snapshot, include_legacy=include_legacy)
        return {
            "layer": layer,
            "field": "",
            "ids": [],
            "raw_ids": "",
            "rows": [],
            "uses_shared_layer": False,
        }
