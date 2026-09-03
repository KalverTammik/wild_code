# Failide ja ühisdialoogide nuppude detailaudit

See juhend kirjeldab Visuaali failide ja korduvkasutatavate dialooginuppude tegelikku käitumist praeguse koodibaasi järgi. Kaetud on kirjekaardi failikokkuvõte, täieliku failihalduse olemasolev, kuid ühendamata dialoog, faili eelvaade, kinnistuseoste ülevaade, ühised teate- ja sisestusdialoogid ning SHP-impordi edenemisaken.

Moodulipõhise nupu eel ja järel toimuvad sammud jäävad vastava mooduli detailauditi teemaks. Sama tekstiga **Tühista**, **Kinnita** või **Sulge** ei tähenda kõikides töövoogudes automaatselt sama andmemõju.

## Mõju lühikaart

| Nupp või nupurühm | Peamine mõju | Kas toiming on tagasi võetav? |
|---|---|---|
| Detaili **Faili nimi** ja pildi eelvaateikoon | Laadib faili eelvaateks ning avab modaalse eelvaatedialoogi | Püsiandmeid ei muudeta |
| Failihalduse **Värskenda** | Laadib Kavitrost kuni 200 faili | Püsiandmeid ei muudeta; varasem tabel võib vea korral nähtavale jääda |
| **Laadi üles** | Lisab ühe või mitu faili Kavitro kirjele | Automaatset tagasivõtmist ei ole |
| Failihalduse **Eelvaade** ja rea topeltklõps | Avab valitud faili eelvaate | Püsiandmeid ei muudeta |
| **Kustuta** | Kustutab kinnituse järel faili Kavitrost | Visuaalis tagasivõtmise võimalust ei ole |
| Eelvaate **Ava väliselt** | Laadib kaugfaili ajutisse asukohta ja annab selle operatsioonisüsteemile avamiseks | Kavitro andmeid ei muudeta; ajutine fail jääb kettale |
| Eelvaate **Sulge** | Sulgeb vaate ja eemaldab sisemise PDF-i ajutise faili | Väliselt avamiseks loodud ajutist faili ei eemaldata |
| Seoste **Vali uuesti** | Loobub praegusest kinnitamata valikust ja naaseb kaardivalikusse | Jah, sest seoseid pole veel saadetud |
| Seoste **Tühista** | Loobub kinnitamata uutest seostest | Jah, enne kinnitamist |
| Seoste **Kinnita** | Lisab valitud kinnistuseosed Kavitrosse | Selle dialoogiga seoseid eemaldada ei saa |
| Teatedialoogi **OK** | Sulgeb teate või tagastab kinnitatud sisestuse | Sõltub avavast töövoost |
| Edenemisakna **Tühista** | Märgib dialoogi katkestatuks, kuid SHP-import jätkub | Ei peata praegust importi |

## Kättesaadavus moodulite lõikes

Failide kokkuvõte luuakse järgmiste moodulite kirjekaardi detailis:

- lepingud;
- kooskõlastused;
- servituudid;
- tööd;
- teostusjoonised.

Tööde ja teostusjooniste failid käsitletakse tehniliselt ülesande failidena. Projektikaardi detail kuvab edenemistahvlit, mitte seda failikokkuvõtet.

Täieliku failihalduse `TaskFilesDialog` klass on repos olemas, kuid ühtegi seda loovat kutset ei ole. Servituudi **Rohkem toiminguid → Failid** viitab olematule `_open_item_files` meetodile. Seetõttu saab praeguses kasutajaliideses kasutada detaili failieelvaadet, kuid mitte allpool kirjeldatud üleslaadimis- ja kustutamisnuppe.

## Detailvaate failide kokkuvõte

Detaili esimesel avamisel laaditakse Kavitrost kuni 200 faili, kuni 50 faili kaupa. Kokkuvõttes kuvatakse neist kuni viis ja ülejäänute arv tekstina. Rohkemate failide avamiseks ega täieliku loendi kuvamiseks nuppu ei ole.

