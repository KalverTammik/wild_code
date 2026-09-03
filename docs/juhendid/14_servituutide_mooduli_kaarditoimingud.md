# Servituutide mooduli kaarditoimingud

Servituutide moodulis saab kuvada servituudi ja selle kinnistud kaardil, joonistada uue seotud ala, siduda olemasoleva polügooni, muuta geomeetriat ning koostada seotud kinnistute ja tehnovõrkude põhjal servituudiala eelvaate. Eelvaatest saab salvestada lõpliku ala, kinnistupõhised tasuandmed ja PDF-skeemi.

Seadistuste kohta vaata juhendeid [Servituutide mooduli seadistamine](08_servituutide_mooduli_seadistamine.md), [Kinnistute kihi seadistamine ja haldamine](05_kinnistute_kihi_seadistamine_ja_haldamine.md) ning [QGIS-i projekti baaskihtide seadistamine](03_qgis_projekti_baaskihtide_seadistamine.md). Põhiakna, üldotsingu ja korduvate kirjekaarditoimingute ülevaade on juhendis [Kavitro põhiaken, otsing ja ühised töövõtted](17_kavitro_pohiaken_otsing_ja_uhised_toovotted.md).

## Eeltingimused

Enne servituudi kaarditoiminguid veendu, et:

- avatud on õige QGIS-i projekt;
- Kavitro sessioon ja internetiühendus on aktiivsed;
- servituutide põhikihiks on valitud kirjutatav polügoonkiht;
- servituutide põhikihil on sobiv staatuseväli;
- kinnistute põhikiht on seadistatud ja sisaldab katastritunnuse välja;
- eelvaate jaoks vajalikud tehnovõrgu baaskihid on seadistatud ja projekti laaditud;
- sul on kihtide muutmiseks ning teenuse andmete ja failide uuendamiseks vajalikud õigused.

Servituutide põhikihi, staatuste vastenduse ja väljade kohta vaata [Servituutide mooduli seadistamine](08_servituutide_mooduli_seadistamine.md).

## Servituudikaardi põhitoimingud

Servituudikaardil võivad olla järgmised tegevused:

- **Ava kirje brauseris** avab servituudi Kavitro veebirakenduses;
- **Näita kaardil** valib seotud kinnistud ja fokuseerib servituutide põhikihil seotud ala;
- **Failid** on mõeldud servituudiga seotud failide halduse avamiseks, kuid praeguses versioonis toiming ei avane puuduva koodikäsitleja tõttu;
- **Joonista uus seotud objekt kaardile** loob uue polügooni;
- **Seo olemasolev joonis kaardilt** seob põhikihil juba oleva polügooni;
- **Muuda joonise geomeetriat kaardil** avab seotud polügooni QGIS-i redigeerimiseks;
- **Ava servituudi eelvaade** koostab kinnistute ja tehnovõrkude põhjal arvutusliku ala;
- **Seosta kinnistuid** lisab servituudile uusi kinnistuseoseid; olemasolevaid seoseid see ei eemalda.

Kaardil fokuseerimiseks otsib Kavitro servituudi põhikihilt eelkõige sama teenuse ID-ga objekti. Identiteedivälja eelistatud nimi on `ext_easement_id`; toetatud varuvälju ja Geospatiali mapperi käitumist kirjeldab juhend [Servituutide mooduli seadistamine](08_servituutide_mooduli_seadistamine.md).

## Servituudi ja kinnistute kuvamine kaardil

1. Leia nimekirjast soovitud servituut.
2. Vajuta toimingut **Näita kaardil**.
3. Kavitro valib teenusest saadud katastritunnuste järgi seotud kinnistud.
4. Seejärel otsib Kavitro servituutide põhikihilt seotud servituudiala ja fokuseerib kaardi sellele.

Kui põhikihilt ala ei leita, võivad seotud kinnistud siiski kaardile ilmuda. Kui kinnistuseoseid ei ole, saab olemasolevat õigesti seotud ala siiski fokuseerida.

