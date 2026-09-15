# Kinnistute halduse asukohavalikute laadimine

14.09.2026 kontroll ja parandused puudutavad maakonna, omavalitsuse ja külade valimist impordikihist.

## Leitud viivitused

- Alamvalikute, kinnistute ja kaardivaate andmeid loeti korduvalt kasutajaliidese lõimes.
- Omavalitsuse valimine laadis kohe kõik selle kinnistud, isegi kui kasutaja soovis järgmisena valida ühe küla.
- Küla valimise järel võis käivituda ka täiendav kaardi uuendus.
- `processEvents()` pika lugemise sees lubas uut valikut töödelda enne vana töö lõppu, kuid ei viinud lugemist taustale.
- Uue tabeli järel lähtestati iga rea kontrolliikoonid uuesti. Arhiveerimise võrdlusbaasi koostamisel loeti iga tunnuse lahtrit kaks korda.
- Valikute juures puudus selge laadimis- ja veateade.

## Käitumine pärast parandusi

Maakondade, omavalitsuste ja külade nimistu loetakse taustal ühe korraga, ilma geomeetriata. Järgmised alamvalikud leitakse sellest nimistust. Impordikihi muutumisel nimistu ja varem laaditud võrdlusbaas tühistatakse.

Piirkonna kinnistud, objektide ID-d ja kaardivaate ulatus loetakse ühe taustatöö käigus. Kaardile rakendatakse juba arvutatud tulemus, ilma piirkonda uuesti läbi vaatamata.

Külade kiirete klikkide vahel oodatakse 250 ms. Uus valik katkestab eelmise lugemise järgmise objekti juures ja vana tulemust ei rakendata. Kui andmepakkuja on ühe lugemiskutse sees hõivatud, saab katkestus toimuda selle kutse naasmisel; kasutajaliides ei oota seda lõimes blokeerudes. Dialoogi sulgemine tühistab poolelioleva tulemuse rakendamise.

Valikute all kuvatakse parasjagu toimuvat tegevust, liikuvat laadimisindikaatorit ning lõpus laaditud kinnistute arvu. Vea korral ilmub selgitus ja „Proovi uuesti“ nupp. Juba kättesaadavad kõrgema taseme valikud jäävad kasutatavaks.

Senine ulatuse käitumine on säilitatud: **omavalitsuse valimine kuvab selle kõik kinnistud; viimase küla valiku eemaldamine taastab omavalitsuse vaate**. Võimalus täita tabel alles pärast küla valimist on kasutajalt eraldi küsitud ega ole selle paranduse osana rakendatud.

Arhiveerimise võrdlusbaas muutub piirkonna vahetamisel kohe kehtetuks. Uus baas salvestatakse alles täieliku, endiselt õigele piirkonnale ja impordikihile vastava laadimise järel. Tabeli hilisem valik või filtreerimine ei muuda juba salvestatud baasi. Tunnused loetakse tabeli mudeli andmetest, ilma iga lahtri jaoks Qt indeksit loomata.

Sama vahetus kustutab ka eelmise lisamise lõpptulemuse: töödeldud ja õnnestunud kinnistute arvud, edenemisriba, katastritunnuse rea ja kinnistupõhiste vigade loendi. Need kirjeldasid eelmist piirkonda ja uue tabeli kõrval oleksid nad eksitavad. Otsust ootavad kinnistud seda ei puuduta; need jäävad koos oma nupu ja loenduriga alles kuni haldusakna sulgemiseni, nagu seni. Lisamise ajal ei kustutata midagi.

Piirkonna vahetus ja arhiveerimiskava ebaõnnestumine on eri asjad. Kava ebaõnnestumine tühistab ainult kava enda ja jätab oma teate ekraanile; ainult tabeli ulatuse muutumine kustutab lisaks ka lisamise tulemuse.

## Kontroll

QGIS 3.40.13 Pythoni keskkonnas lisandus 13 testi. Kaetud on hierarhia eraldamine, samanimelised omavalitsused ja külad eri maakondades, aeglane lugemine, kasutajaliidese sündmused lugemise ajal, kiire valikuvahetus, tegelik rippmenüü klikk, viimase küla eemaldamine, viga ja korduskatse, sulgemine, impordikihi muutumine ning arhiveerimise võrdlusbaas tegelikus haldusdialoogis.

Kogu testikomplekt: **208 testi, neist 205 edukat ja 3 vahele jäetud**. Varasema Tööde testi fikseeritud 30 ms kuvamisootus asendati tegeliku kuvamise lõpu ootamisega.

Kohalikus 20 000 polügooniga GeoPackage'i katses, tegeliku haldusdialoogi ja tabelimudeliga:

| Mõõdik | Tulemus |
|---|---:|
| Maakonna ja omavalitsuse valikute käsitlemine | 3 ms |
| Omavalitsuse andmete lugemine ja tabeli valmimine | 565 ms |
| Kasutajaliidese 10 ms kontrolltaimeri pikim vahe laadimise ajal | 59 ms |
| Sama kontrolltaimeri vahede 95. protsentiil | 14 ms |

