# Lepingute ja kooskõlastuste nuppude detailaudit

See juhend kirjeldab Visuaali lepingute ja kooskõlastuste nuppude tegelikku käitumist praeguse koodibaasi järgi. Mõlemas moodulis kasutatakse sama kirjekaarti ja samu põhitoiminguid; erinevus on peamiselt detailis kuvatavas sisus.

Staatus-, liigi- ja tunnusefiltri, filtrite värskendamise ja tühjendamise ning tähtaja kiirnuppude täpne käitumine on failis [Filtrite nuppude detailaudit](02_01_filtrite_nuppude_detailaudit.md).

## Mõju lühikaart

| Nupp või nupurühm | Peamine mõju | Kas toiming muudab püsiandmeid? |
|---|---|---|
| Filtrid ja tähtaja kiirnupud | Laadivad Kavitrost teistsuguse kirjete loendi | Ei |
| **… Detailne ülevaade** ja failinupud | Laadivad kirjelduse, tingimused ja failid ning võivad faili eelvaateks alla laadida | Kavitro andmeid ei muudeta; väliseks avamiseks luuakse kohalik ajutine fail |
| **Ava kaust**, **Ava kirje brauseris** | Avavad välise asukoha | Ei |
| **Seosta kinnistuid / Näita seotud kinnistuid kaardil** | Seoseta olekus võib pärast ülevaate kinnitamist lisada Kavitro kinnistuseoseid; seosega olekus muudab QGIS-i aktiivset kihti, objektivalikut ja kaardi ulatust | Seostamine muudab Kavitro andmeid; kaardil näitamine mitte |
| **Rohkem toiminguid** | Avab menüü | Ei |
| **Seosta kinnistuid** | Lisab Kavitros lepingule või kooskõlastusele kinnistuseoseid | Jah; selle töövooga seoseid eemaldada ei saa |

Seadistuste vaate üldine **Kinnita** ei kinnita ega võta tagasi ühtegi siin kirjeldatud kirjekaardi toimingut.

## Loendi nupud

Lepingute ja kooskõlastuste loendis on sama nupurühm:

- **Staatus**, **Liik** ja **Tunnused**;
- **Värskenda filtreid** ja **Tühjenda filtrivalikud**;
- **Kiire!** rühma üle tähtaja ja läheneva tähtaja arvunupud.

Nende moodulite eripärad on järgmised:

- tühi liigivalik eemaldab liigi tingimuse täielikult;
- tähtajavaade jätab aktiivse tunnusefiltri kehtima, kuid ei rakenda nähtavaid staatuse- ja liigivalikuid;
- tavaloendisse naasmise järel võib tähtajanupu esiletõstetud kujundus jääda nähtavale, kuigi päring kasutab juba tavapäraseid filtreid;
- tähtajanupu arv ei arvesta parajasti valitud tunnuseid ja võib seetõttu nähtava loendi arvust erineda.

## … Detailne ülevaade

Kirjekaardi alumises servas asuv `…` nupp laiendab või ahendab detaili sama kaardi sees. See ei ava eraldi dialoogi.

- Korraga hoitakse avatuna üks kirjekaardi detail; teise kaardi avamine ahendab eelmise.
- Detail luuakse alles esimesel avamisel.
- Ahendamine ei kustuta loodud detaili ning sama kaardi uuesti avamine ei lae andmeid uuesti.
- Uue kirjelduse, tingimuste või faililoendi nägemiseks tuleb kirjekaart või kogu loend uuesti laadida.

Esimesel avamisel tehakse kaks eraldi andmelaadimist:

1. detailipäring küsib lepingu puhul kirje uusima kirjelduse ning kooskõlastuse puhul uusima kirjelduse ja tingimused;
2. failipäring küsib mõlema mooduli puhul seotud failid.

Kooskõlastuse tingimused lisatakse kirjelduse järele eraldi pealkirja alla. Kirjeldus ja tingimused kuvatakse vormindatud HTML-sisuna; seal olevad veebilingid võivad avaneda väliselt. Detail on ainult lugemiseks.

### Laadimine, värskendamine ja vead

Kirjelduse, tingimuste ja failide päringud käivitatakse detaili avamise ajal kasutajaliidese lõimest. Aeglase ühenduse või suure faililoendi korral võib Visuaali aken seni mitte reageerida.

Kirjelduse ja tingimuste laadijal puudub kohalik veakäsitlus. Päringufaili, seansi või teenuse erind võib seetõttu detaili loomise katkestada ilma selle kaardi sees kuvatava kasutajasõbraliku veateateta. Faililoendi teenusepäringu viga käsitletakse eraldi ning detailis kuvatakse faili laadimise ebaõnnestumise tekst.

