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
**Staatus:** parandus koodis ette valmistatud; GitHubi release immutability seadistuse aktiveerimine ja esimene lukustatud release on veel tegemata

### Kontrollitud tegelik käitumine

- QGIS 3.40, QGIS 3.44 ja QGIS-i praegune plugina paigaldaja ei loe `plugins.xml` failist SHA-256 välja ega kontrolli ZIP-i kontrollsummat enne lahtipakkimist.
- Auditis soovitatud `<sha256>` elemendi lisamine `plugins.xml` faili ei annaks kaitset, sest QGIS eiraks seda.
- GitHub arvutab igale release-varale SHA-256 digesti. Release’i `v2.02.16` kõik kolm vara sisaldavad GitHubi API-s digesti, kuid release ise on `immutable: false`.
- Senine workflow käivitub pärast release’i avaldamist ning kasutab varade tagantjärele asendamiseks valikut `--clobber`. Selline järjekord ei ühildu lukustatud release’idega.

### Rakendusotsus

Release’i terviklus tagatakse GitHubi immutable release’i mehhanismiga, mitte QGIS-i poolt toetamata XML-elemendiga. Uus töövoog:

1. nõuab ettevalmistatud tühja draft-release’i;
2. seob tulevase tag’i täpselt workflow’ kontrollitud commit’iga;
3. koostab `plugins.xml`, plugina ZIP-i ja ikooni enne avaldamist;
4. keelab avaldatud varade ülekirjutamise ning ei kasuta `--clobber` valikut;
5. võrdleb enne avaldamist iga kohaliku faili SHA-256 väärtust GitHubi vara digestiga;
6. avaldab draft’i alles pärast kontrollide õnnestumist;
7. katkestab veaga, kui avaldatud release ei ole `immutable: true`.

LIVE-metaandmete lähteks kasutatakse `metadata.release.txt` faili. See väldib DEV-metaandmetest vana ikooni pärimist ning määrab release’i ikooniks `resources/icons/Kavitro-favicon-96x96.png`.

Enne immutable-protsessi aktiveerimist parandati ühekordselt olemasoleva release’i `v2.02.16` kataloogiikoon. Ainult release’i vara `kavitro_live.png` asendati valitud 96 × 96 Kavitro faviconiga; ZIP ja `plugins.xml` jäid muutmata. GitHubis oleva uue ikoonivara SHA-256 on `ed9ea0c499f6072eb95decc3cf607b426fe5844b5a1446c4dca0814321c970ac` ning see kattub repository failiga.

### Jääkrisk

Immutable release takistab juba avaldatud tag’i ja varade hilisemat muutmist. See ei välista pahatahtliku paketi koostamist enne avaldamist, kui GitHubi konto või build-workflow on juba kompromiteeritud. Build-sõltuvuste ja GitHub Actionsi õiguste tugevdamine käsitletakse WC-12 etapis.

QGIS Plugin Manager ei kontrolli GitHubi release-attestatsiooni ise. Kasutaja automaatse paigalduse usalduspiir jääb GitHubi HTTPS-ühendusele, repository õigustele ja release’i avaldamise protsessile.

### Kasutuselevõtu tingimus

Pärast workflow muudatuse jõudmist vaikimisi harusse tuleb GitHubi repository seadetes lubada **Enable release immutability**. Seadistust ei tohi aktiveerida enne draft-first workflow kasutuselevõttu, sest vana `release: published` voog ei saaks lukustatud release’ile enam faile lisada.
