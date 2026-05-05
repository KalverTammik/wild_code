# Kavitro plugina põhiomaduste ülevaade

## Lühikokkuvõte

Kavitro plugin on QGIS-i integreeritud tööriist, mis koondab ühte aknasse ettevõtte sisemised geoandmete, objektide ja tööprotsesside haldamise töövood. Plugina eesmärk ei ole olla ainult andmete vaatur, vaid praktiline töökeskkond, kus saab liikuda kaardi, äriloogika, seotud objektide ja seadistuste vahel ilma, et kasutaja peaks töö käigus eri süsteemide või käsitsi failihalduse vahel pendeldama.

Sisuliselt seob plugin omavahel kolm tasandit:

- QGIS-i kaardi- ja kihitöö
- backendist laetavad tööobjektid ja nende metaandmed
- moodulipõhised töövood, mis toetavad erinevaid äriprotsesse

## Mille jaoks pluginat kasutatakse

Plugin on mõeldud olukordadeks, kus ruumiandmed ja tööobjektid on omavahel tihedalt seotud. Selle asemel, et hallata projekte, kinnistuid, servituute, töid ja teostusandmeid eraldi kohtades, saab kasutaja avada sobiva mooduli ning töötada kontekstis, kus kaardikiht, objekti detailid, seotud kirjed ja vajalikud tegevused on juba omavahel seotud.

Praktilises kasutuses tähendab see näiteks järgmist:

- kinnistu leidmine ja selle seotud objektide vaatamine
- tööde ja projektide sirvimine koos staatuste, tüüpide ja filtritega
- servituutide ja teostusobjektide haldamine kaardikihi kontekstis
- failikaustade, kihiseadete ja moodulipõhiste eelistuste hoidmine ühes kohas

## Peamised funktsionaalsed tugevused

### 1. Moodulipõhine töölaud

Plugina keskne ülesehitus on moodulipõhine. Kasutaja liigub vasakult külgribalt vastavasse töövaatesse ning iga moodul avab talle konkreetse protsessi jaoks kohandatud sisu. Praegu on põhifookuses järgmised valdkonnad:

- Property ehk kinnistud
- Projects ehk projektid
- Contract ehk lepingud
- Coordination ehk kooskõlastused
- Easements ehk servituudid
- Works ehk tööd
- AsBuilt ehk teostusandmed
- Settings ehk seadistused

Selline jaotus hoiab töövood eraldi, kuid samal ajal ühtse kasutusloogika sees. Moodulid aktiveeritakse dünaamiliselt, mis aitab liidest hoida korrastatud ja vähendab tarbetut koormust korraga ekraanil.

### 2. Sisselogimine ja sessioonihaldus

Plugin kasutab autentimist ning kontrollib sessiooni kehtivust juba käivitamisel. Kui kasutaja sessioon puudub või on aegunud, suunatakse ta esmalt sisselogimisse. See tagab, et andmepäringud ja töövood toimuvad kontrollitud keskkonnas.

Sisselogimisvaade toetab mitut keelt ning sisaldab mugavusfunktsioone nagu parooli nähtavuse lüliti. Sessioon salvestatakse, et töö jätkamine oleks sujuv ka pärast plugina uuesti avamist.

### 3. Backendiga seotud andmelaadimine

Kavitro plugin ei toetu ainult lokaalsetele kihtidele, vaid laeb andmeid ka backendist GraphQL-päringute kaudu. See võimaldab moodulites kuvada ajakohaseid tööobjekte, kasutada filtreid, laadida tulemusi osade kaupa ning avada vajadusel üksikobjekte detailvaates.

Selline lahendus on oluline eelkõige siis, kui andmemaht on suur või kui samade objektidega töötab mitu inimest. Päringuloogika toetab paginatsiooni, filtripõhist laadimist ja vigade klassifitseerimist, mis teeb töökindluse kasutaja jaoks stabiilsemaks.

### 4. QGIS-i kihtide loomine ja haldamine

Plugin toetab erinevaid kihipõhiseid töövooge, mis aitavad backendist või failidest saadud info viia kiiresti kaardile. Töö ei piirdu ainult olemasolevate kihtide vaatamisega, vaid hõlmab ka:

- mälukihtide loomist
- kihtide salvestamist GeoPackage formaati
- imporditud kihtide märgistamist ja korrastamist
- standardiseeritud kihigruppide kasutamist
- omaduste väljade kaardistamist ja ümbertõstmist

See teeb plugina väärtuslikuks eriti olukordades, kus ruumiinfo tuleb mitmest allikast ning see tuleb enne kasutamist ühtlustada või paigutada kindlasse tööstruktuuri.

### 5. Kaardi ja kasutajaliidese sidumine

Oluline tugevus on see, et kaart ja liides ei ole teineteisest lahutatud. Moodulivaates tehtud valikud saavad mõjutada kaardil nähtavat sisu ning kaardikihtide seis saab omakorda toetada tööobjekti käsitlemist. Plugina sees on lahendused objektide valikuks, kihtide esiletõstmiseks, kaardifookuse juhtimiseks ja teatud töövoogudes geomeetria sünkroniseerimiseks.

