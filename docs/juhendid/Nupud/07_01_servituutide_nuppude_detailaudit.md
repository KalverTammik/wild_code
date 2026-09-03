# Servituutide nuppude detailaudit

See juhend kirjeldab Visuaali servituutide nuppude tegelikku käitumist praeguse koodibaasi järgi. Kaetud on kirjekaardi detail, ühised avamis- ja kaarditoimingud, failid, uue ja olemasoleva geomeetria sidumine, geomeetria muutmine, kinnistuseosed, arvutuslik eelvaade, kinnistuandmed ning PDF-skeem.

Staatus- ja liigifiltri ning filtrite värskendamise ja tühjendamise täpne käitumine on failis [Filtrite nuppude detailaudit](02_01_filtrite_nuppude_detailaudit.md). Servituutide filtrireal tunnuse- ega tähtaja kiirnuppe ei ole.

## Mõju lühikaart

| Nupp või nupurühm | Peamine mõju | Kas toiming on tagasi võetav? |
|---|---|---|
| **… Detailne ülevaade** | Kuvab kaardil kaasas olnud kinnistuandmed, laadib failid ja muudab QGIS-i kinnistuvalikut ning kaardi ulatust | Püsiandmeid ei muudeta; kaardivaate saab käsitsi taastada |
| **Ava kaust**, **Ava kirje brauseris** | Avab välise asukoha | Visuaal andmeid ei muuda |
| **Seosta kinnistuid / Näita seotud kinnistuid kaardil** | Seoseta olekus võib pärast ülevaate kinnitamist lisada Kavitro kinnistuseoseid; seosega olekus laadib seotud kinnistud ja fokuseerib võimaluse korral servituudi põhikihi objekti | Seostamist selle töövooga tagasi võtta ei saa; kaardil näitamine püsiandmeid ei muuda |
| **Failid** | Peaks avama failihalduse | Praeguses versioonis ei käivitu |
| **Joonista uus seotud objekt kaardile** | Lisab QGIS-i objekti ja proovib saata geomeetria Kavitrosse | QGIS-i ja Kavitro muudatused ei ole ühine tehing |
| **Seo olemasolev joonis kaardilt** | Kirjutab olemasolevale objektile servituudi väljad ja saadab geomeetria Kavitrosse | Automaatset ühist tagasivõtmist ei ole |
| Konflikti **Kustuta objekt** või **Arhiveeri objekt** | Kustutab QGIS-i objekti või muudab selle staatust | Kavitro kirjet ei muudeta; salvestatud kihimuudatus võib olla pöördumatu |
| **Muuda joonise geomeetriat kaardil** | Käivitab QGIS-i redigeerimise | Muudatusi haldab QGIS; Kavitrot ei sünkroonita |
| **Seosta kinnistuid** | Lisab Kavitro servituudile kinnistuseoseid | Selle töövooga seoseid eemaldada ei saa |
| Eelvaate loomise ja puhastamise nupud | Lisavad või eemaldavad QGIS-i ajutisi mälukihte ja valikuid | Jah, kuni tulemust pole põhikihile salvestatud |
| **Salvesta servituudi kinnistuandmed** | Uuendab Kavitro seosemetaandmeid, QGIS-i põhikihti ja Kavitro geomeetriat | Kolm andmemõju ei ole ühine tehing |
| **Avalda PDF skeem** | Laadib uue faili Kavitrosse | Avaldatud faili eemaldamiseks on vaja failihaldust või veebirakendust |

Seadistuste vaate üldine **Kinnita** ei lõpeta ega võta tagasi ühtegi siin kirjeldatud servituudikaardi toimingut.

## … Detailne ülevaade

Kirjekaardi alumises servas asuv `…` nupp laiendab ja ahendab detaili sama kaardi sees. Teise kirjekaardi detaili avamine ahendab varem avatud kaardi.

Detail kasutab kirjekaardi päringus juba kaasas olnud kinnistuseoseid:

- loendipäring ja üksikkirje päring toovad ühe servituudi kohta kuni 25 kinnistuseost;
- järgmisi kinnistuseoste lehti detaili jaoks ei laadita;
- iga nähtava kinnistu kohta kuvatakse lugemisrežiimis pindala, ühikuhind, tasulisus, kogusumma ja maksekuupäev, kui need andmed on teenusest tulnud;
- detaili all laaditakse eraldi failide kokkuvõte, milles kuvatakse kuni viis esimest kuni 200 laaditud failist.

Detail luuakse kaardi esimesel avamisel ja seda ei värskendata sama kaardi ahendamisel ning uuesti avamisel. Värske seisu saamiseks tuleb servituutide loend uuesti laadida.

### Kaardimõju detaili avamisel ja sulgemisel

Iga `…` vajutus käivitab enne laiendamist või ahendamist ka detaili kaarditoimingu. Seega proovib nupp kinnistud kaardil valida ja neile suumida ka siis, kui kasutaja detaili parajasti sulgeb.

Kaardile viiakse ainult kirjekaardi payload'is olevad kuni 25 kinnistut, mitte eraldi teenusest laaditud täielik seoseloend. Varasemat aktiivset kihti, kinnistuvalikut ega kaardiulatust ei taastata. Puuduva kihi või leidmata tunnuste korral kasutajale eraldi koondhoiatust ei kuvata.

## Ava kaust

Nupp on aktiivne ainult siis, kui kirjekaardi loomise ajal oli servituudi `filesPath` väärtus mittetühi.

- Kohalik tee antakse Windows Explorerile.
- `http` algusega väärtus avatakse operatsioonisüsteemi `start` käsuga.
- Tee olemasolu, ligipääsuõigust ega aadressi kehtivust ei kontrollita.
- Avamisviga logitakse, kuid kasutajale õnnestumise ega vea teadet ei kuvata.

Kavitros muudetud `filesPath` ei uuenda sama kirjekaardi nuppu enne loendi uut laadimist.

## Ava kirje brauseris

Nupp koostab servituudi Kavitro veebiaadressi mooduli baasaadressist ja kirje ID-st. Puuduva baasaadressi või avamisvea korral jääb toiming vaikseks või kirjutab vea logisse.

Veebivaade on praeguses versioonis vajalik ka täielikuks failihalduseks, sest kirjekaardi **Failid** toiming ei käivitu.

## Seosta kinnistuid / Näita seotud kinnistuid kaardil

Servituudikaardi toimingul on kaks olekut. Kinnistuseoseta kirjel kuvatakse seostamisikoon kohtspikriga **Kinnistuseos puudub – seosta kinnistuid** ja klõps käivitab olemasoleva kaardivaliku ning ülevaatedialoogi. Vähemalt ühe seose korral kuvatakse kaardiikoon kohtspikriga **Näita seotud kinnistuid kaardil**. Eduka seostamise järel vahetub ainult sama kaardi nupp kohe kaardiikooniks; tühistamine või viga jätab selle seostamisolekusse.

Klõpsamisel tehakse kaks teineteisest sõltumatut sammu:

1. Kavitrost laaditakse lehekülgede kaupa kõik servituudiga seotud katastritunnused ning leitavad objektid valitakse kinnistute põhikihil;
2. servituutide põhikihilt otsitakse kirje ID-ga objekt ja sellele suumitakse.

Põhikihi fookus otsib välju `ext_easement_id`, `ext_id` või `external_id`. Seotud objekti või kinnistute puudumine ei tekita kasutajale koondhoiatust. Toiming võib anda osalise tulemuse ning ei taasta varasemat aktiivset kihti, objektivalikut ega ulatust.

Servituudi põhikihi objekti fokuseerimine toimub seotud kinnistute näitamise lisasammuna. Seoseta kirje seostamisikoon käivitab selle asemel kinnistute seostamise.

## Rohkem toiminguid

Servituudikaardi menüü sisaldab selles järjekorras:

1. **Failid**;
2. **Joonista uus seotud objekt kaardile**;
3. **Seo olemasolev joonis kaardilt**;
4. **Muuda joonise geomeetriat kaardil**;
5. **Ava servituudi eelvaade**;
6. **Seosta kinnistuid**.

Menüütoiminguid ei peideta puuduva kihi, seadistuse või õiguse järgi. Vajalik kontroll toimub alles valitud tegevuse sees.

