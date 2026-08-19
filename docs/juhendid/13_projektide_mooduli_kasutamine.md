# Projektide mooduli kasutamine

Projektide moodulis saab otsida ja avada projekte, vaadata projektiga seotud tööde edenemist, kuvada projekti ja selle kinnistud kaardil, siduda kinnistuid, luua projektiala ning genereerida ettevalmistatud struktuuriga projektikausta.

Seadistuste kohta vaata juhendeid [Projektide mooduli seadistamine](07_projektide_mooduli_seadistamine.md), [Kinnistute kihi seadistamine ja haldamine](05_kinnistute_kihi_seadistamine_ja_haldamine.md) ning [QGIS-i projekti baaskihtide seadistamine](03_qgis_projekti_baaskihtide_seadistamine.md). Põhiakna, üldotsingu ja korduvate kirjekaarditoimingute ülevaade on juhendis [Kavitro põhiaken, otsing ja ühised töövõtted](17_kavitro_pohiaken_otsing_ja_uhised_toovotted.md).

## Eeltingimused

Enne kaarditoimingute kasutamist veendu, et:

- avatud on õige QGIS-i projekt;
- Kavitro sessioon ja internetiühendus on aktiivsed;
- projektide põhikihiks on valitud polügoonkiht;
- kinnistute põhikiht on seadistatud ja sisaldab katastritunnuse välja;
- projektide põhikiht ja kinnistute kiht on QGIS-i projekti laaditud;
- sul on kihtide muutmiseks ja projektikausta loomiseks vajalikud õigused.

Projektide põhikihi valimist ja vajalikke välju kirjeldab juhend [Projektide mooduli seadistamine](07_projektide_mooduli_seadistamine.md).

## Projektide otsimine ja filtreerimine

Projektide mooduli esmakordsel avamisel rakendab Kavitro seadistustes määratud eelistatud staatused ja tunnused. Need on filtri algvalikud, mitte püsiv piirang.

1. Ava moodul **Projektid**.
2. Sisesta otsingusse projekti nimi, number või muu nähtav tunnus.
3. Muuda vajaduse korral staatuse- ja tunnusefiltri valikuid.
4. Eemalda aktiivsed filtrid, kui soovitud projekt ei ilmu nimekirja.
5. Keri nimekirja lõppu või kasuta jätkulaadimist, kui kõiki tulemusi ei ole veel kuvatud.

## Projektikaardi põhitoimingud

Projektikaardil võivad olla järgmised toimingud:

- **Detailne ülevaade** laiendab või ahendab projektikaardi sees seotud moodulite edenemise tahvli;
- **Ava kaust** avab projekti `filesPath` väljal oleva kausta või veebiaadressi;
- **Ava kirje brauseris** avab sama projekti Kavitro veebirakenduses;
- **Näita kaardil** valib projektiga seotud kinnistud ja proovib fokuseerida projektide põhikihil sama projekti ala;
- **Rohkem toiminguid** avab projektikausta, ala eelvaate, käsitsi joonistamise ja kinnistute sidumise tegevused.

Kaustanupu kasutatavus sõltub sellest, kas projektil on kaustatee juba olemas. Projekti kaardil fokuseerimiseks otsitakse põhikihilt esmalt välja `ext_project_id` järgi sobiv objekt.

## Projekti edenemise tahvel

Projekti detailvaates kuvatakse projekti kinnistute kaudu leitud seotud kirjed kolmes veerus:

- **Alustamata**;
- **Töös**;
- **Tehtud**.

Tahvli avamiseks:

1. Ava soovitud projektikaardi detailne ülevaade.
2. Oota, kuni Kavitro laeb projekti kinnistutega seotud moodulite kirjed.
3. Vaata kirjeid moodulite kaupa rühmitatuna.

Liigitamise loogika on järgmine:

- seadistustes mooduli jaoks **Alustamata** staatuseks märgitud kirje läheb veergu **Alustamata**;
- taustastaatuse tüübiga `CLOSED` kirje läheb veergu **Tehtud**;
- muud leitud kirjed lähevad veergu **Töös**.

Kui projektil ei ole seotud kinnistuid, ei ole tahvlil võimalik seotud moodulite kirjeid leida. Tahvel koondab kirjed kinnistuseoste kaudu ja välistab vaadatava projekti enda.

### Praeguse versiooni piirang

Projektikaardi päring annab detailtahvlile vaikimisi ainult esimese seotud kinnistu. Mitme kinnistuga projekti tahvel ei pruugi seetõttu näidata teiste kinnistute kaudu seotud kirjeid. Lisaks kuvatakse ühe kinnistu ja mooduli kohta kuni 30 kirjet. Ära kasuta tahvlit enne selle piirangu parandamist ainsa täielikkuse kontrollina.

## Projekti ja kinnistute kuvamine kaardil

