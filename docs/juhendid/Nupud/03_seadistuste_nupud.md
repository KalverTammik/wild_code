# Seadistuste nupud

See loend katab seadistuste mooduli kirjutavad ja dialooge avavad nupud. Märkeruudud, kihivalikud ja filtrieelistuste valikuväljad ei ole sellesse nupuloendisse arvestatud. Nuppude eeldused, katkestamine, andmemõju ja auditi tähelepanekud on failis [Seadistuste nuppude detailaudit](03_01_seadistuste_nuppude_detailaudit.md). Seadistuste sisuline ülevaade algab juhendist [Kavitro seadistuste mooduli kasutamine](../01_seadistuste_mooduli_kasutamine.md).

## Salvestamine ja lähtestamine

| Nupp | Asukoht | Lühikirjeldus |
|---|---|---|
| **Kinnita** | Seadistuste vaate alumine ühine jalus; ilmub salvestamata muudatuste korral | Salvestab korraga kasutaja, QGIS-i projekti ja moodulikaartide ootel muudatused. |
| **Lähtesta** | QGIS-i projekti baaskihtide kaardi ja iga mooduli seadistuskaardi päis | Eemaldab vastava kaardi salvestatud seadistuse kohe ja kinnitust küsimata. QGIS-i kihte ega nende objekte ei kustutata. |

## QGIS-i projekti baaskihid

| Nupp | Asukoht | Lühikirjeldus |
|---|---|---|
| **Ühenda Geospatiali kaudu** | Seadistused → QGIS-i projekti baaskihid | Avab Geospatiali abiga seadistamise selgituse ja kinnituse. |
| **OK** | Geospatiali abiga seadistamise teatedialoog | Võtab Geospatiali režiimi ootele; püsivaks salvestamiseks tuleb vajutada üldist **Kinnita** nuppu. |
| **Cancel / Tühista** | Sama dialoog | Sulgeb dialoogi režiimi muutmata. |
| **Vaata Geospatiali seadistust** | Baaskihtide kaart, kui Geospatiali režiim on valitud | Avab tegelikult režiimi väljalülitamise kinnituse; **OK** võtab käsitsi režiimi ootele. |
| **Lisa kaardistus** | Baaskihtide kaart, ühiskanalisatsiooni vastenduse osa | Lisab uue kanalisatsiooniliigi ja tunnuste vastenduse rea. |

## Moodulikihtide tööriistad

| Nupp | Asukoht | Lühikirjeldus |
|---|---|---|
| **Loo/lae ajutine Tööde GPKG kiht** | Seadistused → Tööd; ainult käsitsi režiimis | Loob või laadib tööde GeoPackage'i kihi ja salvestab selle kohe tööde põhikihiks. |
| **Loo/lae ajutine Projektide GPKG kiht** | Seadistused → Projektid; mõlemas seadistusrežiimis | Loob või laadib projektide GeoPackage'i kihi ja salvestab selle kohe projektide põhikihiks. |
| **Ava mapper** | Geospatiali režiimis iga kasutajale kuvatud mooduli seadistuskaart | Avab parajasti valitud põhikihi väljade vastendamise dialoogi. |
| **Kanna andmed üle** | Geospatiali mapperi dialoog | Töötleb kogu valitud lähtekihi ning muudab mooduli sihtkihti kohe pärast eraldi kinnitust. |
| **Cancel / Tühista** | Geospatiali mapperi dialoog | Sulgeb mapperi andmeid üle kandmata. |

## Moodulipõhiste lisaväärtuste nupud

| Nupp | Asukoht | Lühikirjeldus |
|---|---|---|
| **Hammasrattaikoon – vali väärtus** | Projektide seadistuskaardil lähtekausta, sihtkausta ja kausta nimetamise reegli kõrval; servituutide kaardil staatuste seose kõrval | Avab välja tüübile vastava kaustavalija või seadistusdialoogi. |
| **Tühjenda väärtus** ikoon | Eelmise nupu kõrval | Eemaldab ootel oleva lisaväärtuse; lõplikuks salvestamiseks tuleb vajutada üldist **Kinnita** nuppu. |
| **OK** | Kausta nimetamise reegli dialoog | Kinnitab valitud nimekomponentidest moodustatud reegli. |
| **Cancel / Tühista** | Kausta nimetamise reegli dialoog | Sulgeb reeglidialoogi muudatust rakendamata. |
| **OK** | Servituudi staatuste vastendamise dialoog | Võtab dialoogis valitud Kavitro ja QGIS-i staatuseväärtuste vasted ootele. |
| **Cancel / Tühista** | Servituudi staatuste vastendamise dialoog | Sulgeb vastenduse muudatuseta. |

## Kinnistute halduse seadistusnupud

Kinnistute seadistuskaardi haldusnupud on koondatud faili [Kinnistute nupud](04_kinnistute_nupud.md), sest nende põhifunktsioon on kinnistuandmete lisamine, eemaldamine ja parandamine, mitte seadistusväärtuse muutmine.

## Nupulaadsed, kuid sellest loendist eraldatud juhtelemendid

- vaikimisi avatava mooduli valik;
- Sisestuspaani ja Otsingupaani märkeruudud;
- põhi- ja arhiivikihi valijad;
- eelistatud staatuste, liikide ja tunnuste valijad;
- ühiskanalisatsiooni kaardistuse märkeruut ja rippvalikud.

Need on funktsionaalsed seadistusjuhtelemendid, kuid mitte eraldi käsunupud.

## Seotud detailaudit

- [Seadistuste nuppude detailaudit](03_01_seadistuste_nuppude_detailaudit.md)
