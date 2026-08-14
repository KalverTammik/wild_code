# Kavitro seadistuste mooduli kasutamine

Kavitro seadistuste moodulis saab määrata, kuidas plugin kasutab QGIS-i kihte, milline moodul avaneb vaikimisi ning milliseid tööriistu ja moodulipõhiseid eelistusi kasutatakse.

See juhend annab ülevaate seadistuste mooduli ülesehitusest, muudatuste salvestamisest ja seadete lähtestamisest. Üksikute moodulite täpsed seadistusjuhised avaldatakse eraldi juhendites.

## Eeltingimused

Enne seadistamist veendu, et:

- oled Kavitro pluginasse sisse logitud;
- avatud on õige QGIS-i projekt;
- vajalikud QGIS-i kihid on projekti laaditud;
- sinu kasutajakontol on seadistatavate moodulite kasutusõigus.

Kui kasutaja sessioon on aegunud, palub Kavitro enne seadistuste avamist uuesti sisse logida.

## Seadistuste avamine

1. Ava QGIS-is Kavitro plugina aken.
2. Vali plugina külgribalt **Seaded**.
3. Oota, kuni Kavitro laadib kasutaja andmed, õigused ja moodulite seadistuskaardid.

Kui mõne mooduli kohustuslik seadistus on puudu, võib Kavitro selle mooduli avamisel näidata hoiatust ja suunata kasutaja automaatselt vastava mooduli seadistuskaardile.

## Seadistuste mooduli ülesehitus

Seadistused on jagatud kaartideks. Kasutajale kuvatavad kaardid ja valikud sõltuvad tema õigustest ning kasutusel olevatest Kavitro moodulitest.

### Kasutaja

Kasutaja kaardil kuvatakse:

- kasutaja nimi;
- e-posti aadress;
- kasutajale määratud rollid;
- moodulid, millele kasutajal on juurdepääs;
- vaikimisi avatava mooduli valik;
- kaardil kuvatavate Kavitro tööriistade valikud.

Jaotis **Mooduli juurdepääs** ei anna kasutajale uusi õigusi ega eemalda olemasolevaid õigusi. Seal kuvatakse Kavitro teenusest saadud juurdepääsud ning saab valida ainult selle, milline lubatud moodul avaneb vaikimisi.

### QGIS projekti baaskihid

Sellel kaardil määratakse käesoleva QGIS-i projekti vee-, kanalisatsiooni- ja muud tehnovõrkude baaskihid. Võimalik on kasutada käsitsi seadistamist või EVEL-i kihistuse tuvastamist.

Baaskihtide täpne seadistamine on kirjeldatud eraldi juhendis **QGIS projekti baaskihtide seadistamine**.

### Moodulite seadistuskaardid

Igal kasutajale lubatud moodulil võib olla oma seadistuskaart. Sõltuvalt moodulist saab seal määrata:

- mooduli põhikihi;
- arhiivikihi;
- eelistatud staatused;
- eelistatud liigid;
- eelistatud tunnused;
- projekti ülevaate tahvli „Alustamata“ staatused;
- moodulipõhised lisaseaded.

Kui mõne mooduli kaarti ei kuvata, kontrolli esmalt kasutaja õigusi. Osa haldustoiminguid kuvatakse ainult vastava muutmis- või loomisõigusega kasutajale.

## Seadete muutmine ja salvestamine

Tavapärased seadistuste muudatused ei rakendu kohe.

1. Tee vajalik muudatus ühel või mitmel seadistuskaardil.
2. Muudatuse tuvastamisel ilmub seadistuste akna alla nupp **Kinnita**.
3. Kontrolli üle kõik muudetud kaardid.
4. Vajuta **Kinnita**.
5. Pärast edukat salvestamist kaob kinnitusriba.

Ühe kinnitamisega salvestatakse kõik seadistuste moodulis ootel olevad muudatused. Seetõttu tasub enne nupu vajutamist üle vaadata ka teised kaardid, mida sama külastuse ajal muudeti.

Nupuga **Kinnita** salvestatakse muu hulgas:

- vaikimisi avatav moodul;
- kaardi tööriistade nähtavus;
- QGIS projekti baaskihtide valikud;
- moodulite põhi- ja arhiivikihid;
- staatuste, liikide ja tunnuste eelistused;
- moodulipõhised kausta- ja kaardistusseaded.

## Kohe rakenduvad toimingud

Kõik seadistuste moodulis olevad tegevused ei ole ootel seadistusmuudatused. Andmeid või faile töötlevad nupud võivad toimingu teha kohe.

Kohe võivad rakenduda näiteks:

- seadistuskaardi lähtestamine;
- SHP-faili importimine;
- kinnistute lisamine, arhiveerimine või kustutamine;
- otsinguvälja loomine või parandamine;
- andmete ülekandmine ühest kihist teise;
- uue GeoPackage-faili või kihi loomine.

Nende toimingute tagasivõtmiseks ei piisa seadistuste aknast lahkumisel muudatuste hülgamisest. Enne andmeid muutva toimingu kinnitamist kontrolli alati valitud kihti, faili ja objektide arvu.