Ülesannete ehk tööde ja teostusjooniste failipäring tellib failid loomise aja järgi kahanevalt. Teiste moodulite päring ei anna selles koodis järjestust ette, mistõttu lepingu, kooskõlastuse või servituudi viis kuvatavat faili ei ole tingimata viis uusimat.

Detail ja selle failiosa luuakse ühe kirjekaardi kohta ainult üks kord. Detaili ahendamine ning uuesti avamine faililoendit ei värskenda. Värske seisu jaoks tuleb mooduli loend uuesti laadida.

### Faili nimi

Failinimi on nupuna käituv tekst. Klõps kutsub välja sama eelvaate kui failihalduse **Eelvaade**. Puuduva faili UUID korral avaneb dialoog veatekstiga, kuid failisisu ei laadita.

Failinime ees kuvatav ikoon valitakse laiendi või MIME-tüübi järgi. Ikoon kirjeldab vormingut, kuid ei tõenda, et failisisu on terve või eelvaates toetatud.

### Pildi ruudukujuline eelvaateikoon

Pildifailile luuakse rea paremasse serva eraldi ruudukujuline nupp. See proovib taustal laadida kuni 2 MiB andmeid pisipildi loomiseks.

- Edu korral asendatakse vorminguikoon pildi pisipildiga.
- Liiga suure, kärbitud või vigase pildi korral jääb üldikoon alles ja eraldi veateadet ei kuvata.
- Nupu klõps avab sama faili eelvaate nagu failinime klõps.

Pisipildi olemasolu ega puudumine ei mõjuta failinime nupu aktiivsust.

## Täieliku failihalduse dialoog

Järgmised alamjaotised kirjeldavad olemasoleva klassi käitumist juhul, kui avamisvoog hiljem parandatakse. Praeguses versioonis ei saa kasutaja sellesse dialoogi jõuda.

Dialoogi loomisel laaditakse kohe kuni 200 faili. Tabel kuvab faili nime, suuruse, tüübi, üleslaadija ja loomise aja. Valida saab ühe rea. **Eelvaade** ja **Kustuta** on valikuta passiivsed; **Värskenda**, **Laadi üles** ja **Sulge** on alati aktiivsed.

Tabel sorteeritakse loomise aja nähtava, lokaadipõhiselt vormindatud teksti järgi. Tekstisort ei taga kronoloogilist järjestust, eriti kuupäevavormingus, kus päev või kuu paikneb enne aastat.

### Värskenda

Nupp teeb failipäringu kasutajaliidese lõimes ja näitab ootekursorit. Õnnestumisel ehitatakse tabel uuesti ning varasem valik kaob.

Päring tagastab maksimaalselt 200 unikaalset faili. Kui kirjel on rohkem faile, ei kuva dialoog piirangu ega järgmise lehe nuppu ning arv `200` võib näida täieliku failide arvuna.

Päringu vea korral kuvatakse hoiatus, kuid senist tabelit ja loendurit ei tühjendata ega märgita aegunuks. Kasutaja võib seetõttu jätkata töötamist vana loendiga.

### Laadi üles

Nupp avab mitme faili valija filtriga **Kõik failid**. Failitüüpi, failisuurust, valitud failide arvu ega samanimelise faili olemasolu enne saatmist ei kontrollita.

Valitud failid laaditakse üles ükshaaval, igaühe jaoks kuni 120-sekundilise päringuajaga. Dialoogil puudub katkestamisnupp. Failide vahel töödeldakse kasutajaliidese sündmusi, kuid nuppe ei keelata; teise üleslaadimise või sulgemise käivitamine poolelioleva jada ajal ei ole blokeeritud.

Tulemuseks kuvatakse:

- eduteade, kui kõik valitud failid õnnestusid;
- osalise õnnestumise hoiatus koos kuni viie ebaõnnestunud failinimega;
- veateade, kui ükski fail ei õnnestunud.

Vähemalt ühe eduka faili järel värskendatakse loendit enne lõputeate kuvamist. Kui see värskendus ebaõnnestub, võib kasutaja saada esmalt laadimisvea ja seejärel üleslaadimise eduteate, samal ajal kui tabel jääb vanaks.