## Failid

Praeguses koodis ühendatakse menüütoiming kutsega `self._open_item_files(...)`, kuid klassis ega mujal repos sellist meetodit ei ole. Klõps lõpeb puuduva atribuudi veaga ja olemasolevat `TaskFilesDialog` dialoogi ei looda.

Dialoogiklass ise toetaks kuni 200 faili laadimist, failide üleslaadimist, eelvaadet, lubatud tüüpi faili turvakinnitusega väliselt avamist, kinnitusega kustutamist ja värskendamist. Kuni menüü käsitleja parandamiseni kasuta **Ava kirje brauseris** toimingut. Detailvaate kuni viis failirida jäävad lugemiseks ja eelvaateks kasutatavaks.

## Joonista uus seotud objekt kaardile

Toiming vajab seadistatud kirjutatavat servituutide polügoonkihti ja servituudi ID-d.

1. Põhikiht tehakse nähtavaks ning aktiivseks.
2. Vajaduse korral alustatakse redigeerimisrežiimi.
3. QGIS-i tavapärane atribuudivorm surutakse ajutiselt maha.
4. Käivitatakse QGIS-i **Lisa objekt** tööriist.
5. Esimese lisatud objekti järel avaneb **Servituudi ala andmed**.
6. **Salvesta** kirjutab kihiväljad ja proovib saata geomeetria Kavitrosse.

Puuduvad väljad `ext_easement_id`, `ext_system` ja `ext_easement_number` proovitakse kihile automaatselt lisada.

Kui Visuaal alustas redigeerimisseansi, salvestatakse edukas kihimuudatus pärast Kavitro geomeetriapäringut. Juba redigeeritava kihi korral jääb objekt ootele, kuid Kavitro geomeetria võib olla juba uuendatud.

### Katkestamine ja osaline tulemus

Kui vormis vajutada **Katkesta**:

- Visuaali alustatud redigeerimisseanss pööratakse tagasi;
- varem redigeeritavas kihis võib joonistatud objekt muutmispuhvrisse alles jääda;
- katkestust käsitletakse tehniliselt salvestusveana ja kasutajale võidakse kuvada ebaõnnestumise hoiatus.

Joonistuskontroller ei kuula eraldi QGIS-i lisamistööriista `Esc`-katkestust ega tööriista vahetamist. Objektita katkestamisel võib `featureAdded` kuulaja jääda aktiivseks ning järgmine samale kihile lisatud kõrvaline objekt võidakse siduda varem valitud servituudiga.

Kavitro geomeetria saadetakse enne Visuaali alustatud kihiseansi lõplikku kinnitamist. Kui teenuse uuendus õnnestub, kuid hilisem kihi `commitChanges()` ebaõnnestub, võib Kavitro geomeetria uueneda ja QGIS-i objekt kaduda.

## Servituudi ala andmete vorm

Vormi **Salvesta** ei kirjuta kõiki välju tingimusteta:

- väärtus kirjutatakse ainult kihil olemasolevasse sobiva nimega välja;
- tühi vormiväärtus ei tühjenda olemasolevat kihivälja;
- vormi mittetühi staatus kirjutab seadistatud staatusevastenduse tulemuse üle;
- kehtestamise kuupäev saadetakse ainult staatusega täpselt **Kehtestatud** või olemasoleva algkuupäeva korral;
- **Talumistasu arvestatakse** väärtus kogutakse, kuid põhikihi kirjutusloogika seda ühelegi väljale ei salvesta.

**Katkesta** sulgeb vormi väärtusi kinnitamata, kuid selle mõju juba joonistatud objektile sõltub kihi varasemast redigeerimisolekust.

## Seo olemasolev joonis kaardilt

Toiming peidab või minimeerib Visuaali akna ning aktiveerib ühe klõpsuga kaardivaliku.

- Vasakklõps otsib klikitud kohast servituutide põhikihi polügooni.
- Tühja koha klõps kuvab hoiatuse ja jätab valikurežiimi aktiivseks.
- Paremklõps või `Esc` katkestab valiku ja taastab Visuaali akna.
- Leitud objekti korral avaneb andmevorm ning **Salvesta** kirjutab seoseväljad ja saadab geomeetria Kavitrosse.

