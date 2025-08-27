

# 🟨 **REEGLID**

Siia faili kogume kõik arendusideed, mõtted ja tulevased plaanid. Ideede faili sisu on jagatud kolme plokki: Reeglid, Uued ideed ja Lõpetatud ideed.
Kui tekib uus idee, lisatakse see automaatselt plokki "Uued ideed" koos lisamise kuupäeva, vastutaja ja lühikirjeldusega. Selle ploki ideede ette tuleb staatus TEHA (alati esimene valik) või POOLELI.
Kui idee on läbi käidud ja korraldus antud see lõpetada, siis liigub see automaatselt "Lõpetatud ideed" plokki ja saab staatuse idee kirjelduse ette LÕPETATUD ning lisaks alustamise kuupäevale ka lõpetamise kuupäeva.

Näide uue idee lisamiseks:

🟢 TEHA YYYY-MM-DD: <idee pealkiri>
	- Vastutaja: <nimi>
	- Lühikirjeldus või peamised sammud
```
## Vastutajate legend
- 🟠 Anneli
- 🔵 Kalver
- ⚪ Määramata

# 🟩 **UUED IDEED**
# 🟢 TEHA 2025-08-19: Kontrolli OverdueCounterWidgeti
	- Vastutaja: Kalver
	- Kontrolli, kas OverdueCounterWidget töötab ootuspäraselt ja kas loendamine ning kuvamine on korrektne.

� POOLELI 2025-08-23: Moodulite teema vahetuse meetodite standardiseerimine
	- Vastutaja: Kalver
	- Ühtlustada kõikide moodulite teema vahetuse meetodid (nt retheme_project, retheme_contract jne) ja tagada, et dialog.py kasutab õigeid meetodeid. Vajadusel lisada puuduvad meetodid moodulitesse.
	- **Tehtud tööd (27.08.2025):**
		- Standardiseeritud meetodite nimed: `retheme_projects()`, `retheme_contract()`, `retheme_settings()`, `retheme_user_test()`
		- Lihtsustatud arhitektuur: asendatud keerulised stiili värskendused (`setStyleSheet("")/unpolish/polish`) otsese QSS rakendamisega
		- Lisatud `retheme()` meetodid DataDisplayWidgets komponentidele (StatusWidget, MembersView, ModuleFeedBuilder)
		- Parandatud olemasolevate kaartide teema värskendamine
		- Teema-sõltuvad varju värvid kaartidele ja avataritele
		- Kõik failid kompileeruvad edukalt, süntaksivigu pole
	- **Järelejäänud töö:**
		- Testida lihtsustatud lähenemist reaalses kasutuses
		- Kontrollida WelcomePage'i kodeeritud värvide komplekssust vs kasulikkust
		- Vajadusel täiendavad optimeerimised jõudluse parandamiseks
	
🟢 Universaalne päise- ja jaluseala moodulitele
**Kuupäev:** 2025-08-16
**Staatus:** TEHA
**Vastutaja:** ⚪ Määramata
**Kirjeldus:**
Luua universaalne päiseala (toolbar) ja jaluseala (footer), mis ehitatakse mooduli konfiguratsiooni põhjal. Päises saab olla filtreid, nuppe, silte, jne; jaluses loendurid, infotekstid, kiirtoimingud. Iga moodul annab oma tööriistade/infotööriistade konfiguratsiooni, mille põhjal päis/jalus ehitatakse dünaamiliselt. Võimaldab paindlikku ja hooldatavat UI-d kõigile moodulitele.


**Näidis tool-config dict päise jaoks:**
```python
def get_tools(self):
	return [
		{"type": "filter", "name": "status", "widget": StatusFilterWidget},
		{"type": "filter", "name": "type", "widget": TypeFilterWidget},
		{"type": "button", "name": "clear", "icon": ICON_CLEAR, "callback": self.clear_filters},
		{"type": "label", "name": "counter", "getter": self.get_counter_text},
		# ...more tools...
	]
```

**Näidis tool-config dict jaluse jaoks:**
```python
def get_footer_tools(self):
	return [
		{"type": "label", "name": "loaded_count", "getter": self.get_loaded_count_text},
		{"type": "label", "name": "total_count", "getter": self.get_total_count_text},
		{"type": "button", "name": "export", "icon": ICON_EXPORT, "callback": self.export_data},
		# ...more footer tools...
	]