## Kinnistute sidumine servituudiga

Uute kinnistuseoste lisamiseks:

1. Ava servituudi **Rohkem toiminguid**.
2. Vali **Seosta kinnistuid**.
3. Märgi kinnistute põhikihil ristkülikuga üks või mitu katastriüksust.
4. Vaata üle seniste ja valitud kinnistute loend.
5. Vajaduse korral vali kinnistud uuesti.
6. Kinnita uute seoste lisamine.

See toiming saadab ainult uued valitud kinnistud teenusesse. Dialoogis näidatud varasemaid seoseid ei asendata ega eemaldata. Toiming ei arvuta servituudiala ega kinnistupõhiseid pindala- ja tasuandmeid. Nende jaoks kasuta servituudi eelvaadet.

## Uue servituudiala joonistamine

1. Ava servituudi **Rohkem toiminguid**.
2. Vali **Joonista uus seotud objekt kaardile**.
3. Kavitro teeb servituutide põhikihi aktiivseks ja käivitab QGIS-i polügooni lisamise.
4. Joonista ala ning lõpeta polügoon.
5. Täida dialoog **Servituudi ala andmed**.
6. Vajuta **Salvesta**.
7. Kavitro seob objekti servituudiga, täidab sobivad kihiväljad ja proovib saata geomeetria Kavitro teenusesse.

Kui kiht ei sisalda välju `ext_easement_id`, `ext_system` või `ext_easement_number`, proovib Kavitro need automaatselt lisada.

### Servituudi ala andmete vorm

Vormil on kaks vahekaarti.

**Andmed** sisaldab välju:

- liik;
- staatus;
- notari registrinumber;
- maa omanik;
- katastritunnus;
- telefon ja e-post;
- kehtestamise kuupäev;
- allikas;
- võrk;
- kaitsevööndi laius;
- talumistasu;
- märkus.

**Asukoht** sisaldab välju:

- vald;
- piirkond;
- aadress;
- maja number;
- märge **Talumistasu arvestatakse**.

Kavitro kirjutab väärtuse ainult kihil olemasolevasse sobiva nimega välja. Tühja vormiväärtusega olemasolevat kihivälja üle ei kirjutata. Staatus täidetakse esmalt teenuse staatuse ja seadistatud staatusevastenduse järgi, kuid vormil valitud mittetühi staatus kirjutab selle väärtuse üle.

Kehtestamise kuupäev saadetakse vormist ainult siis, kui staatus on täpselt **Kehtestatud** või vorm avati juba olemasoleva kehtestamise kuupäevaga.

### Praeguse versiooni piirang

Vormi märge **Talumistasu arvestatakse** kogutakse vormilt, kuid servituutide põhikihi salvestusloogika ei kirjuta seda praegu ühelegi kihiväljale. Kinnistupõhine tasulisuse märge salvestatakse eraldi servituudi eelvaate kinnistuandmete osas.

### Muutmisrežiimi mõju

- Kui Kavitro alustas kihi muutmisrežiimi, kinnitab ta eduka joonistamise järel muudatused ise.
- Kui vorm katkestatakse või sidumine ebaõnnestub, pöörab Kavitro enda alustatud muutmisseansi tagasi.
- Kui kiht oli juba enne toimingut muutmisrežiimis, jääb uus objekt muutmispuhvrisse ja kasutaja peab muudatused ise salvestama või tühistama.

## Olemasoleva polügooni sidumine

Kasuta seda toimingut, kui servituudiala on põhikihil juba olemas, kuid pole Kavitro servituudiga seotud.

1. Ava servituudi **Rohkem toiminguid**.
2. Vali **Seo olemasolev joonis kaardilt**.
3. Kliki otse servituutide põhikihi soovitud polügoonile.
4. Täida dialoog **Servituudi ala andmed**.
5. Kinnita salvestamine.
6. Kavitro kirjutab teenuse ID, numbri, liigi, staatuse, süsteemi, vormiandmed ja logiväljad ning saadab polügooni geomeetria teenusesse.

