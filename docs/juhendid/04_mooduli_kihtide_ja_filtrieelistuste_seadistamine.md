# Mooduli kihtide ja filtrieelistuste seadistamine

Igal kasutajale lubatud Kavitro moodulil on seadistustes oma kaart. Moodulikaardil määratakse kaardiga seotud töökiht ning moodulist sõltuvalt arhiivikiht, eelistatud staatused, liigid, tunnused ja projekti ülevaate tahvli „Alustamata“ staatused.

See juhend kirjeldab kõikide moodulikaartide ühiseid valikuid. Projektide, kinnistute, servituutide ja teiste moodulite eritoimingud kirjeldatakse eraldi juhendites. Seadistuste salvestamise üldine töövoog on juhendis [Kavitro seadistuste mooduli kasutamine](01_seadistuste_mooduli_kasutamine.md).

## Eeltingimused

Enne mooduli seadistamist veendu, et:

- oled Kavitrosse sisse logitud;
- kasutajal on seadistatava mooduli kasutusõigus;
- avatud on õige QGIS-i projekt;
- vajalikud töö- ja arhiivikihid on projekti laaditud;
- Kavitro teenus on kättesaadav, et laadida staatused, liigid ja tunnused.

Kasutajale kuvatakse ainult nende moodulite kaardid, millele tal on juurdepääs.

## Mooduli seadistuskaardi avamine

1. Ava Kavitro plugina aken.
2. Vali külgribalt **Seaded**.
3. Liigu soovitud mooduli nimega kaardini.
4. Oota vajaduse korral, kuni Kavitro laadib filtri valikud.

Kui proovid avada seadistamata moodulit, võib Kavitro näidata hoiatust, avada automaatselt **Seaded** ja kerida vastava mooduli kaardini.

## Millised valikud on moodulitel?

| Moodul | Mooduli kiht | Arhiivikiht | Staatused | Liigid | Tunnused | „Alustamata“ staatused |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Kinnistud | ✓ | ✓ | – | – | – | – |
| Projektid | ✓ | – | ✓ | – | ✓ | ✓ |
| Lepingud | ✓ | – | ✓ | ✓ | ✓ | ✓ |
| Kooskõlastused | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Servituudid | ✓ | – | ✓ | ✓ | – | ✓ |
| Tööd | ✓ | – | ✓ | ✓ | – | ✓ |
| Teostusjoonised | ✓ | – | ✓ | ✓ | – | ✓ |

Lisaks on mõnel kaardil eriseaded või andmetööriistad:

- **Kinnistud** – kinnistukihtide ja kinnistuandmete haldus, mida kirjeldab juhend [Kinnistute kihi seadistamine ja haldamine](05_kinnistute_kihi_seadistamine_ja_haldamine.md);
- **Projektid** – projekti kaustad, nime reegel, ajutine kiht ja tahvli staatused on juhendis [Projektide mooduli seadistamine](07_projektide_mooduli_seadistamine.md), igapäevased töövood juhendis [Projektide mooduli kasutamine](13_projektide_mooduli_kasutamine.md);
- **Servituudid** – põhikiht ja Kavitro staatuste vastendus QGIS-i kihi väärtustega on juhendis [Servituutide mooduli seadistamine](08_servituutide_mooduli_seadistamine.md), igapäevased kaardi- ja eelvaatetoimingud juhendis [Servituutide mooduli kaarditoimingud](14_servituutide_mooduli_kaarditoimingud.md);
- **Tööd ja teostusjoonised** – kaardikihtide nõuded, ajutise tööde kihi loomine ning teostusjoonise sidumisväljad, mida kirjeldab juhend [Tööde ja teostusjooniste mooduli seadistamine](09_toode_ja_teostusjooniste_seadistamine.md); igapäevased töövood on juhendites [Tööde mooduli kaarditoimingud](11_toode_mooduli_kaarditoimingud.md) ja [Teostusjooniste mooduli kasutamine](12_teostusjooniste_mooduli_kasutamine.md);
- **Lepingud ja kooskõlastused** – kihtide, kooskõlastuste arhiivikihi ja kõigi filtrieelistuste seadistamine, mida kirjeldab juhend [Lepingute ja kooskõlastuste mooduli seadistamine](10_lepingute_ja_kooskolastuste_seadistamine.md);
- **Geospatiali režiim** – lähtekihi väljade ja andmete vastendamine mooduli põhikihti, mida kirjeldab juhend [Geospatiali kihtide vastendamine](06_geospatiali_kihtide_vastendamine.md).

## Mooduli põhikihi valimine

Väli **Mooduli kiht** määrab QGIS-i kihi, mida Kavitro kasutab selle mooduli kaardiga seotud töövoogudes.

Kinnistute kaardil on sama välja nimi **Kinnistute põhikiht**. See kiht on kinnistute kaarditoimingute ja seotud kinnistute kuvamise alus.

Põhikihi valimiseks:

