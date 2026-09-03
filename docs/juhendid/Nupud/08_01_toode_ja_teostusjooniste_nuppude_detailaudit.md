# Tööde ja teostusjooniste nuppude detailaudit

See juhend kirjeldab Visuaali tööde ja teostusjooniste nuppude tegelikku käitumist praeguse koodibaasi järgi. Kaetud on ühised kirjekaardinupud, staatuse muutmine, töö loomine ja kaardipunktid, sidumata GIS-tööd, teostusjoonise märkmed ja uue geomeetria joonistamine.

Staatus- ja liigifiltri ning filtrite värskendamise ja tühjendamise täpne käitumine on failis [Filtrite nuppude detailaudit](02_01_filtrite_nuppude_detailaudit.md). Failide eelvaate ühisdialoogi nupud on failis [Failide ja ühisdialoogide nupud](09_failide_ja_uhisdialoogide_nupud.md).

## Mõju lühikaart

| Nupp või nupurühm | Peamine mõju | Kas toiming on tagasi võetav? |
|---|---|---|
| **… Detailne ülevaade** | Laadib töö kirjelduse ja failide kokkuvõtte sama kirjekaardi sisse | Püsiandmeid ei muudeta |
| **Staatuseriba** | Muudab Kavitro ülesande staatust ja proovib tööde põhikihti sünkroonida | Eraldi kinnitust ega automaatset tagasivõtmist ei ole |
| **Ava kirje brauseris** | Avab töö või teostusjoonise Kavitro ülesande veebivaate | Visuaal andmeid ei muuda |
| **Seosta kinnistuid / Näita seotud kinnistuid kaardil** | Seoseta olekus võib pärast ülevaate kinnitamist lisada Kavitro kinnistuseoseid; seosega olekus kuvab seotud kinnistud ja fokuseerib mooduli põhikihi objekti | Seostamist selle töövooga tagasi võtta ei saa; kaardil näitamine püsiandmeid ei muuda |
| Töö **Lisa uus töö** | Loob Kavitro ülesande, geomeetria ja QGIS-i tööpunkti ning proovib lisada kinnistuseose | Sammud ei ole ühine tehing |
| Töö **Lisa punkt kaardile** | Lisab olemasolevale Kavitro tööle QGIS-i punkti ning saadab asukoha Kavitrosse | Sammud ei ole ühine tehing |
| Töö **Muuda asukohta** | Salvestab tööpunkti uue asukoha QGIS-i kihile; taustakuulaja võib saata selle Kavitrosse | Kihi redigeerimisseanss kinnitatakse kohe |
| **Kontrolli sidumata GIS töid** | Otsib QGIS-i kihilt sidumata punkte ja võimaldab neist Kavitro töid luua | Kontroll ise ei muuda andmeid; rea avamise järel algab loomistöövoog |
| Teostusjoonise **Lisa/uuenda märkmeid** | Asendab Kavitro ülesande kirjelduse struktureeritud märkmete jaotise | Enne **Salvesta** vajutamist saab katkestada |
| Teostusjoonise **Joonista uus seotud objekt kaardile** | Lisab QGIS-i objekti, kirjutab atribuudid ja saadab geomeetria Kavitrosse | QGIS-i ja Kavitro muudatused ei ole ühine tehing |
| **Seosta kinnistuid** | Lisab Kavitro ülesandele kinnistuseoseid | Selle töövooga seoseid eemaldada ei saa |

Tööde ja teostusjooniste Kavitro kirjed on tehniliselt ülesanded. Seetõttu kasutavad kirjeldus, failid, staatus, geomeetria, veebiaadress ja kinnistuseosed ülesannete teenusetoiminguid.

## … Detailne ülevaade

Kirjekaardi alumises servas olev `…` nupp laiendab ja ahendab detaili sama kaardi sees. Teise kirjekaardi detaili avamine ahendab varem avatud kaardi.

Detail luuakse alles esimesel avamisel:

