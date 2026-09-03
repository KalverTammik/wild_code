# Kavitro põhiaken, otsing ja ühised töövõtted

See juhend annab tervikpildi Visuaali ehk Kavitro QGIS-i plugina põhiaknast, avalehest, üldotsingust, kaardipaanidest ja moodulites korduvatest töövõtetest. Moodulipõhiste toimingute täpsed sammud on eraldi juhendites, mille sisukord on selle juhendi lõpus.

## Põhiakna osad

| Akna osa | Otstarve |
|---|---|
| Päis | Abi avamine, üldotsing, teema vahetamine ja väljalogimine |
| Külgriba | Avalehe, kasutajale lubatud moodulite ja seadistuste avamine |
| Sisuosa | Aktiivse mooduli loend, detailvaade või seadistused |
| Jalus | Kodulehe ja tingimuste lingid ning QGIS-i ja plugina versioon |
| QGIS-i kaardipaanid | Üldotsing ja sagedased kaarditoimingud ilma põhiakent ette toomata |

Külgribal kuvatakse **Avaleht**, **Kinnistud**, **Projektid**, **Lepingud**, **Kooskõlastused**, **Servituudid**, **Tööd** ja **Teostusjoonised** vastavalt kasutaja õigustele. **Seadistused** on eraldi külgriba valik.

Kui mõnda moodulit ei ole külgribal, kontrolli kasutaja mooduliõigusi. Õiguste ja vaikimisi avatava mooduli kohta vaata [Kasutaja eelistuste seadistamine](02_kasutaja_eelistuste_seadistamine.md).

## Avaleht

Avalehel kuvatakse teenusest laaditavad KPI-kaardid järgmiste moodulite kohta:

- kinnistud;
- projektid;
- lepingud;
- kooskõlastused;
- servituudid;
- tööd;
- teostusjoonised.

Projektide, lepingute ja kooskõlastuste kaartidel on lisaks koguarvule tähtaja jaotus: hilinenud, peagi tähtajani jõudvad ja muud kirjed. Ülejäänud kaartidel kuvatakse koguarv ilma tähtaja jaotuseta.

Avalehe avamisel värskendatakse kaarte. KPI-kaart on ülevaade, mitte mooduli avamise nupp; töö jätkamiseks vali moodul külgribalt.

## Moodulite vahel liikumine

Mooduli avamiseks vajuta külgribal selle nime. Mooduli vahetamisel lõpetatakse eelmise vaate pooleliolevad laadimised ning aktiivseks muutub uue mooduli sisu.

Mõni toiming suunab automaatselt teise moodulisse:

- üldotsingu toetatud tulemus avab sobiva mooduli ja kirje;
- **Mis see on** avab kaardilt leitud kirje moodulis;
- puuduva kohustusliku seadistuse korral võib toiming avada seadistused ja liikuda õige mooduli kaardini.

## Üldotsingu kasutamine

Sama üldotsing on saadaval kahes kohas:

- Visuaali põhiakna päises;
- QGIS-i kaardi paremas ülanurgas, kui **Otsingupaan** on kasutaja seadetes sisse lülitatud.

Mõlemad otsinguväljad kasutavad sama teenuseotsingut ja sama tulemuse avamise loogikat.

1. Sisesta otsinguväljale vähemalt kolm märki.
2. Oota hetk, kuni otsing käivitub. Sisestamise järel kasutatakse umbes poole sekundi pikkust viivitust.
3. Vaata tulemusi andmerühmade kaupa.
4. Vali sobiv tulemus.

Iga andmerühma kohta küsitakse kuni viis tulemust. Täpsema tulemuse saamiseks lisa otsingusse nime, numbri, katastritunnuse või muu eristava teksti.

## Otsitavad andmerühmad ja avamise tugi

Üldotsing otsib rohkem andmerühmi, kui Visuaalis on avatavaid mooduleid.

| Otsingu andmerühm | Tulemus kuvatakse | Tulemus avaneb Visuaalis |
|---|---:|---:|
| Kinnistud | Jah | Jah |
| Projektid | Jah | Jah |
| Lepingud | Jah | Jah |
| Kooskõlastused | Jah | Jah |
| Ülesanded | Jah | Ei |
| Esitamised | Jah | Ei |
| Servituudid | Jah | Ei |
| Spetsifikatsioonid | Jah | Ei |
| Määrused | Jah | Ei |

