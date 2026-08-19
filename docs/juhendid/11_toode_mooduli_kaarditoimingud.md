# Tööde mooduli kaarditoimingud

Tööde moodulis saab luua Kavitro töö otse kaardipunktist, lisada olemasolevale tööle kaardiobjekti, siduda varem QGIS-i kihile joonistatud punkti uue Kavitro tööga ning muuta seotud töö asukohta. Seadistatud tööde kihi geomeetriat ja osa Kavitro andmeid sünkroonitakse kindlatel tingimustel.

Põhikihi ja mooduli eelistuste ettevalmistamist kirjeldab juhend [Tööde ja teostusjooniste mooduli seadistamine](09_toode_ja_teostusjooniste_seadistamine.md). Põhiakna, üldotsingu ja korduvate kirjekaarditoimingute ülevaade on juhendis [Kavitro põhiaken, otsing ja ühised töövõtted](17_kavitro_pohiaken_otsing_ja_uhised_toovotted.md).

## Eeltingimused

Enne kaarditoimingute kasutamist veendu, et:

- tööde moodul on kasutajale lubatud;
- tööde põhikiht on seadistatud ja QGIS-i projekti laaditud;
- põhikiht on kirjutatav punktikiht;
- kihil on väli `ext_job_id`;
- kinnistu automaatseks tuvastamiseks on seadistatud kinnistute põhikiht;
- eelistatud tööliigid sisaldavad liike, mida soovid luua ja tööde loendis näha;
- Kavitro sessioon ja internetiühendus on aktiivsed.

Kihi täpne struktuur ja ajutise tööde kihi loomine on kirjeldatud seadistusjuhendis.

## Kaarditoimingute ülevaade

| Toiming | Kust käivitada | Tulemus |
|---|---|---|
| **Lisa uus töö** | Tööde mooduli tööriistariba või kaardi ujuv tööriistariba | Loob Kavitro töö ja sellele uue punkti |
| **Lisa punkt kaardile** | Olemasoleva töö kaardi **Rohkem toiminguid** | Lisab juba olemasoleva Kavitro töö punktina põhikihile |
| **Kontrolli sidumata GIS töid** | Kaardi ujuv tööriistariba | Loob olemasolevast sidumata kihipunktist uue Kavitro töö |
| **Muuda asukohta** | Olemasoleva töö kaardi **Rohkem toiminguid** | Muudab seotud punkti geomeetriat |
| **Näita kirjeid kaardil** | Töö kaardi kaardinupp | Suumib seotud kinnistutele ja töö punktile |
| **Mis see on** | Kaardi ujuv tööriistariba | Avab klikitud tööpunktile vastava Kavitro kirje |

Kaardi ujuva tööriistariba nähtavus sõltub kasutaja tööriistade seadest **Sisestuspaan**. Kui paan ei ole nähtav, saab uut tööd luua ka tööde mooduli nupuga ning kirjepõhised toimingud asuvad töö kaardil. Paani sisselülitamist kirjeldab juhend [Kasutaja eelistuste seadistamine](02_kasutaja_eelistuste_seadistamine.md).

## Uue töö loomine kaardipunktist

### Asukoha valimine

1. Ava moodul **Tööd**.
2. Vajuta **Lisa uus töö**.
3. Kavitro aktiveerib kaardil ristkursori ja viib plugina akna kaardivaliku režiimi.
4. Kliki hiire vasaku nupuga töö soovitud asukohal.
5. Valiku katkestamiseks vajuta `Esc` või hiire paremat nuppu.

Kavitro otsib klikitud asukohast seadistatud kinnistute põhikihi objekti. Kui objekt leitakse, kuvatakse loomise vormil selle katastritunnus ja aadressiinfo. Kinnistu puudumine ei takista töö loomist.

### Töö vormi täitmine

Vorm **Loo töö** kuvab valitud koordinaadid ja leitud kinnistu ning võimaldab määrata:

- töö liigi;
- pealkirja;
- vastutaja;
- staatuse;
- prioriteedi;
- lühikirjelduse.

Töö liik ja pealkiri on kohustuslikud. Kui kasutaja ei ole pealkirja käsitsi muutnud, pakub Kavitro pealkirjaks leitud kinnistu info ja valitud tööliigi kombinatsiooni.

