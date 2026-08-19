# Funktsionaalsete nuppude koondkaart

See kataloog koondab Visuaali ehk Kavitro QGIS-i plugina kasutajale nähtavad funktsionaalsed nupud ja menüütoimingud. Iga nupu juures on lühidalt kirjas, mida see teeb ja kus see asub. Nuppude detailne käitumine, eeldused, veateed ja andmemuudatused auditeeritakse teemade kaupa nummerdatud alamfailides.

## Kaardistuse ulatus

Kaardistusse kuuluvad:

- teksti- ja ikooninupud;
- QGIS-i tööriistariba plugina nupp;
- kirjekaardi **Rohkem toiminguid** menüü käsud;
- nupuna käituvad detaili-, staatuse- ja jaotiseavamise juhtelemendid;
- korduvkasutatavate faili-, valiku- ja kinnitusedialoogide nupud.

Eraldi nupuna ei kaardistata tekstivälju, rippmenüüsid, märkeruute, tabeliridu ega tavalisi veebiteksti linke. Kui selline juhtelement käitub kasutaja jaoks nupuna, on see vastavas failis märgitud nupulaadse juhtelemendina.

## Grupeerimise reegel

Sama tehnilise ja kasutusliku tähendusega nupp kirjeldatakse üks kord. Näiteks kirjekaartidel korduvad **Ava kaust**, **Ava kirje brauseris**, **Näita kirjeid kaardil** ja **Rohkem toiminguid** on koondatud ühiste kirjekaardinuppude faili. Moodulipõhises failis näidatakse ainult seda, millised neist selles moodulis esinevad, ning kirjeldatakse mooduli enda lisatoiminguid.

## Sisukord

| Fail | Kaetud nupurühmad |
|---|---|
| [Üldnupud ja navigeerimine](01_uldnupud_ja_navigeerimine.md) | Plugina avamine, sisselogimine, päis, külgriba, otsing ja QGIS-i kaardipaanid |
| ↳ [Üldnuppude ja navigeerimise detailaudit](01_01_uldnuppude_ja_navigeerimise_detailaudit.md) | Faili `01` nuppude eeldused, täpne käitumine, andmemõju, katkestamine ja veateed |
| [Loendid, filtrid ja kirjekaardid](02_loendid_filtrid_ja_kirjekaardid.md) | Filtrid, tähtajanupud, detailivaade ja ühised kirjekaarditoimingud |
| ↳ [Filtrite nuppude detailaudit](02_01_filtrite_nuppude_detailaudit.md) | Faili `02` filtrite, värskendamise, tühjendamise ja tähtaja kiirnuppude detailne käitumine |
| [Seadistuste nupud](03_seadistuste_nupud.md) | Salvestamine, lähtestamine, Geospatial, mapper ning moodulipõhised seadistusnupud |
| ↳ [Seadistuste nuppude detailaudit](03_01_seadistuste_nuppude_detailaudit.md) | Faili `03` nuppude salvestushetk, katkestamine, QGIS-i andmemõju, veateed ja auditi leiud |
| [Kinnistute nupud](04_kinnistute_nupud.md) | Kinnistu avamine, kinnistute haldus, lisamine, eemaldamine ja arhiveerimine |
| ↳ [Kinnistute nuppude detailaudit](04_01_kinnistute_nuppude_detailaudit.md) | Faili `04` kaardivaliku, SHP-impordi, lisamise, arhiveerimise, kustutamise ja otsinguvälja tegelik käitumine |
| [Projektide nupud](05_projektide_nupud.md) | Projektikaart, projektikaust, ala joonistamine ja eelvaade |
| ↳ [Projektide nuppude detailaudit](05_01_projektide_nuppude_detailaudit.md) | Faili `05` projektitahvli, kausta, kaardifookuse, kinnistuseoste ja projektiala töövoogude tegelik käitumine |
| [Lepingute ja kooskõlastuste nupud](06_lepingute_ja_kooskolastuste_nupud.md) | Tähtajad, kirjekaardid ja kinnistute sidumine |
| ↳ [Lepingute ja kooskõlastuste nuppude detailaudit](06_01_lepingute_ja_kooskolastuste_nuppude_detailaudit.md) | Faili `06` detailvaate, failide, väliste avamiste, kaardifookuse ja kinnistuseoste tegelik käitumine |
| [Servituutide nupud](07_servituutide_nupud.md) | Geomeetria, failid, eelvaade, PDF-skeem ja kinnistuandmed |
| ↳ [Servituutide nuppude detailaudit](07_01_servituutide_nuppude_detailaudit.md) | Faili `07` detailvaate, geomeetria, kinnistute, eelvaadete, failide ja PDF-skeemi töövoogude tegelik käitumine |
| [Tööde ja teostusjooniste nupud](08_toode_ja_teostusjooniste_nupud.md) | Töö loomine, GIS-punktid, asukoht, märkmed ja geomeetria |
| ↳ [Tööde ja teostusjooniste nuppude detailaudit](08_01_toode_ja_teostusjooniste_nuppude_detailaudit.md) | Faili `08` kirjekaardi, staatuse, tööpunktide, sidumata GIS-tööde, märkmete ja teostusjoonise geomeetria töövoogude tegelik käitumine |
| [Failide ja ühisdialoogide nupud](09_failide_ja_uhisdialoogide_nupud.md) | Failihaldus, eelvaade, kinnistuseoste kontroll ning ühised kinnitamis- ja sulgemisnupud |
| ↳ [Failide ja ühisdialoogide nuppude detailaudit](09_01_failide_ja_uhisdialoogide_nuppude_detailaudit.md) | Faili `09` failikokkuvõtte, täieliku failihalduse, eelvaate, kinnistuseoste, teadete ja edenemisdialoogi tegelik käitumine |

## Detailauditi kontrollpunktid

Iga nupu detailauditis kontrollitakse vähemalt:

1. millal nupp on nähtav ja aktiivne;
2. milliseid seadistusi, õigusi ja andmeid see eeldab;
3. millise dialoogi või kaarditööriista see avab;
4. milliseid QGIS-i või Kavitro andmeid see muudab;
5. kuidas toimingut katkestada või tagasi võtta;
6. millised on osalise õnnestumise ja vea olukorrad;
7. millise olemasoleva kasutusjuhendiga nupp seostub.

## Kaardistuse alus

Loend on koostatud kasutajaliidese nupuklasside, menüütoimingute, klõpsusignaalide, eestikeelsete tõlgete ja olemasolevate juhendite põhjal. Koondkaart kirjeldab praegust koodibaasi; uue nupu lisamisel või olemasoleva eemaldamisel tuleb uuendada nii vastavat teemafaili kui ka seda sisukorda.
