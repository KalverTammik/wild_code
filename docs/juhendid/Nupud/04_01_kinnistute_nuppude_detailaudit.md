# Kinnistute nuppude detailaudit

See juhend kirjeldab Visuaali kinnistunuppude tegelikku käitumist praeguse koodibaasi järgi. Kaetud on kinnistu avamine kaardilt, seotud kirjete rühmade avamine, Maa-ameti leht, SHP-impordi kihtide loomine, kinnistute lisamine, tähelepanukontroll, arhiveerimine, taastamine, kustutamine ja otsinguvälja genereerimine.

## Mõju lühikaart

| Nupurühm | Peamine mõju | Kas seadistuste **Hülga** taastab? |
|---|---|:---:|
| Kinnistute mooduli **Vali kaardilt** ja rühmanooled | QGIS-i objektivalik ning ekraanil kuvatav kirje | Ei ole vajalik; püsiandmeid ei muudeta |
| **Ava Maa-ameti leht** | Avab välise veebilehe | – |
| **Lisa SHP fail** | Lisab QGIS-i mälukihi; võib luua GPKG-kihid ja salvestada kihiviited | Ei |
| Lisamisdialoogi lisamisnupud | Võivad muuta Kavitro kirjeid ning QGIS-i põhi- ja arhiivikihti | Ei |
| **Arhiveeri**, **Taasta arhiivist**, **Kustuta** | Muudavad Kavitro andmeid; kustutamine muudab ka põhikihti | Ei |
| **Kustuta ID järgi** | Kustutab ainult Kavitro kirje | Ei |
| **Loo/paranda otsinguväli** | Muudab kinnistute põhikihi skeemi ja atribuute | Ei |

Seadistuste vaate üldist **Kinnita** nuppu ei ole ühegi siin kirjeldatud haldustoimingu lõpetamiseks vaja.

## Kinnistute mooduli Vali kaardilt

Nupp asub kinnistute mooduli päises ja vajab seadistatud, kehtivat kinnistute põhikihti.

Klõpsamisel:

1. tehakse põhikiht nähtavaks ja aktiivseks;
2. senine kihivalik tühjendatakse;
3. aktiveeritakse QGIS-i ristkülikvalik;
4. Visuaali aken minimeeritakse;
5. pärast vähemalt ühe objekti valimist taastatakse aken;
6. ekraanile loetakse valiku esimese objekti katastriandmed;
7. katastritunnuse järgi käivitatakse seotud Kavitro kirjete laadimine.

Nupp lubab valida mitu objekti, kuid kinnistuvaade kasutab ainult `selectedFeatures()` loendi esimest objekti. Selle järjekord ei pruugi vastata valimise visuaalsele järjekorrale. Kindla kinnistu avamiseks vali ainult üks polügoon.

Valik muudab QGIS-i aktiivset kihti ja objektivalikut, kuid ei kirjuta kihi atribuute ega Kavitro andmeid.

### Katkestamise piirang

Valikutööriist lõpetab voo alles siis, kui kihil on vähemalt üks valitud objekt. Kontroller ei kuula eraldi `Esc`-klahvi, paremklõpsu ega QGIS-i kaarditööriista vahetamist. Kui valik katkestatakse ilma objektita, ei pruugi Visuaali aken automaatselt taastuda. Sel juhul ava või too aken ette uuesti QGIS-i Visuaali tööriistariba nupuga.

### Seotud kirjete laadimise servajuht

Iga valik käivitab taustal uue seoste päringu, kuid eelmist sama mooduliseansi päringut ei tühistata ega eristata kinnistu-põhise päringutunnusega. Kiiresti järjest erinevaid kinnistuid valides võib aeglasem vana vastus kirjutada uuema kinnistu seotud kirjete vaate üle.

## Seotud moodulirühma laiendamine ja ahendamine

Noolenupp asub iga seotud andmerühma, näiteks projektide või lepingute, päises.

- Kuni viie kirjega rühm on alguses avatud.
- Rohkem kui viie kirjega rühm on alguses suletud.
- Esimene avamine loob rühma kirjeread juba laaditud andmetest.
- Sulgemine peidab read neid hävitamata.
- Uuesti avamine ei käivita Kavitrosse uut päringut.

Nupp ei muuda kinnistu- ega seoseandmeid. Noolenupul pole eraldi teksti ega kohtspikrit.