1. Leia mooduli kaardilt **Mooduli kiht** või **Kinnistute põhikiht**.
2. Ava kihi valik.
3. Vali õige QGIS-i kiht.
4. Kontrolli kaardi all kuvatavat aktiivsete kihtide kokkuvõtet.
5. Vajuta **Kinnita**.

Valikusse kuvatakse QGIS-i projektis olevad geomeetriaga kihid. Salvestatud on kihi sisemine viide, mitte ainult kasutajale kuvatav nimi.

Mooduli töökiht ja kinnistute põhikiht täidavad erinevat ülesannet. Näiteks teise mooduli objekti juures olev seotud kinnistu toiming **Näita kaardil** kasutab kinnistute mooduli põhikihti, mitte aktiivse mooduli enda töökihti.

## Arhiivikihi valimine

Arhiivikiht on olemas kinnistute ja kooskõlastuste seadistuskaardil. Seda kasutatakse ajalooliste või aktiivsest põhikihist eemaldatud objektide hoidmiseks.

Arhiivikihi valimiseks:

1. Vali esmalt mooduli põhikiht.
2. Ava väli **Arhiivikiht**.
3. Vali projektist selle mooduli arhiivikiht.
4. Veendu, et põhi- ja arhiivikihiks ei valitud kogemata sama kihti.
5. Vajuta **Kinnita**.

Praegune mooduli valmisoleku kontroll eeldab arhiivikihti kõigil moodulitel, mille kaardil arhiiviväli kuvatakse. Seetõttu võivad kinnistute ja kooskõlastuste töövood suunata seadistustesse ka siis, kui põhikiht on valitud, kuid arhiivikiht puudub.

## Eelistatud staatused

Jaotis **Eelistatud staatused** kuvatakse projektide, lepingute, kooskõlastuste, servituutide, tööde ja teostusjooniste kaardil.

Eelistatud staatused laaditakse mooduli staatusefiltri algvalikuteks ning mooduli esmasel avamisel kasutatakse neid kirjete filtreerimiseks. Kasutaja saab aktiivse mooduli filtrit hiljem muuta või tühjendada. Seade ei loo uusi staatusi ega muuda objektide olemasolevat staatust.

1. Ava jaotis **Eelistatud staatused**.
2. Oota staatuste laadimist.
3. Märgi üks või mitu sagedamini kasutatavat staatust.
4. Vajuta **Kinnita**.

Vähemalt üks eelistatud staatus peab olema valitud, et staatuseid toetav moodul läbiks valmisoleku kontrolli.

## Eelistatud liigid

Jaotis **Eelistatud liigid** kuvatakse lepingute, kooskõlastuste, servituutide, tööde ja teostusjooniste kaardil.

Valitud liigid laaditakse mooduli liigifiltri algvalikuteks. Tööde ja teostusjooniste moodulis määravad need lisaks mooduli liigipiirkonna: loend ja uue töö loomise vorm kasutavad ainult seadistatud liike. Teistes moodulites saab aktiivset liigifiltrit pärast avamist muuta. Valik ei kustuta teisi liike Kavitro teenusest ega muuda olemasolevate objektide liiki.

1. Ava **Eelistatud liigid**.
2. Märgi üks või mitu kasutatavat liiki.
3. Vajuta **Kinnita**.

Vähemalt üks liik peab olema valitud moodulitel, mis liikide eelistust toetavad.

## Eelistatud tunnused

Jaotis **Eelistatud tunnused** kuvatakse projektide, lepingute ja kooskõlastuste kaardil.

Valitud tunnused laaditakse tunnusefiltri algvalikuteks ja neid kasutatakse mooduli esmasel avamisel kirjete filtreerimiseks. Aktiivset filtrit saab hiljem muuta. Tunnuste valimine ei lisa neid automaatselt olemasolevatele objektidele.

1. Ava **Eelistatud tunnused**.
2. Märgi üks või mitu sagedamini kasutatavat tunnust.
3. Vajuta **Kinnita**.

Vähemalt üks tunnus peab olema valitud moodulitel, mis tunnuste eelistust toetavad.

## Projekti tahvli „Alustamata“ staatused

Jaotis **Vali alustamata staatused** kuvatakse kõigil moodulitel, mis toetavad staatuseid.

Selle valikuga määratakse Kavitro taustastaatused, mille korral kuvatakse mooduli kirjed projekti ülevaate tahvli veerus **Alustamata**. See valik ei muuda kirje staatust – see määrab ainult, kuidas olemasolevat staatust projekti tahvlil rühmitatakse.

1. Ava **Vali alustamata staatused**.
2. Märgi üks või mitu staatust, mis tähendavad teie tööprotsessis alustamata tööd.
3. Vajuta **Kinnita**.

Vähemalt üks „Alustamata“ staatus peab olema valitud, et staatuseid toetav moodul läbiks valmisoleku kontrolli.

Eelistatud staatused ja „Alustamata“ staatused ei ole sama seade:

