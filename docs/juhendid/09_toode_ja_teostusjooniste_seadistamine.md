# Tööde ja teostusjooniste mooduli seadistamine

Tööde ja teostusjooniste seadistuskaartidel määratakse mooduli QGIS-i põhikiht, eelistatud staatused ja liigid ning projekti tahvli „Alustamata“ staatused. Tööde kaardil saab lisaks luua või laadida ajutise GeoPackage-põhise punktikihi.

Moodulikaartide ühine kasutamine on kirjeldatud juhendis [Mooduli kihtide ja filtrieelistuste seadistamine](04_mooduli_kihtide_ja_filtrieelistuste_seadistamine.md).

Moodulite igapäevased kaarditöövood on juhendites [Tööde mooduli kaarditoimingud](11_toode_mooduli_kaarditoimingud.md) ja [Teostusjooniste mooduli kasutamine](12_teostusjooniste_mooduli_kasutamine.md).

## Moodulite peamised erinevused

| Omadus | Tööd | Teostusjoonised |
|---|---|---|
| Põhikiht | Punktikiht | Punkt-, joon- või polügoonikiht |
| Kohustuslik identifikaator | `ext_job_id` peab olemas olema | `ext_job_id` lisatakse vajaduse korral automaatselt |
| Eelistatud staatused | Jah | Jah |
| Eelistatud liigid | Jah | Jah |
| Eelistatud tunnused | Ei | Ei |
| „Alustamata“ staatused | Jah | Jah |
| Arhiivikiht | Ei | Ei |
| Ajutise kihi abiline | Jah | Ei |

## Eeltingimused

Enne seadistamist veendu, et:

- kasutajal on vastava mooduli kasutusõigus;
- avatud on õige QGIS-i projekt;
- vajalik töökiht on projekti laaditud või tead, kuhu uus tööde GeoPackage luua;
- kiht ja selle andmeallikas on kirjutatavad;
- Kavitro sessioon ja internetiühendus on aktiivsed.

## Kohustuslikud seaded

Mõlema mooduli valmisoleku kontroll eeldab:

- põhikihti;
- vähemalt üht eelistatud staatust;
- vähemalt üht eelistatud liiki;
- vähemalt üht projekti tahvli „Alustamata“ staatust.

Töödel ja teostusjoonistel ei ole eelistatud tunnuste ega arhiivikihi seadistust.

## Tööde põhikihi valimine

1. Ava Kavitro **Seaded**.
2. Leia kaart **Tööd**.
3. Vali väljale **Mooduli kiht** õige tööde kiht.
4. Vali eelistatud staatused, liigid ja „Alustamata“ staatused.
5. Vajuta **Kinnita**.

Kaardipõhiste tööde jaoks peab valitud kiht:

- olema kehtiv vektorkiht;
- kasutama punktgeomeetriat;
- sisaldama välja `ext_job_id`;
- võimaldama objektide lisamist ja muutmist.

Kui kiht ei ole punktikiht, ei saa Kavitro uut tööd kaardipunktina luua. Kui väli `ext_job_id` puudub, ei saa loodud kaardiobjekti Kavitro töö kirjega siduda.

Pärast `ext_job_id` leidmist kontrollib Kavitro ka teisi standardseid tööde välju. Puuduvad väljad proovitakse kirjutatavale kihile automaatselt lisada. Kui sama nimega olemasoleva välja tüüp ei sobi oodatud skeemiga, ei saa kihti tööde kaarditoiminguteks kasutada enne skeemi parandamist või sobiva kihi valimist.

Tööde kaarditoimingud võimaldavad muu hulgas:

- luua kaardil valitud punktile uue töö;
- siduda töö võimaluse korral klikitud asukohast leitud kinnistuga;
- lisada olemasoleva töö kaardile;
- näidata ja ümber paigutada seotud töö punkti;
- kontrollida Kavitro kirjega sidumata GIS-i töid.

## Ajutise Tööde GeoPackage-kihi loomine

Jaotis **Ajutine Tööde kihi abiline** loob või laadib punktipõhise tööde kihi ja määrab selle kohe tööde põhikihiks. Abiline on mõeldud eelkõige uue või katsetamiseks sobiva tööde kihi ettevalmistamiseks.

Abiline on nähtav seadistuste tavarežiimis. Geospatiali režiimis kuvatakse selle asemel kihi mapper.

### Viitekihi valimine

Uue kihi koordinaatsüsteem võetakse viitekihilt. Kavitro otsib viitekihi järgmises järjekorras:

1. tööde kaardil parajasti valitud sobiv kiht, eelistades GeoPackage'i kihti;
2. seadistatud kinnistute põhikiht, eelistades GeoPackage'i kihti;
3. muu kehtiv tööde või kinnistute viitekiht.

Kui sobivat viitekihti ei leita, seadista esmalt kinnistute põhikiht või vali tööde kaardil kehtiv kiht.

### Kihi loomise töövoog

1. Vajuta **Loo/lae ajutine Tööde GPKG kiht**.
2. Sisesta kihi nimi.
3. Vali salvestusviis:
   - **Kasuta viitekihi GeoPackage'i**;
   - **Loo eraldiseisev GeoPackage-fail**.
