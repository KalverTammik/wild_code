┌────────────── 🟨 PROTSESSI JUHISED ──────────────┐

- Iga vea juurde lisa Vastutaja: <nimi>, kes peab järgmise sammu tegema (kasuta legendi markereid: 🟠 Anneli, 🔵 Kalver, ⚪ Määramata).
- Kasuta staatuse silte:
    - **UUS** – värskelt avastatud viga, pole veel uuritud.
    - **ARENDAJA TAGASISIDEGA TESTIMISEK** – arendaja on teinud paranduse, vaja testida.
    - **UUESTI LAHENDADA** – testimisel leiti, et viga pole lahendatud, vaja uuesti vaadata.
    - **TEHTUD** – viga on parandatud ja testitud.
- Iga vea juures hoia lühike kirjeldus, sammud kordamiseks, vajadusel lahenduskäik ja kuupäevad.
- Kui viga on lahendatud, jäta alles kogu info, lisa lõppu TEHTUD ja kuupäev.

 Märkus 
Fail on mõeldud ainult vigade ja probleemide jälgimiseks. Uued ideed ja arendussoovid lisa IDEAS.md faili.


 ┌────────────── 🟥 TEGEVUSES BUGID ──────────────┐

🟢 INLINE IMPORTIDE JA VALEDE TAANDETASEMETE RISK WIDGETS/ ALL
**Kuupäev:** 2025-08-12
**Staatus:** UUS
**Vastutaja:** 🔵 Kalver
**Kirjeldus:** Mõnes failis on kasutusel funktsiooni sees olevad import-laused (inline imports), mis suurendavad riski, et automaatsed tööriistad (nt Copilot) lisavad ridu vale taandetasemega (nt `self.*` väljaspool meetodit), põhjustades süntaksi vigu.

Mõjutatud failid (näited):
- `widgets/DataDisplayWidgets/ModuleFeedBuilder.py` – `from PyQt5.QtCore import QSize` meetodi sees
- `widgets/WelcomePage.py` – `from PyQt5.QtCore import QPropertyAnimation` meetodi sees
- `widgets/theme_manager.py` – mitmed import’id meetodite sees (`QIcon`, `QgsSettings`, `file_paths`)
- `widgets/layer_dropdown.py` – `from PyQt5.QtWidgets import QFrame` meetodi sees
- `widgets/HeaderWidget.py` – mitmed import’id meetodite sees

Soovituslik lahendus:
1. Tõsta import-laused faili algusesse, kui puudub mõju jõudlusele või ring-sõltuvus.
2. Kui inline import on vajalik (nt vältimaks raskete sõltuvuste laadimist), lisa kommentaar `# inline import: reason` ja jäta taand tase korrektselt meetodi sisse.
3. Vii läbi kiire kontroll, et üheski failis ei oleks top-level `self.*` ridu.
4. Lisa Copilot’i reeglitesse (copilot-prompt.md) juhis vältida inline import’e ja säilitada taanded.

Kordamise sammud:
1. Ava failid loetelust ja liigu importidele.
2. Tõsta import ülaossa või märgista inline kommentaariga vastavalt.
3. Salvesta ja käivita lühike süntaksikontroll (Problems paneel/linters) veendumaks, et taanded on paigas.

Kui korrigeeritud, uuenda staatust: ARENDAJA TAGASISIDEGA TESTIMISEK (testimiseks) või LÕPETATUD.

 ┌────────────── 🟧 TESTIMISEL BUGID ─────────────┐

(Hetkel tühi – siia lisatakse bugid kui staatus muutub ARENDAJA TAGASISIDEGA TESTIMISEKs)
Kui testitud, märgi staatus vastavalt: TEHTUD või UUESTI LAHENDADA ja lisa kuupäev.

 ┌────────────── 🟩 LÕPETATUD BUGID ─────────────┐

(Hetkel tühi – kui bugi staatus muutub TEHTUD, tõsta täielik kirje siia koos kuupäevaga ja jäta algses plokis lühiviide või eemalda sealt.)

🟢 PLUGIN EI RAKENDA TUMEDAT TEEMAT TEISE ARENDAJA ARVUTIS
**Kuupäev:** 2025-08-12
**Staatus:** TEHTUD 2025-08-13
**Vastutaja:** 🔵 Kalver
**Kirjeldus:** Plugin muudab QGIS teema tumedaks laadides tõenäoliselt minu teema fail. Kalver tegeleb.
**Kokkuvõte:** Plugin rakendas tumeda teema kogu QGIS-ile, mitte ainult plugina dialoogidele. Paranduseks muudeti teema rakendamine nii, et see mõjutab ainult plugina komponente, mitte QGIS-i globaalselt.

