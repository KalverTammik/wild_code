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
| **Ava väliselt** | Faili eelvaate alumine vasak osa | On aktiivne ainult lubatud failitüübi korral. Küsib enne allalaadimist ja operatsioonisüsteemi vaikerakendusega avamist eraldi kinnituse. |
| **Sulge** | Eelvaate alumine parem osa | Sulgeb faili eelvaate. |

### Välise avamise turvareeglid

**Ava väliselt** ei käivita faili kohe. Visuaal kuvab kõigepealt failinime ja kontrollitud faililaiendiga kinnituse. Vaikevalik on **Ei**; kaugfail laaditakse alla ja antakse arvuti vaikerakendusele ainult valiku **Jah** järel.

Väliselt saab avada järgmisi failitüüpe:

- dokumendid ja tabelid: `.asice`, `.bdoc`, `.csv`, `.ddoc`, `.doc`, `.docx`, `.ods`, `.odt`, `.pdf`, `.rtf`, `.txt`, `.xls`, `.xlsx`;
- joonise- ja CAD-failid: `.cad`, `.dgn`, `.dwg`, `.dxf`;
- pildid: `.bmp`, `.gif`, `.jpeg`, `.jpg`, `.png`, `.webp`;
- videod ja arhiivid: `.mov`, `.mp4`, `.zip`.

Nupp on passiivne, kui failitüüp pole loendis, sobivat laiendit ei leita või teenuse ja failinime laiendid on mõlemad olemas, kuid ei ühti. Käivitatavaid ja aktiivsisu sisaldavaid vorminguid, näiteks `.exe`, `.cmd`, `.bat`, `.ps1`, `.js`, `.html` ja `.svg`, Visuaal välisele rakendusele ei anna. HTML-i, SVG-d ja mõnda lähtekoodifaili võib endiselt kuvada tekstilise või sisemise eelvaatena.

Kui kasutaja küsib passiivse **Ava väliselt** nupu kohta, kontrolli faili nime ja Kavitros näidatavat tüüpi. Ära soovita turvakontrollist möödumiseks faili ümber nimetada. Palu üleslaadijal lisada fail õige nime ja toetatud vorminguga või käsitle tegelikult toetamata failitüüpi organisatsiooni failiturbe reeglite järgi Kavitro veebirakenduses.

## Kirjeldustes olevate linkide avamine

Kirjelduse, tingimuste või muu detailteksti link kontrollitakse enne avamist. Lubatud on:

- `http`- ja `https`-veebilingid; enne brauseri avamist kuvatakse täielik aadress ning `http`-lingi puhul krüpteerimata ühenduse hoiatus;
- kohalikud failid, mille laiend kuulub eespool toodud välise avamise nimekirja;
- Visuaali sisemise eelvaatega toetatud kohalikud PDF-, pildi- ja tekstifailid;
- kohalikud kaustad;
- Windowsi võrgufailid ja -kaustad pärast eraldi võrgutee kinnitust.

Kõigi väliste avamiste kinnituse vaike- ja tühistamisvalik on **Ei**. Võrgutee kinnituses kuvatakse serveri nimi ja täielik tee. Visuaal ei kontrolli võrgufaili või -kausta olemasolu enne seda kinnitust, sest juba olemasolu kontrollimiseks peab Windows võrguserveriga ühenduse looma.

Võrgutee võib olla kujul `\\server\kaust\fail.pdf`, `file://server/kaust/fail.pdf` või kasutaja arvutis võrgukettaks ühendatud tee, näiteks `Z:\kaust\fail.pdf`. Kohalik fail võib olla lingitud `file:///C:/kaust/fail.pdf` või Windowsi tavalise failiteena. Tundmatud protokollid, suhtelised failiteed ja lubamata failitüübid blokeeritakse ning kasutajale kuvatakse põhjus.

Kui toetatud PDF-, pildi- või tekstifail avatakse kirjelduse lingist, kasutatakse kõigepealt sisemist eelvaadet. Muud lubatud failitüübid antakse arvuti vaikerakendusele ainult eraldi kinnituse järel. Käivitatavaid ja aktiivsisu sisaldavaid vorminguid väliselt ei avata.

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
