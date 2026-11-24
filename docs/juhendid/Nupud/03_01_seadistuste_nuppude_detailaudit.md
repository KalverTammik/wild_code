# Seadistuste nuppude detailaudit

See juhend kirjeldab Visuaali seadistusnuppude tegelikku käitumist praeguse koodibaasi järgi. Kaetud on ühine salvestamine, kaartide lähtestamine, Geospatiali režiim, kanalisatsiooniliikide kaardistus, ajutiste GeoPackage-kihtide abilised, Geospatiali mapper ning projektide ja servituutide lisaseadistuste nupud.

Kinnistute lisamise, eemaldamise ja impordi nupud asuvad küll kinnistute seadistuskaardil, kuid nende detailaudit kuulub faili [Kinnistute nupud](04_kinnistute_nupud.md).

## Kolm erinevat rakendumisviisi

Seadistuste vaates ei käitu kõik nupud ühtemoodi. Enne toimingut kontrolli, millisesse rühma nupp kuulub.

| Rakendumisviis | Nupud | Kas **Hülga** saab toimingu tagasi võtta? |
|---|---|:---:|
| Ootel muudatus | **Ühenda Geospatiali kaudu**, **Lülita käsitsi seadistusele**, lisaväärtuse hammasratas ja **Tühjenda väärtus** | Jah, kuni üldist **Kinnita** nuppu pole vajutatud |
| Kohene seadistuse kustutamine | Kõik kaartide **Lähtesta** nupud | Ei |
| Kohene faili- või kihitoiming | Ajutise GPKG-kihi abilised ja mapperi **Kanna andmed üle** | Ei |

Üldine **Kinnita** ei ole mapperi ega ajutise kihi tööriista lõppkinnitus. Need tööriistad võivad QGIS-i projekti, faili või kihti muuta juba oma töövoo sees.

## Üldine Kinnita

### Nähtavus ja asukoht

**Kinnita** asub kogu seadistuste vaate all ühises jaluses. Nupp ja jalus on peidetud, kuni vähemalt ühel kaardil või kasutaja seadetes on ootel muudatus.

Ootel muudatuse võivad tekitada näiteks:

- vaikimisi avatava mooduli või QGIS-i kaardipaani valik;
- baaskihi, Geospatiali režiimi või kanalisatsioonikaardistuse muutmine;
- mooduli põhi- või arhiivikihi valimine;
- eelistatud staatuste, liikide, tunnuste või „Alustamata“ staatuste muutmine;
- projektikausta tee, nimereegli või servituudi staatuste seose muutmine.

### Mida nupp teeb

Klõpsamisel salvestatakse muudatused selles järjekorras:

1. QGIS-i projekti baaskihtide kaart;
2. kõik kasutajale loodud moodulikaardid;
3. kasutaja avamooduli ning **Sisestuspaani** ja **Otsingupaani** seaded;
4. kaardipaanide nähtavus sünkroonitakse uue seadistusega.

Iga kaart salvestub eraldi ja annab oma tulemuse tagasi. Ühine tehing puudub: ühe kaardi viga ei peata teiste kaartide salvestamist.

Edu korral muutuvad kaardi ootel väärtused selle uueks algolekuks. Kui kõik salvestusid, kaob **Kinnita** nupp; eraldi eduteadet ei kuvata.

Kui mõne kaardi salvestamine ebaõnnestub, kuvatakse üks hoiatus **Seadeid ei saanud salvestada**, mis nimetab need kaardid. Ebaõnnestunud kaardi muudatused jäävad ootele ja **Kinnita** jääb nähtavale, nii et uus vajutus proovib need uuesti salvestada. Õnnestunud kaardid muutuvad puhtaks. Kaardi sees võivad osa väärtusi olla juba kirjutatud; kordussalvestus kirjutab need samade väärtustega üle.

**Kinnita** ei salvesta QGIS-i redigeerimisrežiimis olevaid mapperi kihimuudatusi. Need tuleb vajaduse korral salvestada QGIS-i enda käsuga **Salvesta kihi muudatused**.

### Katkestamine ja seadistustest lahkumine

Ühises jaluses eraldi **Tühista** nuppu ei ole. Kui kasutaja proovib ootel muudatustega seadistustest lahkuda või akent tavaliselt sulgeda, avaneb valik:

- **Salvesta** – käivitab sama salvestamise nagu **Kinnita**; kui mõni kaart ei salvestunud, jääb kasutaja pärast hoiatust seadistuste vaatesse;
- **Hülga** – taastab viimati salvestatud ootel väärtused;
- **Tühista** – jääb seadistuste vaatesse.

