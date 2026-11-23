# Dokumentatsiooni kaart

See kaust sisaldab ainult versioonihalduses säilitamist väärivat dokumentatsiooni.
Markdown- ja `docs/`-failid jäetakse LIVE-plugina ZIP-paketist välja.

## Avalik lähtekoha dokumentatsioon

- Projekti ülevaade: [`../README.md`](../README.md)
- Release'i protsess: [`../RELEASE.md`](../RELEASE.md)
- Refaktoreerimise püsireeglid: [`../REFACTOR_RULES.md`](../REFACTOR_RULES.md)

Need kolm faili jäävad juurkausta, sest need on arendaja peamised sisenemispunktid.

## Kasutajajuhendid

Kasutajajuhendid on Kavitro abikeskuses: <https://help.kavitro.com/et>. Plugin avab
mooduli juhendi lingi kaudu (`constants/help_urls.py`).

Kaust [`juhendid/Nupud/`](juhendid/Nupud/) koondab plugina nuppude lühiülevaated ja
nende detailauditid (eeldused, veateed, avatud leiud). Neid ei pakendata pluginaga kaasa.

## Arendaja referentsid

Kaust [`development/`](development/) sisaldab kehtivaid tehnilisi leppeid ja
hooldusjuhendeid:

- release'i DEV/LIVE seadistuse mall (`release_setup_reference.md`, selle turvalisust
  kontrollib `tests/test_release_workflow_security.py`);
- turvalise salvestuse poliitika;
- tööde geomeetria lepe;
- kinnistute impordi päringupiirangud;
- jagatud komponentide tehnilised kirjeldused.

Arendaja referents peab kirjeldama praegu kehtivat käitumist. Kui kirjeldatud
komponent eemaldatakse või lahendus asendatakse, tuleb dokument uuendada või arhiivi
viia samas muudatuses.

## Auditid

Kaust [`audits/`](audits/) sisaldab välisauditi algset hetkepilti ja sellele järgnenud
otsuseid. Auditmaterjal ei ole kasutajajuhend ega rakenduse runtime-sisu.

## Arhiiv

Kaust [`archive/`](archive/) sisaldab ajaloolist refaktorilogi ja lõpetatud
teostusetappide märkmeid. Arhiiv ei ole kehtiva lahenduse spetsifikatsioon ning sellele
ei tohi uue koodi kavandamisel tugineda ilma tegelikku koodi kontrollimata.

## Mida repos mitte hoida

Reposse ei lisata:

- tühje ideede nimekirju ega isiklikke ülesandeloendeid;
- AI- või editoripõhiseid dubleerivaid prompt-faile;
- ajutisi kavandeid, ekraanipilte ja ekspordiarhiive;
- ühekordseid katsetulemusi, kui need ei põhjenda säilitatavat tehnilist otsust;
- muudatuste kronoloogiat püsireeglites — see kuulub commit'i või PR-i kirjeldusse.

Vajalik kohalik töömaterjal hoitakse väljaspool plugina tööpuud. Kui materjal peab
ajutiselt tööpuus olema, peab selle asukoht olema `.gitignore`-is.
