02 – Start- ja End-Eventid
🎯 Eesmärk
Tagada, et kõik protsessid algaksid ja lõppeksid selgelt määratletud sündmustega. See aitab nii visuaalsel loetavusel kui ka LLM-ide täpsel mõistmisel.

🚀 Start Events
Reeglid:

Igal protsessil peab olema vähemalt üks start event.

Start event’i tüüp peab vastama käivitajale:

None Start Event – käsitsi käivitamine või automaatne algus süsteemi sees.

Message Start Event – protsess algab sõnumi saabumisest (nt kliendi tellimus).

Timer Start Event – protsess algab kindlal ajal või perioodil.

Signal Start Event – globaalse signaali käivitamine (kasuta harva, eelistada Message’t).

Kui protsessil on mitu võimalikku algust, modelleeri need eraldi start event’idena.

🏁 End Events
Reeglid:

Igal protsessil peab olema vähemalt üks end event.

Lõpu tüüp vali vastavalt tähendusele:

None End Event – protsess lõppes edukalt (happy path).

Message End Event – protsess saadab lõpetamisel sõnumi väljapoole.

Error End Event – protsess lõppes veaga (kasuta ainult alamprotsessis; ülemine püüab boundary/catch’iga).

Escalation End Event – teavitab ülemist protsessi, kuid ei lõpeta seda.

Terminate End Event – katkestab kogu protsessi koheselt (kasuta harva).

Cancel End Event – ainult transaction sub-process’i puhul.

📌 Täiendavad reeglid
Kõik lõpud tuleb kaardistada enne modelleerimist (success, canceled, error, timeout).

Kui mõni lõpp on ebamäärane, lisa Annotation ja märgi TODO.

Sama kehtib ka start event’ide puhul – kõik võimalikud algused tuleb teada ja modelleerida.

Lõpud ei tohiks “kaotsi minna” (flow peab jõudma lõpuni).

📝 Tekstiline illustratsioon
mathematica
Kopeeri
Redigeeri
(Start: Message "Tellimus saabus") --> [Tasks...] --> (End: None "Tellimus täidetud")
                                   \-> (End: None "Tellimus tühistatud")
                                   \-> (End: Error "Maksetõrge")