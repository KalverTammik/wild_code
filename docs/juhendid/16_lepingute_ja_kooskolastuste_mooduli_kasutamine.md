# Lepingute ja kooskõlastuste mooduli kasutamine

Lepingute ja kooskõlastuste moodulid koondavad Kavitro kirjed loendisse, aitavad jälgida tähtaegu ning võimaldavad avada kirje detailid, seotud failid, kinnistud ja Kavitro veebivaate. Mõlema mooduli kasutusloogika on suuresti sama.

Seadistuste kohta vaata juhendit [Lepingute ja kooskõlastuste seadistamine](10_lepingute_ja_kooskolastuste_seadistamine.md). Kogu Visuaali akna, üldotsingu ja ühiste toimingute ülevaade on juhendis [Kavitro põhiaken, otsing ja ühised töövõtted](17_kavitro_pohiaken_otsing_ja_uhised_toovotted.md).

## Moodulite erinevused

| Funktsioon | Lepingud | Kooskõlastused |
|---|---|---|
| Staatus-, liigi- ja tunnusefilter | Jah | Jah |
| Tähtaja kiirfiltrid | Jah | Jah |
| Detailvaate kirjeldus | Lepingu kirjeldus | Kirjeldus ja tingimused |
| Seotud failide kokkuvõte | Jah | Jah |
| Seotud kinnistute kuvamine ja uute seoste lisamine | Jah | Jah |
| Kirje loomine või muutmine Visuaalis | Ei | Ei |

Kooskõlastuste seadistustes valitav arhiivikiht ei lisa moodulisse arhiveerimise toimingut ega liiguta kirjeid automaatselt kihtide vahel.

## Eeltingimused

Enne mooduli kasutamist veendu, et:

- Kavitro sessioon ja internetiühendus on aktiivsed;
- moodul on sinu kasutajakontole lubatud;
- QGIS-is on avatud õige projekt;
- kinnistute põhikiht on seadistatud ja projekti laaditud;
- mooduli kohustuslikud seadistused on salvestatud;
- kausta avamiseks on kirjel `filesPath` väärtus ja sul on asukohale juurdepääs.

Põhikihi, filtrieelistuste ja kooskõlastuste arhiivikihi valimist kirjeldab juhend [Lepingute ja kooskõlastuste seadistamine](10_lepingute_ja_kooskolastuste_seadistamine.md).

## Kirjete loendi avamine

1. Ava Visuaali külgribalt **Lepingud** või **Kooskõlastused**.
2. Oota, kuni laadimine lõpeb.
3. Keri loendit, et vaadata järgmisi kirjeid. Järgmine andmeplokk laaditakse vastavalt vajadusele.
4. Kui soovitud kirjet ei ole näha, kontrolli aktiivseid filtreid.

Mooduli esmakordsel avamisel rakendatakse seadistustes määratud eelistatud staatused, liigid ja tunnused. Need on algvalikud, mitte kasutaja õigusi või teenuse andmeid muutvad piirangud.

## Kirjete filtreerimine

Loendi kohal saab kasutada järgmisi filtreid:

- **Staatus** piirab loendi valitud staatustega;
- **Liik** piirab loendi valitud lepingute või kooskõlastuste liikidega;
- **Tunnused** piirab loendi valitud Kavitro tunnustega.

Filtri muutmisel laaditakse loend uuesti. Filtrite värskendamise nupu kaudu saab taastada või uuesti rakendada mooduli filtrid. Kui loend on ootamatult tühi, eemalda esmalt filtrivalikud või värskenda filtrid ning oota uue päringu lõppemist.

## Tähtaja kiirfiltrid

Mooduli päises olevad arvuga nupud annavad kiire ülevaate tähtaja seisust:

- **Üle tähtaja** kuvab kirjed, mille tähtaeg on varasem kui tänane kuupäev;
- **Tähtaeg läheneb** kuvab kirjed, mille tähtaeg jääb tänasest kuni kolme päeva kaugusele, mõlemad piirkuupäevad kaasa arvatud.

