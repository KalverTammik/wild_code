# Loendite, filtrite ja kirjekaartide nupud

Need nupud korduvad projektide, lepingute, kooskõlastuste, servituutide, tööde ja teostusjooniste moodulites. Moodulist sõltuvad erinevused on kirjas moodulipõhistes nupufailides.

## Filtrite nupud

| Nupp või nupurühm | Asukoht | Lühikirjeldus |
|---|---|---|
| **Staatus** | Mooduli loendi kohal | Avab staatuse valiku; valiku muutmisel laaditakse loend uuesti. |
| **Liik** | Mooduli loendi kohal, liike toetavas moodulis | Avab hierarhilise liigivaliku. |
| **Tunnused** | Mooduli loendi kohal, tunnuseid toetavas moodulis | Avab Kavitro tunnuste mitmikvaliku. |
| **Vali kõik** | Staatuse-, liigi- või tunnusevaliku hüpikaken | Märgib kõik kuvatavad valikud. |
| **Tühjenda valik** | Staatuse-, liigi- või tunnusevaliku hüpikaken | Eemaldab selle filtri kõik valikud. |
| **Värskenda filtreid** ikoon | Mooduli filtrirea parem osa | Taastab salvestatud eelistused ja laadib loendi uuesti. |
| **Tühjenda filtrivalikud** ikoon | Mooduli filtrirea parem osa | Eemaldab staatuse-, liigi- ja tunnusefiltrid ning laadib täielikuma loendi. |

Filtri peaväli ja valikuread on nupulaadsed juhtelemendid, kuigi kõik neist ei ole tehniliselt tavalised tekstinupud.

Filtrite rakendumine, valikute omavaheline koosmõju, moodulierandid ja tähtajanuppude tegelik käitumine on kirjeldatud alamfailis [Filtrite nuppude detailaudit](02_01_filtrite_nuppude_detailaudit.md).

## Tähtaja kiirnupud

| Nupp | Asukoht | Lühikirjeldus |
|---|---|---|
| **Vasak arv – üle tähtaja** | Projektide, lepingute ja kooskõlastuste filtrirea rühm **Kiire!**; kohtspikker **Vajab kiiret tähelepanu** | Filtreerib kirjed, mille tähtaeg on tänasest varasem. |
| **Parem arv – tähtaeg läheneb** | Sama tähtajarühm | Filtreerib kirjed, mille tähtaeg on tänasest kuni kolme päeva kaugusel. |

Nuppudel kuvatakse tekstisildi asemel kirjete arv. Aktiivne nupp on kujundusega esile tõstetud.

## Kirjekaardi detail ja staatus

| Nupp või nupulaadne toiming | Asukoht | Lühikirjeldus |
|---|---|---|
| **… Detailne ülevaade** | Kirjekaardi alumine serv | Avab või sulgeb moodulipõhise detailvaate. |
| **Staatuseriba** | Kirjekaardi vasak serv | Näitab staatust; tööde ja teostusjooniste kaardil avab klõps staatuse muutmise valiku. |
| **Staatuse valikurida** | Töö või teostusjoonise staatuse hüpik | Muudab kirje staatuse valitud väärtuseks ja värskendab kaarti. |
| **Kirjelduse link** | Kirjekaardi detailvaate kirjeldus või tingimused | Avab kontrollitud veebiaadressi, kohaliku faili, kausta või kinnitatud võrgutee. Enne välist avamist kuvatakse sihtkoht ja vaikimisi eitav kinnitus. |
| **Faili nimi** | Kirjekaardi detailvaate failide kokkuvõte | Avab valitud faili sisemise eelvaate. |
| **Pildi eelvaate ikoon** | Pildifaili rea parem serv | Avab sama faili pildieelvaate. |

## Ühised kirjekaardinupud

| Nupp | Asukoht | Lühikirjeldus |
|---|---|---|
| **Ava kaust** kaustaikoon | Kirjekaardi parempoolne toimingurida | Avab kirje `filesPath` kausta või veebiaadressi; nupp puudub töödel ja teostusjoonistel ning on passiivne tühja tee korral. |
| **Ava kirje brauseris** Kavitro ikoon | Kirjekaardi toimingurida | Avab sama kirje Kavitro veebirakenduses. |
| **Seosta kinnistuid / Näita seotud kinnistuid kaardil** | Kirjekaardi toimingurida | Seoseta kirjel käivitab seostamisikoon kinnistute valimise ja kinnitamise töövoo. Vähemalt ühe seose korral valib kaardiikoon seotud kinnistud ning toetatud moodulis proovib fokuseerida ka mooduli põhikihi objekti. |
| **Rohkem toiminguid** plussikoon | Kirjekaardi toimingurida | Avab moodulipõhiste lisatoimingute menüü. |
| **Seosta kinnistuid** | Iga kirjekaardi **Rohkem toiminguid** menüü | Käivitab kinnistute kaardilt valimise ja seoste ülevaatamise. |

## Kirjekaardinuppude olemasolu mooduliti

| Moodul | Ava kaust | Ava brauseris | Näita kaardil | Rohkem toiminguid | Detail |
|---|:---:|:---:|:---:|:---:|:---:|
| Projektid | Jah | Jah | Jah | Jah | Jah |
| Lepingud | Jah | Jah | Jah | Jah | Jah |
| Kooskõlastused | Jah | Jah | Jah | Jah | Jah |
| Servituudid | Jah | Jah | Jah | Jah | Jah |
| Tööd | Ei | Jah | Jah | Jah | Jah |
| Teostusjoonised | Ei | Jah | Jah | Jah | Jah |

## Seotud moodulipõhised loendid

- [Filtrite nuppude detailaudit](02_01_filtrite_nuppude_detailaudit.md)
- [Projektide nupud](05_projektide_nupud.md)
- [Lepingute ja kooskõlastuste nupud](06_lepingute_ja_kooskolastuste_nupud.md)
- [Servituutide nupud](07_servituutide_nupud.md)
- [Tööde ja teostusjooniste nupud](08_toode_ja_teostusjooniste_nupud.md)