Iga edukas fail on Kavitros juba eraldi salvestatud. Hilisema faili ebaõnnestumine ega dialoogi sulgemine varasemaid üleslaadimisi tagasi ei võta.

### Eelvaade ja topeltklõps

Nupp ning tabelirea topeltklõps kasutavad sama eelvaatedialoogi. Puuduva valiku korral näitaks käsitleja hoiatust, kuigi nupp ise on sellises olekus keelatud. Puuduva UUID-ga rida annab eelvaatevea.

### Kustuta

Nupp küsib faili nimega kinnituse. Kinnitusdialoogi vaikevalik on **Tühista**, mistõttu `Enter` ei kustuta faili, kui fookus jääb vaikevalikule.

**Kustuta** saadab faili UUID põhjal kustutamispäringu. Edu korral faililoend värskendatakse ja seejärel kuvatakse eduteade. Kustutamist ei saa Visuaalis tagasi võtta.

Kui kustutamine õnnestub, kuid järgnev loendi värskendamine ebaõnnestub, kuvatakse siiski kustutamise eduteade ning kustutatud fail võib vanas tabelis nähtavale jääda. Korduskatse võib seejärel anda vea.

### Sulge

Nupp lõpetab dialoogi vastusega „kinnitatud“, kuid failihalduse seisukohalt tähendab see ainult akna sulgemist. Varem üleslaaditud või kustutatud faile ei võeta tagasi.

## Faili eelvaate valikureeglid

Eelvaate liik otsustatakse teenusest tulnud MIME-tüübi ja faililaiendi järgi.

| Eelvaate liik | Toetatud näited | Mahupiir | Käitumine piiri korral |
|---|---|---:|---|
| Pilt | PNG, JPEG, BMP, GIF, WEBP, SVG | 25 MiB | Kuvatakse liiga suure faili teade |
| PDF | PDF | 40 MiB | Kuvatakse liiga suure faili teade |
| Tekst | TXT, CSV, JSON, XML, YAML, Markdown, lähtekood ja `text/*` | 512 KiB | Kuvatakse esimene 512 KiB ning kärpimisteade |
| Muu | DOCX, XLSX, DWG, ZIP, video jms | Sisemist eelvaadet pole | Kuvatakse toetamata vormingu teade ja pakutakse välist avamist |

HTML ja muud tekstivormingud kuvatakse toortekstina, mitte veebilehena. Tekst on ainult lugemiseks ning reamurdmine on välja lülitatud.

Pilt laaditakse kirjekaardi kokkuvõttest avatuna taustal. PDF, tekst ja täieliku failidialoogi kaudu avatav pilt laaditakse kasutajaliidese lõimes ootekursoriga ning aeglase ühenduse korral võib dialoog ajutiselt mitte reageerida.

PDF-i jaoks peab QGIS-i Qt WebEngine sisaldama sisseehitatud PDF-vaate tuge. Kui seda tuge pole, kuvatakse enne dialoogi loomist hoiatus ja meetod lõpetab töö. Seetõttu ei teki ka **Ava väliselt** nuppu, kuigi teiste toetamata vormingute dialoog seda pakub.

Koodis on deklareeritud kümne PDF-lehekülje piir ja vastav tõlketekst, kuid eelvaate loogika seda piirangut ei rakenda. Kuni 40 MiB PDF laaditakse tervikuna ajutisse faili ja antakse WebEngine'i vaatele.

## Ava väliselt

Kaugfaili avamisel:

1. kontrollitakse teenuse `ext` ja failinime laiendit; olemasolev väärtus peab olema lihtne ja lubatud tüüpide loendis ning mõlema olemasolul peavad need omavahel sobima;
2. kuvatakse failinime ja kontrollitud laiendiga kinnitus, mille vaike- ja tühistamisvalik on **Ei**;
3. alles valiku **Jah** järel küsitakse faili UUID põhjal ajutine allalaadimislink;
4. kogu fail laaditakse sünkroonselt operatsioonisüsteemi ajutisse kataloogi, päringuajaga kuni 120 sekundit;
5. fail avatakse Windowsis `startfile` abil või varuvariandina Qt vaikeavaga.

