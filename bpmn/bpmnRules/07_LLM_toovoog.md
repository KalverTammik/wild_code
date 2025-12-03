07 – LLM töövoog BPMN modelleerimisel
🎯 Eesmärk
Kirjeldada, kuidas kasutada LLM-i (nt ChatGPT, Copilot) BPMN skeemide loomiseks ja täiustamiseks, järgides meie juhendi reegleid.

🚦 Samm-sammuline protsess
1) Lähteinfo kogumine
Küsi kasutajalt kõik punktid Puuduvate osade kontrollist (06_kontrollid.md).

Ära eelda “happy path’i” — püüa tuvastada ka erandid ja kõrvalteed.

Pane kirja ka kõik välissuhtlused, andmeoperatsioonid ja võimalikud lõpud.

2) Esimese skeemi loomine
Loo BPMN skeem, järgides:

Poolide ja lane’ide reegleid (01_poolid_ja_laned.md).

Start/End event’ide reegleid (02_start_end_events.md).

Paigutusreegleid (03_paigutus.md).

Lõppsündmuste reegleid (04_loppsundmused.md).

Andmevoogude reegleid (05_andmevood.md).

3) Automaatne reeglikontroll
Lase LLM-il või teisel tööriistal võrrelda skeemi juhendi kontrollnimekirjaga.

Märgi kõik puuduolevad või ebamäärased elemendid Annotation + TODO sümboliga.

4) Täiustamine
Lisa puuduvad stardid/lõpud, erindite käsitlused, välissuhtlused ja andmevood.

Kontrolli visuaali: nooled, joondus, värvid, labelid.

5) Testimine
Ava skeem bpmn.io-s ja kontrolli, et:

Ei tekiks “unparsable content” vigu.

Kõik elemendid on korrektse BPMN XML süntaksiga.

Waterflow ja signaali alt algus reeglid on järgitud.

Tee vajadusel parandused.

6) Lõpuks
Salvesta skeem koos versiooninumbriga.

Lisa projekti dokumentatsiooni otsuslogisse (10_otsuslogi.md), mis täiendused või muudatused tehti.

📝 Kiir-prompt LLM-i jaoks
nginx
Kopeeri
Redigeeri
Loo BPMN 2.0 XML skeem järgides minu juhendit (failid 01–06).
Kasutame Waterflow paigutust, signaali alt algust ja empty pool’i reegleid.
Kontrolli, et kõik algused, lõpud, erandid, andmevood ja välissuhtlused oleksid esindatud.
Kui midagi on puudu, lisa Annotation + TODO.
Anna failina, mis avaneb bpmn.io-s veavabalt.