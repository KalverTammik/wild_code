# Üldnuppude ja navigeerimise detailaudit

See juhend kirjeldab Visuaali üldnuppude tegelikku käitumist praeguse koodibaasi järgi. Kaetud on plugina avamine, sisselogimine, põhiakna päis ja külgriba, üldotsing ning QGIS-i kaardile kuvatavad otsingu- ja sisestuspaanid.

## Nuppude paiknemine

| Nupurühm | Kus seda näeb |
|---|---|
| Plugina avamine | QGIS-i tööriistariba |
| Parooli näitamine ja sisselogimine | Visuaali sisselogimisaken |
| Abi, teema ja väljalogimine | Visuaali põhiakna päis |
| Avaleht, sisumoodulid ja seadistused | Põhiakna vasak külgriba |
| Otsingutulemuste sulgemine ja avamine | Päise või QGIS-i kaardi otsingutulemuste hüpik |
| Otsingu käivitamise ikoon | QGIS-i kaardi **Otsingupaan** |
| Töö loomine, objekti tuvastamine ja GIS-tööde kontroll | QGIS-i kaardi **Sisestuspaan** |

## Visuaali avamine QGIS-ist

### Kavitro / Visuaal

Plugina ikoon asub QGIS-i tööriistaribal. Praegune kood lisab toimingu tööriistaribale, kuid ei lisa eraldi QGIS-i pluginate menüü käsku.

Nupu vajutamisel:

1. kontrollitakse, kas QGIS-i projekt on failina salvestatud;
2. puhastatakse vajaduse korral tühjad ajutised kinnistute impordikihid;
3. laaditakse arvutisse salvestatud sessiooniandmed;
4. kehtiva kohaliku sessiooni korral avatakse või tuuakse ette olemasolev Visuaali aken;
5. puuduva sessiooni korral avatakse sisselogimisaken ning põhiaken kuvatakse pärast edukat sisselogimist.

Püsiv juurdepääsutõend laaditakse QGIS-i autentimishalduri kaitstud autentimiskirjest. QGIS-i tavaseadetes säilitatakse ainult autentimiskirje tunnus, kasutajanimi ja sessiooni olek. Kui autentimishaldur vajab kaitstud kirje avamiseks master-parooli, kuvab QGIS selle küsimuse enne sessiooni taastamist.

Kui QGIS-i projekt pole veel failina salvestatud, kuvatakse hoiatus ja Visuaali põhiakent ei avata. Uus nimeta projekt tuleb esmalt salvestada.

Kui Visuaali aken on juba olemas, ei looda uut akent. Minimeeritud aken taastatakse ja tuuakse ette. Põhiakna tavaline sulgemisrist minimeerib akna ning säilitab sessiooni; tööriistariba nupp taastab sama akna ja aktiivse mooduli. Kui **Seadistustes** on kinnitamata muudatusi, rakendub enne minimeerimist seadistuste salvestamise või hülgamise kontroll ning sulgemise saab katkestada.

Põhiakna esmakordsel avamisel valitakse kasutaja seadistatud avamoodul. Kui seda pole määratud, avatakse **Avaleht**. Puuduliku mooduliseadistuse korral võib avamooduli asemel avaneda **Seadistused**.

## Sisselogimisakna nupud

### Näita parooli

Silmaikoon asub paroolivälja paremas servas ja on lülitatav nupp.

- Esimene klõps muudab parooli tavatekstina nähtavaks.
- Järgmine klõps peidab parooli uuesti.
- Nupp ei muuda ega salvesta parooli.
- Nupul pole klaviatuurifookust, et `Enter` käivitaks sisselogimise, mitte parooli nähtavuse muutmise.

Sisselogimisakna keelevalik on rippvalik, mitte nupp. Keele muutmine salvestab keele-eelistuse ning uuendab akna pealkirja, väljade nimetused ja sisselogimisnupu teksti.

### Logi sisse

Sisselogimise saab käivitada nupuga **Logi sisse** või parooliväljal klahviga `Enter`.

Enne teenusepäringut kontrollitakse välju:

- tühi kasutajanimi märgitakse veaks ja fookus viiakse kasutajanime väljale;
- tühi parool märgitakse veaks ja fookus viiakse parooliväljale;
- uue autentimiskatse alguses eemaldatakse võimalik vana aktiivne sessioon.

Päringu ajal on **Logi sisse** passiivne, et sama toimingut ei saadetaks mitu korda. Teenusepäringu ajalimiit on kümme sekundit.

Sisselogimispäring laaditakse eraldi staatilisest GraphQL-failist. Kasutajanimi ja parool saadetakse GraphQL-i muutujate `input.username` ja `input.password` kaudu, mitte päringudokumenti liidetud tekstina. Nii säilib parool JSON-edastuses muutmata ka jutumärkide, kaldkriipsude, reavahetuste ja Unicode'i märkide korral ning päringudokument ise ei sisalda kasutaja autentimisandmeid.

Eduka sisselogimise järel:

- hoitakse aktiivset juurdepääsutõendit töö ajal mälus;
- juurdepääsutõend salvestatakse püsiva sessiooni jaoks QGIS-i autentimishaldurisse;
- QGIS-i tavaseadetesse salvestatakse ainult autentimiskirje tunnus, kasutajanimi ja sessiooni olek;
- sisestatud Kavitro parooli ei salvestata;
- sisselogimisaken suletakse;
- avatakse Visuaali põhiaken.

QGIS võib autentimishalduri esmakordsel kasutamisel paluda luua master-parooli või olemasoleva master-parooli sisestada. Kui kaitstud salvestamine katkestatakse või ebaõnnestub, ei kirjutata juurdepääsutõendit avatekstina kettale. Kasutaja võib jätkata tööd praeguse QGIS-i käivituse lõpuni, kuid pärast QGIS-i sulgemist tuleb uuesti sisse logida.

Uuenduse järel teisendab Kavitro võimaluse korral vana kohaliku sessiooni automaatselt kaitstud autentimiskirjeks ning eemaldab vana avatekstis juurdepääsutõendi. Kui teisendamine ei õnnestu, kuvatakse hoiatus ja puhastamist proovitakse järgmisel sobival sisselogimisel uuesti.

Ebaõnnestumisel jääb sisselogimisaken avatuks, veaga väli tõstetakse esile ja nupp aktiveeritakse uueks katseks. Teade eristab tühje välju, sobimatut kasutajanime või parooli ja üldist teenuseühenduse viga.

Sisselogimisakna sulgemisrist katkestab avamise. Visuaali tööriistariba nuppu saab uueks katseks uuesti vajutada.

## Põhiakna päise nupud

### Abi

Nupp **Abi** avab lingi arvuti vaikimisi veebibrauseris. Avatav aadress sõltub aktiivsest moodulist.

| Aktiivne vaade | Avatav abi |
|---|---|
| Avaleht | Kavitro QGIS-i plugina eestikeelne juhendikogu |
| Seadistused | Sama juhendikogu |
| Kinnistud | Kinnistute QGIS-i juhend |
| Projektid | Projektide QGIS-i juhend |
| Lepingud | Lepingute QGIS-i juhend |
| Muu moodul | Kavitro abi avaleht |

Kooskõlastustel, servituutidel, töödel ja teostusjoonistel pole praeguses URL-kaardis eraldi abilehte, mistõttu avaneb üldine abi avaleht. Kui operatsioonisüsteem veebiaadressi ei ava, logitakse viga, kuid kasutajale eraldi veadialoogi ei kuvata.

### Tume/Hele režiim

Teemaikoon vahetab heleda ja tumeda kujunduse vahel. Klõps:

1. rakendab uue kujunduse põhiaknale;
2. uuendab päise teema- ja väljalogimisikoonid;
3. kujundab uuesti juba loodud moodulivaated;
4. salvestab valiku QGIS-i seadetesse.

Valik säilib Visuaali järgmisel avamisel. Nupp ei muuda QGIS-i enda üldteemat ega Kavitro andmeid.

### Logi välja

Väljalogimisnupp ei küsi kinnitust. Klõps:

1. sulgeb QGIS-i kaardi **Otsingupaani** ja **Sisestuspaani**;
2. eemaldab aktiivse juurdepääsutõendi ja kasutajasessiooni QGIS-i seadetest;
3. märgib sessiooni uut sisselogimist vajavaks;
4. sulgeb ja eemaldab Visuaali põhiakna.

Järgmisel Visuaali avamisel tuleb uuesti sisse logida. Väljalogimine ei kustuta QGIS-i autentimishaldurisse varem salvestatud autentimiskirjet.

**Oluline:** väljalogimine sunnib akna sulgema ega käivita seadistuste salvestamata muudatuste tavapärast kinnitusdialoogi. Kinnita või tühista seadistuste muudatused enne väljalogimist.

## Külgriba navigeerimisnupud

Külgribal on **Avaleht**, seitse sisumoodulit ja all eraldi **Seadistused**. Nupud luuakse plugina mooduliregistri järgi.

Praeguses koodis lisatakse külgribale kõik registreeritud sisumoodulid. Seadistuste vaade kasutab kasutaja õigusi seadistuskaartide ja avamooduli valikute piiramiseks, kuid külgriba nuppe endid õiguste järgi ei peideta.

### Moodulinupu klõpsamise järjekord

1. Kontrollitakse aktiivset sessiooni. Aegunud sessiooni korral avatakse sisselogimine ja navigeerimist proovitakse pärast edukat autentimist uuesti.
2. **Avalehe** ja **Seadistuste** puhul jätkatakse kohe; sisumooduli puhul kontrollitakse kohustuslikku seadistust.
3. Puuduva põhikihi, arhiivikihi, vajalike filtrieelistuste või moodulipõhise kohustusliku seadistusväärtuse korral kuvatakse hoiatus ja kasutaja suunatakse vastava mooduli seadistuskaardile.
4. Kui lahkutakse salvestamata muudatustega seadistustest, küsitakse muudatuste kinnitamist või tühistamist. Navigeerimise katkestamisel jääb **Seadistused** avatuks.
5. Eelmine moodul deaktiveeritakse ja uus moodul luuakse vajaduse korral esimest korda.
6. Uus vaade kuvatakse sisuosas, päise pealkiri muutub ja külgriba aktiivne nupp tõstetakse esile.

Aktiivse mooduli nupp muudetakse passiivseks, mistõttu sama nupu korduv klõps ei laadi moodulit uuesti. Mooduli vahetamise vea korral proovitakse taastada eelmine moodul ja vaade.

Navigeerimine ise ei muuda Kavitro kirjeid. Mooduli aktiveerimine võib siiski käivitada selle mooduli andmelaadimise või sünkroonimise; näiteks tööde mooduli avamine võib sünkroonida Kavitro tööandmeid seadistatud QGIS-i tööde kihile.

### Ahenda/laienda külgriba

Külgriba serval olev noolenupuke vahetab kahte vaadet:

- laiendatud vaates on ikoonid ja tekstid ning nupul märk `«`;
- kompaktses vaates jäävad nähtavaks ikoonid, tekstid peidetakse ja nupul on märk `»`.

Laiuse muutus animeeritakse. Kompaktne olek säilib sama põhiakna kasutamise ajal, kuid seda ei salvestata järgmise uue sessiooni jaoks. Nupp ei vaheta aktiivset moodulit.

## Üldotsing

Sama otsinguloogikat kasutatakse:

- Visuaali põhiakna päise otsinguväljal;
- QGIS-i kaardi **Otsingupaanil**, kui see on kasutaja seadetes sisse lülitatud.

### Otsingu käivitamine

- Alla kolme märgi korral otsingut ei saadeta ja avatud tulemused peidetakse.
- Vähemalt kolme märgi sisestamisel käivitub otsing umbes 0,5 sekundit pärast viimast muudatust.
- Klahv `Enter` käivitab otsingu kohe.
- QGIS-i **Otsingupaani** parempoolne ikoon käivitab sama päringu kohe.
- Iga uus otsing muudab varasema poolelioleva vastuse aegunuks, et vana tulemus ei kirjutaks uuemat üle.

