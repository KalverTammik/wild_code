

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

🟢 TEHA 2025-08-12: Värviline ja mänguline kujundus
	Vastutaja: ⚪ Määramata
	- Taust võiks olla gradient (nt helesinine → valge), mitte lihtsalt hall.
	- Letter selector võiks olla suur ja piltidega (nt “A 🍎”, “B 🚍”, “C 🎪”).
	- Helid saab panna näiteks QSoundEffect-iga.
	- Lisa nupp "Testi mind" — vajutades kuvatakse pilt ja küsitakse “Mis tähega see algab?”.
	- Kasutaja valib tähe QComboBox-ist, saad koheselt öelda “Õige!” või “Proovi uuesti!” värvilise animatsiooniga.

🟢 TEHA 2025-08-12: Mikroanimatsioonid ja liikumine

	Vastutaja: ⚪ Määramata
	- Kui täht vahetub: Pealkiri libiseb vasakult sisse. Tekst ilmub fade-in-iga. Pilt hüppab kergelt nagu “elastic bounce”. Võiks kasutada QGraphicsOpacityEffect ja QPropertyAnimation.

🟢 TEHA 2025-08-12: Väike “progress bar” õppimise edenemise jaoks
	Vastutaja: ⚪ Määramata
	- Kui on rohkem tähti, siis tähe valik lisab “täht õpitud” progressi. Võid panna QProgressBar alumisse ossa ja lasta tal täituda.

🟢 TEHA 2025-08-13: Rakendada debug-siltide lüliti muster kõigis moodulites
	Vastutaja: 🔵 Kalver
	- Standardiseeri “FRAME:” debug-siltide lülitus kõigis moodulites ja õppimise/diagnostika vaadetes.
	- Igal moodulil, mis renderdab õppimise/diagnostika raame, peab olema `set_debug(bool)` API, mis peidab/näitab kõiki vastavaid silte ja delegeerib alamkomponentidele.
	- Kui moodulil on alamsektsioonid (nt `LetterSection`, `LetterIconFrame`), siis need implementeerivad samuti `set_debug(bool)` ja on ühendatud vanemaga.
	- WelcomePage’i muster on dokumenteeritud: vt `copilot-prompt.md` → “WelcomePage & Learning Section (Debug Frames) Pattern”. Rakenda sama lähenemine moodulites.
	- Nupu sildid eesti keeles: ON → “Peida FRAME sildid”, OFF → “Näita FRAME silte”. Vaikeseade tootmises: OFF.
	- Täiendavalt lisada lihtne `retheme()` tugi, et teema vahetusel jääks staatus ja stiil korrektseks.

🟢 TEHA 2025-08-13: Ideede formaati lisada eraldi “Vastutaja” rida
	Vastutaja: 🟠 Anneli
	- REEGLID plokki lisada nõue, et igal ideel on “Vastutaja: <nimi>”.
	- Uuendada olemasolevate ideede kirjed ja lisada neile vastutaja.
	- Lisada IDEAS.md algusesse mini-šabloon uue idee jaoks (koos Vastutajaga).

🟢 TEHA 2025-08-13: Avalehele reaalajas ilma widget (temp, tuul, sademed, 3 päeva prognoos)
	Vastutaja: 🟠 Anneli
	- Teeme eraldiseisva widgeti (nt `WeatherWidget`), mida saab kuvada WelcomePage'il.
	- Kuvada: hetke temperatuur, tuule kiirus/suund, sademed ning järgmise 3 päeva prognoos.
	- Järgida API reegleid: kõik päringud läbi keskse `APIClient`i; võtmed/URL-id ei tohi olla kõvasti kodeeritud.
	- Teematugi: rakendada QSS `ThemeManager.apply_module_style(...)` kaudu; lisada `retheme()`.
	- Vigade/ühenduseta oleku korral kuvada sõbralik placeholder (nt "Ilmaandmed pole hetkel saadaval").
	- Tulevikus võimaldada asukoha valik seadetes (kasutaja eelistus) ja mõistlik cache intervall.

# 🟦 **LÕPETATUD IDEED**

🔵 LÕPETATUD 2025-08-13 (lisatud 2025-08-12) — plugin muudab QGIS teema tumedaks laadides tõenäoliselt minu teema fail. 
	Vastutaja: 🔵 Kalver

🔵 LÕPETATUD 2025-08-12 (lisatud 2025-08-12) — Avalehe tähe haldurisse lisatud "B" ja "C" tähed ning rippmenüü, mis kuvab iga tähe kohta erinevat infot.
	Vastutaja: ⚪ Määramata

🔵 LÕPETATUD 2025-08-12 (lisatud 2025-08-12) — Tähe ikoon — iga tähe valikul kuvatakse suur, värviline täht (nt A punane, B sinine, C roheline) koos kerge “bounce” animatsiooniga. (Paigutus ja animatsioon on implementeeritud WelcomePage-s) - katsetatud, aga meile ei sobi.
	Vastutaja: ⚪ Määramata