## Kinnistute halduse nähtavus

Seadistuste kinnistukaardi **Kinnistute haldus** jaotis luuakse ainult kasutajale, kelle Kavitro õigused lubavad kinnistuid luua. Kui jaotist pole, ei ole põhjuseks nupu olek ega QGIS-i kiht.

Käsitsi seadistusrežiimis arvutatakse nuppude olek järgmiselt:

| Nupp | Aktiivsuse tingimus |
|---|---|
| **Ava Maa-ameti leht** | Alati aktiivne |
| **Lisa SHP fail** | Alati aktiivne |
| **Lisa kinnistuid** | Projektis on märgendatud impordikiht ja sellel vähemalt üks objekt |
| **Eemalda kinnistu** | Kehtiv kinnistute põhikiht on leitav |
| **Kustuta ID järgi** | Alati aktiivne |
| **Loo/paranda otsinguväli** | Kehtiv kinnistute põhikiht on leitav |

Geospatiali režiimis keelatakse **Ava Maa-ameti leht** ja **Lisa SHP fail**, kuid **Lisa kinnistuid** lubatakse tingimusteta. **Eemalda kinnistu** olekut selles režiimiharus uuesti ei arvutata; puuduva põhikihi korral katkestab selle nupu hilisem kontroll töövoo.

## Ava Maa-ameti leht

Nupp avab konfiguratsioonis määratud Maa-ameti katastriandmete lehe arvuti vaikimisi veebibrauseris.

- Visuaal ei laadi ega vali sealt faili automaatselt.
- Nupp ei muuda QGIS-i ega Kavitro andmeid.
- Puuduva või vigase veebiaadressi ja operatsioonisüsteemi avamisvea korral kirjutatakse viga logisse, kuid kasutajale eraldi veateadet ei kuvata.
- Geospatiali režiimis on nupp passiivne.

## Lisa SHP fail

Nupp on aktiivne ainult käsitsi seadistusrežiimis. Failidialoog pakub `.shp` faile, kuid sisaldab ka valikut **All files**; lõplikult kontrollitakse, kas OGR suudab valitud faili kehtiva kihina avada.

### Tavaline import

Kui kinnistute põhikiht on juba olemas:

1. vali failidialoogis lähtefail;
2. Visuaal loob sama geomeetriatüübi, CRS-i ja väljadega QGIS-i mälukihi;
3. kõik lähteobjektid kopeeritakse mälukihti;
4. kiht paigutatakse rühma **Uued kinnistud** ja märgendatakse kinnistute impordikihiks;
5. kihile rakendatakse Maa-ameti impordistiil;
6. kuvatakse imporditud objektide arv.

SHP-objekte ei lisata selle nupuga veel põhikihti ega Kavitrosse. Mälukiht on ajutine ja selle andmed ei ole eraldi failina püsivalt salvestatud.

Mahuka SHP kopeerimisel kuvatava edenemisakna **Tühista** nupp muudab küll enda teksti ja saadab katkestussignaali, kuid imporditsükkel ei kuula seda signaali ega katkestusolekut. Nupu vajutamise järel import jätkub. Ära sulge edenemisakent sulgemisristist, sest töö kasutab sama dialoogiobjekti hilisemate edenemisuuenduste jaoks ja kontrollimata sulgemine võib impordi lõpetada veaga pärast juba lisatud partiisid.

Sama failinime uuesti importimisel eemaldatakse sama nimega varasem mälukiht. Teise nimega SHP importimisel võib projekti jääda mitu impordimärgendiga mälukihti.

### Puuduva põhikihi valikud

Kui kehtivat põhikihti pole, avaneb enne importi valik:

| Nupp | Tulemus |
|---|---|
| **Loo GeoPackage'i kihid** | Palub valida `.gpkg` faili ning loob tühjad kihid **Kinnistud** ja **Arhiveeritud kinnistud** |
| **Jätka ainult SHP-kihiga** | Loob ainult ajutise impordikihi |
| **Tühista** | Ei loo impordikihti ega uusi püsikihte |

Kui valitud GeoPackage on juba olemas, küsib nupp **Lisa kihid** luba kahe uue kihi lisamiseks. Kogu faili üle ei kirjutata. Dialoogi **Tühista** jätab nii impordikihi kui ka uued püsikihid loomata. Kui failis või projektis on juba samanimeline kinnistukiht, peatatakse loomine.

