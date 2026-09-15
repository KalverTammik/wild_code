# Kinnistute impordi päringupiirangud

Kontrollitud 15.09.2026. API dokumentatsioon:

- [Päringu- ja muutmistoimingute piirangud](https://kavitro.dev/docs/basics/rateLimits)
- [Veakäsitlus](https://kavitro.dev/docs/concepts/errors)
- [Kinnistu loomise sisend](https://kavitro.dev/docs/graphql/reference/inputs/create-property-input)
- [Kinnistu uuendamise sisend](https://kavitro.dev/docs/graphql/reference/inputs/update-property-input)

Autenditud päringute piir on dokumentatsiooni järgi 500 minutis tokeni kohta. Muutmistoimingutel on eraldi piirid: 40 minutis kasutaja ja 300 minutis konto kohta. Loendatakse GraphQL-i juurtaseme muutmisvälju, mitte HTTP ümbriseid. Serveri vastusepäised on määravad ka siis, kui piirid muutuvad.

Praegune API ei võimalda sihtotstarbeid `createProperty` ega `updateProperty` sisendis saata. Kinnistu andmete ja sihtotstarvete salvestamiseks jääb kaks muutmistoimingut. Üheks ühendamine eeldab backend'i sisendite laiendamist. Kahe muutmisvälja samasse HTTP-päringusse pakkimine muutmistoimingute eelarvet ei vähenda.

## Rakendatud käitumine

Hooldusprojekti eeskujul alustatakse kõigis töövoogudes vaikimisi kuni 30 muutmistoiminguga minutis, vähemalt kahe sekundi pikkuse vahega. Ühine piiraja arvestab iga tegelikku katset, serveri üld-, kasutaja- ja kontolimiidi päiseid ning teiste plugina klientide päringuid. Kasutaja/konto täpse võtme puudumisel jagatakse kohalikke muutmispiire konservatiivselt sama serveriaadressi kõigi klientide vahel. Üldpäringute eelarve on tokeni põhine; tokenit ei logita.

Ajutine HTTP 429 koos `Retry-After` väärtusega jätab sama füüsilise päringu korduskatsete tsüklisse. Kõigis töövoogudes jätkub see kuni õnnestumise või katkestamiseni. Kui loomine õnnestus ja sihtotstarbe päring sai 429, korratakse ainult sihtotstarbe päringut. Kasutaja näeb ooteaega ja automaatse jätkamise teadet; QGIS-i kasutajaliidese lõim ei maga.

`TOO_MANY_MUTATIONS` vastus ilma `Retry-After` päiseta tähendab dokumentatsiooni järgi ühe päringu liiga suurt mahtu. Sellist päringut muutmata ei korrata. Püsiv salvestusviga peatab nii kontrollitud kui ka kontrollita impordi, näitab veaga kinnistut ja ülejäänud töötlemata kannete arvu. Võrguvea või HTTP 5xx korral ei korrata vaikimisi ühtegi muutmispäringut ega failiüleslaadimist pimesi, sest server võis selle juba täita. Ajutise 429 korduskatse toimub sellest sõltumatult.

Katkestamine peatab oote ja järgmised saatmised. Juba saadetud HTTP päringut ei katkestata jõuga. Kui kinnistu mitmeosalise salvestamise järgmine etapp jääb katkestamisel saatmata, jääb kinnistu töötlemata arvestusse; järgmisel kontrollil tuleb tuvastada selle tegelik backend'i seis.

Mõlemad lisamisnupud (`Lisa valitud` ja `Lisa ilma kontrollita`) kasutavad nüüd ühist `AddBatchRunner`-it. Erineb eelkontrolli nõue. Mõlemal juhul kontrollitakse enne loomist värskelt backend'i olemasolu, et vältida duplikaate. Arhiveeritud või mitmetähenduslikku vastet ning backend'i uuemat erinevat kirjet automaatselt ei asendata. Vana sünkroonne, üksikküsimustega lisamisvoog eemaldati.

Ka kasutajaliidesest sünkroonselt kutsutud API päringud saadetakse nüüd transporditöötajas. Kutsuja saab tulemuse enne jätkamist; QGIS-i kihte ja sessioonihaldust sellesse töötajasse ei viida. Üle 400 ms kestva päringu või oote ajal avaneb katkestatav edenemisaken, mis näitab pausi ja automaatset jätkamist. Lühikesed päringud lisaakent ei ava. `FunctionWorker` kasutab katkestuskonteksti ning `LatestRequest` tühistab aegunud päringu oote.

## Päringute ülevaatuse ulatus

Kogu hoidla otsing leidis Kavitro GraphQL HTTP saatmise ainult `python/api_client.py` kahest kohast. Mõlemad läbivad sama koordinaatori; GUI erand, mis varem ennetavat pausi eiras, eemaldati. Faili sisu allalaadimine allkirjastatud URL-ilt ja välise kaardiandmete teenuse päringud ei ole Kavitro GraphQL päringud.

| Töövoog | Käsitlus |
| --- | --- |
| Mõlemad kinnistute lisamisnupud | Ühine taustatöö, sama etapi korduskatse, katkestamine ja kinnistupõhine tulemus. |
| Importimisel puuduvate kinnistute arhiveerimine | Ühine piiraja; viga peatab järgmised backend'i toimingud, töötlemata tunnused kuvatakse. Arhiivikoopiad jäävad alles. |
| Valitud kinnistute arhiveerimine ja taastamine | Ühine piiraja; ebaõnnestunud toimingu järel järgmiste kinnistutega ei jätkata. |
| Valitud kinnistute kustutamine | Ühine piiraja; kinnitatakse kustutatud kirje ID. Backend'i vea korral põhikihi kustutamist ei alustata. |
| Mitme faili lisamine | Ühine muutmiste eelarve; 429 järel saadetakse sama täielik fail. Püsiva vea järel kuvatakse saatmata failid. |
| Tööde geomeetriate massimuudatus | Ühine piiraja; ebaõnnestumine peatab järgmised salvestused ja sünkroonimisaeg märgitakse ainult kinnitatud õnnestumistele. |
| Moodulite loomine/muutmine; staatused, liikmed, seosed, sildid ja failide toimingud | Kõik läbivad ühise API transpordi, ka mitu järjestikust muutmist ühest kasutajatoimingust. |
| Otsingud, kontrollid, lehekülgede laadimine ja muud lugemispäringud | Sama tokeni päringueelarve ja ajutise 429 korduskatse. Lugemine ei kuluta muutmiste eelarvet. |

Osaliselt lõpetatud tegevus ei ole tervikuna tagasipööratav tehing. Näiteks enne backend'i arhiveerimist on kaardi arhiivikoopiad juba salvestatud. Katkestamise või püsiva vea järel tuleb võrrelda tegelikku seisu; automaatne sama HTTP päringu kordamine on ette nähtud ajutisele 429 vastusele.

## Kontrollimine

### Otsust vajavate kinnistute käsitlus

Aadressikonflikt, ainult arhiveeritud vaste ja mitu aktiivset vastet on eraldi `needs_decision` tulemused. Need tuvastatakse enne salvestamist: taustasüsteemi ega põhikihti selle kinnistu jaoks ei muudeta ja jooksutaja jätkab järgmise kinnistuga. Päringu ebaõnnestumine, ebaselge salvestustulemus ja kehtetu kiht jäävad peatavateks vigadeks.

„Käivita kontroll” ja import kasutavad sama `classify_property_import()` funktsiooni. Asukohapõhise tabeli andmetes säilitatakse `muudet` väli; kontroll arvestab aadressi, backend'i katastriandmete kuupäeva ning põhikihi kuupäeva. Võrdlus toimub kalendrikuupäevades, sest impordi API-sisend on samuti kuupäev; ajavööndiga backend'i ajatempel ei tekita enam võrreldamatute kuupäevade viga. Puuduvat või loetamatut kuupäeva ei esitata kasutajale tõendina, et import on vanem. Värske backend'i kontroll enne iga salvestamist säilib.

Automaatse töö lõpus kuvab haldusaken eraldi õnnestumised, tehnilised vead ja otsust ootavate kinnistute arvu. Nupp „Vaata otsust ootavaid kinnistuid” avab aadresside ja kuupäevade võrdluse. Valikud:

- **Jäta hilisemaks**: kirje säilib otsuste loendis selle haldusakna sulgemiseni. Püsivat kettale salvestamist ei ole.
- **Säilita olemasolev**: kirje eemaldatakse otsuste loendist; selle kinnistu backend'i ja põhikihi andmeid ei muudeta. Loendatakse eraldi, mitte salvestusena.
- **Rakenda impordi andmed**: pakutakse aadressikonflikti korral. Uuendatakse sama backend'i kirje kinnistu numbrit, katastriandmeid, aadressi, pindala ja sihtotstarbeid. Olemasolev põhikihi objekt jääb alles; puuduv kopeeritakse importkihist. Arhiveeritud või mitme aktiivse vastega kirjetele ülekirjutamise valikut ei pakuta.

Rakendatakse ainult valitud ootel kirjed, mitte algset impordivalikut uuesti. Enne ülekirjutamist võrreldakse uuesti backend'i verifitseerimistulemust ning lähte- ja põhikihi identiteeti ja objekte. Muutunud andmed jäävad värske võrdlusega otsust ootama. Backend'i kontroll hõlmab olemasoleva verifitseerimispäringu tagastatud välju (sh ID, aadress, katastriandmete kuupäev, aktiivsed/arhiveeritud vasted ja sildid); see ei ole serveripoolne atomaarne tingimuslik kirjutamine.

Kuni eelmise impordi otsused on ootel, suunavad lisamisnupud nende ülevaatesse, et edukalt imporditud valikut kogemata uuesti mitte töödelda. Tehnilise vea või katkestamise järel säilivad juba kogutud otsused ja tegelikud tulemused. Automaatses osas tähendab 100% kogu valiku läbivaatamist, mitte kõigi kinnistute salvestamist.

Regressioonikatsed kontrollivad „Käivita kontroll” → import töövoogu, kuupäeva säilimist tabelis, 82 kinnistu valikut ühe esimese aadressikonflikti ja 81 eduka impordiga, arhiivi/mitme vaste edasilükkamist, eraldi otsuste rakendamist, muutunud backend'i ja geomeetriat, säilitamist, katkestamist ning koondloendureid. Kõik päringud on asendatud; päris backend'i ei muudeta.

15.09.2026 lõppkontroll QGIS 3.40.15 keskkonnas: **291 testi, neist 288 edukad ja 3 vahele jäetud**. Otsuste dialoogi paigutust vaadati üle ka renderdatud 850 × 680 ja 700 × 600 eelvaates. Päris LIVE-importi ei tehtud.

### Lisamise edenemine

Mõlema lisamisviisi ajal on eraldi nähtavad töödeldud kinnistute arv, kogu käivitatud valiku maht, järelejäänud arv ning protsendiga edenemisriba. Katastritunnus ja päringupausi teade kuvatakse nende all; paus ei asenda loendurit. Töödeldud kinnistute arv muutub jooksutaja tulemuse põhjal, mitte päringu saatmisel. Vea või katkestamise korral jäävad alles tegelik edenemine ja lõpptulemuse eraldi õnnestumiste, ebaõnnestumiste ning töötlemata kannete arvud.

Lõpptulemus jääb nähtavale seni, kuni tabel kirjeldab sama valikut. Piirkonna vahetamine või asukohavalikute värskendamine kustutab arvud, edenemisriba ja vigade loendi, sest need ei kehti uue tabeli kohta. Otsust ootavad kinnistud jäävad sellest hoolimata alles.

Kulunud aeg uueneb kord sekundis ka päringu ja pausi ajal. Järelejäänud aja ligikaudne hinnang tekib pärast esimese kinnistu töötlemist: senine kulunud aeg jagatakse töödeldud kinnistute arvuga ja korrutatakse järelejäänud arvuga. Kulunud aja sisse jäävad päringupausid; hinnang ei ole lühem teadaolevast aktiivsest ooteajast. See on kohanduv hinnang, mitte lubatud lõpetamisaeg. Katkestamise ajal hinnang peidetakse. Uus lisamine alustab loendust ja ajamõõtmist uuesti.

Käsitsi kontroll: mõlema lisamisnupuga peavad arvud, riba ja aeg jääma nähtavale nii tavalise salvestuspausi kui ka serveri piirangu ajal. Katkestamisel ei tohi osaline töö muutuda 100% edenemiseks. Tekst peab mahtuma tegevusnuppude kohale ka kitsamas aknas. Automaatkontrollis kasutatakse asendatud kellaaega, jooksutaja signaale ja mälukihte; võrku päringuid ei saadeta.

15.09.2026 kontroll pärast edenemisnäidu ja külavaliku parandusi: QGIS 3.40.13 keskkonnas 280 testi, neist 277 edukad ja 3 vahele jäetud. Kontrolliti mõlemat lisamisviisi, ooteaja taimerit, arvude püsimist pauside ajal, katkestamist, korduva käivituse lähtestamist ning teksti mahutamist 650 × 420 aknas. Lisaks vaadati üle dialoogi renderdatud eelvaade. Päris LIVE-import selle kontrolli käigus ei toimunud.

Automaattestid asendavad HTTP vastused ja aja; päris backend'i ei muudeta. Kaetud on kasutaja- ja kontolimiidid, vastusepäised, järjestikused 429 vastused, sama etapi kordamine, vastuse ID kontroll, katkestamine ning Qt edenemine. Õnnestumise aluseks on serveri edukas mutatsioonivastus õige kirje ID-ga, mitte eraldi hilisem andmete tagasilugemine.

Kasutajakatses tuleb pärast arendusplugina uuesti laadimist proovida mõlemat lisamisnuppu väikese ülevaadatud valikuga: paus peab olema nähtav, õnnestumiste arv peab kasvama alles pärast kinnistu kõigi etappide lõppu ja ebaõnnestunud toiming ei tohi jääda märkamatult vahele. Katkestamist saab proovida oote ajal. LIVE-paketti tuleb parandus avaldada eraldi versioonina.

### Kinnistute kontrolli pausid ja katkestamine

„Käivita kontroll” teeb iga kinnistu kohta kaks lugemispäringut. Suurema küla puhul jõuab see tokeni minutipiirini ja ühine piiraja peatab kontrolli kuni järgmise lubatud päringuni. Varem ei olnud pausi näha ning taustatöö ootas selle lõpuni ka pärast peatamist.

Kontrolli taustatöö kasutab nüüd sama katkestus- ja ooteteavituse konteksti nagu lisamine. Edenemisriba näitab edasi kontrollitud kinnistute arvu ja selle all kuvatakse järelejäänud ooteaeg. „Tühista” katkestab käimasoleva kontrolli, jätab haldusakna avatuks ja näitab, mitu kinnistut jõuti kontrollida. Katkestatud kontrolli järel „Lisa valitud” ei aktiveeru, sest see nõuab täielikku kontrolli. Akna sulgemine risti või Esc-klahviga sulgeb akna nagu varem. Taustatöö enda lisaviivitused eemaldati, sest päringute tempo määrab ühine piiraja.

Katkestamine lõpetab ootamise kohe. Juba saadetud lugemispäringu vastus oodatakse taustal ära, kuid seda ei rakendata. Kui kontroll käivitatakse uuesti või piirkond vahetub, arvestatakse ainult viimati käivitatud kontrolli tulemusi. Varem võis asendatud kontrolli hilinenud lõputeade eemaldada viite uuele kontrollile, mistõttu uut kontrolli ei saanud enam peatada.

### 15.09.2026 laiendatud kontroll

- QGIS 3.40.13 Python: 276 testi, 273 õnnestunud, 3 vahele jäetud; päris backend'i ei muudetud.
- 50 kinnistut ja nende sihtotstarbed: 100 edukat muutmist, 16 simuleeritud ajutist 429 vastust, kokku 116 füüsilist katset; kõik 50 kinnistut loodi täpselt üks kord.
- JSON ja multipart kasutavad sama pausi; üleslaadimisel kontrolliti kogu faili kordussaatmist.
- Qt taimer jätkas tööd aeglase HTTP päringu ajal; kontrolliti ka ooteakent, katkestamist 429 pausi ajal ja juba saadetud kirjutamise vastuse äraootamist.
- Arhiveerimise, taastamise, kustutamise, failiüleslaadimise ja geomeetriate vea korral kontrolliti järgmiste kannete peatamist ning tõestamata tulemuse õnnestunuks mittelugemist.
- Järgmine käsitsi katse avaldatud LIVE-paketiga: väike valik mõlema lisamisnupuga; pausi ja katkestamise jälgimine; lõpptulemuse võrdlus põhikihi ja backend'iga. See katse on veel tegemata.
