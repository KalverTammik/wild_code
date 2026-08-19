# Kinnistute kihi seadistamine ja haldamine

Kinnistute seadistuskaardil määratakse Kavitro kinnistute põhi- ja arhiivikiht. Kinnistute halduse tööriistadega saab laadida Maa-ameti SHP-andmeid, luua puuduva GeoPackage'i kihistuse, lisada kinnistuid, arhiveerida või kustutada kirjeid ning koostada kinnistute otsinguvälja.

Üldine moodulikihtide valimine ja seadete salvestamine on kirjeldatud juhendis [Mooduli kihtide ja filtrieelistuste seadistamine](04_mooduli_kihtide_ja_filtrieelistuste_seadistamine.md). Kinnistu avamist ning seotud projektide, lepingute ja muude kirjete vaatamist kirjeldab [Kinnistute mooduli kasutamine](15_kinnistute_mooduli_kasutamine.md).

## Õigused ja nähtavus

Kinnistute seadistuskaart kuvatakse kasutajale, kellel on kinnistute mooduli kasutusõigus. Kaardi jaotis **Kinnistute haldus** kuvatakse ainult kasutajale, kelle Kavitro kontol on kinnistute loomise õigus.

Kui näed põhi- ja arhiivikihi valikuid, kuid haldusnuppe ei näe, ei ole põhjuseks QGIS-i projekt. Kontrolli kasutaja õigusi Kavitro administraatoriga.

## Eeltingimused

Enne kinnistute seadistamist või andmete muutmist veendu, et:

- avatud on õige QGIS-i projekt;
- kasutajal on kinnistute haldamiseks vajalik õigus;
- põhi- ja arhiivikihiks kasutatavad kihid on kirjutatavad;
- olemasolevad kinnistuandmed on enne suuremat importi varundatud;
- imporditav SHP-fail pärineb usaldusväärsest allikast ja sisaldab oodatud katastriandmeid;
- internetiühendus ja Kavitro sessioon on aktiivsed, kui toiming muudab ka Kavitro teenuse andmeid.

Kinnistute haldusnupud võivad muuta QGIS-i kihte ja Kavitro teenuse andmeid kohe. Nende toimingute rakendumine ei sõltu seadistuste akna nupust **Kinnita**.

## Kinnistute põhi- ja arhiivikihi määramine

### Põhikiht

**Kinnistute põhikiht** on aktiivsete kinnistute QGIS-i kiht. Seda kasutavad kinnistute otsing, kaardile suumimine, kinnistute valimine ja teiste moodulite toiming **Näita kaardil**.

### Arhiivikiht

**Arhiivikiht** on ajalooliste või aktiivsest kihist eemaldatud kinnistuandmete jaoks. Kinnistute lisamise töövoog kontrollib enne dialoogi avamist, et arhiivikiht oleks seadistatud ja projektis olemas.

Olemasolevate kihtide seadistamiseks:

1. Ava **Seaded** ja leia kinnistute kaart.
2. Vali väljale **Kinnistute põhikiht** aktiivsete kinnistute kiht.
3. Vali väljale **Arhiivikiht** vastav arhiivikiht.
4. Kontrolli, et valisid kaks õiget kihti.
5. Vajuta **Kinnita**.

Kui arhiivikiht on puudu, pakub kinnistute lisamise töövoog võimalust avada seaded või luua arhiivikiht põhikihiga samasse GeoPackage'i. Automaatne arhiivikihi loomine töötab ainult siis, kui põhikiht pärineb `.gpkg` failist.

## Kinnistute haldusnupud

