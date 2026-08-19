# Kinnistute nupud

See loend ühendab kinnistute mooduli nupud ja seadistustes asuva kinnistute halduse tööriistad. Nuppude eeldused, katkestamine, andmemõju ja auditi tähelepanekud on failis [Kinnistute nuppude detailaudit](04_01_kinnistute_nuppude_detailaudit.md). Kinnistute kasutusvood on juhendites [Kinnistute mooduli kasutamine](../15_kinnistute_mooduli_kasutamine.md) ning [Kinnistute kihi seadistamine ja haldamine](../05_kinnistute_kihi_seadistamine_ja_haldamine.md).

## Kinnistute moodul

| Nupp | Asukoht | Lühikirjeldus |
|---|---|---|
| **Vali kaardilt** | Kinnistute mooduli päis | Käivitab ristkülikvaliku kinnistute põhikihil ja avab valiku esimese kinnistu andmed. |
| **Laienda/ahenda seotud moodul** noolenupuke | Kinnistu seotud andmete iga moodulirühma päis | Näitab või peidab selle mooduli seotud kirjete read. |

Seotud kirjete ridadel kasutatakse samu kausta-, brauseri-, kaardi- ja lisatoimingute nuppe nagu tavalisel kirjekaardil. Vaata [Loendid, filtrid ja kirjekaardid](02_loendid_filtrid_ja_kirjekaardid.md).

## Kinnistute haldus seadistustes

| Nupp | Asukoht | Lühikirjeldus |
|---|---|---|
| **Ava Maa-ameti leht** | Seadistused → Kinnistud → Kinnistute haldus | Avab Maa-ameti andmete allalaadimise veebilehe. |
| **Lisa SHP fail** | Sama halduskaart | Valib kinnistute SHP-faili ja laadib selle QGIS-i impordikihina. |
| **Lisa kinnistuid** | Sama halduskaart | Käivitab kinnistute valimise ja Kavitrosse või põhikihti lisamise töövoo. |
| **Eemalda kinnistu** | Sama halduskaart | Käivitab põhikihilt valimise ning pakub taustateenuses arhiveerimist, taastamist või kustutamist; kustutamisel proovitakse eemaldada vasted ka põhikihist. |
| **Kustuta ID järgi** | Sama halduskaart | Avab erakorralise dialoogi ühe Kavitro kinnistu kustutamiseks sisemise ID järgi. |
| **Loo/paranda otsinguväli** | Sama halduskaart | Loob või parandab kinnistute kihi otsinguks kasutatava välja ja selle väärtused. |

Geospatiali seadistusrežiimis on **Ava Maa-ameti leht** ja **Lisa SHP fail** passiivsed. **Lisa kinnistuid** tehakse selles režiimis alati aktiivseks, kuid töövoog vajab endiselt sobivat impordikihti ning põhi- ja arhiivikihti.

## SHP-impordi kihivalikud

| Nupp | Asukoht | Lühikirjeldus |
|---|---|---|
| **Loo GeoPackage'i kihid** | Puuduva põhikihi korral pärast SHP-faili valimist | Loob valitud GeoPackage'i tühja põhi- ja arhiivikihi ning salvestab nende viited kohe. |
| **Jätka ainult SHP-kihiga** | Sama valik | Laadib ajutise impordikihi põhi- ja arhiivikihti loomata. |
| **Lisa kihid** | Valitud `.gpkg` fail on juba olemas | Lisab olemasolevasse faili puuduvad kinnistukihid; kogu faili üle ei kirjutata. |
| **Tühista** | Eelmised valikud või failidialoog | Katkestab enne impordikihi või uute kihtide loomist. |

## Lisamisviisi valik

| Nupp | Asukoht | Lühikirjeldus |
|---|---|---|
| **Vali kaardilt** | Pärast **Lisa kinnistuid** vajutamist | Lubab valida ajutise impordikihi objekte QGIS-i kaardilt. |
| **Vali asukoha järgi (loend)** | Sama valik | Avab maakonna, omavalitsuse ja asustusüksuse filtritega loendi. Lisamise sihiks on kõik tabelis olevad read. |
| **Tühista** | Sama valik | Sulgeb valiku töövoogu avamata. |

