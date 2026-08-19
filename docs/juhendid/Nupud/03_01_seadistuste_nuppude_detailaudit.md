# Seadistuste nuppude detailaudit

See juhend kirjeldab Visuaali seadistusnuppude tegelikku käitumist praeguse koodibaasi järgi. Kaetud on ühine salvestamine, kaartide lähtestamine, Geospatiali režiim, kanalisatsiooniliikide kaardistus, ajutiste GeoPackage-kihtide abilised, Geospatiali mapper ning projektide ja servituutide lisaseadistuste nupud.

Kinnistute lisamise, eemaldamise ja impordi nupud asuvad küll kinnistute seadistuskaardil, kuid nende detailaudit kuulub faili [Kinnistute nupud](04_kinnistute_nupud.md).

## Kolm erinevat rakendumisviisi

Seadistuste vaates ei käitu kõik nupud ühtemoodi. Enne toimingut kontrolli, millisesse rühma nupp kuulub.

| Rakendumisviis | Nupud | Kas **Hülga** saab toimingu tagasi võtta? |
|---|---|:---:|
| Ootel muudatus | **Ühenda Geospatiali kaudu**, **Vaata Geospatiali seadistust**, lisaväärtuse hammasratas ja **Tühjenda väärtus** | Jah, kuni üldist **Kinnita** nuppu pole vajutatud |
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

Klõpsamisel rakendatakse muudatused selles järjekorras:

1. QGIS-i projekti baaskihtide kaart;
2. kõik kasutajale loodud moodulikaardid;
3. kasutaja avamooduli ning **Sisestuspaani** ja **Otsingupaani** seaded;
4. kaardipaanide nähtavus sünkroonitakse uue seadistusega.

Edu korral muutuvad ootel väärtused kaartide uueks algolekuks ja **Kinnita** nupp kaob. Eraldi eduteadet ei kuvata.

**Kinnita** ei salvesta QGIS-i redigeerimisrežiimis olevaid mapperi kihimuudatusi. Need tuleb vajaduse korral salvestada QGIS-i enda käsuga **Salvesta kihi muudatused**.

### Katkestamine ja seadistustest lahkumine

Ühises jaluses eraldi **Tühista** nuppu ei ole. Kui kasutaja proovib ootel muudatustega seadistustest lahkuda või akent tavaliselt sulgeda, avaneb valik:

- **Salvesta** – käivitab sama rakendamise nagu **Kinnita**;
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

Nupp eemaldab kohe avatud QGIS-i projekti salvestusest:

- baaskihtide viited;
- EVEL-i automaattuvastuse oleku;
- ühise kanalisatsioonikihi tüübi välja ja kaardistusread;
- Geospatiali seadistusrežiimi.

Kaart lülitub tühja käsitsi seadistuse olekusse. QGIS-i kihte, kihifaile ega objekte ei kustutata.

### Moodulikaardi lähtestamine

Nupp eemaldab kohe vastava mooduli:

- põhi- ja toetatud moodulitel arhiivikihi viite;
- eelistatud staatused, liigid ja tunnused;
- projekti tahvli „Alustamata“ staatuste valiku;
- projektide kaustateed ja nimereegli või servituudi staatuste seose.

Lähtestamine ei kustuta QGIS-i kihti, GeoPackage-faili, projektikausta ega kihiobjekte.

### Oluline praegune käitumine

**Lähtesta ei küsi kinnitust.** Kustutamine kirjutatakse salvestusse juba nupu vajutamisel, mitte üldise **Kinnita** kaudu. Moodulikaardil võib pärast lähtestamist ühine **Kinnita** nupp siiski nähtavale ilmuda, sest kihi valiku ootel ja algne olek võivad ajutiselt erineda.

Seadistustest lahkumise **Hülga** võib sellisel juhul taastada ekraanile vana kihivaliku, kuigi salvestatud kihiviide on juba kustutatud. Ava seadistused uuesti ja kontrolli tegelikku olekut. Turvaline taastamisviis on valida kõik vajalikud väärtused uuesti ja vajutada **Kinnita**.

## Ühenda Geospatiali kaudu

Nupp asub kaardil **QGIS projekti baaskihid** ja on selle tekstiga nähtav käsitsi seadistusrežiimis.

Klõps avab selgituse, et praegune Geospatiali režiim on ettevalmistav integratsioonivoog ega määra baaskihte automaatselt.

| Dialoogi nupp | Tulemus |
|---|---|
| **OK** | Võtab Geospatiali režiimi ootele, peidab kohe käsitsi baaskihtide ala ja kuvab moodulikaartidel mapperi jaotise |
| **Cancel / Tühista** | Sulgeb selgituse režiimi muutmata |