Lubatud vormingute täielik loend ja abikeskuse kontrolljuhis on failis [Failide ja ühisdialoogide nupud](09_failide_ja_uhisdialoogide_nupud.md). Tundmatu, käivitatava, aktiivsisu sisaldava või vastuoluliste laiendiandmetega faili korral on **Ava väliselt** passiivne. Automaatset välises rakenduses avamise haru enam ei ole. Sisemise eelvaate tugi ja välise avamise allowlist on erinevad: näiteks HTML-i või SVG sisu võib eelvaadata, kuid seda ei anta OS-i rakendusele avamiseks.

Välisel allalaadimisel ei rakendata sisemise eelvaate 25, 40 ega 0,5 MiB mahupiire. Eraldi turvakinnitus kuvatakse enne allalaadimist, kuid suur lubatud tüüpi fail võib pärast kinnitamist kasutajaliidest endiselt pikalt blokeerida.

Väliselt avamiseks loodud ajutiste failide teid hoitakse mälus, kuid olemasolevaid faile ei kustutata dialoogi sulgemisel ega plugina selles koodis. Puhastus eemaldab loendist ainult teed, mille fail on juba muul põhjusel kadunud. Tundlik fail võib seetõttu jääda kasutaja ajutisse kataloogi pärast Visuaali sulgemist.

Kohaliku PDF-i korral avatakse algne fail ega looda koopiat. Avamisvea korral kuvatakse hoiatus.

## Kirjelduse lingi avamisahel

`HtmlDescriptionWidget` ei anna kirjeldusest pärinevat `href` väärtust enam automaatselt Qt-le või operatsioonisüsteemile. Klõpsu järel liigitatakse sihtkoht esmalt ainult tekstilise URL-i ja tee tunnuste põhjal:

1. `http` ja `https` suunatakse pärast täieliku aadressiga kinnitust brauserisse; `http` kinnitus sisaldab krüpteerimata ühenduse hoiatust;
2. kohaliku absoluutse failitee korral kontrollitakse pärast liigitamist faili olemasolu ja keskset failitüüpide loendit; eelvaadatav fail avatakse sisemiselt ning muu lubatud fail antakse pärast kinnitust vaikerakendusele;
3. kohaliku absoluutse kaustatee korral küsitakse enne Exploreri avamist kinnitust;
4. UNC, hosted `file://` ja Windowsi ühendatud võrguketas liigitatakse võrguteeks enne `exists`, `realpath` või muu failisüsteemipäringu tegemist; alles eraldi serveri ja täieliku teega kinnituse järel kontrollitakse sihtkohta ning jätkatakse faili- või kaustareeglitega;
5. suhteline tee, tundmatu skeem, puuduv sihtkoht või välise avamise loendist puuduv failitüüp blokeeritakse.

TipTapi editoripoolne lingivalideerimine ei ole QGIS-i usalduspiir: API-s võib olla varem salvestatud HTML-i, käsitsi sisestatud UNC-vorm või teise kliendi loodud link. Seetõttu rakendatakse avamisreegleid iga klõpsu ajal ka plugina poolel.

## Eelvaate Sulge

Nupp sulgeb modaalse eelvaatedialoogi. Kaug-PDF-i sisemise eelvaate jaoks loodud ajutine PDF eemaldatakse sulgemisel ning WebEngine'i vaade vabastatakse.

Nupp ei kustuta:

- Kavitro faili;
- väliselt avamiseks loodud ajutist faili;
- kasutaja algset kohalikku faili.

Taustal laaditava pildieelvaate jaoks ei saadeta sulgemisel eraldi katkestustaotlust.

## Kinnistuseoste ülevaatedialoog

Ühine dialoog kuvab kaks ainult lugemiseks mõeldud loendit:

- Kavitros juba seotud kinnistud;
- praeguses kaardivalikus olevad uued kinnistud, millest olemasolevad seosed on välja jäetud.

Loendid sorditakse nähtava aadressi- ja katastritunnuse teksti järgi. Dialoogis ei saa ridu lisada, eemaldada ega märgistada. Muudatuseks tuleb kasutada **Vali uuesti** või kogu töövoog tühistada.

