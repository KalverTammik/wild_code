# Servituutide mooduli seadistamine

Servituutide seadistuskaardil määratakse servituutide QGIS-i põhikiht, eelistatud staatused ja liigid, projekti tahvli „Alustamata“ staatused ning Kavitro taustastaatuste vasted QGIS-i kihi staatusevälja väärtustega.

Moodulikaartide üldine kasutamine on kirjeldatud juhendis [Mooduli kihtide ja filtrieelistuste seadistamine](04_mooduli_kihtide_ja_filtrieelistuste_seadistamine.md).

Uue servituudiala joonistamine, olemasoleva polügooni sidumine, geomeetria muutmine, automaatne eelvaade ja PDF-skeem on kirjeldatud juhendis [Servituutide mooduli kaarditoimingud](14_servituutide_mooduli_kaarditoimingud.md).

## Eeltingimused

Enne servituutide seadistamist veendu, et:

- kasutajal on servituutide mooduli kasutusõigus;
- avatud on õige QGIS-i projekt;
- servituutide põhikiht on kehtiv polügoonikiht;
- kihil on staatuseväli nimega `Staatus`, `staatus` või `status`;
- staatuseväljal on QGIS-i väärtuskaart või vähemalt mõnel objektil näidisväärtus;
- Kavitro sessioon ja internetiühendus on aktiivsed.

## Servituutide kohustuslikud seaded

Servituutide mooduli valmisoleku kontroll eeldab:

- põhikihti;
- vähemalt üht eelistatud staatust;
- vähemalt üht eelistatud liiki;
- vähemalt üht projekti tahvli „Alustamata“ staatust;
- salvestatud servituudi kihi staatuste seost.

Servituutide moodulil ei ole eraldi arhiivikihti ega eelistatud tunnuste valikut.

## Servituutide põhikihi valimine

1. Ava Kavitro **Seaded**.
2. Leia kaart **Servituudid**.
3. Vali väljale **Mooduli kiht** õige servituutide kiht.
4. Veendu, et tegemist on polügoonikihiga.
5. Vajuta **Kinnita**.

Kui seadistatud nimega kihte on projektis mitu, ei saa Kavitro üheselt otsustada, millist kasutada. Vali põhikiht seadetes uuesti, et salvestada konkreetse kihi viide.

Servituutide kaarditöövood võivad vajaduse korral lisada kihile väljad `ext_easement_id`, `ext_system` ja `ext_easement_number`. Kihi andmeallikas peab seetõttu olema kirjutatav.

## Eelistatud staatused

Jaotises **Eelistatud staatused** vali Kavitro taustastaatused, mida soovid servituutide staatusefiltri algvalikuna kasutada. Mooduli esmasel avamisel filtreeritakse kirjeid nende staatuste järgi.

See valik ei määra, milline tekst kirjutatakse QGIS-i kihi staatuseväljale. Kihi väärtus määratakse eraldi staatuste vastenduses.

## Eelistatud liigid

Jaotises **Eelistatud liigid** vali servituudiliigid, mida soovid liigifiltri algvalikuna kasutada. Valik mõjutab mooduli esmast filtrit, kuid ei muuda olemasolevate servituutide liiki.

## Projekti tahvli „Alustamata“ staatused

Jaotises **Vali alustamata staatused** määra taustastaatused, mille korral kuvatakse servituut projekti ülevaate tahvli veerus **Alustamata**.

Eelistatud staatused, „Alustamata“ staatused ja kihi staatuste vastendus on kolm erinevat seadet:

- eelistatud staatused määravad staatusefiltri algvaliku;
- „Alustamata“ staatused mõjutavad projekti tahvli rühmitust;
- staatuste vastendus määrab QGIS-i kihi `Staatus` välja väärtuse.

## Staatusevälja nõuded

Kavitro otsib põhikihilt esimest sobivat välja järgmiste nimede järgi:

- `Staatus`;
- `staatus`;
- `status`.

Nime suur- ja väiketähti ei eristata. Kui sobivat välja ei leita, ei saa staatuste vastendamise dialoogi avada.

Dialoogi valikute koostamiseks kasutab Kavitro:

1. eelisjärjekorras QGIS-i välja vidina **Väärtuskaart / Value Map** väärtusi;
2. väärtuskaardi puudumisel kuni 200 kihis juba esinevat unikaalset staatuseväärtust.

Kui väli on olemas, kuid sellel ei ole väärtuskaarti ega ühtegi täidetud näidisväärtust, lisa esmalt QGIS-is väärtuskaart või sisesta kihile vähemalt vajalikud näidisväärtused.

## Kavitro staatuste vastendamine kihi väärtustega

1. Vali ja salvesta esmalt servituutide põhikiht.
2. Leia seadistuskaardilt **Servituudi kihi staatuste seos**.
3. Vajuta rea seadistusnuppu.
4. Kontrolli dialoogi ülaosas kihi ja staatusevälja nime.
5. Vali iga Kavitro taustastaatuse kõrvale vastav QGIS-i kihi väärtus.
6. Jäta mittevajalikud read soovi korral valikule **Ära kirjuta**.
7. Kinnita dialoog.
8. Kontrolli seadistuskaardil kuvatavat seoste kokkuvõtet.
9. Vajuta seadistuste akna all **Kinnita**.

Seos salvestatakse Kavitro staatuse ID ja nimega. Tavakasutuses leitakse vaste esmalt staatuse ID järgi; vanema või muutunud seadistuse korral proovitakse ka staatuse nime.

### Valiku „Ära kirjuta“ praegune käitumine