Puuduva arhiivikihi korral võib enne lisamisdialoogi avaneda valik **Ava Seaded**, **Loo/lae GPKG-s…** või **Tühista**. Teise valiku järel tuleb sisestada arhiivikihi nimi või toiming tühistada.

## Kinnistute lisamise dialoog

| Nupp | Asukoht | Lühikirjeldus |
|---|---|---|
| **Vali kõik** | Kinnistute lisamise dialoogi tabeli kohal | Valib kõik parajasti tabelis kuvatud read. Asukohaloendi režiimis ei muuda see lisamise ulatust. |
| **Tühjenda valik** | Sama rida | Eemaldab visuaalse tabelivaliku. Asukohaloendi režiimis jäävad kõik tabeliread siiski lisamise sihiks. |
| **Vali uuesti kaardilt** | Kaardilt lisamise režiimi tabeli kohal | Sulgeb valikuringi ajutiselt ja laseb kinnistud kaardilt uuesti määrata. |
| **Tühista** | Dialoogi jalus | Katkestab lisamise. |
| **Lisa ilma kontrollita** | Dialoogi jalus | Alustab lisamist uut tähelepanukontrolli käivitamata. Kui kontroll on juba tehtud, võib enne lisamist rakenduda selle arhiiviplaan. |
| **Käivita kontroll** | Dialoogi jalus | Kontrollib kõiki tabeliridu ning koostab ka põhikihilt puuduva impordi põhjal arhiiviplaani. |
| **Lisa valitud** | Dialoogi jalus | Alustab lisamist; kontrolli eelnev läbimine ei ole tehniliselt kohustuslik. Kaardirežiimis kasutatakse valitud ridu, asukoharežiimis kõiki tabeliridu. |
| **Sulge** | Veaseisundis, kui kinnistute impordikihti ei leitud | Sulgeb dialoogi ilma töövoogu jätkamata. |

Lisamise ajal võivad avaneda ka ühe kinnistu otsustusnupud **Jah**, **Ei**, **Jah kõigile**, **Taasta olemasolev**, **Loo uus** ja **Jäta vahele**. Nende täpne tähendus sõltub sellest, kas tunnus on Kavitros, põhikihis või ainult Kavitro arhiivis; vaata detailauditit.

## Kinnistu eemaldamise tegevuse valik

| Nupp | Asukoht | Lühikirjeldus |
|---|---|---|
| **Tühista** | Valitud kinnistute tegevuse dialoog | Sulgeb dialoogi midagi muutmata. |
| **Arhiveeri** | Sama dialoog | Proovib märkida katastritunnuse järgi leitud aktiivse Kavitro kirje arhiveerituks; QGIS-i kihte see nupp ei liiguta. |
| **Taasta arhiivist** | Sama dialoog | Proovib taastada katastritunnuse järgi leitud ühe arhiveeritud Kavitro kirje; QGIS-i kihte see nupp ei liiguta. |
| **Kustuta** | Sama dialoog | Proovib kustutada Kavitro kirje ja eemaldab seejärel sama tunnusega objektid kinnistute põhikihist. |

## ID järgi kustutamise dialoog

| Nupp | Asukoht | Lühikirjeldus |
|---|---|---|
| **Tühista** | **Kustuta ID järgi** dialoog | Sulgeb dialoogi. |
| **Kinnita** | Sama dialoog | Saadab sisestatud kinnistu ID kustutamise päringu Kavitro teenusesse. |

Kinnistute sidumise ühise ülevaatedialoogi nupud on failis [Failide ja ühisdialoogide nupud](09_failide_ja_uhisdialoogide_nupud.md).

## Seotud detailaudit

- [Kinnistute nuppude detailaudit](04_01_kinnistute_nuppude_detailaudit.md)