Uute kihtide loomine eeldab polügoongeomeetriat, kehtivat CRS-i ja kõiki nõutud Maa-ameti välju. Põhikiht saab lisaks välja `search_field`; arhiivikiht luuakse põhikihi struktuuri järgi.

Edu korral:

- kihid lisatakse kohe QGIS-i projekti;
- põhi- ja arhiivikihi nimed salvestatakse kohe kinnistute seadistusse;
- seadistuskaardi valikud sünkroonitakse uute kihtidega;
- üldist **Kinnita** nuppu pole vaja.

### Mitme impordikihi risk

Lisamise töövoog otsib impordikihi märgendi järgi ja võtab projektist esimese leitud kihi. Kui eri nimega impordikihte on mitu, ei ole tagatud, et kasutatakse viimati laaditud SHP-d. Enne uut importi eemalda või tühjenda vanad impordikihid ja kontrolli grupis **Uued kinnistud**, milline kiht on aktiivne.

## Lisa kinnistuid

Nupp avab esmalt lisamisviisi valiku.

| Nupp | Tulemus |
|---|---|
| **Vali kaardilt** | Avab mittemodaalse dialoogi ja käivitab impordikihil ristkülikvaliku |
| **Vali asukoha järgi (loend)** | Avab modaalse dialoogi maakonna, omavalitsuse ja asustusüksuse filtritega |
| **Tühista** | Katkestab enne kihtide või andmete muutmist |

Enne lisamisdialoogi kontrollitakse salvestatud põhi- ja arhiivikihti. Puuduva põhikihi korral kuvatakse hoiatus. Puuduva arhiivikihi korral saab:

- **Ava Seaded** – katkestab lisamise avamise ja viib kinnistute seadistuskaardile;
- **Loo/lae GPKG-s…** – küsib arhiivikihi nime ning loob või laadib selle põhikihiga samas GeoPackage'is;
- **Tühista** – katkestab lisamisdialoogi avamise.

Arhiivikihi nime küsimise dialoogis jätkab kinnitamine sisestatud nimega ja **Tühista** lõpetab voo. Tühi nimi lükatakse tagasi. Automaatne loomine töötab ainult GeoPackage-põhise põhikihiga. Loodud arhiivikihi viide salvestatakse kohe.

### Geospatiali režiimi servajuht

Geospatiali režiimis on **Lisa kinnistuid** alati aktiivne, isegi kui impordikihti pole. Lisamisdialoogi konstruktor jätkab ka pärast puuduva impordikihi veavaate loomist ning järgmine initsialiseerimine eeldab tabeli ja filtrite olemasolu. Seetõttu võib nupuvajutus ilma impordikihita lõppeda programmiveaga, mitte ainult suletava veateatega.

## Lisamisdialoogi tabelinupud

### Vali kõik

Kaardilt valimise režiimis valib nupp kõik tabeliread ja need muutuvad lisamise sihiks. Tabelivalik sünkroonitakse kuni 1500 rea korral tagasi impordikihi kaardivalikuks.

Asukohaloendi režiimis on lisamise sihiks alati kõik parajasti tabelis olevad filtreeritud read, mitte ainult tabelis siniseks valitud read. **Vali kõik** muudab seal ainult visuaalset valikut.

### Tühjenda valik

Kaardirežiimis eemaldab nupp valiku ja blokeerib lisamisnupud, kuni mõni rida uuesti valitakse.

Asukohaloendi režiimis tühjendab nupp ainult visuaalse valiku. Lisamisnuppude loendur kasutab endiselt tabeli ridade arvu ning lisamisel töödeldakse kõiki tabeliridu. Seega ei saa asukoharežiimis selle nupuga kinnistuid lisamisest välja jätta.

### Vali uuesti kaardilt

Nupp esineb ainult kaardirežiimis. See tühistab parajasti aktiivse impordikihi valikukontrolleri, eemaldab kihi alamhulgafiltri ja käivitab uue ristkülikvaliku.

Uus valik asendab tabeli senise sisu ja valib kõik uued read. Kui kaart sulgeda või tööriista vahetada ilma objekti valimata, ei pruugi dialoog ja Visuaali aken automaatselt ette naasta.

