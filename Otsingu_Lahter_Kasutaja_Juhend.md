# Otsingu Lahter Kasutaja Juhend (UI/UX Fookus)

## Otsingu Lahteri Asukoht ja Välimus

**Asukoht:** Otsingu lahter asub päises (header) keskel, pealkirja ja abi nupu vahel.

**Välimus:**
- **Laius:** 220 pikslit (fikseeritud)
- **Kõrgus:** Standardne tekstivälja kõrgus
- **Placeholder tekst:** "Otsi..." (eesti keeles)
- **Visuaalne efekt:** Teal värvi (9, 144, 143) varjutus efekt (blur radius 14px)
- **Tööriistavihje:** "Funktsioon veel ei tööta" (kui hõljutad hiirt)

## Mida Kasutaja Saab Teha

### ✅ Saab:
1. **Kirjutada otsingusõnu** - minimaalselt 3 tähemärki
2. **Oodata automaatset otsingut** - 1.5 sekundi viivitus pärast viimast tähemärki
3. **Vajutada Enter klahvi** - käivitab otsingu kohe
4. **Vaadata tulemusi rippmenüüs** - ilmub otsingu lahtri all
5. **Klõpsata tulemustel** - navigeerib vastavasse moodulisse
6. **Laiendada tulemusi** - "Show X more" link mooduli kohta
7. **Sulgeda tulemused** - ESC klahv või klikk väljaspool
8. **Sulgeda ristist (×)** - paremas ülanurgas

### ✅ Saab (tulemuste vaatamine):
- **Moodulipõhine grupeerimine** - tulemused on grupeeritud moodulite kaupa
- **Tulemuste arv** - näitab iga mooduli kohta tulemuste arvu
- **Piiratud kuvamine** - alguses kuni 5 tulemust mooduli kohta
- **Laiendamine** - "Show X more" link lisatulemuste jaoks

## Mida Kasutaja Ei Saa Teha

### ❌ Ei saa:
1. **Otsida vähem kui 3 tähemärki** - automaatselt ignoreeritakse
2. **Otsida tühja välja** - vajab vähemalt 3 tähemärki
3. **Muuta otsingu viivitust** - fikseeritud 1.5 sekundit
4. **Otsida väljaspool süsteemi** - ainult sisemine andmebaas
5. **Salvestada otsinguajalugu** - ei mäleta eelmisi otsinguid
6. **Filtreerida tulemusi** - ainult tekstipõhine otsing
7. **Otsida mitut sõna korraga** - ainult üks otsingusõna
8. **Kopeerida tulemusi** - ainult vaatamine ja navigeerimine

### ❌ Puuduvad funktsioonid:
- **Otsingu ajalugu** - ei mäleta eelmisi otsinguid
- **Täpsemad filtrid** - ainult tekstipõhine otsing
- **Otsingu soovitused** - ei paku sarnaseid termineid
- **Otsingu salvestamine** - ei saa salvestada lemmikotsinguid
- **Ekspordi tulemused** - ainult kuvamine
- **Otsingu statistika** - ei näita populaarseid otsinguid

## Kasutaja Kogemus (UX)

### Positiivsed aspektid:
- **Intuitiivne asukoht** - päises, alati nähtav
- **Automaatne viivitus** - ei koorma süsteemi liigse otsinguga
- **Selge visuaalne tagasiside** - placeholder ja tööriistavihje
- **Kontekstuaalne navigeerimine** - klikk viib õigesse moodulisse
- **Paindlik sulgemine** - ESC, klikk väljaspool või rist

### Võimalikud täiustused:
- Lisada tööriistavihje mis seletab kuidas otsing töötab
- Lisada kiirklahv otsingu fokuseerimiseks (nt Ctrl+F)
- Lisada otsinguajalugu
- Lisada täpsemad filtrid
- Lisada mitme sõna otsing
- Lisada tulemuste eksport

## Tulemuste Rippmenüü

### Välimus:
- **Asukoht:** Otsingu lahtri all, vasakult joondatud
- **Laius:** Suurem kui otsingu lahter (kohandub sisule)
- **Taust:** Läbipaistev taust teemavärvidega
- **Sulgemisnupp:** × paremas ülanurgas

### Sisu:
- **Mooduli päis:** "MOODULINIMI (tulemuste_arv)" - rasvases kirjas
- **Tulemused:** "• Pealkiri" - rohelise värviga
- **Rohkem link:** "-- Show X more --" - kursiivis, halli värviga
- **Tulemuste puudumine:** "No results found for 'otsingusõna'" - halli värviga

## Testimise Stsenaariumid

### Edukas stsenaarium:
1. Klõpsa otsingu lahtril
2. Kirjuta vähemalt 3 tähemärki
3. Oota 1.5 sekundit või vajuta Enter
4. Kontrolli et tulemused ilmuvad rippmenüüs
5. Klõpsa tulemusel - peaks navigeerima vastavasse moodulisse

### Veastsenaariumid:
1. **Liiga lühike otsing:** Kirjuta 1-2 tähemärki - peaks ignoreerima
2. **Tulemuste puudumine:** Kirjuta olematu termin - peaks näitama "No results found"
3. **Sulgemine:** Vajuta ESC - peaks sulgema rippmenüü
4. **Väline klikk:** Klõpsa väljaspool - peaks sulgema rippmenüü

## Tehnilised Detailid (Testijatele)

- **Objekti ID:** `headerSearchEdit`
- **Minimaalne pikkus:** 3 tähemärki
- **Viivitus:** 1500ms (1.5 sekundit)
- **Maksimaalne tulemuste arv:** 5 alguses, seejärel kõik
- **Otsingu tüübid:** PROPERTIES, PROJECTS, TASKS, SUBMISSIONS, EASEMENTS, COORDINATIONS, SPECIFICATIONS, ORDINANCES, CONTRACTS
- **API lõpp-punkt:** GraphQL search query
- **Keel:** Eesti keel (fikseeritud)

## Praegune Staatus

**⚠️ Tähelepanu:** Otsingu funktsioon näitab tööriistavihjes "Funktsioon veel ei tööta", mis tähendab et see ei pruugi veel täielikult töötada. Testige ettevaatlikult ja dokumenteerige kõik probleemid.

---

*Dokument koostati:* 3. september 2025
*Versioon:* 1.0
*Autor:* Testimismeeskond</content>
<parameter name="filePath">c:\Users\Kalver\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\wild_code\Otsingu_Lahter_Kasutaja_Juhend.md
