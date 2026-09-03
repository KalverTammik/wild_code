# Projektide nuppude detailaudit

See juhend kirjeldab Visuaali projektinuppude tegelikku käitumist praeguse koodibaasi järgi. Kaetud on projektikaardi detailtahvel, kausta- ja veebitoimingud, kaardifookus, projektikausta genereerimine, kinnistuseoste lisamine, projektiala käsitsi joonistamine ning seotud kinnistutest ala eelvaate loomine.

Filtrite, tähtajanuppude ja kirjekaardi üldise ülesehituse detailid on failis [Filtrite nuppude detailaudit](02_01_filtrite_nuppude_detailaudit.md).

## Mõju lühikaart

| Nupp või nupurühm | Peamine mõju | Kas toiming on tagasi võetav? |
|---|---|---|
| **… Detailne ülevaade** | Loeb Kavitrost seotud kirjeid ja kuvab need projektikaardil | Püsiandmeid ei muudeta |
| **Ava kaust**, **Ava kirje brauseris** | Avab välise asukoha | Visuaal andmeid ei muuda |
| **Seosta kinnistuid / Näita seotud kinnistuid kaardil** | Seoseta olekus võib pärast ülevaate kinnitamist lisada Kavitro kinnistuseoseid; seosega olekus muudab QGIS-i aktiivset kihti, objektivalikuid ja kaardi ulatust | Seostamist selle töövooga tagasi võtta ei saa; QGIS-i valikud saab eemaldada |
| **Genereeri projekti kaust** | Kopeerib failisüsteemi kausta ja võib muuta Kavitro projekti `filesPath` väärtust | Automaatset tagasivõtmist ei ole |
| **Seosta kinnistuid** | Lisab Kavitros projektile kinnistuseoseid | Selle töövooga seoseid eemaldada ei saa |
| Eelvaate loomine ja puhastamine | Lisab või eemaldab QGIS-i ajutisi mälukihte | Jah, kuni ala pole põhikihile salvestatud |
| **Salvesta ala kihile** | Lisab või uuendab projektide QGIS-i põhikihi objekti | Sõltub kihi redigeerimis- ja varundusolekust |
| **Joonista uus seotud ala kaardile** | Lisab projektide põhikihi objekti ja proovib uuendada Kavitro geomeetriat | QGIS-i ja Kavitro muudatused ei ole ühine tehing |

Seadistuste vaate üldine **Kinnita** ei lõpeta ega võta tagasi ühtegi siin kirjeldatud projektikaardi toimingut.

## Projektikaardi … Detailne ülevaade

Projektikaardi alumises servas asuv `…` nupp laiendab ja ahendab edenemistahvli sama kaardi sees. See ei ava eraldi dialoogi. Teise kirjekaardi detaili avamisel ahendatakse varem avatud kaart.

Esimesel avamisel:

1. loetakse projektikaardi andmetest seal kaasas olevad katastritunnused;
2. lahendatakse tunnustele Kavitro kinnistute ID-d;
3. küsitakse iga leitud kinnistu kaudu lepingud, kooskõlastused, servituudid, teised projektid, spetsifikatsioonid ja esitused;
4. sama kirje duplikaadid ühendatakse ID järgi;
5. vaadatav projekt ise jäetakse teiste projektide loendist välja;
6. kirjed jaotatakse veergudesse **Alustamata**, **Töös** ja **Tehtud**.

Jaotusreeglid on:

- mooduli seadistustes alustamata staatuseks märgitud kirje läheb veergu **Alustamata**;
- staatuse tüübiga `CLOSED` kirje läheb veergu **Tehtud**;
- kõik muud leitud kirjed lähevad veergu **Töös**.

Tahvli kirjed on lugemiseks. Neil puuduvad avamis- ja muutmisnupud.

### Andmete ulatuse kriitiline piirang

