
# IDEAS.md
TEHA — plugin muudab QGIS teema tumedaks laadides tõenäoliselt minu teema fail. Kalver tegeleb.

### Kuidas ülesandeid lahendatuks märkida?
- Kui lahendad ülesande, lisa selle juurde kuupäev ja märksõna **[TEHTUD]** või **[POOLELI]**.
- Näide:
    - **[TEHTUD 2025-08-12]** Tooltipi QSS seadistatavus lisatud.
    - **[POOLELI 2025-08-13]** Heliefektid implementeerimisel.
- Soovi korral lisa ka lühike kommentaar või link muudatuse logisse.

## Ideede logi

Siia faili kogume kõik arendusideed, mõtted ja tulevased plaanid. Kui tekib uus idee, lisa see siia koos kuupäeva ja lühikirjeldusega.

---

### Näide:
- **2025-08-12:** Tooltipi QSS võiks olla kasutaja poolt seadistatav (värv, font, varjund).

---

Lisa uusi ideid käsuga või kirjeldusega, et saaksime neid hiljem arutada ja ellu viia.

- **2025-08-12:** Lisada võimalus kasutajal valida rakenduse keelt otse peaaknast, ilma seadete menüüsse minemata (nt rippmenüü või nupuriba kaudu).
- **2025-08-12:** Palu Kalveril kontrollida, kas seadetes on õigesti seadistatud, et avaleht peab olema esmaselt avatav, kui ühtegi moodulit pole esmaseks valikuks määratud.

- **[TEHTUD 2025-08-12]** Avalehe tähe haldurisse lisatud "B" ja "C" tähed ning rippmenüü, mis kuvab iga tähe kohta erinevat infot.
- **2025-08-12:** Visuaalid ja animatsioonid
    - **[TEHTUD 2025-08-12]** Tähe ikoon — iga tähe valikul kuvatakse suur, värviline täht (nt A punane, B sinine, C roheline) koos kerge “bounce” animatsiooniga. (Paigutus ja animatsioon on implementeeritud WelcomePage-s)
    - Pildid tähega algavatest asjadest — kui valitakse A, ilmub õunapilt; B puhul banaan või buss; C puhul tsirkuseplakat. Võid kasutada QPixmap + fade-in efekti.
    - Lisa QPropertyAnimation, et tekst või pilt sujuvalt sisse/ välja libiseks.
- **2025-08-12:** Värviline ja mänguline kujundus
    - Taust võiks olla gradient (nt helesinine → valge), mitte lihtsalt hall.
    - Pane header frame-ile ümarad nurgad ja kerge vari (QSS border-radius, box-shadow).
    - Letter selector võiks olla suur ja piltidega (nt “A 🍎”, “B 🚍”, “C 🎪”).
- **2025-08-12:** Heliefektid
    - Kui täht muutub, mängib heli (nt A puhul “ahh”-heli, B puhul “b-b-b” ja C puhul tsirkusefanfaar).
    - Helid saab panna näiteks QSoundEffect-iga.
- **2025-08-12:** Väike mängu-element
    - Lisa nupp "Testi mind" — vajutades kuvatakse pilt ja küsitakse “Mis tähega see algab?”.
    - Kasutaja valib tähe QComboBox-ist, saad koheselt öelda “Õige!” või “Proovi uuesti!” värvilise animatsiooniga.
- **2025-08-12:** Mikroanimatsioonid ja liikumine
    - Kui täht vahetub: Pealkiri libiseb vasakult sisse. Tekst ilmub fade-in-iga. Pilt hüppab kergelt nagu “elastic bounce”. Võiks kasutada QGraphicsOpacityEffect ja QPropertyAnimation.
- **2025-08-12:** Väike “progress bar” õppimise edenemise jaoks
    - Kui on rohkem tähti, siis tähe valik lisab “täht õpitud” progressi. Võid panna QProgressBar alumisse ossa ja lasta tal täituda.

---
