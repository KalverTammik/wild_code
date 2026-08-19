# Failide ja ühisdialoogide nupud

See fail koondab nupud, mida kasutavad mitu moodulit või mitu töövoogu. Moodulipõhises failis neid samu nuppe uuesti üksikasjalikult ei kirjeldata.

Nuppude eeldused, mahupiirid, katkestamine, andmemõju ja veateed on alamfailis [Failide ja ühisdialoogide nuppude detailaudit](09_01_failide_ja_uhisdialoogide_nuppude_detailaudit.md).

## Detailvaate failide kokkuvõte

| Nupp või nupulaadne toiming | Asukoht | Lühikirjeldus |
|---|---|---|
| **Faili nimi** | Kirjekaardi detailvaate failide loend | Avab valitud faili sisemise eelvaate või kuvab teate, kui vormingut ei toetata. Toetamata PDF-käitusaja korral eelvaatedialoogi ei avata. |
| **Pildi ruudukujuline eelvaateikoon** | Pildifaili rea parem serv | Avab pildi eelvaate; funktsioon kattub sama faili nime vajutamisega. |

Failide kokkuvõte kuvatakse lepingu, kooskõlastuse, servituudi, töö ja teostusjoonise detailvaates.

## Täieliku failihalduse dialoog

Dialoog on ette nähtud avanema servituudi **Rohkem toiminguid → Failid** kaudu. Praeguses koodiversioonis viitab menüütoiming aga puuduvale `_open_item_files` käsitlejale ning dialoogiklassi ei looda kusagil mujal. Seetõttu ei ole täielik failihaldus kasutajaliidesest avatav. Allolevad nupud kirjeldavad olemasolevat dialoogiklassi, mis muutub kasutatavaks pärast avamisvoo parandamist.

| Nupp | Asukoht | Lühikirjeldus |
|---|---|---|
| **Värskenda** | Failidialoogi alumine vasak osa | Laeb kirje failide loendi Kavitrost uuesti. |
| **Laadi üles** | Sama nupurida | Avab mitme faili valija ja laadib failid ükshaaval kirje juurde. |
| **Eelvaade** | Sama nupurida | Avab tabelis valitud faili sisemise eelvaate; valikuta on nupp passiivne. |
| **Kustuta** | Sama nupurida | Küsib vaikimisi tühistava kinnituse ja kustutab valitud faili Kavitrost; valikuta on nupp passiivne. |
| **Sulge** | Dialoogi alumine parem osa | Sulgeb failihalduse dialoogi. |

Topeltklõps failitabeli real käitub nagu **Eelvaade**.

## Faili eelvaate dialoog

| Nupp | Asukoht | Lühikirjeldus |
|---|---|---|
| **Ava väliselt** | Faili eelvaate alumine vasak osa | Laadib kaugfaili vajaduse korral täielikult ajutisse faili ja avab selle operatsioonisüsteemi vaikerakendusega. |
| **Sulge** | Eelvaate alumine parem osa | Sulgeb faili eelvaate. |

## Kinnistuseoste ülevaatedialoog

Seda dialoogi kasutavad projektide, lepingute, kooskõlastuste, servituutide, tööde ja teostusjooniste **Seosta kinnistuid** toimingud.

| Nupp | Asukoht | Lühikirjeldus |
|---|---|---|
| **Vali uuesti** | Kinnistuseoste ülevaatedialoogi jalus | Sulgeb ülevaate ja käivitab uute kinnistute kaardilt valimise uuesti. |
| **Tühista** | Sama jalus | Katkestab uute seoste lisamise. |
| **Kinnita** | Sama jalus | Lisab teenusest leitud kaardivaliku kinnistud olemasolevatele Kavitro seostele; varasemaid seoseid ei eemaldata. |

Dialoog kuvab küll eraldi juba seotud ja uued kinnistud, kuid pole lõpliku seoseloendi redaktor. Praegune ühine töövoog toetab ainult uute seoste lisamist.

## Ühised dialooginupud

| Nupp | Tüüpiline asukoht | Lühikirjeldus |
|---|---|---|
| **OK** | Teate-, valiku- ja seadistusdialoog | Kinnitab teate või sisestuse ning sulgeb dialoogi; sisestuse sisulise kehtivuse otsustab avav töövoog. |
| **Kinnita** | Kirjutava toimingu dialoog | Annab dialoogi tulemuse avavale töövoole; varasemad sammud võivad olla juba salvestatud. |
| **Tühista** | Enamiku dialoogide jalus | Sulgeb praeguse dialoogi või saadab katkestustulemuse; enne dialoogi tehtud muudatusi see automaatselt tagasi ei võta. |
| **Katkesta** | Geomeetria vorm või moodulipõhine edenemisaken | Katkestuse tegelik mõju sõltub avavast töövoost ega tähenda alati juba tehtud sammude tagasivõtmist. |
| **Sulge** | Lugemiseks mõeldud detail-, tulemuse- ja eelvaatedialoog | Sulgeb vaate; ei tähenda automaatselt andmete muutmist. |
| **×** | Otsingutulemuse, olekuriba või väikese hüpikakna ülanurk | Peidab või sulgeb vastava ajutise vaate. |

## Valikutega teatedialoogid

Mõni üldine teatedialoog loob nupud dünaamiliselt vastavalt küsitud valikutele. Selliste nuppude nähtav tekst kirjeldab valikut ning vajutamine tagastab sama valiku käivitanud töövoole. Detailauditis tuleb need siduda konkreetse avava nupu ja olukorraga, mitte käsitleda ühe universaalse funktsioonina.

## Edenemisdialoogi nupp

| Nupp | Asukoht | Lühikirjeldus |
|---|---|---|
| **Tühista** | SHP-impordi edenemisdialoog | Muudab nupu tekstiks **Cancelling...**, kuid praegune imporditöö ei kuula katkestussignaali ja jätkab töötamist. |
