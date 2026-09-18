from typing import Iterable, List, Dict, Any

from qgis.core import QgsVariantUtils

from ...Logs.logger import warn
from ...constants.cadastral_fields import Katastriyksus


class PropertyRowBuilder:
    """Build UI-ready property rows from QgsFeature payloads."""

    @staticmethod
    def read_value(value) -> str:
        """Normalize a raw attribute value to text, never the word "NULL".

        Covers the three shapes a cadastral field arrives in: Python `None`, the QGIS
        NULL sentinel (`str()` of it reads as the literal word "NULL"), and the same
        literal text carried as real data by a source file. All three mean "no value".
        """
        if value is None or QgsVariantUtils.isNull(value):
            return ""
        text = str(value).strip()
        return "" if text.upper() == "NULL" else text

    @staticmethod
    def read_field_text(obj, field_key, *, log_prefix: str = "PropertyRowBuilder") -> str:
        """Read one field of a QgsFeature (or feature-like mapping) as null-safe text."""
        try:
            value = obj[field_key]
        except Exception as exc:
            warn(f"{log_prefix}: missing field '{field_key}' on feature: {exc}")
            return ""
        return PropertyRowBuilder.read_value(value)

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
            "cadastral_id": PropertyRowBuilder.read_field_text(feature, Katastriyksus.tunnus, log_prefix=log_prefix),
            "address": PropertyRowBuilder.read_field_text(feature, Katastriyksus.l_aadress, log_prefix=log_prefix),
            "area": PropertyRowBuilder.read_field_text(feature, Katastriyksus.pindala, log_prefix=log_prefix),
            "settlement": PropertyRowBuilder.read_field_text(feature, Katastriyksus.ay_nimi, log_prefix=log_prefix),
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