## Failide kokkuvõtte nupud

Failide kokkuvõte küsib Kavitrost faile kuni 50 kaupa ja lõpetab hiljemalt 200 faili juures. Lepingute ja kooskõlastuste päring ei määra failide järjestust, mistõttu ei saa viit nähtavat faili pidada kindlalt uusimateks.

Detailis kuvatakse ainult kuni viis esimest laaditud faili:

| Nupp või element | Tegelik käitumine |
|---|---|
| **Faili nimi** | Avab faili modaalse eelvaate, kui vorming ja käitusaeg seda toetavad |
| **Pildi ruudukujuline eelvaateikoon** | Laadib kuni 2 MB pisipildi ja avab vajutamisel sama pildi eelvaate nagu failinimi |
| `+N` märge | Näitab, mitu laaditud faili jäi viie nähtava rea taha; see ei ole nupp |

Lepingute ja kooskõlastuste menüüs puudub eraldi täieliku faililoendi toiming. Kuuendat ja hilisemat faili ei saa detailist valida; nende vaatamiseks tuleb avada kirje Kavitro veebirakenduses või kasutada sobiva `filesPath` väärtuse korral kaustatoimingut. Kui kirjel on üle 200 faili, ei näita ka `+N` märge teenuse tegelikku täielikku hulka.

### Faili eelvaate nupud

Eelvaade toetab pilte, teksti ja sobiva QGIS-i Qt WebEngine'i käitusaja korral PDF-e. Muude vormingute puhul kuvatakse eelvaates teade. **Ava väliselt** on kasutatav ainult siis, kui leitud laiend kuulub välise avamise lubatud tüüpide loendisse ning teenuse ja failinime laiendid nende mõlema olemasolul sobivad.

| Nupp | Tegelik käitumine |
|---|---|
| **Ava väliselt** | Kuvab vaikimisi eitava turvakinnituse ning laadib lubatud tüüpi kaugfaili alla ja avab selle vaikerakenduses alles valiku **Jah** järel |
| **Sulge** | Sulgeb eelvaate; Kavitro faili ei muudeta |

Tekstieelvaade loeb kuni 512 KB ja märgib kärbitud sisu. Pildieelvaate piir on 25 MB ning PDF-e proovitakse eelvaadata kuni 40 MB ulatuses. Faili väliselt avamisel eelvaate mahupiir ei kehti ning allalaadimine võib suure faili või aeglase ühenduse korral kasutajaliidest pikalt blokeerida. Lubatud failitüübid ja passiivse nupu kontrolljuhis on failis [Failide ja ühisdialoogide nupud](09_failide_ja_uhisdialoogide_nupud.md).

Kui QGIS-i käitusaeg ei toeta sisseehitatud PDF-vaadet, kuvatakse hoiatus enne eelvaatedialoogi loomist. Selles hoiatuses **Ava väliselt** nuppu ei ole, mistõttu tuleb PDF avada kausta või Kavitro veebivaate kaudu.

Väliseks avamiseks loodud ajutist faili pärast avamist ega eelvaate sulgemisel ei kustutata. Kood eemaldab registrist ainult failid, mis on juba muul põhjusel kettalt kadunud.

Failinime, pildikooni ja eelvaate ühine lühikaart on failis [Failide ja ühisdialoogide nupud](09_failide_ja_uhisdialoogide_nupud.md).

## Ava kaust

Nupp on aktiivne ainult siis, kui kirjekaardi loomise ajal oli kirje `filesPath` väärtus mittetühi.

- Kohalik väärtus antakse Windows Explorerile.
- `http` algusega väärtus avatakse operatsioonisüsteemi `start` käsuga.
- Tee olemasolu, ligipääsuõigust ega aadressi kehtivust enne avamist ei kontrollita.
- Avamisviga kirjutatakse logisse, kuid kasutajale õnnestumise ega vea teadet ei kuvata.

Kavitros muudetud `filesPath` väärtus ei uuenda sama kirjekaardi nupu olekut. Selleks tuleb loend uuesti laadida.

## Ava kirje brauseris

Nupp on aktiivne, kui kirjekaardil on mooduli nimi ja kirje ID. See koostab lepingu või kooskõlastuse Kavitro veebiaadressi ja avab selle süsteemi brauseris.

Puuduva baasaadressi või avamisvea korral jääb toiming vaikseks või kirjutab vea logisse. Kasutajale eraldi veateadet ei kuvata.

## Seosta kinnistuid / Näita seotud kinnistuid kaardil

