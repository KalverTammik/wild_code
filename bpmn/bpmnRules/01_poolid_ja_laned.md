01 – Poolid ja Laned
🎯 Eesmärk
Määratleda, kuidas ja millal kasutada pool’e (Participant) ja lane’e (Lane), et hoida BPMN skeemid selged, loetavad ja üheselt mõistetavad nii inimestele kui ka LLM-idele.

📦 Poolid (Participants)
Definitsioon: eraldiseisev osaleja või süsteem protsessis (nt “Kasutaja (veebiklient)”, “Rakendus”, “Makseteenus”).

Reeglid:

Iga iseseisev süsteem või organisatsioon → eraldi pool.

Väline teenus, mille sisemist loogikat ei modelleerita → black box pool (tühi pool, ainult nimi ja sõnumivoog).

Kui klient (väliskasutaja) on protsessis ainult algataja ja/või sõnumisaatja, kasuta empty pool (tühi, ilma lane’ita või elementideta), et joonised jääksid lihtsad.

🛤️ Laned (Lanes)
Definitsioon: roll või alamvaldkond pooli sees (nt “Admin”, “Server Actions”).

Reeglid:

Lane jagab pooli sisemise loogika erinevate rollide või komponentide järgi.

Lane’id peavad alati sisaldama flowNodeRef viiteid (ehk seal peab olema vähemalt üks element).

Kui lane on tühi, eemalda see või muuda group elemendiks.

🧩 Pool vs Lane vs Group vs Sub-Process
Tüüp	Milleks kasutada?	Liigutamine koos elementidega?
Pool	Eraldi süsteem või organisatsioon	Jah
Lane	Roll või alamvaldkond pooli sees	Jah
Group	Visuaalne rühmitus üle poolide/lane’ide (ei mõjuta voogu)	Ei (liigutab ainult groupi, mitte sisu)
Sub-Process	Detailne alamloogika konteinerina	Jah

💡 Kui vajad, et kõik elemendid liiguksid koos, kasuta lane’i või sub-process’i, mitte group’i.

🌊 Waterflow põhimõte
Põhisuund vasakult → paremale (start vasakul, lõpp paremal).

“Happy path” kulgeb võimalikult sirgelt ja ühel kõrgusel.

Alternatiiv- ja veateed hargnevad üles- või allapoole ja pöörduvad tagasi põhivoolu juurde lühikese lõiguga.

📍 Signaali alt algus
LLM-ile üheselt mõistetav muster:

Kui protsessi algus on signaali või sõnumiga seotud, joonda esimene element (nt Message Start Event) täpselt lane’i/poole vasakusse serva.

Kui sama poolis on mitu stardipunkti, hoia need joondatud vertikaalselt.

📝 Tekstiline illustratsioon
sql
Kopeeri
Redigeeri
[Empty Pool: Kasutaja]       [Pool: Rakendus]
                              +--------------------+
                              | Lane: Server       |
(Start Event) ---> Task --->  | Lane: Workflow     |
                              +--------------------+
Vasak pool: tühi (empty pool) kliendi jaoks, ainult nimi ja sõnumivool.

Parem pool: kaks lane’i (Server ja Workflow).

Esimene sündmus joondatud vasakule (signaali/sõnumi alt alg