## Käivita kontroll

Nupp kontrollib kõiki parajasti tabelis olevaid ridu, mitte üksnes siniselt valitud ridu.

Kontroll võrdleb iga katastritunnust:

- kinnistute põhikihiga;
- Kavitro aktiivsete ja arhiveeritud kinnistukirjetega;
- impordi ja olemasolevate kirjete muutmiskuupäevadega.

Kontroll ise andmeid ei muuda. Kontrolli ajal on lisamisnupud blokeeritud ja edenemist kuvatakse loendurina. Dialoogi **Tühista** peatab kontrollitööd.

### Kriitiline arhiiviplaani käitumine

Kontroll arvutab lisaks `põhikihi kõik tunnused – tabelis olevad tunnused`. Kõik saadud tunnused märgitakse impordist puuduvaks. Järgmine **Lisa valitud** või ka pärast kontrolli vajutatud **Lisa ilma kontrollita** käivitab enne lisamist nende automaatse arhiveerimise:

- põhikihi objekt kopeeritakse arhiivikihti ja eemaldatakse põhikihist;
- vastav aktiivne Kavitro kirje proovitakse arhiveerida;
- eraldi kinnitust kogu selle loendi kohta ei küsita.

Kaardi- või asukohavalik esindab tavaliselt ainult väikest alamhulka, mitte täielikku autoritatiivset kinnisturegistrit. Sellisel juhul võidakse kõik ülejäänud põhikihi kinnistud ekslikult arhiveerimisplaani lisada.

**Ohutu töövõte praeguses versioonis:** ära vajuta piiratud kaardi- või asukohavaliku puhul **Käivita kontroll**. Kui kontroll on juba lõpetatud, sulge dialoog nupuga **Tühista** ja alusta lisamist uuesti; ära vajuta kumbagi lisamisnuppu. Kasuta kontrolli ainult siis, kui tabel sisaldab teadlikult kogu võrdluse aluseks olevat autoritatiivset impordikogumit ja puuduvate arhiveerimine on soovitud.

## Lisa ilma kontrollita

Nupp on aktiivne, kui lisamise sihis on vähemalt üks rida.

- Kaardirežiimis töödeldakse valitud ridu.
- Asukoharežiimis töödeldakse kõiki tabeliridu.
- Uut tähelepanukontrolli ei käivitata.
- Kui kontroll on samas dialoogis juba lõpetatud, rakendatakse olemasolev puuduva impordi arhiiviplaan siiski enne lisamist.

Lisamise käigus kontrollib põhiloogika iga kinnistut taustateenuse ja põhikihi suhtes ka siis, kui tähelepanukontroll jäeti vahele. Vajaduse korral võivad avaneda üksiku kinnistu otsustusdialoogid.

## Lisa valitud

Nupu nimi ei kirjelda mõlema režiimi ulatust ühtemoodi:

- kaardirežiimis lisatakse valitud read;
- asukoharežiimis lisatakse kõik tabelis olevad read, ka pärast **Tühjenda valik** vajutamist.

Nupp ei nõua, et **Käivita kontroll** oleks varem edukalt lõpetatud. Tehniliselt saab selle vajutada kohe, kui sihis on vähemalt üks rida. Kui kontroll on tehtud, rakendatakse enne lisamist selle automaatne arhiiviplaan.

### Ühe kinnistu lisamise otsustusloogika

Iga töödeldava tunnuse puhul võrreldakse Kavitro kirjet ja põhikihti.

| Olemasolu | Põhikäitumine |
|---|---|
| Puudub Kavitros ja põhikihis | Luuakse Kavitro kirje ja kopeeritakse impordiobjekt põhikihti |
| Olemas Kavitros, puudub põhikihis | Vajaduse korral uuendatakse Kavitro kirjet ning küsitakse, kas objekt põhikihti kopeerida |
| Puudub aktiivsena Kavitros, kuid arhiveeritud kirje on olemas | Pakutakse **Taasta olemasolev**, **Loo uus** või **Jäta vahele** |
| Olemas põhikihis, puudub Kavitros | Küsitakse, kas luua Kavitro kirje |
| Olemas mõlemas | Kavitro kirjet võidakse impordiandmetega uuendada; uut kaardiobjekti ei lisata |
| Kavitro kontroll ebaõnnestub | Tunnus jäetakse vahele, et vältida pimedat duplikaati |