Projektide loendi ja ühe projekti päring küsivad vaikimisi ainult ühe seotud kinnistu serva (`propertiesFirst = 1`). Detailtahvel kasutab otse seda projektikaardi andmestikku ega lae projekti kõiki kinnistuseoseid eraldi. Mitme kinnistuga projekti tahvel koostatakse seetõttu tavaliselt ainult esimese päringus tagastatud kinnistu põhjal.

Iga kinnistu ja mooduli kohta küsitakse kuni 30 seotud kirjet. Järgmisi lehti ei laadita. Seega võib tahvel olla puudulik ka ühe kinnistu korral, kui mõne mooduli seoseid on üle 30.

### Värskendamine ja vead

Detail luuakse kaardil esimesel avamisel ja sama detailvidinat uuesti avades ei laadita. Pärast kinnistute sidumist või taustakirjete muutmist tuleb kogu projektikaart või projektide loend värskendada.

Üksiku mooduli päringuvead teisendatakse tühjaks tulemuseks. Tahvel ei kuva nende kohta veateadet ega erista olukorda „seoseid ei ole“ olukorrast „mooduli andmete laadimine ebaõnnestus“. Katastritunnuse põhjal kinnistu ID lahendamise erindit seevastu siin kinni ei püüta ning see võib detaili avamise katkestada. Päringud käivitatakse detaili avamise käigus kasutajaliidese lõimest; suurema seoste hulga või aeglase ühenduse korral võib aken laadimise ajal hanguda.

## Ava kaust

Ikoonnupp on aktiivne, kui projekti `filesPath` väärtus on mittetühi. Projektikausta lingi lisamisel või uuendamisel rakendatakse teenuse kinnitatud uus tee kohe sama kaardi nupule.

- Kohalik tee avatakse Windows Exploreris.
- `http` algusega väärtus avatakse operatsioonisüsteemi kaudu veebiaadressina.
- Tee olemasolu, ligipääsuõigust ega aadressi kehtivust enne avamist ei kontrollita.
- Avamisviga kirjutatakse logisse, kuid kasutajale teadet ei kuvata.

Kaustalingi eduka salvestamise järel ei asendata projektikaarti ega laadita filtreeritud loendit uuesti. Seetõttu säilivad filtrid ja kerimiskoht. Kui mutatsioon ebaõnnestub või kasutaja lingi lisamisest loobub, ei muudeta kaustanupu senist teed ega aktiivsust.

## Ava kirje brauseris

Nupp on aktiivne, kui kaardil on mooduli nimi ja projekti ID. See moodustab Kavitro veebiaadressi mooduli baasaadressist ning lisab projekti ID.

Nupp ei salvesta andmeid. Puuduva baasaadressi või avamisvea korral jääb toiming vaikseks või kirjutab vea logisse; kasutajale õnnestumise ega vea teadet ei kuvata.

## Seosta kinnistuid / Näita seotud kinnistuid kaardil

Projektikaardi toimingul on kaks olekut:

- kui projektil ei ole kinnistuseoseid, kuvatakse seostamisikoon kohtspikriga **Kinnistuseos puudub – seosta kinnistuid**; klõps käivitab sama valiku- ja kinnitustöövoo nagu **Rohkem toiminguid → Seosta kinnistuid**;
- vähemalt ühe kinnistuseose korral kuvatakse kaardiikoon kohtspikriga **Näita seotud kinnistuid kaardil**.

Seostamisoleku klõps ei salvesta andmeid kohe. Kasutaja valib kinnistud kaardilt ja kinnitab need ülevaatedialoogis. Eduka kinnituse järel muutub ainult sama projektikaardi nupp kohe kaardiikooniks; loobumise või vea korral jääb see seostamisolekusse.

Klõpsamisel tehakse kaks teineteisest sõltumatut sammu:

1. Kavitrost laaditakse lehekülgede kaupa projekti kõik seotud katastritunnused ning leitavad objektid valitakse kinnistute põhikihil;
2. projektide põhikihilt otsitakse projekti ID-ga objekt ja kaardivaade fokuseeritakse sellele.

