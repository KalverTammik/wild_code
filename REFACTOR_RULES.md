# Refaktoreerimise püsireeglid

See fail on koodimuudatuste kavandamise ja ülevaatuse kontrollnimekiri. Siin hoitakse
ainult praegu kehtivaid reegleid, mitte muudatuste ajalugu.

Reeglid kehtivad uuele ja sisuliselt puudutatud koodile. Olemasolev kõrvalekalle ei ole
põhjus laiendada fokuseeritud muudatust kogu repo ümbertegemiseks; suurem migratsioon
vajab eraldi ulatust, tõendatud kasu ja kontrolliplaani.

Muudatuse põhjendus, puudutatud failid ja kontrollitulemused kuuluvad commit'i või PR-i
kirjeldusse. PR-is kasuta leitavuse jaoks rida `REFACTOR_NOTE: <kokkuvõte>`. Varasem
projektiajalugu on failis [docs/archive/refactor_log.md](docs/archive/refactor_log.md).

## 1. Lihtsus ja muudatuse ulatus

- Eelista surnud või dubleeriva koodi eemaldamist uuele abstraktsioonile.
- Tee üks sisuline muudatus korraga; ära ühenda samasse muudatusse ümbernimetamist,
  arhitektuuri kolimist ja varjatud käitumismuutust.
- Eelista väikest fokuseeritud diff'i. Kasuta olemasolevat omanikku, kui vastutus sinna
  päriselt kuulub; loo eraldi fail, kui see annab olekule ühe omaniku, selge lepingu või
  Qt-st sõltumatu testitava üksuse. Ära kasvata monoliiti ainult failimuudatuste arvu
  vähendamiseks.
- Hoia loogika kohalikuna, kuni sellel on vähemalt kaks tegelikku kasutuskohta või see
  takistab selgelt loetavust.
- Kasuta varajasi tagastusi ning vähenda harude ja pesastuse hulka.
- Ära lisa oletuslikke lippe, strateegiaid ega seadistusi ilma praeguse kasutuskohata.
- Kommentaar peab kirjeldama põhjust või kompromissi, mitte kordama koodi.

## 2. Üks omanik ja üks avalik kasutusviis

- Otsi enne uue meetodi, klassi või konstandi loomist olemasolevat lahendust kogu repost.
- Igal samal semantilisel lepingul peab olema üks kanooniline avalik sisenemispunkt.
  Sarnase kujuga, kuid erineva lõppemis-, vea- või elutsüklilepinguga toiminguid ei tohi
  ainult koodikuju pärast kokku suruda.
- Korduv loogika tõsta sobivasse olemasolevasse `utils/` või `modules/` omanikku; ära
  jäta paralleelseid teostusi eri kihtidesse.
- Ära loo läbiviik-meetodeid, mis edastavad samad argumendid muutmata edasi. Ühilduvuskiht
  peab olema ajutine, märgistatud ja pärast kasutuskohtade migreerimist eemaldatud.
- Korduvad moodulinimed, sündmusevõtmed, kaustanimed ja logimisvõtmed pärinevad ühest
  konstantide omanikust.
- Impordi sümbol selle defineerivast moodulist. Väldi innukaid paketitaseme re-eksporte.
- Uute failide nimed on `snake_case` ja uute klasside nimed `CamelCase`. Legacy-faili
  ümbernimetamine toimub ainult eraldi kontrollitud migratsioonis, sest see muudab kõiki
  importe ja võib olla failisüsteemi tõstutundlikkuse tõttu platvormirisk.
- Üldine headless-abilloogika kuulub `utils/`-i ja domeeniloogika `modules/`-isse. UI
  komponente ei nimetata utiliitideks ega lisata mugavuse pärast `utils/` alla.

## 3. Sõltuvused ja käivitusaeg