- kirjeldus laaditakse ülesande üksikkirje päringuga;
- failid laaditakse ülesande failidena, kuni 200 faili, 50 faili kaupa;
- kokkuvõttes kuvatakse kuni viis uusimast vanimani järjestatud faili;
- failinime või pildi eelvaate ikooni klõps avab failieelvaate;
- ülejäänud failide arv kuvatakse tekstina, kuid detailis puudub nupp täieliku failihalduse avamiseks.

Detail jääb kirjekaardi eluea jooksul vahemällu. Ahendamine ja uuesti avamine ei laadi kirjeldust ega faile uuesti. Värske seisu jaoks värskenda mooduli loendit.

Kirjelduse laadimine ja failipäring toimuvad detaili loomise ajal kasutajaliidese lõimes. Aeglase ühenduse korral võib avamine näida hangumisena. Failipäringu viga kuvatakse detailis, kuid kirjelduse päringu erindil ei ole samasugust kohalikku veakäsitlust.

## Staatuseriba

Töö ja teostusjoonise kirjekaardi vasakus servas on kitsas värviline staatuseriba. Hiirega ribale liikudes kuvatakse staatuse nimi. Vasakklõps avab valiku ainult siis, kui kirjekaardil on kirje ID.

Valikus kuvatakse kuni 100 kõigile ülesannetele määratud staatust, mitte ainult mooduli seadistustes eelistatud staatuseid. Praegune staatus on visuaalselt esile tõstetud.

Uue staatuse valimisel:

1. menüü sulgub ja riba näitab laadimisolekut;
2. Kavitro ülesande staatus uuendatakse kohe, ilma eraldi kinnitusküsimuseta;
3. ülesanne laaditakse võimaluse korral uuesti;
4. kirjekaart ehitatakse värskete andmetega uuesti;
5. käivitatakse tööde põhikihi üksikkirje sünkroonimine.

Sama või tühja staatuse valimine ei tee midagi. Teenuse vea korral taastatakse kaardil varasem staatus ja kuvatakse hoiatus.

### QGIS-i kihi sünkroonimise erinevus

Töö staatuse muutmisel võib taustas uueneda tööde põhikihi `ext_job_state`, detailne ülesandeinfo ja teenusest tulnud geomeetria. Kui tööde kiht on juba redigeerimisrežiimis, jäetakse sünkroonimine vahele. Kihi sünkroonimise ebaõnnestumine logitakse, kuid kasutajale ei kuvata eraldi hoiatust.

Teostusjoonise staatuse muutmisel käivitab praegune kood samuti tööde kihi sünkroonimisteenuse, mitte teostusjooniste kihi uuendamise. Tavaliselt ei leita tööde kihilt sama ID-ga objekti ning teostusjooniste põhikihi `ext_job_state` jääb muutmata. Kavitro ülesande staatus ja kirjekaart võivad sellest hoolimata õigesti uueneda.

## Ava kirje brauseris

Tööde ja teostusjooniste kirjekaartidel puudub **Ava kaust** nupp. **Ava kirje brauseris** koostab mõlema mooduli puhul ülesande veebiaadressi ning avab selle operatsioonisüsteemi vaikebrauseris.

Nupp on aktiivne kirje ID olemasolul. Puuduva veebibaasaadressi, vigase aadressi või brauseri avamisvea korral õnnestumise ega vea dialoogi ei kuvata; probleem jääb logisse.

Veebivaadet on vaja ka täielikuks failihalduseks, sest tööde ja teostusjooniste **Rohkem toiminguid** menüüs eraldi **Failid** toimingut ei ole.

## Seosta kinnistuid / Näita seotud kinnistuid kaardil

Toimingul on kaks olekut. Kinnistuseoseta kirjel kuvatakse seostamisikoon kohtspikriga **Kinnistuseos puudub – seosta kinnistuid** ja klõps käivitab olemasoleva kaardivaliku ning ülevaatedialoogi. Vähemalt ühe seose korral kuvatakse kaardiikoon kohtspikriga **Näita seotud kinnistuid kaardil**. Eduka seostamise järel vahetub ainult sama kaardi nupp kohe kaardiikooniks; tühistamine või viga jätab selle seostamisolekusse.