```

🟢 Värviline ja mänguline kujundus
**Kuupäev:** 2025-08-12
**Staatus:** TEHA
**Vastutaja:** ⚪ Määramata
**Kirjeldus:**
Taust võiks olla gradient (nt helesinine → valge), mitte lihtsalt hall.
Letter selector võiks olla suur ja piltidega (nt “A 🍎”, “B 🚍”, “C 🎪”).
Helid saab panna näiteks QSoundEffect-iga.
Lisa nupp "Testi mind" — vajutades kuvatakse pilt ja küsitakse “Mis tähega see algab?”.
Kasutaja valib tähe QComboBox-ist, saad koheselt öelda “Õige!” või “Proovi uuesti!” värvilise animatsiooniga.

🟢 Mikroanimatsioonid ja liikumine
**Kuupäev:** 2025-08-12
**Staatus:** TEHA
**Vastutaja:** ⚪ Määramata
**Kirjeldus:**
Kui täht vahetub: Pealkiri libiseb vasakult sisse. Tekst ilmub fade-in-iga. Pilt hüppab kergelt nagu “elastic bounce”. Võiks kasutada QGraphicsOpacityEffect ja QPropertyAnimation.

🟢 Väike “progress bar” õppimise edenemise jaoks
**Kuupäev:** 2025-08-12
**Staatus:** TEHA
**Vastutaja:** ⚪ Määramata
**Kirjeldus:**
Kui on rohkem tähti, siis tähe valik lisab “täht õpitud” progressi. Võid panna QProgressBar alumisse ossa ja lasta tal täituda.

🟢 Rakendada debug-siltide lüliti muster kõigis moodulites
**Kuupäev:** 2025-08-13
**Staatus:** TEHA
**Vastutaja:** 🔵 Kalver
**Kirjeldus:**
Standardiseeri “FRAME:” debug-siltide lülitus kõigis moodulites ja õppimise/diagnostika vaadetes.
Igal moodulil, mis renderdab õppimise/diagnostika raame, peab olema `set_debug(bool)` API, mis peidab/näitab kõiki vastavaid silte ja delegeerib alamkomponentidele.
Kui moodulil on alamsektsioonid (nt `LetterSection`, `LetterIconFrame`), siis need implementeerivad samuti `set_debug(bool)` ja on ühendatud vanemaga.
WelcomePage’i muster on dokumenteeritud: vt `copilot-prompt.md` → “WelcomePage & Learning Section (Debug Frames) Pattern”. Rakenda sama lähenemine moodulites.
Nupu sildid eesti keeles: ON → “Peida FRAME sildid”, OFF → “Näita FRAME silte”. Vaikeseade tootmises: OFF.
Täiendavalt lisada lihtne `retheme()` tugi, et teema vahetusel jääks staatus ja stiil korrektseks.

**Tooltip QSS rakendamise selgitus:**
Varem rakendati `tooltip.qss` otse kogu QGIS UI-le, mis põhjustas globaalseid stiiliprobleeme (nt tumeda teema lekkimine kõikjale).
Praegu kasutatakse ThemeManageris QToolTip paletti, mis mõjutab ainult värve, mitte kõiki QSS omadusi.
Kui soovitakse pluginisiseselt QSS-i rakendada, tuleb luua custom lahendus, sest standardne QToolTip on globaalne.

**Soovitus autorile:**
Tooltip QSS rakendamine ainult pluginisiseselt pole võimalik standardse QToolTip kaudu, kuna see mõjutab kogu QGIS UI-d. Praegu kasutatakse paletipõhist lahendust, mis muudab ainult värve. Kui on vaja detailsemat QSS-i rakendust, tuleb luua custom tooltip-widget, mis võimaldab QSS-i rakendada ainult pluginis sees. See on keerulisem ja muudab standardset käitumist.
Palun vaata üle, kas pluginisisesed custom tooltipid oleksid aktsepteeritav lahendus, või jääme paletipõhise lahenduse juurde, et vältida QGIS-i globaalseid stiiliprobleeme.

🟢 Ideede formaati lisada eraldi “Vastutaja” rida
**Kuupäev:** 2025-08-13
**Staatus:** TEHA
**Vastutaja:** 🟠 Anneli
**Kirjeldus:**
REEGLID plokki lisada nõue, et igal ideel on “Vastutaja: <nimi>”.
Uuendada olemasolevate ideede kirjed ja lisada neile vastutaja.
Lisada IDEAS.md algusesse mini-šabloon uue idee jaoks (koos Vastutajaga).

🟢 Avalehele reaalajas ilma widget (temp, tuul, sademed, 3 päeva prognoos)
**Kuupäev:** 2025-08-13
**Staatus:** TEHA
**Vastutaja:** 🟠 Anneli
**Kirjeldus:**
Teeme eraldiseisva widgeti (nt `WeatherWidget`), mida saab kuvada WelcomePage'il.
Kuvada: hetke temperatuur, tuule kiirus/suund, sademed ning järgmise 3 päeva prognoos.
Järgida API reegleid: kõik päringud läbi keskse `APIClient`i; võtmed/URL-id ei tohi olla kõvasti kodeeritud.
Teematugi: rakendada QSS `ThemeManager.apply_module_style(...)` kaudu; lisada `retheme()`.
Vigade/ühenduseta oleku korral kuvada sõbralik placeholder (nt "Ilmaandmed pole hetkel saadaval").
Tulevikus võimaldada asukoha valik seadetes (kasutaja eelistus) ja mõistlik cache intervall.

🟢 Aegunud API võtme automaatne käsitlemine (uuesti sisselogimise küsimine)
**Kuupäev:** 2025-08-14
**Staatus:** TEHA
**Vastutaja:** 🔵 Kalver
**Kirjeldus:**
Tuvasta aegunud / kehtetu API võti (nt HTTP 401 / 403 vastus keskse `APIClient` kihis).
Lisa ühtne interceptor / wrapper, mis püüab esimese autoriseerimisvea, peatab paralleelsed päringud ja avab sisselogimisdialoogi.
Kui kasutaja logib edukalt sisse, taasta katkestatud päring(d) järjekorrast (säilita vajalikud request payload'id mälus ajutiselt).
Kui sisselogimine katkestatakse, anna kasutajale selge teade ja puhasta sessioon (SessionManager logout).
Väldi lõputut tsüklit: maksimaalselt 1 automaatne retry konkreetse päringu kohta.
Logi sündmused diagnostikasse ("token_expired", "relogin_success", "relogin_cancel").
Lisa kasutajale märguanne (nt väike infobanner) et sessioon aegus ja paluti uus login.
Veendu, et `retheme()` ja keeleseaded ei kaoks login flow ajal.
**2025-08-19 UPDATE:**
 - Sessiooni aegumise dialoog näidatakse nüüd ainult korra sessiooni kohta, vältides lõputut tsüklit.
 - Kasutajale pakutakse valikut: "Logi sisse" või "Tühista". Vajutuse sündmused logitakse konsooli (print).
 - Vajutuse tulemus salvestatakse ja vajadusel seatakse püsiv lipp järgmise käivituse jaoks.
 - Dialoogi avamine on integreeritud APIClienti kaudu, valmis päris login dialoogi ühendamiseks.
 - Kogu dialoogi tekst on lokaliseeritud keelehalduri kaudu.
 - Järgmine samm: päris login dialoogi avamine ja katkestatud päringute taastamine.

🟢 TEHA 2025-08-13: Peida DEV-plokk mittedev-kasutajate eest
	- Vastutaja: Kalver
	- Lisa seadistuslipp (nt wild_code/show_dev_controls), mis on vaikimisi “0/false” tootmises ja “1/true” arenduskeskkonnas.
	- Kui lipp on false, siis Header’i DevControlsWidget ei renderda/kuva end (või on peidetud) ja ei võta paigutuses ruumi.
	- Kui lipp on true, kuvame DEV märgise, DBG lüliti ja FRAME siltide lüliti nagu praegu.
	- Lisa lihtne seadete UI (Settings) valik arendajale: “Näita arendusvahendeid päises (DEV)”.

🟢 TEHA 2025-08-13: DevControls (DBG/FRAME) nähtavuse ja stiili kindlustamine
	- Vastutaja: Kalver
	- Probleem: “mingi stiil on muutunud, kuid nuppude nähtavus/kooslus pole stabiilne” – mõnes keskkonnas OFF-olek jääb liiga nõrgaks või paigutus nihkub.
	- Hüpotees: header.qss võib mõnes järjekorras prioriteediga üle kirjutada DevControls.qss või selektorid on liiga nõrgad.
	- Sammud:
		1) Kinnita QSS rakendamise järjekord (Header → DevControls.retheme()).
		2) Tugevda selektoreid: näiteks `HeaderWidget DevControlsWidget #headerDevToggleButton` vms, vajadusel lisa `!important`-i vältimiseks spetsiifilisust.
		3) Kontrolli min-sizes ja iconSize (framesBtn) mõlemas teemas; vajadusel tõsta min-width 40–44 px.
		4) Lisa ajutine diagnostika: logi, kas `retheme()` käivitus peale teema vahetust.
		5) Visuaalne QA: Light ja Dark ekraanipildid; võrreldav OFF/ON kontrast.
	- Kui selgub, et tegemist on veaga (mitte ainult parendusega), logi see ka BUGS.md-sse.

