from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


def _clean(values: Iterable[object] | None) -> frozenset[str]:
    cleaned = set()
    for value in values or ():
        if value is None:
            continue
        text = str(value).strip()
        if text and text.upper() != "NULL":
            cleaned.add(text)
    return frozenset(cleaned)


@dataclass(frozen=True)
class PropertyArchiveScope:
    county: str
    municipality: str
    settlements: tuple[str, ...]
    import_tunnused: frozenset[str]
    import_layer_id: str
    import_layer_source: str
    complete: bool
    blocked_reason: str = ""

    @classmethod
    def create(
        cls,
        *,
        county: object,
        municipality: object,
        settlements: Iterable[object] | None,
        import_tunnused: Iterable[object] | None,
        import_layer_id: object = "",
        import_layer_source: object = "",
        load_succeeded: bool,
    ) -> "PropertyArchiveScope":
        county_text = str(county or "").strip()
        municipality_text = str(municipality or "").strip()
        settlement_values = tuple(sorted(_clean(settlements)))
        tunnus_values = _clean(import_tunnused)

        reason = ""
        if not load_succeeded:
            reason = "scope_load_failed"
        elif not county_text or not municipality_text or not settlement_values:
            reason = "explicit_settlements_required"
        elif not tunnus_values:
            # An empty table can mean either a genuinely empty settlement or a failed/
            # partial source. It is not safe evidence for archiving every old feature.
            reason = "empty_import_scope"

        return cls(
            county=county_text,
            municipality=municipality_text,
            settlements=settlement_values,
            import_tunnused=tunnus_values,
            import_layer_id=str(import_layer_id or "").strip(),
            import_layer_source=str(import_layer_source or "").strip(),
            complete=not bool(reason),
            blocked_reason=reason,
        )

    @property
    def key(self) -> tuple[str, str, tuple[str, ...]]:
        return (self.county, self.municipality, self.settlements)

    @property
    def identity(self) -> tuple[object, ...]:
        return (
            self.county,
            self.municipality,
            self.settlements,
            tuple(sorted(self.import_tunnused)),
            self.import_layer_id,
            self.import_layer_source,
            self.complete,
            self.blocked_reason,
        )


@dataclass(frozen=True)
class PropertyArchiveClassification:
    candidates: frozenset[str]
    moved_elsewhere: frozenset[str]
    blocked_reason: str = ""

    @property
    def blocked(self) -> bool:
        return bool(self.blocked_reason)


def classify_archive_candidates(
    *,
    scope: PropertyArchiveScope,
    main_scope_tunnused: Iterable[object] | None,
    import_tunnused_found_elsewhere: Iterable[object] | None,
) -> PropertyArchiveClassification:
    """Classify missing properties without depending on QGIS or the backend.

    ``main_scope_tunnused`` must already be limited to the exact county,
    municipality and settlements stored in ``scope``. The final argument is a
    targeted lookup result for preliminary candidates across the full import
    layer. A match there is treated as a location change and is not archived.
    """

    if not scope.complete:
        return PropertyArchiveClassification(
            candidates=frozenset(),
            moved_elsewhere=frozenset(),
            blocked_reason=scope.blocked_reason or "incomplete_scope",
        )

    main_values = _clean(main_scope_tunnused)
    preliminary = main_values.difference(scope.import_tunnused)
    moved_elsewhere = preliminary.intersection(_clean(import_tunnused_found_elsewhere))
    return PropertyArchiveClassification(
        candidates=frozenset(preliminary.difference(moved_elsewhere)),
        moved_elsewhere=frozenset(moved_elsewhere),
    )
