"""What the module layer services (works, as-built, projects, easements) have in common."""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import date, datetime
from typing import Callable, ClassVar, Optional

from qgis.PyQt.QtCore import QDate, QDateTime, QTime, QVariant
from qgis.core import (
    QgsCoordinateTransform,
    QgsFeature,
    QgsFeatureRequest,
    QgsField,
    QgsGeometry,
    QgsMapLayer,
    QgsPointXY,
    QgsProject,
    QgsRectangle,
    QgsVectorLayer,
    QgsWkbTypes,
)
from qgis.utils import iface

from ..settings_service import SettingsService
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...Logs.python_fail_logger import PythonFailLogger
from ..MapTools.MapHelpers import MapHelpers
from ..SessionManager import SessionManager
from ..geometry_payload import GeometryPayloadService
from ...constants.module_names import Module
from ..user_dialogs import UserDialogs


@dataclass(frozen=True)
class FieldValueProblem:
    """A value a layer save could not convert for its field. The field was written empty and the save went on."""

    NUMBER: ClassVar[str] = "number"
    INTEGER: ClassVar[str] = "integer"
    YES_NO: ClassVar[str] = "yes/no"
    DATE: ClassVar[str] = "date"
    DATE_TIME: ClassVar[str] = "date and time"
    # Long text (a whole note in the wrong field) is cut, so a message or log line stays readable.
    MAX_VALUE_LENGTH: ClassVar[int] = 60

    field_name: str
    field_label: str  # the field's alias when the layer has one
    raw_value: str
    value_type: str
    expected: str  # one of the kinds above

    @classmethod
    def for_field(cls, field, value, expected: str) -> "FieldValueProblem":
        name = str(field.name() or "")
        label = str(field.displayName() or "") or name
        raw = str(value)
        if len(raw) > cls.MAX_VALUE_LENGTH:
            raw = raw[: cls.MAX_VALUE_LENGTH - 1] + "\u2026"
        return cls(field_name=name, field_label=label, raw_value=raw, value_type=type(value).__name__, expected=expected)


@dataclass(frozen=True)
class LayerEditTexts:
    """What one layer edit returns when a step fails, and its log events for an unexpected error."""

    start_failed: str
    change_failed: str
    commit_failed: str
    failed_event: str
    rollback_event: str


_REJECTED = object()
_INTEGER_RANGES = {
    QVariant.Int: (-(2**31), 2**31 - 1),
    QVariant.UInt: (0, 2**32 - 1),
    QVariant.LongLong: (-(2**63), 2**63 - 1),
    QVariant.ULongLong: (0, 2**64 - 1),
}
_TRUE_WORDS = frozenset({"1", "true", "t", "yes", "y", "jah"})
_FALSE_WORDS = frozenset({"0", "false", "f", "no", "n", "ei"})


