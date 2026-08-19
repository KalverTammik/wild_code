# Lepingute ja kooskõlastuste mooduli seadistamine

Lepingute ja kooskõlastuste seadistuskaartidel määratakse mooduli QGIS-i kihid, eelistatud staatused, liigid ja tunnused ning projekti tahvli „Alustamata“ staatused. Kooskõlastuste kaart nõuab lisaks arhiivikihti.

Moodulikaartide ühine kasutamine on kirjeldatud juhendis [Mooduli kihtide ja filtrieelistuste seadistamine](04_mooduli_kihtide_ja_filtrieelistuste_seadistamine.md). Igapäevast loendi, tähtajafiltrite, detailide ja kinnistuseoste kasutamist kirjeldab [Lepingute ja kooskõlastuste mooduli kasutamine](16_lepingute_ja_kooskolastuste_mooduli_kasutamine.md).

## Moodulite erinevused

| Seadistus | Lepingud | Kooskõlastused |
|---|:---:|:---:|
| Põhikiht | ✓ | ✓ |
| Arhiivikiht | – | ✓ |
| Eelistatud staatused | ✓ | ✓ |
| Eelistatud liigid | ✓ | ✓ |
| Eelistatud tunnused | ✓ | ✓ |
| „Alustamata“ staatused | ✓ | ✓ |

## Eeltingimused

Enne seadistamist veendu, et:

- kasutajal on lepingute või kooskõlastuste mooduli kasutusõigus;
- avatud on õige QGIS-i projekt;
- vajalikud põhi- ja arhiivikihid on projekti laaditud;
- Geospatiali mapperi kasutamisel on sihtkiht kirjutatav;
- Kavitro sessioon ja internetiühendus on aktiivsed.

## Lepingute kohustuslikud seaded

Lepingute mooduli valmisoleku kontroll eeldab:

- põhikihti;
- vähemalt üht eelistatud staatust;
- vähemalt üht eelistatud liiki;
- vähemalt üht eelistatud tunnust;
- vähemalt üht projekti tahvli „Alustamata“ staatust.

Lepingute moodulil ei ole arhiivikihi valikut.

## Kooskõlastuste kohustuslikud seaded

Kooskõlastuste mooduli valmisoleku kontroll eeldab:

- põhikihti;
- arhiivikihti;
- vähemalt üht eelistatud staatust;
- vähemalt üht eelistatud liiki;
- vähemalt üht eelistatud tunnust;
- vähemalt üht projekti tahvli „Alustamata“ staatust.

Kui kasvõi üks neist väärtustest puudub, võib Kavitro suunata kasutaja kooskõlastuste mooduli asemel seadistustesse.

## Lepingute põhikihi valimine

1. Ava Kavitro **Seaded**.
2. Leia kaart **Lepingud**.
3. Vali väljale **Mooduli kiht** lepingute QGIS-i kiht.
4. Vali eelistatud staatused, liigid ja tunnused.
5. Vali projekti tahvli „Alustamata“ staatused.
6. Vajuta **Kinnita**.

Praeguses versioonis kasutatakse lepingute põhikihti eelkõige mooduli kihiseadistusena ja Geospatiali mapperi sihtkihina. Lepingute loend ja detailandmed laaditakse Kavitro teenusest.

## Kooskõlastuste põhi- ja arhiivikihi valimine

1. Ava Kavitro **Seaded**.
2. Leia kaart **Kooskõlastused**.
3. Vali väljale **Mooduli kiht** kooskõlastuste töökiht.
4. Vali väljale **Arhiivikiht** kooskõlastuste arhiivikiht.
5. Vali eelistatud staatused, liigid ja tunnused.
6. Vali projekti tahvli „Alustamata“ staatused.
7. Vajuta **Kinnita**.

Kavitro ei loo kooskõlastuste arhiivikihti automaatselt. Vajalik kiht tuleb enne QGIS-i projekti laadida ja seejärel seadistuskaardilt valida.

### Arhiivikihi praegune roll

Praeguses koodiversioonis on kooskõlastuste arhiivikiht mooduli valmisoleku kontrolli kohustuslik osa, kuid kooskõlastuste moodulis ei ole eraldi arhiveerimistoimingut, mis objekte automaatselt põhikihilt sellele kihile tõstaks.

Seetõttu:

- vali organisatsiooni töökorralduses kooskõlastuste arhiiviks mõeldud õige kiht;
- ära eelda, et ainult seadistuse salvestamine kopeerib või liigutab objekte;
- ära aja seda segi kinnistute arhiivikihiga, millel on eraldi andmehaldustoimingud;
- arvesta, et arhiivikihi puudumine takistab siiski kooskõlastuste mooduli valmisoleku kontrolli läbimist.

## Eelistatud staatused

Jaotises **Eelistatud staatused** vali mõlemas moodulis staatused, mida soovid staatusefiltri algvalikuna kasutada. Mooduli esmasel avamisel filtreeritakse kirjeid nende staatuste järgi.

Valik:

- ei muuda olemasolevate lepingute või kooskõlastuste staatust;
- ei eemalda teisi staatuseid Kavitro teenusest;
- määrab kasutaja filtri algvaliku, mida saab aktiivses moodulis muuta.

Vähemalt üks eelistatud staatus peab olema valitud.

## Eelistatud liigid

Jaotises **Eelistatud liigid** vali lepingu- või kooskõlastusliigid, mida soovid liigifiltri algvalikuna kasutada. Valik mõjutab mooduli esmast filtrit, mitte olemasolevate kirjete andmeid.