| Nupp | Eeltingimus | Toime |
|---|---|---|
| **Ava Maa-ameti leht** | Kinnistute halduse õigus ja käsitsi seadistusrežiim | Avab Maa-ameti katastriandmete veebilehe |
| **Lisa SHP fail** | Käsitsi seadistusrežiim | Laadib valitud SHP-faili ajutiseks impordikihiks; võib luua ka põhi- ja arhiivikihi |
| **Lisa kinnistuid** | Tavarežiimis peab impordikiht sisaldama objekte | Avab kinnistute lisamise töövoo |
| **Eemalda kinnistu** | Kehtiv kinnistute põhikiht | Võimaldab valida põhikihilt objektid ning need arhiveerida, taastada või kustutada |
| **Kustuta ID järgi** | Kinnistute halduse õigus | Kustutab Kavitro teenuse kirje selle sisemise ID järgi |
| **Loo/paranda otsinguväli** | Kehtiv kinnistute põhikiht | Loob või arvutab uuesti `search_field` välja |

## Maa-ameti SHP-faili laadimine

Nupp **Lisa SHP fail** ei kopeeri kinnistuid kohe põhikihti. Esmalt luuakse QGIS-i projekti ajutine impordikiht grupis **Uued kinnistud**. Seda kihti kasutatakse hiljem toimingus **Lisa kinnistuid**.

1. Vajuta **Ava Maa-ameti leht** ja hangi vajalik katastriandmete SHP-fail.
2. Naase Kavitro seadetesse.
3. Vajuta **Lisa SHP fail**.
4. Vali `.shp` fail.
5. Oota, kuni QGIS laadib andmed ajutisse impordikihti.
6. Kontrolli teavituses imporditud objektide arvu.

Kui kinnistute põhikiht on juba seadistatud, lõpeb laadimine ajutise impordikihi loomisega. Kinnistute põhikihti muudetakse alles siis, kui käivitad eraldi lisamise töövoo.

## Puuduvate kinnistukihtide automaatne loomine

Kui vajutad **Lisa SHP fail**, kuid projektis ei ole kehtivat kinnistute põhikihti, pakub Kavitro järgmisi valikuid:

- **Loo GeoPackage'i kihid** – loob SHP struktuuri põhjal tühja põhi- ja arhiivikihi;
- **Jätka ainult SHP-kihiga** – laadib ainult ajutise impordikihi ja jätab põhi- ning arhiivikihi seadistamata;
- **Tühista** – katkestab laadimise.

GeoPackage'i kihtide loomiseks:

1. Vali **Loo GeoPackage'i kihid**.
2. Määra loodava `.gpkg` faili asukoht. Vaikimisi pakutakse SHP-faili kausta faili `kinnistud.gpkg`.
3. Kui fail on juba olemas, kinnita, et soovid lisada kinnistukihid sellesse faili.
4. Oota põhi- ja arhiivikihi loomist ning projekti laadimist.
5. Kontrolli õnnestumise teadet ja seadistuskaardi kihivalikuid.

Kavitro loob ja seadistab:

- põhikihi **Kinnistud**;
- arhiivikihi **Arhiveeritud kinnistud**;
- põhikihile vajaduse korral tekstivälja `search_field`;
- ajutise impordikihi SHP-faili objektidega.

Loodud põhi- ja arhiivikiht on esialgu tühi. SHP-faili objektid lisatakse põhikihti toiminguga **Lisa kinnistuid**.

### Automaatse loomise nõuded

SHP peab:

- olema kehtiv polügoonikiht;
- sisaldama kehtivat koordinaatsüsteemi;
- sisaldama nõutud välju `tunnus`, `l_aadress`, `ay_nimi`, `ov_nimi`, `mk_nimi`, `registr`, `muudet`, `pindala`, `siht1`, `siht2`, `siht3`, `so_prts1`, `so_prts2`, `so_prts3` ja `maks_hind`.

Väljade nimede suur- ja väiketähti ei eristata. SHP muud väljad säilitatakse loodava põhikihi struktuuris.

Kavitro ei kirjuta üle projektis või valitud GeoPackage'is juba olemasolevat kihti nimega **Kinnistud** või **Arhiveeritud kinnistud**. Konflikti korral vali teine GeoPackage või seadista olemasolevad kihid käsitsi.

## Kinnistute lisamine

