"""Properties of an easement: backend edges, labels, prices and the cut area on each property.

No dialog state and no widgets; the easement preview dialog and its mixins call these.
"""
from __future__ import annotations

from typing import Optional

from qgis.core import QgsDistanceArea, QgsProject, QgsUnitTypes

from ...constants.cadastral_fields import AreaUnit, Katastriyksus
from .easement_distance_rules import coerce_number

DEFAULT_CURRENCY = "EUR"


def normalize_area_unit(value: object) -> str:
    unit = str(value or "").strip().upper()
    if unit in ("M", "SQM"):
        return AreaUnit.M
    if unit == "H":
        return AreaUnit.H
    return AreaUnit.M


def normalize_currency(value: object) -> str:
    text = str(value or DEFAULT_CURRENCY).strip().upper()
    return text or DEFAULT_CURRENCY


def property_display_label(number: str, display_address: str = "") -> str:
    number_text = str(number or "").strip()
    address_text = str(display_address or "").strip()
    if address_text and number_text and address_text != number_text:
        return f"{address_text} — {number_text}"
    return address_text or number_text or "-"


def normalize_property_edge(edge: Optional[dict]) -> dict[str, object]:
    """One backend property edge (nested `node` or flat) in the shape the editor rows use."""
    edge = edge or {}
    node = edge.get("node") if isinstance(edge.get("node"), dict) else {}
    area = edge.get("area") if isinstance(edge.get("area"), dict) else {}
    price = edge.get("pricePerAreaUnit") if isinstance(edge.get("pricePerAreaUnit"), dict) else {}
    total = edge.get("totalPrice") if isinstance(edge.get("totalPrice"), dict) else {}

    number = str(node.get("cadastralUnitNumber") or edge.get("cadastralUnitNumber") or "").strip()
    property_id = str(node.get("id") or edge.get("id") or "").strip()
    display_address = str(node.get("displayAddress") or edge.get("displayAddress") or "").strip()

    return {
        "id": property_id,
        "cadastralUnitNumber": number,
        "displayAddress": display_address,
        "display": property_display_label(number, display_address),
        "area": {
            "size": coerce_number(area.get("size")),
            "unit": normalize_area_unit(area.get("unit")),
        },
        "pricePerAreaUnit": {
            "amount": coerce_number(price.get("amount")),
            "currencyCode": normalize_currency(price.get("currencyCode")),
        },
        "totalPrice": {
            "amount": coerce_number(total.get("amount")),
            "currencyCode": normalize_currency(total.get("currencyCode")),
        },
        "isPayable": bool(edge.get("isPayable")),
        "nextPaymentDate": str(edge.get("nextPaymentDate") or "").strip(),
    }


def calculate_total_amount(area_value: float, price_value: float) -> Optional[float]:
    try:
        if area_value <= 0 or price_value <= 0:
            return None
    except TypeError:
        return None
    return round(float(area_value) * float(price_value), 2)


def format_total_amount(value: Optional[float], currency_code: str) -> str:
    if value is None:
        return "–"
    return f"{value:.2f} {currency_code}".strip()


def format_area_display(square_meters: float, unit: str = AreaUnit.M) -> str:
    try:
        numeric = max(0.0, float(square_meters or 0.0))
    except (TypeError, ValueError, OverflowError):
        numeric = 0.0

    if unit == AreaUnit.H:
        return f"{numeric / 10000.0:.4f} ha"
    return f"{numeric:.2f} m²"


def format_property_label(number: str, feature=None) -> str:
    """'<address or place> — <number>' from the first filled address field, else the number."""
    if feature is not None:
        for fld in (
            Katastriyksus.l_aadress,
            Katastriyksus.ay_nimi,
            Katastriyksus.ov_nimi,
            Katastriyksus.mk_nimi,
        ):
            try:
                value = feature[fld]
                if value:
                    return f"{value} — {number}"
            except KeyError:
                continue
    return str(number or "")


def _ellipsoid_for(layer) -> str:
    """The project's ellipsoid; without one, planar for a projected layer and the CRS's own for degrees.

    Without an ellipsoid ("NONE", the default of a project without a CRS) the area is planar in the
    layer's units. That is right for a projected layer such as L-EST97, whose planar area is the
    cadastral one, but square degrees are then converted with the equator's factor: about twice the
    real area at Estonia's latitude.
    """
    ellipsoid = str(QgsProject.instance().ellipsoid() or "").strip()
    if ellipsoid and ellipsoid.upper() != "NONE":
        return ellipsoid
    if not layer.crs().isGeographic():
        return "NONE"
    return str(layer.crs().ellipsoidAcronym() or "").strip() or "EPSG:7030"


def measure_geometry_area_sqm(geometry, layer) -> float:
    """Area in square metres on the project ellipsoid, planar when that fails."""
    try:
        if geometry is None or geometry.isEmpty():
            return 0.0
    except (AttributeError, RuntimeError):
        return 0.0

    try:
        distance_area = QgsDistanceArea()
        distance_area.setSourceCrs(layer.crs(), QgsProject.instance().transformContext())
        distance_area.setEllipsoid(_ellipsoid_for(layer))
        measured = distance_area.measureArea(geometry)
        return max(0.0, float(distance_area.convertAreaMeasurement(measured, QgsUnitTypes.AreaSquareMeters)))
    except (AttributeError, RuntimeError, TypeError):
        try:
            return max(0.0, float(geometry.area()))
        except (AttributeError, TypeError, ValueError):
            return 0.0


def property_cut_areas(final_layer, property_layer) -> tuple[dict[str, float], float]:
    """(cut area on each selected property by tunnus, total cut area), in square metres."""
    try:
        final_features = list(final_layer.getFeatures())
    except (AttributeError, RuntimeError):
        final_features = []

    final_geometries = []
    total_final_area = 0.0
    for feature in final_features:
        try:
            geometry = feature.geometry()
        except (AttributeError, RuntimeError):
            geometry = None
        if geometry is None:
            continue
        final_geometries.append(geometry)
        total_final_area += measure_geometry_area_sqm(geometry, final_layer)

    calculated: dict[str, float] = {}
    try:
        property_features = list(property_layer.getSelectedFeatures())
    except (AttributeError, RuntimeError):
        property_features = []

    for feature in property_features:
        try:
            row_key = str(feature[Katastriyksus.tunnus] or "").strip()
        except KeyError:
            row_key = ""
        if not row_key:
            continue

        try:
            property_geometry = feature.geometry()
        except (AttributeError, RuntimeError):
            property_geometry = None
        if property_geometry is None:
            calculated[row_key] = 0.0
            continue

        property_area = 0.0
        for final_geometry in final_geometries:
            try:
                if not final_geometry.intersects(property_geometry):
                    continue
                clipped = final_geometry.intersection(property_geometry)
            except (AttributeError, TypeError):
                clipped = None
            if clipped is None:
                continue
            property_area += measure_geometry_area_sqm(clipped, final_layer)

        calculated[row_key] = property_area

    return calculated, total_final_area