Korduva valiku puhul võib nupp pakkuda ka **Jah kõigile**, millega kopeeritakse kõik sama jooksu Kavitros olemas, kuid kaardilt puuduvad objektid põhikihti ilma iga järgneva küsimuseta.

### Lisamise käigus avanevad otsustusnupud

| Olukord | Nupp | Tulemus |
|---|---|---|
| Tunnus on ainult Kavitro arhiivis | **Taasta olemasolev** | Aktiveerib arhiveeritud kirje, uuendab seda impordiandmetega ja võib seejärel küsida põhikihti kopeerimist |
| Sama | **Loo uus** | Jätkab uue Kavitro kirje loomise haruga |
| Sama | **Jäta vahele** | Ei muuda ega lisa seda tunnust |
| Kavitro kirje puudub, kuid põhikihi objekt on olemas | **Jah** | Lubab luua puuduva Kavitro kirje |
| Sama | **Ei** | Jätab tunnuse selles jooksus vahele |
| Kavitro kirje on olemas, kuid põhikihi objekt puudub | **Jah** | Kopeerib impordiobjekti põhikihti |
| Sama | **Ei** | Ei kopeeri objekti põhikihti; võimalik varasem Kavitro uuendus jääb alles |
| Sama kordub mitme tunnusega | **Jah kõigile** | Kopeerib käimasoleva jooksu kõik järgmised samas olukorras objektid põhikihti uut kinnitust küsimata |

Dialoogi sulgemist või **Ei** valikut käsitletakse vastava küsimuse tühistava vastusena. Otsused rakenduvad jooksvalt; hilisem lisamisdialoogi **Tühista** ei võta juba tehtud muudatusi tagasi.

### Salvestamine, osaline õnnestumine ja katkestamine

Lisamine muudab Kavitrot ja QGIS-i kihte ühes protsessis, kuid mitte ühise tehinguna. Kavitro päring võib õnnestuda enne kihimuudatust või vastupidi.

Dialoogi **Tühista** lisamise ajal:

- peatab järjekorda jäänud kinnistute töötlemise;
- proovib katkestada parajasti kontrollitava või lisatava üksuse;
- ei võta tagasi varem lõpetatud üksuste Kavitro ega kihimuudatusi;
- sulgeb dialoogi pärast katkestuse jõustumist.

Edenemise `tehtud/kokku` arv loendab töödeldud järjekorraüksusi, mitte edukalt lisatud kinnistuid. Taustal tekkivad vead võidakse logida või üksikdialoogis näidata, kuid lõpus eraldi õnnestunud ja ebaõnnestunud kirjete koondit ei kuvata.

## Lisamisdialoogi Tühista ja Sulge

### Tühista

Enne lisamise algust peatab nupp tähelepanukontrolli, eemaldab impordikihi ajutise alamhulgafiltri ja sulgeb dialoogi andmeid lisamata.

Lisamise ajal muutub nupp katkestamistaotluseks. Juba rakendunud toimingud jäävad alles.

### Sulge

Nupp kuvatakse veavaates, kui impordikihti ei leitud. See sulgeb dialoogi. Geospatiali režiimi puuduva impordikihi servajuhus võib konstruktor jõuda veani enne, kui kasutaja saab nuppu kasutada.

## Eemalda kinnistu

Nupp vajab kinnistute põhikihti. Klõps:

1. kuvab kaardilt valimise juhise;
2. käivitab põhikihil ristkülikvaliku;
3. minimeerib Visuaali akna;
4. taastab akna pärast vähemalt ühe objekti valimist;
5. kuvab valitud objektide tabeli;
6. pakub **Arhiveeri**, **Taasta arhiivist**, **Kustuta** või **Tühista**.

Tabel on ainult ülevaatamiseks; kõik leitud read on toimingu siht ning üksikuid ridu ei saa tegevusdialoogis välja jätta. Katastritunnuseta valiku puhul toiming peatatakse.

Ka siin ei lõpeta `Esc`, paremklõps või kaarditööriista vahetamine kontrollerit eraldi. Objektita katkestamisel võib Visuaali aken jääda minimeerituks.

## Arhiveeri

Nupp proovib iga kordumatu katastritunnuse kohta:

1. leida täpselt ühe aktiivse Kavitro kinnistu;
2. määrata võimaluse korral Kavitro staatuseks `ARCHIVED`;
3. lisada tunnuse **Arhiveeritud**;
4. lisada aadressi ette arhiiviprefiksi.

See eemaldamise dialoogi nupp ei kopeeri objekti kinnistute arhiivikihti ega eemalda seda põhikihist. QGIS-i kiht jääb muutmata.

Kui tunnusele ei leita üht aktiivset kirjet, vasteid on mitu või mõni päring ebaõnnestub, kirjutatakse põhjus peamiselt logisse. Ülemine tegevusteenus ei kogu üksikute kirjete tulemust ja tagastab kasutajale ikkagi üldise õnnestumisteate valitud kirjete arvu järgi.

## Taasta arhiivist

Nupp proovib katastritunnuse järgi leida täpselt ühe arhiveeritud Kavitro kirje. Seejärel:

- proovib määrata staatuseks `ACTIVE`;
- eemaldab tunnuse **Arhiveeritud**;
- eemaldab aadressi arhiiviprefiksi.

Nupp ei kopeeri objekti QGIS-i arhiivikihist põhikihti. Kuna valik tehakse algselt põhikihilt, peab taastatava tunnusega objekt olema põhikihil juba olemas, et kasutaja saaks selle selles töövoos valida.

Ka selle toimingu üksikvead jäävad peamiselt logisse ja üldine tulemus võib näida edukas.

## Kustuta

Nupp teeb toimingud selles järjekorras:

1. proovib iga tunnuse kohta leida ühe aktiivse või ühe arhiveeritud Kavitro kirje;
2. saadab leitud kirje ID-ga kustutamispäringu;
3. otsib põhikihilt kõik sama tunnusega objektid;
4. kustutab need objektid ja salvestab kihi muudatused.

Kavitro kustutuse tulemusi ei anta kihikustutuse teenusele tagasi. Seetõttu võib põhikihi kustutamine jätkuda ka siis, kui Kavitro päring ebaõnnestus. Kasutajale näidatav `ok` tulemus põhineb lõpuks põhikihi salvestamisel, mitte kogu Kavitro ja QGIS-i toimingu terviklikul õnnestumisel.

Kui põhikiht oli juba enne toimingut redigeerimisrežiimis, kutsub kustutaja ikkagi `commitChanges()`. See võib koos kustutusega salvestada ka kasutaja muud sama kihi ootel muudatused.

## Kustuta ID järgi

See on erakorraline taustateenuse toiming ja ei kasuta QGIS-i kihivalikut.

| Dialoogi nupp | Tulemus |
|---|---|
| **Tühista** | Sulgeb dialoogi midagi muutmata |
| **Kinnita** | Kontrollib, et väli pole tühi, keelab päringu ajaks mõlemad nupud ja saadab sisestatud väärtuse Kavitro kirje ID-na |

Edu korral dialoog suletakse. Vea korral kuvatakse hoiatus ja dialoog jääb avatuks.

Toiming:

- ei kontrolli enne kustutamist kirje nime ega katastritunnust;
- ei küsi teist lõplikku kinnitust;
- ei eemalda vastavat objekti põhikihist ega arhiivikihist;
- ei värskenda kinnistute mooduli avatud vaadet.

API-kutse tehakse kasutajaliidese lõimes. Meetodis puudub üldine erindikäsitlus kustutamispäringu ümber, mistõttu ootamatu ühendus- või kliendiviga võib väljuda dialoogi nupukäsitlejast ilma kasutajasõbraliku koondteateta.

## Loo/paranda otsinguväli

Nupp on aktiivne, kui kehtiv kinnistute põhikiht on leitav. Klõps:

1. kontrollib, et kihil oleks vähemalt üks lähteväli `tunnus`, `l_aadress`, `ay_nimi`, `ov_nimi` või `mk_nimi`;
2. lisab puuduva kuni 512 märgi pikkuse tekstivälja `search_field`;
3. koostab kõigile objektidele otsinguteksti olemasolevatest lähteväärtustest;
4. jätab tühjad ja korduvad väärtused välja;
5. kuvab muudetud objektide arvu.

Kui kiht ei olnud varem redigeerimisrežiimis, alustab tööriist redigeerimist ja salvestab muudatused ise. Salvestusvea korral proovitakse tööriista muudatused tagasi võtta.