Loomise vormil kuvatavad tööliigid piiratakse seadistustes valitud **Eelistatud liikidega**. Kui sobivat liiki ei kuvata või nupp **Lisa uus töö** on vormil keelatud, lisa vajalik liik tööde seadistuskaardile ja kinnita muudatus.

Vastutajate, staatuste ja prioriteetide valikud laaditakse Kavitro teenusest. Vastutaja ja staatuse vaikeväärtus võetakse võimaluse korral kasutaja ning mooduli taustaseadetest.

### Salvestamise järjekord

Pärast vormi kinnitamist teeb Kavitro toimingud järgmises järjekorras:

1. loob Kavitro teenuses töö;
2. määrab töö alguskuupäevaks jooksva päeva ja tähtajaks seitsmenda päeva pärast loomist;
3. salvestab valitud punkti töö geomeetriaks Kavitro teenuses;
4. lisab sama punkti QGIS-i tööde põhikihile;
5. kirjutab kihile töö ID, nime, liigi, staatuse ja muud sünkroonimisväljad;
6. seob leitud kinnistu Kavitro tööga, kui kinnistul on kasutatav katastritunnus;
7. värskendab tööde loendit.

Lühikirjeldus salvestatakse Kavitro töö kirjeldusse. Punkti asukoht salvestatakse eraldi geomeetriana.

### Osaliselt õnnestunud loomine

Kavitro töö luuakse enne QGIS-i kihiobjekti ja kinnistuseose salvestamist. Seetõttu võib veateade tähendada, et:

- töö on Kavitro teenuses olemas, kuid punkt jäi tööde kihile lisamata;
- töö ja punkt on olemas, kuid kinnistuseos jäi loomata.

Sellisel juhul ära vajuta kohe uuesti **Lisa uus töö**, sest see looks teise Kavitro töö. Leia esmalt loodud töö loendist või brauserist. Puuduva punkti saad lisada toiminguga **Lisa punkt kaardile** ja kinnistu seostada toiminguga **Seosta kinnistuid**.

## Olemasolevale tööle punkti lisamine

Kasuta seda toimingut, kui Kavitro töö on juba olemas, kuid tööde põhikihis ei ole sama `ext_job_id` väärtusega punkti.

1. Leia töö tööde mooduli loendist.
2. Ava töö kaardil **Rohkem toiminguid**.
3. Vali **Lisa punkt kaardile**.
4. Kliki kaardil punkti soovitud asukohal.
5. Katkestamiseks vajuta `Esc` või hiire paremat nuppu.

Kavitro laadib töö värsked andmed, lisab põhikihile punkti, kirjutab sellele töö andmed ja saadab geomeetria Kavitro teenusesse. Klikitud asukohast leitud kinnistu seotakse võimaluse korral tööga.

Kui sama töö ID-ga punkt on kihil juba olemas, uut punkti ei lisata. Kavitro valib olemasoleva punkti ja suumib sellele.

Kui punkti kihile salvestamine õnnestub, kuid geomeetria saatmine Kavitro teenusesse ebaõnnestub, ei kuvata praeguses versioonis eraldi geomeetria sünkroonimise veateadet. Olulise töö korral kontrolli asukohta ka Kavitro veebivaates.

## Sidumata GIS-tööde kontroll

Sidumata GIS-töö on tööde põhikihi punkt, millel:

- puudub `ext_job_id` väärtus;
- puudub `ext_system` väärtus;
- on olemas mittetühi geomeetria.

Kui väljal `ext_system` on juba väärtus, ei käsitleta objekti sidumata uue GIS-tööna ka siis, kui `ext_job_id` on tühi.

### Sidumata punkti sidumine

1. Vajuta kaardi ujuval tööriistaribal **Kontrolli sidumata GIS töid**.
2. Oota, kuni Kavitro kontrollib tööde põhikihi objektid.
3. Dialoogis **Sidumata GIS tööd** vali soovitud rida.
4. Tee real topeltklikk või vajuta **Ava valitud**.
5. Kontrolli eeltäidetud töö liiki, staatust ja pealkirja.
6. Täida vastutaja, prioriteet ja kirjeldus.
7. Vajuta **Lisa uus töö**.

Dialoog kuvab objekti FID-i, pealkirja, liigi, staatuse ja muutmise aja. Puuduva pealkirja asemel kasutatakse ajutist nime kujul `GIS feature <FID>`.