Päise otsingul eraldi nuppu ei ole. QGIS-i kaardi otsingunupp kasutab praeguses teostuses abiikooni ja sellel pole eraldi kohtspikrit, kuigi nupu toiming on otsingu käivitamine. Mõlema otsinguvälja eestikeelne kohtspikker ütleb praegu ekslikult „Funktsioon veel ei tööta”, kuid otsinguloogika on koodis ühendatud ja kasutatav.

Otsing küsib teenuselt iga andmerühma kohta kuni viis vastet. Tulemused rühmitatakse andmetüübi järgi ja rühma pealkirjal näidatakse teenuse tagastatud koguarvu.

### Otsingutulemuste nupulaadsed read

| Nupp või rida | Tulemus |
|---|---|
| **× Sulge otsingutulemused** | Peidab tulemuste hüpiku, kuid jätab otsinguteksti väljale. Uus tekstimuudatus võib hüpiku uuesti avada. |
| **Andmerühma pealkiri** | Proovib rühma tulemusi laiendada või ahendada ning käivitab otsingu uuesti. |
| **Otsingutulemus** | Peidab hüpiku ja proovib avada kirje vastavas Visuaali moodulis. |
| **-- Show N more --** | Proovib näidata rühma ülejäänud tulemusi ja käivitab otsingu uuesti. Tekst pole praegu eesti keelde tõlgitud. |

Tulemuste hüpik peidetakse ka sellest väljapoole klõpsamisel või QGIS-i fookuse kaotamisel. Sulgemine ei tühjenda otsinguvälja ega katkesta juba avatud kirjet. Kui otsingupäring on sulgemise hetkel veel pooleli, võib selle hilisem vastus hüpiku uuesti avada.

### Millised tulemused avanevad

| Otsingu andmerühm | Kuvatakse tulemustes | Avaneb Visuaalis |
|---|:---:|:---:|
| Kinnistud | Jah | Jah |
| Projektid | Jah | Jah |
| Lepingud | Jah | Jah |
| Kooskõlastused | Jah | Jah |
| Ülesanded | Jah | Ei |
| Esitamised | Jah | Ei |
| Servituudid | Jah | Ei |
| Spetsifikatsioonid | Jah | Ei |
| Määrused | Jah | Ei |

Toetatud tulemus vahetab mooduli ja avab selle ühe kirje režiimis. Täielikku loendisse naasmist kirjeldab [filtrite nuppude detailaudit](02_01_filtrite_nuppude_detailaudit.md).

Mittetoetatud tulemuse klõps kuvab praeguses teostuses ingliskeelse teate, et moodulit ei saa veel otsingust avada. Moodulivahetuse seadistus- ja sessioonikontrollid rakenduvad ka otsingutulemuse avamisel.

### Praeguse teostuse „Näita veel“ piirang

Otsingupäring küsib andmerühma kohta maksimaalselt viis vastet, kuid **Show N more** rida lisatakse ainult siis, kui vastuste loendis on üle viie kirje. Lisaks käivitab rea või rühmapealkirja klõps sama viie vastega otsingu uuesti ning uus vastus tühjendab laiendatud oleku. Seetõttu ei saa **Näita veel** praeguses versioonis tavaliselt lisatulemusi nähtavale tuua. Täpsema vaste leidmiseks tuleb otsinguteksti täpsustada.

## QGIS-i kaardi Otsingupaan

**Otsingupaan** kuvatakse QGIS-i kaardi paremas ülanurgas pärast Visuaali avamist ainult siis, kui:

- kasutajal on aktiivne Visuaali sessioon;
- valik **Seadistused → Kasutaja → Tööriistad → Otsingupaan** on sisse lülitatud.

Vaikimisi on paan lubatud. Seadistuse kinnitamisel ilmub või kaob see kohe; väljalogimisel paan suletakse. Paan liigub QGIS-i kaardi suuruse muutmisel uuesti paremasse ülanurka.

Otsinguväli ja tulemused töötavad samade reeglitega nagu põhiakna päise otsing. Tulemuse valimine avab või toob ette Visuaali põhiakna ning käivitab sama mooduliavamise voo.

## QGIS-i kaardi Sisestuspaan