Projektiala otsitakse väljadest `ext_project_id`, `ext_id` või `external_id`. Esimene sobiv objekt valitakse ja sellele suumitakse.

Toiming võib seega anda osalise tulemuse: kuvada ainult kinnistud või ainult projektiala. Kui kihid, väljad või objektid puuduvad, ei kuvata kasutajale koondhoiatust. Samuti ei taastata varasemat aktiivset kihti, kaardi ulatust ega objektivalikuid.

Projektiala otsene fokuseerimine jääb seotud kinnistute näitamise lisasammuks. Seoseta projekti puhul käivitab sama nupp seostamise ega luba eksitavalt projektiala või kinnistutele suumimist.

## Rohkem toiminguid

Ikoonnupp avab projektikaardil neli menüütoimingut:

- **Genereeri projekti kaust**;
- **Ava projekti ala eelvaade**;
- **Joonista uus seotud ala kaardile**;
- **Seosta kinnistuid**.

Menüü ise püsiandmeid ei muuda. Tegevused kuvatakse ka juhul, kui mõni vajalik kiht või seadistus puudub; kontroll toimub alles valitud tegevuse sees.

## Genereeri projekti kaust

### Eeltingimuste kontroll

Enne kinnitust kasutatakse kogu projektimooduli valmisolekukontrolli. See nõuab lisaks lähtekaustale, sihtkaustale ja nime reeglile ka:

- projektide põhikihti;
- eelistatud staatusi;
- eelistatud tunnuseid;
- projekti tahvli alustamata staatuseid.

Kui mõni neist puudub, kuvatakse üldine seadistuse hoiatus ja kasutaja suunatakse projektide seadistuskaardile. Seetõttu võib näiteks puuduva tahvlistaatuse tõttu olla blokeeritud ka ainult failisüsteemi kasutav kaustatoiming.

### Kinnitused ja failimõju

Enne esimest **Jah / Ei** valikut kontrollitakse, et lähte- ja sihtkaust on olemas ning et sihtkaust ei paikne mallkausta sees. Reeglist arvutatud nimi normaliseeritakse üheks Windowsis sobivaks kaustakomponendiks: teeeraldajad, kontrollmärgid ja keelatud märgid asendatakse, lõpu punktid ning tühikud eemaldatakse ja reserveeritud seadmenimed tehakse ohutuks.

Esimene kinnitus tuletab meelde, et töövoog on mõeldud eelkõige uutele projektidele, ning näitab nii lähtekausta kui ka täielikku normaliseeritud sihtteed. Vaike- ja tühistamisvalik on **Ei**, seega `Enter`, `Esc` või akna sulgemine kopeerimist ei käivita.

**Jah** korral:

1. moodustatakse kaustanimi salvestatud reeglist või vaikereeglist `PROJECT_NUMBER + PROJECT_NAME`;
2. nimi normaliseeritakse ja kontrollitakse, et lahendatud sihttee on seadistatud sihtkausta vahetu alamkaust;
3. kasutajale näidatakse tegelikku lähte- ja sihtteed;
4. **Jah** korral kopeeritakse lähtekaust koos kogu sisu ja alamkaustadega sihtkausta;
5. kui sama nimega kaust on juba olemas, ei kopeerita ega muudeta selle sisu; kasutajale näidatakse täielikku teed ja pakutakse vaikimisi eitava kinnitusega toimingut **Lisa või uuenda**;
6. pärast edukat kopeerimist küsitakse teise **Jah / Ei** valikuga, kas kaustatee lisada Kavitro projektile.

Teise valiku **Ei** jätab kausta kettale, kuid ei muuda projekti `filesPath` väärtust. Juba kopeeritud kausta ei kustutata ka hilisema lingivea korral.

Seadistuskaardil salvestatud nime reeglit kasutatakse sõltumata varasemast peidetud väärtusest **Luba eelistatud kausta nime struktuur**. Vaikereeglit kasutatakse ainult salvestatud reegli puudumisel ning see ühendab projekti numbri ja nime ilma automaatse tühiku või eraldajata. Projektinumber lahendatakse väljadest `projectNumber` või `number`; kui rakendatav reegel nõuab numbrit, kuid seda kirjel pole, peatatakse loomine hoiatusega.