4. Vali vajaduse korral faili asukoht.
5. Kinnita olemasoleva faili ülekirjutamine ainult siis, kui selle kogu sisu võib kustutada.
6. Oota kihi loomist või laadimist.
7. Kontrolli teadet, et kiht määrati tööde põhikihiks.

Loodud või laaditud kiht salvestatakse kohe tööde põhikihi seadeks. Selle toimingu jaoks ei ole vaja vajutada seadistuste akna nuppu **Kinnita** ning hilisem **Hülga** ei taasta tingimata eelmist põhikihti.

### Olemasoleva GeoPackage'i kasutamine

Seda valikut saab kasutada ainult siis, kui viitekiht pärineb `.gpkg` failist.

- Kui sama nimega kiht on GeoPackage'is juba olemas, laaditakse olemasolev kiht.
- Kui sama nimega kihti ei ole, luuakse uus kiht olemasolevasse faili.
- Teisi samas GeoPackage'is olevaid kihte ei kirjutata üle.

### Eraldiseisva GeoPackage'i loomine

Kui valitud `.gpkg` fail on juba olemas, küsib Kavitro ülekirjutamiseks kinnitust.

**Oluline:** kinnitamisel eemaldatakse QGIS-i projektist kõik selle failiga seotud laaditud kihid ja kustutatakse kogu olemasolev GeoPackage-fail. Koos failiga kaovad kõik selles olnud kihid, mitte ainult sisestatud nimega tööde kiht.

### Loodava tööde kihi struktuur

Abiline loob viitekihi koordinaatsüsteemis punktikihi järgmiste väljadega:

| Väli | Tüüp |
|---|---|
| `ext_job_id` | Täisarv |
| `ext_job_name` | Tekst |
| `ext_job_type` | Täisarv |
| `ext_job_state` | Täisarv |
| `detailed` | Tekst |
| `active` | Tõeväärtus |
| `begin_date` | Kuupäev ja kellaaeg |
| `end_date` | Kuupäev ja kellaaeg |
| `added_by` | Tekst |
| `added_date` | Kuupäev ja kellaaeg |
| `updated_by` | Tekst |
| `update_date` | Kuupäev ja kellaaeg |

Loodud kiht on tühi, kuid sobib kohe tööde kaarditoiminguteks.

## Teostusjooniste põhikihi valimine

1. Ava Kavitro **Seaded**.
2. Leia kaart **Teostusjoonised**.
3. Vali väljale **Mooduli kiht** õige teostusjooniste vektorkiht.
4. Vali eelistatud staatused, liigid ja „Alustamata“ staatused.
5. Vajuta **Kinnita**.

Teostusjooniste töövoog ei piira põhikihti ainult ühe geomeetriatüübiga. Kasutada saab punkti-, joone- või polügoonikihti sõltuvalt sellest, millise geomeetriana teie organisatsioon teostusjoonise ulatust hoiab.

Kiht peab olema kirjutatav. Toiming **Joonista uus seotud objekt kaardile** käivitab valitud kihi tavapärase QGIS-i objekti lisamise tööriista, seob loodud objekti Kavitro teostusjoonise kirjega ja saadab geomeetria Kavitro teenusesse.

## Teostusjooniste automaatsed sidumisväljad

Enne joonistamise alustamist kontrollib Kavitro järgmisi välju ja lisab puuduvad väljad põhikihile automaatselt:

| Väli | Lisatav tüüp |
|---|---|
| `ext_job_id` | Tekst |
| `ext_system` | Tekst |
| `ext_job_name` | Tekst |
| `ext_job_type` | Tekst |
| `ext_job_state` | Täisarv |
| `added_by` | Tekst |
| `added_date` | Kuupäev ja kellaaeg |
| `updated_by` | Tekst |
| `update_date` | Kuupäev ja kellaaeg |

Kui andmeallikas ei luba välju lisada, joonistamist ei käivitata. Kui kihis on sama nimega väli juba olemas, kasutab Kavitro olemasolevat välja ega muuda selle tüüpi.

## Teostusjoonise andmevormi väljad

Pärast geomeetria joonistamist avatakse vorm **Teostusjoonise andmed**. Vormil saab sisestada töö numbri, objekti, mõõdistamise kuupäeva, mõõdistaja, kontakti, joonise liigi, mõõtkava, koordinaat- ja kõrgussüsteemi, võrgu liigid ning märkused.

Vormi väärtused kirjutatakse järgmistele kihiväljadele ainult siis, kui vastav väli on kihis juba olemas:

- `Töö nr`;
- `Objekt`;
- `Mõõdistamise kpv`;
- `Mõõdistaja`;
- `Kontakt`;
- `Mõõdistaja, märkused`;
- `Joonis`;
- `Mõõtkava`;
- `Koordinaatsüsteem`;
- `Kõrgussüsteem`;
- `Sisestaja` ja `Sisetus kpv`;
- `Muutja` ja `Muutmis kpv`;
- `Vesi`, `Kanal`, `Sadevesi`, `Elekter ja tänavavalgustus`, `Gaas` ning `Side`.