Režiimi püsivaks salvestamiseks tuleb vajutada üldist **Kinnita** nuppu. Enne seda taastab seadistustest lahkumise **Hülga** varasema režiimi.

Kuigi Geospatiali režiim on alles ootel, saab kohe nähtavale ilmunud mapperi avada ja sellega sihtkihti muuta. Mapperi andmemuudatusi **Hülga** tagasi ei võta.

## Vaata Geospatiali seadistust

Kui Geospatiali režiim on valitud, muutub sama nupu tekstiks **Vaata Geospatiali seadistust**. Nimi on eksitav: nupp ei ava seadistuse ülevaadet, vaid küsib Geospatiali režiimi väljalülitamise kinnitust.

| Kinnitusnupp | Tulemus |
|---|---|
| **OK** | Võtab käsitsi režiimi ootele, näitab baaskihtide välju ja peidab mapperi jaotised |
| **Cancel / Tühista** | Jätab Geospatiali režiimi valituks |

Käsitsi režiim salvestub alles üldise **Kinnita** vajutamisel. Režiimi väljalülitamine ei kustuta moodulite põhikihte ega mapperiga sihtkihti kantud objekte, kuigi dialoogi tekst ütleb laiemalt, et eemaldatakse kõik salvestatud Geospatiali seadistused.

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

**Oluline:** **OK** eemaldab QGIS-i projektist kõik selle failiga seotud laaditud kihid ja kustutab kogu olemasoleva GeoPackage-faili koos kõigi selles olnud kihtidega. **Cancel / Tühista** jätab faili alles.

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

Teistes moodulites või sobiva ID-välja puudumisel lisatakse objektid uutena. Korduskäivitus võib seetõttu tekitada duplikaate.

Kui sihtkiht ei olnud enne ülekannet redigeerimisrežiimis, proovib mapper muudatused ise salvestada. Kui kiht oli juba redigeerimisrežiimis, jäävad muudatused QGIS-is ootele ja kasutaja peab need eraldi salvestama või tühistama.

Üldine **Kinnita**, seadistustest lahkumise **Hülga** ja mapperi hilisem sulgemine ei võta ülekannet tagasi.

Täielik väljade, vaikeväärtuste, geomeetria ja ID-de juhend on failis [Geospatiali kihtide vastendamine](../06_geospatiali_kihtide_vastendamine.md).

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

Praeguses versioonis kasutatakse salvestatud reeglit ainult siis, kui profiilis on eraldi varasem lipp **Luba eelistatud kausta nime struktuur** sisse lülitatud. Seda lülitit seadistuskaardil ei kuvata. Ilma liputa kasutab kausta loomine vaikereeglit „projekti number + projekti nimi”, isegi kui dialoogis salvestati muu reegel.

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

Pärast **OK** vajutamist tuleb seos salvestada üldise **Kinnita** nupuga. Valik **Ära kirjuta** jätab vastava staatuse salvestatud vastendusest välja; praegune hilisem kihi kirjutamisloogika võib puuduva vaste korral siiski kasutada Kavitro staatuse nime.

## Nuppude mõju koondtabel

| Nupp | Seadistus muutub kohe | QGIS-i kiht või fail muutub kohe | Vajab üldist **Kinnita** | **Hülga** taastab |
|---|:---:|:---:|:---:|:---:|
| **Kinnita** | Jah | Ainult kaardipaanide nähtavus | – | Ei |
| **Lähtesta** | Jah | Ei | Ei | Ei |
| **Ühenda Geospatiali kaudu** / **Vaata Geospatiali seadistust** | Ei | Ei | Jah | Jah |
| **Lisa kaardistus** | Ei | Ei | Jah | Jah |
| **Loo/lae ajutine Tööde GPKG kiht** | Jah | Jah | Ei | Ei |
| **Loo/lae ajutine Projektide GPKG kiht** | Jah | Jah | Ei | Ei |
| **Ava mapper** | Ei | Ei | Ei | – |
| **Kanna andmed üle** | Ei | Jah | Ei | Ei |
| Lisaväärtuse hammasratas | Ei | Ei | Jah | Jah |
| **Tühjenda väärtus** | Ei | Ei | Jah | Jah |

## Auditi käigus leitud parandamist vajavad kohad