1. Leia projektide nimekirjast soovitud projekt.
2. Vajuta toimingut **Näita kaardil**.
3. Kavitro küsib teenusest projekti seotud kinnistud ja valib need kinnistute põhikihil.
4. Seejärel otsib Kavitro projektide põhikihilt projektiga seotud ala ja fokuseerib kaardi sellele.

Toiming võib anda osalise tulemuse:

- kui projektiala ei ole põhikihil, kuvatakse siiski seotud kinnistud;
- kui kinnistuseoseid ei ole, saab olemasolevat projektiala siiski fokuseerida;
- kui kumbagi ei leita, kontrolli kihiseadistust, `ext_project_id` väärtust ja kinnistuseoseid.

## Kinnistute sidumine projektiga

Kinnistuid saab siduda projekti toimingust **Seosta kinnistuid** või projekti ala eelvaate dialoogist.

1. Ava projekti **Rohkem toiminguid**.
2. Vali **Seosta kinnistuid**.
3. Märgi kinnistute põhikihil ristkülikvalikuga üks või mitu katastriüksust.
4. Vaata üle dialoogis näidatud senised ja uued kinnistud.
5. Vajaduse korral vali kinnistud uuesti.
6. Kinnita seosed.

Kavitro lahendab valitud katastritunnustele teenuse kinnistute ID-d ja salvestab seosed Kavitro teenuses. Kui mõnele katastritunnusele ID-d ei leita, kuvatakse see õnnestumise teates eraldi.

**Oluline:** kinnitatud uus kaardivalik lisatakse olemasolevatele seostele. Ülevaatedialoog kuvab seniseid seoseid võrdluseks, kuid ei eemalda ega asenda neid.

## Uue projektiala käsitsi joonistamine

Kasuta käsitsi joonistamist siis, kui soovitud ala ei pea täpselt lähtuma seotud kinnistute piiridest.

1. Ava projekti **Rohkem toiminguid**.
2. Vali **Joonista uus seotud ala kaardile**.
3. Kavitro teeb projektide põhikihi nähtavaks ja aktiivseks ning lülitab selle vajaduse korral muutmisrežiimi.
4. Joonista QGIS-i kaardil polügoon ja lõpeta objekti loomine.
5. Kavitro seob uue objekti projektiga, täidab projektiväljad ja proovib saata geomeetria Kavitro teenusesse.
6. Kontrolli õnnestumise või veateadet ja projektide kihti.

Kavitro peidab selle toimingu ajaks QGIS-i tavalise atribuudivormi. Projekti ID, süsteem, nimi, number, detailsus, aktiivsus ja logiväljad täidetakse automaatselt, kui vastavad väljad kihil olemas on.

Kui kihilt puuduvad väljad `ext_project_id`, `ext_system`, `ext_project_name` või `ext_project_number`, proovib Kavitro need enne joonistamist lisada.

### Muutmisrežiimi mõju

- Kui Kavitro käivitas kihi muutmisrežiimi, kinnitab ta eduka toimingu järel muudatused ise.
- Kui sidumine ebaõnnestub, pöörab Kavitro enda alustatud muutmisseansi tagasi.
- Kui kiht oli juba enne toimingut muutmisrežiimis, jätab Kavitro muudatuse ootele. Kasutaja peab kihi muudatused QGIS-is ise salvestama või tühistama.

Kihi salvestamine ja geomeetria saatmine teenusesse on eri sammud. Veateate korral kontrolli mõlemat poolt eraldi.

## Projektiala loomine seotud kinnistutest

Projektiala eelvaade ühendab seotud kinnistute geomeetriad üheks ajutiseks alaks. Tulemusele saab lisada puhvri ja ümardada nurki.

1. Ava projekti **Rohkem toiminguid**.
2. Vali **Ava projekti ala eelvaade**.
3. Dialoog laeb projekti kinnistuseosed, valib kinnistud kaardil ja loob automaatselt eelvaate.
4. Kontrolli sihtkihti, seotud kinnistute loendit ja kinnistu näidiskaarti.
5. Määra vajaduse korral **Puhvri kaugus** vahemikus 0–500 m.
6. Lülita **Ümardatud nurgad** sisse või välja.
7. Määra ümardamise korral **Nurga raadius** vahemikus 0–250 m.
8. Vajuta **Värskenda eelvaadet**, kui soovid seosed uuesti teenusest laadida.
9. Kontrolli kaardile loodud ajutist eelvaatekihti.
10. Vajuta **Salvesta ala kihile**.

Puhvri või nurga valiku muutmisel luuakse eelvaade uuesti. Kinnistud liidetakse esmalt üheks alaks; positiivne puhver kasvatab ala ning nurga ümardamine tehakse väljapoole ja tagasi puhverdades.

### Kinnistute lisamine eelvaate dialoogis

1. Vajuta **Seosta kinnistuid**.
2. Vali kaardilt ristkülikuga vajalikud kinnistud.
3. Vaata senised seosed ja uus valik üle.
4. Kinnita uute seoste lisamine.
5. Dialoog lisab valitud seosed teenusesse ja loob eelvaate värskendatud seoseloendi põhjal uuesti.