Dialoog ei salvesta vastendusrida staatusele, mille juures on valitud **Ära kirjuta**. Praegune servituutide kihi kirjutamisloogika kasutab puuduva vastenduse korral siiski Kavitro taustastaatuse nime.

Seega ei tähenda **Ära kirjuta** praeguses versioonis alati tühjaks jätmist. Kui taustastaatus saadetakse objekti loomise või uuendamise töövoogu, võib kihi staatuseväljale kirjutuda taustastaatuse nimi. Kui soovid kindlat kihiväärtust, määra sellele staatusele alati otsene vaste.

## Millal vastendust kasutatakse?

Kavitro kasutab salvestatud seost siis, kui servituudi andmeid kirjutatakse taustateenusest QGIS-i põhikihti, näiteks:

- uue servituudiobjekti loomisel;
- olemasoleva servituudiobjekti uuendamisel;
- servituudi andmete ja geomeetria sünkroonimisel.

Vastendus ei muuda tagasiulatuvalt kõigi olemasolevate kihiobjektide staatuseid kohe pärast **Kinnita** vajutamist. Uus väärtus rakendub järgmise vastava kirjutamis- või sünkroonimistoimingu käigus.

Servituudiobjekti eraldi arhiveerimise toiming määrab kihi staatuseks vaikimisi `(puudub)` ja ei kasuta selleks staatuste vastendust.

## Näide

Oletame, et Kavitro teenuses on staatused:

- Uus;
- Menetluses;
- Sõlmitud.

QGIS-i kihi väärtuskaardis kasutatakse väärtusi:

- Kavandamisel;
- Töös;
- Kehtiv.

Sobiv vastendus võib olla:

| Kavitro taustastaatus | QGIS-i kihi väärtus |
|---|---|
| Uus | Kavandamisel |
| Menetluses | Töös |
| Sõlmitud | Kehtiv |

Pärast salvestamist kirjutab Kavitro sünkroonimisel taustastaatuse **Menetluses** korral kihi staatuseväljale väärtuse **Töös**.

## Geospatiali mapper

Geospatiali režiimis kuvatakse servituutide kaardil ka kihi mapper. Selle abil saab olemasoleva lähtekihi geomeetria ja atribuudid kanda valitud servituutide põhikihti.

Servituutide puhul proovib mapper olemasolevaid objekte uuendada välja `ext_easement_id` järgi ning selle puudumisel välja `ext_job_id` järgi. Üksikasjalik töövoog on juhendis [Geospatiali kihtide vastendamine](06_geospatiali_kihtide_vastendamine.md).

Mapperi väljavastendus ja servituutide staatuste seos täidavad erinevat eesmärki:

- mapper kannab korraga olemasoleva lähtekihi andmed sihtkihti;
- staatuste seos teisendab Kavitro taustastaatuse väärtuse hilisemates servituutide töövoogudes.

## Muudatuste salvestamine

Põhikihi, eelistuste ja staatuste seose muudatused rakenduvad pärast seadistuste akna nupu **Kinnita** vajutamist.

Staatuste vastendamise dialoogi **OK** sulgeb dialoogi ja jätab uue seose ootele. Kui lahkud seadistustest valikuga **Hülga**, taastatakse viimati salvestatud vastendus.

## Lähtestamine

Servituutide kaardi **Lähtesta** nupp eemaldab kohe:

- põhikihi viite;
- eelistatud staatused;
- eelistatud liigid;
- „Alustamata“ staatused;
- staatuste vastenduse.

Lähtestamine ei kustuta servituutide kihti ega muuda kohe olemasolevate objektide staatuseväärtusi. Pärast lähtestamist ei läbi moodul valmisoleku kontrolli enne seadete uuesti määramist.

## Levinumad olukorrad

### Staatuste seostamise dialoog ei avane

Kontrolli järjekorras:

1. kas servituutide põhikiht on valitud ja salvestatud;
2. kas kiht on kehtiv polügoonikiht;
3. kas kihil on väli `Staatus` või `status`;
4. kas väljal on väärtuskaart või olemasolevad väärtused;
5. kas Kavitro taustastaatused laaditi edukalt.

### Kihi staatuse väärtust ei ole valikus

Lisa soovitud väärtus QGIS-is staatusevälja väärtuskaarti. Väärtuskaardi puudumisel sisesta väärtus vähemalt ühele näidisobjektile ja ava dialoog uuesti.

### Kihi staatuseks kirjutati Kavitro staatuse nimi

Sellele taustastaatusele ei olnud salvestatud otsest vastet. Ava staatuste seos, vali soovitud kihiväärtus ja vajuta **Kinnita**.

### Muudetud seos ei rakendunud olemasolevatele objektidele

Vastendus ei tee massuuendust. See rakendub objekti järgmise loomise või sünkroonimise ajal. Olemasolevate väärtuste massiliseks muutmiseks kasuta kontrollitud QGIS-i redigeerimist või eraldi andmetöötlust.

### Servituutide moodul suunab seadistustesse

Kontrolli lisaks põhikihile ka eelistatud staatuseid, liike, „Alustamata“ staatuseid ja staatuste seost. Pärast kõigi väärtuste määramist vajuta **Kinnita**.

## Kontrollnimekiri

Pärast servituutide seadistamist kontrolli, et:

- valitud põhikiht on õige ja polügoongeomeetriaga;
- kiht on kirjutatav;
- staatuseväli on olemas;
- eelistatud staatused ja liigid on määratud;
- „Alustamata“ staatused vastavad tööprotsessile;
- kõik vajalikud Kavitro staatused on seotud sobiva kihiväärtusega;
- vähemalt ühe testobjekti sünkroonimisel kirjutatakse oodatud staatus;
- ootel muudatused on kinnitatud.
