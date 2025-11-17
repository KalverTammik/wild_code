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

---

### 2025-08-13
**Teema:** Sidebar Avalehe nupu viimine külgpaneelile ja headeri puhastamine
**Tegevused:**

- Lisatud aktiivse oleku QSS (gradient, vasak värviriba, bold font).
- Tõlked lisatud `sidebar_button_names_en/et.py` – võti `HOME`.
- Lisatud ikoonimajandus: korduvalt testitud erineva suurusega `icons8-home-*` failid; lõpuks standardiseeritud iconSize 25x25.
**Õppetund:**
- Pseudomoodul võimaldab koodi minimaalse muutusega lisada staatilise vaate navigeerimise loogikasse.
- Aktiivse oleku visuaalne tugevdamine parandab kasutaja ruumilist orientatsiooni.

---

**Teema:** Ikoonide ühtlustamine ja meta-funktsioonide dokitud footer
---

### 2025-08-15
**Teema:** Debug-loggeri refaktor ja print-lahenduste ühtlustamine
**Tegevused:**
- Lisatud tsentraliseeritud logger (`utils/logger.py`), mis on seotud peaakna DBG-nupuga.
- Kõik print() laused asendatud loggeri debug/info/error meetoditega, mis arvestavad lüliti olekut.
- Algne debug-olek tuletatakse WILDCODE_DEBUG env-muutujast või QGIS seadetest.
- Kontrollitud, et kõik muudatused läbivad süntaksi/lint-kontrolli.
- Parandatud ContractUi ja StatusFilterWidgeti taandevead loggeri integreerimisel.
**Õppetund:**
- Tsentraliseeritud logimine võimaldab arenduse diagnostikat mugavalt sisse/välja lülitada.
- Print-lahenduste ühtlustamine väldib segadust ja aitab arendusprotsessi jälgida.

---
**Tegevused:**
- Ühtlustatud Avaleht, Projektid, Lepingud, Seaded ikoonide suurus 25x25 (koodis eksplitsiitselt `setIconSize`).
- Projekti ikoon vahetatud `icons8-microsoft-powerpoint-30.png` (suurus piiratud 25x25) ühetaolisuse nimel.
- Lepingute (ContractsModule) ikoon uuendatud `icons8-policy-document-25.png`.
- Seadete ikoon vahetatud `icons8-settings-25.png` (varasema gear 50px asemel).
- Lisatud dokitud alumine footer (`SidebarFooterBar`) meta-nuppudele ja migreeritud Seaded sinna.
- Lisatud Abi (Help) nupp footerisse koos signaaliga `helpRequested` ja ikooniga (50px baaspilt, skaleeritud 25px peale).
- Refaktoreeritud varjuefektid `_apply_section_shadows` toetama uut footer konteinerit.
- QSS Dark/Light uuendatud: footer bar gradient taust, eraldi hover ja active stiilid.
**Õppetund:**
- Dokitud meta-riba eraldab sisunavigatsiooni ja rakenduse halduse / toe funktsioonid; parandab IA selgust.
- Ikoonide ühtne mõõtskaala vähendab visuaalset müra ja lihtsustab teema hooldust.
- Eraldi footer võimaldab tulevikus lisada logout / versiooniteabe ilma peamist naviplokki koormamata.

---

### 2025-08-14
**Teema:** Vastutajate ja ideede täiendus – API võtme aegumise käsitlus
**Tegevused:**
- Lisatud `IDEAS.md` failis uus idee: aegunud API võtme automaatne käsitlemine (401/403 interceptor, login retry, katkestatud päringute taastamine, logid "token_expired", "relogin_success", "relogin_cancel").
- Defineeritud piirang: üks automaatne retry, et vältida lõputut tsüklit.
**Õppetund:**
- Keskne autentimisvea interceptor vähendab korduskoodi ja parandab UX-i, vältides vaikseid tõrkeid.
- Sündmuste logimine varakult lihtsustab hilisemat monitooringut ja vigade analüüsi.

---

### 2025-08-14
**Teema:** Animatsioonide keskne utiliit ja DevControlsWidget stabiilsus; DateWidget üle tähtaja hoiatus
**Tegevused:**
- Ekstraheeritud jagatud animatsiooniutiliidid `utils/animation` paketti:
	- `pulses.py` (create_colorize_pulse, build_glow_pulse), `groups.py` (AnimationGroupManager), `palettes.py` (teemastatud halo paletid), `controller.py` (AnimationController).