Kui kiht ei olnud redigeeritav, kinnitatakse QGIS-i muudatus enne Kavitro geomeetria saatmist. Teenuse saatmise vea korral jääb juba salvestatud QGIS-i objekt uue ID-ga seotuks. Juba redigeeritava kihi korral jääb väljamuudatus ootele, kuid Kavitro võib olla uuendatud.

### Teise servituudiga seotud objekti konflikt

Kui objektil on teine servituudi ID, pakutakse:

| Nupp | Tegelik käitumine |
|---|---|
| **Kustuta objekt** | Kustutab valitud objekti ainult QGIS-i servituudikihilt ja lõpetab sidumisvoo |
| **Arhiveeri objekt** | Määrab ainult QGIS-i objekti staatuseks `(puudub)`, jätab varasema servituudi ID alles ja lõpetab voo |
| **Loobu** | Ei muuda objekti ja lõpetab voo |

Kustutamine ega arhiveerimine ei muuda Kavitro teenuse servituudikirjet. Uue objekti sidumiseks tuleb menüütoiming uuesti käivitada.

Kui kiht oli enne toimingut redigeerimisrežiimis, jääb edukas kustutamine või arhiveerimine ootele. Erindite käsitlemise harud võivad aga kutsuda `rollBack()` ka kasutaja varem avatud redigeerimisseansile ning tühistada samal kihil muid ootel muudatusi.

## Muuda joonise geomeetriat kaardil

Toiming otsib servituudi põhikihilt objekti esmalt ID ja seejärel numbri järgi, valib selle ning käivitab QGIS-i tippude tööriista või varuvariandina objekti liigutamise.

See nupp:

- võib alustada kihi redigeerimisrežiimi;
- ei jälgi redigeerimise lõpetamist;
- ei salvesta ega tühista muudatusi;
- ei saada muudetud geomeetriat Kavitrosse.

Kasutaja peab kihi muudatused QGIS-is ise salvestama või tühistama ning vajaduse korral kasutama eraldi Kavitro sünkroonimisviisi.

Objekti otsing kontrollib iga kihiobjekti juures ID-d ja seejärel numbrit. Kihis varem paiknev sama numbriga objekt võib seetõttu sobida enne hiljem paiknevat täpse ID-ga objekti.

## Seosta kinnistuid

Kirjekaardi menüü kasutab sama ühist lisavat töövoogu nagu projektid, lepingud ja kooskõlastused.

1. Olemasolevad seosed laaditakse Kavitrost ja näidatakse võimaluse korral kaardil.
2. Kasutaja valib kinnistute põhikihilt ristkülikuga uued kinnistud.
3. Ülevaatedialoog näitab eraldi olemasolevaid ja uusi valikuid.
4. **Kinnita** lahendab valitud tunnustele kinnistu ID-d ning saadab need `associate` toiminguna.

See töövoog ainult lisab seoseid. **Vali uuesti** käivitab uue valiku, **Tühista** ei lisa midagi ja **Kinnita** ei eemalda ega asenda olemasolevaid seoseid.

Kinnistu-ID lahendamise või seostamise erind võib väljuda nupukäsitlejast ilma kasutajasõbraliku veadialoogita. Objektita `Esc`-katkestamine, paremklõps või tööriistavahetus ei taasta selles ühises ristkülikvalikus alati Visuaali akent.

## Ava servituudi eelvaade

Nupp avab mittemodaalse eelvaatedialoogi. Sama kirjekaardi kaudu juba avatud dialoog tuuakse uuesti ette.

Esimesel kuvamisel:

1. laaditakse Kavitrost lehekülgede kaupa kõik servituudi kinnistuseosed ja seosemetaandmed;
2. leitavad kinnistud valitakse põhikihil ning neile suumitakse;
3. kinnistutest luuakse üldise puhvri kaugusega ajutine mälukiht;
4. üheksalt seadistatud tehnovõrgukihilt valitakse puhveralaga ristuvad objektid;
5. igale leitud objektirühmale luuakse arvutatud või üldise kaugusega puhver.