### Vali uuesti

Nupp märgib eraldi `reselect_requested` oleku ja sulgeb dialoogi tehniliselt tagasilükatud tulemusega. Avav töövoog eristab seda tavalisest tühistamisest ning käivitab kinnistute ristkülikvaliku uuesti.

Praegune kinnitamata uus valik asendatakse järgmise valikuga. Kavitros juba seotud kinnistud jäävad kaardile kontekstiks valituks, kuid neid ei tagastata uue valiku hulgas.

### Tühista

Nupp sulgeb ülevaate ja ei saada praeguseid uusi kinnistuid Kavitrosse. Olemasolevad seosed ei muutu.

Pärast tavapärast tühistamist taastab kirjekaardi töövoog Visuaali akna. Kaardivaliku varasem objektita katkestamine `Esc`-i, paremklõpsu või tööriistavahetusega ei jõua alati sellesse dialoogi ega samasse taastamisharusse.

### Kinnita

Nupp sulgeb dialoogi kinnitatud tulemusega. Alles seejärel:

1. lahendatakse valitud katastritunnustele Kavitro kinnistu ID-d;
2. leitud ID-d saadetakse mooduli `associate` toiminguga;
3. kõik kirje kinnistuseosed laaditakse uuesti;
4. kuvatakse tulemus ja kirjekaardi kaardinupp aktiveeritakse vajaduse korral.

Dialoog ei ole lõpliku seoseloendi redaktor. **Kinnita** ainult lisab uued seosed ning ei eemalda olemasolevaid. Eduka teate arv kirjeldab pärast toimingut värskendatud seoste koguarvu, mitte tingimata just lisatud seoste arvu.

Kinnistu-ID lahendamise ja seostamise ümber puudub ühises käsitlejas üldine erindipüüdur. Erind võib väljuda pärast dialoogi kinnitamist ilma kasutajasõbraliku veateateta ning enne kontrolleriviite tühjendamist ja akna lõplikku taastamist.

## Ühised teatedialoogid

### OK

Info-, hoiatus- ja veadialoogi **OK** on vaikimisi valitud nupp. `Enter` kinnitab ning sulgeb dialoogi. Tavapärases teates tähendab see ainult teate lugemist, mitte teate põhjustanud andmemuudatuse tagasivõtmist või uuesti käivitamist.

Kui hoiatus luuakse koos **Tühista** nupuga, tagastab **OK** tõeväärtuse `true` ja **Tühista** `false`. Tulemust peab tõlgendama konkreetne avav töövoog.

### Dünaamilised valikunupud

Valikudialoog loob nupud avaja antud tekstidest. Üks tekst võib olla märgitud tühistavaks ja üks vaikevalikuks.

- Tavalise valiku vajutamine tagastab selle nähtava teksti ning kinnitatud tulemuse.
- Tühistav valik tagastab samuti oma teksti, kuid sulgeb dialoogi tagasilükatud tulemusega.
- Akna sulgemisrist või `Esc` tagastab valikuks `None`.
- Nupu tekst ise ei määra andmemõju; avav kood võrdleb tagastatud teksti ja otsustab jätkamise.

Seetõttu on näiteks **Kustuta**, **Arhiveeri**, **Loo**, **Jätka** ja **Ava Seaded** käitumine dokumenteeritud neid avava moodulinupu detailauditis.

### Tekstisisestuse OK ja Tühista

Üherealise tekstisisestuse dialoogis kinnitavad nii **OK** kui ka sisestusvälja `Enter` väärtuse. **Tühista**, sulgemisrist ja `Esc` tagastavad tühja väärtuse ning ebaõnnestunud kinnituse.

Ühine dialoog ei valideeri tühja teksti, nime unikaalsust ega keelatud märke. Sisulise kontrolli teeb avav töövoog pärast dialoogi sulgemist.

## Sulgemisrist ×

Tavalises modaalses teate-, valiku- või sisestusdialoogis võrdub sulgemisrist enamasti tagasilükkamisega. See ei tähenda, et enne dialoogi avamist tehtud muudatused pööratakse tagasi.