Klõpsamisel tehakse kaks sõltumatut sammu:

1. Kavitrost laaditakse lehekülgede kaupa kõik ülesandega seotud katastritunnused ning leitavad kinnistud valitakse kinnistute põhikihil;
2. mooduli põhikihilt otsitakse kirje ID-ga objekt, kiht tehakse nähtavaks ja leitud objektile suumitakse.

Töö puhul proovitakse ID-välju `ext_works_id`, `ext_job_id`, `ext_id` ja `external_id`; teostusjoonisel `ext_asbuilt_id`, `ext_job_id`, `ext_id` ja `external_id`. Esimene kihil olemas olev kandidaat valitakse identifikaatoriväljaks.

Toiming võib anda osalise tulemuse: näiteks kinnistud võivad avaneda, kuigi tööpunkti ei leita. Puuduv kiht, väli või objekt ei tekita koondhoiatust. Varasemat aktiivset kihti, objektivalikut ega kaardiulatust ei taastata.

Töö või teostusjoonise põhikihi objekti fokuseerimine toimub seotud kinnistute näitamise lisasammuna. Seoseta kirje seostamisikoon käivitab selle asemel kinnistute seostamise.

## Tööde Rohkem toiminguid

Töö kirjekaardi menüü sisaldab selles järjekorras:

1. **Lisa punkt kaardile**;
2. **Muuda asukohta**;
3. **Seosta kinnistuid**.

Menüütoiminguid ei peideta puuduva kihi, välja ega õiguse järgi. Vajalik kontroll toimub alles pärast toimingu valimist.

## Lisa uus töö

Nupp asub tööde loendi filtrirea paremas osas ning sama töövoogu saab käivitada ka QGIS-i kaardipaani **Lisa uus töö** nupuga.

### Punkti valimine ja katkestamine

Toiming kontrollib seadistatud tööde põhikihti, peidab või minimeerib Visuaali akna ja aktiveerib ristkursori.

- Vasakklõps valib tööpunkti ja avab loomise vormi.
- Paremklõps või `Esc` katkestab ning taastab Visuaali akna.
- Muu QGIS-i tööriista käsitsi aktiveerimine ei kutsu kontrolleri katkestust; Visuaali aken võib jääda kaardivaliku olekusse kuni järgmise lõpetava toiminguni.

Klikitud kohast otsitakse kinnistute põhikihi objekti. Kinnistu puudumine ei takista vormi avamist ega töö loomist.

### Vormi Tühista

**Tühista** sulgeb vormi ja ühtegi Kavitro ülesannet ega QGIS-i punkti ei looda. Kaardipunkti valimist tuleb uueks katseks alustada uuesti.

### Vormi Lisa uus töö

Nupp on keelatud, kui seadistuste eelistatud liikide ja teenusest laaditud tööliikide ühisosas pole ühtegi valikut. Vajutamisel kontrollitakse ainult töö liiki ja pealkirja; kirjeldus, prioriteet, vastutaja ning staatus võivad jääda tühjaks, kui vastav valik seda võimaldab.

Pealkirja pakutakse leitud kinnistu nime ja valitud tööliigi kombinatsioonina kuni kasutaja pealkirja käsitsi muudab. Alguskuupäevaks saadetakse tänane päev ja tähtajaks tänasest seitse päeva.

Kinnitamisel toimub:

1. Kavitro ülesanne luuakse koos kirjelduse, valitud staatuse ja punktgeomeetriaga;
2. vajaduse korral proovitakse staatust teise päringuga uuesti seada ja geomeetria värvi värskendada;
3. QGIS-i tööde põhikihile lisatakse punkt ja tööväljad;
4. klikitud kinnistu olemasolul proovitakse lisada kinnistuseos;
5. tööde loend ja kihi sünkroonimine käivitatakse uuesti.

Need sammud ei ole ühine tehing. Kavitro ülesanne võib jääda alles, kui punkti lisamine või kinnistu seostamine hiljem ebaõnnestub.

### Olemasolev redigeerimisseanss