Päringud, QGIS-i valikud ja töötlemisalgoritmid käivad kasutajaliidese lõimest ning suure andmehulga korral võib dialoog ajutiselt mitte reageerida. Teenuse päringu vea korral võib tagastuda tühi või osaline kinnistuloend ilma veaseisu ja päriselt puuduva seose selge eristuseta.

## Puhvri kaugus ja Ümardatud nurgad

**Puhvri kaugus** on vaikimisi `2,0 m`, vahemikuga `0,1–500,0`. Väärtus on varukaugus; fikseeritud või atribuudi järgi arvutatava reegliga tehnovõrgureal võib muudatus nähtavat puhvrit mitte mõjutada.

Kood annab kauguse QGIS-i `native:buffer` algoritmile otse lähtekihi koordinaatsüsteemi ühikutes. Meetri järelliide ja automaatreeglite meetritähendus on õiged ainult meetrites töötaval lähtekihil. Geograafilises CRS-is võib näiteks `2 m` muutuda kaheks kraadiks.

**Ümardatud nurgad** muudab ainult puhvri `END_CAP_STYLE` parameetrit. `JOIN_STYLE` ehk tegelik nurgastiil jääb alati ümardatuks. Seetõttu mõjutab märkeruut eelkõige jooneotsi ning polügoonide nurkade puhul ei pruugi midagi muuta.

Mõlema juhtelemendi muutmine eemaldab varasemad ajutised eelvaated ja lõpliku lõike, tühjendab arvutatud pindalad ning käivitab automaatika uuesti.

## Määra kinnistud kaardilt

Nupp kuvatakse ainult siis, kui Kavitrost laaditud kinnistuseoste loend on tühi. Olemasoleva ühe või enama seose korral nupp peidetakse.

Kaardilt kinnitatud valikud liidetakse dialoogi redaktoris olevatele ridadele. Neid ei saadeta selle nupu kaudu Kavitrosse ning olemasolevaid ridu ei saa eemaldada. Teenusesse kirjutamine toimub alles nupuga **Salvesta servituudi kinnistuandmed**.

Ülevaatedialoogis saab kasutada **Vali uuesti**, **Tühista** ja **Kinnita**. Pärast esimese valiku kinnitamist peidetakse **Määra kinnistud kaardilt**, seega täiendava valiku jaoks tuleb enne kinnitamist kasutada **Vali uuesti** või lisada hiljem kirjekaardi **Seosta kinnistuid** toiminguga.

## Loo lõplik lõige

Nupp lõikab iga tehnovõrgu puhverala valitud kinnistukihiga, ühendab tulemused ja lahustab need üheks ajutiseks servituudiala mälukihiks.

- Põhikihti ega Kavitrot ei muudeta.
- Edu korral eemaldatakse tehnovõrgu- ja kinnistupuhvrite ajutised vahekihid, kuid lähtekihtide objektivalikud jäävad alles.
- Kui ükski puhver kinnistutega ei lõiku, lõplikku kihti ei looda.
- Lõplikust kihist arvutatakse dialoogi kinnisturidade pindalad ja kogupindala.

Dialoogi üldine olekutekst on kasutajaliideses konstruktoris peidetud ja seda hiljem nähtavaks ei tehta. Seetõttu ei ole lõpliku lõike õnnestumise, ebaõnnestumise ega **Puhasta eelvaated** koondtekst nähtav; tulemust tuleb kontrollida QGIS-i kihipaneelilt ja kaardilt.

## Kinnistupõhiste andmete juhtelemendid

Iga kinnisturea juures saab määrata pindalaühiku, ühikuhinna, valuuta, tasulisuse ja järgmise makse kuupäeva. Pindala ise arvutatakse lõpliku lõike ning kinnistu geomeetria lõikumisest.

Kui teenusest tulnud seos ei olnud alguses tasuline, ei looda reale kogusumma ega järgmise makse välja. Hiljem **Tasuline** märkimine neid juhtelemente dünaamiliselt ei lisa, kuigi tasulisuse väärtus salvestatakse. Kui seos oli alguses tasuline, jäävad väljad nähtavale ka märkeruudu eemaldamisel.

