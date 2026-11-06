"""Helpers to compare layer fields against Maa-amet logical schemas."""

from typing import List, Tuple


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