- DevControlsWidget:
	- Ühtlustatud halo: pulse aktiveerub, kui DBG või FRAME on ON; DBG korral oranž/roosa, muidu tsüaan/teal; nupud ei liigu.
	- Viidud üle AnimationControllerile; `closeEvent` peatab animatsioonid korrektselt.
	- Ikoon teemastatud `ThemeManager.get_qicon(...)` kaudu; tooltipid i18n LanguageManagerist.
- Loodud lihtne `DateWidget` (silt + QDateEdit) ning lisatud üle tähtaja (overdue) punakas merevaigukarva vilkuv hoiatus sildile.
- IDEAS.md täiendused: kontrolleri rakendamine teistes vidinates; animatsioonide test-harness; DateWidget "due soon" pehme vihje; moodulikaartide punase hoiatuspulsi ühtlustamine.

**Õppetund:**
- Keskne kontroller ja utiliidid vähendavad koodi dubleerimist ning hoiavad visuaalse käitumise kooskõlas.
- Geomeetria animatsioone (y-offset) tuleks vältida peaelementidel; efektipõhine pulse on piisavalt informatiivne ja stabiilne.

---

### 2025-08-15
**Teema:** Kaartide renderdamise parandused ja InfoCardHeader eraldamine
**Tegevused:**
- Parandatud ModuleFeedBuilder: taastatud korrektne `create_item_card` struktuur (vasak: InfoCardHeader + liikmed + ExtraInfo; parem: staatus); varem lisatud `add_items_to_feed` abimeetod on nüüd eemaldatud (vastutus kaartide lisamisel elab BaseUI-s).
- Staatuses peidetud privaatsuse ikoon (kuvatakse nüüd pealkirja reas InfoCardHeader-is), väldib topeltkuvamist.
- Lisatud kerge tilk varju kaartidele (`QGraphicsDropShadowEffect`).
- Loodud eraldi InfoCardHeader (privaat ikoon, projekti nimi, number-märk, sildid/hover, klient) ja ühendatud feedi kaartidega.
- Diagnostika: lisatud ühe-realine logi „[ModuleFeedBuilder] Added N card(s)“ kaarte lisamisel.

**Õppetund:**
- Suurte failide refaktoorimisel on ohutu liikuda väikeste sammudega ja vahepeal kompileerida; taandused kipuvad murduma.
- Korduma kippuvad elemendid (header) tasub eraldada korduvkasutatavaks komponendiks; vähendab regressiooniriski.

### 2025-08-15
**Teema:** Plugin ei laadinud – eemaldatud tühi/staatiline DateWidget import
**Tegevused:**
- Eemaldatud `widgets/__init__.py` failist aegunud rida `from .DateWidget import DateWidget`, mis põhjustas `ModuleNotFoundError` (fail oli varem eemaldatud pärast refaktorit).
- Plugin laadib taas korrektselt; ei ole teisi sõltuvaid viiteid DateWidget-ile.

**Õppetund:**
- Pärast suuremat harude liitmist tasub otsida orvuks jäänud ekspordid (`__init__.py`) ja puhastada need, et vältida käivitusaegseid import-tõrkeid.

---

### 2025-08-15
**Teema:** DevControlsWidget – DBG pulse eemaldatud, Frames pulse viidud nupule; handleri parandus
**Tegevused:**
- Liigutatud halo/varjuefekt otse Frames nupule (varem oli konteinerraamil), et pulse oleks visuaalselt selgelt seotud nupuga.
- Eemaldatud DBG nupu pulse; DBG jääb staatiliseks (colorize strength 0.0).
- Parandatud `AttributeError: 'DevControlsWidget' object has no attribute '_on_local_frames_toggled'` – lisatud kohalikud `_on_local_frames_toggled` ja `_on_local_debug_toggled` handlerid, mis kutsuvad `AnimationController.apply_state(...)`.
- Uuendatud `AnimationController`: glow pulse aktiveerub nüüd ainult siis, kui Frames on ON; Frames-i colorize pulse säilib; DBG pulse on keelatud.
- Paigutus püsib stabiilselt horisontaalne; QSS rakendub läbi `DevControls.qss`.

**Õppetund:**
- Efekti sihtimine otse nupule annab selgema UX-i, kuid Qt lubab ühel vidinal korraga vaid ühe `graphicsEffect`i – kui on vaja korraga grupi-halo ja per-nupu efekte, on eraldi konteiner kasulik. Keskne kontroller hoiab käitumise ühtse ja koodi puhtana.