Maksekuupäev peab olema kujul `AAAA-KK-PP`. Vigane esimene kuupäev peatab kogu salvestamise.

## Salvesta servituudi kinnistuandmed

Nupp on aktiivne, kui redaktoris on vähemalt üks kinnisturida. Toimingute järjekord on:

1. loetakse redaktorist seosed ja arvutatud pindalad;
2. uutele katastritunnustele lahendatakse Kavitro kinnistu ID-d;
3. leitud seosed koos pindala-, hinna-, valuuta-, tasulisuse ja makseandmetega saadetakse Kavitrosse `associate` toiminguna;
4. seosed laaditakse teenusest uuesti;
5. vajaduse korral luuakse lõplik lõige;
6. avatakse **Servituudi ala andmed**;
7. lõplik geomeetria lisatakse või kirjutatakse servituutide põhikihil üle;
8. salvestatud geomeetria proovitakse saata Kavitrosse.

See ei ole ühine tehing. Teenuse seoseandmed võivad olla muudetud ka siis, kui kasutaja vajutab hiljem andmevormis **Katkesta**, põhikihi salvestamine ebaõnnestub või geomeetriat ei õnnestu Kavitrosse saata.

### Pindala salvestamise järjekorraviga

Kinnistuandmete payload koostatakse enne seda, kui nupp vajaduse korral lõpliku lõike loob. Kui kasutaja ei vajutanud varem **Loo lõplik lõige**, on arvutatud pindalad payload'i koostamise ajal nullid ja neid ei saadeta selle salvestuskorraga Kavitrosse. Nupu hiljem loodud lõige ei käivita seosemetaandmete teist salvestamist.

Ohutu tööjärjekord on seetõttu: loo esmalt lõplik lõige, kontrolli arvutatud pindalasid ja vajuta alles siis **Salvesta servituudi kinnistuandmed**.

### QGIS-i põhikihi ja Kavitro lahknemise risk

- Olemasolev sama servituudi objekt kirjutatakse üle ilma eraldi kinnitusküsimuseta.
- Juba redigeeritava põhikihi muudatus jääb ootele, kuigi Kavitro seosed ja geomeetria võivad olla salvestatud.
- Kihi salvestamise järel ebaõnnestunud Kavitro geomeetriapäring ei pööra QGIS-i objekti tagasi.
- Erindite haru võib kutsuda `rollBack()` ka kasutaja varem avatud redigeerimisseansile ja tühistada teisi ootel kihimuudatusi.
- Olemasoleva objekti otsing võib sama numbri järgi leida varasema vale objekti enne täpset ID-vastet.

Põhikihi pindalaväljale kirjutatakse `geometry.area()` tulemus sihtkihi ruutühikutes, mitte alati ruutmeetrites. Dialoogi kinnistupindalad arvutatakse seevastu `QgsDistanceArea` abil ruutmeetriteks. Mitte-meetrilises CRS-is võivad teenuse seosepindala ja põhikihi pindalaväli erineda väga suurelt.

## Eelvaata PDF skeemi

Nupp kasutab olemasolevat lõplikku lõiget või proovib selle automaatselt luua, genereerib kohaliku PDF-i ja avab failieelvaate.

- Kaart kasutab QGIS-i kaardil parajasti nähtavaid kihte ning lisab kinnistu- ja lõpliku servituudiala kihi.
- Ulatus arvutatakse lõplikust alast ja valitud kinnistutest.
- Kinnistu kokkuvõttes kuvatakse kuni kaks nimetust ning ülejäänute arv.
- PDF-i numbrivälja pealkiri on koodis ekslikult **Lepingu nr**, kuigi väärtus on servituudi number.
- Genereeritud PDF asendab sama servituudinumbriga varasema ajutise PDF-i.

Kui QGIS-i käitusaeg ei toeta sisseehitatud PDF-vaadet, kuvatakse hoiatus enne eelvaatedialoogi loomist. **Ava väliselt** nuppu siis ei pakuta.

## Avalda PDF skeem

Nupp genereerib PDF-i iga vajutusega uuesti ja laadib selle servituudi failina Kavitrosse. Enne üleslaadimist ei küsita kinnitust ega kontrollita, kas sama nimega skeem on juba olemas.