### Eelvaate salvestamise tulemus

**Salvesta ala kihile**:

- uuendab sama `ext_project_id`-ga olemasoleva objekti geomeetriat või lisab uue objekti;
- teisendab geomeetria projektide põhikihi koordinaatsüsteemi;
- täidab projekti identiteedi- ja logiväljad;
- salvestab muudatuse kohe ainult siis, kui Kavitro ise muutmisrežiimi alustas.

Kui projektide kiht oli juba muutmisrežiimis, jääb tulemus QGIS-i muutmispuhvrisse ja kasutaja peab kihi ise salvestama.

### Praeguse versiooni piirang

Eelvaate nupp **Salvesta ala kihile** salvestab geomeetria projektide QGIS-i põhikihile, kuid ei saada seda geomeetriat Kavitro teenusesse. Käsitsi joonistamise töövoog proovib geomeetria teenusesse saata.

Seetõttu kontrolli pärast eelvaate salvestamist, kas sinu tööprotsess nõuab geomeetria olemasolu ka Kavitro teenuses. Vajaduse korral kasuta organisatsioonis kokkulepitud eraldi sünkroonimistoimingut.

## Eelvaate puhastamine ja sulgemine

- **Puhasta eelvaade** eemaldab selle projekti ajutised eelvaatekihid.
- Dialoogi sulgemine eemaldab ajutised eelvaatekihid ja kinnistute valiku.
- Puhastamine ei kustuta juba projektide põhikihile salvestatud objekti.
- Eelvaate puhastamine ei tühista teenusesse juba salvestatud kinnistuseoseid.

## Projektikausta genereerimine

1. Ava projekti **Rohkem toiminguid**.
2. Vali **Genereeri projekti kaust**.
3. Kui kaustaseaded puuduvad, suunab Kavitro seadistuste moodulisse.
4. Kinnita hoiatus, et sama sisuga kausta ei ole varem loodud.
5. Kavitro moodustab nime ja kopeerib kogu mallkausta sihtkohta.
6. Pärast kopeerimist vali, kas lisada loodud kausta tee projektile.

Kui sama nimega kaust on juba olemas, Kavitro seda üle ei kirjuta. Kui keeldud kaustalingi lisamisest või lingi salvestamine ebaõnnestub, jääb loodud kaust failisüsteemi alles.

Praeguses koodiversioonis viitab kaustalingi uuendaja vale nimega GraphQL-failile. Pärast kausta kopeerimist valitud lingi lisamise **Jah** lõpeb seetõttu veahoiatusega ning `filesPath` jääb uuendamata. Kontrolli kausta ja projekti kaustateed eraldi.

Kaustade lähte- ja sihtkoha ning nime reegli kohta vaata [Projektide mooduli seadistamine](07_projektide_mooduli_seadistamine.md#projektide-lähtekaust).

## Levinumad olukorrad

### Projekt ei ilmu nimekirja

Eemalda aktiivsed staatuse- ja tunnusefiltrid ning kontrolli, kas järgmine tulemuste plokk on laaditud.

### Näita kaardil kuvab ainult kinnistud

Projektide põhikihilt ei leitud projekti ala. Kontrolli, kas kihil on õige `ext_project_id` väärtus ja kas valitud on õige põhikiht.

### Eelvaadet ei looda

Kontrolli, et projektil oleks vähemalt üks seotud kinnistu, kinnistute põhikiht oleks laaditud ning valitud kinnistute geomeetriad oleksid kehtivad.

### Projektiala ei salvestu

Kontrolli, et projektide põhikiht oleks polügoonkiht, kirjutatav ja kehtiva andmeallikaga. Kui kiht oli juba muutmisrežiimis, vaata QGIS-i ootel muudatusi.

### Käsitsi joonistatud objekt jäi ootele

Kiht oli enne toimingut juba muutmisrežiimis. Salvesta või tühista kihi muudatused QGIS-is käsitsi.

### Tahvel on tühi

Kontrolli projekti kinnistuseoseid. Tahvel leiab seotud moodulite kirjed just projekti kinnistute kaudu.

### Kaust loodi, kuid kaustanupp on endiselt passiivne

Kausta tee jäeti projektile lisamata või teenuse uuendamine ebaõnnestus. Kaust võib sellest hoolimata sihtkohas olemas olla.

## Kontrollnimekiri

Pärast projektitoimingu lõpetamist kontrolli, et:

- projektil on õiged kinnistuseosed;
- projektiala asub õiges põhikihis ja õiges asukohas;
- `ext_project_id` vastab avatud projekti ID-le;
- QGIS-i kihil ei ole ootamatuid salvestamata muudatusi;
- käsitsi joonistamise korral õnnestus vajaduse korral ka geomeetria teenusesse saatmine;
- eelvaatest salvestatud ala puhul on arvestatud teenusesse sünkroonimise piiranguga;
- projektikaust loodi õigesse sihtkohta;
- kaustalink lisati projektile, kui see oli vajalik.
