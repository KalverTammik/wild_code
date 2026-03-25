from __future__ import annotations

from datetime import date, datetime
import json
from typing import Optional

from qgis.PyQt.QtCore import QVariant, QDate, QDateTime
from qgis.core import QgsCoordinateTransform, QgsFeature, QgsField, QgsGeometry, QgsMapLayer, QgsProject, QgsVectorLayer, QgsWkbTypes
from qgis.utils import iface

from ...constants.settings_keys import SettingsService
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ..Settings.setting_keys import SettingDialogPlaceholders
from ...utils.MapTools.MapHelpers import MapHelpers
from ...utils.SessionManager import SessionManager
from ...utils.url_manager import Module
from ...utils.messagesHelper import ModernMessageDialog
from ...Logs.python_fail_logger import PythonFailLogger


class EasementLayerService:
    EXT_SYSTEM_NAME = "Kavitro"
    FIELD_EXTERNAL_ID = "ext_easement_id"
    FIELD_EXTERNAL_SYSTEM = "ext_system"
    FIELD_EXTERNAL_NUMBER = "ext_easement_number"

    FIELD_ID_CANDIDATES = (FIELD_EXTERNAL_ID, "ext_job_id", "easement_id", "ext_id", "external_id")
    FIELD_NUMBER_CANDIDATES = (FIELD_EXTERNAL_NUMBER, "number", "nr")
    FIELD_TYPE_CANDIDATES = ("Liik", "liik", "type", "type_name")
    FIELD_STATUS_CANDIDATES = ("Staatus", "staatus", "status")
    FIELD_SYSTEM_CANDIDATES = (FIELD_EXTERNAL_SYSTEM, "Allikas", "allikas", "system")
    FIELD_PROPERTY_CANDIDATES = ("Katastritunnus", "katastritunnus")
    FIELD_ADDED_BY_CANDIDATES = ("Sisestaja", "sisestaja", "added_by")
    FIELD_ADDED_DATE_CANDIDATES = ("Sisestamis kpv", "sisestamis kpv", "added_date")
    FIELD_UPDATED_BY_CANDIDATES = ("Muutja", "muutja", "updated_by")
    FIELD_UPDATE_DATE_CANDIDATES = ("Muutmis kpv", "muutmis kpv", "update_date")
    FIELD_FINAL_AREA_CANDIDATES = ("Kaitsevööndi pindala", "kaitsevööndi pindala", "pindala", "Pindala_serv")
    FIELD_COMPENSATION_CANDIDATES = ("Talumistasu", "talumistasu")

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
            source = str(getattr(layer, "source", lambda: "")() or "").strip()
        except Exception:
            source = ""
        name = str(getattr(layer, "name", lambda: "")() or "").strip()
        if name and source:
            return f"{name} ({source})"
        return name or source or ""

    @classmethod
    def resolve_main_layer(cls, *, lang_manager=None, silent: bool = False) -> Optional[QgsVectorLayer]:
        lang = lang_manager or LanguageManager()
        identifier = SettingsService().module_main_layer_name(Module.EASEMENT.value) or ""
        matches = cls._configured_layers(identifier)
        if len(matches) > 1:
            if not silent:
                ModernMessageDialog.show_warning(
                    lang.translate(TranslationKeys.ERROR),
                    "Configured easement main layer is ambiguous. Please re-select the main easement layer in Settings.",
                )
            return None

        layer = matches[0] if matches else None
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            if not silent:
                ModernMessageDialog.show_warning(
                    lang.translate(TranslationKeys.ERROR),
                    lang.translate(TranslationKeys.EASEMENT_LAYER_MISSING),
                )
            return None

        try:
            if str(identifier or "").strip() != str(layer.id() or "").strip():
                SettingsService().module_main_layer_name(Module.EASEMENT.value, value=layer.id())
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.EASEMENT.value,
                event="easement_layer_setting_id_migrate_failed",
                extra={"identifier": str(identifier or "")},
            )

        if layer.geometryType() != QgsWkbTypes.PolygonGeometry:
            if not silent:
                ModernMessageDialog.show_warning(
                    lang.translate(TranslationKeys.ERROR),
                    lang.translate(TranslationKeys.EASEMENT_LAYER_INVALID_GEOMETRY),
                )
            return None

        return layer

    @staticmethod
    def _field_map(layer: Optional[QgsVectorLayer]) -> dict[str, str]:
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return {}
        try:
            return {field.name().lower(): field.name() for field in layer.fields()}
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.EASEMENT.value,
                event="easement_layer_field_map_failed",
            )
            return {}

    @classmethod
    def _resolve_first_field_name(cls, layer: Optional[QgsVectorLayer], candidates: tuple[str, ...]) -> Optional[str]:
        field_map = cls._field_map(layer)
        for candidate in candidates:
            actual = field_map.get(str(candidate).lower())
            if actual:
                return actual
        return None

    @classmethod
    def _resolve_identity_field_name(cls, layer: Optional[QgsVectorLayer]) -> Optional[str]:
        return cls._resolve_first_field_name(layer, cls.FIELD_ID_CANDIDATES)

    @classmethod
    def _resolve_number_field_name(cls, layer: Optional[QgsVectorLayer]) -> Optional[str]:
        return cls._resolve_first_field_name(layer, cls.FIELD_NUMBER_CANDIDATES)

    @classmethod
    def resolve_status_field_name(cls, layer: Optional[QgsVectorLayer]) -> Optional[str]:
        return cls._resolve_first_field_name(layer, cls.FIELD_STATUS_CANDIDATES)

    @classmethod
    def parse_status_mapping_rows(cls, value) -> list[dict[str, str]]:
        payload = value
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return []
            try:
                payload = json.loads(text)
            except Exception:
                return []

        rows_payload = payload
        if isinstance(payload, dict):
            if isinstance(payload.get("rows"), list):
                rows_payload = payload.get("rows") or []
            else:
                normalized_rows: list[dict[str, str]] = []
                for key, raw_value in payload.items():
                    status_id = str(key or "").strip()
                    if isinstance(raw_value, dict):
                        layer_status = str(
                            raw_value.get("layerStatus")
                            or raw_value.get("layerValue")
                            or raw_value.get("value")
                            or ""
                        ).strip()
                        status_name = str(raw_value.get("statusName") or raw_value.get("name") or "").strip()
                    else:
                        layer_status = str(raw_value or "").strip()
                        status_name = ""
                    if layer_status:
                        normalized_rows.append(
                            {
                                "statusId": status_id,
                                "statusName": status_name,
                                "layerStatus": layer_status,
                            }
                        )
                return normalized_rows

        if not isinstance(rows_payload, list):
            return []

        rows: list[dict[str, str]] = []
        for row in rows_payload:
            if not isinstance(row, dict):
                continue
            status_id = str(row.get("statusId") or row.get("id") or "").strip()
            status_name = str(row.get("statusName") or row.get("name") or "").strip()
            layer_status = str(
                row.get("layerStatus") or row.get("layerValue") or row.get("value") or ""
            ).strip()
            if not layer_status:
                continue
            rows.append(
                {
                    "statusId": status_id,
                    "statusName": status_name,
                    "layerStatus": layer_status,
                }
            )
        return rows

    @classmethod
    def load_status_mapping_rows(cls) -> list[dict[str, str]]:
        stored = SettingsService().module_label_value(
            Module.EASEMENT.value,
            SettingDialogPlaceholders.EASEMENT_LAYER_STATUS_MAPPING,
        ) or ""
        return cls.parse_status_mapping_rows(stored)

    @classmethod
    def format_status_mapping_summary(cls, stored_value) -> str:
        rows = cls.parse_status_mapping_rows(stored_value)
        lang = LanguageManager()
        if not rows:
            return lang.translate(TranslationKeys.EASEMENT_STATUS_MAPPING_SUMMARY_EMPTY)

        preview_parts = []
        for row in rows[:2]:
            status_name = str(row.get("statusName") or row.get("statusId") or "?").strip()
            layer_status = str(row.get("layerStatus") or "").strip()
            if status_name and layer_status:
                preview_parts.append(f"{status_name} → {layer_status}")
        preview = ", ".join(preview_parts)
        if len(rows) > 2:
            preview = f"{preview}, +{len(rows) - 2}" if preview else f"+{len(rows) - 2}"
        preview = preview or "-"
        return lang.translate(TranslationKeys.EASEMENT_STATUS_MAPPING_SUMMARY).format(
            count=len(rows),
            preview=preview,
        )

    @classmethod
    def map_backend_status_to_layer_value(cls, status_payload) -> str:
        status_name = str(((status_payload or {}).get("name") or "")).strip()
        status_id = str(((status_payload or {}).get("id") or "")).strip()
        rows = cls.load_status_mapping_rows()
        for row in rows:
            if status_id and str(row.get("statusId") or "").strip() == status_id:
                return str(row.get("layerStatus") or "").strip()
        upper_name = status_name.upper()
        for row in rows:
            if upper_name and str(row.get("statusName") or "").strip().upper() == upper_name:
                return str(row.get("layerStatus") or "").strip()
        return status_name

    @classmethod
    def layer_status_value_options(cls, layer: Optional[QgsVectorLayer]) -> list[str]:
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return []

        field_name = cls.resolve_status_field_name(layer)
        if not field_name:
            return []

        field_index = layer.fields().indexFromName(field_name)
        if field_index < 0:
            return []

        values: list[str] = []
        try:
            widget_setup = layer.editorWidgetSetup(field_index)
            widget_type = str(getattr(widget_setup, "type", lambda: "")() or "").strip().lower()
            config = getattr(widget_setup, "config", lambda: {})() or {}
            if widget_type == "valuemap":
                raw_map = config.get("map") or config.get("Map") or []
                if isinstance(raw_map, dict):
                    raw_map = [raw_map]
                if isinstance(raw_map, list):
                    for item in raw_map:
                        if not isinstance(item, dict):
                            continue
                        for key, raw_value in item.items():
                            candidate = str(raw_value if raw_value not in (None, "") else key).strip()
                            if candidate and candidate not in values:
                                values.append(candidate)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.EASEMENT.value,
                event="easement_layer_status_value_map_failed",
            )

        if values:
            return values

        try:
            unique_values = layer.uniqueValues(field_index, limit=200)
        except TypeError:
            unique_values = layer.uniqueValues(field_index)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.EASEMENT.value,
                event="easement_layer_status_unique_values_failed",
            )
            unique_values = set()

        for raw_value in sorted((str(v).strip() for v in unique_values if str(v).strip()), key=str.lower):
            if raw_value not in values:
                values.append(raw_value)
        return values

    @classmethod
    def _ensure_custom_fields(cls, layer: Optional[QgsVectorLayer]) -> tuple[bool, str]:
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return False, "Invalid easement main layer"

        existing = cls._field_map(layer)
        missing_fields: list[QgsField] = []
        if cls.FIELD_EXTERNAL_ID.lower() not in existing:
            missing_fields.append(QgsField(cls.FIELD_EXTERNAL_ID, QVariant.String, len=64))
        if cls.FIELD_EXTERNAL_SYSTEM.lower() not in existing:
            missing_fields.append(QgsField(cls.FIELD_EXTERNAL_SYSTEM, QVariant.String, len=32))
        if cls.FIELD_EXTERNAL_NUMBER.lower() not in existing:
            missing_fields.append(QgsField(cls.FIELD_EXTERNAL_NUMBER, QVariant.String, len=64))

        if not missing_fields:
            return True, ""

        started_edit = False
        try:
            if not layer.isEditable():
                started_edit = bool(layer.startEditing())
                if not started_edit:
                    return False, "Could not start editing easement layer to add external fields"

            provider = layer.dataProvider()
            if provider is None or not provider.addAttributes(missing_fields):
                if started_edit:
                    layer.rollBack()
                return False, "Could not add external easement fields to layer"

            layer.updateFields()
            if started_edit and not layer.commitChanges():
                errors = "; ".join(layer.commitErrors() or [])
                layer.rollBack()
                return False, errors or "Could not commit new easement layer fields"
            return True, ""
        except Exception as exc:
            try:
                if layer.isEditable():
                    layer.rollBack()
            except Exception:
                pass
            PythonFailLogger.log_exception(
                exc,
                module=Module.EASEMENT.value,
                event="easement_layer_ensure_fields_failed",
            )
            return False, str(exc)

    @classmethod
    def find_feature(cls, layer: Optional[QgsVectorLayer], *, item_id: str, item_number: str = ""):
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return None

        identity_field = cls._resolve_identity_field_name(layer)
        number_field = cls._resolve_number_field_name(layer)
        item_id_text = str(item_id or "").strip()
        item_number_text = str(item_number or "").strip()

        try:
            for feature in layer.getFeatures():
                if identity_field and item_id_text:
                    current = str(feature.attribute(identity_field) or "").strip()
                    if current == item_id_text:
                        return feature
                if number_field and item_number_text:
                    current = str(feature.attribute(number_field) or "").strip()
                    if current == item_number_text:
                        return feature
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.EASEMENT.value,
                event="easement_layer_find_feature_failed",
                extra={"item_id": item_id_text, "item_number": item_number_text},
            )
        return None

    @staticmethod
    def current_username() -> str:
        try:
            session = SessionManager()
            username = str(getattr(session, "username", "") or "").strip()
            if username:
                return username
            session.load_credentials()
            return str(getattr(session, "username", "") or "").strip()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.EASEMENT.value,
                event="easement_current_user_resolve_failed",
            )
            return ""

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
    def coerce_value_for_field(field, value):
        if field is None or value is None:
            return value
        try:
            field_type = field.type()
        except Exception:
            field_type = None

        if field_type in (QVariant.Int, QVariant.UInt, QVariant.LongLong, QVariant.ULongLong):
            try:
                return int(value)
            except Exception:
                return value

        if field_type == QVariant.Double:
            try:
                return float(value)
            except Exception:
                return value

        if field_type == QVariant.DateTime:
            if isinstance(value, QDateTime):
                return value
            parsed_datetime = value if isinstance(value, datetime) else EasementLayerService.parse_backend_datetime(value)
            if isinstance(parsed_datetime, datetime):
                return QDateTime(
                    parsed_datetime.year,
                    parsed_datetime.month,
                    parsed_datetime.day,
                    parsed_datetime.hour,
                    parsed_datetime.minute,
                    parsed_datetime.second,
                )
            return value

        if field_type == QVariant.Date:
            if isinstance(value, QDate):
                return value
            parsed_date = value if isinstance(value, date) and not isinstance(value, datetime) else None
            parsed_datetime = value if isinstance(value, datetime) else EasementLayerService.parse_backend_datetime(value)
            if isinstance(parsed_datetime, datetime):
                parsed_date = parsed_datetime.date()
            if isinstance(parsed_date, date):
                return QDate(parsed_date.year, parsed_date.month, parsed_date.day)
            return value

        return value

    @classmethod
    def _set_attr_if_present(cls, feature: QgsFeature, *, layer: QgsVectorLayer, candidates: tuple[str, ...], value) -> None:
        actual = cls._resolve_first_field_name(layer, candidates)
        if not actual:
            return
        field_index = layer.fields().indexFromName(actual)
        field = layer.fields()[field_index] if field_index >= 0 else None
        feature.setAttribute(actual, cls.coerce_value_for_field(field, value))

    @staticmethod
    def _coerce_area_value(layer: QgsVectorLayer, candidates: tuple[str, ...], area_sqm: float):
        actual = EasementLayerService._resolve_first_field_name(layer, candidates)
        if not actual:
            return actual, None
        field_index = layer.fields().indexFromName(actual)
        field = layer.fields()[field_index] if field_index >= 0 else None
        try:
            field_type = field.type() if field is not None else None
        except Exception:
            field_type = None
        if field_type in (QVariant.Int, QVariant.UInt, QVariant.LongLong, QVariant.ULongLong):
            return actual, int(round(area_sqm))
        return actual, round(float(area_sqm), 2)

    @staticmethod
    def _geometry_in_layer_crs(geometry: QgsGeometry, *, source_layer: QgsVectorLayer, target_layer: QgsVectorLayer) -> QgsGeometry:
        transformed = QgsGeometry(geometry)
        try:
            if source_layer.crs() != target_layer.crs():
                transform = QgsCoordinateTransform(
                    source_layer.crs(),
                    target_layer.crs(),
                    QgsProject.instance(),
                )
                transformed.transform(transform)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.EASEMENT.value,
                event="easement_layer_geometry_transform_failed",
            )
        return transformed

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

    @classmethod
    def upsert_final_cut_feature(
        cls,
        *,
        layer: QgsVectorLayer,
        final_layer: QgsVectorLayer,
        item_id: str,
        item_data: Optional[dict] = None,
        property_edges: Optional[list[dict]] = None,
    ) -> tuple[bool, str]:
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return False, "Invalid easement main layer"
        if not isinstance(final_layer, QgsVectorLayer) or not final_layer.isValid():
            return False, "Invalid final cut layer"

        ok_fields, field_error = cls._ensure_custom_fields(layer)
        if not ok_fields:
            return False, field_error

        item_payload = item_data if isinstance(item_data, dict) else {}
        item_id_text = str(item_id or "").strip()
        item_number = str(item_payload.get("number") or "").strip()
        item_type_name = str(((item_payload.get("type") or {}).get("name") or "")).strip()
        added_date = cls.parse_backend_datetime(item_payload.get("createdAt")) or datetime.now()
        updated_date = cls.parse_backend_datetime(item_payload.get("updatedAt")) or datetime.now()
        username = cls.current_username()
        property_edges = property_edges or []

        try:
            final_feature = next(final_layer.getFeatures(), None)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.EASEMENT.value,
                event="easement_layer_final_feature_read_failed",
            )
            final_feature = None
        if final_feature is None:
            return False, "Final cut layer has no geometry"

        geometry = final_feature.geometry()
        if geometry is None or geometry.isEmpty():
            return False, "Final cut geometry is empty"

        target_geometry = cls._geometry_in_layer_crs(geometry, source_layer=final_layer, target_layer=layer)
        try:
            area_sqm = max(0.0, float(target_geometry.area()))
        except Exception:
            area_sqm = 0.0

        cadastral_numbers = [
            str(edge.get("cadastralUnitNumber") or "").strip()
            for edge in property_edges
            if str(edge.get("cadastralUnitNumber") or "").strip()
        ]
        primary_cadastral = cadastral_numbers[0] if cadastral_numbers else ""

        total_compensation = 0.0
        has_compensation = False
        for edge in property_edges:
            total_price = edge.get("totalPrice") if isinstance(edge.get("totalPrice"), dict) else {}
            amount = total_price.get("amount")
            try:
                if amount not in (None, ""):
                    total_compensation += float(amount)
                    has_compensation = True
            except Exception:
                continue

        existing_feature = cls.find_feature(layer, item_id=item_id_text, item_number=item_number)
        feature = QgsFeature(existing_feature) if existing_feature is not None else QgsFeature(layer.fields())
        feature.setGeometry(target_geometry)

        cls._set_attr_if_present(feature, layer=layer, candidates=cls.FIELD_ID_CANDIDATES, value=item_id_text)
        cls._set_attr_if_present(feature, layer=layer, candidates=cls.FIELD_NUMBER_CANDIDATES, value=item_number)
        cls._set_attr_if_present(feature, layer=layer, candidates=cls.FIELD_TYPE_CANDIDATES, value=item_type_name)
        cls._set_attr_if_present(
            feature,
            layer=layer,
            candidates=cls.FIELD_STATUS_CANDIDATES,
            value=cls.map_backend_status_to_layer_value(item_payload.get("status") or {}),
        )
        cls._set_attr_if_present(feature, layer=layer, candidates=cls.FIELD_SYSTEM_CANDIDATES, value=cls.EXT_SYSTEM_NAME)
        cls._set_attr_if_present(feature, layer=layer, candidates=cls.FIELD_PROPERTY_CANDIDATES, value=primary_cadastral)
        cls._set_attr_if_present(feature, layer=layer, candidates=cls.FIELD_UPDATED_BY_CANDIDATES, value=username)
        cls._set_attr_if_present(feature, layer=layer, candidates=cls.FIELD_UPDATE_DATE_CANDIDATES, value=updated_date)

        area_field_name, area_value = cls._coerce_area_value(layer, cls.FIELD_FINAL_AREA_CANDIDATES, area_sqm)
        if area_field_name:
            feature.setAttribute(area_field_name, area_value)

        if has_compensation:
            cls._set_attr_if_present(
                feature,
                layer=layer,
                candidates=cls.FIELD_COMPENSATION_CANDIDATES,
                value=round(total_compensation, 2),
            )

        if existing_feature is None:
            cls._set_attr_if_present(feature, layer=layer, candidates=cls.FIELD_ADDED_BY_CANDIDATES, value=username)
            cls._set_attr_if_present(feature, layer=layer, candidates=cls.FIELD_ADDED_DATE_CANDIDATES, value=added_date)

        started_edit = False
        try:
            if not layer.isEditable():
                started_edit = bool(layer.startEditing())
                if not started_edit:
                    return False, "Could not start editing easement layer"

            if existing_feature is not None:
                if not layer.updateFeature(feature):
                    if started_edit:
                        layer.rollBack()
                    return False, "Could not update easement feature"
            else:
                if not layer.addFeature(feature):
                    if started_edit:
                        layer.rollBack()
                    return False, "Could not add easement feature"

            if started_edit and not layer.commitChanges():
                errors = "; ".join(layer.commitErrors() or [])
                layer.rollBack()
                return False, errors or "Could not commit easement layer changes"

            cls._refresh_saved_layer(layer)
            verified_feature = cls.find_feature(layer, item_id=item_id_text, item_number=item_number)
            if verified_feature is None:
                return False, "Saved easement feature could not be verified on the configured main layer"

            return True, cls._layer_target_label(layer)
        except Exception as exc:
            try:
                if layer.isEditable():
                    layer.rollBack()
            except Exception as rollback_exc:
                PythonFailLogger.log_exception(
                    rollback_exc,
                    module=Module.EASEMENT.value,
                    event="easement_layer_rollback_failed",
                )
            PythonFailLogger.log_exception(
                exc,
                module=Module.EASEMENT.value,
                event="easement_layer_save_failed",
                extra={"item_id": item_id_text},
            )
            return False, str(exc)