Parema hiireklõpsu või klahviga `Esc` saab kaardivaliku katkestada. Kui klõps ei taba polügooni, jääb valikurežiim aktiivseks ja saad uuesti proovida.

### Kui polügoon on juba seotud

Kui klikitud objektil on teise servituudi ID, on uus sidumine blokeeritud. Kavitro pakub kolme valikut:

- **Kustuta objekt** eemaldab polügooni servituutide QGIS-i kihilt;
- **Arhiveeri objekt** jätab polügooni alles ja määrab selle staatuseks `(puudub)`;
- **Loobu** ei muuda objekti.

Kustutamine ja arhiveerimine lõpetavad käimasoleva sidumistoimingu. Uue objekti sidumiseks tuleb käsk uuesti käivitada.

**Oluline:** need valikud muudavad ainult QGIS-i servituudikihti. Need ei kustuta ega arhiveeri Kavitro teenuse servituudikirjet. Arhiveerimine ei eemalda objektilt varasemat välist ID-d, mistõttu jääb objekt endiselt vana teenusekirjega seotuks.

Kustutamine on pöördumatu kohe siis, kui Kavitro käivitas muutmisrežiimi ja kinnitas muudatuse. Kui kiht oli juba muutmisrežiimis, jääb kustutamine või arhiveerimine ootele.

## Geomeetria muutmine

1. Ava servituudi **Rohkem toiminguid**.
2. Vali **Muuda joonise geomeetriat kaardil**.
3. Kavitro otsib ID või numbri järgi seotud objekti, teeb kihi aktiivseks ja valib objekti.
4. QGIS käivitab eelistatult tippude tööriista, vajaduse korral objekti liigutamise tööriista.
5. Muuda geomeetriat.
6. Salvesta või tühista kihi muudatused QGIS-i tavapäraste vahenditega.

### Praeguse versiooni piirang

Geomeetria muutmise toiming ainult avab QGIS-i redigeerimise. See ei jälgi muudatuse lõpetamist, ei salvesta kihti automaatselt ega saada muudetud geomeetriat Kavitro teenusesse.

Kui teenuse geomeetria peab samuti muutuma, kasuta organisatsioonis kokkulepitud eraldi sünkroonimisviisi. Ära eelda, et QGIS-i kihi salvestamine uuendab teenust.

## Servituudiala eelvaate avamine

Eelvaade kasutab servituudiga seotud kinnistuid ning järgmisi QGIS-i baaskihte:

- veetorud;
- isevoolsed kanalisatsioonitorud;
- survekanalisatsioonitorud;
- sademeveetorud;
- reoveepumplad;
- purgimissõlmed;
- reoveepuhastid;
- veejaamad;
- sademeveepumplad.

1. Ava servituudi **Rohkem toiminguid**.
2. Vali **Ava servituudi eelvaade**.
3. Dialoog laeb teenusest servituudi kinnistuseosed.
4. Kavitro valib seotud kinnistud kaardil ja teeb neist ajutise puhverala.
5. Kavitro valib baaskihtidelt puhveralaga ristuvad tehnovõrgu objektid.
6. Iga leitud objektirühma ümber luuakse eraldi ajutine eelvaatepuhver.
7. Kontrolli iga kihi real seadistatud kihi nime, valitud objektide arvu ja kasutatud kaugust.

Seadistamata baaskiht jäetakse vahele. Samuti jäetakse vahele kiht, millelt ristuvaid objekte ei leitud.

## Puhvri kauguse automaatika

Dialoogi üldine **Puhvri kaugus** on vaikimisi 2 m ja seda saab muuta vahemikus 0,1–500 m. Kavitro kasutab üldist väärtust siis, kui konkreetse objektitüübi reegli jaoks pole piisavalt lähteandmeid.

Automaatreeglid on järgmised:

