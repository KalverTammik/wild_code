04 – Lõppsündmused ja erindite käsitlus
🎯 Eesmärk
Tagada, et igal protsessil oleks selgelt määratletud lõpp ja et eri tüüpi lõppsündmusi kasutataks õigesti vastavalt kontekstile.

🏁 Lõppsündmuste tüübid ja kasutus
Lõpp-event tüüp	Kasutusala	Märkused
None End Event	Edukas või tavapärane lõpetamine	Happy path’i lõpp.
Message End Event	Lõpetamisel saadetakse sõnum väljapoole	Kasuta, kui protsessi lõpp sisaldab teavitust.
Error End Event	Protsess lõppes veaga	Ainult alamprotsessis; ülemine püüab Error Boundary/Catch’iga.
Escalation End Event	Lõpetamisel teavitatakse ülemist protsessi ilma kõike lõpetamata	Kasuta eskalatsiooni olukordades.
Terminate End Event	Kohene kogu protsessi peatamine	Kasuta harva ja ainult kui see on äriloogiliselt põhjendatud.
Cancel End Event	Transaction Sub-Process’i katkestamine	Ei tohi kasutada mujal.

📌 Täiendavad reeglid
Äritühistus ≠ tehniline viga – kasuta erinevaid lõpusündmusi ja selgeid label’eid.

Kõik võimalikud lõpud tuleb ette planeerida ja modelleerida:

Success

Canceled (äritühistus)

Error (tehniline tõrge)

Timeout

Kui mõni lõpp on teadmata või lahtine, lisa Annotation koos TODO märkega.

Lõppude nimed peavad olema selged ja lühikesed (“Tellimus täidetud”, “Tellimus tühistatud”).

Vältida tuleb olukorda, kus flow jääb “õhku” – kõik teed peavad lõppema End Event’iga.

📝 Tekstiline illustratsioon
rust
Kopeeri
Redigeeri
(Start: Message "Tellimus saabus") 
   --> [Töövoog]
       --> (End: None "Täidetud")
       --> (End: None "Tühistatud")
       --> (End: Error "Maksetõrge")
       --> (End: None "Aegus")