Kui vajutad tulemusele, mille avamist Visuaal veel ei toeta, kuvatakse teade, et moodulit ei saa otsingust avada. Tulemus ei ole selle tõttu vigane; avamisvoog ei ole lihtsalt selles versioonis ühendatud.

Kinnistu, projekti, lepingu või kooskõlastuse valimisel avatakse vastav moodul ja laaditakse üks valitud kirje. Loendimoodulis täieliku loendi taastamiseks vajuta filtrite värskendamise või tühjendamise nuppu või muuda mõnda filtrit.

## QGIS-i kaardipaanid

Kasutaja seadetes saab eraldi sisse või välja lülitada:

- **Otsingupaani**, mis lisab kaardile üldotsingu;
- **Sisestuspaani**, mis lisab kaardile kolm sagedast toimingut.

Sisestuspaani toimingud on:

- **Lisa uus töö** – avab töö loomise kaardipunktist;
- **Mis see on** – avab aktiivse mooduli kihi objekti;
- **Kontrolli sidumata GIS töid** – käivitab tööde kihi sidumata objektide kontrolli.

Paanide seadistamise kohta vaata [Kasutaja eelistuste seadistamine](02_kasutaja_eelistuste_seadistamine.md). Tööde loomist ja sidumata GIS-tööde kontrolli kirjeldab [Tööde mooduli kaarditoimingud](11_toode_mooduli_kaarditoimingud.md).

## Kaarditoiming „Mis see on“

**Mis see on** töötab aktiivse mooduli põhikihil ja on toetatud järgmistes moodulites:

| Aktiivne moodul | Vajalik ID-väli kihil |
|---|---|
| Kinnistud | `id`, `ext_property_id`, `property_id`, `ext_id`, `external_id` või `tunnus` |
| Projektid | `ext_project_id`, `ext_id` või `external_id` |
| Tööd | `ext_works_id`, `ext_job_id`, `ext_id` või `external_id` |
| Teostusjoonised | `ext_asbuilt_id`, `ext_job_id`, `ext_id` või `external_id` |
| Servituudid | `ext_easement_id`, `ext_id` või `external_id` |

1. Ava külgribalt toetatud moodul.
2. Vajuta kaardil **Mis see on**.
3. Klõpsa aktiivse mooduli põhikihil objekti.
4. Visuaal loeb objekti ID, avab mooduli ja laadib vastava Kavitro kirje.

Paremklõps või `Esc` katkestab valimise. Lepingute ja kooskõlastuste moodulis toiming praegu ei tööta, isegi kui neile on põhikiht seadistatud.

Kinnistukihi `tunnus` välja väärtus peab selles avamisvoos olema teenuse jaoks sobiv kirje ID. Kui väljal on ainult katastritunnus ja teenus ootab sisemist ID-d, ei pruugi kirje avaneda.

## Kirjekaardi ühine ülesehitus

Projektide, lepingute, kooskõlastuste, servituutide, tööde ja teostusjooniste loendid kasutavad sarnaseid kirjekaarti. Kaardil võivad olla:

- värviline staatuseriba;
- nimi, number, liik ja kuupäevad;
- vastutajad, kontaktid või tunnused;
- seotud kinnistute arv;
- detailse ülevaate avamise käepide;
- kausta-, veebi-, kaardi- ja lisatoimingute nupud.

Kõiki välju ei kuvata igal moodulil. Puuduv väärtus võib tähendada, et see pole Kavitros täidetud või mooduli päring seda ei tagasta.

Tööde ja teostusjooniste staatuseriba vajutamisel saab staatust muuta, kui kirjel on ID ja teenus tagastab kasutatavad staatused. Teistes moodulites on staatuseriba ainult staatuse näitamiseks.

## Ühised kirjekaardi toimingud

| Toiming | Käitumine |
|---|---|
| **Ava kaust** | Avab `filesPath` asukoha; tööde ja teostusjooniste kaartidel seda nuppu ei ole |
| **Ava kirje brauseris** | Avab sama kirje Kavitro veebirakenduses |
| **Seosta / Näita kaardil** | Seoseta kirjel käivitab seostamisikoon kinnistute seostamise; seosega kirjel kuvab kaardiikoon seotud kinnistud ja toetatud moodulites fokuseerib ka mooduli põhikihi objekti |
| **Rohkem toiminguid** | Avab moodulipõhised kaardi-, faili- ja sidumistoimingud |

