# Dokumentatsiooni kaart

See kaust sisaldab ainult versioonihalduses säilitamist väärivat dokumentatsiooni.
Markdown- ja `docs/`-failid jäetakse LIVE-plugina ZIP-paketist välja.

## Avalik lähtekoha dokumentatsioon

- Projekti ülevaade: [`../README.md`](../README.md)
- Release'i protsess: [`../RELEASE.md`](../RELEASE.md)
- Refaktoreerimise püsireeglid: [`../REFACTOR_RULES.md`](../REFACTOR_RULES.md)

Need kolm faili jäävad juurkausta, sest need on arendaja peamised sisenemispunktid.

## Kasutajajuhendid

Kaust [`juhendid/`](juhendid/) sisaldab Kavitro kasutus- ja seadistusjuhendeid.
Alamkaust `juhendid/Nupud/` koondab nuppude lühiülevaated ja detailauditid.
Need failid on dokumentatsiooni allikmaterjal, kuid neid ei pakendata pluginaga kaasa.

## Arendaja referentsid

Kaust [`development/`](development/) sisaldab kehtivaid tehnilisi leppeid ja
hooldusjuhendeid:

- release'i DEV/LIVE seadistuse detailne referents;
- turvalise salvestuse poliitika;
- geomeetria payload'i lepe;
- aktiivsete komponentide tehnilised kirjeldused.

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