Otsingutulemuste ja väikeste hüpikute `×` nupud ei kasuta seda ühist dialoogiloogikat. Nende käitumine on kirjeldatud failis [Üldnuppude ja navigeerimise detailaudit](01_01_uldnuppude_ja_navigeerimise_detailaudit.md).

## SHP-impordi edenemisdialoogi Tühista

`ProgressDialogModern` on praeguses repos kasutusel Maa-ameti SHP objektide kopeerimisel QGIS-i mälukihti.

Nupu vajutamisel:

1. dialoogi `is_cancelled` olek muutub tõeseks;
2. nupu tekstiks saab tõlkimata **Cancelling...**;
3. nupp keelatakse;
4. saadetakse `canceled` signaal.

Impordikood ei ühenda selle signaaliga ühtegi käsitlejat ega kontrolli `is_cancelled` olekut. Juba lisatud partiisid ei eemaldata ja ka ülejäänud objektide kopeerimine jätkub. Nupp ei sulge dialoogi.

`Esc` kutsub esmalt sama katkestusmeetodi ja annab klahvisündmuse seejärel edasi QDialogile, mistõttu dialoog võib sulguda, kuigi import jätkub. Sulgemisrist märgib sulgemise lõpetatud tulemuseks, mitte katkestuseks. Kuna imporditsükkel kasutab dialoogi hilisemate edenemisuuenduste jaoks, võib dialoogi enneaegne kustumine tekitada erindi ning jätta mälukihi osaliselt täidetuks.

Import ise töötab kasutajaliidese lõimes ja töötleb QGIS-i sündmusi vaid edenemisintervallidel. Suure partii ajal võib dialoog ajutiselt mitte reageerida.

Edu lõpus ajastatakse dialoogi sulgemine 1,2 sekundi pärast, kuid meetodi `finally` haru sulgeb selle kohe. Seetõttu ei pruugi lõplik **Import complete!** tekst nähtavaks jääda.

## Auditi käigus leitud parandamist vajavad kohad

Välise avamise laiendikontrolli ja kinnituse puudumine on Etapp 1A ehk WC-02 raames lahendatud. Allolevasse tabelisse jäävad teised, sellest muudatusest sõltumatud tähelepanekud.