Kolme ikooniga **Sisestuspaan** kuvatakse pärast Visuaali avamist otsingupaani all, kui kasutaja seadetes on **Sisestuspaan** sisse lülitatud ja Visuaali sessioon kehtib. Vaikimisi on paan lubatud. Kõik kolm nuppu on ikoonnupud ning nende nimed kuvatakse kohtspikrina.

### Lisa uus töö

Nupp avab mooduli **Tööd** ja käivitab uue töö asukoha valimise.

Eeltingimused:

- tööde mooduli kohustuslik seadistus on lõpetatud;
- seadistatud tööde põhikiht on kehtiv punktikiht;
- kihil on väli `ext_job_id` ja vajalik skeem;
- Kavitrost on saadaval töö loomise valikud.

Kaardivaliku käivitamisel minimeeritakse Visuaali aken ja kursor muutub ristiks. Vasakklõps määrab punkti ning avab töö loomise vormi. Paremklõps või `Esc` katkestab valiku ja taastab akna.

Vormi kinnitamine võib luua Kavitro töö, lisada QGIS-i kihile punkti ja seostada leitud kinnistu. Kuna Kavitro töö luuakse enne kihiobjekti ja kinnistuseose salvestamist, võib toiming õnnestuda osaliselt. Täielik töövoog ja kontrollsammud on juhendis [Tööde mooduli kaarditoimingud](../11_toode_mooduli_kaarditoimingud.md).

### Mis see on

Nupp käivitab aktiivse mooduli põhikihil objekti tuvastamise. Toetatud on:

| Aktiivne moodul | Kasutatavad ID-väljad |
|---|---|
| Kinnistud | `id`, `ext_property_id`, `property_id`, `ext_id`, `external_id` või `tunnus` |
| Projektid | `ext_project_id`, `ext_id` või `external_id` |
| Tööd | `ext_works_id`, `ext_job_id`, `ext_id` või `external_id` |
| Teostusjoonised | `ext_asbuilt_id`, `ext_job_id`, `ext_id` või `external_id` |
| Servituudid | `ext_easement_id`, `ext_id` või `external_id` |

Käivitamisel tehakse mooduli põhikiht nähtavaks ja aktiivseks ning selle senine objektivalik tühjendatakse. Visuaali aken minimeeritakse ja kaardikursor muutub tuvastamiskursoriks.

- Vasakklõps otsib klikitud kohast objekti.
- Punktikihil kasutatakse väikest klõpsutolerantsi; joon- või polügoonkihil peab geomeetria klikitud punkti sisaldama või sellega lõikuma.
- Edu korral valitakse objekt kihil, avatakse vastav Visuaali moodul ja kirje ning taastatakse aken.
- Tühjas kohas või puuduva ID-välja korral kuvatakse hoiatus ja tööriist jääb uueks katseks aktiivseks.
- Paremklõps või `Esc` katkestab toimingu, taastab tavalise panoraamimise ja Visuaali akna.

Lepingud, kooskõlastused, avaleht ja seadistused ei toeta seda toimingut. Kinnistukihi välja `tunnus` väärtus peab olema teenuses avatav kirje ID, mitte tingimata ainult katastritunnus.

### Kontrolli sidumata GIS töid

Nupp avab mooduli **Tööd** ja kontrollib seadistatud tööde põhikihi objekte. Sidumata GIS-tööks loetakse geomeetriaga punkt, mille väljad `ext_job_id` ja `ext_system` on mõlemad tühjad.

Kontrolli ajal kuvatakse edenemismärguanne ja skannimist ei saa eraldi katkestada. Kontroll ise loeb kihti ega muuda objekte.

- Kui sobivaid punkte pole, kuvatakse teade ja dialoogi ei avata.
- Leitud punktid kuvatakse dialoogis **Sidumata GIS tööd**; esimene rida on vaikimisi valitud.
- Rea topeltklõps või **Ava valitud** avab eeltäidetud töö loomise vormi.
- **Tühista** sulgeb nimekirja andmeid muutmata.