Lepingute ja kooskõlastuste puhul näitab nupp ainult kirjega seotud kinnistuid. Moodulite enda QGIS-i põhikihi lepingu- või kooskõlastusobjekti see toiming ei otsi ega fokuseeri.

Nupu algolek tuletatakse kirjekaardi päringus kaasas olevast kinnistuseoste arvust:

- nulli korral kuvatakse seostamisikoon kohtspikriga **Kinnistuseos puudub – seosta kinnistuid**; klõps käivitab olemasoleva kaardivaliku ja ülevaatedialoogi;
- kui arv on suurem kui null, kuvatakse kaardiikoon kohtspikriga **Näita seotud kinnistuid kaardil**;
- pärast edukat **Seosta kinnistuid** toimingut muutub ainult sama kirjekaardi seostamisikoon kohe kaardiikooniks.

Seostamisoleku klõps ise andmeid ei muuda. Seosed salvestatakse alles ülevaatedialoogi kinnitamisel; tühistamise või vea korral nupu olek ei muutu.

Klõpsamisel laaditakse Kavitrost kirjega seotud katastritunnused uuesti. Kinnistute põhikihilt leitud objektid valitakse, kiht tehakse aktiivseks ning kaart liigub nende ulatusse. Varasemat aktiivset kihti, objektivalikut ega kaardiulatust ei taastata.

Kui kaardiikooni klõpsamisel teenus ei tagasta tunnuseid, kinnistukiht või objekt puudub või katastritunnuse väli ei sobi, ei kuvata kasutajale veel koondhoiatust. Nupp võib seega näida mittetöötavana.

## Rohkem toiminguid

Lepingu ja kooskõlastuse kirjekaardil sisaldab menüü ainult toimingut **Seosta kinnistuid**. See ei paku:

- kirje loomist ega muutmist;
- geomeetria joonistamist või muutmist;
- kooskõlastuse arhiveerimist;
- failide üleslaadimist või kustutamist.

Need muudatused tuleb teha Kavitro veebirakenduses või vastava andmekihi jaoks ettenähtud töövahendiga.

## Seosta kinnistuid

Toiming vajab kirje ID-d, seadistatud kinnistute põhikihti ja selle katastritunnuse välja.

1. Olemasolevad seosed laaditakse Kavitrost ja neid proovitakse kinnistukihil näidata.
2. Visuaali aken peidetakse või minimeeritakse ning QGIS-is aktiveeritakse ristkülikvalik.
3. Kasutaja valib ühe või mitu uut kinnistut.
4. Ülevaatedialoog näitab eraldi olemasolevaid ja uusi kinnistuid.
5. **Kinnita** lahendab uutele katastritunnustele Kavitro kinnistute ID-d ja saadab need `associate` toiminguna kirjega seostamiseks.

See on lisav, mitte asendav töövoog. Dialoog ei ole lõpliku seoseloendi redaktor: olemasolevaid seoseid ei saadeta uuesti, ei asendata ega eemaldata.

### Ülevaatedialoogi nupud

| Nupp | Tegelik käitumine |
|---|---|
| **Vali uuesti** | Sulgeb ülevaate ja käivitab uue kaardivaliku; Kavitro seoseid ei muudeta |
| **Tühista** | Sulgeb ülevaate uusi seoseid lisamata |
| **Kinnita** | Lisab teenusest leitud uued kinnistud; leidmata tunnused jäetakse välja ja loetletakse õnnestumise teates |

Ülevaate loendid on lugemiseks. Üksikut uut valikut ei saa dialoogis eemaldada; selleks tuleb kasutada **Vali uuesti** ja teha uus kaardivalik.

Kui ühelegi valitud tunnusele Kavitro kinnistu ID-d ei leita või seostamispäring tekitab erindi, võib erind väljuda nupukäsitlejast ilma kasutajasõbraliku veadialoogita. Koodis olev tavapärane ebaõnnestumise teateharu sellise erindi korral ei käivitu.

Edu korral loetakse seosed teenusest uuesti ja kaardinupp võidakse aktiivseks muuta. Kirjekaardi seotud kinnistute arv, detail ja muud kaasas olnud andmed samal ajal ei värskene; täieliku värske seisu saamiseks tuleb loend uuesti laadida.

Kaardivaliku kontroller ei käsitle objekti valimata `Esc`-klahvi, paremklõpsu ega kaarditööriista vahetamist eraldi lõpetamisena. Sellise katkestamise järel võib Visuaali aken jääda peidetuks või minimeerituks, kuni kasutaja selle uuesti ette toob.