### Kaustalingi salvestamine

Kaustalingi uuendamine kasutab eraldi väikest GraphQL-faili `updateProjectFilesPath.graphql`, mitte kinnistuseoste muutmiseks mõeldud `updateProjectProperties.graphql` mutatsiooni. Moodulipõhine uuendaja saadab projekti ID ja loodud kausta täieliku tee ning kontrollib vastuses `updateProject.id` ja `updateProject.filesPath` väärtusi.

Valideeritud vastuses tagastatud `filesPath` edastatakse lokaalse tagasisidega ainult sama projektikaardi toiminguribale. **Ava kaust** nupp hakkab kasutama uut teed kohe; teisi kaarte, projektide päringut ega aktiivset filtrit see toiming ei värskenda.

Olemasoleva arvutatud sihtkausta korral ei käivitata `copytree` toimingut. **Lisa või uuenda** seob ainult selle kontrollitud tee projektiga; kausta faile ja alamkaustu ei muudeta. `Enter`, `Esc`, **Ei** või dialoogi sulgemine jätab nii kausta sisu kui ka Kavitro `filesPath` väärtuse muutmata.

Puuduva päringufaili, GraphQL-vea või vastuse lahknevuse korral ei kuvata lingi salvestamist õnnestununa. Kasutajale näidatakse, et kaust on failisüsteemis juba loodud, kuid Kavitro link jäi salvestamata. Kaustanime ja sihttee kontroll toimub enne kopeerimist ega sõltu kaustalingi hilisemast salvestamisest.

## Seosta kinnistuid projektikaardi menüüst

Toiming vajab kinnistute põhikihti ja projekti ID-d.

1. Senised seosed laaditakse Kavitrost ja näidatakse võimaluse korral kinnistukihil.
2. Visuaali aken peidetakse või minimeeritakse ning QGIS-is aktiveeritakse ristkülikvalik.
3. Kaardilt valitakse üks või mitu uut kinnistut.
4. Ülevaatedialoog näitab eraldi juba seotud ja uusi valikuid.
5. **Kinnita** lahendab valitud katastritunnustele Kavitro kinnistute ID-d ja saadab need `associate` toiminguna projektile.

See on lisav, mitte asendav töövoog. **Kinnita** ei saada Kavitrosse dialoogis kuvatud olemasolevate ja uute seoste täielikku lõppnimekirja ning ei eemalda ühtegi varasemat seost.

### Ülevaatedialoogi nupud

| Nupp | Tegelik käitumine |
|---|---|
| **Vali uuesti** | Sulgeb ülevaate ja käivitab uue kaardivaliku; seniseid Kavitro seoseid ei muudeta |
| **Tühista** | Sulgeb ülevaate uusi seoseid lisamata |
| **Kinnita** | Lisab teenusest leitud valitud kinnistud projektile; leidmata tunnused jäetakse välja ja loetletakse õnnestumise teates |

Kui ühelegi valitud tunnusele Kavitro kinnistu ID-d ei leita või API-päring ebaõnnestub, võib menüüst käivitatud voos erind väljuda nupukäsitlejast ilma kasutajasõbraliku veadialoogita. Eelvaatedialoogist käivitatud samalaadne voog püüab selle vea kinni ja kuvab hoiatuse.

Kaardivaliku kontroller ei käsitle `Esc`-klahvi, paremklõpsu ega kaarditööriista vahetamist eraldi lõpetamisena. Objektita katkestamisel võib Visuaali aken või eelvaatedialoog jääda peidetuks, kuni see tuuakse uuesti ette.

## Ava projekti ala eelvaade

Nupp avab mittemodaalse dialoogi. Kui sama projektikaardi nupu kaudu avatud dialoog on juba nähtav, tuuakse olemasolev aken ette.

