"""
Cadastral field constants and mappings for Estonian property data.
This module contains field definitions for cadastral data processing.
"""

from typing import Iterable, Tuple, List

from qgis.core import QgsVectorLayer

class Katastriyksus:
    """Field constants for cadastral property data (new format)."""
    fid = "fid"               # Baasis olev id
    tunnus = "tunnus"          # Katastriüksuse tunnus
    hkood = "hkood"            # Asustusüksuse kood
    mk_nimi = "mk_nimi"        # Maakonna nimetus
    ov_nimi = "ov_nimi"        # Omavalitsuse nimetus
    ay_nimi = "ay_nimi"        # Asustusüksuse nimetus
    l_aadress = "l_aadress"    # Lahiaadress
    registr = "registr"        # Katastriüksuse esmaregistreerimise kuupäev
    muudet = "muudet"          # Katastriüksuse viimase muudatuse kuupäev
    siht1 = "siht1"            # 1. sihtostarve
    siht2 = "siht2"            # 2. sihtostarve
    siht3 = "siht3"            # 3. sihtostarve
    so_prts1 = "so_prts1"      # 1. sihtostarbe protsent
    so_prts2 = "so_prts2"      # 2. sihtostarbe protsent
    so_prts3 = "so_prts3"      # 3. sihtostarbe protsent
    pindala = "pindala"        # Katastriüksuse pindala
    haritav = "haritav"        # Haritava maa kõlvik
    rohumaa = "rohumaa"        # Loodusliku rohumaa kõlvik
    mets = "mets"              # Metsamaa kõlvik
    ouemaa = "ouemaa"          # Õuemaa kõlvik
    muumaa = "muumaa"          # Muu maa kõlvik
    kinnistu = "kinnistu"      # Kinnistu registriosa number
    #muutpohjus = "muutpohjus" # Katatastriüksuse viimane muudatus   new
    omvorm = "omvorm"          # Katastriüksuse omandivorm
    maks_hind = "maks_hind"    # Maatüki maksustamishind
    marked = "marked"          # Katastriüksuse märked
    #ads_oid = "ads_oid"        # ADS objekti identifikaator, identifitseerib objekti läbi versioonide. new
    #adob_id = "adob_id"        # Aadressiobjekti versiooni unikaalne identifikaator (unikaalne üle kõikide objektide kõikide versioonide).   new
    #oiguslik_alus = "oiguslik_alus"  # Katastriüksuse viimase muudatuse õiguslik alus  new
    eksport = "eksport"        # Andmete väljavõtte kuupäev

    # Field lists for different purposes
    FieldsForTables = [tunnus, registr, ay_nimi, l_aadress, siht1, so_prts1, siht2, so_prts2, siht3, so_prts3, omvorm]
    search_field = "search_field"
    search_field_items = [tunnus, l_aadress, ay_nimi, ov_nimi, mk_nimi]


class Purpose:
    """Purpose constants for land use classification."""
    transport = "TRANSPORDIMAA"



class AreaUnit:
    M = "SQM"
    H = "H"