## Auditi käigus leitud parandamist vajavad kohad

| Prioriteet | Leid | Kasutajarisk | Soovitatav parandus |
|---|---|---|---|
| Kõrge | Detaili kirjelduse, tingimuste ja failide laadimine toimub kasutajaliidese lõimes ning kirjelduse laadimise erindit ei käsitleta | Detail võib aeglase ühenduse korral akna hanguma panna või üldse avanemata jääda | Laadi detail taustatöös, kuva edenemine ning teisenda kõik vead kaardi sees nähtavaks olekuks |
| Kõrge | Detail näitab ainult viit faili, peidetud failide märge ei ole avatav ja moodulis puudub täieliku faililoendi nupp | Kuuendat ja hilisemat faili ei saa Visuaalis valida | Lisa **Näita kõiki faile** või ava moodulipõhine failidialoog lugemisrežiimis |
| Kõrge | Kinnistu-ID lahendamise või seostamise erind väljub ülevaatedialoogi kinnitusharust | Seostamine võib katkeda ilma arusaadava tulemuse ja taastamisjuhiseta | Püüa erind, säilita valik ning kuva lisatud, leidmata ja vigaste tunnuste koond |
| Keskmine | Detail luuakse üks kord ja sellel puudub värskendusnupp | Ahendamise järel uuesti avatud kirjeldus, tingimused ja failid võivad olla vananenud | Lisa detailile värskendamine või laadi andmed igal avamisel uuesti |
| Keskmine | Failipäring lõpetab 200 faili juures ja lepingute ning kooskõlastuste failidel puudub määratud sorteerimine | Nähtav `+N` ja viis faili ei pruugi kirjeldada täielikku ega uusimat seisu | Kasuta teenuse koguarvu, lisa paginatsioon ning määra `createdAt DESC` järjestus |
| Keskmine | PDF-i käitustoe puudumisel suletakse voog enne eelvaatedialoogi ning välise avamise nuppu ei pakuta | Kasutaja ei saa failirea kaudu PDF-i väliselt avada | Lisa hoiatusse **Ava väliselt** valik või ava piiratud PDF otse välises rakenduses |
| Keskmine | Väliseks avamiseks alla laaditud ajutisi faile ei kustutata | Kaugfailide koopiad kogunevad ajutisse kataloogi ja võivad jääda sinna pikaks ajaks | Kustuta fail rakenduse sulgemisel või halda seda kontrollitud vahemäluna |
| Keskmine | Kaardivaliku katkestamine objekti loomata ei taasta alati Visuaali akent | Töövoog näib hangunud või kadunud | Kuula `Esc`-i, paremklõpsu ja tööriista deaktiveerimist ning taasta aken ühes lõpetamisharus |
| Madal | Kaarditoimingu ebaõnnestumised on kasutajale vaiksed ja kohtspikker on ingliskeelne | Nupp võib näida mittetöötavana ning keelekasutus on ebaühtlane | Kuva leitud ja leidmata kinnistute koond ning kasuta tõlgitud kohtspikrit |

## Soovituslik tööjärjekord

1. Kontrolli, et kinnistute põhikiht ja katastritunnuse väli oleksid seadistatud.
2. Värskenda loend enne detaili avamist, kui kirjet muudeti äsja Kavitros.
3. Kasuta detaili kuni viie nähtava faili kiireks kontrolliks; täieliku faililoendi jaoks ava kirje brauseris.
4. **Seosta kinnistuid** töövoos käsitle olemasolevate seoste loendit taustainfona ja kontrolli hoolikalt just uusi valikuid.
5. Pärast sidumist värskenda loend ning kontrolli teenusest tagastatud kinnistute arvu.
6. Kui kaardinupp ei näita midagi, kontrolli eraldi teenuse seoseid, kinnistukihti ja katastritunnuseid.

## Seotud juhendid

- [Lepingute ja kooskõlastuste nupud](06_lepingute_ja_kooskolastuste_nupud.md)
- [Lepingute ja kooskõlastuste mooduli kasutamine](../16_lepingute_ja_kooskolastuste_mooduli_kasutamine.md)
- [Lepingute ja kooskõlastuste mooduli seadistamine](../10_lepingute_ja_kooskolastuste_seadistamine.md)
- [Filtrite nuppude detailaudit](02_01_filtrite_nuppude_detailaudit.md)
- [Loendite, filtrite ja kirjekaartide nupud](02_loendid_filtrid_ja_kirjekaardid.md)
- [Failide ja ühisdialoogide nupud](09_failide_ja_uhisdialoogide_nupud.md)