class ModuleLayerServiceBase:
    """Helpers every module layer service shares. A service names its module and warning texts below."""

    MODULE: Module
    LAYER_MISSING_KEY: str
    LAYER_AMBIGUOUS_KEY: str
    REQUIRED_GEOMETRY: Optional[QgsWkbTypes.GeometryType] = None
    LAYER_INVALID_GEOMETRY_KEY: str = ""

    @staticmethod
    def parse_backend_datetime(value) -> Optional[datetime]:
        """Backend ISO text, or a date the user typed in Estonian notation (dd.mm.yyyy, optionally with the time)."""
        text = str(value or "").strip()
        if not text:
            return None
        normalized = text.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            parsed = None
        if parsed is None:
            # strptime refuses a day the month does not have (31.02.2024), so a wrong date stays rejected.
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M", "%d.%m.%Y"):
                try:
                    parsed = datetime.strptime(text, fmt)
                    break
                except ValueError:
                    continue
        if parsed is None:
            return None
        if parsed.tzinfo is not None:
            try:
                parsed = parsed.astimezone().replace(tzinfo=None)
            except (ValueError, OSError, OverflowError):  # dates outside the OS time range
                parsed = parsed.replace(tzinfo=None)
        return parsed

    @staticmethod
    def parse_number_text(value) -> Optional[float]:
        """Number from form text; Estonian input uses a decimal comma and may group digits with spaces."""
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value) if math.isfinite(value) else None
        text = ModuleLayerServiceBase._number_text(value)
        if not text:
            return None
        try:
            number = float(text)
        except (TypeError, ValueError, OverflowError):
            return None
        # "inf" and "nan" parse, but no layer field can store them.
        return number if math.isfinite(number) else None

    @staticmethod
    def _number_text(value) -> str:
        return str(value or "").strip().replace("\u00a0", "").replace(" ", "").replace(",", ".")

    @staticmethod
    def _integer_value(value, field_type):
        if isinstance(value, bool):
            number = int(value)
        elif isinstance(value, int):
            number = value
        else:
            try:
                # Exact for long digit strings, which a float would round.
                number = int(ModuleLayerServiceBase._number_text(value))
            except ValueError:
                parsed = ModuleLayerServiceBase.parse_number_text(value)
                # "2,5" in a whole-number field is a typing mistake, not something to round away.
                if parsed is None or not parsed.is_integer():
                    return _REJECTED
                number = int(parsed)
        low, high = _INTEGER_RANGES[field_type]
        return number if low <= number <= high else _REJECTED

    @staticmethod
    def _double_value(value, field_type):
        if isinstance(value, bool):
            return float(value)
        number = ModuleLayerServiceBase.parse_number_text(value)
        return _REJECTED if number is None else number

    @staticmethod
    def _bool_value(value, field_type):
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        if text in _TRUE_WORDS:
            return True
        if text in _FALSE_WORDS:
            return False
        return _REJECTED

    @staticmethod
    def _python_datetime(value) -> Optional[datetime]:
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return datetime(value.year, value.month, value.day)
        return ModuleLayerServiceBase.parse_backend_datetime(value)

    @staticmethod
    def _date_value(value, field_type):
        if isinstance(value, QDate):
            return value if value.isValid() else None
        if isinstance(value, QDateTime):
            return value.date() if value.isValid() else None
        parsed = ModuleLayerServiceBase._python_datetime(value)
        return _REJECTED if parsed is None else QDate(parsed.year, parsed.month, parsed.day)

    @staticmethod
    def _datetime_value(value, field_type):
        if isinstance(value, QDateTime):
            return value if value.isValid() else None
        if isinstance(value, QDate):
            return QDateTime(value, QTime(0, 0)) if value.isValid() else None
        parsed = ModuleLayerServiceBase._python_datetime(value)
        if parsed is None:
            return _REJECTED
        return QDateTime(parsed.year, parsed.month, parsed.day, parsed.hour, parsed.minute, parsed.second)

    @staticmethod
    def coerce_field_value(field, value) -> tuple[object, Optional[FieldValueProblem]]:
        """The value as the field stores it, and the problem when it could not be converted (then the value is None).

        A wrong value must not fail the whole layer save: the field stays empty and the caller can tell the user.
        Field types without a rule, and fields whose type cannot be read, get the value unchanged.
        """
        if field is None or value is None:
            return value, None
        if isinstance(value, QVariant) and value.isNull():  # QGIS NULL
            return None, None
        try:
            field_type = field.type()
        except (AttributeError, RuntimeError):  # not a field, or the layer was deleted
            return value, None

        if field_type == QVariant.String:
            if isinstance(value, (dict, list)):
                try:
                    return json.dumps(value, ensure_ascii=False), None
                except (TypeError, ValueError):  # not JSON-serialisable, or a circular structure
                    return str(value), None
            return value, None

        if field_type in _INTEGER_RANGES:
            convert, expected = ModuleLayerServiceBase._integer_value, FieldValueProblem.INTEGER
        elif field_type == QVariant.Double:
            convert, expected = ModuleLayerServiceBase._double_value, FieldValueProblem.NUMBER
        elif field_type == QVariant.Bool:
            convert, expected = ModuleLayerServiceBase._bool_value, FieldValueProblem.YES_NO
        elif field_type == QVariant.Date:
            convert, expected = ModuleLayerServiceBase._date_value, FieldValueProblem.DATE
        elif field_type == QVariant.DateTime:
            convert, expected = ModuleLayerServiceBase._datetime_value, FieldValueProblem.DATE_TIME
        else:
            return value, None

        if isinstance(value, str) and not value.strip():  # a blank form field means no value
            return None, None
        converted = convert(value, field_type)
        if converted is _REJECTED:
            return None, FieldValueProblem.for_field(field, value, expected)
        return converted, None

    @classmethod
    def coerce_value_for_field(cls, field, value, problems: Optional[list[FieldValueProblem]] = None):
        """`coerce_field_value` for writing: a rejected value is logged, added to `problems`, and becomes None."""
        coerced, problem = cls.coerce_field_value(field, value)
        if problem is None:
            return coerced
        PythonFailLogger.log(
            f"{cls.MODULE.value}_field_value_rejected",
            module=cls.MODULE.value,
            extra={
                "field": problem.field_name,
                "value_type": problem.value_type,
                "value": problem.raw_value,
                "expected": problem.expected,
            },
        )
        if problems is not None:
            problems.append(problem)
        return coerced

    @staticmethod
    def coerce_optional_int(value) -> Optional[int]:
        text = str(value or "").strip()
        if not text:
            return None
        try:
            return int(text)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _field_map(cls, layer: Optional[QgsVectorLayer]) -> dict[str, str]:
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return {}
        try:
            return {field.name().lower(): field.name() for field in layer.fields()}
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=cls.MODULE.value,
                event=f"{cls.MODULE.value}_layer_field_map_failed",
            )
            return {}

    @classmethod
    def _find_first_feature(
        cls, layer: Optional[QgsVectorLayer], keys: tuple[tuple[Optional[str], object], ...], *, log_extra: dict
    ) -> Optional[QgsFeature]:
        """The feature matching the first key that any feature matches; within one key, the first in layer order.

        The keys are in priority order (the Kavitro id first), so a feature carrying the id wins over an earlier one
        that only matches the number or name. In edit mode QGIS returns the features added in the session first.
        """
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return None
        wanted = [(field, str(value or "").strip()) for field, value in keys]
        wanted = [(field, text) for field, text in wanted if field and text]
        if not wanted:
            return None
        # One pass over the layer: the first match per key, stopping as soon as the first key matches.
        first_match: list[Optional[QgsFeature]] = [None] * len(wanted)
        try:
            for feature in layer.getFeatures():
                for index, (field, text) in enumerate(wanted):
                    if first_match[index] is None and str(feature.attribute(field) or "").strip() == text:
                        first_match[index] = feature
                if first_match[0] is not None:
                    break
            return next((feature for feature in first_match if feature is not None), None)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=cls.MODULE.value,
                event=f"{cls.MODULE.value}_layer_find_feature_failed",
                extra=log_extra,
            )
        return None

    @classmethod
    def _layer_text(cls, key: str) -> str:
        """A layer message in the plugin language; "{module}" in it is this service's module name."""
        lang = LanguageManager()
        return lang.translate(key, fallback=key).format(module=lang.translate_module_name(cls.MODULE.value))

    @classmethod
    def sync_status_to_feature(cls, item_id: str, values: list[tuple[tuple[str, ...], object]]) -> bool:
        """Write status-derived values onto the item's map feature; True when the feature holds them afterwards.

        `values` are (field name candidates, value) pairs; a pair whose field the layer lacks is skipped.
        Runs after a status change on the card. A layer the user is editing is left alone: committing
        would also save the user's own pending edits.
        """
        item_id_text = str(item_id or "").strip()
        if not item_id_text or not values:
            return False
        layer = cls.resolve_main_layer(dialogs=None)
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return False
        module = cls.MODULE.value
        extra = {"item_id": item_id_text, "layer": layer.name()}
        if layer.isEditable():
            PythonFailLogger.log(f"{module}_status_sync_skipped_layer_editable", module=module, extra=extra)
            return False
        feature = cls.find_feature(layer, item_id=item_id_text)
        if feature is None:
            return False

        changes: dict[int, object] = {}
        found_field = False
        for candidates, value in values:
            field_name = cls._resolve_first_field_name(layer, candidates)
            index = layer.fields().indexOf(field_name) if field_name else -1
            if index < 0:
                continue
            found_field = True
            coerced = cls.coerce_value_for_field(layer.fields().at(index), value)
            if feature.attribute(index) != coerced:
                changes[index] = coerced
        if not found_field:
            return False
        if not changes:
            return True

        started_edit = bool(layer.startEditing())
        if not started_edit:
            PythonFailLogger.log(f"{module}_status_sync_start_failed", module=module, extra=extra)
            return False
        try:
            written = all(layer.changeAttributeValue(feature.id(), index, value) for index, value in changes.items())
            if written and layer.commitChanges():
                layer.triggerRepaint()
                return True
            errors = "; ".join(layer.commitErrors() or [])
            PythonFailLogger.log(f"{module}_status_sync_failed", module=module, extra={**extra, "errors": errors})
        except RuntimeError as exc:  # the layer was deleted meanwhile
            PythonFailLogger.log_exception(exc, module=module, event=f"{module}_status_sync_failed", extra=extra)
        cls._rollback_own_edit(layer, started_edit, event=f"{module}_status_sync_rollback_failed")
        return False

    @classmethod
    def _rollback_own_edit(cls, layer: QgsVectorLayer, started_edit: bool, *, event: str) -> None:
        # Only the session this service opened: rolling back the user's own session would drop their other edits.
        try:
            if started_edit and layer.isEditable():
                layer.rollBack()
        except Exception as rollback_exc:
            PythonFailLogger.log_exception(rollback_exc, module=cls.MODULE.value, event=event)

    @classmethod
    def _add_missing_fields(cls, layer: QgsVectorLayer, missing: list[QgsField], *, texts: LayerEditTexts) -> tuple[bool, str]:
        """Adds the fields through the provider, committing only an edit session opened here.

        Through the provider the fields are on the layer at once: undoing or rolling back the user's own edit
        session cannot remove them while the features drawn in it still need them.
        """
        if not missing:
            return True, ""
        started_edit = False
        try:
            if not layer.isEditable():
                started_edit = bool(layer.startEditing())
                if not started_edit:
                    return False, cls._layer_text(texts.start_failed)

            provider = layer.dataProvider()
            if provider is None or not provider.addAttributes(missing):
                if started_edit:
                    layer.rollBack()
                return False, cls._layer_text(texts.change_failed)

            layer.updateFields()
            if not started_edit:
                layer.triggerRepaint()
                return True, ""
            if not layer.commitChanges():
                errors = "; ".join(layer.commitErrors() or [])
                layer.rollBack()
                return False, errors or cls._layer_text(texts.commit_failed)
            return True, ""
        except Exception as exc:
            cls._rollback_own_edit(layer, started_edit, event=texts.rollback_event)
            PythonFailLogger.log_exception(exc, module=cls.MODULE.value, event=texts.failed_event)
            return False, str(exc)

    @classmethod
    def _write_feature(
        cls,
        layer: QgsVectorLayer,
        feature: QgsFeature,
        *,
        add: bool,
        texts: LayerEditTexts,
        log_extra: Optional[dict] = None,
        check_saved: Optional[Callable[[Optional[int]], tuple[bool, str]]] = None,
    ) -> tuple[bool, str]:
        """Adds or updates the feature; commits and refreshes when the layer was not already in edit mode.

        In the user's own edit session the change stays in it, for the user (or the draw flow) to save.
        `check_saved` gets the id the written feature has now (None when the layer did not report it).
        """
        started_edit = False
        committed_ids: list[int] = []
        try:
            if not layer.isEditable():
                started_edit = bool(layer.startEditing())
                if not started_edit:
                    return False, cls._layer_text(texts.start_failed)

            written = layer.addFeature(feature) if add else layer.updateFeature(feature)
            if not written:
                if started_edit:
                    layer.rollBack()
                return False, cls._layer_text(texts.change_failed)

            if started_edit and not cls._commit_noting_added_ids(layer, committed_ids):
                errors = "; ".join(layer.commitErrors() or [])
                layer.rollBack()
                return False, errors or cls._layer_text(texts.commit_failed)

            cls._refresh_after_save(layer)
            if check_saved is None:
                return True, ""
            return check_saved(cls._written_feature_id(feature, add=add, committed=started_edit, committed_ids=committed_ids))
        except Exception as exc:
            cls._rollback_own_edit(layer, started_edit, event=texts.rollback_event)
            PythonFailLogger.log_exception(exc, module=cls.MODULE.value, event=texts.failed_event, extra=log_extra)
            return False, str(exc)

    @staticmethod
    def _commit_noting_added_ids(layer: QgsVectorLayer, added_ids: list[int]) -> bool:
        # A feature added in the session has a temporary id until the commit; the provider's ids arrive in this signal.
        def note(_layer_id, features) -> None:
            added_ids.extend(int(feature.id()) for feature in features)

        layer.committedFeaturesAdded.connect(note)
        try:
            return bool(layer.commitChanges())
        finally:
            try:
                layer.committedFeaturesAdded.disconnect(note)
            except (TypeError, RuntimeError):  # already disconnected, or the layer was deleted
                pass

    @staticmethod
    def _written_feature_id(feature: QgsFeature, *, add: bool, committed: bool, committed_ids: list[int]) -> Optional[int]:
        if add and committed:
            # The session was opened here, so the one feature it added is the written one.
            return committed_ids[0] if len(committed_ids) == 1 else None
        return int(feature.id())

    @classmethod
    def _refresh_after_save(cls, layer: QgsVectorLayer) -> None:
        cls._refresh_saved_layer(layer)

    @staticmethod
    def _refresh_saved_layer(layer: Optional[QgsVectorLayer]) -> None:
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return
        try:
            layer.updateExtents()
        except RuntimeError:  # layer deleted after the save
            pass
        try:
            if not layer.isEditable():
                layer.reload()
        except RuntimeError:
            pass
        try:
            layer.triggerRepaint()
        except RuntimeError:
            pass
        try:
            if iface is not None and iface.mapCanvas() is not None:
                iface.mapCanvas().refresh()
        except RuntimeError:  # canvas deleted
            pass

    @classmethod
    def current_username(cls) -> str:
        try:
            session = SessionManager()
            username = str(session.username or "").strip()
            if username:
                return username
            return session.get_username()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=cls.MODULE.value,
                event=f"{cls.MODULE.value}_current_user_resolve_failed",
            )
            return ""

    @classmethod
    def _point_in_layer_crs(cls, point: QgsPointXY, layer: QgsVectorLayer) -> QgsPointXY:
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
            transform = QgsCoordinateTransform(source_crs, target_crs, QgsProject.instance().transformContext())
            return transform.transform(point)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=cls.MODULE.value,
                event=f"{cls.MODULE.value}_point_transform_failed",
            )
            return point

    @classmethod
    def backend_geometry_payload_from_geometry(cls, geometry: Optional[QgsGeometry]) -> Optional[dict[str, object]]:
        return GeometryPayloadService.from_qgs_geometry(
            geometry,
            module=cls.MODULE.value,
            error_event=f"{cls.MODULE.value}_geometry_to_payload_failed",
        )

    @classmethod
    def resolve_main_layer(cls, *, dialogs: Optional[UserDialogs]) -> Optional[QgsVectorLayer]:
        lang = LanguageManager()
        identifier = SettingsService().module_main_layer_name(cls.MODULE.value) or ""
        matches = cls._configured_layers(identifier)
        if len(matches) > 1:
            if dialogs is not None:
                dialogs.show_warning(
                    lang.translate(TranslationKeys.ERROR),
                    lang.translate(cls.LAYER_AMBIGUOUS_KEY),
                )
            return None

        layer = matches[0] if matches else None
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            if dialogs is not None:
                dialogs.show_warning(
                    lang.translate(TranslationKeys.ERROR),
                    lang.translate(cls.LAYER_MISSING_KEY),
                )
            return None

        try:
            if str(identifier or "").strip() != str(layer.id() or "").strip():
                SettingsService().module_main_layer_name(cls.MODULE.value, value=layer.id())
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=cls.MODULE.value,
                event=f"{cls.MODULE.value}_layer_setting_id_migrate_failed",
                extra={"identifier": str(identifier or "")},
            )

        if cls.REQUIRED_GEOMETRY is not None and layer.geometryType() != cls.REQUIRED_GEOMETRY:
            if dialogs is not None:
                dialogs.show_warning(
                    lang.translate(TranslationKeys.ERROR),
                    lang.translate(cls.LAYER_INVALID_GEOMETRY_KEY),
                )
            return None

        return layer if cls._main_layer_is_ready(layer, lang=lang, dialogs=dialogs) else None

    @classmethod
    def _main_layer_is_ready(cls, layer: QgsVectorLayer, *, lang, dialogs: Optional[UserDialogs]) -> bool:
        """The module's own checks on a layer that passed the shared ones."""
        return True

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
            except RuntimeError:  # layer deleted since the project list was read
                continue
            if candidate and candidate.lower() == target:
                matches.append(layer)
        return matches