Loomisvormi kinnitamine loob esmalt Kavitro töö ning kirjutab seejärel selle ID ja värsked andmed samale olemasolevale QGIS-i kihipunktile. Kihi uuendamise või kinnistuseose vea korral võib Kavitro töö olla juba loodud. Enne toimingu kordamist kontrolli Kavitro tööde loendit.

## Mõju ja katkestamise koondtabel

| Nupp | Püsiv seadistus või andmemuudatus | Katkestamine või tagasitee |
|---|---|---|
| **Kavitro / Visuaal** | Võib avada uue sessiooni ja põhiakna; kirjeid ei muuda | Sulge sisselogimisaken või minimeeri põhiaken |
| **Näita parooli** | Ei | Klõpsa uuesti |
| **Logi sisse** | Salvestab sessiooni; proovib salvestada autentimiskirje | Sulge sisselogimisaken enne edukat autentimist |
| **Abi** | Ei | Sulge brauserileht |
| **Tume/Hele režiim** | Salvestab teemaeelistuse | Klõpsa uuesti |
| **Logi välja** | Kustutab aktiivse kohaliku sessiooni | Pärast klõpsu tagasivõttu pole; logi uuesti sisse |
| Moodulinupp | Ise kirjeid ei muuda; mooduli aktiveerimine võib andmeid laadida või sünkroonida | Katkesta seadistuste hoiatus või vali eelmine moodul |
| **Ahenda/laienda külgriba** | Ei salvestata uue sessiooni jaoks | Klõpsa uuesti |
| Otsingu käivitamine | Ei | Muuda tekst alla kolme märgi; tulemuste sulgemine peidab hüpiku, kuid ei katkesta pooleliolevat päringut |
| Otsingutulemus | Avab ühe kirje vaate; kirjet ei muuda | Taasta mooduli tavaloend filtritega |
| **Lisa uus töö** | Võib luua Kavitro töö, kihiobjekti ja kinnistuseose | Enne vormi kinnitamist paremklõps, `Esc` või vormi tühistamine |
| **Mis see on** | Muudab aktiivset kihti ja objektivalikut; kirjet ei muuda | Paremklõps või `Esc` |
| **Kontrolli sidumata GIS töid** | Kontroll ise ei muuda; loomise kinnitamine muudab Kavitrot ja QGIS-i kihti | Nimekirjas **Tühista**; loomise vormil tühista |

## Kui nupp ei tööta ootuspäraselt

- Kui Visuaal ei avane, salvesta QGIS-i projekt esmalt failina.
- Kui nupuvajutus avab **Seadistused**, täida hoiatatud mooduli kohustuslikud seadistused ja kinnita need.
- Kui külgribal on moodul, millele kasutajal ei peaks olema juurdepääsu, arvesta, et külgriba nähtavust õiguste järgi praegu ei filtreerita; teenus võib andmepäringu siiski keelata.
- Kui otsing ei käivitu, sisesta vähemalt kolm märki ja kontrolli sessiooni ning internetiühendust.
- Kui **Näita veel** ei lisa tulemusi, täpsusta otsinguteksti; praegune päring tagastab kuni viis vastet rühma kohta.
- Kui **Mis see on** ei käivitu, kontrolli aktiivset moodulit, põhikihti ja sobivat ID-välja.
- Kui kaardipaanid puuduvad, kontrolli kasutaja seadete valikuid **Otsingupaan** ja **Sisestuspaan**, kinnita muudatused ning veendu, et sessioon kehtib.
- Kui töö loomine ebaõnnestub pärast kinnitamist, kontrolli enne kordamist, kas Kavitro töö või QGIS-i kihiobjekt loodi osaliselt.

## Seotud juhendid

- [Üldnupud ja navigeerimine](01_uldnupud_ja_navigeerimine.md)
- [Kavitro põhiaken, otsing ja ühised töövõtted](../17_kavitro_pohiaken_otsing_ja_uhised_toovotted.md)
- [Kasutaja eelistuste seadistamine](../02_kasutaja_eelistuste_seadistamine.md)
- [Tööde mooduli kaarditoimingud](../11_toode_mooduli_kaarditoimingud.md)
- [Filtrite nuppude detailaudit](02_01_filtrite_nuppude_detailaudit.md)