Neid valdkonnavälju Kavitro automaatselt ei loo. Kui soovid vormi kogu info kihile salvestada, loo vajalikud väljad kihi skeemi enne töövoo kasutamist.

### Oluline QGIS-i redigeerimisseansi kohta

Kui teostusjooniste kiht ei olnud enne joonistamist redigeerimisrežiimis, alustab Kavitro seansi ise. Eduka toimingu järel kinnitatakse Kavitro alustatud seanss ning vea või vormi katkestamise korral pööratakse see tagasi.

Kui kiht oli juba redigeerimisrežiimis, jätab Kavitro seansi kasutaja hallata. Uus objekt võib jääda ootele ka katkestamise või vea korral ning Kavitro teenuse geomeetria võib olla uuendatud enne kohalike muudatuste kinnitamist.

Kõige turvalisem on lõpetada enne toimingu **Joonista uus seotud objekt kaardile** käivitamist sama kihi varasem redigeerimisseanss. Täpne töövoog ja veaolukorrad on kirjeldatud juhendis [Teostusjooniste mooduli kasutamine](12_teostusjooniste_mooduli_kasutamine.md).

## Staatuste ja liikide eelistused

Mõlema mooduli kaardil:

- **Eelistatud staatused** laaditakse staatusefiltri algvalikuks ja neid kasutatakse mooduli esmasel avamisel kirjete filtreerimiseks;
- **Eelistatud liigid** määravad tööde või teostusjooniste mooduli liigipiirkonna, liigifiltri algvaliku ning tööde puhul uue töö vormil lubatud liigid;
- **Vali alustamata staatused** määrab, millised kirjed kuvatakse projekti ülevaate tahvli veerus **Alustamata**.

Need seaded ei muuda olemasolevate kirjete staatust ega liiki. Vähemalt üks valik peab olema tehtud igas kuvatavas jaotises.

## Geospatiali mapper

Geospatiali režiimis saab olemasoleva lähtekihi andmed kanda tööde või teostusjooniste põhikihti. Mõlema mooduli puhul kasutab mapper olemasoleva objekti tuvastamiseks välja `ext_job_id`.

Olemasolevat sihtobjekti uuendatakse ainult siis, kui nii lähte- kui ka sihtkihis on väli `ext_job_id` ja lähteobjektil on selles väärtus. Vastasel juhul lisatakse objekt sihtkihti uuena.

Mapperi täielik töövoog ja geomeetrianõuded on juhendis [Geospatiali kihtide vastendamine](06_geospatiali_kihtide_vastendamine.md).

## Lähtestamine

Kaardi **Lähtesta** nupp eemaldab kohe vastava mooduli:

- põhikihi viite;
- eelistatud staatused;
- eelistatud liigid;
- „Alustamata“ staatused.

Lähtestamine ei kustuta QGIS-i kihti, GeoPackage-faili ega kihi objekte. Ajutise tööde kihi abilisega juba loodud fail jääb alles.

## Levinumad olukorrad

### Tööde moodul ei luba kaardile tööd lisada

Kontrolli, et põhikiht on punktikiht, sisaldab välja `ext_job_id` ja on kirjutatav. Vajaduse korral loo abilisega uus sobiva struktuuriga tööde kiht.

### Ajutise tööde kihi abiline ei ole nähtav

Seadistused on Geospatiali režiimis. Lülita režiim tagasi tavavaatesse; tööde abiline ja Geospatiali mapper ei ole tööde kaardil korraga nähtavad.

### Abiline ei leia viitekihti

Vali tööde kaardil kehtiv viitekiht või seadista kinnistute põhikiht. Viitekihti kasutatakse loodava kihi koordinaatsüsteemi määramiseks.

### Teostusjoonise joonistamine ei käivitu

Kontrolli, et seadistatud põhikiht on projektis alles, kehtiv vektorkiht ja kirjutatav. Andmeallikas peab lubama puuduvate sidumisväljade lisamist.

### Teostusjoonise vormi andmed ei jõudnud kihile

Kavitro lisab automaatselt ainult sidumis- ja auditiväljad. Kontrolli, et kihis on vormile vastava täpse nimega valdkonnaväljad.

### Mapper lisas samad objektid uuesti

Kontrolli, et nii lähte- kui ka sihtkihis on täidetud `ext_job_id`. Ilma ühise identifikaatorita ei saa mapper olemasolevat objekti uuest eristada.

## Kontrollnimekiri

Pärast seadistamist kontrolli, et:

- mõlemal kasutataval moodulil on valitud õige põhikiht;
- tööde kiht on punktikiht ja sisaldab välja `ext_job_id`;
- teostusjooniste kiht on kirjutatav ning vajalike vormiväljadega;
- eelistatud staatused ja liigid on valitud;
- „Alustamata“ staatused vastavad projekti tahvli tööloogikale;
- muudatused on kinnitatud;
- ajutise GeoPackage'i ülekirjutamist ei kinnitatud ekslikult;
- enne teostusjoonise joonistamist ei ole kihil muid salvestamata muudatusi.