| Objekt | Reegel |
|---|---|
| Purgimissõlm, reoveepuhasti, veejaam | 30 m |
| Reovee- ja sademeveepumpla | vooluhulk üle 10 → 20 m, muul juhul 10 m |
| Survetoru, läbimõõt alla 250 mm | 2 m |
| Survetoru, läbimõõt 250–499 mm | 2,5 m |
| Survetoru, läbimõõt vähemalt 500 mm | 3 m |
| Muu toru, läbimõõt alla 250 mm | sügavus kuni 2 m → 2 m, muidu 2,5 m |
| Muu toru, läbimõõt 250–999 mm | sügavus kuni 2 m → 2,5 m, muidu 3 m |
| Muu toru, läbimõõt vähemalt 1000 mm | sügavus kuni 2 m → 2,5 m, muidu 5 m |

Reeglid otsivad lähtekihilt eri nimekujudega läbimõõdu, sügavuse ja vooluhulga välju. Mitme valitud objekti korral kasutatakse vastava kihi suurimat arvutatud kaugust. Kui vajalikku välja või väärtust ei leita, kasutatakse üldist puhvri kaugust.

Puhvriarvutus saab kauguse otse lähtekihi koordinaatsüsteemi ühikutes, kuigi väljal kuvatakse `m`. Meetri tähis on seetõttu õige ainult meetrites töötava lähtekihi korral.

Valik **Ümardatud nurgad** muudab praeguses koodis puhvri otsakuju parameetrit, kuid nurgastiil jääb alati ümardatuks. Joone otstes võib valik mõju avaldada, kuid polügooni nurkade puhul ei pruugi nähtavat erinevust tekkida. Puhvri või valiku muutmisel käivitatakse eelvaate automaatika uuesti.

## Kinnistute määramine eelvaates

Nupp **Määra kinnistud kaardilt** on nähtav ainult siis, kui servituudil ei ole veel ühtegi kinnistuseost. Selle kaudu saab lisada esimesed kinnistud eelvaate redaktorisse:

1. Vajuta **Määra kinnistud kaardilt**.
2. Vali kinnistute põhikihilt ristkülikuga üks või mitu katastriüksust.
3. Vaata senised ja uued kinnistud üle.
4. Kinnita valik.

Valitud kinnistud lisatakse esmalt eelvaate kinnisturedaktorisse. Teenuse seosed salvestatakse alles nupuga **Salvesta servituudi kinnistuandmed**. Kui servituudil on juba vähemalt üks seos, peidetakse nupp ning eelvaatest ei saa olemasolevaid seoseid eemaldada ega uusi juurde valida; uute seoste lisamiseks kasuta kirjekaardi **Seosta kinnistuid** toimingut.

## Lõpliku lõike loomine

1. Kontrolli, et automaatika oleks leidnud vajalikud tehnovõrgu objektid.
2. Vajuta **Loo lõplik lõige**.
3. Kavitro lõikab iga tehnovõrgu puhverala valitud kinnistute piiridega.
4. Lõiked liidetakse ja ühendatakse üheks lõplikuks servituudiala eelvaateks.
5. Kavitro arvutab kogu lõike pindala ja iga kinnistu sisse jääva pindala.

**Loo lõplik lõige** loob ainult ajutise mälukihi. See ei salvesta veel servituutide põhikihti ega teenuse geomeetriat.

Kui tehnovõrkude puhvrid valitud kinnistutega ei lõiku, lõplikku ala ei looda. Kontrolli kinnistuid, lähtekihtide valikuid, geomeetriaid ja puhvri kaugusi.

## Kinnistupõhised pindala- ja tasuandmed

Iga seotud kinnistu real saab üle vaadata või määrata:

- arvutatud pindala;
- pindala ühiku `m²` või `ha`;
- hinna pindalaühiku kohta;
- valuuta, vaikimisi `EUR`;
- tasulisuse;
- järgmise makse kuupäeva.

Kogusumma arvutatakse siis, kui nii pindala kui ka ühikuhind on suuremad kui null. Järgmise makse kuupäev peab olema ISO-kujul `AAAA-KK-PP`.

## Kinnistuandmete ja lõpliku ala salvestamine

