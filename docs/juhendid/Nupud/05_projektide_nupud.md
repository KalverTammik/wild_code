# Projektide nupud

See fail koondab projektikaardi ja projektiala töövoogude nupud. Nuppude eeldused, andmemõju, katkestamine, veateed ja auditi leiud on failis [Projektide nuppude detailaudit](05_01_projektide_nuppude_detailaudit.md). Projektide mooduli põhjalik kasutus on juhendis [Projektide mooduli kasutamine](../13_projektide_mooduli_kasutamine.md). Filtrite, tähtaja ja ühiste kirjekaardinuppude kirjeldus on failis [Loendid, filtrid ja kirjekaardid](02_loendid_filtrid_ja_kirjekaardid.md).

## Projektikaardi ühised nupud

| Nupp | Asukoht | Lühikirjeldus |
|---|---|---|
| **… Detailne ülevaade** | Projektikaardi alumine serv | Laiendab või ahendab projektikaardi sees seotud moodulite edenemise tahvli. |
| **Ava kaust** | Projektikaardi toimingurida | Avab projekti `filesPath` kausta või veebiaadressi; tühja väärtuse korral on nupp passiivne ning projektikausta lingi salvestamisel uuendatakse sama nuppu kohe. |
| **Ava kirje brauseris** | Projektikaardi toimingurida | Avab projekti Kavitro veebirakenduses. |
| **Seosta kinnistuid / Näita seotud kinnistuid kaardil** | Projektikaardi toimingurida | Seoseta projektil käivitab seostamisikoon kinnistute seostamise. Seosega projektil valib kaardiikoon seotud kinnistud ja proovib fokuseerida sama projekti ala projektide põhikihil. |
| **Rohkem toiminguid** | Projektikaardi toimingurida | Avab projekti lisatoimingute menüü. |

## Projekti „Rohkem toiminguid“ menüü

| Toiming | Asukoht | Lühikirjeldus |
|---|---|---|
| **Genereeri projekti kaust** | Projektikaart → Rohkem toiminguid | Kontrollib lähte- ja sihtkausta, muudab arvutatud nime üheks turvaliseks kaustanimeks ning näitab enne kopeerimist täielikku sihtteed vaikimisi eitavas kinnituses. |
| **Ava projekti ala eelvaade** | Sama menüü | Avab seotud kinnistutest projektiala koostamise dialoogi ning loob võimaluse korral eelvaate automaatselt. |
| **Joonista uus seotud ala kaardile** | Sama menüü | Käivitab uue polügooni käsitsi joonistamise projektide põhikihile ja seob loodud objekti projektiga. |
| **Seosta kinnistuid** | Sama menüü | Käivitab uute kinnistuseoste kaardilt valimise ja Kavitrosse lisamise; olemasolevaid seoseid selle vooga ei eemaldata. |

## Projektiala eelvaate dialoog

| Nupp | Asukoht | Lühikirjeldus |
|---|---|---|
| **Seosta kinnistuid** | Projektiala eelvaate alumine toimingurida | Avab kinnistute kaardilt valimise ja lisab kinnitatud uued seosed projektile. |
| **Värskenda eelvaadet** | Sama toimingurida | Loeb seotud kinnistud uuesti ja arvutab eelvaate kehtivate puhvri- ning ümardusvalikutega. |
| **Salvesta ala kihile** | Sama toimingurida | Lisab eelvaate projektide QGIS-i põhikihile või uuendab leitud projektiobjekti; Kavitro geomeetriat see nupp ei uuenda. |
| **Puhasta eelvaade** | Sama toimingurida | Eemaldab selle projekti ajutised eelvaatekihid, kuid mitte põhikihile juba salvestatud ala ega kinnistuseoseid. |
| **Sulge** | Dialoogi parem alanurk | Eemaldab ajutised eelvaatekihid ja kinnistukihi valiku ning sulgeb dialoogi. |

## Kinnistuseoste ülevaatedialoog

| Nupp | Asukoht | Lühikirjeldus |
|---|---|---|
| **Vali uuesti** | Seoste ülevaatedialoogi jalus | Sulgeb ülevaate ja käivitab uute kinnistute kaardivaliku uuesti. |
| **Tühista** | Sama jalus | Katkestab uute seoste lisamise; juba olemasolevad seosed säilivad. |
| **Kinnita** | Sama jalus | Lisab Kavitrosse kaardilt valitud ja teenusest leitud kinnistud; olemasolevaid seoseid ei asendata ega eemaldata. |

## Projektide seadistusnupud

Ajutise projektikihi, kaustade ja nime reegli nupud on failis [Seadistuste nupud](03_seadistuste_nupud.md).

## Seotud detailaudit

- [Projektide nuppude detailaudit](05_01_projektide_nuppude_detailaudit.md)
