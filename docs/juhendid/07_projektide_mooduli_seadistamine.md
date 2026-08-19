# Projektide mooduli seadistamine

Projektide seadistuskaardil määratakse projektide QGIS-i töökiht, eelistatud staatused ja tunnused, projekti tahvli „Alustamata“ staatused ning projektikaustade loomise lähte- ja sihtkoht. Samal kaardil saab luua või laadida ajutise GeoPackage-põhise projektikihi.

Moodulikaartide ühised kihid ja filtrieelistused on kirjeldatud juhendis [Mooduli kihtide ja filtrieelistuste seadistamine](04_mooduli_kihtide_ja_filtrieelistuste_seadistamine.md).

Projektide nimekirja, edenemistahvli, kinnistuseoste, projektiala ja projektikausta igapäevane kasutamine on kirjeldatud juhendis [Projektide mooduli kasutamine](13_projektide_mooduli_kasutamine.md).

## Eeltingimused

Enne projektide mooduli seadistamist veendu, et:

- kasutajal on projektide mooduli kasutusõigus;
- avatud on õige QGIS-i projekt;
- projektide töökiht on projekti laaditud või tead, kuhu uus GeoPackage luua;
- Kavitro sessioon ja internetiühendus on aktiivsed;
- projektikaustade kasutamisel on kasutajal lähte- ja sihtkausta lugemis- ning kirjutusõigus.

## Projektide mooduli kohustuslikud seaded

Projektide mooduli tavapäraseks kasutamiseks seadista:

- **Mooduli kiht**;
- **Eelistatud staatused**;
- **Eelistatud tunnused**;
- **Vali alustamata staatused**.

Projektikausta genereerimise toiming kontrollib lisaks:

- **Projektide lähtekausta**;
- **Projektide sihtkausta**;
- **Eelistatud kausta nime struktuuri reeglit**.

Puuduvate põhiseadete korral võib Kavitro projektide avamise asemel suunata kasutaja seadistuskaardile. Puuduvad kaustaseaded ei takista projektide mooduli tavavaate avamist, kuid takistavad projekti kausta genereerimist.

## Projektide põhikihi valimine

1. Ava Kavitro **Seaded**.
2. Leia kaart **Projektid**.
3. Vali väljale **Mooduli kiht** projektide QGIS-i kiht.
4. Kontrolli kaardi all kuvatavat aktiivse kihi nime.
5. Vajuta **Kinnita**.

Projektide põhikihti kasutatakse projektide kaardiga seotud toimingutes. Seotud kinnistute kaardil kuvamiseks kasutab Kavitro eraldi kinnistute põhikihti.

## Staatuste ja tunnuste eelistused

### Eelistatud staatused

Vali staatused, mida soovid projektide mooduli staatusefiltri algvalikuna kasutada. Mooduli esmasel avamisel filtreeritakse kirjeid nende staatuste järgi, kuid aktiivset filtrit saab hiljem muuta. Vähemalt üks eelistatud staatus peab olema määratud.

### Eelistatud tunnused

Vali tunnused, mida soovid projektide tunnusefiltri algvalikuna kasutada. Valik mõjutab mooduli esmast filtrit, kuid ei lisa tunnuseid olemasolevatele projektidele. Vähemalt üks eelistatud tunnus peab olema määratud.

### Projekti tahvli „Alustamata“ staatused

Vali taustastaatused, mille korral kuvatakse projekti kirje projekti ülevaate tahvli veerus **Alustamata**. See seadistus ei muuda projekti staatust.

Pärast kõigi eelistuste valimist vajuta **Kinnita**.

## Projektide lähtekaust

**Projektide lähtekaust** on mallkaust, mille kogu sisu kopeeritakse uue projekti kausta. Mall võib sisaldada alamkaustu ja ettevalmistatud faile.

Lähtekausta määramiseks:

1. Vajuta lähtekausta rea seadistusnuppu.
2. Vali olemasolev mallkaust.
3. Kontrolli seadistuskaardil kuvatavat teed.
4. Vajuta **Kinnita**.

Kavitro kopeerib kausta genereerimisel kogu lähtekausta sisu. Hoia mallkaustas ainult failid ja alamkaustad, mis peavad jõudma igasse uude projektikausta.

## Projektide sihtkaust

**Projektide sihtkaust** on juurkaust, mille alla luuakse iga projekti nimeline kaust.

1. Vajuta sihtkausta rea seadistusnuppu.
2. Vali olemasolev sihtkaust.
3. Veendu, et sul on sinna kirjutamisõigus.
4. Kontrolli seadistuskaardil kuvatavat teed.
5. Vajuta **Kinnita**.

