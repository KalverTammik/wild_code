# Filtrite nuppude detailaudit

See juhend kirjeldab Visuaali moodulite filtrirea nuppude tegelikku käitumist praeguse koodibaasi järgi. Siin käsitletakse staatuse-, liigi- ja tunnusevalikuid, filtrite värskendamist ja tühjendamist ning tähtaja kiirnuppe.

Filtrid muudavad eelkõige ekraanil kuvatavat Kavitro kirjete loendit. Erand on **Tööde** mooduli **Värskenda filtreid** ja **Tühjenda filtrivalikud**: enne loendi laadimist võib tööde põhikihi sünkroonimine uuendada QGIS-i kihil olemasolevate tööobjektide atribuute või geomeetriat Kavitro andmete järgi.

## Filtrite olemasolu mooduliti

| Moodul | Staatus | Liik | Tunnused | Tähtaja kiirnupud |
|---|:---:|:---:|:---:|:---:|
| Projektid | Jah | Ei | Jah | Jah |
| Lepingud | Jah | Jah | Jah | Jah |
| Kooskõlastused | Jah | Jah | Jah | Jah |
| Servituudid | Jah | Jah | Ei | Ei |
| Tööd | Jah | Jah | Ei | Ei |
| Teostusjoonised | Jah | Jah | Ei | Ei |

Kinnistute moodulil sellist filtririda ei ole.

## Filtrirea üldine tööpõhimõte

- Filtrivalikud laaditakse Kavitrost mooduli esmakordsel avamisel.
- Laadimise ajal näitab väli laadimisteadet ja valikut ei saa avada.
- Seadistustes salvestatud eelistused märgitakse algvalikuks.
- Valik rakendub kohe. Eraldi **Rakenda** või **OK** nuppu ei ole.
- Iga valikumuudatus tühjendab senise loendivaate, viib loendi algusesse ja käivitab uue laadimise.
- Filtrirea valik ei muuda Kavitro kirje staatust, liiki ega tunnuseid ning ei salvesta uut filtrieelistust seadistustesse.
- Staatuse-, liigi- ja tunnusefilter kombineeritakse omavahel tingimusega **JA**.
- Sama filtri sees vastab kirje vähemalt ühele valitud väärtusele.

Näiteks kahe staatuse ja ühe tunnuse valimisel kuvatakse kirjed, millel on üks valitud staatustest **ja** valitud tunnus.

## Staatuste järgi filtreerimine

### Asukoht ja avamine

Nupp **Staatuste järgi filtreerimine** asub mooduli loendi kohal filtrirea vasakus osas. Klõps avab mitmikvaliku; sama välja uuesti klõpsamine või hüpikust väljapoole klõpsamine sulgeb valiku.

Staatused on rühmitatud Kavitro staatuse tüübi järgi ja kuvatakse järjekorras:

1. **AVATUD**;
2. **SULETUD**;
3. **MUUD** või mõni muu Kavitrost tulnud staatuse tüüp.

Iga staatuse juures kuvatakse selle värvitähis. Rühma pealkiri on ainult jaotis, mitte eraldi valikunupp.

### Nupud ja valikuread

| Nupp või nupulaadne rida | Tulemus |
|---|---|
| **Staatuse rida** | Lisab staatuse valikusse või eemaldab selle sealt; loend laaditakse kohe uuesti. |
| **Vali kõik** | Valib kõik hüpikus saadaolevad staatused ja rakendab need loendile. |
| **Tühjenda valik** | Eemaldab kõik staatusevalikud ja eemaldab päringust staatuse tingimuse. |

Filtriväljal näidatakse valitud staatuste nimesid ja kohtspikris nende täielikku loendit. Mitme valiku korral võib välja nähtav tekst välja laiuse tõttu olla lühendatud.

**Vali kõik** ja **Tühjenda valik** ei ole samaväärsed. Kõigi teadaolevate staatuste valimine nõuab kirjelt üht neist staatustest; tühja valiku korral staatuse tingimust päringusse ei lisata. Seetõttu võib tühjendatud filter kuvada ka staatuseta või tundmatu staatuseväärtusega kirjeid.

## Liigi järgi filtreerimine

### Asukoht ja ülesehitus