Need on ühe kohaliku katse mõõtmised, mitte kiirusgarantiid. Kaardi päris joonistamine oli katses asendatud kontrollitava väljakutsega. Serverisse päringuid ega kasutaja projektis muudatusi ei tehtud.

Käsitsi korduskatse pärast plugina uuesti laadimist:

1. Ava Kinnistute haldus ja jälgi nimistu laadimisteadet.
2. Vaheta kiiresti maakonda ja omavalitsust; alamvalikud peavad kohe uue valikuga vastavusse minema.
3. Vali mitu küla järjest ja eemalda mõni linnuke. Tabel ja kaart peavad vastama viimasele valikule.
4. Eemalda viimane küla: praeguse loogika järgi kuvatakse omavalitsuse kinnistud.
5. Sule dialoog laadimise ajal ning ava uuesti. Vana tulemus ei tohi taastuda.
6. Kontrolli, et laadimise ajal on vanad read ja kontrollitulemused eemaldatud ning kinnistute kontrolli saab käivitada pärast tabeli valmimist.

## QGIS-i lõimede käsitlus

Elusat projektikihti ja vidinaid kasutatakse ainult kasutajaliidese lõimes. Taustatöö saab seal loodud `QgsVectorLayerFeatureSource` andmeallika hetkeseisu. See järgib [QGIS-i taustatöö juhise](https://docs.qgis.org/3.40/en/docs/pyqgis_developer_cookbook/tasks.html) piiranguid; andmeallika hetkeseisu kirjeldab [QGIS 3.40 API](https://api.qgis.org/api/3.40/classQgsVectorLayerFeatureSource.html).

## 15.09.2026: külavaliku teavitus ja käsitsi värskendamine

Live-versiooni 2.02.22 logis `switch_log_09_15_072257.log` lõppes asukohanimekirja lugemine 07:24:36 ja sellele järgnesid piirkondade lugemised. Algse, 07:25:13 lõppeva lõigu järel uut külavaliku lugemist ei alanud. Hiljem lisandus kasutamise käigus uusi lugemisi. Senine logi ei sisaldanud valitud piirkonda ega sisestusviisi, mistõttu konkreetse Live-kliki põhjust ei saa ainult logi põhjal lõplikult kinnitada.

QGIS 3.40.13-ga taasesitati sama nähtav viga tühikuklahviga küla linnukest muutes: linnuke ja kuvatav külanimi muutusid, tabelisse jäid kogu omavalitsuse read. [QGIS-i valikukasti lähtekoodis](https://github.com/qgis/QGIS/blob/final-3_40_13/src/gui/qgscheckablecombobox.cpp) uuendab mudeli `dataChanged` kuvatavat teksti, kuid `checkedItemsChanged` väljastatakse eraldi meetodist. Senine plugin kuulas ainult viimast signaali.

Parandus kuulab ka linnukeste mudeli muutumist. Maakonna või omavalitsuse täitmisel tehtavaid sisemisi lähtestamisi eiratakse ja sama valiku korduvad signaalid ühendatakse üheks laadimiseks. Kiirete muudatuste senine 250 ms viide ja aegunud tulemuste tühistamine säilivad.

Külavaliku kõrval on 22 px värskendusikoon. Vajutamine loeb praeguse piirkonna tabeli ja kaardivaate uuesti, säilitades sama impordikihi korral maakonna, omavalitsuse ja külade valiku. Kogu asukohanimekirja uuesti ei loeta, kui see on juba olemas; puuduva nimistu või vahetunud kihi puhul käivitatakse nimistu laadimine. Nupp on kasutatav ka poolelioleva lugemise asendamiseks. Kinnistute lisamise ajal lukustub nupp koos teiste asukohavalikutega.

Värskendamisel tühistatakse vanad kontrollitulemused ja arhiveerimise võrdlusbaas. Uus baas tekib alles täieliku tabeli laadimise järel. Logisse lisanduvad `property_location_scope_requested`, `property_location_table_ready` ja `property_location_scope_discarded` koos piirkonna ning rakendatud tabeli reaarvuga.

Lisatud katsed kontrollivad tühikuklahviga valimist ja viimase küla eemaldamist, sama piirkonna värskendamist pärast uue lähterea lisandumist ning poolelioleva lugemise asendamist värskendusnupuga. Enne parandust ebaõnnestus klaviatuurikatse, sest tabel jäi muutumatuks. Käsitsi Live-katse uue paketiga on veel vajalik.

Lõppkontroll QGIS 3.40.13-ga: **279 testi, neist 276 edukat ja 3 vahele jäetud**. Värskendusnupu paigutust kontrolliti ka renderdatud asukohavalikute vidinas. Live-projekti andmeid ja backend'i ei muudetud.
