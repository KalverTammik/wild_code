"""
Cadastral field constants and mappings for Estonian property data.
This module contains field definitions for cadastral data processing.
"""

class Katastriyksus:
    """Field constants for cadastral property data (new format)."""
    #fid = "fid"               # Baasis olev id
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


class OldKatastriyksus:
    """Field constants for old format cadastral data."""
    tunnus = "TUNNUS"                            # Katastriüksuse tunnus
    hkood = "HKOOD"                              # Haldusüksuse kood
    mk_nimi = "MK_NIMI"                          # Maakonna nimetus
    ov_nimi = "OV_NIMI"                          # Omavalitsuse nimetus
    ay_nimi = "AY_NIMI"                          # Asustusüksuse nimetus
    l_aadress = "L_AADRESS"                      # Lahiaadress
    registr = "REGISTR"                          # Katastriüksuse esmaregistreerimise kuupäev
    muudet = "MUUDET"                            # Katastriüksuse viimase muudatuse kuupäev
    siht1 = "SIHT1"                              # 1. sihtostarve
    siht2 = "SIHT2"                              # 2. sihtostarve
    siht3 = "SIHT3"                              # 3. sihtostarve
    so_prts1 = "SO_PRTS1"                        # 1. sihtostarbe protsent
    so_prts2 = "SO_PRTS2"                        # 2. sihtostarbe protsent
    so_prts3 = "SO_PRTS3"                        # 3. sihtostarbe protsent
    pindala = "PINDALA"                          # Katastriüksuse pindala
    haritav = "HARITAV"                          # Haritava maa kõlvik
    rohumaa = "ROHUMAA"                          # Loodusliku rohumaa kõlvik
    mets = "METS"                                # Metsamaa kõlvik
    ouemaa = "OUEMAA"                            # Õuemaa kõlvik
    muumaa = "MUUMAA"                            # Muu maa kõlvik
    kinnistu = "KINNISTU"                        # Kinnistu registriosa number
    omvorm = "OMVORM"                            # Katastriüksuse omandivorm
    maks_hind = "MAKS_HIND"                      # Maa-ameti arvutatud maaüksuse maksustamishind €
    marked = "MARKETEKST"                        # Katastriüksuse märked
    eksport = "EKSPORT"                          # Katastriüksuse märked


class KatasterMappings:
    """Field mapping between old and new cadastral data formats."""
    field_mapping = {
        OldKatastriyksus.tunnus: Katastriyksus.tunnus,
        OldKatastriyksus.hkood: Katastriyksus.hkood,
        OldKatastriyksus.mk_nimi: Katastriyksus.mk_nimi,
        OldKatastriyksus.ov_nimi: Katastriyksus.ov_nimi,
        OldKatastriyksus.ay_nimi: Katastriyksus.ay_nimi,
        OldKatastriyksus.l_aadress: Katastriyksus.l_aadress,
        OldKatastriyksus.registr: Katastriyksus.registr,
        OldKatastriyksus.muudet: Katastriyksus.muudet,
        OldKatastriyksus.siht1: Katastriyksus.siht1,
        OldKatastriyksus.siht2: Katastriyksus.siht2,
        OldKatastriyksus.siht3: Katastriyksus.siht3,
        OldKatastriyksus.so_prts1: Katastriyksus.so_prts1,
        OldKatastriyksus.so_prts2: Katastriyksus.so_prts2,
        OldKatastriyksus.so_prts3: Katastriyksus.so_prts3,
        OldKatastriyksus.pindala: Katastriyksus.pindala,
        OldKatastriyksus.haritav: Katastriyksus.haritav,
        OldKatastriyksus.rohumaa: Katastriyksus.rohumaa,
        OldKatastriyksus.mets: Katastriyksus.mets,
        OldKatastriyksus.ouemaa: Katastriyksus.ouemaa,
        OldKatastriyksus.muumaa: Katastriyksus.muumaa,
        OldKatastriyksus.kinnistu: Katastriyksus.kinnistu,
        OldKatastriyksus.omvorm: Katastriyksus.omvorm,
        OldKatastriyksus.maks_hind: Katastriyksus.maks_hind,
        OldKatastriyksus.marked: Katastriyksus.marked,
        OldKatastriyksus.eksport: Katastriyksus.eksport
    }


class Purpose:
    """Purpose constants for land use classification."""
    transport = "TRANSPORDIMAA"
