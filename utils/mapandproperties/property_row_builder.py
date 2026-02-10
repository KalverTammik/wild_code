from typing import Iterable, List, Dict, Any

from ...Logs.logger import warn
from ...constants.cadastral_fields import Katastriyksus


class PropertyRowBuilder:
    """Build UI-ready property rows from QgsFeature payloads."""

    @staticmethod
    def _safe_attr(feature, field_key, *, log_prefix: str) -> str:
        try:
            value = feature[field_key]
        except Exception as exc:
            warn(f"{log_prefix}: missing field '{field_key}' on feature: {exc}")
            return ""

        if value is None:
            return ""

        try:
            return str(value)
        except Exception as exc:
            warn(f"{log_prefix}: failed to stringify field '{field_key}': {exc}")
            return ""

    @staticmethod
    def row_from_feature(feature, *, log_prefix: str = "PropertyRowBuilder") -> Dict[str, Any]:
        if feature is None:
            return {
                "cadastral_id": "",
                "address": "",
                "area": "",
                "settlement": "",
                "feature": None,
            }

        return {
            "cadastral_id": PropertyRowBuilder._safe_attr(feature, Katastriyksus.tunnus, log_prefix=log_prefix),
            "address": PropertyRowBuilder._safe_attr(feature, Katastriyksus.l_aadress, log_prefix=log_prefix),
            "area": PropertyRowBuilder._safe_attr(feature, Katastriyksus.pindala, log_prefix=log_prefix),
            "settlement": PropertyRowBuilder._safe_attr(feature, Katastriyksus.ay_nimi, log_prefix=log_prefix),
            "feature": feature,
        }

    @staticmethod
    def rows_from_features(features: Iterable, *, log_prefix: str = "PropertyRowBuilder") -> List[Dict[str, Any]]:
        return [
            PropertyRowBuilder.row_from_feature(feature, log_prefix=log_prefix)
            for feature in (features or [])
        ]

    @staticmethod
    def extract_tunnused(rows: Iterable[Dict[str, Any]], *, key: str) -> List[str]:
        values: List[str] = []
        for row in rows or []:
            try:
                value = row.get(key, "")
            except Exception:
                value = ""
            if value:
                values.append(value)
        return values

    @staticmethod
    def dedupe_values(values: Iterable[str]) -> List[str]:
        seen: set[str] = set()
        unique_values: List[str] = []
        for value in values or []:
            value = str(value or "").strip()
            if not value or value in seen:
                continue
            seen.add(value)
            unique_values.append(value)
        return unique_values
