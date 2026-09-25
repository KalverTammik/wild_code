# Tööde nimekirja sortimine ja grupeerimine

Esimene versioon on Tööde moodulis. „Sordi” ja „Grupeeri” nupud paiknevad filtrikasti kõrval eraldi plokis ning avavad menüüd. Valitud suund või grupeerimistunnus on menüüs märgitud; hõljuk kirjeldab aktiivset valikut. Valikud salvestatakse eraldi kasutaja, API-keskkonna ja mooduli järgi. Filtrite värskendamine säilitab need.

## Sortimise ulatus

| Valik | Ulatus | Suunad |
| --- | --- | --- |
| Vaikimisi järjekord | Senine serveri vastuse järjekord | — |
| Pealkiri | Kogu filtreeritud tulemus | A–Z / Z–A |
| Tähtaeg, algusaeg, loomise aeg, muutmise aeg | Kogu filtreeritud tulemus | Varasem / hilisem ees |
| Staatus, liik, vastutaja | Laaditud kanded | A–Z / Z–A |
| Prioriteet | Laaditud kanded | Kõrgem / madalam ees |

Kasutaja kinnitas 12.09.2026 kohaliku sortimise erandi: erijuhud tuleb menüüs tähistada sõnadega „laaditud kannetes”. Sama piirang on valiku kasutamise ajal nähtav nimekirja jaluses. Kõiki tulemusi ei laadita kohaliku sortimise pärast automaatselt alla.

Kuupäevasortimisel küsitakse esmalt kuupäevaga kanded ja seejärel kuupäevata kanded. Mõlemad päringud säilitavad sama filtri. Võrdsete serveriväärtuste lisajärjestus on ID; puuduvad kuupäevad jäävad mõlemas suunas lõppu. Kahe päringuosa ajal ei esitata ühe osa serveriarvu kogu nimekirja koguarvuna. Sortimisviisi vahetamine tühjendab sobimatuks muutunud kursori ja laadimispuhvri.

## Grupeerimine

Valikud: grupeerimata, staatus, liik, prioriteet, vastutaja ja tähtaja seis. Grupid sisaldavad laaditud kandeid; päises on näiteks „Mari Maasikas · 5 laaditud”. Uute lehekülgede lisandumisel võivad lisanduda grupid ja nende arvud suureneda. Valitud sortimine kehtib grupi sees.

- Puuduva vastutajaga kanded on grupis „Vastutaja määramata”.
- Mitme vastutajaga töö ilmub iga vastutaja grupis. Üldloendur loeb unikaalseid töö ID-sid; grupiarvude summa võib olla suurem.
- Tähtaja seis: üle tähtaja, täna, homme, sel nädalal, järgmisel nädalal, hiljem, lõpetatud ja tähtajata. Grupid ei kattu; näiteks homne esmaspäev on grupis „Homme”. Lõpetatuks loetakse süsteemi staatuse tüüpi `CLOSED`.
- Kuupäevarühmad arvutatakse kohaliku kuupäeva alusel nimekirja ümberpaigutamisel, näiteks uue lehe laadimisel või valiku muutmisel.
- Gruppe saab avada/sulgeda ükshaaval või menüü kaudu kõiki korraga. Suletud olek säilib uute lehekülgede lisandumisel.
- Kõigi gruppide sulgemine peatab vaate automaatse täitmise; gruppide avamisel saab laadimine jätkuda.
- Kaardil staatuse muutmine uuendab töö kuvatud eksemplare ja grupikuuluvust. Serveris sorditud vaade laaditakse sel juhul uuesti, et järjekord püsiks õige.

## Laadimise parandused (12.09.2026)

Grupeerimise eemaldamisel nähtud „No values found!” oli ekslik tühja vaate teade: järgmine leht oli tühi, kuid varem laaditud tööd olid alles. Tühi lõppleht ei näita enam seda teadet, kui kaardid või kuvamist ootavad kirjed on olemas. Päris päringuviga jääb nähtavaks ka grupeerimise muutmisel. Tõeliselt tühi tulemus kasutab tõlgitud teadet.

Tööde nimekirja päringud ja kaardikihi hulgiuuenduse serveripäringud toimuvad taustal. Uue vaate esimese lehe ootel kuvatakse „Laadimine...”. Iga laadija käitab korraga üht päringut; kiirete muudatuste korral jääb ootele ainult viimane soov. Filtri, sortimise, üksiku töö või mooduli vahetamise järel vana vastust vaatesse ei rakendata. Üksnes grupeerimise muutmine ei vaja uut serveripäringut.

QGIS-i kihtide lugemine ja muutmine toimub endiselt kasutajaliidese lõimes. Taustale antakse ainult tööde tunnused. Vastuse saabumisel kontrollitakse kihti, seanssi ja redigeerimisolekut ning jäetakse vahele objektid, mida kasutaja jõudis päringu ajal muuta. Moodulist lahkumine tühistab poolelioleva vastuse rakendamise.