class AttachableLayerServiceBase(ModuleLayerServiceBase):
    """A module that attaches backend items to features on one configured layer: as-built, projects, easements.

    A service sets the names and texts below and writes its own attributes in `_write_item_attributes`.
    """

    DRAW_START_FAILED_KEY: str
    INVALID_LAYER_TEXT: str
    # (name, type) or (name, type, length): the fields an attach needs, added to the layer when missing.
    CUSTOM_FIELDS: tuple[tuple, ...]
    FIELDS_TEXTS: LayerEditTexts
    # The field the backend id is written to: the first one the layer has.
    ID_FIELD_CANDIDATES: tuple[str, ...]
    MISSING_ITEM_ID_TEXT: str
    FEATURE_NOT_FOUND_TEXT: str
    ATTACH_TEXTS: LayerEditTexts
    ATTACH_VERIFY_FAILED_TEXT: str

    # How a new drawing treats the item's feature already on the layer: an item keeps one feature.
    AREA_REPLACE = "replace"
    AREA_ADD_PART = "add_part"

    @classmethod
    def item_feature_ids(cls, layer: Optional[QgsVectorLayer], item_id: str) -> list[int]:
        """Ids of every feature carrying this item's backend id."""
        field_name = cls._resolve_first_field_name(layer, cls.ID_FIELD_CANDIDATES)
        item_id_text = str(item_id or "").strip()
        if not field_name or not item_id_text:
            return []
        try:
            return [
                int(feature.id())
                for feature in layer.getFeatures()
                if str(feature.attribute(field_name) or "").strip() == item_id_text
            ]
        except RuntimeError:  # the layer was deleted
            return []

    @staticmethod
    def allows_multi_part(layer: Optional[QgsVectorLayer]) -> bool:
        try:
            return bool(QgsWkbTypes.isMultiType(layer.wkbType()))
        except (AttributeError, RuntimeError):
            return False

    @classmethod
    def fold_existing_areas(
        cls, layer: QgsVectorLayer, *, keep_feature_id: int, item_id: str, mode: str
    ) -> tuple[bool, str]:
        """Leave the item one feature: the drawn one replaces the older ones or takes them in as parts.

        Works in the open edit session; the draw flow commits it, or rolls all of it back on failure.
        """
        keep_id = int(keep_feature_id)
        others = [feature_id for feature_id in cls.item_feature_ids(layer, item_id) if feature_id != keep_id]
        if not others or mode not in (cls.AREA_REPLACE, cls.AREA_ADD_PART):
            return True, ""
        if mode == cls.AREA_ADD_PART:
            if not cls.allows_multi_part(layer):
                return False, cls._layer_text(TranslationKeys.LAYER_EDIT_MULTIPART_NOT_ALLOWED)
            kept = cls._feature_by_id(layer, keep_id)
            if kept is None:
                return False, cls._layer_text(cls.FEATURE_NOT_FOUND_TEXT)
            combined = QgsGeometry(kept.geometry())
            for feature_id in others:
                older = cls._feature_by_id(layer, feature_id)
                if older is not None and not older.geometry().isEmpty():
                    combined = combined.combine(older.geometry())
            if combined.isNull() or combined.isEmpty():
                return False, cls._layer_text(TranslationKeys.LAYER_EDIT_JOIN_PART_FAILED)
            combined.convertToMultiType()
            if not layer.changeGeometry(keep_id, combined):
                return False, cls._layer_text(TranslationKeys.LAYER_EDIT_JOIN_PART_FAILED)
        for feature_id in others:
            if not layer.deleteFeature(feature_id):
                return False, cls._layer_text(TranslationKeys.LAYER_EDIT_REMOVE_OLD_FAILED)
        PythonFailLogger.log(
            f"{cls.MODULE.value}_existing_features_folded",
            module=cls.MODULE.value,
            extra={"item_id": str(item_id or ""), "mode": mode, "removed": len(others)},
        )
        return True, ""

    @classmethod
    def _ensure_custom_fields(cls, layer: Optional[QgsVectorLayer]) -> tuple[bool, str]:
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return False, cls._layer_text(cls.INVALID_LAYER_TEXT)
        existing = cls._field_map(layer)
        missing = [cls._custom_field(spec) for spec in cls.CUSTOM_FIELDS if spec[0].lower() not in existing]
        return cls._add_missing_fields(layer, missing, texts=cls.FIELDS_TEXTS)

    @staticmethod
    def _custom_field(spec: tuple) -> QgsField:
        name, field_type, *length = spec
        return QgsField(name, field_type, len=length[0]) if length else QgsField(name, field_type)

    @classmethod
    def attach_backend_item_to_feature(
        cls,
        *,
        layer: QgsVectorLayer,
        feature_id: int,
        item_id: str,
        item_data: Optional[dict] = None,
        value_problems: Optional[list[FieldValueProblem]] = None,
    ) -> tuple[bool, str]:
        """Links the feature to the backend item and saves it; (ok, layer label) or (False, why)."""
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return False, cls._layer_text(cls.INVALID_LAYER_TEXT)

        ok_fields, field_error = cls._ensure_custom_fields(layer)
        if not ok_fields:
            return False, field_error

        item_payload = item_data if isinstance(item_data, dict) else {}
        item_id_text = str(item_id or "").strip()
        if not item_id_text:
            return False, cls._layer_text(cls.MISSING_ITEM_ID_TEXT)

        feature_number = cls._feature_id_number(feature_id)
        if feature_number is None:
            return False, cls._feature_id_not_number_text(feature_id)
        feature_id = feature_number
        feature = cls._feature_by_id(layer, feature_id)
        if feature is None:
            return False, cls._layer_text(cls.FEATURE_NOT_FOUND_TEXT)

        cls._write_item_attributes(
            feature,
            layer=layer,
            item_id=item_id_text,
            item=item_payload,
            username=cls.current_username(),
            value_problems=value_problems,
        )

        def check_saved(saved_id: Optional[int]) -> tuple[bool, str]:
            if not cls._verify_attached(layer, feature_id=saved_id, item_id=item_id_text, item=item_payload):
                return False, cls._layer_text(cls.ATTACH_VERIFY_FAILED_TEXT)
            return True, cls._layer_target_label(layer)

        return cls._write_feature(
            layer,
            feature,
            add=False,
            texts=cls.ATTACH_TEXTS,
            log_extra={"item_id": item_id_text, "feature_id": feature_id},
            check_saved=check_saved,
        )

    @classmethod
    def _write_item_attributes(
        cls,
        feature: QgsFeature,
        *,
        layer: QgsVectorLayer,
        item_id: str,
        item: dict,
        username: str,
        value_problems: Optional[list[FieldValueProblem]],
    ) -> None:
        raise NotImplementedError

    @classmethod
    def _verify_attached(cls, layer: QgsVectorLayer, *, feature_id: Optional[int], item_id: str, item: dict) -> bool:
        """The saved feature itself carries the id. Another feature with the same id (an older link) does not count."""
        if feature_id is None:
            return False
        saved = cls._feature_by_id(layer, feature_id)
        id_field = cls._resolve_first_field_name(layer, cls.ID_FIELD_CANDIDATES)
        if saved is None or not id_field:
            return False
        return str(saved.attribute(id_field) or "").strip() == item_id

    @classmethod
    def _feature_id_number(cls, feature_id) -> Optional[int]:
        """The feature id as a number; None (logged) when it is not one."""
        try:
            return int(feature_id)
        except (TypeError, ValueError, OverflowError):
            PythonFailLogger.log(
                f"{cls.MODULE.value}_feature_id_not_number",
                module=cls.MODULE.value,
                extra={"feature_id": str(feature_id)},
            )
            return None

    @staticmethod
    def _feature_id_not_number_text(feature_id) -> str:
        return LanguageManager().translate(TranslationKeys.LAYER_FEATURE_ID_NOT_NUMBER).format(feature_id=feature_id)

    @classmethod
    def _fill_added_fields_if_empty(
        cls,
        feature: QgsFeature,
        *,
        layer: QgsVectorLayer,
        by_candidates: tuple[str, ...],
        date_candidates: tuple[str, ...],
        username: str,
        created,
        item_id: str,
        value_problems: Optional[list[FieldValueProblem]],
    ) -> None:
        # Who added the feature and when stays as it was on a feature that is linked again.
        added_by_field = cls._resolve_first_field_name(layer, by_candidates)
        added_date_field = cls._resolve_first_field_name(layer, date_candidates)
        try:
            if added_by_field and not str(feature.attribute(added_by_field) or "").strip():
                cls._set_attr_if_present(
                    feature, layer=layer, candidates=by_candidates, value=username, value_problems=value_problems
                )
            if added_date_field and not feature.attribute(added_date_field):
                cls._set_attr_if_present(
                    feature, layer=layer, candidates=date_candidates, value=created, value_problems=value_problems
                )
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=cls.MODULE.value,
                event=f"{cls.MODULE.value}_added_fields_set_failed",
                extra={"item_id": item_id},
            )

    @classmethod
    def prepare_layer_for_draw(
        cls, *, dialogs: Optional[UserDialogs]
    ) -> tuple[Optional[QgsVectorLayer], str]:
        layer = cls.resolve_main_layer(dialogs=dialogs)
        if layer is None:
            return None, ""

        ok, message = cls._ensure_custom_fields(layer)
        if ok:
            return layer, ""

        lang = LanguageManager()
        if dialogs is not None:
            dialogs.show_warning(
                lang.translate(TranslationKeys.ERROR),
                str(message or lang.translate(cls.DRAW_START_FAILED_KEY)),
            )
        return None, str(message or "")

    @staticmethod
    def _layer_target_label(layer: Optional[QgsMapLayer]) -> str:
        if layer is None:
            return ""
        try:
            return str(layer.name() or "").strip()
        except RuntimeError:  # layer deleted
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
    def _set_attr_if_present(
        cls,
        feature: QgsFeature,
        *,
        layer: QgsVectorLayer,
        candidates: tuple[str, ...],
        value,
        value_problems: Optional[list[FieldValueProblem]] = None,
    ) -> None:
        actual = cls._resolve_first_field_name(layer, candidates)
        if not actual:
            return
        field_index = layer.fields().indexFromName(actual)
        field = layer.fields()[field_index] if field_index >= 0 else None
        feature.setAttribute(actual, cls.coerce_value_for_field(field, value, value_problems))

    @classmethod
    def _feature_by_id(cls, layer: Optional[QgsVectorLayer], feature_id: int) -> Optional[QgsFeature]:
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return None

        try:
            feature = next(layer.getFeatures(QgsFeatureRequest(int(feature_id))), None)
            if feature is not None:
                return feature
        except (TypeError, ValueError, OverflowError, RuntimeError):  # bad id, or the layer was deleted
            pass

        try:
            target_id = int(feature_id)
            for candidate in layer.getFeatures():
                if int(candidate.id()) == target_id:
                    return candidate
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=cls.MODULE.value,
                event=f"{cls.MODULE.value}_feature_by_id_failed",
                # str: a bad id is what failed above, int() here would raise again from the log call.
                extra={"feature_id": str(feature_id)},
            )
        return None

    @classmethod
    def find_feature_at_point(cls, point: QgsPointXY, *, layer: Optional[QgsVectorLayer], radius_multiplier: float = 3.0):
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return None

        canvas = iface.mapCanvas() if iface is not None else None
        if canvas is None:
            return None

        try:
            search_radius = canvas.mapUnitsPerPixel() * float(radius_multiplier)
        except (RuntimeError, TypeError, ValueError, OverflowError):  # canvas deleted, or the radius is not a number
            search_radius = 0.0
        if search_radius <= 0:
            search_radius = 2.0

        layer_point = cls._point_in_layer_crs(point, layer)
        search_rect = QgsRectangle(
            layer_point.x() - search_radius,
            layer_point.y() - search_radius,
            layer_point.x() + search_radius,
            layer_point.y() + search_radius,
        )

        try:
            request = QgsFeatureRequest().setFilterRect(search_rect)
            point_geometry = QgsGeometry.fromPointXY(layer_point)
            closest_feature = None
            closest_distance = float("inf")
            for feature in layer.getFeatures(request):
                geometry = feature.geometry()
                if geometry is None or geometry.isEmpty():
                    continue
                if layer.geometryType() == QgsWkbTypes.PointGeometry:
                    try:
                        distance = geometry.distance(point_geometry)
                    except TypeError:
                        continue
                    if distance <= search_radius and distance < closest_distance:
                        closest_feature = feature
                        closest_distance = distance
                    continue
                try:
                    if geometry.contains(point_geometry) or geometry.intersects(point_geometry):
                        return feature
                except TypeError:
                    continue
            return closest_feature
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=cls.MODULE.value,
                event=f"{cls.MODULE.value}_feature_at_point_failed",
            )
            return None

    @classmethod
    def _geometry_in_layer_crs(cls, geometry: QgsGeometry, *, source_layer: QgsVectorLayer, target_layer: QgsVectorLayer) -> QgsGeometry:
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
                module=cls.MODULE.value,
                event=f"{cls.MODULE.value}_layer_geometry_transform_failed",
            )
        return transformed