Kui tööde kiht ei olnud redigeerimisrežiimis, alustab Visuaal seansi ja kinnitab lisatud punkti. Kui kiht oli juba redigeerimisrežiimis, jääb punkt muutmispuhvrisse, kuid Kavitro ülesanne ja geomeetria on selleks ajaks juba salvestatud. Kasutajale võidakse siiski kuvada täieliku õnnestumise teade.

Lisamise erindiharus võib kood kutsuda `rollBack()` ka varem avatud redigeerimisseansile. Seetõttu salvesta või tühista enne nupu kasutamist muud ootel tööde kihi muudatused.

## Kontrolli sidumata GIS töid

Kaardipaani nupp skannib tööde põhikihi kasutajaliidese lõimes. Kontrolli ajal kuvatakse ilma katkestamisnuputa edenemisaken või nupu juures edenemismull.

Sidumata objekt peab:

- olema mittetühja geomeetriaga;
- omama tühja `ext_job_id` väärtust;
- omama tühja `ext_system` väärtust.

Kui tingimustele vastavaid objekte pole, kuvatakse infoteade. Leitud read kuvatakse ühekaupa valitavas tabelis; esimene rida on automaatselt valitud.

### Dialoogi Tühista

**Tühista** sulgeb loendi andmeid muutmata. Skannimine on selleks ajaks juba toimunud, kuid Kavitro ülesannet ei looda.

### Ava valitud ja topeltklõps

**Ava valitud** ning tabelirea topeltklõps fokuseerivad QGIS-i objekti ja avavad selle andmetega eeltäidetud töö loomise vormi. Kui objekti, geomeetriat või punkti enam ei leita, jääb dialoog avatuks ja kuvatakse hoiatus.

Vormi **Tühista** jätab GIS-objekti sidumata ning sidumata tööde dialoog jääb avatuks. Eduka või osaliselt eduka loomise korral kirjutatakse uue ülesande ID samale QGIS-i objektile ja dialoog sulgub. Kavitro ülesanne luuakse enne kihiobjekti uuendamist, mistõttu võib kihi salvestusvea järel tekkida teenuses uus ülesanne, kuigi GIS-objekt jäi sidumata.

## Lisa punkt kaardile

Toiming on mõeldud olemasolevale Kavitro tööle, millel ei ole tööde põhikihis sama `ext_job_id` väärtusega punkti.

Kui punkt on juba olemas, uut objekti ei lisata: olemasolev punkt valitakse, sellele suumitakse ja kuvatakse infoteade. Muul juhul aktiveeritakse sama ristkursori tüüpi kaardivalik nagu uue töö loomisel. Paremklõps ja `Esc` katkestavad.

Pärast vasakklõpsu:

1. laaditakse võimaluse korral ülesande värsked andmed;
2. QGIS-i põhikihile lisatakse punkt ja töö atribuudid;
3. punktgeomeetria saadetakse Kavitro ülesandele;
4. klikitud kinnistu seotakse võimaluse korral ülesandega.

QGIS-i punkt salvestatakse enne eraldi geomeetriapäringut. Geomeetriapäringu tagastusväärtust ei kontrollita ja selle vale-tulemust ei kuvata kasutajale. Seetõttu võib nupp näidata edu ka siis, kui Kavitro geomeetria jäi uuendamata.

Juba redigeeritaval kihil jääb uus punkt ootele. Erind võib sama kihi kogu varasema redigeerimisseansi tagasi pöörata, mistõttu lõpeta enne toimingut muud ootel muudatused.

## Muuda asukohta

Toiming vajab põhikihil üheselt leitavat sama `ext_job_id` väärtusega tööpunkti. Olemasolev punkt valitakse ja sellele suumitakse, seejärel saab vasakklõpsuga valida uue asukoha. Paremklõps või `Esc` katkestab ilma geomeetriat muutmata.

Vasakklõps kirjutab uue geomeetria tööde kihile ja kutsub alati `commitChanges()`. See tähendab, et juba redigeeritava kihi korral kinnitatakse lisaks tööpunktile kõik sama kihi ootel muudatused. Kinnitamisvea korral saab Visuaal automaatselt tagasi pöörata ainult enda alustatud seansi.