Kaartide lisamine koondatakse lühikese kuvamisintervalli sisse. Paigal püsivaid kaarte ei eemaldata ega lisata uuesti paigutusse ning igal lehel ei rakendata kogu nimekirjale uuesti kujundust. Vaate täitmine jätkub päringu või kuvamise lõppedes; serverivastust ei oodata pidevas taimeritsüklis.

Paranduste järel läbis kogu testikomplekt kontrolli: **195 testi, neist 192 edukat ja 3 vahele jäetud**. Lisandus 15 regressioonitesti. Aeglase serveri katses hoiti vastust kontrollitult ootel ning kinnitati, et kasutajaliidese sündmused jätkuvad ja päringud ei kattu. Mälukihiga kontrolliti tegelikku QGIS-i salvestamist, päringu ajal tehtud muudatuse säilimist, redigeerimisrežiimi, kihi vahetamist ja moodulist lahkumist. Need katsed ei mõõda päris serveri vastamisaega.

Käsitsi korduskatse pärast plugina uuesti laadimist:

1. Vaheta mitu korda Tööde ja teise mooduli vahel. Kontrolli, et päringu ajal saab kasutajaliidest kasutada ning esimese lehe ootel on laadimisteade.
2. Grupeeri tööd, eemalda grupeerimine ning keri nimekirja lõppu. Kaardid peavad säilima ilma tühja vaate teateta.
3. Muuda aeglase laadimise ajal sortimist või filtrit; ava otsingust üks töö. Lõppvaates peavad olema viimase valiku tulemused.
4. Lahku Töödest laadimise ajal ja naase. Vana vastus ei tohi taastada eelmise vaate kaarte.
5. Kontrolli väikeses testkihis, et tavapärane serverist uuendamine töötab ning päringu ajal tehtud kohalikku muudatust ei kirjutata üle.

## Kontroll ja piirid

Serveri skeemi introspektsioon on keelatud. Autentimata lugemispäringute valideerimine tunnistas Tööde `orderBy` sisendit, pealkirja/kuupäevade/ID veerge ning kuupäeva puudumise tingimusi. Vastutaja sortimisveerg `RESPONSIBLE` lükati tagasi. Staatuse ja liigi veerud on olemas, kuid nende nime järgi järjestamist ning prioriteedi sisulist järjekorda serveriandmetega ei kinnitatud; need valikud töötavad seetõttu kohalike reeglitega.

Päris serveriandmetega sortimise tulemust pole selles etapis kontrollitud. Avatud QGIS-i seanssi ei laaditud automaatselt uuesti. Katsetes asendatakse API vastused ning kujunduse kontrollis kasutatakse tegelikke Qt-kaarte näidisandmetega heledas ja tumedas teemas.

Kontrolli tulemus QGIS 3.40.13 Pythoni keskkonnas: 21 uut sihitud testi läbisid kontrolli; kogu testikomplektis 180 testi, neist 177 edukat ja 3 vahele jäetud. Hõlmatud on sortimissuunad, puuduvad väärtused, kahe päringuosa lehekülgjaotus, viga ja korduskatse, filtri säilimine, üksiku töö avamine, eelistuste eraldamine, mitme vastutaja grupid, sulgemine, vana puhvri eemaldamine ning tegeliku kaardi staatusemuudatuse jõudmine kõikidesse eksemplaridesse.

Käsitsi katse pärast plugina uuesti laadimist:

1. Vali Töödes väike tulemuste hulk, seejärel „Sordi → Tähtaeg → Varasem ees”. Laadi juurde ja kontrolli järjekorda ning tähtajata tööde asumist lõpus.
2. Vaheta suunda ja sortimistunnust enne järgmise lehe laadimist; vana järjekorra kaarte ei tohi uude tulemusse lisanduda.
3. Vali „Grupeeri → Vastutaja”. Kontrolli mitme vastutajaga tööd ja üldloenduri unikaalset arvu.
4. Vali „Sordi → Prioriteet”. Kontrolli mõlemat suunda ning nähtavat „laaditud kannetes” selgitust.
5. Sulge grupp, laadi järgmine leht ja ava grupp uuesti. Kontrolli ka kõigi gruppide sulgemist/avamist.
6. Muuda testtöö staatust: töö peab liikuma õigesse staatusegruppi. Vastutaja järgi grupeerimisel peavad uuenema selle töö kõik eksemplarid.
7. Kontrolli „Grupeerimata”, filtrite muutmist, otsingust ühe töö avamist ja moodulisse naasmisel valikute taastumist.
8. Korda heledas ja tumedas teemas, sealhulgas klaviatuuriga menüüdes liikumine ja nende sulgemine Esc-klahviga.
