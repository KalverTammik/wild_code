"""Helpers to compare layer fields against Maa-amet logical schemas."""

from typing import Iterable, List, Tuple

from qgis.core import QgsVectorLayer

from ...constants.cadastral_fields import Katastriyksus


class MaaAmetFieldComparer:
    """Shared helpers to compare a layer's fields against Maa-amet logical definitions."""

    @staticmethod
    def logical_fields() -> Tuple[List[str], List[str]]:
        """Return required and optional logical field names for cadastral data."""
        logical_required = [
            Katastriyksus.tunnus,
            Katastriyksus.l_aadress,
            Katastriyksus.ay_nimi,
            Katastriyksus.ov_nimi,
            Katastriyksus.mk_nimi,
            Katastriyksus.registr,
            Katastriyksus.muudet,
            Katastriyksus.pindala,
            Katastriyksus.siht1,
            Katastriyksus.siht2,
            Katastriyksus.siht3,
            Katastriyksus.so_prts1,
            Katastriyksus.so_prts2,
            Katastriyksus.so_prts3,
            Katastriyksus.maks_hind,
        ]
        logical_optional = [
            Katastriyksus.haritav,
            Katastriyksus.rohumaa,
            Katastriyksus.mets,
            Katastriyksus.ouemaa,
            Katastriyksus.muumaa,
            Katastriyksus.kinnistu,
            Katastriyksus.omvorm,
            Katastriyksus.marked,
            Katastriyksus.eksport,
        ]
        return logical_required, logical_optional

    @staticmethod
    def compare_layer_fields(
        layer: QgsVectorLayer,
        mapping: dict,
        logical_required: Iterable[str],
        logical_optional: Iterable[str],
        *,
        label_extra: str,
        status_mapped: str,
        status_missing: str,
        status_unmapped: str,
        status_extra: str,
        note_required: str,
        note_optional: str,
        note_extra: str,
        source_stored: str,
        source_auto: str,
    ) -> Tuple[List[dict], List[str], List[str]]:
        """Compare a layer's fields against required/optional logical fields.

        Returns rows for UI, plus lists of missing required and optional fields.
        """

        logical_required = list(logical_required)
        logical_optional = list(logical_optional)

        actual = {f.name(): f.name() for f in layer.fields()}
        actual_ci = {name.lower(): name for name in actual}

        def resolve(logical: str):
            if logical in mapping:
                target = mapping[logical]
                if target and target in actual:
                    return target
            if logical in actual:
                return logical
            return actual_ci.get(logical.lower())

        missing_required = [f for f in logical_required if resolve(f) is None]
        missing_optional = [f for f in logical_optional if resolve(f) is None]

        rows: List[dict] = []

        def add_row(logical: str, mapped: str, status: str, note: str = "") -> None:
            rows.append({"logical": logical, "mapped": mapped, "status": status, "note": note})

        for logical in logical_required:
            target = resolve(logical)
            if target:
                source = source_stored if logical in mapping else source_auto
                add_row(logical, target, status_mapped, source)
            else:
                add_row(logical, "", status_missing, note_required)

        for logical in logical_optional:
            target = resolve(logical)
            if target:
                source = source_stored if logical in mapping else source_auto
                add_row(logical, target, status_mapped, source)
            else:
                add_row(logical, "", status_unmapped, note_optional)

        extras = [
            name
            for name in actual
            if name.lower() not in {f.lower() for f in logical_required + logical_optional}
        ]
        for ex in sorted(extras):
            add_row(label_extra, ex, status_extra, note_extra)

        return rows, missing_required, missing_optional

    @staticmethod
    def compare_against_target(
        shp_layer: QgsVectorLayer,
        target_layer: QgsVectorLayer,
        target_label: str,
        *,
        label_extra: str,
        status_mapped: str,
        status_missing: str,
        status_extra: str,
        note_target_only: str,
    ) -> Tuple[List[dict], int, int]:
        """Compare SHP layer fields against a target layer.

        Returns rows plus counts of missing and extra fields on the target.
        """

        shp_fields = {f.name(): f.name() for f in shp_layer.fields()}
        shp_ci = {n.lower() for n in shp_fields}
        target_fields = {f.name(): f.name() for f in target_layer.fields()}
        target_ci = {n.lower(): n for n in target_fields}

        rows: List[dict] = []

        def add_row(logical: str, mapped: str, status: str, note: str = "") -> None:
            rows.append({"logical": logical, "mapped": mapped, "status": status, "note": note})

        missing_in_target: List[str] = []
        for shp_name in sorted(shp_fields):
            if shp_name.lower() in target_ci:
                add_row(shp_name, target_ci[shp_name.lower()], status_mapped, target_label)
            else:
                missing_in_target.append(shp_name)
                add_row(shp_name, "", status_missing, target_label)

        extras_in_target: List[str] = []
        for tgt_name in sorted(target_fields):
            if tgt_name.lower() not in shp_ci:
                extras_in_target.append(tgt_name)
                add_row(label_extra, tgt_name, status_extra, note_target_only)

        return rows, len(missing_in_target), len(extras_in_target)