Edu korral kuvatakse teade. Avaldatud faili ei eemaldata eelvaatedialoogi sulgemisel. Kuna **Failid** menüütoiming on katki, tuleb avaldatud faili kontrollimiseks või kustutamiseks avada servituut Kavitro veebirakenduses.

## Puhasta eelvaated

Nupp:

- katkestab aktiivse kinnistute ristkülikvaliku;
- eemaldab dialoogi ajutised tehnovõrgu-, kinnistu- ja lõpliku lõike mälukihid;
- eemaldab kinnistute ja tehnovõrgukihtide automaatsed objektivalikud;
- nullib arvutatud pindalad.

Nupp ei kustuta põhikihile salvestatud objekti, Kavitro seoseid, geomeetriat ega avaldatud PDF-i. Samuti ei kustuta see kohe genereeritud kohalikku PDF-i; kohalik fail eemaldatakse järgmise genereerimise või dialoogi sulgemise ajal. Puhastamise koondtekst jääb peidetud olekusildi tõttu nähtamatuks.

## Sulge

Nupp ja akna sulgemisrist eemaldavad samad ajutised kihid ja valikud nagu puhastamine, kustutavad dialoogi viimase kohaliku PDF-i, katkestavad kinnistute valiku, taastavad peidetud Visuaali akna ja sulgevad eelvaate.

Põhikihile, Kavitrosse või avaldatud faili tehtud muudatusi sulgemine tagasi ei võta.

## Auditi käigus leitud parandamist vajavad kohad

| Prioriteet | Leid | Kasutajarisk | Soovitatav parandus |
|---|---|---|---|
| Kriitiline | **Failid** menüütoiming viitab olematule `_open_item_files` meetodile | Täielikku failihaldust ei saa Visuaalist avada, sh avaldatud PDF-i kustutada | Lisa käsitleja, mis loob `TaskFilesDialog` dialoogi, ning kata menüütoiming testiga |
| Kriitiline | Puhvrikaugused märgitakse meetrites, kuid `native:buffer` saab väärtuse lähtekihi CRS-i ühikutes | Geograafilises või muus mitte-meetrilises CRS-is võib servituudiala olla väga vale | Teisenda töögeomeetriad meetrilisse CRS-i või valideeri ja kuva tegelik ühik |
| Kriitiline | Kinnistuandmete payload koostatakse enne puuduva lõpliku lõike loomist | Ilma eelneva **Loo lõplik lõige** vajutuseta võivad arvutatud pindalad Kavitrosse salvestamata jääda | Loo ja arvuta lõige enne payload'i kogumist või saada pärast arvutust teine kontrollitud uuendus |
| Kriitiline | Katkestatud uue objekti joonistamine võib jätta `featureAdded` kuulaja aktiivseks | Hilisem kõrvaline polügoon võidakse siduda vale servituudiga | Kuula lisamistööriista deaktiveerimist ja `Esc`-i ning lõpeta kontroller kindlalt |
| Kõrge | Kihi ja Kavitro kirjutustoimingud ei moodusta ühist tehingut | QGIS-i objekt, seosemetaandmed ja teenuse geomeetria võivad jääda eri seisu | Raporteeri iga sammu tulemus ning lisa taastatav või korduv sünkroonimisvoog |
| Kõrge | Erindite harud võivad `rollBack()` abil tühistada kasutaja juba avatud redigeerimisseansi muudatused | Servituuditoiminguga mitteseotud ootel kihimuudatused võivad kaduda | Pööra tagasi ainult tööriista enda alustatud seanss või kasuta eraldi edit command'i |
| Kõrge | Eelvaate üldine olekusilt peidetakse ja seda ei näidata hiljem | Lõpliku lõike ning puhastamise tulemus ja vead ei ole tekstina nähtavad | Kutsu oleku muutmisel `show()` või eemalda algne püsiv peitmine |
| Kõrge | **Määra kinnistud kaardilt** peidetakse kõigi olemasolevate seoste korral | Eelvaatest ei saa olemasolevale servituudile uut kinnistut lisada, kuigi nupu nimi viitab üldisele määramisele | Hoia nupp nähtaval ja luba lisamine; seoste eemaldamiseks loo eraldi kinnitatud töövoog |
| Kõrge | Põhikihi pindala arvutatakse kihi ruutühikutes, aga väärtust käsitletakse ruutmeetritena | Mitte-meetrilises CRS-is salvestub vale pindala | Kasuta sama `QgsDistanceArea` ruutmeetriarvutust nagu kinnistuseostel |
| Kõrge | Uue objekti Kavitro sünkroon toimub enne Visuaali alustatud kihi commit'i | Kavitro võib uueneda ka siis, kui QGIS-i salvestus hiljem ebaõnnestub | Kinnita kiht enne teenuse saatmist või rakenda kompenseeriv tagasipööramine |
| Keskmine | **Ümardatud nurgad** muudab otsakuju, mitte nurgastiili | Nupp ei anna nimele vastavat tulemust, eriti polügoonidel | Seo märkeruut `JOIN_STYLE` parameetriga ja nimeta otsakuju eraldi |
| Keskmine | Objekti otsing võib numbri vaste leida enne täpset ID-vastet | Muutmisele või ülekirjutamisele võib sattuda vale servituudiala | Otsi kogu kihilt esmalt ainult ID järgi ja kasuta numbrit alles üheselt kontrollitud varuvariandina |
| Keskmine | Mittetasulise seose märkimine tasuliseks ei lisa maksekuupäeva ega kogusumma juhtelemente | Kasutaja ei saa uue tasulise seose kõiki andmeid sisestada ega kontrollida | Ehita tasulisuse muutusel sõltuvad väljad dünaamiliselt ümber |
| Keskmine | PDF-i silt ütleb **Lepingu nr** ja avaldamine ei kontrolli duplikaati | Skeem on valesti nimetatud ning korduvad vajutused võivad luua dubleeritud failid | Paranda silt, näita failinime ja küsi olemasoleva faili korral asendamise või uue versiooni valik |
| Madal | Detaili ahendamine käivitab uuesti kinnistute kaardile näitamise | Sulgemisnupp muudab ootamatult QGIS-i vaadet | Käivita detaili avamiskallback ainult suletud olekust avamisel |
| Madal | Kaardinupu kohtspikker on ingliskeelne ja osa kaardivigu on vaiksed | Keelekasutus on ebaühtlane ning nupp võib näida mittetöötavana | Kasuta tõlgitud võtit ja kuva leitud ning leidmata objektide koond |