Tööde mooduli sünkroonimisteenus kuulab kinnitatud geomeetriamuudatusi ja proovib saata uue asukoha Kavitrosse. Nupu eduteade kinnitab QGIS-i kihi salvestamist; teenuse geomeetriauuenduse viga logitakse ja kasutaja ei pruugi eraldi hoiatust saada.

Toimingu lõpus eemaldatakse tööde kihilt objektivalik, seega algselt fokuseeritud punkt ei jää valituks.

## Töö kinnistute seostamine

**Seosta kinnistuid** kasutab sama ühist lisavat töövoogu nagu teostusjoonised ja teised moodulid.

1. Olemasolevad seosed laaditakse Kavitrost ja näidatakse võimaluse korral kaardil.
2. Kasutaja valib kinnistute põhikihilt ristkülikuga ühe või mitu objekti.
3. Ülevaatedialoog näitab olemasolevaid ja uusi valikuid.
4. **Kinnita** lahendab valitud katastritunnustele kinnistu ID-d ning saadab need ülesande `associate` toiminguna.

Töövoog ainult lisab seoseid. **Vali uuesti** käivitab uue valiku, **Tühista** ei lisa midagi ja **Kinnita** ei eemalda ega asenda olemasolevaid seoseid.

Kinnistu-ID lahendamise või seostamise erind võib väljuda nupukäsitlejast ilma kasutajasõbraliku veadialoogita. Objektita `Esc`-katkestamine, paremklõps või tööriistavahetus ei taasta ühises ristkülikvalikus alati Visuaali akent.

## Teostusjooniste Rohkem toiminguid

Teostusjoonise kirjekaardi menüü sisaldab selles järjekorras:

1. **Lisa/uuenda märkmeid**;
2. **Joonista uus seotud objekt kaardile**;
3. **Seosta kinnistuid**.

Menüüs ei ole **Failid**, olemasoleva objekti sidumise ega geomeetria muutmise toimingut. Teostusjoonise hilisem QGIS-i geomeetriamuudatus ei sünkroonitu automaatselt Kavitrosse.

## Lisa/uuenda märkmeid

Toiming laadib Kavitro ülesande kirjelduse ja otsib sellest Visuaali struktureeritud jaotist **Märkused ja kommentaarid**. Muu vabatekst ei muutu märkmeridadeks.

Kui struktureeritud märkmeid pole, lisatakse dialoogi üks tänase kuupäevaga tühi rida. Read rühmitatakse nende salvestatud kuupäevateksti järgi; rühmade ega olemasolevate ridade kuupäeva dialoogis muuta ei saa.

### Lisa märkus

Nupp lisab tänase kuupäeva rühma uue tühja rea. Uut Kavitro päringut ega salvestust veel ei tehta.

### Rea Kustuta

Nupp eemaldab rea dialoogist kohe ja kinnitusküsimuseta. Kustutamine jõuab Kavitrosse alles **Salvesta** järel. Kui rühm jääb tühjaks, eemaldatakse ka selle pealkiri.

### Lahendatud märkeruut

Kuigi märkeruut ei ole eraldi nupp, mõjutab see salvestatavat tulemust: märkimisel täidetakse tühi lahendamiskuupäev tänase kuupäevaga ja märke eemaldamisel kuupäev tühjendatakse. Käsitsi sisestatud kuupäeva vormingut ei valideerita.

### Tühista

**Tühista** sulgeb dialoogi ning jätab Kavitro kirjelduse muutmata. Dialoogis tehtud rea lisamised, kustutamised ja muudatused kaovad.

### Märkmete Salvesta

Enne salvestamist laaditakse ülesande kirjeldus uuesti. Visuaal asendab selles ainult struktureeritud märkmete jaotise ning proovib muu vahepeal muutunud sisu säilitada.

Täiesti tühi rida jäetakse välja. Kõigi sisuliste ridade eemaldamisel kustutatakse kirjeldusest märkmete jaotis. Märkmetekst teisendatakse HTML-is ohutuks tekstiks ja reavahetused säilitatakse.

