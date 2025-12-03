03 – Paigutus ja joonestus
🎯 Eesmärk
Luua visuaalselt selged ja loogilised BPMN skeemid, kus protsessi voog on kergesti jälgitav nii inimestele kui ka LLM-idele.

📐 Üldised joondusreeglid
Vasak → Parem on peamine voolusuund (start vasakul, end paremal).

Vool peab olema sirge happy path’i puhul; kõrvalharud lähevad üles- või allapoole.

Kasuta Manhattan-routing’ut (90° nurgad) ja väldi liigselt diagonaalseid ühendusi.

Vältida tuleb flow crossing’ut (jooned ei ristu ilma selge visuaalse vajaduseta).

Joonte ühenduspunktid peavad olema elementide külgedel (center-side anchoring).

🌊 Waterflow põhimõte
Happy path kulgeb järjest, sammud liiguvad nagu kosk – iga järgmine samm asub eelmisega samal horisontaaljoonel või veidi allpool, et vältida tagasivoolu muljet.

Alternatiivteed (error, cancel) hargnevad põhivoolust üles või alla ja pöörduvad tagasi nii lühidalt kui võimalik.

Täiendatud reegel: kõik järgmised lane’id/poolid algavad täpselt sealt, kus nende aktiveeriv signaal või sõnum tekib – joonista esimene element signaali täpselt alla.

📍 Signaali/sõnumi alt algus
Kui pooli/lane’i aktiveerib signaal või sõnum teiselt poolelt, joonda esimene element vertikaalselt selle sõnumi alla.

Vältida tuleb olukorda, kus kõik lane’id algavad samalt vertikaaltasandilt – see võib tekitada eksitava mulje, et kõik aktiveeruvad korraga.

Kui lane’il pole oma protsessi (ainult sõnumivahetus), kasuta empty pool või black-box pool’i, et vältida tühje alasid.

🔄 Tagasivoolu vältimine
Vältida tuleb sequence flow’d, mis liiguvad paremalt tagasi vasakule – see rikub lugemisloogikat.

Kui tagasivool on vältimatu (nt loop), märgi see selgelt loop markeriga või lisa selgitav annotation.

🎨 Visuaalsed rühmitused
Kui on vaja esile tuua tegevuste komplekti üle mitme lane’i, kasuta Group’i.

Group ei liigu koos elementidega – kui vajad liigutamist koos sisuga, kasuta lane’i või sub-process’i.

Group’i pealkiri peab selgelt kirjeldama rühma eesmärki.

📝 Tekstiline illustratsioon
pgsql
Kopeeri
Redigeeri
[Pool: Klient]        [Pool: Rakendus]
                      Lane: Server Logic
(Start) --> Task -->  (Message "Tellimus")
                      |
                      v
                      (Start Event: Message "Tellimus")
                      --> Task (Kontrolli varu)
Klient: empty pool, ainult sõnumisaatja.

Rakendus: lane algab täpselt sõnumi alt.