- UI võib sõltuda headless-teenustest ja domeeniloogikast, kuid need ei impordi dialooge
  ega widget'eid. Reegel käib komponendi tegeliku rolli, mitte ainult praeguse kaustanime
  kohta; vales kihis oleva komponendi liigutamine vajab eraldi migratsiooniplaani.
- Dialoog ja widget koostavad UI ning delegeerivad tegevuse; hargnev äriloogika ei ela
  UI-klassis.
- Mooduli importimisel ei tehta võrgu-, andmebaasi- ega rasket arvutustööd. Algväärtusta
  laisalt või konstruktori/teenuse kaudu.
- Pika elueaga, olekut hoidvad või eraldi testitavad teenused võtavad IO-kliendi sõltuvuse
  väljast. Ühekordse kanoonilise kliendi loomise ümber ei lisata ainult süstimise nimel
  tehaseid ega läbiviikkihte.
- Abifunktsioonid hoitakse võimalusel puhtad.
- Äri-, andme- ja turvaviga püütakse ainult kohas, kus on tegelik taastumisviis; see ei
  tohi vaikides kaduda ega muutuda näiliseks õnnestumiseks. Qt cleanup võib ignoreerida
  ainult kitsalt määratud ja ootuspärast kustutatud-objekti viga, mitte üldist
  `Exception`-it.
- Kohustusliku liidese puhul ära kasuta `hasattr`/`getattr` varuteed; paranda leping või
  kasutuskoht.

## 4. UI, tõlked ja QGIS

- Tõlkevõtmed lahendatakse rangelt. Ära lisa UI-sse fallback-teksti ega võtme kuvamist
  tekstina.
- Kasuta olemasolevat ühist teema- ja retheme-elutsüklit. Rakenda widget'ile kitsaim
  vajalik QSS-skoop.
- Eemalda kasutamata konstruktoriargumendid, olekulipud ja `setProperty(...)` väärtused,
  millel pole enam tarbijat.
- Ühenda signaal otse kanoonilise callable'iga, kui eraldi ühe rea handler pole vajalik.
- Ära käivita API- või reload-tööd widget'i `__init__`-is. Kasuta aktiveerimist või
  vajadusel `QTimer.singleShot(0, ...)` edasilükkamist.
- Ära muuda `resizeEvent`-is teksti ilma re-entry kaitse või järjekorda pandud uuenduseta.
- Ära märgi moodulit aktiivseks enne eduka `activate()` lõppu.
- Ära käsitle „Vali kõik” valikut võltsandmereana; kasuta eraldi kontrolli või menüüd.
- Enne kihi objektide lugemist kontrolli kihi kehtivust ja nõutud välju. Tühja vaste
  korral ära muuda valikut ega nähtavust; tagasta ja kuva kasutajale teade.
- Jagatud dialoogikäitumise jaoks eelista
  [`DialogHelpers`](ui/window_state/dialog_helpers.py)-it kohalikele lambdadele.

## 5. Asünkroonne elutsükkel ja lõimed

- Igal timeril, worker'il ja taustakäivitusel on üks selge omanik, mis hoiab viidet kuni
  töö tegeliku lõppemiseni ning peatab töö sulgemisel, tühistamisel ja plugina reload'il.
- Uus käivitus tühistab või asendab vana käivituse ühes kohas. Kasuta `run_id`-d,
  päringutokenit või samaväärset põlvkonnatunnust, et hilinenud callback ei saaks muuta
  uuema käivituse olekut.
- Lõpetamise signaal ja lõpptulemuse rakendamine toimuvad ühe käivituse kohta kõige rohkem
  ühe korra. Tühistatud käivitus ei teata õnnestumist.
- QObject'i kustutamisel ühendatakse ohtlikud signaalid lahti või kontrollitakse omaniku
  ja käivituse kehtivust enne callback'i edastamist.