Kui uus tulemus võrdub uuesti laaditud kirjeldusega, sulgub dialoog ilma salvestuspäringu ja teateta. Edu korral uuendatakse Kavitro ülesande `description` ning kuvatakse infoteade; vea korral hoiatus.

Kui nii avamisel kui ka enne salvestamist kirjelduse laadimine ebaõnnestub, käsitleb kood lähtekirjeldust tühjana. Järgnev edukas salvestus võib seetõttu asendada tegeliku kirjelduse ainult märkmete tabeliga. Laadimisvea kohta eraldi teadet ei kuvata.

## Joonista uus seotud objekt kaardile

Toiming kontrollib seadistatud teostusjooniste vektorkihti ja lisab vajaduse korral standardsed väljad `ext_job_id`, `ext_system`, `ext_job_name`, `ext_job_type`, `ext_job_state`, `added_by`, `added_date`, `updated_by` ja `update_date`.

Puuduvate väljade lisamine võib käivitada ja kohe kinnitada eraldi kihiskeemi redigeerimise. Kui kiht oli juba redigeerimisrežiimis, jäävad lisatud väljad selle olemasolevasse seanssi.

Seejärel:

1. põhikiht tehakse nähtavaks ja aktiivseks;
2. vajaduse korral alustatakse redigeerimisrežiimi;
3. QGIS-i tavaline atribuudivorm surutakse ajutiselt maha;
4. käivitatakse QGIS-i **Lisa objekt** tööriist;
5. esimese lisatud objekti järel avaneb **Teostusjoonise andmed** vorm.

Toiming ei kontrolli enne joonistamist, kas sama `ext_job_id` objekt on kihil juba olemas. Korduv kasutamine võib luua ühe Kavitro kirje jaoks mitu QGIS-i objekti.

### Joonistamise katkestamise risk

Kontroller ei kuula eraldi QGIS-i lisamistööriista `Esc`-katkestust ega tööriista vahetamist. Kui kasutaja katkestab enne objekti loomist, võib `featureAdded` kuulaja jääda aktiivseks. Järgmine samale kihile hiljem lisatud kõrvaline objekt võidakse siduda varem valitud teostusjoonisega.

Ohutu katkestusviis praeguses versioonis on lõpetada loodav geomeetria ja vajutada seejärel andmevormil **Katkesta**, eeldusel et põhikiht ei olnud enne töövoogu redigeerimisrežiimis.

## Teostusjoonise andmevorm

Vormil saab sisestada töö numbri, objekti, mõõdistamise kuupäeva, mõõdistaja, kontakti, joonise liigi, mõõtkava, koordinaat- ja kõrgussüsteemi, võrguliigid ning märkused.

Töö numbri vaikeväärtus tuleb kirje numbrist või ID-st, objekti vaikeväärtus kirje nimest. Mõõdistamise kuupäev on tänane päev. **Salvesta** ei kontrolli kohustuslikke tekstivälju; ka tühi töö number ja objekt on lubatud.

Vormi väärtus kirjutatakse ainult siis, kui põhikihil on täpselt sobiva nimega väli. Valdkonnavälju nagu `Töö nr`, `Objekt` ja `Mõõdistaja` automaatselt ei looda. Väli **Võrgu piirkond** on koodis defineeritud, kuid vorm ei küsi ega kirjuta sellele väärtust.

### Katkesta

Nupp tagastab joonistamise käsitlejale vea-tulemuse ning kasutajale kuvatakse salvestamise ebaõnnestumise hoiatus.

- Kui Visuaal alustas redigeerimisseansi, pööratakse seanss tagasi ja äsja joonistatud objekt eemaldatakse.
- Kui kiht oli enne töövoogu juba redigeerimisrežiimis, ei pööra Visuaal objekti tagasi ning sidumata geomeetria võib muutmispuhvrisse alles jääda.

Seega ei käitu **Katkesta** kasutaja jaoks vaikse tavakatkestusena.

### Andmevormi Salvesta