Enne lisamist peab projektis olema objektidega ajutine impordikiht. Tavarežiimis muutub nupp **Lisa kinnistuid** aktiivseks pärast SHP-faili edukat laadimist.

1. Vajuta **Lisa kinnistuid**.
2. Vali kinnistute leidmise viis:
   - **Vali kaardilt**;
   - **Vali asukoha järgi (loend)**.
3. Kontrolli, et kinnistute põhi- ja arhiivikiht on olemas.
4. Vali lisatavad kinnistud.
5. Soovi korral käivita tähelepanu kontrollid.
6. Kontrolli tabelis leitud probleeme ja olemasolevaid vasteid.
7. Vajuta **Lisa valitud**.
8. Oota, kuni lisamise edenemine lõpeb.

### Kaardilt valimine

Valik **Vali kaardilt** lubab märkida ajutiselt impordikihilt ühe või mitu kinnistut ristkülikuga. Pärast valimist kuvatakse objektid kinnistute tabelis. Nupuga **Vali uuesti kaardilt** saab valikut korrata.

### Asukoha järgi valimine

Valik **Vali asukoha järgi (loend)** võimaldab filtreerida imporditud kinnistuid maakonna, omavalitsuse ja asustusüksuse järgi. Selles režiimis rakendub lisamine parajasti filtreeritud tabeli kirjetele.

### Tähelepanu kontrollid

Tähelepanu kontrollid võrdlevad valitud kinnistuid olemasolevate kihi- ja Kavitro teenuse andmetega. Kontroll võib tuvastada näiteks aktiivse või arhiveeritud olemasoleva kirje ning küsida, kuidas sellega toimida.

Nupp **Lisa ilma kontrollideta** jätab need eelkontrollid vahele. Kasuta seda ainult siis, kui oled kindel, et valik ei tekita duplikaate ega asenda valet kirjet.

Kinnistute lisamine võib muuta korraga põhikihti, arhiivikihti ja Kavitro teenuse andmeid. Seadistuste akna **Hülga** ei võta lisamist tagasi.

## Kinnistu eemaldamine, arhiveerimine või taastamine

Nupp **Eemalda kinnistu** käivitab kaardivaliku kinnistute põhikihil.

1. Vajuta **Eemalda kinnistu**.
2. Järgi kuvatavat juhist ja vali põhikihilt ristkülikuga üks või mitu kinnistut.
3. Kontrolli dialoogis valitud kinnistute katastritunnuseid.
4. Vali toiming:
   - **Arhiveeri**;
   - **Taasta arhiivist**;
   - **Kustuta**.
5. Kontrolli toimingu tulemust.

Toiming saadetakse Kavitro teenusele katastritunnuse järgi. **Kustuta** eemaldab sobivad objektid lisaks ka kinnistute põhikihist. Arhiveerimise ja taastamise mõju sõltub Kavitro teenuse vastavast töövoost.

**Oluline:** need toimingud rakenduvad kohe. Enne kinnitamist kontrolli hoolikalt valitud objektide arvu ja katastritunnuseid.

## Kustutamine Kavitro ID järgi

**Kustuta ID järgi** on erakorraline toiming juhuks, kui kirjet ei saa kaardilt katastritunnuse järgi valida.

1. Vajuta **Kustuta ID järgi**.
2. Sisesta Kavitro teenuse kinnistukirje sisemine ID.
3. Vajuta **Kinnita**.
4. Kontrolli kustutamise tulemust.

See toiming kustutab kirje Kavitro teenusest. See ei otsi ega kustuta vastavat objekti QGIS-i põhikihist. Vajaduse korral tuleb QGIS-i kihi objekt eraldi kontrollida ja eemaldada.

Ära sisesta sellesse välja katastritunnust, kui sul ei ole kinnitust, et see on ühtlasi Kavitro kirje sisemine ID.

## Otsinguvälja loomine või parandamine

Kavitro kinnistuotsing ja automaatne kaardile suumimine kasutavad põhikihi välja `search_field`.