Kui kiht oli juba redigeerimisrežiimis, jäävad otsinguvälja muudatused samasse QGIS-i redigeerimisse. Nupp ei salvesta neid automaatselt. Edenemisdialoogil puudub katkestamisnupp.

Kui mõne objekti atribuudi muutmine tagastab `False`, ei lisata seda muudetud kirjete arvu, kuid töövoog ei käsitle seda eraldi veana. Seetõttu kontrolli pärast „õnnestumise“ teadet välja väärtusi, eriti kirjutuspiirangutega andmeallikal.

## Auditi käigus leitud parandamist vajavad kohad

| Prioriteet | Leid | Kasutajarisk | Soovitatav parandus |
|---|---|---|---|
| Kriitiline | Tähelepanukontroll käsitleb kõiki põhikihi, kuid parajasti tabelist puuduvaid tunnuseid arhiveeritavana ning järgmine lisamisnupp rakendab plaani ilma eraldi kinnituseta | Piiratud kaardi- või asukohavalik võib arhiveerida peaaegu kogu ülejäänud kinnistukihi ja Kavitro andmestiku | Arvuta puuduvad ainult selgelt määratud täieliku impordikogumi suhtes; näita täielik arhiiviloend ja nõua eraldi kinnitust |
| Kriitiline | Automaatse arhiivimise käigus proovitakse esmalt salvestada arhiivikiht ja seejärel põhikihi kustutused; arhiivikihi salvestusvea järel jätkub põhikihi salvestamine | Objekt võib põhikihist kaduda, kuigi koopiat arhiivikihti ei salvestatud | Peata põhikihi kustutuse salvestamine arhiivikihi vea korral või kasuta ühist taastatavat tehingut |
| Kriitiline | Eemaldamise **Kustuta** ei arvesta Kavitro kustutuspäringute üksiktulemusi enne põhikihi objektide kustutamist | Kavitro kirje võib jääda alles, kuid kaardiobjekt kustutatakse ja toiming näib edukas | Tagasta iga Kavitro toimingu tulemus, kustuta kaardilt ainult edukad vasted ja kuva koondraport |
| Kõrge | Uue Kavitro kirje loomise tagastusväärtust ei kontrollita enne impordiobjekti põhikihti kopeerimist | Kihile võib tekkida objekt ilma Kavitro kirjeta | Kopeeri objekt alles kinnitatud teenuse-ID järel või märgi osaline tulemus taastatavaks veaks |
| Kõrge | Juba redigeerimisrežiimis põhi- ja arhiivikihtide lisamis-, arhiivimis- ja kustutamisvood kutsuvad `commitChanges()` | Tööriist võib salvestada ka kasutaja varasemad, selle toiminguga mitteseotud muudatused | Jälgi, milline voog redigeerimise alustas, ja salvesta ainult enda alustatud seanss |
| Kõrge | Asukohaloendi **Vali kõik** ja **Tühjenda valik** ei mõjuta lisamise ulatust; kõik tabeliread töödeldakse | Kasutaja võib arvata, et tühjendas osa või kogu valiku, kuid andmed lisatakse ikkagi | Eemalda selles režiimis eksitavad valikunupud või kasuta lisamisel tegelikku tabelivalikut |
| Kõrge | **Lisa valitud** ei nõua tähelepanukontrolli läbimist ning **Lisa ilma kontrollita** rakendab juba loodud arhiiviplaani | Nuppude nimed ei vasta tegelikule kontrolli- ja andmemõjule | Seo kontrollitud lisamine kehtiva kontrollitulemusega ning lisa arhiiviplaani eraldi kinnitamine |
| Kõrge | Lisamisjärjekord neelab üksuse erandid ja loendab töödeldud üksuse tehtuks sõltumata tulemusest | Lõpu edenemisnäit võib jätta vale mulje täielikust õnnestumisest | Kogu iga tunnuse olek, kuva edukate, vahele jäetud ja vigaste kirjete koond ning paku vigaste eksporti |
| Kõrge | Arhiveerimise ja taastamise üksiktulemusi ei tagastata tegevusteenusele; kasutajale kuvatakse üldine edu ka ebaõnnestumiste korral | Kasutaja ei tea, millised kirjed tegelikult muutusid | Tagasta struktureeritud tulemused ja kuva tunnuste kaupa koondraport |
| Keskmine | Geospatiali režiimis lubatakse **Lisa kinnistuid** ilma impordikihita ning veavaate järel jätkub dialoogi initsialiseerimine puuduvate juhtelementidega | Nupuvajutus võib põhjustada programmivea | Arvuta nupu olek impordikihi järgi ka Geospatiali režiimis ja lõpeta konstruktor puuduva kihi veavaates ohutult |
| Keskmine | Eri nimega SHP-de import võib jätta mitu märgendatud mälukihti; töövoog kasutab esimest, mitte tingimata uusimat | Lisada võidakse vana impordi kinnistud | Luba üks kanooniline impordikiht või küsi kasutajalt aktiivne impordikiht |
| Keskmine | Kaardivaliku kontroller ei käsitle objekti valimata `Esc`-i, paremklõpsu ega tööriistavahetust lõpetamisena | Visuaali aken või lisamisdialoog võib jääda minimeerituks | Kuula kaarditööriista deaktiveerimist ja taasta kasutajaliides katkestussignaaliga |
| Keskmine | Olemasoleva Kavitro kirje samade tunnuste korral käivitatakse uuendus enne impordi uuemuse otsuse rakendamist | Vanemad impordiandmed võivad taustakirje välju üle kirjutada | Uuenda ainult uuema või kasutaja kinnitatud impordi korral |
| Keskmine | **Kustuta ID järgi** ei kuva kustutatava kirje eelvaadet ega puuduta QGIS-i kihti | Vale sisemise ID sisestamine on raskesti kontrollitav ja andmeallikad lahknevad | Laadi enne kinnitamist kirje nimi ja tunnus ning paku kontrollitud kihisünkroonimist |
| Keskmine | Kiirete järjestikuste kaardivalikute seoste päringuid ei eristata kinnistu kaupa | Vanem vastus võib kuvada vale kinnistu seotud kirjed | Tühista vana töö või kasuta iga valiku jaoks eraldi päringutunnust |
| Madal | Maa-ameti lingi avamise ebaõnnestumine ei kuva kasutajale teadet | Nupp näib mittetöötav | Kuva vigase URL-i või avamisvea korral hoiatus |
| Madal | Mitmed impordi edenemistekstid ja failifiltri **All files** tekst on ingliskeelsed | Keelekasutus on ebaühtlane | Vii tekstid tõlkevõtmetesse ja piira failivalik vajaduse korral SHP-le |
| Madal | Seotud andmerühma noolenupul puudub kirjeldav kohtspikker | Funktsioon on klaviatuuri- ja abitehnoloogia kasutajale raskemini mõistetav | Lisa „Näita/peida seotud kirjed“ kohtspikker ja ligipääsetav nimi |