Nupp ei salvesta kohe, vaid tagastab vormiväärtused joonistamise töövoole. Seejärel:

1. QGIS-i objektile kirjutatakse ülesande ID, nimi, liik, staatus, auditiväljad ja olemasolevad vormiväljad;
2. kontrollitakse, et sama objekt on kihilt ID või nime järgi leitav;
3. objekti geomeetria teisendatakse teenuse payload'iks;
4. geomeetria saadetakse Kavitro ülesandele;
5. Visuaali alustatud redigeerimisseanss kinnitatakse;
6. objekt valitakse ja sellele suumitakse.

Kui kiht oli juba redigeerimisrežiimis, jäävad QGIS-i objekt ja atribuudid ootele, kuid Kavitro geomeetria saadetakse kohe. Hilisem QGIS-i tagasipööramine võib seetõttu jätta teenuse ja kihi eri seisu.

Kavitro geomeetria saadetakse enne Visuaali alustatud kihi lõplikku kinnitamist. Kui teenuse päring õnnestub, kuid hilisem `commitChanges()` ebaõnnestub, võib Kavitro geomeetria jääda alles ja QGIS-i objekt kaduda.

## Teostusjoonise kinnistute seostamine

Töövoog on sama mis töödel: olemasolevad seosed kuvatakse kontekstiks, ristkülikuga valitud kinnistud vaadatakse üle ja **Kinnita** saadab leitud kinnistu ID-d ülesande `associate` toiminguna.

See toiming ainult lisab kinnistuseoseid. See ei seo joonistatud geomeetriat kinnistuga, ei eemalda varasemaid seoseid ega kasuta valikust väljajäänud kinnistuid eemaldamisloendina.

## Auditi käigus leitud parandamist vajavad kohad

| Prioriteet | Leid | Kasutajarisk | Soovitatav parandus |
|---|---|---|---|
| Kriitiline | Teostusjoonise joonistuskontroller ei lõpeta `featureAdded` kuulamist objekti loomisele eelneva `Esc`-katkestuse ega tööriistavahetuse korral | Hilisem kõrvaline objekt võidakse siduda vale teostusjoonisega | Kuula kaarditööriista deaktiveerimist ja katkestust ning lõpeta kontroller kindlalt |
| Kriitiline | Tööde kihi lisamise erindiharu võib pöörata tagasi ka kasutaja varem avatud redigeerimisseansi | Nupuga mitteseotud ootel kihimuudatused võivad kaduda | Kutsu `rollBack()` ainult Visuaali enda alustatud seansile või kasuta eraldatud edit command'i |
| Kõrge | **Muuda asukohta** kinnitab alati kogu tööde kihi redigeerimisseansi | Koos tööpunktiga salvestuvad ootamatult muud ootel muudatused | Kinnita ainult enda alustatud seanss või hoiata ja keela toiming aktiivse seansi korral |
| Kõrge | Teostusjoonise staatuse järel sünkroonitakse tööde, mitte teostusjooniste põhikihti | Kavitro staatus ja teostusjoonise `ext_job_state` jäävad eri seisu | Vali sünkroonimisteenus mooduli järgi ja lisa teostusjooniste atribuudisünkroon |
| Kõrge | **Lisa punkt kaardile** ei kontrolli geomeetriauuenduse `False` tulemust | QGIS-i punkt võib olla olemas ja kuvada edu, kuigi Kavitro asukoht ei muutunud | Kontrolli vastust, näita osalise õnnestumise hoiatust ja paku kordussünkroonimist |
| Kõrge | Märkmete mõlema kirjelduse laadimise ebaõnnestumisel saab salvestada tühja lähtekirjelduse peale | Ülesande muu kirjeldus võib kaduda | Ära ava või salvesta märkmeid enne edukat kirjelduse laadimist; kuva selge veateade |
| Kõrge | Teostusjoonise QGIS-i ja Kavitro kirjutused ei ole ühine tehing | Teenuse geomeetria võib jääda ilma QGIS-i objektita või vastupidi | Kinnita kiht enne teenuse saatmist või lisa taastatav sünkroonimisvoog ja sammude koondtulemus |
| Keskmine | Teostusjoonise **Katkesta** kuvatakse salvestusveana | Kasutaja ei erista teadlikku katkestust tegelikust rikkest | Anna kontrollerile eraldi cancelled-tulemus ja sulge ilma veahoiatuseta |
| Keskmine | Uue teostusjoonise joonistamine ei kontrolli olemasolevat sama ID-ga objekti | Ühe kirje jaoks võivad tekkida duplikaatobjektid | Kontrolli ID-d enne lisamist ning paku olemasoleva objekti fokuseerimist või kinnitatud asendamist |
| Keskmine | Teostusjoonise salvestusjärgne kontroll otsib iga objekti juures ID-d ja seejärel nime | Kihis eespool olev sama nimega objekt võib põhjustada õige uue objekti kontrolli ebaõnnestumise | Otsi kogu kihilt esmalt ainult täpse ID järgi ning kasuta nime alles üheselt kontrollitud varuvariandina |
| Keskmine | Tööpunkti valiku- ja ümberpaigutustööriistad ei käsitle muu tööriista aktiveerimist katkestusena | Visuaali aken võib jääda kaardivaliku režiimi ja kontroller ootele | Kuula tööriista deaktiveerimist ning taasta aken ja pan-režiim |
| Keskmine | Staatuse valik ei piirdu mooduli eelistatud staatustega ja salvestab ilma kinnituseta | Kasutaja võib valida ootamatu ülesandestaatuse ühe klõpsuga | Piira loend lubatud töövooga või lisa enne muutmist kinnitamine |
| Keskmine | Tööde ja teostusjooniste menüüs puudub täieliku failihalduse toiming | Detailis näeb kuni viit faili, kuid kõiki faile ei saa Visuaalis hallata | Lisa kontrollitud `TaskFilesDialog` avav **Failid** toiming |
| Madal | Kaardinupu kohtspikker on ingliskeelne ning puuduv objekt annab vaikse tulemuse | Nupp võib näida mittetöötavana | Kasuta tõlkevõtit ja kuva leitud ning leidmata objektide koond |

