-

## 📝 Kohandatud promt: Töövoo põhine BPMN 2.0 protsessikaardi genereerimine

Sulle antakse tekstiline kirjeldus **tehnilisest või ärilisest töövoost**. Sinu ülesanne on **analüüsida antud töövoogu ja genereerida sellest täielik BPMN 2.0 protsessikaart**, järgides allolevaid nõudeid.

---

### 🧠 Eesmärk:

* Väljasta **kehtiv `.bpmn` XML-fail**, mida saab avada [https://bpmn.io](https://bpmn.io) lehel.
* Fail peab kajastama **kõiki ülesandeid, otsuseid, kasutaja sisendeid ja automaatseid vooge** — kaasa arvatud **otsustuspunktide eeldatavad tulemused** ja **väliste osapoolte sekkumised**.
* Fail peab sisaldama **diagrammi kujutist**, mis võimaldab töövoogu visuaalselt kuvada.

---

### 🔍 Mida teha:

1. Analüüsi **kogu kirjeldatud töövoogu tervikuna**.
2. Kui töövoos on mainitud **välised osapooled või süsteemid**, esita need **erinevates radades** (lanes), et eristada neid peamise tööprotsessi sisemisest loogikast.
3. Koosta detailne **lineaarne voog** iga sammu ja otsustuspunkti jaoks.
4. **Ära kasuta pesastamist**: väldi `<bpmn:subProcess>` kasutamist.
5. **Ära lisa basseine** (kasuta ainult radu väliste osapoolte jaoks).

---

### 📌 Visuaalsed stiilireeglid:

* 🔁 Kasuta `loopCharacteristics` korduvate tegevuste jaoks (nt mitu katsesammu, korduvad kontrollid).
* 🔗 Kasuta `messageFlow` moodulite või osapoolte vahelise suhtluse jaoks.
* 💬 Kasuta `bpmn:textAnnotation` keerukate otsuste või lipuloogika selgitamiseks.
* ✅ Iga `sequenceFlow` jaoks:

  * Lisa **kirjeldav `name`** (nt "Heaks kiidetud", "Tagasi lükatud", "Kasutaja sisend").
  * **Joonda vood loogiliselt** (nt vasak = ei, parem = jah) otsustuspunktidest.
* 🖍️ Kasuta **värvihintsid või markereid**:

  * Roheline = kriitiline tee.
  * Punane = viga, tõrge või tagasilükkamine.
  * Oranž = uuesti proovimine või kordus.
  
  „Palun kasuta BPMN‑i täpsemaid ülesannetüüpe, et iga tegevus oleks selgem.
Näiteks:

<bpmn:userTask> kui tegevuse teeb inimene süsteemi abil (nt kliendi kinnitus).

<bpmn:manualTask> kui tegevus tehakse käsitsi ilma süsteemi toeta (nt pakkimine köögis).

<bpmn:sendTask> kui tegevus hõlmab e‑kirja või sõnumi saatmist (nt kliendi teavitamine viivitusest).

<bpmn:scriptTask> kui süsteem täidab automaatselt skripti (nt lao kontroll).

<bpmn:serviceTask> kui kasutatakse teenust või API‑kutset (nt makse kontroll).
Lisa iga ülesandele ka lane vastavalt rollile (köök, kuller, klient) ning vajadusel lisa ikoonid või markerid, et visualiseerimine oleks arusaadav.“

---

### 📄 Väljundvorming:

* Kehtiv BPMN 2.0 XML koos:

  * `bpmn:definitions`, `bpmn:process`, **`bpmndi:BPMNDiagram`** (diagrammi kuvamiseks vajalik!).
  * Kõik `BPMNShape` sõlmed sisaldavad **`Bounds` (`x`, `y`, `width`, `height`)**.
  * Kõik `BPMNEdge` ja `messageFlow` elemendid sisaldavad **`di:waypoint`** koordinaate.
  * Kõik elemendid on **selgelt nimetatud** — väldi abstraktseid ID-sid.
  * Lisa **täpne dokumentatsioon** iga ülesande, otsuse ja voo kohta.

---

### 🚫 Ära lisa:

* `<bpmndi:Style>`, `<custom:*>` ega `<bpmn:subProcess>`.
* Kohatäiteid nagu "Task 1", "Flow X".
* Diagrammita faile — **fail peab sisaldama `bpmndi:BPMNDiagram` osa**.

---

### 📁 Salvesta kõik genereeritud failid projekti `bpmn` kausta.

---

### 📤 Väljund:

* Väljasta **ainult `.bpmn` XML-fail**, **ilma markdowni või selgitusteta**.