🟢 TEHA 2025-08-13: DevControlsWidget — standardi täpsustused ja pisiparendused
	- Vastutaja: Kalver
	- Eesmärk: tuua DevControlsWidget täielikult kooskõlla projekti tavadega (i18n, teemastatud ikoonid, diagnostika) ja parandada hooldatavust.
	- Ülesanded:
		1) TEHTUD 2025-08-13 — I18n: viia “DBG” ja “FRAME siltide” nuppude tooltipid LanguageManager’i alla (en/et võtmed, nt `dev_dbg_tooltip`, `dev_frames_tooltip`).
		2) POOLELI 2025-08-13 — Teemastatud ikoon: asendada `QIcon(ResourcePaths.EYE_ICON)` kasutusega `ThemeManager.get_qicon(...)` ja lisada Light/Dark silmaikooni variandid, kui vaja. (Vastutaja: 🟠 Anneli)
		3) Diagnostika: asendada kriitilised `try/except: pass` plokid valikulise logiga (nt kui ThemeManager._debug on true), et vea korral oleks kontekst.
		4) TEHTUD 2025-08-14 — Elutsükkel: lisada `closeEvent` või `deleteLater` hook, mis peatab animatsioonigrupid (kui need on aktiivsed) — topeltsäde hoidmiseks.
		5) API viimistlus: kaaluda `set_debug_checked(bool)` ja `set_frames_checked(bool)` abi meetodeid; `set_states(...)` jääb põhi-API-ks.
		6) Dokumentatsioon: uuenda `IDEAS.md` ja/või lühikommentaar klassi päisesse, kirjeldades signaale ja `set_states` lepingu.