Pärast kinnitamist loob Kavitro uue töö ning kirjutab selle ID ja värsked andmed samale olemasolevale kihipunktile. Uut geomeetriat kihile ei lisata.

Ka selles töövoos luuakse Kavitro töö enne olemasoleva kihiobjekti uuendamist. Kui kihiobjekti uuendamine ebaõnnestub, võib uus töö Kavitros siiski alles jääda.

## Töö asukoha muutmine

1. Leia töö tööde mooduli loendist.
2. Ava **Rohkem toiminguid**.
3. Vali **Muuda asukohta**.
4. Kavitro valib seotud tööpunkti ja suumib sellele.
5. Kliki kaardil uus asukoht.
6. Katkestamiseks vajuta `Esc` või hiire paremat nuppu.

Toiming muudab põhikihi punkti ja kinnitab kihi redigeerimisseansi. Kui tööde mooduli sünkroonimisteenus on kihiga ühendatud, saadetakse kinnitatud geomeetriamuudatus ka Kavitro teenusesse.

**Oluline:** kui tööde kiht oli enne toimingut juba redigeerimisrežiimis, kinnitab **Muuda asukohta** kogu selle kihi redigeerimisseansi. Salvesta või tühista enne ümberpaigutamist kõik muud ootel muudatused.

Edukas teade kinnitab eelkõige QGIS-i kihi geomeetria salvestamist. Taustas toimuva Kavitro geomeetriauuenduse viga logitakse, kuid kasutajale ei pruugita selle kohta eraldi hoiatust kuvada. Kontrolli olulise muudatuse tulemust veebivaates.

## Töö näitamine kaardil

Töö kaardi nupp **Näita kirjeid kaardil** teeb kaks eraldi toimingut:

1. kuvab ja valib tööga seotud kinnistud;
2. otsib tööde põhikihilt sama ID-ga punkti ning valib ja suumib sellele.

Tööpunkti otsitakse eelisjärjekorras väljadelt `ext_works_id`, `ext_job_id`, `ext_id` ja `external_id`. Tavapärases tööde kihis kasutatakse välja `ext_job_id`.

Kui seotud kinnistud kuvatakse, kuid tööpunktile ei suumita, kontrolli põhikihti ja tööpunkti `ext_job_id` väärtust.

## Kaardipunktist töö avamine

Toiming **Mis see on** võimaldab avada töö otse kaardilt.

1. Ava moodul **Tööd**.
2. Vajuta kaardi ujuval tööriistaribal **Mis see on**.
3. Kliki tööde põhikihi punktile.
4. Kavitro loeb objekti ID-välja ja avab vastava töö kirje.

Kui klikitud objektil puudub kasutatav ID või väärtus on tühi, ei saa Kavitro kirjet avada. Parema hiirenupu või `Esc`-klahviga saab tuvastamise katkestada.

## Kinnistute seostamine

Toiming **Seosta kinnistuid** asub töö kaardi menüüs **Rohkem toiminguid**. Selle abil saab valida kinnistute põhikihilt ühe või mitu objekti, vaadata valiku enne salvestamist üle ning saata seosed Kavitro teenusesse.

See toiming ei muuda tööpunkti asukohta. Uue töö loomisel leitud kinnistu automaatne seostamine ja hilisem käsitsi seostamine kasutavad sama Kavitro kinnistuseost, kuid on eraldi töövood.

Toiming ainult lisab seoseid. Valimata jätmine ei eemalda varasemaid seoseid ning **Kinnita** ei asenda olemasolevat seoseloendit.

## Kavitro andmete sünkroonimine tööde kihile

Tööde loendi või filtrite värskendamisel kontrollib Kavitro põhikihi objekte, millel on `ext_job_id`, ning laadib nende tööde värsked andmed teenusest.

Olemasolevale kihipunktile võidakse uuendada:

- geomeetria;
- töö nimi;
- liik ja staatus;
- aktiivsuse väärtus;
- detailne staatuseinfo;
- algus- ja lõppkuupäev;
- loomise ja muutmise aeg.

Sünkroonimine ei lisa kihile Kavitro töid, millele punkt veel puudub. Nende jaoks kasuta toimingut **Lisa punkt kaardile**.

