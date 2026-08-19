# Kinnistute mooduli kasutamine

Kinnistute moodulis saab valida kinnistu QGIS-i kaardilt või avada selle Kavitro üldotsingust, vaadata katastriandmeid ning sirvida kinnistuga seotud projekte, lepinguid, kooskõlastusi, servituute ja muid teenusekirjeid.

Kinnistukihtide seadistamist, importi, lisamist, arhiveerimist ja kustutamist kirjeldab juhend [Kinnistute kihi seadistamine ja haldamine](05_kinnistute_kihi_seadistamine_ja_haldamine.md).

## Eeltingimused

Enne kinnistute mooduli kasutamist veendu, et:

- avatud on õige QGIS-i projekt;
- Kavitro sessioon ja internetiühendus on aktiivsed;
- kinnistute põhikiht on seadistatud ja projekti laaditud;
- põhikiht sisaldab Kavitro kasutatavaid katastriandmete välju;
- katastritunnuse väli `tunnus` on täidetud;
- üldotsingu ja automaatse kaardile suumimise jaoks on kihil korras `search_field`.

Väljade ja otsinguvälja loomise kohta vaata [Kinnistute kihi seadistamine ja haldamine](05_kinnistute_kihi_seadistamine_ja_haldamine.md#otsinguvälja-loomine-või-parandamine).

## Kinnistu valimine kaardilt

1. Ava moodul **Kinnistud**.
2. Vajuta **Vali kaardilt**.
3. Kavitro muudab kinnistute põhikihi valitavaks ja viib fookuse QGIS-i kaardile.
4. Vali soovitud kinnistu.
5. Kavitro toob plugina akna tagasi ette, täidab kinnistu kokkuvõtte ja alustab seotud kirjete laadimist.

Kinnistuvaade kasutab valitud objektidest esimest. Kui märgid korraga mitu kinnistut, kuvatakse ainult valiku esimese objekti andmed ja seosed. Ühe kinnistu kindlaks avamiseks puhasta varasem valik ning vali üks objekt.

Kui kinnistute põhikiht on juba enne mooduli avamist valitud objektiga aktiivne, proovib Kavitro mooduli avamisel selle kinnistu andmed automaatselt kuvada.

## Kinnistu avamine üldotsingust

Kinnistu saab avada nii Kavitro akna päise otsingust kui ka QGIS-i kaardil olevast Otsingupaanist.

1. Sisesta vähemalt kolm tähemärki, näiteks katastritunnuse või aadressi osa.
2. Ava tulemuste rühm **Kinnistud**.
3. Vali soovitud kinnistu.
4. Kavitro avab kinnistute mooduli ja küsib teenusest kinnistu katastritunnuse.
5. Vastav objekt valitakse kinnistute põhikihil ja kaart suumitakse sellele.
6. Kinnistu kokkuvõte ning seotud kirjed laaditakse kinnistuvaatesse.

Kui kinnistu on Kavitro teenuses olemas, kuid seda ei leita seadistatud QGIS-i põhikihilt, saab Kavitro siiski laadida teenuse seosed. Kaardiandmete kokkuvõttes kuvatakse sel juhul, et kinnistut ei leitud kaardikihilt.

Üldotsingu kasutamist ja selle piiranguid kirjeldab juhend [Kavitro põhiaken, otsing ja ühised töövõtted](17_kavitro_pohiaken_otsing_ja_uhised_toovotted.md).

## Kinnistu avamine kaardi toiminguga „Mis see on“

1. Ava Kavitro moodul **Kinnistud**.
2. Käivita QGIS-i kaardi Sisestuspaanilt **Mis see on**.
3. Kliki kinnistute põhikihi polügoonile.
4. Kavitro loeb objekti identiteedivälja ja avab kinnistu moodulis.

Tuvastamine otsib sobivat välja järgmises järjestuses: `id`, `ext_property_id`, `property_id`, `ext_id`, `external_id`, `tunnus`. Leitud väärtus saadetakse praegu avamisvoogu Kavitro kirje ID-na. Kui ainsa sobiva väljana leitakse `tunnus`, kuid selles on tavaline katastritunnus, võib kirje avamine ebaõnnestuda.

Parema hiireklõpsu või klahviga `Esc` saab tuvastamise katkestada.

## Kinnistuandmete kokkuvõte

Valitud kinnistu kohta kuvatakse võimaluse korral:

- katastritunnus;
- kinnistu registriosa number;
- aadress, asustusüksus ja maakond;
- pindala;
- kuni kolm sihtotstarvet koos osakaaludega;
- registreerimise kuupäev;
- viimase muutmise kuupäev.

Andmed loetakse otse valitud QGIS-i põhikihi objektilt. Kavitro ei täida selles vaates puuduvaid kihivälju teenuse andmetega ega salvesta kokkuvõtte muutmiseks uusi väärtusi.

Kui mõni väli puudub või on tühi, võidakse väärtuse asemel kuvada kriips või väli täielikult peita.

## Seotud andmete laadimine

Pärast kinnistu valimist:

1. Kavitro lahendab katastritunnuse järgi teenuse kinnistu ID.
2. Seotud moodulite päringud käivitatakse taustal.
3. Tulemused rühmitatakse mooduli kaupa.
4. Iga mooduli pealkirja juures kuvatakse leitud kirjete arv.
5. Väiksemad rühmad avatakse automaatselt; suurema rühma saab noolenupust avada.

Praegu laadib kinnistuvaade järgmiste seoste andmed:

- lepingud;
- kooskõlastused;
- servituudid;
- projektid;
- spetsifikatsioonid;
- esitused.

Tulemused on teenuses numbri järgi kasvavalt järjestatud ning ühe mooduli päring toob korraga kuni 30 kirjet.

### Praeguse versiooni piirang

Tööde ja Teostusjooniste kirjeid kinnistute mooduli seotud andmete puu praegu ei lae. See ei tähenda tingimata, et kinnistusel vastavaid seoseid pole.

Spetsifikatsioonid ja esitused võivad seotud andmete puus ilmuda, kuigi neil ei ole pluginas eraldi külgribamoodulit. Nende puhul võivad saadaval olla ainult veebikirje, kausta või muu ühise kirjekaardi toimingud.

## Seotud kirje rea sisu

Seotud kirje real kuvatakse andmete olemasolul:

- number;
- nimi või pealkiri;
- liik ja klient;
- kuupäevad;
- staatus;
- kirjekaardi toimingud.

Mooduli sektsiooni esmakordsel avamisel luuakse selle kirjeread. Juba avatud sektsiooni sulgemine ja uuesti avamine ei tee teenusele uut päringut.

Kinnistu seoste päringut hoitakse lühiajaliselt vahemälus. Sama kinnistu kiirel uuesti avamisel võib vaade seetõttu näidata kuni ligikaudu 45 sekundi vanust tulemust.

## Seotud kirje toimingud

Sõltuvalt moodulist ja kirje andmetest võib real olla kuni neli nuppu.

### Ava kaust

Nupp on aktiivne, kui kirjel on `filesPath` väärtus. Kohalik tee avatakse Windows Exploreris ja veebiaadress vaikimisi veebibrauseris.

Tööde ja Teostusjooniste ridadel kaustanuppu ei kuvata.

### Ava kirje brauseris

Avab sama kirje Kavitro veebirakenduses. Nupp vajab mooduli nime ja teenuse kirje ID-d.

### Näita kaardil

Toiming valib kõigepealt kirjega seotud kinnistud. Projektide, Tööde, Teostusjooniste ja Servituutide puhul proovib Kavitro lisaks leida mooduli põhikihilt sama ID-ga kaardiobjekti ning sellele suumida.

Lepingute ja Kooskõlastuste puhul kuvatakse ainult seotud kinnistud, sest nende põhikihi objektile fokuseerimist praegune versioon ei toeta.

### Rohkem toiminguid

Kõigi toetatud moodulite ühine toiming on **Seosta kinnistuid**. Projektidel, Servituutidel, Töödel ja Teostusjoonistel lisanduvad nende moodulite eritoimingud, mida kirjeldavad vastavad kasutusjuhendid.

Kinnistute sidumine muudab teenuse andmeid. Kontrolli ülevaatedialoogis nii senised kui valitud kinnistud enne kinnitamist.

Ühiste kirjekaardi nuppude kohta vaata [Kavitro põhiaken, otsing ja ühised töövõtted](17_kavitro_pohiaken_otsing_ja_uhised_toovotted.md#ühised-kirjekaardi-toimingud).

## Seotud andmete värskendamine

Kinnistuvaates ei ole eraldi värskendusnuppu. Seoste uuesti laadimiseks:

1. vali mõni teine kinnistu ja seejärel algne kinnistu uuesti; või
2. oota lühiajalise vahemälu aegumist ning ava kinnistu uuesti.

Kui muutsid kinnistuseost mõne kirjerea toimingust, võib vastava rea kaardinupp kohe aktiveeruda, kuid kogu seotud andmete puu ei pruugi automaatselt ümber laadida.

## Levinumad olukorrad

### „Vali kaardilt“ ei käivitu

Kontrolli, et kinnistute põhikiht oleks seadistatud, kehtiv ja QGIS-i projekti laaditud.

### Kuvatakse vale kinnistu

Kaardil oli valitud mitu objekti ja Kavitro kasutas valiku esimest. Puhasta valik ning vali ainult soovitud kinnistu.

### Kinnistu leiti otsingust, kuid mitte kaardilt

Kinnistu on teenuses olemas, kuid puudub põhikihilt või ei leita katastritunnuse järgi. Kontrolli õiget põhikihti, välja `tunnus` ja `search_field` väärtusi.

### Seotud andmeid ei leitud

Kontrolli, kas kinnistu on Kavitro teenuses olemas ja katastritunnus vastab täpselt teenuse väärtusele. Arvesta, et Töid ja Teostusjooniseid see vaade praegu ei lae.

### Seoste muutmine ei kajastu kohe

Seotud andmete vaade kasutab lühiajalist vahemälu ega lae kogu puud automaatselt ümber. Ava kinnistu hiljem uuesti.

### Kaustanupp on passiivne

Kirjel puudub kaustatee. Kausta olemasolu QGIS-i failisüsteemis ei aktiveeri nuppu enne, kui tee on salvestatud kirje `filesPath` väärtusse.

### Leping või kooskõlastus ei fokuseeru põhikihile

Praegune kaardinupp toetab nende moodulite puhul ainult seotud kinnistute kuvamist.

## Kontrollnimekiri

Pärast kinnistuvaate kasutamist kontrolli, et:

- valitud on õige kinnistute põhikiht;
- kokkuvõttes kuvatakse soovitud kinnistu katastritunnus;
- kaardil ei ole kogemata mitut kinnistut valitud;
- seotud andmete puuduvat tulemust ei tõlgendata automaatselt seose puudumisena;
- kirjekaardi kausta- ja veebitoiming avavad õige kirje;
- kinnistuseoste muutmisel kinnitati õige tervikvalik;
- vajaduse korral arvestati lühiajalise vahemälu ja moodulikatvuse piirangutega.