Dialoogi esimesel kuvamisel:

1. laaditakse Kavitrost projekti kõik katastritunnused;
2. leitavad kinnistud valitakse kinnistute põhikihil ja kaardile suumitakse;
3. valitud geomeetriad ühendatakse üheks ajutiseks alaks;
4. rakendatakse puhver ja nurkade ümardamine;
5. lõpptulemus lisatakse rühma **Sandboxing** mälukihina.

Avamine muudab QGIS-i aktiivset kihti, kinnistukihi valikut ja kaardi ulatust. Dialoogi sulgemisel kinnistuvalik eemaldatakse, kuid varasemat valikut, aktiivset kihti ega kaardiulatust ei taastata.

### Eelvaate algseaded

- Puhvri kaugus on alguses `0,0`.
- **Ümardatud nurgad** on alguses sisse lülitatud.
- Nurga raadius on alguses `2,0`.

Seega muudab esmane automaatne eelvaade vaikimisi geomeetriat kahe ühiku võrra väljapoole ja tagasi puhverdades ka siis, kui põhipuhver on null. Täpselt kinnistupiire järgiva algtulemuse jaoks lülita **Ümardatud nurgad** välja või määra raadiuseks null.

Puhvri- ja raadiuseväljade järelliide on `m`, kuid QGIS-i `native:buffer` saab väärtuse otse kinnistukihi koordinaatsüsteemi ühikutes. Kood ei teisenda geograafilise või muus mitte-meetrilises CRS-is kihti meetrilisse CRS-i. Meetri tähis on seetõttu õige ainult meetrites töötava kinnistukihi korral.

## Eelvaate Seosta kinnistuid

Nupp kasutab sama lisavat seostamisloogikat nagu projektikaardi menüü. Kaardilt kinnitatud kinnistud lisatakse olemasolevatele seostele; seoste eemaldamise võimalust ei ole.

Edu korral:

- seosed loetakse Kavitrost uuesti;
- leidmata katastritunnused näidatakse teates;
- kinnistuvalik ja eelvaategeomeetria arvutatakse uuesti ilma dialoogi sulgemata.

**Vali uuesti**, **Tühista** ja **Kinnita** käituvad nagu eelmises jaotises, kuid API-vead püütakse siin kinni ja kuvatakse hoiatusena.

## Värskenda eelvaadet

Nupp laadib projekti kinnistuseosed Kavitrost uuesti, valib leitavad kinnistud põhikihil ja loob eelvaate nullist praeguste puhvri- ning ümardusseadetega.

Puhvri kauguse, ümardusmärkeruudu või raadiuse muutmine käivitab sama geomeetria ümberarvutuse, kuid ei lae seoseid Kavitrost uuesti.

Eelmine sama projekti ajutine eelvaade eemaldatakse enne uut arvutust. Kui mõni seotud tunnus ei leidu kinnistukihil, luuakse ala ainult leitud ja valitud objektidest; teates kuvatav arv on QGIS-is valitud objektide arv.

## Salvesta ala kihile

Nupp vajab olemasolevat eelvaatekihti ja kehtivat polügoongeomeetriaga projektide põhikihti.

Salvestamisel:

1. eelvaate esimese objekti geomeetria teisendatakse projektide põhikihi CRS-i;
2. põhikihilt otsitakse projekti objekti ID, projekti numbri või nime järgi;
3. leitud objekti geomeetria ja projektiväljad uuendatakse või lisatakse uus objekt;
4. vajaduse korral lisatakse kihile väljad `ext_project_id`, `ext_system`, `ext_project_name`, `ext_project_number`, `detailed`, `active`, `added_by`, `added_date`, `updated_by` ja `update_date`.

Enne olemasoleva objekti asendamist eraldi kinnitust ei küsita.

Kui kiht ei olnud redigeerimisrežiimis, alustab ja salvestab tööriist muudatused ise. Kui kiht oli juba redigeerimisrežiimis, jääb tulemus koos muude ootel muudatustega salvestamata, kuigi Visuaal kuvab toimingu õnnestumise teate.

