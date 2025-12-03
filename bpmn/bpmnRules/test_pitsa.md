# 🍕 Test-skeem: Pitsa tellimus (TEMP)

See on ajutine näide, millega testime BPMN reegleid enne, kui rakendame neid päris äriprotsessidele.
Pärast juhendi küpsemist võib see fail eemalduda või asenduda universaalsema testjuhtumiga.

## Kliendi tagasiside (intervjuu stiilis: kes • millal • mida teeb • tulemus)

- **Põhivoog**
  1. Klient • kui on isu • valib e-poes pitsa ja kinnitab tellimuse • „tellimus loodud”.
  2. Süsteem • kohe pärast kinnitamist • kontrollib vajalike koostisosade varu • „varu OK” või „puudub”.
  3. Kui varu on olemas • süsteem palub valida makseviisi; klient valib kas „maksa kohe” või „maksa kättesaamisel” • „makseviis salvestatud”.
  4. Süsteem • pärast makseviisi • salvestab tellimuse ja teavitab kööki • „tellimus köögis”.
  5. Köök • kui tellimus saabub • valmistab pitsa • „valmis tarnesse”.
  6. Tarne • kui pitsa valmis • võtab kauba ja viib kliendile • „kohaletoimetatud, protsess lõpp”.

- **„Out of stock” (koostis puudub)**
  - Süsteem • kui varu puudub • pakub kliendile alternatiivi • „vali teine või tühista”.
  - Klient • valib teise pitsa • süsteem kontrollib uue valiku varu • jätkub põhivoo alusel.
  - Klient • ei soovi alternatiivi • tühistab tellimuse; kui oli makse tehtud • süsteem algatab tagasimakse • „tühistatud, tagasimakse teel”.

- **Tühistamine pärast tellimust**
  - Klient • soovib tühistada enne valmistuse algust • süsteem tühistab ilma trahvita; kui makse oli tehtud • algatab tagasimakse • „tühistatud”.
  - Klient • soovib tühistada pärast valmistuse algust • süsteem tühistab reeglite järgi (võimalik tasu) ja teavitab • „tühistatud vastavalt tingimustele”.

- **Teavitused ja tarne**
  - Tarne on välisteenus; soovime staatuse teateid (väljus, teel, kohal).
  - Kliendile lähevad olulised teated: kinnitused, tühistused, „teel”, „kohal”.

📌 Märkus: See on testsektsioon, mitte äriametlik. Eemaldame hiljem.