Vähemalt üks eelistatud liik peab olema valitud.

## Eelistatud tunnused

Jaotises **Eelistatud tunnused** vali tunnused, mida soovid tunnusefiltri algvalikuna kasutada. Valik mõjutab mooduli esmast filtrit, kuid ei lisa tunnuseid automaatselt olemasolevatele kirjetele.

Vähemalt üks eelistatud tunnus peab olema valitud.

## Projekti tahvli „Alustamata“ staatused

Jaotises **Vali alustamata staatused** määra taustastaatused, mille korral kuvatakse leping või kooskõlastus projekti ülevaate tahvli veerus **Alustamata**.

See seadistus on eelistatud staatustest eraldi:

- eelistatud staatused määravad staatusefiltri algvaliku;
- „Alustamata“ staatused määravad projekti tahvlil rühmitamise.

Valik ei muuda lepingu ega kooskõlastuse tegelikku staatust.

## Filtrite kasutamine moodulis

Lepingute ja kooskõlastuste mooduli tööriistaribal saab filtreerida Kavitro teenusest laaditud kirjeid staatuse, liigi ja tunnuste järgi. Seadistuskaardil valitud eelistused määravad nende filtrite eelistatud valikud.

Kui filtri väärtuseid ei kuvata, kontrolli sessiooni ja internetiühendust. Filtrite loendid pärinevad Kavitro teenusest, mitte QGIS-i põhikihi atribuutidest.

## Geospatiali mapper

Geospatiali režiimis saab lähtekihi geomeetria ja atribuudid kanda lepingute või kooskõlastuste põhikihti. Põhikiht on mapperi sihtkiht; arhiivikihti mapper sihtkohana ei kasuta.

Lepingute ja kooskõlastuste moodulile ei ole praeguses versioonis määratud automaatset identifikaatorivälja, mille alusel mapper olemasolevat sihtobjekti uuendaks. Seetõttu lisatakse ülekantavad objektid uutena ka siis, kui lähte- ja sihtkihis leidub mõni sama nimega ID-väli.

**Oluline:** sama lähtekihi korduv ülekandmine võib tekitada sihtkihti duplikaadid. Kontrolli enne uut käivitust, millised objektid on juba üle kantud.

Mapperi geomeetrianõuded, väljade vastendamine ja eelvaade on kirjeldatud juhendis [Geospatiali kihtide vastendamine](06_geospatiali_kihtide_vastendamine.md).

## Kaardilt Kavitro kirje avamise piirang

Üldine kaarditoiming **Mis see on** ei toeta praeguses versioonis lepingute ega kooskõlastuste moodulit. Põhikihi valimine ei lisa nendele moodulitele automaatselt kaardilt kirje avamise võimalust.

Lepingud ja kooskõlastused avatakse mooduli loendist, otsingust või seotud objektide vaadetest.

## Muudatuste salvestamine

Kihtide ja kõigi eelistuste muudatused rakenduvad pärast seadistuste akna nupu **Kinnita** vajutamist. Kui lahkud kinnitamata muudatustega ja valid **Hülga**, taastatakse viimati salvestatud valikud.

## Lähtestamine

Kaardi **Lähtesta** nupp eemaldab kohe:

- põhikihi viite;
- kooskõlastuste puhul arhiivikihi viite;
- eelistatud staatused;
- eelistatud liigid;
- eelistatud tunnused;
- „Alustamata“ staatused.

Lähtestamine ei kustuta QGIS-i kihte ega nende objekte. Pärast lähtestamist ei läbi moodul valmisoleku kontrolli enne kõigi kohustuslike seadete uuesti määramist.

## Levinumad olukorrad

### Lepingute moodul suunab seadistustesse

Kontrolli põhikihti ning kõiki nelja eelistuste osa: staatused, liigid, tunnused ja „Alustamata“ staatused. Vajuta pärast valikuid **Kinnita**.

### Kooskõlastuste moodul suunab seadistustesse

Kontrolli lisaks põhikihile ka arhiivikihti. Mõlemad kihid ja kõik eelistused peavad olema salvestatud.

### Arhiivikihti ei ole valikus

Lisa sobiv vektorkiht esmalt QGIS-i projekti. Seejärel ava seadistused uuesti või värskenda kaarti ja vali kiht väljale **Arhiivikiht**.

### Eelistuste valikud on tühjad

Kontrolli internetiühendust, Kavitro sessiooni ja mooduli kasutusõigust. Staatused, liigid ning tunnused laaditakse Kavitro teenusest.

### Mapper tekitas topeltobjektid

Lepingute ja kooskõlastuste mapper ei uuenda objekte ID-välja alusel. Eemalda duplikaadid kontrollitud QGIS-i redigeerimisega ja väldi sama lähteandmestiku korduvat ülekandmist.

### Arhiivikihi valimine ei liigutanud objekte

See on praeguses versioonis ootuspärane. Seadistus salvestab kihi viite ja täidab valmisoleku nõude, kuid ei käivita kooskõlastuste arhiveerimist.

## Kontrollnimekiri

Pärast seadistamist kontrolli, et:

- lepingutel on valitud õige põhikiht;
- kooskõlastustel on valitud õige põhi- ja arhiivikiht;
- mõlemas moodulis on valitud vähemalt üks staatus, liik ja tunnus;
- „Alustamata“ staatused vastavad projekti tahvli tööloogikale;
- muudatused on kinnitatud;
- mõlemad moodulid avanevad ilma seadistustesse suunamiseta;
- Geospatiali mapperi korduskäivitamisel on duplikaatide oht läbi mõeldud.