Nupp ei saada eelvaate geomeetriat Kavitro teenusesse. QGIS-i projektiala ja Kavitro geomeetria võivad seetõttu lahkneda.

### Vale objekti uuendamise risk

Objekti otsing käib kihil objekt-haaval ning iga objekti juures kontrollitakse järjest ID-d, numbrit ja nime. Kui kihi varasemal real on sama projekti nimi või number, võib see rida sobida enne hiljem asuvat täpse `ext_project_id` vastega rida. Sellisel juhul võidakse üle kirjutada vale projektiala.

## Puhasta eelvaade

Nupp eemaldab QGIS-i projektist selle projekti nimega kuni kolm ajutist mälukihti: põhitulemuse, vahetulemuse ja ümardatud vahetulemuse.

Nupp ei:

- kustuta projektide põhikihile salvestatud objekti;
- tühista Kavitrosse salvestatud kinnistuseoseid;
- eemalda kinnistukihi objektivalikut;
- tühjenda seotud kinnistute loendit ega näidiskaarti.

Kui ühtegi kihti ei eemaldatud, ei muudeta ka olekuteksti. Varasem „eelvaade loodi“ tekst võib seetõttu jääda nähtavaks ka puuduva eelvaate korral.

## Sulge

Nupp ja akna sulgemisrist:

- eemaldavad selle projekti ajutised eelvaatekihid;
- peatavad dialoogi aktiivse kinnistute valiku kontrolleri;
- eemaldavad eelvaates kasutatud kinnistukihi valiku;
- taastavad kaardivaliku ajal peidetud Visuaali akna;
- sulgevad dialoogi.

Põhikihile salvestatud projektiala ja Kavitro kinnistuseosed jäävad alles.

## Joonista uus seotud ala kaardile

Nupp vajab projekti ID-d ja seadistatud kirjutatavat projektide polügoonkihti.

Käivitamisel:

1. kontrollitakse ja vajaduse korral lisatakse projektide väljad;
2. kiht tehakse nähtavaks ja aktiivseks;
3. vajaduse korral alustatakse redigeerimisrežiimi;
4. QGIS-i atribuudivorm surutakse ajutiselt maha;
5. aktiveeritakse QGIS-i **Lisa objekt** tööriist;
6. esimese lisatud polügooni väljad täidetakse projekti andmetega;
7. loodud geomeetria proovitakse saata Kavitrosse.

Kui Visuaal alustas redigeerimisrežiimi, salvestab ta eduka QGIS-i toimingu järel kihi ise. Juba redigeeritava kihi korral jääb uus objekt ootele ja kasutaja peab muudatused QGIS-is salvestama või tühistama.

### Kihimuudatuse ja Kavitro sünkroonimise piirangud

Kavitro geomeetriapäring tehakse enne Visuaali alustatud kihi redigeerimisseansi lõplikku `commitChanges()` kutset. Need toimingud ei ole ühine tehing:

- Kavitro võib saada geomeetria, kuigi hilisem kihisalvestus ebaõnnestub ja QGIS-i objekt pööratakse tagasi;
- Kavitro geomeetria uuenduse ebaõnnestumine ainult logitakse ning QGIS-i sidumist käsitletakse ikkagi õnnestununa;
- kasutajale võidakse kuvada „loodi ja seoti“ eduteade ka siis, kui Kavitro geomeetria jäi uuendamata.

Geomeetriapäringusse pannakse projektikihi toorkoordinaadid ilma CRS-i teisenduse või CRS-i metaandmeta. Tulemuse õigsus sõltub sellest, millist koordinaatsüsteemi Kavitro teenus eeldab.

Toiming ei kontrolli, kas samal projektil on põhikihil juba objekt. Iga käivitus lisab uue polügooni ja sama `ext_project_id` väärtusega duplikaadid on võimalikud.

### Joonistamise katkestamise servajuht