Nupp **Liigi järgi filtreerimine** asub staatusefiltri kõrval moodulites, mis liike toetavad. Hüpik koosneb kahest osast:

- vasakul on liigigrupid;
- paremal on parajasti nähtavate gruppide liigid.

Liiginimi, milles sisaldub ` - `, paigutatakse sidekriipsule eelneva nimega gruppi. Muud liigid kuvatakse omaette grupina. Grupi järel olev arv näitab kujul „valitud/kokku”, mitu selle grupi liiki on valitud.

### Nupud ja valikuread

| Nupp või nupulaadne rida | Tulemus |
|---|---|
| **Kõik grupid** | Kuvab paremal kõigi gruppide liigid. See ei vali ega tühjenda liike. |
| **Liigigrupi rida** | Kui kogu grupp ei ole valitud, valib grupi kõik liigid; täielikult valitud grupi uuesti klõpsamine eemaldab selle grupi liigid. |
| **Liigi rida** | Lisab ühe liigi valikusse või eemaldab selle; loend laaditakse kohe uuesti. |
| **Vali kõik** | Valib kõik parajasti paremal nähtavad liigid. Juba valitud, kuid peidetud liikide valik säilib. |
| **Tühjenda valik** | Eemaldab kõik liigivalikud ja kuvab taas kõik grupid. |

Kui liigivalik hõlmab üht gruppi, näidatakse filtriväljal ka grupi nime. Kuni kahe liigi puhul näidatakse liikide nimesid; suurema valiku puhul valitud liikide arvu.

### Servituutide, tööde ja teostusjooniste erand

Nendes kolmes moodulis kasutatakse seadistustes salvestatud eelistatud liike ka mooduli liigipiirkonna arvutamisel:

- kui liigivalikut pole tehtud, rakendub loendile kogu seadistatud liigipiirkond;
- kui valida piirkonda kuuluvad liigid, rakendub valiku ja piirkonna ühisosa;
- kui valikus on nii piirkonda kuuluvaid kui ka sellest välja jäävaid liike, rakenduvad ainult piirkonda kuuluvad valikud.

Seetõttu ei tähenda **Tühjenda valik** ega kogu filtrirea **Tühjenda filtrivalikud** neis moodulites tingimata „näita kõiki Kavitro liike”. Liigipiirkonna muutmiseks tuleb muuta vastava mooduli eelistatud liike seadistustes.

Praeguses teostuses on servajuht: kui valida ainult seadistatud liigipiirkonnast väljapoole jäävaid liike, muutub arvutatud ühisosa tühjaks ja loendipäringusse ei lisata liigi tingimust. Tulemuseks võib olla oodatust laiem loend, mitte üksnes valitud liik. Sellises olukorras kasuta **Värskenda filtreid** või vali seadistatud piirkonda kuuluv liik.

Lepingute ja kooskõlastuste moodulis eemaldab tühi liigivalik liigi tingimuse täielikult.

## Tunnuste järgi filtreerimine

Nupp **Tunnuste järgi filtreerimine** on projektide, lepingute ja kooskõlastuste filtrireal. Hüpikus on Kavitro tunnuste mitmikvalik.

| Nupp või nupulaadne rida | Tulemus |
|---|---|
| **Tunnuse rida** | Lisab tunnuse valikusse või eemaldab selle; loend laaditakse kohe uuesti. |
| **Vali kõik** | Valib kõik hüpikus laaditud tunnused. |
| **Tühjenda valik** | Eemaldab kõik tunnusevalikud ja tunnuse tingimuse päringust. |

Mitme tunnuse valimisel kasutatakse režiimi **VÄHEMALT ÜKS**: kirjel peab olema vähemalt üks valitud tunnustest, mitte tingimata kõik valitud tunnused.

Ka tunnuste puhul erineb **Vali kõik** tühjast filtrist. Kõigi tunnuste valimine jätab välja tunnusteta kirjed; tühjendamine eemaldab tunnuse tingimuse ja lubab loendisse ka tunnusteta kirjed.

## Värskenda filtreid

Ringnoole ikoon asub filtrirea paremas osas ja selle kohtspikker on **Värskenda filtreid**.

Klõps teeb järgmised toimingud:

1. käivitab vajaduse korral filtrivalikute laadimise;
2. loeb seadistustest mooduli eelistatud staatused, liigid ja tunnused;
3. asendab filtrireal olevad ajutised valikud salvestatud eelistustega;
4. väljub üksiku otsingutulemuse vaatest;
5. tühjendab senise loendi, viib selle algusesse ja laadib kirjed uuesti.

See nupp ei tähenda „laadi samade hetkevalikutega uuesti”. Kui kasutaja on filtrireal teinud seadistustest erineva valiku, taastatakse **Värskenda filtreid** klõpsamisel seadistustes salvestatud valik.

Tööde moodulis käivitab nupp enne loendi värskendamist ka Kavitro andmete sünkroonimise seadistatud tööde põhikihile. Kui kiht on muutmisrežiimis või vajalik seoseväli puudub, jätab sünkroonimine kihi uuendamise vahele.

## Tühjenda filtrivalikud

Ristiikoon asub ringnoole kõrval ja selle kohtspikker on **Tühjenda filtrivalikud**.

Klõps:

1. eemaldab filtrirealt staatuse-, liigi- ja tunnusevalikud;
2. väljub üksiku otsingutulemuse vaatest;
3. tühjendab senise loendi, viib selle algusesse ja laadib kirjed uuesti.

Tühjendamine ei kustuta seadistustes salvestatud eelistusi. Nende taastamiseks klõpsa **Värskenda filtreid** või ava moodul hiljem uuesti.

Servituutide, tööde ja teostusjooniste liigipiirkonna erand jääb kehtima ka kogu filtrirea tühjendamisel. Tööde moodulis käivitub enne loendi laadimist sama põhikihi sünkroonimine nagu värskendamisel.

## Tähtaja kiirnupud

Projektide, lepingute ja kooskõlastuste filtrirea paremas osas on rühm **Kiire!**. Selles on kaks arvuga nuppu:

| Nupp | Rakendatav kuupäevatingimus |
|---|---|
| Vasak arv | Tähtaeg on tänasest varasem. Tänase tähtajaga kirje ei ole üle tähtaja. |
| Parem arv | Tähtaeg on tänasest kuni kolme kalendripäeva kaugusel, mõlemad piirpäevad kaasa arvatud. |

Arvud laaditakse mooduli esmakordsel avamisel. Laadimise ajal kuvatakse `…` ja nupud on passiivsed. Arv näitab kogu mooduli vastava tähtajavahemiku kirjete hulka ega arvesta filtrireal parajasti valitud staatuseid, liike ega tunnuseid.

### Tähtajanupu klõpsamise tegelik koosmõju

- Nupp asendab tavalise loendi staatuse- ja liigitingimuse valitud kuupäevatingimusega.
- Staatuse- ja liigivalikud jäävad filtrireal nähtavaks, kuid tähtajavaates neid päringus ei kasutata.
- Projektide, lepingute ja kooskõlastuste parajasti valitud tunnused jäävad tähtajafiltriga kaasa.
- Seetõttu võib nupu järel kuvatud kirjete arv olla nupul olevast arvust väiksem, kui tunnusefilter on valitud.
- Aktiivne tähtajanupp tõstetakse esile.
- Aktiivse nupu uuesti klõpsamine ei lülita filtrit välja, vaid rakendab sama tähtajafiltri uuesti.
- Tavaloendisse naasmiseks muuda mõnd tavalist filtrit või kasuta **Värskenda filtreid** või **Tühjenda filtrivalikud**.

Projektide moodulis eemaldab tavapärase filtri rakendamine ka tähtajanupu aktiivse kujunduse. Lepingute ja kooskõlastuste praeguses teostuses võib tähtajanupu esiletõstetud kujundus pärast tavaloendisse naasmist nähtavale jääda, kuigi loend ise on juba tavaliste filtritega uuesti laaditud.

Tähtajanupp ei väljuta koodis eraldi üksiku otsingutulemuse režiimist. Kui nuppu kasutatakse kohe pärast otsingust ühe kirje avamist ja loend ei muutu ootuspäraselt, kasuta tavaloendisse naasmiseks filtrirea värskendamise või tühjendamise ikooni.

## Nuppude võrdlus