Nupul olev arv näitab vastava rühma kirjete arvu. Vajutatud tähtajanupp muutub aktiivseks ja loend laaditakse tähtajatingimusega uuesti.

Tähtaja kiirfilter on eraldi kuupäevavaade. See ei säilita automaatselt kõiki staatuse- ja liigifiltri tingimusi; aktiivne tunnusefilter võetakse kaasa. Tavaloendisse naasmiseks muuda mõnda tavapärast filtrit või kasuta filtrite värskendamist.

## Kirje avamine üldotsingust

Lepingut ja kooskõlastust saab avada ka Visuaali üldotsingu kaudu.

1. Sisesta põhiakna otsinguväljale vähemalt kolm märki.
2. Vali tulemuste hulgast leping või kooskõlastus.
3. Visuaal avab vastava mooduli ja laadib valitud kirje üksikvaatesse.
4. Täieliku loendi taastamiseks vajuta filtrite värskendamise või tühjendamise nuppu või muuda mõnda filtrit.

Kui üldotsing leiab tulemuse, kuid selle valimine ei ava kirjet, kontrolli, et moodul oleks sinu kontole lubatud ja sessioon kehtiks.

## Kirjekaardi sisu

Kirjekaardil kuvatav teave sõltub teenusest saadud andmetest. Tavaliselt on näha:

- kirje nimi või number;
- staatus ja liik;
- algus- ja tähtajakuupäev;
- vastutaja või osapooled;
- tunnused;
- seotud kinnistute arv;
- kirje toimingud.

Puuduv väli tähendab üldjuhul seda, et väärtust ei ole Kavitros täidetud või seda ei tagastatud kasutaja õiguste piires.

## Detailvaade ja seotud failid

Kirjekaardi `…` nupu vajutamisel laiendatakse detailne ülevaade sama kaardi sees. Teise kaardi detaili avamine ahendab varem avatud kaardi. Detailis kuvatakse:

- lepingu puhul kirjeldus;
- kooskõlastuse puhul kirjeldus ja eraldi tingimused;
- mõlema mooduli puhul seotud failide kokkuvõte.

Failide kokkuvõttes kuvatakse kuni viis teenusest esimesena tagastatud faili ja vajaduse korral märge ülejäänud laaditud failide arvu kohta. Märge ei ole nupp ning sellest ei saa peidetud faile avada. Faili vajutamisel avaneb eelvaade, kui failivorming, QGIS-i käitusaeg ja juurdepääs seda võimaldavad. Eelvaatest saab faili vajaduse korral välise rakendusega avada. Ülejäänud failide vaatamiseks kasuta **Ava kirje brauseris** toimingut.

Detail luuakse kaardi esimesel avamisel ja sama kaardi ahendamisel ei kustutata. Kavitros vahepeal muudetud kirjelduse, tingimuste või failide laadimiseks värskenda kogu mooduli loendit.

See detailvaade on lugemiseks. Lepingute ja kooskõlastuste moodul ei paku failide üleslaadimise, kustutamise ega täieliku failihalduse toimingut.

## Kirjekaardi toimingud

### Ava kaust

Toiming avab kirje `filesPath` väljal oleva kohaliku kausta või veebiaadressi. Nupp on passiivne, kui asukohta ei ole määratud.

Kui kohalik kaust ei avane, kontrolli, et tee oleks sinu arvutist või võrgust ligipääsetav. Veebiaadressi korral kontrolli brauserit ja internetiühendust.

### Ava kirje brauseris

Toiming avab sama lepingu või kooskõlastuse Kavitro veebirakenduses. Kasuta veebivaadet kirje loomiseks, muutmiseks või toiminguteks, mida Visuaal ei paku.

### Näita kaardil

Lepingute ja kooskõlastuste puhul näitab toiming kaardil kirjega seotud kinnistuid.

1. Vajuta kirjekaardil **Näita kaardil**.
2. Visuaal küsib teenusest kirjega seotud kinnistud.
3. Vastavad katastriüksused valitakse kinnistute põhikihil ja kaart liigub nende ulatusse.

