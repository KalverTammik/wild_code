05 – Andmevood ja andmeobjektid
🎯 Eesmärk
Kirjeldada, kuidas modelleerida andmete loomist, muutmist, kustutamist ja kasutamist BPMN skeemis selgelt ja üheselt.

📦 Andmesümbolid BPMN-is
Element	Kasutusala	Märkused
Data Object	Ajutised või protsessiga seotud andmed	Nt “Tellimuse andmed”, “Arve info”.
Data Store	Püsiv andmeallikas	Nt “Andmebaas”, “Dokumendiarhiiv”.
Data Association	Andmevoo ühendus Activity või Event’iga	Ainult andmete liikumiseks, mitte protsessijooksu jaoks.

📌 Reeglid
Sequence Flow ≠ Data Flow

Ära modelleeri andmevoogu sequence flow’ga (nooled tegevuste vahel).

Kasuta alati Data Association’it.

Data Store

Kasuta, kui andmed salvestatakse püsivalt.

Data Store peab olema selgelt nimetatud (“Klientide DB”, mitte “DB”).

Data Object

Kasuta, kui andmed on ajutised või seotud ainult selle protsessi käiguga.

Nimi peab viitama sisule, mitte ainult vormingule (“Kliendi tellimus”, mitte “JSON payload”).

Andmeoperatsioonid

Märgi juurde (nt labelina või eraldi sümboliga), kas tegemist on:

Create – andmete loomine

Update – muutmine

Delete – kustutamine

Näiteks: Update: Tellimuse olek.

Visuaalne selgus

Hoia andmeelemendid põhivoolust eemal (tavaliselt allpool või kõrval).

Data Association peab olema lühike ja võimalikult sirge.

📝 Tekstiline illustratsioon
yaml
Kopeeri
Redigeeri
[Task: Kontrolli varu]
      |
      v (Data Association)
  [Data Store: Koostisosade DB]
Sequence flow viib protsessi edasi, Data Association näitab andmete lugemist.