Kui sama nimega projekti kaust on sihtkohas juba olemas, Kavitro seda üle ei kirjuta ega ühenda olemasoleva kaustaga.

## Projekti kausta nime reegel

Kausta nimetamise reegel koosneb kuni kolmest järjestikusest osast. Igas osas saab kasutada:

- **Projekti number**;
- **Projekti nimi**;
- **Sümbol** – kasutaja sisestatud eraldaja või muu püsiv tekst;
- **Tühi** – seda kohta ei kasutata.

Näiteks reegel:

1. **Projekti number**;
2. **Sümbol** väärtusega `_`;
3. **Projekti nimi**

moodustab kausta nime kujul `(24)AR-3-1_Minu lemmik projekt`.

Reegli määramiseks:

1. Vajuta rea **Eelistatud kausta nime struktuuri reegel** seadistusnuppu.
2. Vali esimese, teise ja kolmanda koha sisu.
3. Sisesta sümboli tekst kõigil kohtadel, kus valisid **Sümbol**.
4. Kontrolli dialoogi eelvaadet.
5. Kinnita reegel.
6. Vajuta seadistuste akna all **Kinnita**.

Reegel peab sisaldama vähemalt üht osa. Tühja tekstiga sümbolit salvestada ei saa.

### Praeguse versiooni piirang

Koodi praeguses versioonis rakendatakse salvestatud nime reeglit ainult siis, kui kasutaja profiilis on varasem seadistus **Luba eelistatud kausta nime struktuur** sisse lülitatud. Praegusel seadistuskaardil seda lülitit ei kuvata.

Kui lubamise väärtus puudub või on välja lülitatud, kasutab Kavitro salvestatud reegli asemel vaikereeglit:

```text
Projekti number + projekti nimi
```

Vaikereegel ei lisa numbri ja nime vahele automaatselt tühikut ega muud eraldajat. Seetõttu kontrolli loodava kausta nime enne kaustalingi lisamist projektile.

## Projektikausta genereerimine

Projektikausta loomine käivitatakse projektide moodulis konkreetse projekti toimingute menüüst.

1. Ava projektide moodulis soovitud projekt.
2. Vali projekti lisatoimingutest kausta genereerimine.
3. Kontrolli hoiatust, et sama sisuga kausta ei oleks juba loodud.
4. Kinnita loomine.
5. Kavitro moodustab projektinumbri, nime ja salvestatud reegli põhjal kaustanime.
6. Kavitro kopeerib lähtekausta koos alamkaustade ja failidega sihtkausta alla.
7. Pärast kopeerimist vali, kas lisada loodud kausta tee Kavitro projektile.

Kui loobud kaustalingi lisamisest, jääb loodud kaust failisüsteemi alles, kuid projekti `filesPath` väärtust Kavitro teenuses ei uuendata.

Kausta genereerimine on kohene failitoiming. Seadistuste akna **Hülga** ei kustuta loodud kausta ega eemalda juba salvestatud projektilinki.

## Ajutise Projektide GeoPackage-kihi loomine

Jaotis **Ajutine Projektide kihi abiline** loob või laadib polügoonpõhise projektikihi ja määrab selle kohe projektide põhikihiks.

Tööriist vajab viitekihti, mille järgi määrata uue kihi koordinaatsüsteem. Viitekihina kasutatakse:

1. projektide kaardil parajasti valitud sobivat kihti;
2. võimaluse korral kinnistute seadistatud põhikihti;
3. muud kehtivat valitud viitekihti.

Ajutise kihi loomiseks:

1. Vali projektide põhikiht või veendu, et kinnistute põhikiht on seadistatud.
2. Vajuta **Loo/lae ajutine Projektide GPKG kiht**.
3. Sisesta projektide kihi nimi.
4. Vali salvestusviis:
   - **Kasuta viitekihi GeoPackage'i**;
   - **Loo eraldiseisev GeoPackage-fail**.
5. Kinnita faili asukoht ja vajaduse korral ülekirjutamine.
6. Oota kihi loomist või laadimist.
7. Kontrolli teadet, et uus kiht määrati projektide põhikihiks.

Tööriista tehtud kihiseadistus rakendub kohe. Selle jaoks ei ole vaja seadistuste akna **Kinnita** nuppu ning hilisem **Hülga** ei pruugi taastada enne tööriista käivitamist salvestatud kihiviidet.

### Viitekihi GeoPackage'i kasutamine

See valik on saadaval ainult siis, kui viitekiht pärineb `.gpkg` failist.

