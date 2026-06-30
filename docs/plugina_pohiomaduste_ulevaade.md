# Kavitro Plugina Põhiomaduste Ülevaade

## Lühikokkuvõte

Kavitro plugin on QGIS-i integreeritud tööriist, mis seob kaardi, Kavitro backendist tulevad objektid ja moodulipõhised töövood ühtseks töökeskkonnaks.

Plugin ei ole ainult andmete vaatur. Selle eesmärk on vähendada käsitsi liikumist QGIS-i, failihalduse ja põhirakenduse vahel ning hoida ruumiandmed seotud äriloogikaga.

## Milleks Pluginat Kasutatakse

Plugin toetab töövooge, kus ruumiandmed ja objektide seisud peavad olema omavahel seotud:

- kinnistute leidmine ja seotud objektide vaatamine
- projektide, lepingute ja kooskõlastuste sirvimine
- servituutide ja teostusandmete haldamine kaardikihi kontekstis
- tööde loomine, geomeetria sidumine ja backendiga sünkroonimine
- mooduli- ja kasutajapõhiste seadete haldamine

## Põhivõimekused

### Moodulipõhine Töölaud

Kasutaja liigub vasakult külgribalt sobivasse moodulisse. Iga moodul avab konkreetse protsessi jaoks kohandatud vaate, filtrid ja tegevused.

Peamised moodulid:

- Kinnistud
- Projektid
- Lepingud
- Kooskõlastused
- Servituudid
- Tööd
- Teostusjoonised
- Seaded

### Sisselogimine Ja Sessioon

Plugin kontrollib kasutaja sessiooni ning suunab vajadusel sisselogimisse. Sessiooni taastamine, aegumise käsitlemine ja korduv sisselogimine peavad toimima ilma QGIS-i või plugina käsitsi värskendamiseta.

### Backendiga Andmevahetus

Moodulid kasutavad Kavitro backendist tulevaid andmeid, filtreid, staatuseid, tüüpe ja silte. Suuremate andmehulkade puhul kasutatakse pagineeritud laadimist ja moodulipõhist värskendamist.

### QGIS-i Kihid

Plugin toetab kihtide loomist, valimist, aktiveerimist ja geomeetria sidumist backendiga. Mõnes moodulis saab kasutaja kaardile joonistatud geomeetria saata backendile vastava objekti `geometry` väljale.

### Kaardi Ja UI Sidumine

Moodulivaate valikud saavad mõjutada kaardil nähtavat sisu ning kaardiobjektid saavad avada või eeltäita moodulite töövooge.

Näited:

- otsingust valitud kinnistule zoomimine
- moodulile seadistatud kihi aktiveerimine
- sisestuspaani kaudu uue töö lisamine
- GIS-is loodud sidumata tööde ülevaatamine enne Kavitrosse saatmist

## Tehniline Väärtus

Kasutaja jaoks väljendub tehniline pool peamiselt stabiilsuses ja järjepidevuses:

- ühine stiilisüsteem
- korduvkasutatavad filtrid ja pickerid
- keskne tõlkesüsteem
- QGIS-i kihtide ja backend-objektide sidumine
- logimine ja veainfo hilisemaks analüüsiks

## Märkus

See fail on üldine ülevaade. Detailsemad arendusotsused ja käimasolevad muutused on kirjas `REFACTOR_RULES.md` failis.