Joonistuskontroller kuulab kihi `featureAdded` signaali, kuid ei kuula eraldi QGIS-i lisamistööriista deaktiveerimist ega `Esc`-katkestust. Kui joonistamine katkestatakse objekti loomata või kasutaja vahetab tööriista, võib kontroller jääda järgmise kihiobjekti lisamist ootama. Hiljem samale kihile lisatud objekt võidakse siis siduda varem valitud projektiga. Samaks ajaks võib jääda kehtima ka atribuudivormi mahasurumine.

## Auditi käigus leitud parandamist vajavad kohad

| Prioriteet | Leid | Kasutajarisk | Soovitatav parandus |
|---|---|---|---|
| Kriitiline | Detailtahvel kasutab projektikaardi päringus vaikimisi ainult esimest seotud kinnistut | Mitme kinnistuga projekti edenemistahvel võib jätta suure osa seotud töödest kuvamata | Laadi detaili avamisel kõik projekti kinnistuseosed lehekülgede kaupa |
| Kriitiline | Puhvri väljad on märgitud meetrites, kuid töötlus kasutab kinnistukihi CRS-i ühikuid | Geograafilises CRS-is võib `2 m` muutuda kaheks kraadiks ja tekitada väga vale projektiala | Teisenda töögeomeetria meetrilisse CRS-i või kuva ja valideeri tegelikud ühikud |
| Kriitiline | Käsitsi joonistamise Kavitro uuendus toimub enne kihi commit'i ning selle ebaõnnestumist käsitletakse ikkagi eduna | QGIS ja Kavitro võivad lahkneda mõlemas suunas, samal ajal kui kasutaja näeb eduteadet | Seo tulemus mõlema sammu õnnestumisega ning lisa taastatav tehing või koondveateade |
| Kriitiline | Katkestatud käsitsi joonistamine võib jätta `featureAdded` kuulaja aktiivseks | Hiljem lisatud kõrvaline polügoon võidakse siduda vale projektiga | Kuula kaarditööriista deaktiveerimist ja `Esc`-i ning tühista kontroller kindlalt |
| Kõrge | Seotud moodulite päring piirdub 30 kirjega ega kasuta `pageInfo` järgmist lehte | Suurte seostega tahvel on puudulik | Rakenda iga mooduli päringule paginatsioon või näita kärpimise hoiatust |
| Kõrge | Moodulipäringu vead muudetakse tühjaks tulemuseks, kinnistu-ID viga võib avamise katkestada ja kogu laadimine blokeerib UI-lõime | Andmeviga näib puuduva tööna või detail ei avane ning aken võib hanguda | Laadi taustatöös, kuva edenemine ja käsitle kõik päringuvead ühtse nähtava tulemusena |
| Kõrge | Projektiala otsing võib nime või numbri järgi leida varasema rea enne täpset ID-vastet | **Salvesta ala kihile** võib üle kirjutada vale projekti objekti | Otsi esmalt kogu kihilt ainult ID järgi; kasuta numbrit või nime alles üheselt kontrollitud varuvariandina |
| Kõrge | Eelvaate salvestamine ei uuenda Kavitro geomeetriat | QGIS-i ja Kavitro projektiala jäävad erinevaks | Paku kontrollitud sünkroonimist ja kuva selgelt mõlema andmeallika tulemus |
| Kõrge | Projektikaardi menüüst käivitatud seostamisvoog ei püüa API-erindeid | Dialoog võib sulguda ilma arusaadava veateateta ja seoste seis jääb ebaselgeks | Kasuta sama veakäsitlust nagu eelvaatedialoogis ning kuva värskendatud seoste koond |
| Kõrge | Käsitsi joonistamine lubab lisada samale projektile piiramatult sama ID-ga alasid | Kaardifookus ja hilisem ala uuendamine kasutavad vaid üht mitmest duplikaadist | Küsi olemasoleva ala korral, kas seda asendada, muuta või lisada eraldi ala |
| Keskmine | Detailtahvel laaditakse ainult esimesel avamisel ja ei värskene pärast seoste lisamist | Avatud kaart kuvab aegunud tööde ja seoste seisu | Lisa tahvlile **Värskenda** või invalideeri detail pärast seosemuudatust |
| Keskmine | Kinnistuseoste dialoogi **Kinnita** on lisav `associate`, mitte lõpliku loendi salvestus | Kasutaja võib eeldada, et valik asendab seosed või võimaldab neid eemaldada | Nimeta tegevus „Lisa valitud seosed“ ja loo eraldi eemaldamisvoog |
| Keskmine | Projektikausta valmisolekukontroll nõuab ka kihte, filtreid ja tahvlistaatusi | Failikausta loomine võib olla blokeeritud kõrvalise seadistuse tõttu | Kontrolli kaustatoimingus ainult lähte-, siht- ja nimeseadeid |
| Keskmine | Eelvaate vaikeseade ümardab ala raadiusega 2,0 | Kasutaja võib salvestada kinnistupiiridest erineva ala seda märkamata | Kasuta vaikimisi nullraadiust või nõua enne salvestamist nähtavat kinnitust |
| Keskmine | Kaardivaliku `Esc`, paremklõps ja tööriistavahetus ei taasta alati Visuaali akent | Töövoog näib kinni jäänud | Lisa kontrollerile katkestussignaal ja kasutajaliidese taastamine |
| Keskmine | Kihil juba avatud redigeerimisseansi korral kuvatakse salvestamise edu, kuigi muudatus jääb ootele | Kasutaja võib QGIS-i sulgedes projektiala kaotada | Erista „salvestatud“ ja „QGIS-is ootel“ teated |
| Madal | **Ava kaust** ja **Ava kirje brauseris** ei kuva avamisviga kasutajale | Nupp võib näida mittetöötav | Kuva vigase tee, URL-i või käivitamisvea korral hoiatus |
| Madal | Kaardinupu kohtspikker on tõlkimata ning **Puhasta eelvaade** võib jätta vana olekuteksti | Kasutajaliidese seis ja keel on eksitavad | Rakenda kohtspikrile tõlge ning tühjenda olek alati pärast puhastamist |