Nupp **Salvesta servituudi kinnistuandmed** käivitab mitu järjestikust toimingut:

1. Kavitro lahendab uute katastritunnuste teenuse kinnistu-ID-d.
2. Teenusesse salvestatakse servituudi kinnistuseosed koos pindala-, hinna-, valuuta-, tasulisuse ja maksekuupäeva andmetega.
3. Kavitro loob vajaduse korral lõpliku lõike.
4. Avaneb vorm **Servituudi ala andmed**.
5. Lõplik geomeetria lisatakse servituutide põhikihti või sama servituudi olemasolev objekt uuendatakse.
6. Kavitro proovib saata salvestatud geomeetria Kavitro teenusesse.

Pindalaandmete kindlaks salvestamiseks vajuta enne **Loo lõplik lõige**. Kui lõplikku lõiget ei olnud varem loodud, kogub salvestusnupp teenusesse saadetavad kinnistuandmed enne lõike automaatset loomist ning arvutatud pindala võib seetõttu sellest salvestuskorrast välja jääda.

Põhikihti salvestatakse võimaluse korral teenuse ID ja number, liik, vastendatud staatus, süsteem, esimene katastritunnus, lõpliku ala pindala, kinnistute kogutalumistasu, vormiandmed ja logiväljad.

### Osalise õnnestumise võimalus

Kinnistuandmed salvestatakse teenusesse enne QGIS-i põhikihi ja geomeetria sünkroonimist. Kui hilisem kihi salvestamine, vormi kinnitamine või geomeetria saatmine ebaõnnestub, võivad kinnistuseosed ja tasuandmed olla teenuses juba uuendatud.

Samuti võib QGIS-i objekt olla edukalt salvestatud, kuid geomeetria saatmine teenusesse ebaõnnestuda. Veateate korral kontrolli eraldi:

- teenuse kinnistuseoseid ja tasuandmeid;
- servituutide QGIS-i põhikihti;
- teenuse geomeetriat.

Kui põhikiht oli enne toimingut juba muutmisrežiimis, jääb kihi muudatus ootele. Teenuse kinnistuandmed ja geomeetria võivad samal ajal olla juba uuendatud.

## PDF-skeemi eelvaade ja avaldamine

### Eelvaade

1. Vajuta **Eelvaata PDF skeemi**.
2. Kavitro loob vajaduse korral lõpliku lõike.
3. PDF koostatakse plugina mallist ning sinna lisatakse kaart, legend, kogupindala, mõõtkava, kinnistu kokkuvõte ja servituudi number.
4. PDF avatakse plugina failieelvaates.

### Avaldamine

1. Vajuta **Avalda PDF skeem**.
2. Kavitro genereerib skeemi uuesti praeguse kaardiseisu põhjal.
3. Fail laaditakse servituudi failina Kavitro teenusesse.
4. Kontrolli õnnestumise teadet ja vajaduse korral servituudi failide loendit.

PDF-kaart kasutab praegu kaardil nähtavaid kihte ning lisab kinnistu- ja lõpliku servituudiala kihi. Enne avaldamist kontrolli kihtide nähtavust, stiile ja kaardi sisu. PDF-i numbrivälja pealkiri on praeguses mallitäites ekslikult **Lepingu nr**, kuigi väärtus on servituudi number.

Genereeritud kohalik PDF on ajutine ning eemaldatakse järgmise genereerimise või eelvaatedialoogi sulgemise käigus. Avaldatud teenusefail jääb alles.

## Servituudi failid

Servituudi failihalduse dialoog on koodis olemas ja selles saab:

- seotud failide loendit värskendada;
- toetatud faili plugina sees eelvaadata;
- faile üles laadida;
- lubatud tüüpi valitud faili pärast turvakinnitust väliselt avada;
- faili pärast kinnitust kustutada.

Praeguses versioonis ei ava **Rohkem toiminguid → Failid** seda dialoogi, sest nupu käsitleja puudub. Kasuta seni **Ava kirje brauseris** ja halda faile Kavitro veebirakenduses.