- Qt widget'eid, dialooge ja muid GUI-objekte luuakse ning muudetakse ainult GUI-lõimes.
- Elavat `QgsMapLayer` objekti ei kasutata vabalt taustalõimes. Taustatööks eelista
  immutable sisendit või selleks sobivat `QgsFeatureSource` hetktõmmist; projekti, kihi ja
  UI muudatus rakendatakse GUI-lõimes.
- `processEvents()` ei ole taustatöötluse asendus. Seda võib kasutada ainult lühikeses,
  mõõdetud ja re-entry eest kaitstud voos; pika töö jaoks kasuta worker'it või etapiviisilist
  timerit.
- `QTimer.singleShot(...)` closure ei tohi olla ainus tühistamis- ega omandimehhanism.
  Korduvkäivitusega töö kasutab omatud timerit või kontrollitavat põlvkonnatunnust.

## 6. Jõudlus ja andmemahu eeldused

- Ära nimeta jõudlusprobleemi põhjust oletuse põhjal. Mõõda enne muudatust representatiivse
  andmemahu ja sama kasutusstsenaariumiga ning profileeri piisavalt, et leida tegelik kuum tee.
- Kihi- ja tabelitsüklite puhul hinda algoritmilist kasvu. Väldi kogu kihi või tabeli
  korduvat läbimist rea, tunnuse, värvimise või callback'i kohta.
- Eelista provideripoolset filtrit, batched-päringut ja ühe käivituse lookup'i üksikutele
  täisskaneeringutele, kui nende tulemuste semantiline samaväärsus on enne kontrollitud.
- Pärast jõudlust või andmevoogu muutvat refaktorit korda sama mõõtmist. Salvesta commit'i
  või PR-i kirjeldusse andmemaht, stsenaarium, enne/pärast tulemus ja teadaolevad piirid.
- Testi eraldi tühja, väikest ja realistlikult suurt ulatust. Üksnes unit-testide roheline
  tulemus ei tõesta QGIS-i UI reageerimisvõimet ega lõimeohutust.

## 7. Muudatuse vastuvõtukontroll

Enne ühendamist kontrolli:

1. Harude, pesastuse ja avaliku API hulk ei kasvanud põhjendamatult.
2. Sarnase olemasoleva lahenduse otsing tehti enne uue üksuse loomist.
3. Muudetud vastutusalal jäi alles üks omanik ja üks kasutusviis.
4. Käitumismuutus on tahtlik ning commit'i või PR-i kirjelduses nähtav.
5. Veateed logivad või tagastavad selge ebaõnnestumise; vaikivat fallback'i pole.
6. UI-s pole uut äriloogikat, tõlkefallback'i ega surnud olekut.
7. Avaliku sümboli muutmisel uuendati kõik kasutuskohad ja tehti impordi-/kompileerimiskontroll.
8. Muutunud äriloogika või teenusepiir on kaetud sihitud testiga.
9. Asünkroonse muudatuse test katab vähemalt taaskäivituse, tühistamise või omaniku
   sulgemise ning tõestab, et aegunud callback tulemust ei muuda.
10. Jõudlustundliku muudatuse põhjus ja tulemus on mõõdetud sama stsenaariumiga; mõõtmata
    oletust ei esitata põhjusena.
11. UI- või lõimemuudatuse korral tehti võimalusel QGIS-i runtime-suitsukontroll, mitte
    ainult mock'idel põhinev unit-test.
12. Käivitati puudutatud ala testid ning tulemus ja teadlikult tegemata kontrollid märgiti
    commit'i või PR-i kirjeldusse.

## 8. Dokumentatsiooni piir

- Kehtiv arhitektuuri- või käitumislepe kuulub `docs/development/` alla.
- Lõpetatud teostusetapi arutelu kuulub `docs/archive/` alla ega ole spetsifikatsioon.
- Kohalikud prompt'id, ideede töölauad ja ajutised katsemärkmed reposse ei kuulu.
- Dokumentatsiooni täielik jaotus on failis [docs/README.md](docs/README.md).
