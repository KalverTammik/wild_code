"""Works layer services.
Note:
Strict required-field validation for the Works layer field set should be enabled next.
This is planned for the Geospatial partnership workflow so the Geospatial-partnered
GIS application can be activated with automated schema validation.
"""

from __future__ import annotations

from datetime import date, datetime
import html
import json
import re
from typing import Optional

from PyQt5.QtCore import QDate, QDateTime
from qgis.PyQt.QtCore import QVariant
from qgis.core import (
    QgsCoordinateTransform,
    QgsFeature,
    QgsFeatureRequest,
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    QgsRectangle,
    QgsVectorLayer,
    QgsWkbTypes,
)
from qgis.utils import iface

from ...constants.cadastral_fields import Katastriyksus
from ...constants.settings_keys import SettingsService
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...utils.SessionManager import SessionManager
from ...utils.MapTools.MapHelpers import ActiveLayersHelper, MapHelpers
from ...utils.messagesHelper import ModernMessageDialog
from ...utils.url_manager import Module
from ...Logs.python_fail_logger import PythonFailLogger


class WorksLayerService:
    FIELD_EXT_JOB_ID = "ext_job_id"
    FIELD_EXT_JOB_NAME = "ext_job_name"
    FIELD_EXT_JOB_TYPE = "ext_job_type"
    FIELD_EXT_JOB_STATE = "ext_job_state"
    FIELD_ACTIVE = "active"
    FIELD_DETAILED = "detailed"
    FIELD_BEGIN_DATE = "begin_date"
    FIELD_END_DATE = "end_date"
    FIELD_ADDED_BY = "added_by"
    FIELD_ADDED_DATE = "added_date"
    FIELD_UPDATED_BY = "updated_by"
    FIELD_UPDATE_DATE = "update_date"

    @staticmethod
    def build_canonical_feature_values(
        *,
        title: str,
        type_label: str,
        status_id: object = None,
        active: Optional[bool] = None,
        detailed: object = None,
        begin_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        added_by: Optional[str] = None,
        added_date: Optional[datetime] = None,
        updated_by: Optional[str] = None,
        update_date: Optional[datetime] = None,
    ) -> dict[str, object]:
        created_at = added_date or datetime.now()
        updated_at = update_date or created_at
        creator_name = str(added_by or WorksLayerService.current_username() or "").strip()
        updater_name = str(updated_by or creator_name).strip()
        return {
            WorksLayerService.FIELD_EXT_JOB_NAME: str(title or "").strip(),
            WorksLayerService.FIELD_EXT_JOB_TYPE: str(type_label or "").strip(),
            WorksLayerService.FIELD_EXT_JOB_STATE: WorksLayerService.coerce_optional_int(status_id),
            WorksLayerService.FIELD_BEGIN_DATE: begin_date,
            WorksLayerService.FIELD_END_DATE: end_date,
            WorksLayerService.FIELD_ADDED_BY: creator_name,
            WorksLayerService.FIELD_ADDED_DATE: created_at,
            WorksLayerService.FIELD_UPDATED_BY: updater_name,
            WorksLayerService.FIELD_UPDATE_DATE: updated_at,
            WorksLayerService.FIELD_ACTIVE: active,
            WorksLayerService.FIELD_DETAILED: detailed,
        }

    @staticmethod
    def resolve_main_layer(*, lang_manager=None, silent: bool = False) -> Optional[QgsVectorLayer]:
        lang = lang_manager or LanguageManager()
        identifier = SettingsService().module_main_layer_name(Module.WORKS.value) or ""
        layer = MapHelpers.resolve_layer(identifier)
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            if not silent:
                ModernMessageDialog.show_warning(
                    lang.translate(TranslationKeys.ERROR),
                    lang.translate(TranslationKeys.WORKS_LAYER_MISSING),
                )
            return None

        if layer.geometryType() != QgsWkbTypes.PointGeometry:
            if not silent:
                ModernMessageDialog.show_warning(
                    lang.translate(TranslationKeys.ERROR),
                    lang.translate(TranslationKeys.WORKS_LAYER_INVALID_GEOMETRY),
                )
            return None

        if WorksLayerService.resolve_task_id_field_name(layer) is None:
            if not silent:
                ModernMessageDialog.show_warning(
                    lang.translate(TranslationKeys.ERROR),
                    lang.translate(TranslationKeys.WORKS_LAYER_ID_FIELD_MISSING),
                )
            return None

        return layer

    @staticmethod
    def resolve_task_id_field_name(layer: Optional[QgsVectorLayer]) -> Optional[str]:
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return None

        try:
            field_map = {field.name().lower(): field.name() for field in layer.fields()}
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="works_layer_field_map_failed",
            )
            return None

        return field_map.get(WorksLayerService.FIELD_EXT_JOB_ID.lower())

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
                module=Module.WORKS.value,
                event="works_current_user_resolve_failed",
            )
            return ""

    @staticmethod
    def coerce_optional_int(value) -> Optional[int]:
        text = str(value or "").strip()
        if not text:
            return None
        try:
            return int(text)
        except (TypeError, ValueError):
            return None

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
    def created_date_from_task(task: Optional[dict]) -> Optional[datetime]:
        if not isinstance(task, dict):
            return None
        return WorksLayerService.parse_backend_datetime(task.get("createdAt"))

    @staticmethod
    def updated_date_from_task(task: Optional[dict]) -> Optional[datetime]:
        if not isinstance(task, dict):
            return None
        return WorksLayerService.parse_backend_datetime(task.get("updatedAt"))

    @staticmethod
    def status_id_from_task(task: Optional[dict]) -> Optional[int]:
        if not isinstance(task, dict):
            return None
        status_payload = task.get("status") or {}
        if not isinstance(status_payload, dict):
            return None
        return WorksLayerService.coerce_optional_int(status_payload.get("id"))

    @staticmethod
    def status_type_from_task(task: Optional[dict]) -> str:
        if not isinstance(task, dict):
            return ""
        status_payload = task.get("status") or {}
        if not isinstance(status_payload, dict):
            return ""
        return str(status_payload.get("type") or "").strip().upper()

    @staticmethod
    def active_from_task(task: Optional[dict]) -> Optional[bool]:
        status_type = WorksLayerService.status_type_from_task(task)
        if not status_type:
            return None
        if status_type == "CLOSED":
            return False
        if status_type == "OPEN":
            return True
        return True

    @staticmethod
    def detailed_from_task(task: Optional[dict]):
        if not isinstance(task, dict):
            return None
        status_payload = task.get("status") or {}
        if not isinstance(status_payload, dict):
            status_payload = {}
        return {
            "status": {
                "id": status_payload.get("id"),
                "name": status_payload.get("name"),
                "type": status_payload.get("type"),
            },
            "updatedAt": task.get("updatedAt"),
        }

    @staticmethod
    def begin_date_from_task(task: Optional[dict]) -> Optional[datetime]:
        if not isinstance(task, dict):
            return None
        return (
            WorksLayerService.parse_backend_datetime(task.get("startAt"))
            or WorksLayerService.created_date_from_task(task)
        )

    @staticmethod
    def end_date_from_task(task: Optional[dict]) -> Optional[datetime]:
        if not isinstance(task, dict):
            return None

        status_type = WorksLayerService.status_type_from_task(task)
        if status_type != "CLOSED":
            return None

        return (
            WorksLayerService.parse_backend_datetime(task.get("updatedAt"))
            or WorksLayerService.parse_backend_datetime(task.get("dueAt"))
        )

    @staticmethod
    def find_property_feature_at_point(point: QgsPointXY, *, radius_multiplier: float = 3.0):
        property_layer = ActiveLayersHelper.resolve_main_property_layer(silent=True)
        if not isinstance(property_layer, QgsVectorLayer) or not property_layer.isValid():
            return None

        canvas = iface.mapCanvas() if iface is not None else None
        if canvas is None:
            return None

        try:
            search_radius = canvas.mapUnitsPerPixel() * float(radius_multiplier)
        except Exception:
            search_radius = 0.0

        if search_radius <= 0:
            search_radius = 2.0

        layer_point = WorksLayerService._point_in_layer_crs(point, property_layer)

        search_rect = QgsRectangle(
            layer_point.x() - search_radius,
            layer_point.y() - search_radius,
            layer_point.x() + search_radius,
            layer_point.y() + search_radius,
        )
        request = QgsFeatureRequest().setFilterRect(search_rect)

        try:
            return next(property_layer.getFeatures(request), None)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="works_property_lookup_failed",
            )
            return None

    @staticmethod
    def property_cadastral_number(feature) -> str:
        if feature is None:
            return ""
        try:
            value = feature.attribute(Katastriyksus.tunnus)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="works_property_tunnus_failed",
            )
            return ""
        return str(value or "").strip()

    @staticmethod
    def property_display_text(feature, *, lang_manager=None) -> str:
        lang = lang_manager or LanguageManager()
        if feature is None:
            return lang.translate(TranslationKeys.WORKS_CREATE_PROPERTY_NONE)

        parts: list[str] = []
        cadastral = WorksLayerService.property_cadastral_number(feature)
        if cadastral:
            parts.append(cadastral)

        for field_name in (
            Katastriyksus.l_aadress,
            Katastriyksus.ay_nimi,
            Katastriyksus.ov_nimi,
            Katastriyksus.mk_nimi,
        ):
            try:
                value = feature.attribute(field_name)
            except Exception:
                value = None
            text = str(value or "").strip()
            if text:
                parts.append(text)

        return " · ".join(parts) if parts else lang.translate(TranslationKeys.WORKS_CREATE_PROPERTY_NONE)

    @staticmethod
    def find_feature_by_task_id(layer: Optional[QgsVectorLayer], task_id: str):
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return None

        task_id_text = str(task_id or "").strip()
        if not task_id_text:
            return None

        task_id_field = WorksLayerService.resolve_task_id_field_name(layer)
        if not task_id_field:
            return None

        try:
            for feature in layer.getFeatures():
                value = str(feature.attribute(task_id_field) or "").strip()
                if value == task_id_text:
                    return feature
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="works_layer_find_feature_failed",
                extra={"task_id": task_id_text},
            )
        return None

    @staticmethod
    def focus_feature_by_task_id(layer: Optional[QgsVectorLayer], task_id: str) -> bool:
        feature = WorksLayerService.find_feature_by_task_id(layer, task_id)
        if feature is None:
            return False

        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return False

        try:
            MapHelpers.ensure_layer_visible(layer, make_active=True)
            MapHelpers.select_features_by_ids(layer, [int(feature.id())], zoom=True)
            return True
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="works_layer_focus_feature_failed",
                extra={"task_id": str(task_id or "").strip()},
            )
            return False

    @staticmethod
    def insert_work_feature(
        *,
        layer: QgsVectorLayer,
        point: QgsPointXY,
        task_id: str,
        title: str,
        type_label: str,
        status_id: object = None,
        active: Optional[bool] = None,
        detailed: object = None,
        begin_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        added_by: Optional[str] = None,
        added_date: Optional[datetime] = None,
        updated_by: Optional[str] = None,
        update_date: Optional[datetime] = None,
    ) -> tuple[bool, str]:
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return False, "Invalid works layer"

        task_id_field = WorksLayerService.resolve_task_id_field_name(layer)
        if not task_id_field:
            return False, "Task id field missing"

        feature = QgsFeature(layer.fields())
        layer_point = WorksLayerService._point_in_layer_crs(point, layer)
        feature.setGeometry(QgsGeometry.fromPointXY(layer_point))

        field_map = {field.name().lower(): field.name() for field in layer.fields()}
        field_values = WorksLayerService.build_canonical_feature_values(
            title=title,
            type_label=type_label,
            status_id=status_id,
            active=active,
            detailed=detailed,
            begin_date=begin_date,
            end_date=end_date,
            added_by=added_by,
            added_date=added_date,
            updated_by=updated_by,
            update_date=update_date,
        )

        task_id_value = WorksLayerService.coerce_optional_int(task_id)
        feature.setAttribute(task_id_field, task_id_value if task_id_value is not None else str(task_id or "").strip())
        for canonical_name, value in field_values.items():
            WorksLayerService._set_attr_if_present(
                feature,
                layer=layer,
                field_map=field_map,
                field_name=canonical_name,
                value=value,
            )

        started_edit = False
        try:
            if not layer.isEditable():
                started_edit = bool(layer.startEditing())
                if not started_edit:
                    return False, "Could not start editing works layer"

            if not layer.addFeature(feature):
                if started_edit:
                    layer.rollBack()
                return False, "Could not add feature to works layer"

            if started_edit and not layer.commitChanges():
                errors = "; ".join(layer.commitErrors() or [])
                layer.rollBack()
                return False, errors or "Could not commit works layer changes"

            layer.triggerRepaint()
            return True, ""
        except Exception as exc:
            try:
                if layer.isEditable():
                    layer.rollBack()
            except Exception as rollback_exc:
                PythonFailLogger.log_exception(
                    rollback_exc,
                    module=Module.WORKS.value,
                    event="works_layer_rollback_failed",
                )
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="works_layer_insert_failed",
            )
            return False, str(exc)

    @staticmethod
    def _set_attr_if_present(
        feature: QgsFeature,
        *,
        layer: Optional[QgsVectorLayer],
        field_map: dict[str, str],
        field_name: str,
        value,
    ) -> None:
        actual = field_map.get(str(field_name).lower())
        if not actual:
            return

        field = None
        if isinstance(layer, QgsVectorLayer) and layer.isValid():
            field_index = layer.fields().indexFromName(actual)
            if field_index >= 0:
                field = layer.fields()[field_index]

        feature.setAttribute(actual, WorksLayerService.coerce_value_for_field(field, value))

    @staticmethod
    def coerce_value_for_field(field, value):
        if field is None or value is None:
            return value

        try:
            field_type = field.type()
        except Exception:
            field_type = None

        if field_type == QVariant.Bool:
            if isinstance(value, bool):
                return value
            text = str(value or "").strip().lower()
            if text in ("true", "1", "yes", "y"):
                return True
            if text in ("false", "0", "no", "n"):
                return False
            return value

        if field_type == QVariant.String and isinstance(value, (dict, list)):
            try:
                return json.dumps(value, ensure_ascii=False)
            except Exception:
                return str(value)

        if field_type == QVariant.DateTime:
            if isinstance(value, QDateTime):
                return value

            parsed_datetime = value if isinstance(value, datetime) else WorksLayerService.parse_backend_datetime(value)
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
            parsed_datetime = value if isinstance(value, datetime) else WorksLayerService.parse_backend_datetime(value)
            if isinstance(parsed_datetime, datetime):
                parsed_date = parsed_datetime.date()
            if isinstance(parsed_date, date):
                return QDate(parsed_date.year, parsed_date.month, parsed_date.day)
            return value

        return value

    @staticmethod
    def _point_in_layer_crs(point: QgsPointXY, layer: QgsVectorLayer) -> QgsPointXY:
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return point

        canvas = iface.mapCanvas() if iface is not None else None
        if canvas is None:
            return point

        try:
            source_crs = canvas.mapSettings().destinationCrs()
            target_crs = layer.crs()
            if not source_crs.isValid() or not target_crs.isValid() or source_crs == target_crs:
                return point

            transform = QgsCoordinateTransform(
                source_crs,
                target_crs,
                QgsProject.instance().transformContext(),
            )
            return transform.transform(point)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="works_point_transform_failed",
            )
            return point