Kasutaja jaoks tähendab see vähem käsitsi otsimist ja väiksemat ohtu, et töö käigus kaob seos objekti andmete ning selle ruumilise asukoha vahel.

## Moodulite sisuline roll

### Property

Kinnistumoodul on üks plugina kesksemaid osi. Selle roll on aidata leida ja kuvada kinnistuga seotud infot ning siduda see teiste objektidega. Kinnistu ei ole siin ainult üks kirje, vaid lähtepunkt, mille ümber saab vaadata seotud projekte, lepinguid, servituute ja töid.

### Projects

Projektimoodul toetab projektide sirvimist ja korrastamist ning seob selle staatuste, siltide ja kaustastruktuuriga. Lisaks on seadete kaudu võimalik määrata projektidega seotud lähte- ja sihtkaustad ning eelistatud kaustanime reegel. See aitab ühendada GIS-töö ja praktilise failihalduse.

### Contract ja Coordination

Need moodulid toetavad lepingute ja kooskõlastuste töövooge. Nende juures on oluline, et moodulid toetavad tüüpe, staatuseid ja silte, mis tähendab, et kasutaja saab infot struktureerida, filtreerida ja hallata ühtse loogika järgi.

### Easements

Servituudimoodul ühendab backendi staatuseinfo ja QGIS-i kihitöö. Eriti oluline on siin võimalus siduda backendi staatuseid kihi väljaväärtustega, mis teeb servituutide visualiseerimise ja tööseisu tõlgendamise järjepidevamaks.

### Works

Tööde moodul keskendub välitööde või tööobjektide käsitlemisele ning toetab kihiga seotud töövooge. Selle tugevus on seos geomeetria, staatuste ja muude tööobjekti omaduste vahel.

### AsBuilt

Teostusmoodul aitab hallata teostusinfot ning märkusi. Selle roll on oluline seal, kus töö käigus kogutud info peab jääma seotud nii objekti kirjelduse kui ka ruumilise kontekstiga.

### Settings

Seadetemoodul ei ole ainult tehniline lisa, vaid plugina kasutuselevõtu jaoks kriitiline osa. Seal saab hallata moodulipõhiseid eelistusi, staatuseid, tüüpe, silte, arhiveerimiskihi valikuid ning teatud juhtudel ka eraldi nupuvälju või kaustaseadeid. See võimaldab sama pluginat kohandada eri tööprotsesside jaoks ilma, et peaks koodi pidevalt muutma.

## Kasutusmugavust toetavad lisafunktsioonid

Plugin sisaldab mitut funktsiooni, mis ei pruugi olla esimesel vaatamisel kõige nähtavamad, kuid mis mõjutavad tugevalt igapäevast kasutuskogemust.

- Valguse ja tumeda teema tugi
- Mitmekeelne liides
- Keskne otsing kasutajaliideses
- Akna suuruse ja asukoha haldus
- Jalus- ja päiseelemendid ühtse töövoo jaoks
- Diagnostika- ja vealogid, mis aitavad tõrkeid analüüsida

Need detailid aitavad teha plugina stabiilsemaks, järjepidevamaks ja lihtsamini hooldatavaks ka siis, kui funktsionaalsus kasvab.

## Tehniline väärtus kasutaja vaates

Kuigi plugin on kasutajale nähtavalt eelkõige töövahend, on selle taustal mitu tugevat tehnilist lahendust, mille praktiline mõju jõuab otse kasutuskogemusse:

- moodulid laetakse vajaduspõhiselt, mis aitab hoida töö kiirema ja selgema
- teemad ja stiilid on tsentraalselt hallatud, mis teeb liidese ühtlaseks
- logimine ja tõrkeinfo kogumine lihtsustab probleemide lahendamist
- andmete laadimine on üles ehitatud suuremate andmemahtude jaoks
- kihihaldus toetab päris töövooge, mitte ainult demo-taset

Teisisõnu ei ole tegemist pelgalt visuaalse QGIS-i lisapaneeliga, vaid tööriistaga, mille arhitektuur toetab pikemaid ja sisukamaid tööprotsesse.

## Kokkuvõte

Kavitro plugina suurim väärtus seisneb selles, et see toob kokku kaardipõhise töö, backendi andmed ja ettevõtte sisemised protsessid. Plugina loogika ei piirdu ühe vaate või ühe objektitüübiga, vaid toetab mitut omavahel seotud töövaldkonda alates kinnistutest ja projektidest kuni servituutide, tööde ja teostusandmeteni.

Kui seda kirjeldada ühe lausega, siis on Kavitro plugin QGIS-i sisene moodulipõhine töölaud, mis aitab hallata ruumiandmetega seotud tööobjekte, seadistusi ja protsesse ühes koondatud kasutajaliideses.