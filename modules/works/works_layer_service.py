from __future__ import annotations

from datetime import datetime
import html
import re
from typing import Optional

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
from ...utils.MapTools.MapHelpers import ActiveLayersHelper, MapHelpers
from ...utils.messagesHelper import ModernMessageDialog
from ...utils.url_manager import Module
from ...Logs.python_fail_logger import PythonFailLogger


class WorksLayerService:
    TASK_ID_FIELD_CANDIDATES = ("Mailabl_id", "mailabl_id", "task_id", "taskid")

    @staticmethod
    def build_canonical_feature_values(
        *,
        title: str,
        description: str,
        type_label: str,
        priority: str,
        has_property: bool,
        timestamp: Optional[datetime] = None,
    ) -> dict[str, object]:
        now = timestamp or datetime.now()
        return {
            "title": str(title or "").strip(),
            "description": str(description or "").strip(),
            "type": str(type_label or "").strip(),
            "priority": str(priority or "").strip(),
            "status": True,
            "active": True,
            "affected_properties": bool(has_property),
            "datetime": now.strftime("%Y-%m-%d %H:%M"),
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
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

        for candidate in WorksLayerService.TASK_ID_FIELD_CANDIDATES:
            actual = field_map.get(str(candidate).lower())
            if actual:
                return actual
        return None

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
        description: str,
        type_label: str,
        priority: str,
        has_property: bool,
        timestamp: Optional[datetime] = None,
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
            description=description,
            type_label=type_label,
            priority=priority,
            has_property=has_property,
            timestamp=timestamp,
        )

        feature.setAttribute(task_id_field, str(task_id))
        for canonical_name, value in field_values.items():
            WorksLayerService._set_attr_if_present(feature, field_map, canonical_name, value)

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
    def _set_attr_if_present(feature: QgsFeature, field_map: dict[str, str], field_name: str, value) -> None:
        actual = field_map.get(str(field_name).lower())
        if not actual:
            return
        feature.setAttribute(actual, value)

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
        field_values: dict[str, object],
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
        description_text = str(field_values.get("description") or "").strip()

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
            field_values={"description": description_text},
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