Kui tööde kiht on redigeerimisrežiimis, jäetakse taustast kihile sünkroonimine vahele, et mitte kirjutada ootel muudatustele peale. Lõpeta redigeerimine ja värskenda tööde loendit uuesti.

Kui kihil on mitu sama `ext_job_id` väärtusega punkti, ei saa Kavitro neid ühe töö eri objektidena eristada. Hoia töö ID põhikihis unikaalne.

## QGIS-i muudatuste saatmine Kavitrosse

Tööde mooduli aktiivsuse ajal kuulab Kavitro põhikihi kinnitatud geomeetriamuudatusi. Kui seotud punkti geomeetria QGIS-is muudetakse ja muudatus kinnitatakse, saadetakse uus geomeetria sama `ext_job_id` tööle Kavitro teenusesse.

Praeguse versiooni piirid:

- Kavitrosse saadetakse automaatselt geomeetria, mitte käsitsi muudetud atribuudid;
- muudatus peab olema QGIS-is kinnitatud;
- tööde moodul ja selle sünkroonimisteenus peavad muudatuse kinnitamise ajal aktiivsed olema;
- sünkroonimisvea korral jääb QGIS-i kinnitatud muudatus alles ning kasutajale ei pruugita eraldi hoiatust kuvada;
- kui muudatus tehti ajal, mil sünkroonimisteenus ei kuulanud kihti, võib järgmine taustast sünkroonimine kohaliku geomeetria taas üle kirjutada.

Kõige turvalisem on muuta töö geomeetriat töö kaardi toiminguga **Muuda asukohta** ning kontrollida olulist tulemust ka veebivaates.

## Kihi skeemi automaatne kontroll

Tööde põhikihi avamisel kontrollib Kavitro nõutud sünkroonimisvälju. `ext_job_id` peab kihil juba olemas olema. Teised puuduvad standardväljad proovitakse kirjutatavale kihile automaatselt lisada.

Olemasolevate väljade tüüpe võrreldakse oodatud skeemiga. Täisarvulise välja asemel lubatakse ka tekstivälja, kuid tõeväärtuse ja kuupäevaväljade tüübid peavad vastama. Sobimatu skeemi korral palub Kavitro valida või luua sobiva tööde kihi.

## Levinumad olukorrad

### Uue töö vormil ei ole ühtegi liiki

Kontrolli tööde seadistuskaardi **Eelistatud liikide** valikut. See valik määrab tööde mooduli liigipiirkonna ja uue töö vormil lubatud liigid.

### Töö loodi, kuid punkti ei ole kaardil

Ära loo tööd uuesti. Leia olemasolev töö ja vali **Rohkem toiminguid** → **Lisa punkt kaardile**.

### Punkt lisati, kuid kinnistu jäi sidumata

Leia töö ja vali **Rohkem toiminguid** → **Seosta kinnistuid**. Kontrolli ka, et kinnistute põhikihil oleks väli `tunnus` täidetud.

### Sidumata GIS-punkti loendis ei kuvata

Kontrolli, et objektil on geomeetria ning väljad `ext_job_id` ja `ext_system` on mõlemad tühjad. Seejärel käivita kontroll uuesti.

### Kavitro andmed ei uuene tööde kihile

Lõpeta tööde kihi redigeerimisseanss ja värskenda tööde loendit või filtreid. Kontrolli ka `ext_job_id` väärtust ja internetiühendust.

### Käsitsi muudetud kihiatribuut ei jõudnud Kavitrosse

See on praeguses versioonis ootuspärane. Automaatne kihilt Kavitrosse sünkroonimine saadab geomeetriamuudatusi, mitte vabalt muudetud atribuute.

## Kontrollnimekiri

Pärast tööde kaarditoimingu kasutamist kontrolli, et:

- Kavitro töö ID ja kihi `ext_job_id` kattuvad;
- ühe töö ID-ga on kihil ainult üks punkt;
- punkt asub õiges kohas;
- töö nimi, liik ja staatus vastavad Kavitro kirjele;
- vajalik kinnistu on tööga seotud;
- osalise veateate korral ei loodud kogemata teist tööd;
- olulise geomeetriamuudatuse tulemus on kontrollitud ka veebivaates;
- tööde kihile ei jäänud soovimatuid ootel redigeerimisi.