**Hülga** ei taasta enne seda vajutatud **Lähtesta** nupu kustutusi, loodud või üle kirjutatud GeoPackage-faili ega mapperiga muudetud objekte.

## Lähtesta

### Asukoht

**Lähtesta** asub kaardi päise paremas servas:

- kaardil **QGIS projekti baaskihid**;
- kinnistute, projektide, lepingute, kooskõlastuste, servituutide, tööde ja teostusjooniste kaartidel, kui vastav kaart on kasutajale kuvatud.

Nupp on nähtav sõltumata sellest, kas kaardil on seadistus juba olemas.

### Baaskihtide kaardi lähtestamine

Pärast kinnitust tühjendab nupp ootel muudatusena (salvestub alles üldise **Kinnita** nupuga):

- baaskihtide viited;
- EVEL-i automaattuvastuse oleku;
- ühise kanalisatsioonikihi tüübi välja ja kaardistusread;
- Geospatiali seadistusrežiimi.

Kaart lülitub tühja käsitsi seadistuse olekusse. QGIS-i kihte, kihifaile ega objekte ei kustutata.

### Moodulikaardi lähtestamine

Pärast kinnitust tühjendab nupp ootel muudatusena vastava mooduli:

- põhi- ja toetatud moodulitel arhiivikihi viite;
- eelistatud staatused, liigid ja tunnused;
- projekti tahvli „Alustamata“ staatuste valiku;
- projektide kaustateed ja nimereegli või servituudi staatuste seose.

Lähtestamine ei kustuta QGIS-i kihti, GeoPackage-faili, projektikausta ega kihiobjekte.

### Kinnitus ja tagasivõtmine

**Lähtesta** küsib enne kinnitust (vaikimisi **Tühista**). Lähtestus jääb ootele: üldine **Kinnita** salvestab selle, seadistustest lahkumise **Hülga** taastab kõik endised väärtused, ka kihivaliku ja lisaväärtused.

## Ühenda Geospatiali kaudu

Nupp asub kaardil **QGIS projekti baaskihid** ja on selle tekstiga nähtav käsitsi seadistusrežiimis.

Klõps avab selgituse, et praegune Geospatiali režiim on ettevalmistav integratsioonivoog ega määra baaskihte automaatselt.

| Dialoogi nupp | Tulemus |
|---|---|
| **OK** | Võtab Geospatiali režiimi ootele, peidab kohe käsitsi baaskihtide ala ja kuvab moodulikaartidel mapperi jaotise |
| **Cancel / Tühista** | Sulgeb selgituse režiimi muutmata |

Režiimi püsivaks salvestamiseks tuleb vajutada üldist **Kinnita** nuppu. Enne seda taastab seadistustest lahkumise **Hülga** varasema režiimi.

Kuigi Geospatiali režiim on alles ootel, saab kohe nähtavale ilmunud mapperi avada ja sellega sihtkihti muuta. Mapperi andmemuudatusi **Hülga** tagasi ei võta.

## Lülita käsitsi seadistusele

Kui Geospatiali režiim on valitud, muutub sama nupu tekstiks **Lülita käsitsi seadistusele**. Nupp küsib kinnitust **Kas lülitada käsitsi seadistusele?** (vaikimisi **Tühista**). Dialoog ütleb, et moodulikaartidelt kaob **Ava mapper**, baaskihte saab jälle ise valida ning QGIS-i kihid, moodulite kihivalikud ja mapperiga kantud andmed jäävad alles.

| Kinnitusnupp | Tulemus |
|---|---|
| **Lülita käsitsi seadistusele** | Võtab käsitsi režiimi ootele, näitab baaskihtide välju, peidab mapperi jaotised ja toob tööde kaardile tagasi ajutise kihi abilise |
| **Tühista** | Jätab Geospatiali režiimi valituks |

Käsitsi režiim salvestub alles üldise **Kinnita** vajutamisel; enne seda taastab **Hülga** Geospatiali režiimi. Salvestamisel eemaldatakse ainult Geospatiali režiimi märge. Baaskihtide varasemad valikud, moodulite põhi- ja arhiivikihid ning mapperiga sihtkihti kantud objektid jäävad muutmata.

## Lisa kaardistus

Nupp asub baaskihtide kaardi ühise kanalisatsioonikihi jaotises.

Nupp on nähtav, kui märge **Kasuta üht kanalisatsioonikihti tüüpide ID-kaardistusega** on valitud. Nupp muutub aktiivseks ainult siis, kui:

- kanalisatsioonitorude kiht on olemas;
- Geospatiali režiim ei ole aktiivne;
- vähemalt üks toetatud kanalisatsiooniliik ei ole veel real kasutusel.

Klõps lisab järgmise kasutamata liigiga rea ja täidab selle Kavitro pakutud ID algväärtusega. Rea liiki ja ID-de loendit saab seejärel muuta. Liik **Muud** ei kasuta ID-välja ja hõlmab muude ridadega katmata väärtusi.

Muudatus jääb ootele kuni üldise **Kinnita** vajutamiseni. **Hülga** taastab varem salvestatud read.

Praeguses kasutajaliideses puudub üksiku kaardistusrea eemaldamise nupp. Lisatud rea saab muuta teiseks veel kasutamata liigiks; kogu kaardistuse saab välja lülitada või eemaldada baaskihtide kaardi **Lähtesta** nupuga.

## Loo või lae ajutine GPKG-kiht

Sama töövoogu kasutavad:

- **Loo/lae ajutine Tööde GPKG kiht** – loob punktikihi;
- **Loo/lae ajutine Projektide GPKG kiht** – loob polügoonkihi.

Projektide abiline on nähtav nii käsitsi kui ka Geospatiali režiimis. Tööde abiline on nähtav ainult käsitsi režiimis; Geospatiali režiimis kuvatakse selle asemel mapper.

### Eeltingimus

Abiline vajab kehtivat viitekihti, millelt võtta koordinaatsüsteem. Esmalt kasutatakse kaardil parajasti valitud sobivat moodulikihti, seejärel võimaluse korral seadistatud kinnistute põhikihti. Viitekihi puudumisel kuvatakse hoiatus ja töövoog peatub.

### Nupuvajutuse töövoog

1. Sisesta loodava või laaditava kihi nimi ja kinnita tekstidialoog.
2. Vali **Kasuta viitekihi GeoPackage'i**, **Loo eraldiseisev GeoPackage-fail** või **Tühista**.
3. Eraldiseisva faili korral vali faili asukoht.
4. Olemasoleva faili korral kinnita või tühista kogu faili ülekirjutamine.
5. Abiline laadib sama nimega olemasoleva kihi või loob uue kihi.
6. Valmis kiht lisatakse QGIS-i projekti ja salvestatakse kohe mooduli põhikihiks.

Nime-, salvestusviisi- või failidialoogi katkestamine enne loomist ei muuda midagi.

### Olemasoleva GeoPackage'i kasutamine

Valik **Kasuta viitekihi GeoPackage'i** töötab ainult siis, kui viitekiht pärineb `.gpkg` failist.

- Sama nimega olemasolev kiht laaditakse QGIS-i projekti.
- Puuduva kihi korral luuakse samasse faili uus kiht.
- Faili teisi kihte ei kustutata.

### Eraldiseisva faili ülekirjutamine

Kui valitud eraldiseisev `.gpkg` fail on juba olemas, küsitakse ülekirjutamiseks eraldi kinnitust.

Kinnitus loetleb faili kihid ja projektist eemaldatavad laaditud kihid; vaikimisi valik on **Tühista**. **Kirjuta üle** nimetab vana faili ümber varukoopiaks (`<nimi>.backup-<aeg>.gpkg` samas kaustas) ja loob uue faili; vana faili ei kustutata. Eduteade näitab varukoopia asukohta. Kui faili ei saa ümber nimetada (näiteks on see teises programmis lahti), ei kirjutata midagi üle.

### Salvestushetk ja tagasivõtmine

Eduka loomise või laadimise järel kirjutatakse uus põhikihi viide kohe seadistusse ning kaardi kihivalik sünkroonitakse sellega. Üldist **Kinnita** nuppu ei ole selle toimingu jaoks vaja. **Hülga** ei taasta eelmist põhikihi viidet ega kustuta loodud faili.

## Ava mapper

**Ava mapper** kuvatakse Geospatiali režiimis igal kasutajale loodud moodulikaardil. See võib seega esineda kinnistute, projektide, lepingute, kooskõlastuste, servituutide, tööde ja teostusjooniste kaardil.

Nupu vajutamisel kasutatakse sihtkihina kaardil parajasti valitud põhikihti. Nupp ise jääb aktiivseks ka puuduva või sobimatu sihtkihi korral, kuid dialoogi asemel kuvatakse hoiatus, kui:

- valitud sihtkiht puudub või ei ole kehtiv vektorkiht;
- sihtkihil ei ole peale sisemiste väljade `fid`, `id` ja `geom` ühtegi kaardistatavat välja.