Nupp võib olla passiivne, kui toiminguks vajalik ID või kaustatee puudub. Puuduv kinnistuseos ei muuda kaardirea toimingut passiivseks, vaid vahetab selle kinnistute seostamisikooniks.

### „Seosta / Näita kaardil“ moodulite lõikes

| Moodul | Seotud kinnistud | Mooduli põhikihi objekti fookus |
|---|---:|---:|
| Projektid | Jah | Jah |
| Lepingud | Jah | Ei |
| Kooskõlastused | Jah | Ei |
| Servituudid | Jah | Jah |
| Tööd | Jah | Jah |
| Teostusjoonised | Jah | Jah |

Põhikihi objekti leidmiseks peab kihil olema sobiv teenuse ID-väli. Seotud kinnistute leidmiseks peavad seosed olema Kavitros olemas ning kinnistute põhikiht õigesti seadistatud.

## „Rohkem toiminguid“ moodulite lõikes

Lisatoimingute menüü sisu sõltub moodulist:

- **Projektid** – projektikausta genereerimine, projektiala eelvaade, uue ala joonistamine ja kinnistute sidumine;
- **Lepingud** – kinnistute sidumine;
- **Kooskõlastused** – kinnistute sidumine;
- **Servituudid** – failihalduse menüütoiming, uue ala joonistamine, olemasoleva objekti sidumine, geomeetria muutmine, ala eelvaade ja kinnistute sidumine; praeguses versioonis ei avane failihalduse dialoog puuduva käsitleja tõttu;
- **Tööd** – olemasolevale tööle punkti lisamine, asukoha muutmine ja kinnistute sidumine;
- **Teostusjoonised** – märkmete muutmine, uue ala joonistamine ja kinnistute sidumine.

Kõigi moodulite ühises kinnistute sidumise töövoos valitakse kinnistud kaardilt ning vaadatakse eraldi üle olemasolevad ja uued valikud. **Kinnita** saadab teenusesse ainult uued valitud kinnistud; olemasolevaid seoseid see ei asenda ega eemalda.

## Detailvaated ja failide eelvaade

Detailse ülevaate sisu on mooduliti erinev:

- projekt kuvab seotud moodulite edenemise tahvli;
- leping kuvab kirjelduse ja failide kokkuvõtte;
- kooskõlastus kuvab kirjelduse, tingimused ja failide kokkuvõtte;
- servituut kuvab seotud kinnistute ülevaate ja failide kokkuvõtte;
- töö ning teostusjoonis kuvavad kirjelduse ja failide kokkuvõtte.

Failide kokkuvõttes kuvatakse kuni viis esimest faili. Faili vajutamisel proovib Visuaal avada sisemise eelvaate. Eelvaatedialoogi **Ava väliselt** on aktiivne ainult lubatud ja failinimega kooskõlas oleva laiendi korral ning küsib enne allalaadimist vaikimisi eitava turvakinnituse. Käivitatavaid ja aktiivsisu sisaldavaid failitüüpe välisele rakendusele ei anta. Kui PDF-e toetav Qt WebEngine puudub, eelvaatedialoogi ja selle välise avamise nuppu ei looda; kasuta sel juhul Kavitro veebivaadet. Täpne failitüüpide loend ja abikeskuse kontrolljuhis on failis [Failide ja ühisdialoogide nupud](Nupud/09_failide_ja_uhisdialoogide_nupud.md).

Kirjeldustes olevad lingid ei avane automaatselt. Veebilingi puhul näidatakse enne brauseri avamist täielikku aadressi; `http`-lingi kinnitus hoiatab lisaks krüpteerimata ühenduse eest. Kohalik toetatud fail avatakse esmalt Visuaali eelvaates, kust saab lubatud failitüübi eraldi kinnitusega anda arvuti vaikerakendusele. Kohaliku kausta avamine küsib samuti kinnitust. Võrgufaili või -kausta korral näidatakse eraldi, millise serveriga ühendus luuakse, ning faili olemasolu kontrollitakse alles pärast vaikimisi eitavat kinnitust. Tundmatud protokollid ja lubamata failitüübid blokeeritakse.

