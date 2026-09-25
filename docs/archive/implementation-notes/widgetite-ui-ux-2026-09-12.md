# Moodulikaartide UI/UX: 12.09.2026

Kasutajaga kokku lepitud ulatus:

- Kasutajate pealkirjad säilivad tervikuna.
- Staatuse värviriba ja olemasolevate kaardinuppude mõõdud säilivad.
- Detaili avamise sakk jääb kaardi alumisele servale. Ellipsi asemel näitab suunanool avatud/suletud olekut; selgitus ja klaviatuurifookus on mõlemas teemas nähtavad.
- Kirjelduse ja metaandmete struktuuri ning üldist kohanduvat paigutust käsitleme hiljem.
- Faili pisipilt/ikoon on nime kõrval. „Vaata kõiki faile (N)” avab olemasoleva failidialoogi; seal saab faile vaadata ja hallata.
- Vastutajata kandel kuvatakse tühi avatar. Klõps või Enter/tühik avab liikmed ja selgituse „Vastutaja määramata”. Määratud vastutajatel säilib hõljuk; klõpsuga näeb täielikku liikmeloendit.
- Detailide ja faililoendi päringud töötavad taustal. Laadimisviga pakub korduskatset. Kaardi sulgemine või eemaldamine päringu ajal ei ava seda hilise vastuse saabumisel uuesti.

Kohalikud kontrollid kasutavad näidisandmeid ja asendatud API-vastuseid. Need ei vaja kliendi andmebaasi. Hõlmatud on aeglane vastus, viga ja korduskatse, kaardi eemaldamine, avamise/sulgemise olek, vastutajata ning paljude liikmetega kanded ja täieliku faililoendi avamine. Kujundust kontrollitakse QGIS-i Qt-keskkonnas heleda ja tumeda teemaga.

Kontrolli tulemus QGIS 3.40.13 Pythoni ja Qt keskkonnas:

- 14 sihitud testi läbisid kontrolli. Lisaks eelnevale kontrolliti taustal saabuvate failide järel kaardi kõrguse uuendamist, üle 200 faili sisaldavat loendit ning vigase lehekülgjaotuse käsitlemist laadimisveana.
- Kogu testikomplekt: 159 testi, neist 156 edukat ja 3 vahele jäetud.
- Tegelikud Qt-kaardid ja liikmeloend renderdati näidisandmetega mõlemas teemas ning kontrolliti visuaalselt.
- Avatud QGIS-i seanssi ei laaditud uuesti ja päris serveriandmetega kasutuskatset ei tehtud.

Lühike käsitsi katse pärast plugina uuesti laadimist:

1. Ava töö detail alumisest sakist: nool muutub, päringu ajal kuvatakse „Laadin…” ja seejärel sisu.
2. Sulge detail laadimise ajal ning ava teine kaart: esimene peab jääma suletuks ka vastuse saabumisel.
3. Katseta laadimisviga ja „Proovi uuesti” tegevust; edukas vastus asendab veateate.
4. Klõpsa vastutajata kande tühjal avataril: kuvatakse määramata vastutaja selgitus ja kõik liikmed. Kontrolli ka ilma liikmeteta kannet ning sulgemist Esc-klahviga.
5. Ava faililoendi „Vaata kõiki faile (N)”: loendi arv ja failid peavad vastama kaardil laaditud andmetele. Kontrolli faili eelvaadet.
6. Korda heledas ja tumedas teemas; kontrolli ka teema vahetamise järel uuesti avatud liikmeloendit.