Mapperi avamine ise andmeid ei muuda. Dialoogi **Cancel / Tühista** või sulgemisrist sulgeb vastenduse ilma ülekandeta.

## Kanna andmed üle

Nupp asub Geospatiali mapperi dialoogi all. Enne selle vajutamist valitakse lähtekiht ja kontrollitakse iga sihtvälja automaatselt pakutud lähtevälja või vaikeväärtust.

### Kontroll enne ülekannet

Nupp kontrollib, et lähtekiht oleks kehtiv vektorkiht. Seejärel kuvatakse eraldi kinnitus koos:

- lähtekihi nimega;
- sihtkihi nimega;
- kogu lähtekihi objektide arvuga.

Kinnituse **OK** käivitab ülekande. **Cancel / Tühista** naaseb mapperisse midagi muutmata.

### Tegelik andmemõju

Mapper töötleb kogu lähtekihti, mitte ainult QGIS-is valitud objekte. See kopeerib geomeetria ning kaardistatud lähte- või vaikeväärtused.

Olemasolevaid objekte proovitakse uuendada järgmiste väliste ID-de järgi:

| Moodul | Uuendamiseks kasutatav väli |
|---|---|
| Projektid | `ext_project_id` |
| Tööd | `ext_job_id` |
| Teostusjoonised | `ext_job_id` |
| Servituudid | `ext_easement_id`, selle puudumisel `ext_job_id` |

Teistes moodulites või sobiva ID-välja puudumisel lisatakse objektid uutena.

Ülekanne on üks tehing. Kui mõnda objekti ei saa lisada või selle koordinaate teisendada, võetakse kogu ülekanne tagasi: sihtkiht jääb endisesse seisu ja dialoog jääb avatuks, nii et kordamine ei dubleeri midagi. Kui ülekanne salvestati, aga mõni väärtus jäi sobimatu tüübi tõttu tühjaks, kuvatakse hoiatus ja dialoog suletakse. Sihtkiht, mis on juba redigeerimisrežiimis, lükatakse tagasi.

Kui lähte- või sihtkihil puudub koordinaatsüsteem või nende vahel ei saa teisendust luua, peatatakse ülekanne enne kinnitust ja kuvatakse põhjus; objekte ei kopeerita teisendamata koordinaatidega.

Üldine **Kinnita**, seadistustest lahkumise **Hülga** ja mapperi hilisem sulgemine ei võta salvestatud ülekannet tagasi.

