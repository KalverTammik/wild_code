# Teostusjooniste mooduli kasutamine

Teostusjooniste moodulis saab filtreerida ja avada Kavitro teostusjooniste kirjeid, joonistada kirjega seotud QGIS-i kaardiobjekti, lisada struktureeritud märkmeid ning seostada kirje kinnistutega.

Põhikihi, väljade ja eelistuste seadistamist kirjeldab juhend [Tööde ja teostusjooniste mooduli seadistamine](09_toode_ja_teostusjooniste_seadistamine.md). Põhiakna, üldotsingu ja korduvate kirjekaarditoimingute ülevaade on juhendis [Kavitro põhiaken, otsing ja ühised töövõtted](17_kavitro_pohiaken_otsing_ja_uhised_toovotted.md).

## Eeltingimused

Enne kaarditoimingute kasutamist veendu, et:

- teostusjooniste moodul on kasutajale lubatud;
- teostusjooniste põhikiht on seadistatud ja QGIS-i projekti laaditud;
- kiht on kirjutatav vektorkiht;
- kihi geomeetriatüüp vastab teie töökorraldusele;
- vajalikud teostusjoonise vormiväljad on kihile eelnevalt lisatud;
- Kavitro sessioon ja internetiühendus on aktiivsed.

Enne uue seotud objekti joonistamist lõpeta soovitatavalt põhikihi varasem redigeerimisseanss. Redigeerimisseansi täpne mõju on kirjeldatud allpool.

## Mooduli loend ja filtrid

Teostusjooniste moodul kasutab staatuse- ja liigifiltrit. Seadistustes valitud eelistatud väärtused laaditakse filtrite algvalikuteks.

Eelistatud liigid määravad lisaks mooduli liigipiirkonna: teostusjooniste loendisse küsitakse ainult nende liikidega kirjeid ning liigifiltri valik toimib selle piirkonna sees. Kui vajalik teostusjoonis loendist puudub, kontrolli esmalt seadistuskaardi **Eelistatud liike**.

Filtrite muutmisel laaditakse vastavad kirjed Kavitro teenusest uuesti. Filtrite valikud ei pärine QGIS-i põhikihi atribuutidest.

## Teostusjoonise kaardi toimingud

Kirje kaardil võivad olla järgmised nupud ja toimingud:

- **Ava kirje brauseris** – avab sama kirje Kavitro veebivaates;
- **Näita kirjeid kaardil** – kuvab seotud kinnistud ja suumib seotud teostusjoonise objektile;
- **Rohkem toiminguid** → **Lisa/uuenda märkmeid**;
- **Rohkem toiminguid** → **Joonista uus seotud objekt kaardile**;
- **Rohkem toiminguid** → **Seosta kinnistuid**.

## Uue seotud objekti joonistamine

### Töövoo käivitamine

1. Leia teostusjoonis mooduli loendist.
2. Ava kirje **Rohkem toiminguid**.
3. Vali **Joonista uus seotud objekt kaardile**.
4. Kavitro kontrollib põhikihti ja lisab vajaduse korral standardsed sidumisväljad.
5. Põhikiht tehakse nähtavaks ja aktiivseks.
6. Käivitub QGIS-i tavapärane **Lisa objekt** tööriist.
7. Joonista punkt, joon või polügoon vastavalt põhikihi geomeetriatüübile.
8. Lõpeta geomeetria QGIS-i tavapärasel viisil.

Kavitro peidab selle töövoo ajal QGIS-i tavapärase atribuudivormi, sest vajalikud andmed küsitakse eraldi teostusjoonise vormil.

### Teostusjoonise andmevorm

Pärast geomeetria loomist avaneb vorm **Teostusjoonise andmed**. Vormil saab määrata:

- töö numbri;
- objekti nime;
- mõõdistamise kuupäeva;
- mõõdistaja ja kontakti;
- joonise liigi – **Teostusjoonis** või **Geoalus**;
- mõõtkava – `1:500` või `1:1000`;
- koordinaatsüsteemi – **L-EST97** või **Tartu kohalik**;
- kõrgussüsteemi **EH2000**;
- võrgu liigid;
- mõõdistaja märkused.

Töö numbri vaikeväärtus võetakse võimaluse korral kirje numbrist ja selle puudumisel kirje ID-st. Objekti vaikeväärtus võetakse kirje nimest.

Vormi **Katkesta** jätab sidumise lõpetamata. Selle mõju äsja joonistatud objektile sõltub sellest, kes alustas kihi redigeerimisseansi.

### Andmete salvestamine

Vormi **Salvesta** järel:

1. kirjutatakse kaardiobjektile teostusjoonise Kavitro ID ja muud standardsed sidumisväljad;
2. kirjutatakse olemasolevatele valdkonnaväljadele vormi väärtused;
3. kontrollitakse, et loodud objekt on põhikihilt sama ID järgi leitav;
4. saadetakse objekti geomeetria Kavitro teenusesse;
5. Kavitro enda alustatud redigeerimisseanss kinnitatakse;
6. loodud objekt valitakse ja sellele suumitakse.

