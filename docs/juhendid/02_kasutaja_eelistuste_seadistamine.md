# Kasutaja eelistuste seadistamine

Kavitro kasutaja seadetes saab valida vaikimisi avaneva mooduli ning määrata, millised Kavitro kiirtööriistad kuvatakse QGIS-i kaardil. Samal kaardil näeb kasutaja ka oma konto andmeid, rolle ja moodulite kasutusõigusi.

Üldine ülevaade seadistuste salvestamisest ja lähtestamisest on juhendis [Kavitro seadistuste mooduli kasutamine](01_seadistuste_mooduli_kasutamine.md).

## Kasutaja seadete avamine

1. Ava QGIS-is Kavitro plugina aken.
2. Vali plugina külgribalt **Seaded**.
3. Oota, kuni kaardil **Kasutaja** kuvatakse sinu konto andmed.

Kasutaja kaart asub seadistuste mooduli alguses. Andmete laadimise ajal kuvatakse väljade asemel laadimise teade.

## Konto andmed ja rollid

Kasutaja kaardil kuvatakse:

- kasutaja nimi;
- e-posti aadress;
- kasutajale määratud rollid;
- moodulid, millele kasutajal on juurdepääs.

Need andmed saadakse Kavitro teenusest. Neid ei saa QGIS-i pluginas muuta.

Kui nimi, e-posti aadress või rollid on valed, pöördu Kavitro administraatori poole. Seadistuste muutmine ega QGIS-i projekti vahetamine ei muuda kasutaja õigusi.

## Moodulite juurdepääsu tähendus

Jaotises **Mooduli juurdepääs** kuvatakse **Avaleht** ja Kavitro moodulid.

- Tavaliselt kuvatud ja valitav moodul on kasutajale lubatud.
- Keelatud ning läbikriipsutatud moodulile kasutajal juurdepääsu ei ole.
- Märkeruut näitab, milline vaade on valitud vaikimisi avatavaks mooduliks.

**Oluline:** mooduli märkeruudu valimine ei anna kasutajale selle mooduli kasutusõigust. Õigused määratakse Kavitro teenuses ning plugin ainult kuvab nende hetkeseisu.

## Vaikimisi avatava mooduli valimine

Vaikimisi avatav moodul määrab, milline vaade avatakse uue Kavitro seansi alguses plugina akna esmakordsel näitamisel.

Vaikimisi mooduli valimiseks:

1. Leia kasutaja kaardilt jaotis **Mooduli juurdepääs**.
2. Klõpsa soovitud mooduli märkeruutu, mooduli nime või seda ümbritsevat ala.
3. Veendu, et valituks jäi õige moodul.
4. Vajuta seadistuste akna all nuppu **Kinnita**.

Korraga saab olla valitud üks vaikimisi moodul. Uue mooduli valimisel eemaldatakse valik eelmiselt moodulilt.

Kui soovid, et Kavitro avaneks üldvaatel, vali **Avaleht**. Kui eemaldad valiku parajasti valitud moodulilt ega vali uut moodulit, kasutab Kavitro samuti Avalehte.

Vaikimisi mooduli valik ei sunni juba avatud Kavitro akent kohe teise moodulisse liikuma. Kui avad sama akna uuesti sama seansi jooksul, säilitab Kavitro üldjuhul viimati aktiivse mooduli. Uus vaikimisi valik rakendub plugina akna järgmisel esmakordsel avamisel.

## QGIS-i kaardi tööriistad

Kasutaja kaardi jaotises **Tööriistad** saab QGIS-i kaardile lisada kaks teineteisest sõltumatut Kavitro paani:

- **Sisestuspaan**;
- **Otsingupaan**.

Mõlemat paani saab kasutada korraga. Samuti saab ühe paani sisse lülitada ja teise välja lülitada.

### Sisestuspaan

Sisestuspaan on QGIS-i kaardi paremas ülanurgas kuvatav vertikaalne kiirtoimingute riba. See võimaldab avada sagedamini kasutatavaid kaarditoiminguid ilma Kavitro menüüdes liikumata.

Sisestuspaanilt saab:

- alustada uue töö lisamist kaardilt;
- kasutada toimingut **Mis see on**, et tuvastada kaardilt aktiivse mooduliga seotud objekt;
- avada sidumata GIS-tööde kontrolli.