| Prioriteet | Leid | Kasutajarisk | Soovitatav parandus |
|---|---|---|---|
| Kriitiline | Servituudi **Failid** menüü viitab olematule `_open_item_files` meetodile ja `TaskFilesDialog` klassi ei looda mujal | Täielikku faililoendit, üleslaadimist ega kustutamist ei saa Visuaalist kasutada | Lisa testitud avamiskäsitleja või eemalda katkine menüü kuni funktsiooni valmimiseni |
| Kriitiline | SHP-impordi edenemisakna katkestussignaali ega olekut ei kontrollita | **Tühista** jätab mulje katkestamisest, kuid import jätkub; kontrollimata sulgemine võib jätta osalise kihi | Kontrolli olekut igas partiis, lõpeta kontrollitult ja otsusta osalise mälukihi säilitamine või eemaldamine |
| Kõrge | PDF-i WebEngine toe puudumisel lõpetatakse enne eelvaatedialoogi loomist | Kasutajale ei pakuta **Ava väliselt** nuppu, kuigi fail on Kavitros olemas | Paku hoiatuses eraldi välise avamise valik või ava piiratud eelvaatedialoog |
| Kõrge | Väliselt avamiseks allalaaditud ajutisi faile ei kustutata | Tundlikud dokumendid jäävad kettale ja ajutine kataloog kasvab | Halda elutsüklit, paku säilitamisvalikut ning kustuta fail pärast ohutut viivitust või sessiooni lõpus |
| Kõrge | Failide üleslaadimise ajal jäävad dialooginupud aktiivseks ning toimingul puudub katkestamine | Võimalik on käivitada kattuvaid jadasid või sulgeda dialoog poole töö ajal | Keela vastuolulised nupud, kasuta taustatööd ja lisa kontrollitud katkestamine |
| Kõrge | Kinnistuseoste kinnitamise teenuseetappidel puudub ühine erindipüüdur | Dialoog sulgub, kuid kasutaja ei saa selget tulemust ning aken või kontroller võib jääda valesse olekusse | Püüa erindid, kuva sammupõhine tulemus ja taasta aken `finally` harus |
| Keskmine | Failipäringu 200 faili piir ei ole kasutajale nähtav | Dialoogi loendurit võidakse pidada täielikuks failide arvuks | Kuva piirang ja lisa lehekülgede või „Laadi veel“ tugi |
| Keskmine | Ebaõnnestunud värskendus jätab vana failitabeli nähtavale ilma aegumise märgita | Kasutaja võib eelvaadata või kustutada juba muutunud faili | Märgi tabel aegunuks, keela kirjutavad nupud või tühjenda tulemus |
| Keskmine | Failitabel sorteerib lokaliseeritud kuupäevateksti leksikograafiliselt | Failide järjekord võib olla vale | Salvesta tabelireale eraldi kuupäeva sortimisväärtus või säilita serveri järjestus |
| Keskmine | Välise avamise täisallalaadimine toimub kasutajaliidese lõimes ilma mahupiirita | Suur fail võib Visuaali kuni 120 sekundiks blokeerida | Laadi taustal, kuva maht ja edenemine ning võimalda katkestada |
| Keskmine | Edukas seostamisteade kasutab värskendatud seoste koguarvu | Kasutaja võib pidada koguarvu uute seoste arvuks | Kuva eraldi lisatud, juba olemas olnud ja lahendamata kinnistute arv |
| Madal | Kümne PDF-lehekülje konstant ja tõlketekst on kasutamata | Tegelik PDF-käitumine ei vasta koodis väljendatud piirile | Rakenda leheküljepiir või eemalda eksitav surnud seadistus |
| Madal | Edenemisakna lõpetamistekst suletakse `finally` harus kohe ja osa tekste on ingliskeelsed | Lõpptulemus jääb märkamatuks ning keelekasutus on ebaühtlane | Sulge dialoog ainult ühes lõpetamisharus ja kasuta tõlkevõtmeid |

## Soovituslik turvaline tööjärjekord

1. Kasuta detailvaate failinuppe eelkõige pildi-, teksti- ja toetatud PDF-failide lugemiseks.
2. Kui PDF-i käitusaja hoiatus ilmub, ava kirje Kavitro veebivaates; selles harus Visuaal **Ava väliselt** nuppu ei paku.
3. Kinnita välise avamise dialoog ainult siis, kui usaldad faili ja selle üleslaadijat. Passiivse nupu korral ära proovi faili ümbernimetamisega turvakontrollist mööduda.
4. Halda failide täielikku loendit, üleslaadimist ja kustutamist praegu Kavitro veebirakenduses.
5. Kontrolli kinnistuseoste dialoogis eraldi juba seotud ja uute kinnistute loendit; **Kinnita** on ainult lisav toiming.
6. Ära eelda, et dialoogi **Tühista** võtab tagasi enne dialoogi avamist tehtud Kavitro või QGIS-i muudatused.
7. SHP-impordi edenemisaknas ära kasuta praegu katkestusnuppu ega sulgemisristi töö peatamise vahendina; oota töö lõppu ja kontrolli imporditud mälukihti.

## Seotud juhendid

- [Failide ja ühisdialoogide nupud](09_failide_ja_uhisdialoogide_nupud.md)
- [Üldnuppude ja navigeerimise detailaudit](01_01_uldnuppude_ja_navigeerimise_detailaudit.md)
- [Kinnistute nuppude detailaudit](04_01_kinnistute_nuppude_detailaudit.md)
- [Lepingute ja kooskõlastuste nuppude detailaudit](06_01_lepingute_ja_kooskolastuste_nuppude_detailaudit.md)
- [Servituutide nuppude detailaudit](07_01_servituutide_nuppude_detailaudit.md)
- [Tööde ja teostusjooniste nuppude detailaudit](08_01_toode_ja_teostusjooniste_nuppude_detailaudit.md)
- [Kavitro põhiaken, otsing ja ühised töövõtted](../17_kavitro_pohiaken_otsing_ja_uhised_toovotted.md)