🟢 TEHA 2025-08-14: Keskne animatsioonikontroller teistesse vidinatesse
	- Vastutaja: Kalver
	- Võta kasutusele `utils/animation/AnimationController` vähemalt ühes teises vidinas, mis vajab pulse/glow indikatsioone (nt mõni Settings/Status väike nupp).
	- Sammud:
		1) Lisa QGraphicsColorizeEffect/QGraphicsDropShadowEffect sihtkomponentidele.
		2) Loo `AnimationController(owner, glow_effect=..., dbg_effect=..., frames_effect=...)` või sobiva konfiguratsiooniga isend.
		3) Ühenda lülitite handlerid `controller.apply_state(...)`-ga ja elutsükli lõpetamisel `controller.stop_all()`.
		4) Visuaalne QA: nupud ei liigu; pulse töötab ainult ON-olekus; halo püsib teema reeglitega kooskõlas.

🟢 TEHA 2025-08-14: Väike test-harness animatsioonide kontrolliks
	- Vastutaja: Kalver
	- Eesmärk: lihtne testkonteiner (väike QWidget), mis loob efekti(d), käivitab `AnimationController.apply_state(...)` ja lubab käsitsi lülitada ON/OFF.
	- Sammud:
		1) Loo `experimental/animation_harness.py` (või `scripts/animation_harness.py`).
		2) Instantsi värvi- ja haloefektid, seosta ajutiste nuppudega.
		3) Kontrolli, et `loopCount == -1` ja OFF-is `strength == 0.0`.
		4) Dokumenteeri IDEAS.md-s tulem.

🟢 TEHA 2025-08-14: DateWidget "due soon" pehme vihje
	- Vastutaja: Kalver
	- Lisa mittevilkuv (steady) õrn merevaigukarva vihje või aeglasem pulse olukorras, kus tähtaeg on "soon" (`DateHelpers.due_state == "soon"`).
	- Hoia üle tähtaja ("overdue") puhul olemasolev punane vilkumine; "ok" puhul mitte ühtegi efekti.

🟢 TEHA 2025-08-14: Moodulikaartide punane hoiatuspulsatsioon
	- Vastutaja: Kalver
	- Miks mõni kaart (module element info) ei kasuta värskelt loodud punast hoiatuspulssi? Märgi uurimiseks.
	- Kahtlus: efekt jäeti rakendamata või elutsükli haldus puudulik. Vaja üle vaadata ja ühtlustada rakendamine utiliitidega (`utils/animation`).

