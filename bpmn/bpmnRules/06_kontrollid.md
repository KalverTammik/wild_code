06 – Kontrollid ja puuduvate osade tuvastus
🎯 Eesmärk
Enne modelleerimist ja enne skeemi avaldamist tuvastada kõik olulised protsessiosad ning tagada, et skeem oleks täielik ja üheselt mõistetav.

🔍 1) Puuduvate osade kontroll (Before modeling)
Kontrollküsimused:

Algused: Kes käivitab protsessi? On mitu algust (automaatne vs käsitsi)?

Lõpud: Success, canceled, error/exception, timeout.

Välissuhtlus: Milliste API-de, kasutajate või välisteenustega suheldakse (köök, tarne, makse…)?

Ootamine/otsus: On kõik “wait for user/service” hetked kirjas?

Vigade käsitlus: On kirjeldatud out-of-stock, maksetõrge, hilinemine jne?

Andmeoperatsioonid: Millal toimub create/update/delete? Kas vihjed (“tellimus loodud”) on täpsustatud?

📌 Reegel: Kui mõni punkt on puudu või ebamäärane, lisa 📝 Annotation koos TODO märkega skeemile. Ära eelda, et “happy path” on ainus vajalik voog.

✅ 2) Kiirkontroll enne avaldamist (Publish check)
Nimed selged: Kõik elemendid on selgelt ja ühtlaselt nimetatud.

Värvid/palett: Kasutatakse juhendis määratud värvikoode.

Voolu loogika: Nooled ei ristu (või on ristumised minimaalsed ja põhjendatud).

Labelid lisatud: Yes/No, Canceled, Retry jne; mitte ainult värviga eristamine.

Data Association ainult activity sees: Andmeühendused joonistatud eraldi, mitte sequence flow’s.

Properties: Skeemil on allika versioon + TODO-de loetelu.

📝 Mini-mall LLM-i jaoks
bash
Kopeeri
Redigeeri
Enne skeemi teen kiire kontrolli. Palun kinnita:
1) Algtrigger(id)
2) Lõpud (success/canceled/error/timeout)
3) Välissuhtlused (kellele/millal)
4) Otsustus- ja ootamiskohad
5) Andmeoperatsioonid (create/update/delete)
6) Tüüpilised erandid ja käsitlus
Kui midagi on lahtine, märgin skeemile TODO-ga.