- **Eelistatud staatused** määravad staatusefiltri algvaliku;
- **„Alustamata“ staatused** mõjutavad kirjete paigutust projekti ülevaate tahvlil.

## Soovitatav seadistamise järjekord

Iga mooduli puhul kasuta järgmist järjekorda:

1. Vali mooduli põhikiht.
2. Vali arhiivikiht, kui see on kaardil olemas.
3. Vali eelistatud staatused.
4. Vali eelistatud liigid, kui moodul neid toetab.
5. Vali eelistatud tunnused, kui moodul neid toetab.
6. Vali projekti tahvli „Alustamata“ staatused.
7. Täida moodulipõhised lisaseaded.
8. Kontrolli kaardi all kuvatavat kokkuvõtet.
9. Vajuta **Kinnita**.

## Muudatuste salvestamine ja hülgamine

Kihi- ja filtrivalikud ei rakendu enne nupu **Kinnita** vajutamist. Ühe kinnitamisega salvestatakse kõikidel seadistuskaartidel ootel olevad muudatused.

Kui lahkud seadistustest enne kinnitamist:

- **Salvesta** kinnitab kõik ootel muudatused;
- **Hülga** taastab viimati salvestatud valikud;
- **Tühista** jätab kasutaja seadistuste moodulisse.

## Moodulikaardi lähtestamine

Moodulikaardi **Lähtesta** nupp eemaldab kohe:

- põhikihi viite;
- arhiivikihi viite, kui moodul seda toetab;
- eelistatud staatused;
- eelistatud liigid;
- eelistatud tunnused;
- projekti tahvli „Alustamata“ staatused;
- moodulipõhised lisaväärtused.

**Oluline:** lähtestamine kirjutab salvestatud väärtused kohe tühjaks. Hilisem **Hülga** ei taasta neid. QGIS-i kihte ja nende objekte ei kustutata.

Pärast lähtestamist tuleb moodul enne kasutamist uuesti seadistada.

## Millal seadistus on kohustuslik?

Kavitro kontrollib mooduli avamisel, kas selle tööks vajalikud väärtused on olemas. Sõltuvalt moodulist kontrollitakse:

- põhikihti;
- arhiivikihti;
- vähemalt üht eelistatud staatust;
- vähemalt üht eelistatud liiki;
- vähemalt üht eelistatud tunnust;
- vähemalt üht projekti tahvli „Alustamata“ staatust;
- moodulipõhiseid kohustuslikke lisaseadeid.

Puuduva väärtuse korral kuvatakse hoiatus ja kasutaja suunatakse vastava mooduli seadistuskaardile.

## Levinumad olukorrad

### Mooduli kaarti ei kuvata

Kasutajal puudub selle mooduli kasutusõigus. Kontrolli kasutaja kaardil rolle ja moodulite juurdepääse. Õigusi ei saa QGIS-i pluginas muuta.

### Kihti ei ole valikus

Kontrolli, et õige projekt oleks avatud ning vajalik geomeetriaga kiht projekti laaditud. Kui kiht lisati pärast seadistuste avamist, sulge ja ava seadistuste vaade uuesti.

### Varem valitud kiht on kadunud

Kiht on projektist eemaldatud või projekt on vahetunud. Lisa kiht tagasi või vali uues projektis sobiv kiht ja vajuta **Kinnita**.

### Staatuseid, liike või tunnuseid ei kuvata

Valikud laaditakse Kavitro teenusest. Kontrolli internetiühendust ja aktiivset kasutajasessiooni ning ava valik uuesti. Kuvatud valikud sõltuvad moodulist ja kasutaja õigustest.

### Moodul suunab endiselt seadistustesse

Kontrolli kogu moodulikaarti, mitte ainult põhikihti. Puudu võib olla arhiivikiht, filtrieelistus, „Alustamata“ staatus või moodulipõhine lisaseade. Pärast kõigi väärtuste valimist vajuta **Kinnita**.

### Eelistuse muutmine ei muutnud olemasolevaid objekte

See on ootuspärane. Eelistused mõjutavad filtrite algvalikuid ja projekti tahvli rühmitamist, mitte olemasolevate objektide andmeid.

### „Kinnita“ nuppu ei kuvata

Nupp ilmub ainult tuvastatud salvestamata muudatuse korral. Kui vajutasid moodulikaardi **Lähtesta** nuppu või käivitasid eraldi andmetööriista, võis toiming rakenduda kohe.

## Kontrollnimekiri

Pärast mooduli seadistamist kontrolli, et:

- valitud on õige põhikiht;
- arhiiviväljaga moodulil on valitud õige arhiivikiht;
- kõik kuvatavad eelistuste jaotised sisaldavad vähemalt üht sobivat valikut;
- „Alustamata“ staatuste valik vastab teie tööprotsessile;
- moodulipõhised lisaseaded on täidetud;
- muudatused on kinnitatud;
- moodul avaneb ilma seadistustesse suunamiseta;
- kaarditoimingud kasutavad õiget QGIS-i kihti.