## Soovituslik turvaline tööjärjekord

1. Veendu, et kinnistute ja projektide kihid kasutaksid meetrilist ning omavahel õigesti teisendatavat CRS-i.
2. Hoia projektide kiht enne automaatset salvestamist redigeerimisrežiimist väljas või arvesta teadlikult ootel muudatustega.
3. Kontrolli enne detailtahvli põhjal otsustamist projektiga seotud kinnistute koguarvu; mitme kinnistu korral ei ole tahvel praegu täielik.
4. Lülita eelvaates ümardamine välja, kui soovid täpselt kinnistupiire järgivat ala.
5. Enne **Salvesta ala kihile** vajutamist kontrolli `ext_project_id`, sama nime või numbriga objekte ja tee kihist varukoopia.
6. Pärast käsitsi joonistamist kontrolli eraldi QGIS-i objekti, kihi salvestusolekut ja Kavitro geomeetriat.
7. Pärast projektikausta lingi lisamist kontrolli sama kirjekaardi **Ava kaust** nuppu; see peab kasutama uut teed ilma projektide loendit uuesti laadimata.
8. Kui kaardivalik või joonistamine katkestati, ära lisa samale kihile teist objekti enne projektitöövoo uuesti käivitamist või Visuaali taaskäivitamist.

## Seotud juhendid

- [Projektide nupud](05_projektide_nupud.md)
- [Projektide mooduli kasutamine](../13_projektide_mooduli_kasutamine.md)
- [Projektide mooduli seadistamine](../07_projektide_mooduli_seadistamine.md)
- [Seadistuste nuppude detailaudit](03_01_seadistuste_nuppude_detailaudit.md)
- [Filtrite nuppude detailaudit](02_01_filtrite_nuppude_detailaudit.md)
- [Failide ja ühisdialoogide nupud](09_failide_ja_uhisdialoogide_nupud.md)
