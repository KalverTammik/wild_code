"""Layer reads and row mapping behind the add-property dialog's archive plan.

No dialog state and no widgets: the dialog passes in the layers, the scope and the
translator. Read errors raise RuntimeError so the caller can block the plan.
"""
from __future__ import annotations

from typing import Callable

from qgis.core import QgsFeatureRequest

from ....constants.cadastral_fields import Katastriyksus
from ....languages.translation_keys import TranslationKeys
from ....utils.property.PropertyDataLoader import PropertyDataLoader
from .property_archive_plan import PropertyArchiveScope


def layer_identity(layer) -> tuple[str, str]:
    """(id, source) of a layer; empty strings for None, a non-layer or a deleted layer."""
    if layer is None:
        return ("", "")
    try:
        layer_id = str(layer.id() or "")
    except (AttributeError, RuntimeError):  # not a layer, or deleted
        layer_id = ""
    try:
        source = str(layer.source() or "")
    except (AttributeError, RuntimeError):  # not a layer, or deleted
        source = ""
    return (layer_id, source)


def read_scope_features(layer, scope: PropertyArchiveScope) -> dict[str, object]:
    """Features of `layer` inside the scope's county, municipality and settlements, by tunnus."""
    if layer is None or not layer.isValid():
        raise RuntimeError("scope layer is missing or invalid")
    required = (
        Katastriyksus.tunnus,
        Katastriyksus.mk_nimi,
        Katastriyksus.ov_nimi,
        Katastriyksus.ay_nimi,
    )
    missing_fields = [name for name in required if layer.fields().lookupField(name) < 0]
    if missing_fields:
        raise RuntimeError(f"scope fields missing: {', '.join(missing_fields)}")

    expression = PropertyDataLoader.build_scope_expression(
        county_name=scope.county,
        municipality_name=scope.municipality,
        settlements=scope.settlements,
    )
    request = QgsFeatureRequest()
    request.setFilterExpression(expression)
    request.setFlags(QgsFeatureRequest.Flag.NoGeometry)
    result: dict[str, object] = {}
    for feature in layer.getFeatures(request):
        tunnus = str(feature.attribute(Katastriyksus.tunnus) or "").strip()
        if tunnus and tunnus not in result:
            result[tunnus] = feature
    return result


def find_import_tunnused(import_layer, tunnused: set[str]) -> set[str]:
    """Which of `tunnused` the import layer holds anywhere (also outside the scope)."""
    if not tunnused:
        return set()
    if import_layer is None or not import_layer.isValid():
        raise RuntimeError("import layer is missing or invalid")
    if import_layer.fields().lookupField(Katastriyksus.tunnus) < 0:
        raise RuntimeError(f"import field missing: {Katastriyksus.tunnus}")

    expression = PropertyDataLoader._in_expr(Katastriyksus.tunnus, sorted(tunnused))
    request = QgsFeatureRequest()
    request.setFilterExpression(expression)
    request.setFlags(QgsFeatureRequest.Flag.NoGeometry)
    found = set()
    for feature in import_layer.getFeatures(request):
        tunnus = str(feature.attribute(Katastriyksus.tunnus) or "").strip()
        if tunnus in tunnused:
            found.add(tunnus)
    return found


def archive_candidate_row(
    tunnus: str,
    backend_info,
    *,
    settlement: str,
    translate: Callable[[str], str],
) -> dict:
    """Map one background lookup result to a plan row; only one active match may be archived."""
    row = {
        "tunnus": tunnus,
        "settlement": settlement,
        "backend_allowed": False,
        "backend_label": translate(TranslationKeys.PROPERTY_ARCHIVE_PLAN_BACKEND_FAILED),
        "note": "",
    }
    if not isinstance(backend_info, dict) or backend_info.get("exists") is None:
        row["note"] = translate(TranslationKeys.PROPERTY_ARCHIVE_PLAN_BACKEND_FAILED)
        return row

    active_ids = [
        str(value).strip()
        for value in (backend_info.get("active_ids") or [])
        if str(value).strip()
    ]
    active_count = backend_info.get("active_count")
    if (isinstance(active_count, int) and active_count > 1) or len(active_ids) > 1:
        row["backend_label"] = translate(TranslationKeys.PROPERTY_ARCHIVE_PLAN_BACKEND_MULTIPLE)
    elif len(active_ids) == 1:
        row["backend_allowed"] = True
        row["backend_label"] = translate(TranslationKeys.PROPERTY_ARCHIVE_PLAN_BACKEND_ARCHIVE)
    else:
        row["backend_label"] = translate(TranslationKeys.PROPERTY_ARCHIVE_PLAN_BACKEND_MISSING)
    return row