Täieliku failide üleslaadimise ja kustutamise dialoogi klass on olemas ainult servituutide töövoo jaoks, kuid praeguses versioonis ei ava menüütoiming seda dialoogi. Kasuta failihalduseks Kavitro veebivaadet. Moodulite detailvaate failiosa on lugemiseks ja eelvaateks.

## Teema, abi ja versioon

- Päise teemanupuga saab vahetada heledat ja tumedat kujundust.
- **Abi** avab aktiivse mooduli Kavitro abilehe. Avalehel ja seadistustes avaneb juhendite kogu; eraldi abilingita moodulis avaneb Kavitro abi avaleht.
- Jaluse paremas servas kuvatakse QGIS-i ja plugina versioon. Arenduskeskkonna korral lisatakse plugina versioonile märge `DEV`.

Kui on vaja kontrollida, milline plugina versioon tegelikult QGIS-is töötab, vaata jaluse väärtust, mitte ainult repositooriumi haru või Git-ajalugu.

## Akna sulgemine ja väljalogimine

Tavaline akna sulgemine minimeerib Visuaali ning säilitab aktiivse sessiooni. Plugina saab uuesti ette tuua QGIS-i tööriistaribalt või menüüst.

Päise väljalogimisnupp:

- eemaldab aktiivse Kavitro sessiooni;
- sulgeb kaardi otsingu- ja sisestuspaani;
- sulgeb Visuaali akna;
- nõuab järgmisel avamisel uut sisselogimist.

Kasuta väljalogimist jagatud arvutis või siis, kui soovid konto sessiooni lõpetada. Kui tahad ainult tööakna eest ära saada, sulge või minimeeri aken.

## Soovituslik igapäevane tööjärjekord

1. Ava õige QGIS-i projekt.
2. Kontrolli jalusest plugina versiooni.
3. Ava Visuaal ja veendu, et sessioon kehtib.
4. Vali külgribalt tööks sobiv moodul.
5. Leia kirje mooduli filtrite, üldotsingu või toetatud moodulis **Mis see on** toiminguga.
6. Vaata kirje detailid ja seotud kinnistud üle.
7. Käivita kirjekaardi või **Rohkem toiminguid** menüü sobiv tegevus.
8. Kontrolli pärast salvestamist nii Kavitro kirjet kui ka QGIS-i kihti.
9. Värskenda loend, kui taustal tehtud muudatus kohe ei kajastu.

## Levinumad olukorrad

### Otsing ei käivitu

Sisesta vähemalt kolm märki. Kontrolli internetiühendust ja Kavitro sessiooni. Kaardil oleva otsinguvälja puudumisel lülita kasutaja seadetes sisse **Otsingupaan**.

### Otsing leidis kirje, kuid seda ei saa avada

Kontrolli tabelist, kas selle andmerühma avamine on toetatud. Ülesanded, esitamised, servituudid, spetsifikatsioonid ja määrused kuvatakse otsingutulemustes, kuid neid ei saa praegu üldotsingust Visuaali moodulisse avada.

### „Mis see on“ ei käivitu

Kontrolli, et aktiivne moodul oleks kinnistud, projektid, tööd, teostusjoonised või servituudid. Seejärel kontrolli mooduli põhikihi seadistust, kihi laadimist ja sobivat ID-välja.

### „Näita kaardil“ annab ainult osalise tulemuse

Toiming võib leida seotud kinnistud, kuid mitte mooduli objekti, või vastupidi. Kontrolli eraldi kinnistuseoseid, kinnistute põhikihti, mooduli põhikihti ja ID-välja väärtust. Lepingute ja kooskõlastuste puhul ongi toetatud ainult seotud kinnistute kuvamine.

### Kirjekaardi andmed ei värskene

Sulge detailvaade, värskenda filtrid või ava moodul uuesti. Kui muudatus tehti Kavitro veebis, veendu enne, et see oleks seal salvestatud.

### Kaust või fail ei avane

Kontrolli kirje kaustateed, võrguühendust ja kasutaja juurdepääsu. Faili sisemise eelvaate asemel proovi välise rakendusega avamist.