Üksiku toimingu kasutatavus sõltub kasutaja õigustest, vajalikest mooduliseadetest ja QGIS-i projekti kihtidest.

### Otsingupaan

Otsingupaan kuvatakse QGIS-i kaardi paremas ülanurgas. Selle kaudu saab otsida Kavitro objektide seast ja avada leitud objekti vastavas moodulis.

Otsingu kasutamiseks:

1. Sisesta otsinguväljale vähemalt kolm tähemärki.
2. Oota automaatse otsingu tulemusi või käivita otsing otsingunupuga.
3. Vali tulemuste loendist sobiv objekt.
4. Kavitro avab objekti tema moodulis.

Otsingutulemused sõltuvad kasutaja mooduliõigustest ja Kavitro teenuses olevatest andmetest.

## Kaardipaanide sisse- ja väljalülitamine

1. Ava **Seaded** ja leia kaart **Kasutaja**.
2. Leia jaotis **Tööriistad**.
3. Märgi **Sisestuspaan**, kui soovid näha kaardi kiirtoiminguid.
4. Märgi **Otsingupaan**, kui soovid näha kaardi otsingut.
5. Paani peitmiseks eemalda vastav märge.
6. Vajuta **Kinnita**.

Pärast kinnitamist kuvatakse või peidetakse valitud paanid kohe. Valikud salvestatakse QGIS-i profiili ning neid ei ole vaja igas QGIS-i projektis eraldi määrata.

## Mitme muudatuse salvestamine

Vaikimisi mooduli ja mõlema kaardipaani valikud võib muuta korraga. Kõik muudatused salvestatakse ühe nupuvajutusega.

1. Vali vaikimisi moodul.
2. Määra Sisestuspaani olek.
3. Määra Otsingupaani olek.
4. Vajuta **Kinnita**.

Kui lahkud seadistustest enne kinnitamist, saad muudatused salvestada, hüljata või jääda seadistuste moodulisse.

## Levinumad olukorrad

### Moodul on läbikriipsutatud ja seda ei saa valida

Kasutajal puudub selle mooduli kasutusõigus. Õigust ei saa anda seadistuste moodulis. Pöördu Kavitro administraatori poole.

### Valitud moodul ei avanenud

Kontrolli, et vajutasid pärast valiku tegemist nuppu **Kinnita**. Arvesta ka sellega, et juba sama seansi jooksul kasutatud Kavitro aken võib taastada viimati aktiivse mooduli. Vaikimisi valik rakendub akna järgmisel esmakordsel avamisel.

Kui valitud mooduli kohustuslikud kihid või eelistused on seadistamata, võib Kavitro suunata sind esmalt selle mooduli seadistuskaardile.

### Sisestus- või Otsingupaani ei kuvata

Kontrolli, et:

- vastava paani märkeruut on valitud;
- vajutasid pärast muudatust nuppu **Kinnita**;
- QGIS-i kaardiaken on nähtav;
- Kavitro kasutaja sessioon on aktiivne.

Kui paan ei ilmu ka pärast kontrolli, ava Kavitro aken uuesti või logi Kavitrosse uuesti sisse.

### Sisestuspaani nupp ei käivita toimingut

Veendu, et kasutajal on vastava mooduli õigus ning mooduli vajalikud põhi- ja arhiivikihid on seadistatud. Puuduva seadistuse korral võib Kavitro kuvada hoiatuse ja suunata seadistustesse.

### Otsing ei kuva tulemusi

Kasuta vähemalt kolme tähemärki. Kontrolli ka internetiühendust, aktiivset Kavitro sessiooni ja seda, et otsitav objekt kuulub kasutajale lubatud moodulisse.

## Kontrollnimekiri

Pärast kasutaja eelistuste seadistamist kontrolli, et:

- õige vaikimisi moodul on märgitud;
- vajalikud kaardipaanid on sisse lülitatud;
- muudatused on kinnitatud;
- Sisestuspaan kuvatakse QGIS-i kaardi paremas servas;
- Otsingupaan kuvatakse QGIS-i kaardi paremas ülanurgas;
- paanide toimingud avavad kasutajale lubatud Kavitro moodulid.