- Kui sama nimega kiht on selles GeoPackage'is juba olemas, laaditakse olemasolev kiht projekti.
- Kui kihti ei ole, luuakse see olemasolevasse GeoPackage'i.
- Teisi failis olevaid kihte ei kirjutata üle.

### Eraldiseisva GeoPackage'i loomine

Selle valikuga määrad uue `.gpkg` faili asukoha. Kui valitud fail on juba olemas, küsib Kavitro luba selle ülekirjutamiseks.

**Oluline:** ülekirjutamise kinnitamisel eemaldatakse kogu olemasolev GeoPackage-fail koos kõigi selles olevate kihtidega. Seda valikut ei tohi kasutada mitut vajalikku kihti sisaldava GeoPackage'i puhul.

### Loodava ajutise kihi struktuur

Kavitro loob polügoonkihi viitekihi koordinaatsüsteemis järgmiste väljadega:

| Väli | Tüüp |
|---|---|
| `ext_project_id` | Tekst |
| `ext_system` | Tekst |
| `ext_project_name` | Tekst |
| `ext_project_number` | Tekst |
| `detailed` | Tekst |
| `active` | Tõeväärtus |
| `added_by` | Tekst |
| `added_date` | Kuupäev ja kellaaeg |
| `updated_by` | Tekst |
| `update_date` | Kuupäev ja kellaaeg |

Loodud kiht on tühi. Olemasolevad projektid saab sinna kanda Geospatiali mapperiga, mida kirjeldab juhend [Geospatiali kihtide vastendamine](06_geospatiali_kihtide_vastendamine.md).

## Geospatiali režiim

Geospatiali režiimis kuvatakse projektide kaardil nii Geospatiali mapper kui ka ajutise projektikihi abiline. Ajutise kihi saab esmalt luua sihtkihiks ning seejärel kanda sinna olemasoleva kihi andmed.

Projektide puhul kasutab mapper olemasolevate objektide uuendamiseks välja `ext_project_id`. Ilma selle väljata või tühjade väärtuste korral lisatakse objektid uutena.

## Lähtestamine

Projektide kaardi **Lähtesta** nupp eemaldab kohe:

- projektide põhikihi viite;
- eelistatud staatused;
- eelistatud tunnused;
- „Alustamata“ staatused;
- lähte- ja sihtkausta väärtused;
- kausta nimetamise reegli.

Lähtestamine ei kustuta juba loodud projektikaustu, GeoPackage-faile ega nende kihte.

## Levinumad olukorrad

### Projektide moodul suunab seadistustesse

Kontrolli põhikihti, eelistatud staatuseid, eelistatud tunnuseid ja „Alustamata“ staatuseid. Vajuta pärast valikuid **Kinnita**.

### Kausta genereerimine suunab seadistustesse

Kontrolli lisaks põhiseadetele ka lähtekausta, sihtkausta ja nime reeglit. Kõik kolm peavad olema salvestatud.

### Kausta nimi ei vasta dialoogis valitud reeglile

Praeguses versioonis ei pruugi nime reegel rakenduda, kui varasem lubamise seadistus ei ole kasutaja profiilis aktiivne. Sel juhul kasutatakse projektinumbri ja projektinime vaikereeglit.

### Sihtkaust on juba olemas

Kavitro ei kirjuta sama nimega kausta üle. Kontrolli, kas kaust kuulub samale projektile, ning muuda vajaduse korral nime reeglit või korrasta sihtkaust käsitsi.

### Ajutise kihi abiline ei leia viitekihti

Vali projektide kaardil kehtiv viitekiht või seadista kinnistute põhikiht. Viitekihti on vaja uue projektikihi koordinaatsüsteemi määramiseks.

### Olemasoleva GeoPackage'i valik ei tööta

Viitekiht ei pärine GeoPackage'ist. Kasuta `.gpkg`-põhist viitekihti või vali eraldiseisva GeoPackage'i loomine.

## Kontrollnimekiri

Pärast projektide mooduli seadistamist kontrolli, et:

- valitud on õige projektide põhikiht;
- eelistatud staatused ja tunnused on määratud;
- „Alustamata“ staatused vastavad projekti tahvli tööloogikale;
- lähtekaust sisaldab ainult soovitud mallifaile;
- sihtkaust on õige ja kirjutatav;
- kaustanime eelvaade on arusaadav;
- loodud ajutise kihi CRS ja väljad on õiged;
- olemasoleva GeoPackage'i ülekirjutamist ei kinnitatud ekslikult;
- kõik ootel seadistusmuudatused on kinnitatud.