## Seadistustest lahkumine salvestamata muudatustega

Kui proovid seadistuste moodulist lahkuda enne muudatuste kinnitamist, kuvab Kavitro valiku:

- **Salvesta** – salvestab kõik ootel muudatused ja avab valitud mooduli;
- **Hülga** või **Discard** – taastab viimati salvestatud seadistused ja avab valitud mooduli;
- **Tühista** – jääb seadistuste moodulisse ning jätab muudatused ootele.

Muudatuste hülgamine mõjutab ainult veel salvestamata seadistusvalikuid. See ei võta tagasi juba tehtud andmehaldustoiminguid ega seadistuskaardi lähtestamist.

## Seadistuskaardi lähtestamine

Mooduli- ja baaskihtide kaartidel olev nupp **Lähtesta** eemaldab vastava kaardi salvestatud seadistused ning taastab vaikeoleku.

Lähtestamine võib eemaldada:

- valitud põhi- ja arhiivikihi viited;
- salvestatud staatuste, liikide ja tunnuste eelistused;
- „Alustamata“ staatuste valiku;
- moodulipõhised kausta- ja kaardistusseaded;
- projekti baaskihtide seosed.

**Oluline:** lähtestamine rakendub kohe. Seda ei saa tühistada seadistuste aknast lahkumisel valikuga **Hülga**.

Lähtestamine eemaldab Kavitro seadistused ja kihiviited, kuid ei kustuta QGIS-i kihte ega nende objekte. Andmeid kustutavad ainult eraldi andmehaldustoimingud, mille juures küsitakse kasutajalt vastav kinnitus.

## Millised seaded kehtivad projektile ja millised kasutajale?

Kavitro kasutab kahte seadistuste ulatust.

### QGIS-i projektiga seotud seaded

QGIS projekti baaskihtide valikud ja ühise kanalisatsioonikihi kaardistus salvestatakse avatud QGIS-i projekti. Teise projekti avamisel tuleb kasutada selle projekti enda baaskihtide seadistust.

### QGIS-i profiiliga seotud seaded

Kasutaja eelistused ja moodulite seadistuskaartide väärtused salvestatakse kasutatavasse QGIS-i profiili. Nende hulka kuuluvad näiteks vaikimisi avatav moodul, kaardi tööriistade nähtavus, moodulite kihiviited, filtrieelistused ja moodulipõhised lisaväärtused.

Kui avad teise QGIS-i projekti, milles varem valitud kihti ei ole, tuleb vastava mooduli kiht uuesti valida.

Kasutaja rollid ja moodulite kasutusõigused tulevad Kavitro teenusest ning neid ei saa seadistuste moodulis muuta.

## Levinumad olukorrad

### Mooduli seadistuskaarti ei kuvata

Tõenäoliselt puudub kasutajal selle mooduli kasutusõigus. Kontrolli kasutaja kaardil kuvatavaid rolle ja moodulite juurdepääse. Vajaduse korral pöördu Kavitro administraatori poole.

### Kihti ei saa valikust leida

Kontrolli, et:

- õige QGIS-i projekt on avatud;
- vajalik kiht on projekti laaditud;
- kiht on kehtiv ruumikiht;
- kihti ei ole projektist eemaldatud pärast seadistuste avamist.

### Nuppu „Kinnita“ ei kuvata

Nupp kuvatakse ainult siis, kui Kavitro tuvastab salvestamata seadistusmuudatuse. Kui kasutasid andmeid töötlevat tegevusnuppu, võis toiming rakenduda kohe ja eraldi kinnitamist ei ole vaja.

### Kavitro suunab mooduli asemel seadistustesse

Mooduli tööks vajalik põhikiht, arhiivikiht või mõni kohustuslik eelistus on määramata. Täida esile tõstetud mooduli seadistuskaart ja vajuta **Kinnita**.

### Muudatus ei rakendunud

Kontrolli, kas vajutasid pärast valiku tegemist nuppu **Kinnita**. Kui valitud kiht on QGIS-i projektist eemaldatud või teise projektiga asendatud, vali kehtiv kiht uuesti.

## Soovitatav seadistamise järjekord

Uue QGIS-i projekti või QGIS-i profiili seadistamisel kasuta järgmist järjekorda:

1. Kontrolli kasutaja nime, rolle ja moodulite juurdepääse.
2. Vali soovi korral vaikimisi avatav moodul ja kaardi tööriistad.
3. Seadista QGIS projekti baaskihid.
4. Määra iga kasutatava mooduli põhi- ja vajaduse korral arhiivikiht.
5. Vali moodulite eelistatud staatused, liigid ja tunnused.
6. Määra projekti tahvli „Alustamata“ staatused.
7. Täida moodulipõhised lisaseaded.
8. Kontrolli tehtud valikud üle ja vajuta **Kinnita**.

Pärast salvestamist ava soovitud moodul ja kontrolli, et Kavitro leiab seadistatud kihid ning kuvab mooduli tööriistad ootuspäraselt.