## Soovituslik turvaline tööjärjekord

1. Kasuta meetrilise CRS-iga lähte- ja põhikihte ning kontrolli kõiki vajalikke baaskihte.
2. Hoia põhikiht enne kirjutavat toimingut redigeerimisrežiimist väljas ja salvesta muud ootel kihimuudatused.
3. Kontrolli eelvaates automaatselt valitud kinnistuid ning tehnovõrgu objekte.
4. Vajuta **Loo lõplik lõige** ja kontrolli kaardilt geomeetriat ning pindalasid.
5. Alles seejärel sisesta hinna- ja makseandmed ning vajuta **Salvesta servituudi kinnistuandmed**.
6. Pärast salvestamist kontrolli eraldi Kavitro seoseid, QGIS-i põhikihti ja Kavitro geomeetriat.
7. Kontrolli PDF-skeemi kihte ja sisu enne **Avalda PDF skeem** vajutamist.
8. Halda avaldatud faile praegu Kavitro veebirakenduses.

## Seotud juhendid

- [Servituutide nupud](07_servituutide_nupud.md)
- [Servituutide mooduli kaarditoimingud](../14_servituutide_mooduli_kaarditoimingud.md)
- [Servituutide mooduli seadistamine](../08_servituutide_mooduli_seadistamine.md)
- [Filtrite nuppude detailaudit](02_01_filtrite_nuppude_detailaudit.md)
- [Loendite, filtrite ja kirjekaartide nupud](02_loendid_filtrid_ja_kirjekaardid.md)
- [Failide ja ühisdialoogide nupud](09_failide_ja_uhisdialoogide_nupud.md)
