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
**Staatus:** parandus teostatud ja automaattestidega valideeritud; GitHubi käsitsi release-test on tegemata

Release’i sündmuse tagi, manuaalse käivituse sisendeid ja valideeritud sammuväljundeid ei tohi lisada otse GitHub Actionsi `run:` skripti. Sisendid antakse keskkonnamuutujate kaudu testitavale resolverile, mis lubab ainult Kavitro release’i versiooni- ja tagivormingut. Järgmised sammud saavad kasutada ainult resolveri kontrollitud väljundeid ning samuti ainult keskkonnamuutujate kaudu.

Sama turvapiir peab kajastuma nii tegelikus `.github/workflows/qgis_release.yml` failis kui ka `MAIN_PLUGIN_RELEASE_SETUP.md` mallis.

Teostuses lahendab `tools/resolve_release_values.py` release’i sündmuse ja manuaalse käivituse väärtused, kontrollib need range lubatud vormingu järgi ning kirjutab ainult üherealised kontrollitud väärtused faili `GITHUB_OUTPUT`. Workflow’ `run:` plokkides ei ole pärast parandust GitHubi kontekstiavaldisi.