### Põhiakna sulgemisel sessioon jäi alles

See on kavandatud käitumine: tavaline sulgemine minimeerib akna. Sessiooni lõpetamiseks kasuta päise väljalogimisnuppu.

## Juhendite lõplik sisukord

### Alustamine ja üldseadistused

1. [Seadistuste mooduli kasutamine](01_seadistuste_mooduli_kasutamine.md) – seadistusvaate üldloogika, salvestamine ja lähtestamine.
2. [Kasutaja eelistuste seadistamine](02_kasutaja_eelistuste_seadistamine.md) – konto, mooduliõigused, avamoodul ja kaardipaanid.
3. [QGIS-i projekti baaskihtide seadistamine](03_qgis_projekti_baaskihtide_seadistamine.md) – projektifail, kihigrupid ja baaskihid.
4. [Mooduli kihtide ja filtrieelistuste seadistamine](04_mooduli_kihtide_ja_filtrieelistuste_seadistamine.md) – moodulikaartide ühised valikud.

### Kihid ja moodulipõhised seadistused

5. [Kinnistute kihi seadistamine ja haldamine](05_kinnistute_kihi_seadistamine_ja_haldamine.md) – kinnistukihi loomine, uuendamine ja arhiveerimine.
6. [Geospatiali kihtide vastendamine](06_geospatiali_kihtide_vastendamine.md) – teenuse- ja QGIS-i väljade vastendus.
7. [Projektide mooduli seadistamine](07_projektide_mooduli_seadistamine.md) – projektikiht ja projektikaustad.
8. [Servituutide mooduli seadistamine](08_servituutide_mooduli_seadistamine.md) – kiht, staatusevastendus ja filtrieelistused.
9. [Tööde ja teostusjooniste seadistamine](09_toode_ja_teostusjooniste_seadistamine.md) – töökihtide seadistus ja ajutine töökiht.
10. [Lepingute ja kooskõlastuste seadistamine](10_lepingute_ja_kooskolastuste_seadistamine.md) – kihid ja filtrieelistused.

### Igapäevased moodulitöövood

11. [Tööde mooduli kaarditoimingud](11_toode_mooduli_kaarditoimingud.md) – töö loomine, sidumine ja sünkroonimine.
12. [Teostusjooniste mooduli kasutamine](12_teostusjooniste_mooduli_kasutamine.md) – joonistamine, märkmed ja kaarditoimingud.
13. [Projektide mooduli kasutamine](13_projektide_mooduli_kasutamine.md) – loend, projektitahvel, alad ja kaustad.
14. [Servituutide mooduli kaarditoimingud](14_servituutide_mooduli_kaarditoimingud.md) – geomeetria, eelvaade, failid ja kinnistuseosed.
15. [Kinnistute mooduli kasutamine](15_kinnistute_mooduli_kasutamine.md) – kinnistu avamine ja seotud andmete ülevaade.
16. [Lepingute ja kooskõlastuste mooduli kasutamine](16_lepingute_ja_kooskolastuste_mooduli_kasutamine.md) – loendid, tähtajad, detailid ja kinnistuseosed.
17. **Kavitro põhiaken, otsing ja ühised töövõtted** – käesolev juhend ning kogu sarja sisukord.

## Kogu lahenduse kontrollnimekiri

- [ ] QGIS-is on avatud õige projekt ja vajalikud kihid on laaditud.
- [ ] Kavitro sessioon ja internetiühendus töötavad.
- [ ] Kasutajale vajalikud moodulid on külgribal nähtavad.
- [ ] Jaluses kuvatav plugina versioon vastab oodatule.
- [ ] Üldotsingu ja **Mis see on** erinevus on kasutajale teada.
- [ ] Moodulite filtrid ning tähtajavaated on enne veaotsingut kontrollitud.
- [ ] Kaarditoimingute jaoks vajalikud põhikihid ja ID-väljad on seadistatud.
- [ ] Kinnistuseoste kinnitamisel vaadatakse üle kogu lõplik loend.
- [ ] Pärast kirjutavat toimingut kontrollitakse nii Kavitro kirjet kui ka QGIS-i kihti.
- [ ] Töö lõpus kasutatakse vajaduse järgi minimeerimist või väljalogimist.
