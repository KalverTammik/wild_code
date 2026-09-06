# Wild Code välisauditi otsused

See dokument täiendab faili `wild-code-audit-external.html`, mis säilib muutmata kujul auditi algse hetkepildina. Siia kantakse pärast koodi kontrollimist tehtud rakendus- ja riskiaktsepteerimise otsused.

## WC-07 — autentimiskirje säilimine pärast väljalogimist

**Otsuse kuupäev:** 2026-09-03  
**Staatus:** aktsepteeritud madal jääkrisk  
**Seotud parandus:** Etapp 2A, commit `d2cb04d`

### Kontrollitud tegelik käitumine

- Kavitro juurdepääsutõend salvestatakse QGIS Authentication Manageri kaitstud autentimiskirjesse.
- Tavaseadetes säilib ainult autentimiskirje tunnus, kasutajanimi ja sessiooni olek; avatekstis tokenit ei säilitata.
- Kavitro parooli ega vana API-võtit autentimiskirjes ei säilitata.
- Väljalogimine eemaldab aktiivse tokeni mälust, kustutab aktiivse kasutajasessiooni ja määrab `session/needs_login` oleku.
- Allesjäänud autentimiskirjet ei taastata pärast väljalogimist automaatselt. Kavitro nõuab järgmisel avamisel uut sisselogimist.
- Käsitsi kontroll kinnitas, et alles on üks aktiivne `Kavitro session` kirje, selles on token ning puuduvad väljad `password` ja `apikey`.

### Otsuse põhjendus

QGIS Authentication Manager on QGIS-i standardne tundlike autentimisandmete hoidla. Selle autentimisandmebaasi kaitseb master-parool ning tavaseadetesse salvestatav konfiguratsiooni tunnus ei avalda kaitstud väärtust. Seetõttu käsitletakse allesjäävat tokenit turvaliselt salvestatud autentimisandmena, mitte avateksti lekkega.

Väljalogimise järel ei kasuta Kavitro allesjäänud kirjet aktiivse sessiooni taastamiseks. Autentimiskirje kustutamine oleks täiendav kaitsemeede, kuid ei ole praeguse ohumudeli järgi kohustuslik parandus.

### Teadaolev jääkrisk

Kui QGIS-i master-parool on aktiivse QGIS-i käivituse ajal avatud, võivad sama kasutaja õigustes töötavad PyQGIS-i pluginad autentimishaldurile ligi pääseda. See on QGIS-i autentimissüsteemi üldine usaldusmudel ning puudutab ka teisi sinna salvestatud ühendusi.

Serveris võib eemaldamata bearer-token kehtida kuni serveripoolse aegumise või tühistamiseni. Tokeni aegumise, värskendamise ja serveripoolse tühistamise elutsükkel käsitletakse eraldi autentimisetapis.

### Otsuse uuesti avamise tingimused

WC-07 tuleb uuesti hinnata, kui vähemalt üks järgmistest tingimustest muutub:

- Kavitrot kasutatakse jagatud QGIS-i profiiliga arvutites, kus väljalogimine peab eemaldama kõik kohalikud autentimisandmed;
- turvanõue määratleb **Logi välja** toimingu kohaliku autentimiskirje täieliku kustutamisena;
- QGIS Auth Manageri asemel võetakse kasutusele nõrgem või avatekstine hoidla;
- token muutub pika elueaga või server ei võimalda selle kehtivust piisavalt piirata;
- ilmneb realistlik ründemudel, kus teised samas QGIS-i protsessis töötavad pluginad ei ole usaldatud.

### Viited