| Prioriteet | Leid | Kasutajarisk | Soovitatav parandus |
|---|---|---|---|
| Kõrge | **Lähtesta** ei küsi kinnitust ja kustutab seaded enne üldist salvestamist | Üks juhuklõps võib muuta mooduli kasutuskõlbmatuks; **Hülga** ei taasta kustutust | Lisa selge kinnitus ning hoia lähtestus ootel kuni üldise **Kinnita** vajutamiseni |
| Kõrge | Moodulikaardi lähtestus võib pärast **Hülga** kuvada vana kihivalikut, kuigi salvestatud viide on juba tühi | Ekraan ja tegelik salvestus võivad lahkneda | Lähtesta korraga ainult ootel olek või laadi pärast kohest kustutust kogu kaart salvestusest uuesti |
| Kõrge | Eraldiseisva GeoPackage'i ülekirjutamine kustutab kogu faili ja eemaldab projektist kõik selle faili kihid | Kaovad ka sama faili teised, tööriistaga mitteseotud kihid | Näita kinnituses kustutatavate kihtide loendit, nõua tugevamat kinnitust ja soovita või loo varukoopia |
| Kõrge | Mapper võib osa objekte edukalt kirjutada ja alles seejärel vigadest teatada; vigadega dialoog jääb avatuks | Uuesti vajutamine võib juba lisatud objektid dubleerida | Kasuta terviklikku tehingut või märgi osaline tulemus üheselt ja blokeeri pime korduskäivitus |
| Kõrge | Koordinaatteisenduse loomise või rakendamise viga ei peata mapperit, vaid kasutada võidakse teisendamata geomeetriat | Objektid võivad sattuda valesse asukohta | Peata ülekanne vigase CRS-i või teisendusvea korral ja kuva kasutajale konkreetne viga |
| Keskmine | Mapper lubab valida lähtekihiks sama kihi, mida kasutatakse sihtkihina | Võimalik on iseendasse kopeerimine ja duplikaadid | Välista sihtkiht lähtekihi valikust ning kontrolli võrdsust enne ülekannet |
| Keskmine | Üldine **Kinnita** salvestab kaardid järjestikku, ilma ühise tehingu ja koondveateateta; mõned salvestusabilised logivad vea, kuid ei anna seda kutsujale tagasi | Vea korral võib osa seadeid salvestuda ja kasutajaliides siiski puhta oleku näidata | Kogu salvestustulemused, näita ebaõnnestunud kaardid ja jäta need ootel olekusse |
| Keskmine | **Vaata Geospatiali seadistust** käivitab väljalülitamise ning dialoogi väide kõigi Geospatiali seadete eemaldamisest on tegelikust mõjust laiem | Kasutaja võib eeldada üksnes ülevaadet või andmete kustumist | Nimeta nupp **Lülita käsitsi seadistusele** ja täpsusta dialoogis, et kihid ning mapperiga kantud andmed säilivad |
| Keskmine | Servituudi staatuste dialoog kasutab ainult salvestatud põhikihti ja laadib Kavitro staatused avamisvoos kaks korda | Uus ootel kiht näib vigane ning avamine teeb tarbetu topeltpäringu | Kasuta kaardil valitud kihti või selgita salvestusnõuet kasutajaliideses; anna juba laaditud staatused dialoogile kaasa |
| Keskmine | Salvestatud projektikausta nimereegel ei rakendu ilma peidetud varasema lubamisliputa | Dialoogis kinnitatud reegel võib jääda kasutamata | Kuva lubamislüliti või käsitle kehtiva reegli olemasolu automaatselt lubamisena |
| Madal | Ühiskanalisatsiooni üksikut kaardistusrida ei saa eemaldada | Ekslikku lisarida ei saa otse kustutada | Lisa igale reale eemaldamisnupp |
| Madal | Lisaväärtuste hammasrattal puudub tekst ja kohtspikker; kaustavalija pealkiri on koodis ingliskeelne **Select folder** | Funktsiooni on raske avastada ning keelekasutus on ebaühtlane | Lisa rea tegevust kirjeldav kohtspikker ja tõlgitud kaustavalija pealkiri |

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
- [Kavitro seadistuste mooduli kasutamine](../01_seadistuste_mooduli_kasutamine.md)
- [QGIS-i projekti baaskihtide seadistamine](../03_qgis_projekti_baaskihtide_seadistamine.md)
- [Mooduli kihtide ja filtrieelistuste seadistamine](../04_mooduli_kihtide_ja_filtrieelistuste_seadistamine.md)
- [Geospatiali kihtide vastendamine](../06_geospatiali_kihtide_vastendamine.md)
- [Projektide mooduli seadistamine](../07_projektide_mooduli_seadistamine.md)
- [Servituutide mooduli seadistamine](../08_servituutide_mooduli_seadistamine.md)
- [Tööde ja teostusjooniste seadistamine](../09_toode_ja_teostusjooniste_seadistamine.md)