PDF-eelvaate tugi sõltub QGIS-i Qt/PyQt ja WebEngine'i versioonist. Kui tugi puudub, katkestatakse eelvaate avamine enne **Ava väliselt** nupuga dialoogi loomist. Eelvaates genereeritud PDF-i saab sellest hoolimata nupuga **Avalda PDF skeem** Kavitrosse laadida ja seejärel veebirakendusest avada.

Faili kustutamine muudab teenuse andmeid kohe ja seda ei saa QGIS-i kihi muudatuste tühistamisega tagasi võtta.

## Eelvaate puhastamine ja sulgemine

- **Puhasta eelvaated** eemaldab servituudi ajutised mälukihid.
- Dialoogi sulgemine eemaldab eelvaatekihid, ajutise PDF-i ja automaatsed kaardivalikud.
- Puhastamine ei kustuta põhikihile juba salvestatud servituudiala.
- Puhastamine ei tühista teenusesse salvestatud kinnistuseoseid, tasuandmeid, geomeetriat ega avaldatud PDF-i.

## Levinumad olukorrad

### Servituut ei ilmu kaardile

Kontrolli põhikihti ja objekti välist ID-d. Kui objektil on ainult number, peab see samuti vastama teenuse servituudi numbrile.

### Olemasoleva objekti klikk ei tööta

Kliki otse polügooni täitealale. Kontrolli, et seadistatud põhikiht oleks projektis laaditud ja polügoontüüpi.

### Uue objekti vormi katkestamisel jäi objekt kihile

Kiht oli enne toimingut juba muutmisrežiimis. Uus objekt võib olla QGIS-i muutmispuhvris; tühista või salvesta kihi muudatused käsitsi.

### Eelvaade jätab tehnovõrgukihi vahele

Kiht on seadistamata, projektist puudu või kinnistu puhveralaga ei leitud ristuvaid objekte. Vaata kihi real kuvatavat automaatika teadet.

### Puhvri kauguse muutmine ei mõjuta mõnda rida

Sellele objektitüübile rakendub fikseeritud või atribuutidest arvutatud kaugus. Üldväärtust kasutatakse ainult siis, kui erireegli lähteandmeid ei ole.

### Lõplikku lõiget ei teki

Ükski tehnovõrgu puhver ei lõiku valitud kinnistutega. Kontrolli kinnistuseoseid, geomeetriaid, baaskihte ja kasutatud vahemaid.

### Kinnistuandmed salvestusid, kuid ala mitte

See on võimalik, sest teenuse kinnistuandmed salvestatakse enne põhikihi toimingut. Paranda põhikihi või vormi probleem ja käivita salvestamine uuesti.

### Geomeetria muutus QGIS-is, kuid mitte teenuses

Käsitsi geomeetria muutmise käsk ei sünkrooni tulemust. Kasuta eraldi kokkulepitud sünkroonimisviisi.

### PDF ei avane plugina sees

QGIS-i käitusaeg ei pruugi toetada sisseehitatud PDF-eelvaadet. Praegune hoiatus ei paku selles olukorras välise avamise nuppu. Avalda skeem Kavitrosse ja ava see veebirakendusest või kasuta uuemat sobiva WebEngine'i toega QGIS-i versiooni.

## Kontrollnimekiri

Pärast servituuditoimingu lõpetamist kontrolli, et:

- õiged kinnistud on servituudiga seotud;
- põhikihi objektil on õige `ext_easement_id`;
- staatuse väärtus vastab kihi kokkuleppele;
- geomeetria asub õiges kohas ja on kehtiv;
- QGIS-i kihil ei ole ootamatuid ootel muudatusi;
- teenuse kinnistu-, tasu- ja geomeetriaandmed vastavad QGIS-i tulemusele;
- lõpliku lõike pindalad on mõistlikud;
- PDF-skeemi kihid, stiilid ja ulatus on enne avaldamist üle vaadatud;
- konflikti korral ei kustutatud ekslikult vajalikku QGIS-i objekti.