- [QGIS Authentication System](https://docs.qgis.org/3.44/en/docs/user_manual/auth_system/auth_overview.html)
- [QGIS Authentication System — Security Considerations](https://docs.qgis.org/3.34/en/docs/user_manual/auth_system/auth_considerations.html)

## WC-09 — sisselogimismutatsiooni stringinterpolatsioon

**Otsuse kuupäev:** 2026-09-03  
**Staatus:** parandus teostatud ning automaatselt ja käsitsi valideeritud
**Seotud parandus:** commit `2492b0f`

Sisselogimismutatsioon viidi staatilisse faili `python/queries/graphql/user/login.graphql`. Kasutajanimi ja parool edastatakse nüüd GraphQL-i `LoginInput!` muutuja kaudu ning neid ei liideta päringudokumendi teksti.

Parandus säilitab senise vastuseväljade ja veakäsitluse lepingu. `refreshToken` ja `expiresIn` küsitakse endiselt vastuses, kuid nende elutsüklit selles etapis ei muudeta.

Automaattestid kontrollivad päringufaili lepingut, mandaatide puudumist päringudokumendist, erimärkide muutmata jõudmist JSON-muutujatesse ja autentimisheaderi puudumist login-päringul. Arenduskeskkonna GraphQL-endpoint kinnitas ilma resolverit käivitamata, et staatiline päring kasutab kehtivat `LoginInput!` sisendtüüpi.

Käsitsi kontroll kinnitas pärast plugina uuesti laadimist, et sisselogimine ja väljalogimine töötavad ootuspäraselt.

## WC-10 — release’i sisendite otsene interpolatsioon

**Otsuse kuupäev:** 2026-09-04
**Staatus:** parandus teostatud ning automaattestide ja GitHubi release’iga `v2.02.16` valideeritud

Release’i sündmuse tagi, manuaalse käivituse sisendeid ja valideeritud sammuväljundeid ei tohi lisada otse GitHub Actionsi `run:` skripti. Sisendid antakse keskkonnamuutujate kaudu testitavale resolverile, mis lubab ainult Kavitro release’i versiooni- ja tagivormingut. Järgmised sammud saavad kasutada ainult resolveri kontrollitud väljundeid ning samuti ainult keskkonnamuutujate kaudu.

Sama turvapiir peab kajastuma nii tegelikus `.github/workflows/qgis_release.yml` failis kui ka `MAIN_PLUGIN_RELEASE_SETUP.md` mallis.

Teostuses lahendab `tools/resolve_release_values.py` release’i sündmuse ja manuaalse käivituse väärtused, kontrollib need range lubatud vormingu järgi ning kirjutab ainult üherealised kontrollitud väärtused faili `GITHUB_OUTPUT`. Workflow’ `run:` plokkides ei ole pärast parandust GitHubi kontekstiavaldisi.

GitHubi release `v2.02.16` osutab parandust sisaldavale commit’ile `6ac7bf7`. Release-workflow lõppes edukalt ning avaldas oodatud `plugins.xml`, versioonitud ZIP-i ja ikooni, millega WC-10 sisendipiir on kontrollitud ka tegelikus avaldamisvoos.

## WC-11 — avaldatud plugina ZIP-i terviklus

**Otsuse kuupäev:** 2026-09-04
**Staatus:** parandus teostatud ning esimese immutable release’iga `v2.02.17` valideeritud

### Kontrollitud tegelik käitumine

- QGIS 3.40, QGIS 3.44 ja QGIS-i praegune plugina paigaldaja ei loe `plugins.xml` failist SHA-256 välja ega kontrolli ZIP-i kontrollsummat enne lahtipakkimist.
- Auditis soovitatud `<sha256>` elemendi lisamine `plugins.xml` faili ei annaks kaitset, sest QGIS eiraks seda.
- GitHub arvutab igale release-varale SHA-256 digesti. Release’i `v2.02.16` kõik kolm vara sisaldavad GitHubi API-s digesti, kuid release ise on `immutable: false`.
- Senine workflow käivitub pärast release’i avaldamist ning kasutab varade tagantjärele asendamiseks valikut `--clobber`. Selline järjekord ei ühildu lukustatud release’idega.

### Rakendusotsus

Release’i terviklus tagatakse GitHubi immutable release’i mehhanismiga, mitte QGIS-i poolt toetamata XML-elemendiga. Uus töövoog:

1. nõuab ettevalmistatud tühja draft-release’i;
2. loob või valideerib päris Git-tag’i täpselt workflow’ kontrollitud commit’il;
3. koostab `plugins.xml`, plugina ZIP-i ja ikooni enne avaldamist;
4. keelab avaldatud varade ülekirjutamise ning ei kasuta `--clobber` valikut;
5. võrdleb enne avaldamist iga kohaliku faili SHA-256 väärtust GitHubi vara digestiga;
6. avaldab draft’i alles pärast kontrollide õnnestumist;
7. kontrollib pärast avaldamist `immutable: true` väärtust, täpset tag’i nime, target-commit’i ja kõigi varade tag’ipõhiseid allalaadimis-URL-e.

LIVE-metaandmete lähteks kasutatakse `metadata.release.txt` faili. See väldib DEV-metaandmetest vana ikooni pärimist ning määrab release’i ikooniks `resources/icons/Kavitro-favicon-96x96.png`.

Enne immutable-protsessi aktiveerimist parandati ühekordselt olemasoleva release’i `v2.02.16` kataloogiikoon. Ainult release’i vara `kavitro_live.png` asendati valitud 96 × 96 Kavitro faviconiga; ZIP ja `plugins.xml` jäid muutmata. GitHubis oleva uue ikoonivara SHA-256 on `ed9ea0c499f6072eb95decc3cf607b426fe5844b5a1446c4dca0814321c970ac` ning see kattub repository failiga.

### Jääkrisk

Immutable release takistab juba avaldatud tag’i ja varade hilisemat muutmist. See ei välista pahatahtliku paketi koostamist enne avaldamist, kui GitHubi konto või build-workflow on juba kompromiteeritud. Build-sõltuvuste ja GitHub Actionsi õiguste tugevdamine käsitletakse WC-12 etapis.

QGIS Plugin Manager ei kontrolli GitHubi release-attestatsiooni ise. Kasutaja automaatse paigalduse usalduspiir jääb GitHubi HTTPS-ühendusele, repository õigustele ja release’i avaldamise protsessile.

### Kasutuselevõtu valideerimine

GitHubi repository seadistus **Enable release immutability** aktiveeriti 2026-09-04 pärast draft-first workflow jõudmist `main` harusse.

Esimese avaldamiskatse järelkontroll tuvastas GitHubi draft-release’i erijuhtumi: ilma päris Git-ref’i ja avaldamispäringus korratud `tag_name` väärtuseta võis GitHub lukustada release’i sisemise `untagged-*` nimega. Valesti märgistatud katserelease’id eemaldati ning kasutajatele mõeldud `v2.02.17` tag jäi vabaks. Workflow’d täiendati nii, et see loob Git-ref’i enne üleslaadimist, saadab avaldamisel `tag_name` ja `target_commitish` väärtused üheselt ning valideerib lõpliku release’i URL-id.

Release `v2.02.17` avaldati commit’ilt `d77ac74e58fe80ee81c6afc7cef6eb9b29b29928`. GitHub kinnitas `immutable: true`, release sisaldab täpselt `plugins.xml`, `kavitro_live.2.02.17.zip` ja `kavitro_live.png` vara ning kõik sisaldavad SHA-256 digesti. Avalik `plugins.xml` viitab versioonile `2.02.17` ja sama tag’i varadele. Käsk `gh release verify v2.02.17` valideeris release-attestatsiooni edukalt.

## WC-12 — release-workflow’ sõltuvused ja autentimisandmed

**Otsuse kuupäev:** 2026-09-05

**Staatus:** parandus teostatud ja automaattestidega valideeritud; tegelik avaldamisvoog valideeritakse järgmise release’iga

### Kontrollitud tegelik olukord

- Auditis kirjeldatud piiranguta `qgis-plugin-ci` paigaldamine ei olnud enam aktuaalne. WC-11 käigus asendati see repository enda standardteegi põhise pakkimisloogikaga ning release-workflow ei paigalda enam Pythoni pakette.
- `actions/checkout` ja `actions/setup-python` kasutasid endiselt muudetavaid major-versiooni viiteid `@v5` ja `@v6`.
- Checkout-samm ei määranud `persist-credentials` väärtust. Vaikeväärtuse `true` tõttu paigutati töövoo `GITHUB_TOKEN` lokaalsesse Git-konfiguratsiooni kuni checkout-action’i järeltegevuseni.
- Workflow vajab jätkuvalt `contents: write` õigust, sest loob Git-ref’i, laadib release’i varad üles ning avaldab kontrollitud draft-release’i.

### Rakendusotsus

- `actions/checkout` lukustati täispika commit SHA `fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09` külge, mis vastab versioonile `v5.1.0`.
- `actions/setup-python` lukustati täispika commit SHA `ece7cb06caefa5fff74198d8649806c4678c61a1` külge, mis vastab versioonile `v6.3.0`.
- Checkout-samm kasutab nüüd `persist-credentials: false`, sest hilisemad GitHub API toimingud saavad tokeni ainult neid vajavate sammude `GH_TOKEN` keskkonnamuutuja kaudu.
- Sama piir rakendati tegelikule workflow’le ja `MAIN_PLUGIN_RELEASE_SETUP.md` näidisele.
- Regressioonitest kontrollib mõlemas allikas lubatud SHA-sid, keelab major-tag’id, nõuab `persist-credentials: false` väärtust ning takistab `qgis-plugin-ci` või dünaamilise `pip install` sammu tagasitulekut.

`contents: write` õigus jäeti alles, sest selle eemaldamine katkestaks praeguse release-protsessi. Build- ja publish-õiguste eraldamine eri job’ideks jääb võimalikuks hilisemaks kaitsekihiks, kuid ei ole WC-12 sulgemiseks vajalik.

### Jääkrisk ja kasutuselevõtu kontroll

Täispikk SHA muudab action’i lähtekoodi viite muutumatuks, kuid uuele action’i versioonile üleminek peab edaspidi toimuma teadliku SHA uuenduse ja testimise kaudu. Workflow käib jätkuvalt GitHubi majutatud `ubuntu-latest` runneril ning avaldamissammudel on tööks vajalik kirjutamisõigus.

Staatilised regressioonitestid valideerivad usalduspiiri repository tasemel. Järgmise tavapärase release’i õnnestumisel tuleb siia lisada release’i versioon ja kinnitada, et SHA-dega lukustatud action’id läbisid täieliku immutable avaldamisvoo.

## WC-13 — HTTP veavastuste sisu logimine

**Otsuse kuupäev:** 2026-09-05

**Staatus:** parandus teostatud ning QGIS 3.40 testikeskkonnas valideeritud

### Kontrollitud tegelik olukord

- `APIClient.send_query` ja `APIClient.send_multipart_query` lisasid 4xx HTTP vastuse kogu `response.text` sisu erindi sõnumisse. 401, 403 ja 5xx vastused olid juba piiratud üldise vealiigi või HTTP olekukoodiga.
- API erindid võisid jõuda muutmata kujul nii `PythonFailLogger` logisse kui ka taustatöö `SwitchLogger` logisse.
- Logikataloogid ja failid loodi vaikimisi õigustega. Tegelik ligipääs sõltus operatsioonisüsteemist, kasutajaprofiili ACL-ist ja POSIX-süsteemides protsessi `umask` väärtusest.
- Kontrollitud Windowsi kasutajaprofiilis puudus üldine `Everyone` või `Users` lugemisõigus, kuid rakendus ei jõustanud ise sama kaitsepiiri kõigil toetatud platvormidel.

### Rakendusotsus

- Mittestandardse HTTP vastuse keha ei loeta enam veateate koostamiseks ega edastata kasutajaliidesesse, erindisse või logisse.
- Diagnostikaks säilib ainult ohutu HTTP olekukood tõlgitavas teates `Serveri päring ebaõnnestus (HTTP {status_code})`.
- Tavapärase HTTP 200 GraphQL-vastuse `errors` väljade senist käsitlust selles etapis ei muudetud. Need on rakendustaseme vead, mitte WC-13 kirjeldatud täieliku HTTP vastuse logimine.
- Lisati ühine `Logs/secure_log_io.py` abimoodul. Uued logikataloogid luuakse õigusega `0700` ja logifailid õigusega `0600`; POSIX-süsteemides parandatakse ka olemasolevate kasutatavate kataloogide ja failide õigused.
- Turvaline faili avamine kasutab append-režiimi ega kirjuta varasemat logi üle. Toetatud platvormil kasutatakse ka `O_NOFOLLOW` lippu, et logifaili avamisel mitte järgneda sümboolsele lingile.
- `PythonFailLogger` ja `SwitchLogger` kasutavad mõlemad sama turvalise logifaili piiri. Windowsis rakendub uue kataloogi `0700` ACL Python 3.13-st; vanemates QGIS-i Pythoni versioonides päritakse kasutajaprofiili NTFS-õigused.

### Valideerimine ja jääkrisk

Regressioonitestid kontrollivad mõlemat API veateed 422 vastusega, mille keha sisaldab näilist juurdepääsutõendit. Nii tavalises kui ka failiga päringus säilib `HTTP 422`, kuid vastuse keha ega `accessToken` tekst ei jõua tagastatud veasse. Staatiline test takistab `response.text` kasutuse tagasitulekut ning kontrollib, et mõlemad faililogijad kasutaksid turvalist I/O abimoodulit.

QGIS 3.40.13 Pythoni keskkonnas läbis kogu komplekt 103 testi; kaks platvormi- või keskkonnaspetsiifilist testi jäeti vahele. POSIX-i `0700` ja `0600` õiguste test käivitub Linuxi CI-s või muus POSIX-keskkonnas.

Jääkriskina võivad tavapärased GraphQL-i rakendustaseme veateated endiselt logisse jõuda. Backend ei tohiks neisse lisada paroole, tokeneid ega muid saladusi. Crash-logi loomise viis failis `main.py` ei kuulu WC-13 parandusse ja hinnatakse eraldi WC-14 etapis.

## WC-14 — crash-logi turvaline loomine ja elutsükkel

**Otsuse kuupäev:** 2026-09-06

**Staatus:** parandus teostatud ning QGIS 3.40 testikeskkonnas valideeritud

### Kontrollitud tegelik olukord

- `main.py` avas juba mooduli importimisel fikseeritud nimega `%TEMP%/kavitro_crash.log` faili kirjutusrežiimis. Iga import kärpis eelneva faili nullbaidiseks ning jagatud ajutises kataloogis võis fikseeritud nimi võimaldada sümboolse lingi kaudu teise faili kärpimist.
- Moodul hoidis faili globaalses `_CRASH_LOG_HANDLE` muutujas, kuid ei kutsunud plugina mahalaadimisel `faulthandler.disable()` ega sulgenud käepidet.
- QGIS-i testikomplekt kinnitas elutsüklivea `ResourceWarning: unclosed file` hoiatusega.
- Kontrollitud Windowsi `%TEMP%/kavitro_crash.log` oli nullbaidine ning kasutajaprofiili ACL-iga piiratud. WC-14 üldine risk tulenes eelkõige plugina platvormiülesest käitumisest ja jagatud POSIX-i ajutistest kataloogidest.

### Rakendusotsus

- Mooduli impordi kõrvalmõju eemaldati `main.py` failist täielikult. Crash-logimine käivitub nüüd alles `WildCodePlugin.initGui()` lõpus ja lõpetatakse `unload()` käigus.
- Lisati eraldiseisev `Logs/crash_logger.py`, mis loob sessioonipõhise juhusliku nimega faili turvalises `Logs/CrashLogs` kataloogis. Fail luuakse `tempfile.mkstemp()` abil atomaar­selt ja ainult loojale ligipääsetavana.
- Crash-logger ei kirjuta üle QGIS-i või teise komponendi juba aktiveeritud `faulthandler` seadistust. Käivitamine on idempotentne ning logger lülitab välja ainult enda käivitatud handler’i.
- `faulthandler` keelatakse enne faili sulgemist. Kui keelamine ebaõnnestub, jäävad omandiinfo ja avatud käepide alles, et vältida aktiivse handler’i suunamist suletud või hiljem taaskasutatud failideskriptorile.
- Tavapärasel sulgemisel eemaldatakse nullbaidine sessioonifail. Sisuga crash-logi säilib ning logger hoiab alles kuni kolm viimast mittetühja faili.
- `CrashLogger.latest_log_path()` võimaldab leida uusima säilinud faili selle sisu avamata. Failid jäävad kasutaja ja sama töökausta õigustes töötava diagnostika jaoks loetavaks.
- Vana fikseeritud `%TEMP%/kavitro_crash.log` faili ei avata, kärbita, migreerita ega kustutata. Kontroll kinnitas, et selle muutmisaeg ei muutunud uute testide käigus.

### Valideerimine ja jääkrisk

Regressioonitestid kontrollivad juhuslikku sessioonifaili, idempotentset käivitamist, korrektset sulgemist, tühja faili eemaldamist, sisuga faili säilitamist, kolme faili rotatsiooni, uusima logi leidmist, olemasoleva host-handler’i austamist, keelamise tõrke korral käepideme säilitamist ning vana fikseeritud ajutise faili puutumatust.

QGIS 3.40.13 Pythoni keskkonnas läbis kogu komplekt 110 testi; kaks platvormi- või keskkonnaspetsiifilist testi jäeti vahele. Varasem sulgemata `kavitro_crash.log` ressursihoiatus kadus.

Jääkriskina on `faulthandler` protsessiülene ressurss ja sellel puudub avalik API aktiivse sihtfaili omaniku kontrollimiseks. Kavitro vähendab konflikti riski sellega, et ei aktiveeru, kui handler on juba kasutusel. Crash-logid sisaldavad failiteid, funktsiooninimesid ja reanumbreid ning neid tuleb käsitleda diagnostiliste andmetena. `Logs/CrashLogs` kataloog on release-paketist välistatud.

## WC-17 — servituudi PDF-i turvaline ajutine fail

**Otsuse kuupäev:** 2026-09-06

**Staatus:** parandus teostatud ning QGIS 3.40 testikeskkonnas valideeritud

### Kontrollitud tegelik olukord

- Servituudi PDF kirjutati varem alati fikseeritud nimega `kavitro_easement_drawings` ajutisse kataloogi. `exist_ok=True` tõttu aktsepteeris rakendus kontrollimata ka juba olemasolevat kataloogi.
- PDF-i failinimi põhines objekti numbril või ID-l. Failinime puhastamine takistas kataloogist väljumist, kuid sama objekti samaaegsed ekspordid kasutasid sama faili ja võisid üksteise tulemust üle kirjutada või kustutada.
- Dialoog eemaldas loodud PDF-i sulgemisel, kuid ei eemaldanud kataloogi. Ebaõnnestunud või erindiga katkenud eksport võis jätta osalise faili alles.
- Windowsi kasutajaprofiili `%TEMP%` vähendas kontrollitud keskkonnas teiste kohalike kasutajate ligipääsu. Jagatud ajutise kataloogiga platvormidel oli etteaimatava kataloogi ja failinime risk suurem.

### Rakendusotsus

- Iga eksport loob `tempfile.mkdtemp()` abil süsteemi ajutisse kataloogi uue juhusliku nimega `kavitro_easement_drawings_*` kataloogi. Loomine on atomaarne ning POSIX-süsteemis on kataloog vaikimisi ligipääsetav ainult loojale.
- Inimloetav ja puhastatud PDF-i failinimi säilib, kuid sama objekti paralleelsed ekspordid asuvad nüüd erinevates kataloogides.
- `EasementPdfService` registreerib protsessi mälus iga enda loodud väljundtee. Puhastus aktsepteerib ainult täpselt registreeritud teed, keeldub faili või emakataloogi sümbollingist ning ei järgi linke.
- Puhastus eemaldab ainult registreeritud PDF-i ja proovib seejärel eemaldada tühja emakataloogi. Ootamatu naaberfaili korral ei kasutata rekursiivset kustutamist ja kataloog jäetakse alles.
- Dialoogi olemasolev sulgemispuhastus kasutab nüüd teenuse turvalist puhastusmeetodit. Sama puhastus käivitub ka PDF-i ekspordi veakoodi või erindi korral.
- Vana fikseeritud `kavitro_easement_drawings` kataloogi ei kasutata, migreerita ega kustutata automaatselt, sest selle päritolu ja omandit ei saa usaldusväärselt kinnitada.

### Valideerimine ja jääkrisk

Regressioonitestid kontrollivad unikaalseid privaatseid katalooge, sama objekti eraldatud väljundeid, vana fikseeritud kataloogi puutumatust, võõra tee tagasilükkamist, ainult registreeritud PDF-i eemaldamist ning osalise faili puhastamist nii ekspordi veakoodi kui ka erindi korral. Sümbollingi test on olemas, kuid kontrollitud Windowsi keskkonnas jäeti see operatsioonisüsteemi puuduva sümbollingi loomise õiguse tõttu vahele.

QGIS 3.40.13 Pythoni keskkonnas läbis kogu komplekt 118 testi; kolm platvormi- või keskkonnaspetsiifilist testi jäeti vahele.

Jääkriskina võib QGIS-i või operatsioonisüsteemi järsk katkestamine jätta privaatse ajutise kataloogi ja PDF-i kettale, sest protsessisisene omandiregister ei säili taaskäivitamisel. Rakendus ei korista järgmisel käivitamisel nimepõhise oletuse alusel vanu katalooge, kuna see taastaks ohu kustutada tundmatu päritoluga sisu. Tavapärase dialoogi sulgemise ja käsitletud ekspordivigade korral puhastus toimib.

## WC-18 — välises rakenduses avatud manuste ajutised failid

**Otsuse kuupäev:** 2026-09-06

**Staatus:** madal jääkrisk aktsepteeritud; koodi ei muudeta

Kaugmanuse välises rakenduses avamisel luuakse fail `tempfile.NamedTemporaryFile(delete=False)` abil juhusliku nimega. Kontrollitud Windowsi keskkonnas asub fail kasutaja enda `%LOCALAPPDATA%/Temp` kataloogis. Failinime kaaperdamise või kataloogist väljumise riski ei tuvastatud.

Ajutine fail võib jääda kettale pärast QGIS-i sulgemist, sest rakendus ei tea usaldusväärselt, millal väline PDF-, Wordi- või CAD-rakendus faili enam ei kasuta. Riski mõju piirdub peamiselt kasutaja ajutise kataloogi kasvamise ja manuse pikema kohaliku säilimisega. Arvestades kasutajapõhist Windowsi ajutist kataloogi ning leiu madalat raskusastet, aktsepteeritakse jääkrisk ja automaatset kustutamist ei lisata.

## WC-19A — API-vastuste ja projektiandmete konsooliväljund

**Otsuse kuupäev:** 2026-09-06

**Staatus:** parandus teostatud ning QGIS 3.40 testikeskkonnas valideeritud

### Kontrollitud tegelik olukord

- Auditi kolmest API-vastuse väljatrükist kaks olid endiselt aktiivsed kinnistu uuendamise voos. Esimene väljastas GraphQL-i `updateProperty` vastuse koos kinnistu ID ja aadressiväljadega; teine väljastas kasutusotstarbe mutatsiooni tagastatud ID.
- Väljatrükid ei sisaldanud täielikku HTTP vastust, sessioonitokenit ega parooli. `APIClient.send_query()` tagastas neile GraphQL-i `data` osa koos päringus küsitud väljadega.
- Auditis nimetatud projektikausta mutatsiooni `print(response)` oli varasema spetsiaalse `ModuleFilesPathUpdater` parandusega juba eemaldatud.
- Projektikausta nime generaatoris olid alles viis tingimusteta arendusväljatrükki, mis sisaldasid projekti nime, numbrit, nimereeglit ja genereeritud kaustanime.
- Repository runtime-koodis on veel arvukalt muid `print()`-kutseid. Nende üldine refaktoreerimine ei kuulu WC-19A piiratud API- ja projektiandmete lekke parandusse.

### Rakendusotsus

- Kinnistu uuendamise ja kasutusotstarbe eduka GraphQL-vastuse väljatrükid eemaldati. Vastuseid ei olnud töövoo jätkamiseks vaja.
- Kinnistu uuendamise tõrke konsooliväljund asendati struktureeritud `PythonFailLogger.log_exception()` sündmusega `property_backend_update_failed`. Diagnostika säilib WC-13 käigus turvatud kasutajapõhises logis.
- Projektikausta nime generaatorist eemaldati projekti nime, numbri, reegli ja tulemuse arendusväljatrükid. Kausta nime koostamise loogikat ei muudetud.
- Ülejäänud mittetundlikke või muude moodulite `print()`-kutseid selles etapis ei muudetud, et vältida auditi leiust oluliselt laiema refaktoreerimise regressiooniriski.

### Valideerimine ja jääkrisk

Regressioonitestid kontrollivad mõlema kinnistumutatsiooni edukat käitumist ilma konsooliväljundita, tõrke suunamist turvalisse loggerisse, projektikausta nime loomist ilma projektiandmete väljatrükita ning auditis käsitletud failide tundlike aktiivsete `print()`-kutsete puudumist.

QGIS 3.40.13 Pythoni keskkonnas läbis kogu komplekt 122 testi; kolm platvormi- või keskkonnaspetsiifilist testi jäeti vahele.

Jääkriskina võivad teiste moodulite vanad diagnostilised `print()`-kutsed endiselt protsessi standardväljundisse jõuda. WC-19A sulgemine tähendab, et kontrollitud GraphQL-vastuseid ja projektikausta nime andmeid enam ei väljastata; kogu repository konsoolilogimise ümberkujundamist see otsus ei hõlma. Rich-text-sildi HTML-escaping on eraldi WC-19B etapp.

## WC-19B — faili metaandmete turvaline rich-text-kuvamine

**Otsuse kuupäev:** 2026-09-06

**Staatus:** parandus teostatud ning QGIS 3.40 testikeskkonnas valideeritud

### Kontrollitud tegelik olukord

- Faili eelvaate metaandmete `QLabel` koostas HTML-i, millesse lisati kodeerimata failinimi, MIME-tüüp või laiend, inimloetav suurus ja üleslaadija kuvanimi.
- `QLabel` kasutas vaikimisi `Qt.AutoText` režiimi. Kuna metaandmete tekst algas `<b>` märgendiga, tõlgendas Qt kogu väärtust rich-text’ina. Failinime või üleslaadija nime lisatud märgendid võimaldasid muuta teksti suurust, värvi ja paigutust ning lisada võltsitud teateridu.
- Sama failinimi jõudis ka plain-text’ina mõeldud eelvaate veateadetesse, välise avamise tooltip’i ning kinnitus- ja veadialoogidesse. Need kasutasid samuti Qt automaatset rich-text’i tuvastust.
- Kontrollitud QGIS 3.40.13 Qt keskkonnas tõlgendati ka tavalise lause keskel olevat HTML-märgendit rich-text’ina.
- Sildid ei käivitanud JavaScripti ega süsteemikäske. Metaandmete sildi välislinkide automaatne avamine oli keelatud ja lingisignaal polnud toiminguga ühendatud, mistõttu jäi mõju visuaalse võltsimise tasemele.

### Rakendusotsus

- Metaandmete silt määrati teadlikult `Qt.RichText` režiimi ning kõik neli dünaamilist väärtust kodeeritakse standardteegi `html.escape()` abil. Failinime rasvane kiri, reavahetus ja ülejäänud kujundus säilivad.
- Eelvaate teatesilt ja dünaamiliselt loodud kohatäitesilt kasutavad nüüd selgelt `Qt.PlainText` režiimi.
- Tooltip’i ning välise avamise kinnitus- ja veateate lõpetatud tekst teisendatakse `Qt.convertFromPlainText()` abil turvaliseks rich-text-dokumendiks. Reavahetused säilivad, kuid failinime märgendeid ei tõlgendata.
- Algset failinime ei puhastata ega nimetata ümber. HTML-i erimärgid kuvatakse kasutajale sõna-sõnalt, sest kaitse rakendub ainult kuvamise kontekstis.
- Ühist `ModernMessageDialog` komponenti ei muudetud, et vältida mõju muudele dialoogidele. Kaitse on piiratud `TaskFilePreviewDialog` komponendi kontrollitud failimetaandmete vooga.

### Valideerimine ja jääkrisk

Regressioonitestid kontrollivad failinime, MIME-tüübi, suuruse ja üleslaadija nime HTML-kodeerimist, tavapärase metaandmete visuaalse teksti säilimist, eelvaate teate- ja kohatäitesildi plain-text-režiimi ning välise avamise kinnitusteksti puutumatust pahatahtliku failinime korral.

QGIS 3.40.13 Pythoni keskkonnas läbis kogu komplekt 126 testi; kolm platvormi- või keskkonnaspetsiifilist testi jäeti vahele.

Jääkriskina võivad sama API-andmevälja teised, selles etapis kontrollimata kuvamiskohad kasutada mujal rakenduses Qt automaatset rich-text’i tuvastust. WC-19B sulgeb auditis nimetatud faili eelvaate metaandmete ja sama dialoogi turvakinnituste voo; kogu rakenduse dünaamiliste `QLabel`-tekstide inventuur oleks eraldi kaitsesügavuse audit.
