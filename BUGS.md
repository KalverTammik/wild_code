
# 🟨 PROTSESSI JUHISED

- Iga vea juurde lisa Vastutaja: <nimi>, kes peab järgmise sammu tegema (kasuta legendi markereid: 🟠 Anneli, 🔵 Kalver, ⚪ Määramata).
- Kasuta staatuse silte:
    - **UUS** – värskelt avastatud viga, pole veel uuritud.
    - **ARENDAJA TAGASISIDEGA TESTIMISEK** – arendaja on teinud paranduse, vaja testida.
    - **UUESTI LAHENDADA** – testimisel leiti, et viga pole lahendatud, vaja uuesti vaadata.
    - **TEHTUD** – viga on parandatud ja testitud.
- Iga vea juures hoia lühike kirjeldus, sammud kordamiseks, vajadusel lahenduskäik ja kuupäevad.
- Kui viga on lahendatud, jäta alles kogu info, lisa lõppu **TEHTUD** ja kuupäev.

## Märkus 
Fail on mõeldud ainult vigade ja probleemide jälgimiseks. Uued ideed ja arendussoovid lisa IDEAS.md faili.

---

# 🟥 BUGID

### 2025-08-12: PLUGIN EI RAKENDA TUMEDAT TEEMAT TEISE ARENDAJA ARVUTIS
**Staatus:** TEHTUD 2025-08-13
Vastutaja: 🟠 Anneli
**Kirjeldus:** Plugin muudab QGIS teema tumedaks laadides tõenäoliselt minu teema fail. Kalver tegeleb.

**Põhjus (leitud):** `ThemeManager.apply_tooltip_style()` kasutas varem `QApplication.instance().setStyleSheet(...)`, mis rakendas plugina QSS-i globaalselt tervele QGIS-ile (toolbarid muutusid tumedaks jne).

**Parandus:** Vältida globaalse `QApplication` stiili seadmist. Muutsime `apply_tooltip_style()` nii, et see seab ainult `QToolTip` paleti (taust/tekst) eikäivita üldist `setStyleSheet`-i.

**Kuidas testida (regr-test):**
1. Sulge QGIS.
2. Tõmba plugin uuendustega või kopeeri muudetud failid.
3. Ava QGIS ja käivita plugin.
4. Kontrolli: QGIS enda tööriistaribad ja paneelid EI tohi vahetada värviskeemi; tumedus/valgus peab mõjutama ainult plugina dialoogi komponente. Tooltipid peaksid olema loetavad (tume teema → tume taust/hele tekst; hele teema → hele taust/tume tekst).
5. Lülita plugina teemat (Light/Dark) ja kinnita, et QGIS-i globaalne stiil ei muutu.

Kui OK, märgi staatus: **TEHTUD** ja lisa kuupäev. Kui QGIS UI ikka muutub, märgi **UUESTI LAHENDADA** ja lisa ekraanipildid.

**Testi ja kontrolli:**
- Kui plugin töötab Sinu arvutis, kuid mitte teisel arendajal, võib probleem olla tema QGIS-i või arenduskeskkonna vahemälus või failides.
- Tüüpilised põhjused:
    - Vanad `__pycache__` kaustad või `.pyc` failid, mis ei ühti koodiga.
    - QGIS plugin cache pole pärast uuendusi tühjendatud.
    - VS Code/Visual Studio ei värskenda pluginakataloogi muudatuste järel.
    - Failiõigused või failid lukustatud editori poolt.
- Soovituslikud sammud:
    1. Sulge QGIS ja editor.
    2. Kustuta kõik `__pycache__` kaustad ja `.pyc` failid pluginakataloogist.
    3. Tühjenda QGIS plugin cache (`%APPDATA%\QGIS\QGIS3\profiles\default\cache`).
    4. Ava QGIS ja testi pluginat uuesti.
- Kui probleem püsib, klooni plugin uuesti või kontrolli QGIS Python Console veateateid.

Kui testitud, märgi staatus vastavalt: **TEHTUD** või **UUESTI LAHENDADA** ja lisa kuupäev.

---

### 2025-08-12: INLINE IMPORTIDE JA VALEDE TAANDETASEMETE RISK WIDGETS/ ALL
**Staatus:** UUS
Vastutaja: 🔵 Kalver
**Kirjeldus:** Mõnes failis on kasutusel funktsiooni sees olevad import-laused (inline imports), mis suurendavad riski, et automaatsed tööriistad (nt Copilot) lisavad ridu vale taandetasemega (nt `self.*` väljaspool meetodit), põhjustades süntaksi vigu.

**Mõjutatud failid (näited):**
- `widgets/DataDisplayWidgets/ModuleFeedBuilder.py` – `from PyQt5.QtCore import QSize` meetodi sees
- `widgets/WelcomePage.py` – `from PyQt5.QtCore import QPropertyAnimation` meetodi sees
- `widgets/theme_manager.py` – mitmed import’id meetodite sees (`QIcon`, `QgsSettings`, `file_paths`)
- `widgets/layer_dropdown.py` – `from PyQt5.QtWidgets import QFrame` meetodi sees
- `widgets/HeaderWidget.py` – mitmed import’id meetodite sees

**Soovituslik lahendus:**
1. Tõsta import-laused faili algusesse, kui puudub mõju jõudlusele või ring-sõltuvus.
2. Kui inline import on vajalik (nt vältimaks raskete sõltuvuste laadimist), lisa kommentaar `# inline import: reason` ja jäta taand tase korrektselt meetodi sisse.
3. Vii läbi kiire kontroll, et üheski failis ei oleks top-level `self.*` ridu.
4. Lisa Copilot’i reeglitesse (copilot-prompt.md) juhis vältida inline import’e ja säilitada taanded.

**Kordamise sammud:**
1. Ava failid loetelust ja liigu importidele.
2. Tõsta import ülaossa või märgista inline kommentaariga vastavalt.
3. Salvesta ja käivita lühike süntaksikontroll (Problems paneel/linters) veendumaks, et taanded on paigas.

Kui korrigeeritud, uuenda staatust: **ARENDAJA TAGASISIDEGA TESTIMISEK** (testimiseks) või **TEHTUD**.