Täielik väljade, vaikeväärtuste, geomeetria ja ID-de juhend on failis „Geospatiali kihtide vastendamine“ ([Kavitro abikeskus](https://help.kavitro.com/et)).

## Hammasrattaikoon – vali väärtus

Hammasrattaikoon asub projektide ja servituutide kaartide lisaväärtuste ridadel.

| Rida | Avatav tööriist |
|---|---|
| **Projektide lähtekaust** | Operatsioonisüsteemi kaustavalija |
| **Projektide sihtkaust** | Operatsioonisüsteemi kaustavalija |
| **Eelistatud kausta nime struktuuri reegel** | Kolmeosaline nimereegli dialoog |
| **Servituudi kihi staatuste seos** | Kavitro taustastaatuste ja QGIS-i kihiväärtuste vastendamise dialoog |

Valitud väärtus kuvatakse kaardil ja jääb ootele. Selle salvestamiseks tuleb vajutada üldist **Kinnita** nuppu; **Hülga** taastab varasema väärtuse.

Hammasrattanupul ei ole praegu nähtavat teksti ega kohtspikrit. Nupu tähendus tuleb tuletada rea nimetusest.

## Tühjenda väärtus

Punase ikooniga nupp asub iga eelnevas tabelis nimetatud hammasratta kõrval. Kohtspikker on **Tühjenda väärtus**.

Nupp eemaldab väärtuse ainult ootel olekust. Üldine **Kinnita** salvestab tühjenduse, **Hülga** taastab varem salvestatud väärtuse.

Projektide kaustatee tühjendamine takistab vastavat projektikausta töövoogu. Servituudi staatuste seose tühjendamine ei tühjenda olemasolevate kihiobjektide väärtusi; hilisem kirjutamine võib otsese vaste puudumisel kasutada Kavitro staatuse nime.

## Kausta nimetamise reegli dialoog

Dialoogis saab määrata kuni kolm järjestikust osa: projekti number, projekti nimi, sümbol või tühi koht. Eelvaade uueneb valikute tegemisel.

| Nupp | Tulemus |
|---|---|
| **OK** | Kontrollib reeglit, sulgeb dialoogi ja võtab reegli seadistuskaardil ootele |
| **Cancel / Tühista** | Sulgeb dialoogi ning jätab varasema reegli muutmata |

**OK** ei luba täiesti tühja reeglit ega tühja tekstiga sümboliosa. Pärast dialoogi tuleb vajutada üldist **Kinnita** nuppu.

Seadistusnupu sündmusekäsitleja kasutab lisaväärtuste ühist kolme argumendiga lepingut: moodul, seadistusvõti ja praegune väärtus. Dialoogi avajale antakse neist edasi praegune väärtus. Seetõttu avaneb dialoog ka väärtuse **Määramata** korral, **Cancel / Tühista** tagastab senise väärtuse ning **OK** saab anda seadistuskaardile uue ootel reegli.

Salvestatud reegel rakendub sõltumata varasemast peidetud lipust **Luba eelistatud kausta nime struktuur**. Kui reegel puudub, kasutatakse vaikereeglit „projekti number + projekti nimi”. Projektinumber loetakse nii uuema `projectNumber` kui ka projektipäringu tegeliku `number` välja kaudu. Kui rakendatav reegel nõuab projektinumbrit, kuid kumbki väli ei sisalda väärtust, kausta loomine peatatakse ja kasutajale kuvatakse hoiatus.

## Servituudi staatuste vastendamise dialoog

Dialoogi avamiseks peab olema juba salvestatud:

- kehtiv servituutide põhikiht;
- sellel väli `Staatus`, `staatus` või `status`;
- staatuseväljal QGIS-i väärtuskaart või vähemalt üks kihil esinev näidisväärtus;
- Kavitro teenusest laaditav servituudi staatuste loend.

Parajasti ootel, kuid veel kinnitamata põhikihi valikut dialoog ei kasuta. Uue põhikihi korral vajuta esmalt üldist **Kinnita** nuppu ja ava seejärel staatuste seos.

| Nupp | Tulemus |
|---|---|
| **OK** | Koostab ainult täidetud vastendustest JSON-väärtuse ja võtab selle seadistuskaardil ootele |
| **Cancel / Tühista** | Sulgeb dialoogi ja jätab varasema seose muutmata |

Pärast **OK** vajutamist tuleb seos salvestada üldise **Kinnita** nupuga. Valik **Ära kirjuta** jätab vastava staatuse salvestatud vastendusest välja; sellise staatusega servituudi salvestamisel jääb kihi staatuseväli puutumata.

## Nuppude mõju koondtabel

| Nupp | Seadistus muutub kohe | QGIS-i kiht või fail muutub kohe | Vajab üldist **Kinnita** | **Hülga** taastab |
|---|:---:|:---:|:---:|:---:|
| **Kinnita** | Jah | Ainult kaardipaanide nähtavus | – | Ei |
| **Lähtesta** | Jah | Ei | Ei | Ei |
| **Ühenda Geospatiali kaudu** / **Lülita käsitsi seadistusele** | Ei | Ei | Jah | Jah |
| **Lisa kaardistus** | Ei | Ei | Jah | Jah |
| **Loo/lae ajutine Tööde GPKG kiht** | Jah | Jah | Ei | Ei |
| **Loo/lae ajutine Projektide GPKG kiht** | Jah | Jah | Ei | Ei |
| **Ava mapper** | Ei | Ei | Ei | – |
| **Kanna andmed üle** | Ei | Jah | Ei | Ei |
| Lisaväärtuse hammasratas | Ei | Ei | Jah | Jah |
| **Tühjenda väärtus** | Ei | Ei | Jah | Jah |

## Auditi käigus leitud parandamist vajavad kohad

Leiud on 2026-11-24 koodi vastu üle kontrollitud ja parandatud leiud on eemaldatud. Avatud leide praegu ei ole.

## Turvaline tööjärjekord

1. Tee tavalised kihi-, filtri- ja lisaväärtuste valikud.
2. Salvesta need üldise **Kinnita** nupuga.
3. Tee enne GeoPackage'i ülekirjutamist failist varukoopia.
4. Ava mapper alles pärast sihtkihi, CRS-i ja väliste ID-de kontrollimist.
5. Katseta mapperit võimaluse korral lähtekihi väikese koopiaga.
6. Kontrolli pärast ülekannet objektide arvu, geomeetria asukohta ja duplikaate.
7. Kui sihtkiht oli redigeerimisrežiimis, salvesta või tühista muudatused QGIS-is.

## Seotud juhendid

- [Seadistuste nupud](03_seadistuste_nupud.md)
- Kasutusjuhendid: [Kavitro abikeskus](https://help.kavitro.com/et)