🟢 TEHA 2025-08-14: Uuring — QGIS privaatne plugin-repo (DO Spaces + Laravel API)
	- Vastutaja: Kalver
	- Eesmärk: kinnitada privaatselt hallatava pluginirepositooriumi lahendus, mis toetab lihtsat paigaldust ja poolautomaatsed uuendused.
	- Sisu: koosta kokkuvõte ja võtmekohad failis `docs/QGIS_Private_Repo_Study.md` (DO Spaces privaatsed objektid, Laraveli vahendus `plugins.xml` jaoks püsiva autentimisega, ZIP-idele presigned URL suunamised, QGIS Plugin Manageri seadistamine, GPL-märkused).
	- Sammud:
		1) CI: ehita ZIP + `plugins.xml` ja lae üles DO Spaces privaat-bucket’isse.
		2) Laravel: `GET /api/qgis/plugins` (tagastab `plugins.xml`, Basic Auth või token), `GET /api/qgis/download/:file` (presigned redirect ZIP-ile).
		3) QGIS: Lisa repo URL (Laravel endpoint), seadista Authentication Manager.
		4) Test: uuenduste kontroll, installeerimine ja versiooni tõstmine.
	- Märkmed: `plugins.xml` ei pea olema avalik; püsivalt ligipääsetav (autentitud) on parem kui aeguvad presigned lingid. ZIP-idele sobib presigned. Arvesta GPL-i nõuetega.

🟢 TEHA 2025-08-15: ModuleCardHeader ikoon ja number-märgi viimistlus
**Kuupäev:** 2025-08-15
**Staatus:** TEHA
**Vastutaja:** 🟠 Anneli
**Kirjeldus:**
- Leia sobiv ikoon InfoCardHeader-i pealkirja reale (privaatuse kõrvale või vajadusel eraldi visuaalne aktsent).
- Number-märgi (badge) visuaal vajab kohendust: ümaramad nurgad, ühtlane vertikaalne joondus.
- Lisa QSS-is ümardus (border-radius) nii, et väiksemate kõrguste korral kohandub raadius (nt min(height/2 - 1px)).
- Märkus: kui raadius > elemendi kõrgus/2, siis ei ilmu kaar korrektne — vajadusel vähendada raadiust (tingimuslik klass või style hack).
- Kontrolli Light/Dark teemas kontrasti ja varju (kerge sisemine varjund võib parandada loetavust).

🟢 Dashboard ideede inspiratsiooni kogumine (CodePen)
**Kuupäev:** 2025-08-15
**Staatus:** TEHA
**Vastutaja:** 🟠 Anneli
**Kirjeldus:**
- Uuri CodePen’i dashboard’i näiteid ja mustreid: https://codepen.io/search/pens?q=dashboard&cursor=OQ
- Koosta lühikokkuvõte (mis töötab QGIS/Qt kontekstis, mis mitte) ja paku välja 3–5 sobivaimat ideed (kriitiliselt hinnata/“challenge’ida” olemasolevaid mõtteid).
- Lisa kõik kasulikud lingid eraldi dokumenti `docs/Dashboard_Links.md` (üks link rea kohta + lühikommentaar: „miks see meeldib / mida kasutaks”).
- Soovi korral lisa väikesed kuvatõmmised inspiratsiooni offline-hoidmiseks.


🟢 TEHA 2025-08-27: Uuri ja õpi, kuidas uued Overdue nupud töötavad
**Staatus:** TEHA
**Vastutaja:** 🟠 Anneli
**Kirjeldus:**
- Uuri ja õpi, kuidas meie uued Overdue nupud töötavad
- Leia nende implementatsioonis loogilised vead
- Mõtle filtri paigutuse üle ja paku välja parandusi

🟢 TEHA 2025-08-27: Filtrite värskendusnupu ümberpaigutamine ja täiustused
**Staatus:** TEHA
**Vastutaja:** 🟠 Anneli
**Kirjeldus:**
- Filtrite värskendusnupp vajab ümberpaigutamist
- Lisa sobiv ikoon
- Mõtle muudele detailidele ja parandustele värskendusnupu jaoks


# 🟦 **LÕPETATUD IDEED**

🔵 LÕPETATUD 2025-08-13 (lisatud 2025-08-12) — plugin muudab QGIS teema tumedaks laadides tõenäoliselt minu teema fail. 
	Vastutaja: 🔵 Kalver

🔵 LÕPETATUD 2025-08-12 (lisatud 2025-08-12) — Avalehe tähe haldurisse lisatud "B" ja "C" tähed ning rippmenüü, mis kuvab iga tähe kohta erinevat infot.
	Vastutaja: ⚪ Määramata

🔵 LÕPETATUD 2025-08-12 (lisatud 2025-08-12) — Tähe ikoon — iga tähe valikul kuvatakse suur, värviline täht (nt A punane, B sinine, C roheline) koos kerge “bounce” animatsiooniga. (Paigutus ja animatsioon on implementeeritud WelcomePage-s) - katsetatud, aga meile ei sobi.
	Vastutaja: ⚪ Määramata