Nupp **Loo/paranda otsinguväli**:

- lisab puuduva `search_field` tekstivälja;
- arvutab välja väärtuse kõigile põhikihi objektidele;
- arvutab olemasolevad väärtused vajaduse korral uuesti;
- salvestab muudatused, kui kiht ei olnud enne toimingut muutmisrežiimis.

Otsinguväärtus koostatakse olemasolevatest väljadest järgmises järjekorras:

1. `tunnus`;
2. `l_aadress`;
3. `ay_nimi`;
4. `ov_nimi`;
5. `mk_nimi`.

Puuduvad ja tühjad väärtused jäetakse vahele ning korduvaid väärtusi samasse otsinguteksti ei lisata.

Otsinguvälja loomiseks:

1. Veendu, et valitud on kirjutatav kinnistute põhikiht.
2. Vajuta **Loo/paranda otsinguväli**.
3. Oota kõigi objektide töötlemist.
4. Kontrolli teadet uuendatud kirjete arvuga.

Kui põhikiht oli juba QGIS-i muutmisrežiimis, jäävad muudatused selle aktiivsesse redigeerimisse. Salvesta või tühista need QGIS-i tavapäraste redigeerimistööriistadega.

## Kinnistute haldus Geospatiali režiimis

Geospatiali seadistusrežiimis:

- **Ava Maa-ameti leht** on keelatud;
- **Lisa SHP fail** on keelatud;
- **Lisa kinnistuid** jääb kättesaadavaks;
- otsinguvälja nupp sõltub endiselt põhikihi olemasolust;
- moodulikaardil kuvatakse eraldi Geospatiali kihi mapper.

Geospatiali kihtide andmete vastendamine on kirjeldatud juhendis [Geospatiali kihtide vastendamine](06_geospatiali_kihtide_vastendamine.md).

## Levinumad olukorrad

### Kinnistute halduse jaotist ei kuvata

Kasutajal puudub kinnistute loomise õigus. Pöördu Kavitro administraatori poole.

### „Lisa kinnistuid“ on keelatud

Laadi esmalt **Lisa SHP fail** abil objektidega impordikiht. Tühja SHP või puuduva ajutise impordikihi korral nuppu tavarežiimis kasutada ei saa.

### Kinnistute lisamine ei avane

Kontrolli, et kinnistute põhikiht ja arhiivikiht on seadistatud ning projektis olemas. Puuduva arhiivikihi korral vali see seadetes või loo see põhikihiga samasse GeoPackage'i.

### GeoPackage'i kihte ei loodud

Kontrolli veateatest puuduvaid välju. Veendu ka, et SHP oleks polügoonikiht, selle koordinaatsüsteem oleks kehtiv ning projektis või GeoPackage'is ei oleks samanimelisi kihte.

### Otsinguvälja loomine ebaõnnestus

Põhikiht peab olema kirjutatav ja sisaldama vähemalt üht otsingu lähtevälja. Kontrolli ka andmeallika kirjutusõigust ning QGIS-i kihi redigeerimisvigu.

### Kustutatud Kavitro kirje on endiselt kaardil

Kui kasutasid **Kustuta ID järgi** toimingut, kustutati ainult Kavitro teenuse kirje. Kontrolli ja korrasta QGIS-i põhikiht eraldi.

## Kontrollnimekiri

Pärast kinnistute seadistamist kontrolli, et:

- valitud on õige põhikiht ja arhiivikiht;
- mõlemad kihid on projektis olemas ja kirjutatavad;
- põhikihil on ajakohane `search_field`;
- SHP impordikiht asub grupis **Uued kinnistud** ja sisaldab oodatud objekte;
- enne lisamist on üle vaadatud tähelepanu kontrollide tulemused;
- kustutamisel või arhiveerimisel valiti õiged katastritunnused;
- Kavitro teenuse ja QGIS-i põhikihi andmed on pärast toimingut kooskõlas.
