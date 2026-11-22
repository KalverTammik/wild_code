"""Buffer distance rules of the easement preview: how wide the easement around a network is.

No dialog state: the layers come in as arguments and the buffer distance chosen in the
dialog is passed as `default_depth`, used when a pipe has no depth value.
"""
from __future__ import annotations

import re
from typing import Optional

from ...utils.project_base_layers import ProjectBaseLayerKeys

FIXED_DISTANCE_BY_ROW = {
    ProjectBaseLayerKeys.SEWAGE_DUMP: 30.0,
    ProjectBaseLayerKeys.SEWAGE_PLANT: 30.0,
    ProjectBaseLayerKeys.WATER_STATION: 30.0,
}

PUMP_ROWS = {ProjectBaseLayerKeys.SEWAGE_PUMPING, ProjectBaseLayerKeys.RAIN_PUMP}

DIAMETER_FIELD_CANDIDATES = (
    "Läbimõõt, mm",
    "Läbimõõt",
    "Siseläbimõõt",
    "Diameeter",
    "Diameter",
    "DN",
)

DEPTH_FIELD_CANDIDATES = (
    "Sügavus",
    "Rajamissügavus",
    "Paigaldussügavus",
    "Lähtekõrgus",
    "Lõppkõrgus",
    "Alguskõrgus",
    "Loppkorgus",
    "Lahtekorgus",
    "Depth",
)

FLOW_FIELD_CANDIDATES = (
    "Vooluhulk",
    "Vooluhulk, m3/d",
    "Vooluhulk m3/d",
    "Flow",
    "Capacity",
    "Tootlikkus",
    "Q",
)


def normalize_field_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").casefold())


def coerce_number(value) -> Optional[float]:
    """The first number in `value` as a positive float, or None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return abs(float(value))
        except (TypeError, ValueError, OverflowError):
            return None

    text = str(value or "").strip()
    if not text:
        return None
    text = text.replace("\xa0", " ").replace(",", ".")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    try:
        return abs(float(match.group(0)))
    except ValueError:
        return None


def format_distance(value: float) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError, OverflowError):
        return str(value)
    if abs(numeric - round(numeric)) < 0.001:
        return str(int(round(numeric)))
    return f"{numeric:.1f}".rstrip("0").rstrip(".")


def find_field_names(layer, candidates: tuple[str, ...]) -> list[str]:
    """Fields of `layer` whose name equals or contains a candidate (letters and digits only)."""
    if layer is None:
        return []

    normalized_candidates = [normalize_field_name(candidate) for candidate in candidates if candidate]
    matched: list[str] = []
    try:
        fields = layer.fields()
    except (AttributeError, RuntimeError):
        return matched

    for field in fields:
        field_name = field.name()
        normalized_field = normalize_field_name(field_name)
        if normalized_field in normalized_candidates:
            matched.append(field_name)
            continue
        if any(candidate and candidate in normalized_field for candidate in normalized_candidates):
            matched.append(field_name)
    return matched


def feature_is_pressure_pipe(layer_key: str, feature, source_layer) -> bool:
    if layer_key == ProjectBaseLayerKeys.PRESSURE_SEWERPIPES:
        return True
    field_names = find_field_names(source_layer, ("Survetoru",))
    for field_name in field_names:
        value = feature[field_name]
        if value in (True, 1, "1", "true", "True"):
            return True
    return False


def flow_based_distance(source_layer) -> float:
    """Pumps: 20 m when a selected feature moves more than 10 (m3/d), otherwise 10 m."""
    flow_fields = find_field_names(source_layer, FLOW_FIELD_CANDIDATES)
    max_flow = None
    try:
        selected_features = list(source_layer.getSelectedFeatures())
    except (AttributeError, RuntimeError):
        selected_features = []

    for feature in selected_features:
        flow = next(
            (coerce_number(feature[field_name]) for field_name in flow_fields if coerce_number(feature[field_name]) is not None),
            None,
        )
        if flow is None:
            continue
        max_flow = flow if max_flow is None else max(max_flow, flow)

    if max_flow is not None and max_flow > 10.0:
        return 20.0
    return 10.0


def suggest_distance(
    *,
    diameter: Optional[float],
    depth: Optional[float],
    is_pressure: bool,
    default_depth: float,
) -> Optional[float]:
    """Easement width of one pipe from its diameter (mm) and depth (m)."""
    if diameter is None:
        return None

    if is_pressure:
        if diameter < 250:
            return 2.0
        if diameter < 500:
            return 2.5
        return 3.0

    depth_value = depth if depth is not None else float(default_depth)
    if diameter < 250:
        return 2.0 if depth_value <= 2.0 else 2.5
    if diameter < 1000:
        return 2.5 if depth_value <= 2.0 else 3.0
    return 2.5 if depth_value <= 2.0 else 5.0


def row_distance(layer_key: str, source_layer, *, default_depth: float) -> Optional[float]:
    """Distance rule of one network row for its selected features, or None when no rule applies."""
    if source_layer is None:
        return None

    if layer_key in FIXED_DISTANCE_BY_ROW:
        return float(FIXED_DISTANCE_BY_ROW[layer_key])

    if layer_key in PUMP_ROWS:
        return flow_based_distance(source_layer)

    diameter_fields = find_field_names(source_layer, DIAMETER_FIELD_CANDIDATES)
    depth_fields = find_field_names(source_layer, DEPTH_FIELD_CANDIDATES)
    if not diameter_fields:
        return None

    max_distance: Optional[float] = None

    try:
        selected_features = list(source_layer.getSelectedFeatures())
    except (AttributeError, RuntimeError):
        selected_features = []

    for feature in selected_features:
        diameter = next(
            (coerce_number(feature[field_name]) for field_name in diameter_fields if coerce_number(feature[field_name]) is not None),
            None,
        )
        depth_values = [
            numeric
            for numeric in (coerce_number(feature[field_name]) for field_name in depth_fields)
            if numeric is not None
        ]
        depth = max(depth_values) if depth_values else None
        distance = suggest_distance(
            diameter=diameter,
            depth=depth,
            is_pressure=feature_is_pressure_pipe(layer_key, feature, source_layer),
            default_depth=default_depth,
        )
        if distance is None:
            continue
        max_distance = distance if max_distance is None else max(max_distance, distance)

    return max_distance