Lepingute ja kooskõlastuste põhikihi üksikobjekti praegune versioon selle toiminguga ei fokuseeri. Kui kirjel pole kinnistuseoseid ja moodul ei toeta põhikihi fookust, võib nupp olla passiivne.

### Rohkem toiminguid

Lepingute ja kooskõlastuste menüüs on kasutatav toiming **Seosta kinnistuid**. Visuaal ei paku nende moodulite menüüs uue kirje loomist, geomeetria joonistamist ega arhiveerimist.

## Kinnistute sidumine

1. Ava kirje **Rohkem toiminguid**.
2. Vali **Seosta kinnistuid**.
3. Märgi kinnistute põhikihil ristkülikuga üks või mitu katastriüksust.
4. Vaata üle dialoogis kuvatud olemasolevad ja uued kinnistud.
5. Vajaduse korral vali kinnistud uuesti.
6. Kinnita uute seoste lisamine.

Visuaal lahendab valitud katastritunnustele Kavitro kinnistute ID-d ning saadab leitud kinnistud lisatavate seostena teenusesse. Olemasolevad seosed kuvatakse taustainfona: neid ei saadeta lõpliku loendina, neid ei asendata ega saa selles töövoos eemaldada.

Kui mõnele katastritunnusele Kavitro kinnistut ei leita, kuvatakse see tulemuses eraldi. Kontrolli siis kinnistute põhikihi katastritunnuse välja ning kinnistu olemasolu Kavitros.

## Kirje muutmine

Lepingu või kooskõlastuse nime, staatuse, tähtaja, kirjelduse, tingimuste ja failide muutmine toimub Kavitro veebirakenduses.

1. Ava kirjekaardilt **Ava kirje brauseris**.
2. Tee muudatus Kavitros ja salvesta.
3. Naase Visuaali.
4. Värskenda mooduli loend või ava kirje uuesti.

## Levinumad olukorrad

### Moodul suunab seadistustesse

Kontrolli mooduli põhikihi ja muude kohustuslike seadete valikut. Salvesta seadistus ning ava moodul uuesti.

### Eelistatud kirjet ei ole loendis

Eemalda staatus-, liigi- ja tunnusefiltrid. Kontrolli ka, kas aktiivne on tähtaja kiirfilter, ning värskenda loendit.

### Tähtaja arv ja nähtav loend erinevad

Tähtaja arv loetakse tähtajatingimuse järgi kogu mooduli kohta. Tavaloendis võivad samal ajal olla aktiivsed muud filtrid. Vajuta soovitud tähtajanuppu, et laadida vastav kuupäevavaade.

### Faili eelvaade ei avane

Fail võib puududa, kasutajal ei pruugi olla juurdepääsu või vorming ei pruugi sisemist eelvaadet toetada. Proovi faili avada välise rakendusega või kontrolli seda Kavitro veebivaates.

### „Näita kaardil“ ei leia kinnistuid

Kontrolli kinnistute põhikihi seadistust, katastritunnuse välja, kihi laadimist ja kirje kinnistuseoseid. Lepingute või kooskõlastuste põhikihi olemasolu üksi ei anna sellele toimingule üksikobjekti fookust.

### Lisatud seosed ei kajastu kohe

Sulge detailvaade ja laadi mooduli loend uuesti. Vajaduse korral ava kirje Kavitros ning kontrolli, kas seosed salvestusid teenuses.

## Kontrollnimekiri

- [ ] Õige QGIS-i projekt on avatud.
- [ ] Kavitro sessioon ja internetiühendus töötavad.
- [ ] Lepingute või kooskõlastuste moodul on kasutajale lubatud.
- [ ] Mooduli kohustuslikud seadistused on salvestatud.
- [ ] Kinnistute põhikiht on seadistatud ja laaditud.
- [ ] Ootamatult tühja loendi korral on filtrid ja tähtajavaade kontrollitud.
- [ ] Kaardi kuvamiseks on kirjel kinnistuseosed.
- [ ] Seoste kinnitamise eel on uued lisatavad kinnistud üle vaadatud.
- [ ] Kirje sisulised muudatused tehakse Kavitro veebirakenduses.