class WorksDescriptionService:
    SECTION_MARKER = "kavitro:type=works-metadata"
    _DESCRIPTION_SPACER_HTML = "<p>&nbsp;</p>\n<p>&nbsp;</p>"
    _SECTION_PATTERN = re.compile(
        r'<p[^>]*?>\s*🛠️.*?</p>\s*<div[^>]*?>\s*<table[^>]*?>.*?</table>\s*</div>\s*(?:<p>\s*</p>\s*)?\s*$',
        re.IGNORECASE | re.DOTALL,
    )
    _BREAK_PATTERN = re.compile(r'<\s*br\s*/?\s*>', re.IGNORECASE)
    _PARAGRAPH_END_PATTERN = re.compile(r'</p\s*>', re.IGNORECASE)
    _TAG_PATTERN = re.compile(r'<[^>]+>')

    _TABLE_STYLE = (
        "width: 100%; border-collapse: collapse; font-family: Arial, sans-serif; "
        "font-size: 12px;"
    )
    _HEADER_CELL_STYLE = (
        "padding: 4px 6px; font-weight: bold; background: #e5e7eb; border: 1px solid #cbd5e1; "
        "text-align: center; color: #333333;"
    )
    _BODY_CELL_STYLE = (
        "padding: 4px 6px; border: 1px solid #d1d5db; vertical-align: top;"
    )

    @classmethod
    def build_task_description(
        cls,
        *,
        layer: Optional[QgsVectorLayer],
        point: QgsPointXY,
        description_text: str,
        property_feature=None,
        task_id: Optional[str] = None,
        lang_manager=None,
        point_in_layer_crs: bool = False,
    ) -> str:
        lang = lang_manager or LanguageManager()
        layer_point = (
            point
            if point_in_layer_crs or layer is None
            else WorksLayerService._point_in_layer_crs(point, layer)
        )
        description_text = str(description_text or "").strip()

        rows: list[tuple[str, str]] = []

        layer_name = cls._layer_name(layer)
        if layer_name:
            rows.append((lang.translate(TranslationKeys.WORKS_METADATA_LAYER_NAME), layer_name))

        for label, value in cls._project_rows(lang_manager=lang):
            rows.append((label, value))

        rows.append(("x", cls._format_coordinate(layer_point.x())))
        rows.append(("y", cls._format_coordinate(layer_point.y())))

        z_value = cls._extract_z(point)
        rows.append(("z", cls._format_coordinate(z_value) if z_value is not None else "—"))

        if isinstance(layer, QgsVectorLayer) and layer.isValid():
            try:
                crs_value = layer.crs().authid() or layer.crs().description()
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module=Module.WORKS.value,
                    event="works_description_crs_read_failed",
                )
                crs_value = ""
            if crs_value:
                rows.append(("crs", str(crs_value).strip()))

        rows_html = "".join(cls._render_table_row(label, value) for label, value in rows if str(value or "").strip())
        if not rows_html:
            return cls._render_description_only(description_text)

        description_block = cls._render_description_block(
            description_text,
            lang_manager=lang,
        )

        return (
            f"{description_block}"
            f"<!-- {cls.SECTION_MARKER} -->\n"
            f"<p style=\"font-size: 13px; font-weight: bold; margin: 14px 0 4px 6px;\">"
            f"🛠️ {html.escape(lang.translate(TranslationKeys.WORKS_METADATA_SECTION_TITLE))}</p>\n"
            f"<div style=\"width: 100%;\">\n"
            f"  <table style=\"{cls._TABLE_STYLE}\">\n"
            f"    {cls._render_table_header(lang_manager=lang)}\n"
            f"    {rows_html}\n"
            f"  </table>\n"
            f"</div>\n"
            f"<p></p>"
        )

    @classmethod
    def _render_description_only(cls, description_text: str) -> str:
        normalized = str(description_text or "").strip()
        if not normalized:
            return ""
        return f"<p style=\"margin: 6px 6px 0 6px;\">{cls._plain_text_to_html(normalized)}</p>"

    @classmethod
    def remove_metadata_section(cls, description_html: str | None) -> str:
        description = cls._normalize_html(description_html)
        if not description:
            return ""
        description = re.sub(r'<!--\s*kavitro:type=works-metadata\s*-->\s*', "", description, count=1)
        return cls._SECTION_PATTERN.sub("", description, count=1).strip()

    @classmethod
    def extract_user_description(cls, description_html: str | None) -> str:
        return cls._html_to_plain_text(cls.remove_metadata_section(description_html))

    @classmethod
    def merge_metadata_into_description(
        cls,
        *,
        existing_html: str | None,
        layer: Optional[QgsVectorLayer],
        point: QgsPointXY,
        lang_manager=None,
        point_in_layer_crs: bool = False,
    ) -> str:
        description_text = cls.extract_user_description(existing_html)
        return cls.build_task_description(
            layer=layer,
            point=point,
            description_text=description_text,
            lang_manager=lang_manager,
            point_in_layer_crs=point_in_layer_crs,
        )

    @classmethod
    def _render_description_block(
        cls,
        description_text: str,
        *,
        lang_manager=None,
    ) -> str:
        normalized = str(description_text or "").strip()
        if not normalized:
            return ""
        return (
            f"<p style=\"margin: 6px 6px 0 6px;\">{cls._plain_text_to_html(normalized)}</p>\n"
            f"{cls._DESCRIPTION_SPACER_HTML}\n"
        )

    @staticmethod
    def _layer_name(layer: Optional[QgsVectorLayer]) -> str:
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return ""
        try:
            return str(layer.name() or "").strip()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="works_description_layer_name_failed",
            )
            return ""

    @classmethod
    def _project_rows(cls, *, lang_manager: LanguageManager) -> list[tuple[str, str]]:
        project = QgsProject.instance()
        if project is None:
            return []

        rows: list[tuple[str, str]] = []
        try:
            project_name = str(project.baseName() or "").strip()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="works_description_project_name_failed",
            )
            project_name = ""

        try:
            project_title = str(project.title() or "").strip()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="works_description_project_title_failed",
            )
            project_title = ""

        if project_name:
            rows.append((lang_manager.translate(TranslationKeys.WORKS_METADATA_PROJECT_NAME), project_name))
        if project_title and project_title != project_name:
            rows.append((lang_manager.translate(TranslationKeys.WORKS_METADATA_PROJECT_TITLE), project_title))
        return rows

    @staticmethod
    def _field_map(layer: Optional[QgsVectorLayer]) -> dict[str, str]:
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return {}
        try:
            return {field.name().lower(): field.name() for field in layer.fields()}
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="works_description_field_map_failed",
            )
            return {}

    @staticmethod
    def _extract_z(point: QgsPointXY) -> Optional[float]:
        z_getter = getattr(point, "z", None)
        if not callable(z_getter):
            return None
        try:
            z_value = z_getter()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="works_description_z_read_failed",
            )
            return None

        try:
            return float(z_value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _format_coordinate(value: float) -> str:
        return f"{float(value):.3f}"

    @staticmethod
    def _plain_text_to_html(value: str) -> str:
        return html.escape(value or "").replace("\n", "<br/>")

    @staticmethod
    def _normalize_html(value: str | None) -> str:
        return value.strip() if isinstance(value, str) else ""

    @classmethod
    def _html_to_plain_text(cls, value: str | None) -> str:
        if not value:
            return ""
        normalized = cls._BREAK_PATTERN.sub("\n", value)
        normalized = cls._PARAGRAPH_END_PATTERN.sub("\n", normalized)
        normalized = cls._TAG_PATTERN.sub("", normalized)
        normalized = html.unescape(normalized)
        normalized = normalized.replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ")

        cleaned_lines: list[str] = []
        blank_emitted = False
        for raw_line in normalized.split("\n"):
            line = raw_line.strip()
            if not line:
                if cleaned_lines and not blank_emitted:
                    cleaned_lines.append("")
                    blank_emitted = True
                continue
            cleaned_lines.append(line)
            blank_emitted = False

        return "\n".join(cleaned_lines).strip()

    @classmethod
    def _render_table_header(cls, *, lang_manager: LanguageManager) -> str:
        return (
            "<tr>"
            f"<td style=\"{cls._HEADER_CELL_STYLE} width: 35%;\">"
            f"{html.escape(lang_manager.translate(TranslationKeys.WORKS_METADATA_COLUMN_FIELD))}</td>"
            f"<td style=\"{cls._HEADER_CELL_STYLE} width: 65%; text-align: left;\">"
            f"{html.escape(lang_manager.translate(TranslationKeys.WORKS_METADATA_COLUMN_VALUE))}</td>"
            "</tr>"
        )

    @classmethod
    def _render_table_row(cls, label: str, value: str) -> str:
        return (
            "<tr>"
            f"<td style=\"{cls._BODY_CELL_STYLE}\"><p>{cls._plain_text_to_html(str(label or '').strip())}</p></td>"
            f"<td style=\"{cls._BODY_CELL_STYLE}\"><p>{cls._plain_text_to_html(str(value or '').strip())}</p></td>"
            "</tr>"
        )