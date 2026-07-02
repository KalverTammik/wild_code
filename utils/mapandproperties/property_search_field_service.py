from __future__ import annotations

import re
from typing import Optional

from PyQt5.QtCore import QVariant
from PyQt5.QtWidgets import QProgressDialog
from qgis.core import QgsField, QgsVectorLayer

from ...constants.cadastral_fields import Katastriyksus
from ...Logs.python_fail_logger import PythonFailLogger
from ...utils.url_manager import Module


class PropertySearchFieldService:
    """Creates and refreshes the generated cadastral search field."""

    FIELD_NAME = Katastriyksus.search_field
    SOURCE_FIELDS = tuple(Katastriyksus.search_field_items)

    @classmethod
    def has_search_field(cls, layer: Optional[QgsVectorLayer]) -> bool:
        return bool(cls.resolve_search_field_name(layer))

    @classmethod
    def resolve_search_field_name(cls, layer: Optional[QgsVectorLayer]) -> str:
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return ""
        target = cls.FIELD_NAME.lower()
        try:
            for field in layer.fields():
                name = str(field.name() or "").strip()
                if name.lower() == target:
                    return name
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.PROPERTY.value,
                event="property_search_field_resolve_failed",
            )
        return ""

    @classmethod
    def source_field_names(cls, layer: Optional[QgsVectorLayer]) -> list[str]:
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return []
        try:
            field_map = {str(field.name() or "").strip().lower(): str(field.name() or "").strip() for field in layer.fields()}
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.PROPERTY.value,
                event="property_search_source_fields_failed",
            )
            return []
        return [field_map[name.lower()] for name in cls.SOURCE_FIELDS if name.lower() in field_map]

    @classmethod
    def ensure_search_field(
        cls,
        layer: Optional[QgsVectorLayer],
        *,
        parent=None,
        progress_title: str = "",
        progress_label: str = "",
    ) -> tuple[bool, str, int]:
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return False, "Kinnistukiht puudub või ei ole korrektne.", 0

        source_fields = cls.source_field_names(layer)
        if not source_fields:
            return False, "Kihilt ei leitud välju, mille põhjal search_field väärtust koostada.", 0

        started_edit = False
        already_editable = bool(layer.isEditable())
        progress = None
        changed_count = 0

        try:
            if not already_editable:
                started_edit = bool(layer.startEditing())
                if not started_edit:
                    return False, "Kihi muutmisrežiimi ei saanud käivitada.", 0

            search_field = cls.resolve_search_field_name(layer)
            if not search_field:
                if not layer.addAttribute(QgsField(cls.FIELD_NAME, QVariant.String, len=512)):
                    if started_edit:
                        layer.rollBack()
                    return False, "search_field välja lisamine ebaõnnestus.", 0
                layer.updateFields()
                search_field = cls.resolve_search_field_name(layer)
                if not search_field:
                    if started_edit:
                        layer.rollBack()
                    return False, "search_field väli lisati, kuid seda ei õnnestunud kihilt uuesti leida.", 0

            search_idx = layer.fields().indexFromName(search_field)
            if search_idx < 0:
                if started_edit:
                    layer.rollBack()
                return False, "search_field välja indeksit ei õnnestunud määrata.", 0

            total = int(layer.featureCount() or 0)
            if parent is not None and total > 0:
                progress = QProgressDialog(progress_label or "Koostan kinnistute otsinguvälja...", "", 0, total, parent)
                progress.setWindowTitle(progress_title or "Kinnistute otsinguväli")
                progress.setCancelButton(None)
                progress.setMinimumDuration(0)
                progress.show()

            for index, feature in enumerate(layer.getFeatures(), start=1):
                value = cls._build_search_value(feature, source_fields)
                current = str(feature.attribute(search_field) or "").strip()
                if value != current:
                    if layer.changeAttributeValue(feature.id(), search_idx, value):
                        changed_count += 1

                if progress is not None and (index % 250 == 0 or index == total):
                    progress.setValue(index)

            if started_edit:
                if not layer.commitChanges():
                    errors = "; ".join(layer.commitErrors() or [])
                    layer.rollBack()
                    return False, errors or "search_field muudatuste salvestamine ebaõnnestus.", changed_count
            else:
                layer.triggerRepaint()

            return True, "", changed_count
        except Exception as exc:
            try:
                if started_edit and layer.isEditable():
                    layer.rollBack()
            except Exception as rollback_exc:
                PythonFailLogger.log_exception(
                    rollback_exc,
                    module=Module.PROPERTY.value,
                    event="property_search_field_rollback_failed",
                )
            PythonFailLogger.log_exception(
                exc,
                module=Module.PROPERTY.value,
                event="property_search_field_generate_failed",
            )
            return False, str(exc), changed_count
        finally:
            if progress is not None:
                progress.close()
                progress.deleteLater()

    @classmethod
    def _build_search_value(cls, feature, source_fields: list[str]) -> str:
        parts: list[str] = []
        seen: set[str] = set()
        for field_name in source_fields:
            try:
                raw_value = feature.attribute(field_name)
            except Exception:
                continue
            text = cls._normalize_value(raw_value)
            if not text:
                continue
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            parts.append(text)
        return " ".join(parts)

    @staticmethod
    def _normalize_value(value) -> str:
        if value is None:
            return ""
        is_null = getattr(value, "isNull", None)
        if callable(is_null):
            try:
                if is_null():
                    return ""
            except Exception:
                pass
        text = re.sub(r"\s+", " ", str(value or "").strip())
        return "" if text.upper() in ("NULL", "NONE", "NAN") else text