## Soovituslik turvaline tööjärjekord

1. Hoia QGIS-i põhi- ja arhiivikiht enne massitoimingut redigeerimisrežiimist väljas ning tee andmetest varukoopia.
2. Veendu, et projektis oleks ainult üks soovitud impordimärgendiga kiht.
3. Kontrolli kaardi- või asukohavaliku järel tabeli tegelikku ridade arvu.
4. Ära käivita piiratud valikul tähelepanukontrolli enne kriitilise arhiiviplaani vea parandamist.
5. Lisa esmalt väike proovikogum ilma varasema kontrolliplaanita.
6. Võrdle pärast lisamist eraldi Kavitro kirjeid, põhikihti ja arhiivikihti.
7. Kasuta **Kustuta ID järgi** ainult siis, kui sisemine Kavitro ID on sõltumatult kontrollitud.

## Seotud juhendid

- [Kinnistute nupud](04_kinnistute_nupud.md)
- [Kinnistute kihi seadistamine ja haldamine](../05_kinnistute_kihi_seadistamine_ja_haldamine.md)
- [Kinnistute mooduli kasutamine](../15_kinnistute_mooduli_kasutamine.md)
- [Seadistuste nuppude detailaudit](03_01_seadistuste_nuppude_detailaudit.md)
- [Loendite, filtrite ja kirjekaartide nupud](02_loendid_filtrid_ja_kirjekaardid.md)
- [Failide ja ühisdialoogide nupud](09_failide_ja_uhisdialoogide_nupud.md)