| Toiming | Kas rakendub kohe? | Kas muudab salvestatud eelistusi? | Kas taastab tavaloendi otsingutulemusest? | Kas muudab kirje andmeid? |
|---|:---:|:---:|:---:|:---:|
| Staatuse valimine või tühjendamine | Jah | Ei | Jah | Ei |
| Liigi valimine või tühjendamine | Jah | Ei | Jah | Ei |
| Tunnuse valimine või tühjendamine | Jah | Ei | Jah | Ei |
| **Värskenda filtreid** | Jah | Ei; loeb eelistused uuesti | Jah | Üldjuhul ei; Töödes võib sünkroonida põhikihti |
| **Tühjenda filtrivalikud** | Jah | Ei | Jah | Üldjuhul ei; Töödes võib sünkroonida põhikihti |
| Tähtaja vasak või parem arv | Jah | Ei | Mitte eraldi | Ei |

## Soovituslikud töövõtted

### Ajutine kitsendus

1. Ava sobiv staatuse-, liigi- või tunnusevalik.
2. Märgi üks või mitu väärtust; loend uueneb iga muudatuse järel.
3. Töö lõpetamisel klõpsa **Värskenda filtreid**, et taastada seadistatud eelistused.

### Võimalikult lai loend

1. Klõpsa filtrirea **Tühjenda filtrivalikud** ikooni.
2. Arvesta, et servituutide, tööde ja teostusjooniste seadistatud liigipiirkond võib jääda kehtima.
3. Kui vaja on ka sellest piirkonnast väljapoole jäävaid liike, muuda esmalt mooduli eelistatud liike seadistustes.

### Tähtajaliste kirjete kontroll

1. Vaata rühma **Kiire!** vasakut ja paremat arvu.
2. Klõpsa vastavalt üle tähtaja või läheneva tähtajaga kirjete nuppu.
3. Kui tunnusefilter on aktiivne, arvesta, et loend kitseneb veel tunnuste järgi.
4. Naase tavaloendisse filtrirea värskendamise või tühjendamise ikooniga.

## Kui filter ei anna oodatud tulemust

- Kui filtriväljal on laadimisteade, oota valikute laadimise lõppu.
- Kasuta filtrirea tühjendamise ikooni pärast valikute laadimise lõppu; laadimise ajal tehtud tühjenduse järel võivad salvestatud liigi- või tunnuse-eelistused väljal uuesti nähtavale ilmuda.
- Kui **Värskenda filtreid** toob tagasi ootamatu valiku, kontrolli mooduli eelistusi seadistustes.
- Kui **Tühjenda filtrivalikud** ei näita töödes, teostusjoonistes või servituutides kõiki liike, kontrolli seadistatud eelistatud liikide piirkonda.
- Kui mitme tunnuse valik annab oodatust rohkem vasteid, arvesta režiimiga **VÄHEMALT ÜKS**.
- Kui tähtajanupu arv ja loendi kirjete arv erinevad, kontrolli aktiivset tunnusefiltrit.
- Kui filtrivalikute laadimine lõpeb veaga, jääb vastav väli passiivseks; kontrolli Kavitro seanssi ja internetiühendust ning ava moodul uuesti.

## Praeguse teostuse mahupiirid

- Staatusevalikusse laaditakse kuni 100 mooduli staatust.
- Tunnusevalikusse laaditakse kuni 50 mooduli tunnust.
- Liigid laaditakse lehekülgede kaupa kuni kõigi saadaolevate liikide kättesaamiseni.

Kui Kavitros on vastavas moodulis piirist rohkem staatuseid või tunnuseid, ei pruugi hilisemad väärtused filtrivalikus nähtavale ilmuda.

## Seotud juhendid

- [Loendite, filtrite ja kirjekaartide nupud](02_loendid_filtrid_ja_kirjekaardid.md)
- [Üldnuppude ja navigeerimise detailaudit](01_01_uldnuppude_ja_navigeerimise_detailaudit.md)
- [Mooduli kihtide ja filtrieelistuste seadistamine](../04_mooduli_kihtide_ja_filtrieelistuste_seadistamine.md)
- [Kavitro põhiaken, otsing ja ühised töövõtted](../17_kavitro_pohiaken_otsing_ja_uhised_toovotted.md)