Automaatselt loodavate sidumisväljade ja eelnevalt vajalike valdkonnaväljade täielik loend on seadistusjuhendis.

Kui kihil puudub mõni vormile vastav valdkonnaväli, jäetakse ainult selle välja väärtus kihile kirjutamata. Sidumisväljad lisatakse eraldi automaatselt.

## Redigeerimisseansi käitumine

Joonistamise tulemus sõltub sellest, kas teostusjooniste põhikiht oli toimingu käivitamisel juba redigeerimisrežiimis.

### Kiht ei olnud redigeerimisrežiimis

Kavitro alustab redigeerimisseansi ise.

- Eduka sidumise ja geomeetria saatmise järel kinnitab Kavitro muudatused.
- Vormi katkestamisel, sidumise vea või geomeetria saatmise vea korral pöörab Kavitro enda alustatud seansi tagasi.
- Tagasipööramisel eemaldatakse ka äsja joonistatud sidumata objekt.

See on soovitatav ja kõige terviklikum töövoog.

### Kiht oli juba redigeerimisrežiimis

Kavitro kasutab olemasolevat redigeerimisseanssi ega kinnita või pööra seda automaatselt tagasi.

- Eduka toimingu järel jäävad uus objekt ja selle atribuudid QGIS-is ootele, kuni kasutaja need kinnitab.
- Vormi katkestamisel või vea korral võib äsja joonistatud sidumata objekt jääda redigeerimispuhvrisse.
- Geomeetria võidakse eduka töövoo käigus Kavitro teenusesse saata enne seda, kui kasutaja QGIS-i muudatused kinnitab.
- Hilisem QGIS-i muudatuste tagasipööramine võib seetõttu jätta Kavitro geomeetria ja kohaliku kihi omavahel vastuollu.

Lõpeta enne toimingu käivitamist põhikihi muud varasemad redigeerimised. Nii saab Kavitro kogu sidumistoimingu õnnestumise või vea korral tervikuna kinnitada või tagasi pöörata.

## Osaliselt ebaõnnestunud joonistamine

Kui kuvatakse teade, et kaardiobjekti sidumine või geomeetria saatmine ebaõnnestus:

1. kontrolli, kas põhikiht oli juba redigeerimisrežiimis;
2. vaata, kas kihile jäi uus objekt;
3. kontrolli selle `ext_job_id` väärtust;
4. kontrolli Kavitro veebivaatest, kas geomeetria jõudis kirjele;
5. ära käivita kohe uut joonistamist enne, kui esimese katse seis on selge.

Korduv toiming võib põhjustada sama `ext_job_id` väärtusega mitu objekti. Sidumise kontroll eeldab, et üks Kavitro teostusjoonis vastab ühele üheselt leitavale kihiobjektile.

## Hilisem geomeetria muutmine

Praeguses versioonis ei ole teostusjooniste moodulil tööde mooduliga võrreldavat kihi geomeetriamuudatuste kuulajat ega eraldi toimingut **Muuda asukohta**.

Seetõttu ei saadeta pärast esmast sidumist QGIS-is käsitsi tehtud ja kinnitatud geomeetriamuudatusi automaatselt Kavitro teenusesse. Samuti ei ole **Joonista uus seotud objekt kaardile** mõeldud olemasoleva geomeetria tavapäraseks redigeerimiseks.

Kui seotud geomeetriat on vaja muuta, kontrolli enne töökorraldust Kavitro veebivaates või lepi kokku eraldi andmeparanduse protsess. Ära loo sama kirje jaoks kontrollimatult uut objekti.

## Teostusjoonise näitamine kaardil

Nupp **Näita kirjeid kaardil**:

1. kuvab teostusjoonisega seotud kinnistud;
2. otsib põhikihilt kirje ID-ga objekti;
3. teeb kihi nähtavaks ning valib ja suumib leitud objektile.

Objekti otsimisel proovitakse välju `ext_asbuilt_id`, `ext_job_id`, `ext_id` ja `external_id`. Automaatselt loodud teostusjooniste kihil kasutatakse välja `ext_job_id`.

Kui seotud kinnistud kuvatakse, kuid teostusjoonise objektile ei suumita, kontrolli põhikihti ja `ext_job_id` väärtust.

## Kaardiobjektist kirje avamine

Kaardi ujuva tööriistariba toiming **Mis see on** toetab teostusjooniste moodulit.

1. Ava moodul **Teostusjoonised**.
2. Vajuta **Mis see on**.
3. Kliki teostusjooniste põhikihi objektil.
4. Kavitro valib objekti ja avab selle ID-le vastava kirje.

Punktobjekti korral tuleb klikkida punkti lähedale; joone või polügooni korral otse geomeetriale. Tuvastamise katkestamiseks vajuta `Esc` või hiire paremat nuppu.

## Märkmete lisamine ja uuendamine

### Märkmete dialoogi avamine

1. Leia teostusjoonis mooduli loendist.
2. Ava **Rohkem toiminguid**.
3. Vali **Lisa/uuenda märkmeid**.