## Soovituslik turvaline tööjärjekord

1. Lõpeta ja salvesta enne kaardile kirjutavat toimingut tööde või teostusjooniste põhikihi muud ootel redigeerimised.
2. Kontrolli, et õige mooduli põhikiht on seadistatud, projektis olemas ja kirjutatav.
3. Uue töö loomisel kontrolli pärast teadet eraldi Kavitro ülesannet, QGIS-i punkti ja kinnistuseost.
4. Olemasoleva töö punkti lisamisel või asukoha muutmisel kontrolli tulemust ka Kavitro veebivaates.
5. Teostusjoonise joonistamise katkestamisel kontrolli põhikihi redigeerimispuhvrit; ära lisa samale kihile kõrvalisi objekte enne, kui pooleliolev kontroller on kindlalt lõpetatud.
6. Teostusjoonise salvestamise järel kontrolli nii QGIS-i objekti `ext_job_id` kui ka Kavitro geomeetriat.
7. Märkmete dialoogis ära salvesta, kui olemasolev kirjeldus või märkmed ootamatult puuduvad; kontrolli kirjet esmalt veebivaates.
8. Kasuta **Seosta kinnistuid** ainult lisamiseks ja kontrolli eemaldamisvajadus Kavitro veebirakenduses.

## Seotud juhendid

- [Tööde ja teostusjooniste nupud](08_toode_ja_teostusjooniste_nupud.md)
- [Tööde mooduli kaarditoimingud](../11_toode_mooduli_kaarditoimingud.md)
- [Teostusjooniste mooduli kasutamine](../12_teostusjooniste_mooduli_kasutamine.md)
- [Tööde ja teostusjooniste mooduli seadistamine](../09_toode_ja_teostusjooniste_seadistamine.md)
- [Filtrite nuppude detailaudit](02_01_filtrite_nuppude_detailaudit.md)
- [Failide ja ühisdialoogide nupud](09_failide_ja_uhisdialoogide_nupud.md)
