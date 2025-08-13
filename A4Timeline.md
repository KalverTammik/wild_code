# A4Timeline.md

## Muudatuste logi

### 2025-08-12
**Teema:** Tooltipi akna visuaalne ühtlustamine ja tõlgete parandamine
**Tegevused:**
- Rakendatud tooltipi akna oliivroheline taust kõigile peaakna ja sidebar-i elementidele (QSS failid: `styles/Dark/tooltip.qss`, `styles/Light/tooltip.qss`).
- Parandatud sidebar-i "Ahenda/Laienda külgriba" nupu abiteksti tõlge, et see oleks alati keelefailist.
- Lisatud ThemeManagerisse automaatne tooltipi QSS laadimine, et kõik abitekstid oleksid visuaalselt ühtsed.
- Parandatud QssPaths klassi, et toetada TOOLTIP QSS viidet.

**Õppetund:**
- Tooltipi QSS tuleb laadida globaalselt, et see rakenduks kõigile elementidele.
- Tõlked peavad tulema alati keelefailist, mitte olla koodis kõvasti määratud.

---

### 2025-08-12
**Teema:** Ideede logi loomine
**Tegevused:**
- Loodud eraldi fail `IDEAS.md` arendusideede ja mõtete kogumiseks.
- Esimene idee: tooltipi QSS võiks olla kasutaja poolt seadistatav.
- Teine idee: keele valik otse peaaknast.

**Õppetund:**
- Eraldi ideede logi aitab arendusprotsessi paremini planeerida ja jälgida.

---

### 2025-08-12
**Teema:** Avalehe nupu lisamine headerisse
**Tegevused:**
- Lisatud headerisse avalehe ikooniga nupp (homeButton), mis avab Welcome page'i.
- Nupp ühendatud otse welcome page'i avamisega läbi callbacki.
- Parandatud lint-vea jaoks os import.

**Õppetund:**
- Callbacki abil saab headeri nupu funktsionaalsust paindlikult määrata.
- Visuaalse ja funktsionaalse muudatuse logimine aitab hiljem arendust jälgida.

---

Jätka logi iga muudatuse kohta, et hiljem oleks lihtne jälgida tehtud tööd ja õppida varasematest lahendustest.

---

### 2025-08-13
**Teema:** WelcomePage debug-siltide lüliti ja õppesektsiooni mustri dokumenteerimine
**Tegevused:**
- WelcomePage’i lisatud kontrollnupp (checkable) värviliste “FRAME:” siltide peitmiseks/näitamiseks.
- Nupu sildid eesti keeles: ON → “Peida FRAME sildid”, OFF → “Näita FRAME silte”.
- Lüliti ühendatud `LetterSection.set_debug(bool)` abil; `WelcomePage.set_debug(bool)` delegeerib alamsektsioonile.
- `LetterSection` ja `LetterIconFrame` said `set_debug()` lepingu; animatsioonil (`QPropertyAnimation`) on vanem ja viide `self`-is, et vältida GC-d.
- Parandatud taandevead `WelcomePage.__init__` sees – kogu UI ehitus (labelid, nupud, paigutused) on korrektselt meetodis.
- Rippmenüü seadistatud `AdjustToContents`; pealkirja/teksti labelitel `setWordWrap(True)`.
- Dokumenteeritud muster failis `copilot-prompt.md` jaotises “WelcomePage & Learning Section (Debug Frames) Pattern”.

**Õppetund:**
- Kõik `self.*` liikmete algväärtustused peavad jääma meetoditesse; pärast suuremaid muudatusi tee alati kiirkontroll süntaksi/taande vigade osas.
- Õpetuslikud/diagnostilised raamid peavad olema lülitatavad; tootmises on mõistlik vaikimisi peidetud.
- Teemastamine peab käima läbi `ThemeManager.apply_module_style(...)`; globaalset `setStyleSheet` ei tohi kasutada.