Kavitro laadib kirje kirjelduse teenusest ja otsib sellest struktureeritud jaotist **Märkused ja kommentaarid**. Varem sama tööriistaga salvestatud märkmed kuvatakse kuupäevade järgi rühmitatuna.

Kui struktureeritud märkmeid ei ole, lisatakse vormile automaatselt üks tühi tänase kuupäevaga rida. Kirjeldusse vabatekstina kirjutatud märkusi ei teisendata automaatselt märkmeridadeks.

### Märkmerea väljad

Igal real on:

- märkuse tekst;
- märkeruut **Lahendatud**;
- lahendamise kuupäev;
- nupp rea kustutamiseks.

Kui märgid rea lahendatuks ja kuupäev on tühi, täidab Kavitro kuupäeva tänase kuupäevaga kujul `pp.kk.aaaa`. Märke eemaldamisel tühjendatakse lahendamise kuupäev.

Lahendamise kuupäev on vabalt sisestatav tekstiväli. Praeguses versioonis ei kontrollita, kas kasutaja sisestatud kuupäev vastab etteantud vormingule.

### Uue märkuse lisamine ja rea kustutamine

- **Lisa märkus** lisab uue rea tänase kuupäeva rühma.
- Rea **Kustuta** eemaldab rea dialoogist kohe, kuid muudatus jõuab Kavitro teenusesse alles nupu **Salvesta** järel.
- Kustutamisel eraldi kinnitusküsimust ei esitata.
- **Katkesta** sulgeb dialoogi ilma muudatusi teenusesse saatmata.

Tühi rida, millel pole märkuse teksti, lahendamise märget ega lahendamise kuupäeva, jäetakse salvestamisel välja. Kõigi märkmeridade kustutamisel eemaldatakse kirjeldusest struktureeritud märkmete jaotis.

### Kirjelduse säilitamine

Enne märkmete salvestamist laadib Kavitro kirje kirjelduse uuesti ning asendab selles ainult struktureeritud märkmete jaotise. Kirjelduse muu sisu püütakse säilitada ka siis, kui see muutus pärast dialoogi avamist.

Märkmed salvestatakse Kavitro kirje `description` väärtusesse HTML-tabelina. Neid ei kirjutata teostusjooniste QGIS-i põhikihi atribuutidesse.

## Kinnistute seostamine

Toiming **Seosta kinnistuid** võimaldab valida kinnistute põhikihilt ühe või mitu kinnistut, kontrollida valiku ülevaatedialoogis ning salvestada seosed Kavitro teostusjoonisele.

Kinnistuseos on teostusjoonise geomeetriast eraldi. Kaardiobjekti joonistamine ei otsi ega seo kinnistut automaatselt.

Toiming ainult lisab seoseid. Valimata jätmine ei eemalda varasemaid seoseid ning **Kinnita** ei asenda olemasolevat seoseloendit.

## Levinumad olukorrad

### Teostusjoonist ei kuvata loendis

Kontrolli staatuse- ja liigifiltrit ning seadistustes valitud eelistatud liike. Eelistatud liigid piiravad mooduli liigipiirkonda.

### Joonistamise toiming ei käivitu

Kontrolli, et põhikiht on projektis olemas, kehtiv ja kirjutatav. Andmeallikas peab võimaldama puuduvate sidumisväljade lisamist.

### Vormiväärtus ei jõudnud kihile

Kontrolli, et põhikihis on täpselt sama nimega valdkonnaväli. Kavitro loob automaatselt sidumisväljad, kuid mitte kõiki teostusjoonise vormi välju.

### Katkestatud joonistamisest jäi objekt kihile

Põhikiht oli enne toimingut tõenäoliselt juba redigeerimisrežiimis. Kustuta soovimatu objekt redigeerimispuhvrist või pööra muudatused kontrollitult tagasi.

### Käsitsi muudetud geomeetria ei jõudnud Kavitrosse

See on praeguses versioonis ootuspärane. Automaatne geomeetria saatmine toimub uue objekti sidumise töövoos, mitte hilisemal tavalisel QGIS-i redigeerimisel.

### Olemasolevad märkused ei ilmu dialoogi

Dialoog loeb ainult Kavitro märkmetööriistaga loodud struktureeritud jaotist. Kirjelduse muu vabatekst jääb alles, kuid seda ei kuvata märkmeridadena.

### Märkmete salvestamine ebaõnnestus

Kontrolli internetiühendust ja Kavitro sessiooni. Ebaõnnestumise korral jääb kirje varasem kirjeldus teenuses alles.

## Kontrollnimekiri

Pärast teostusjoonise toimingut kontrolli, et:

- kirje on õiges staatuse- ja liigifiltris nähtav;
- loodud kihiobjektil on õige `ext_job_id`;
- ühe kirje ID-ga ei ole kihil mitu objekti;
- geomeetria ja vormiväljad salvestati soovitud kujul;
- QGIS-i kihile ei jäänud soovimatuid ootel muudatusi;
- Kavitro veebivaates on õige geomeetria;
- märkmete muu kirjeldussisu jäi alles;
- vajalikud kinnistud on kirjega seotud.
