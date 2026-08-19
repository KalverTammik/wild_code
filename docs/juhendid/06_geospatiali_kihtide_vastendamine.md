# Geospatiali kihtide vastendamine

Geospatiali kihi mapper kannab olemasoleva QGIS-i lähtekihi geomeetria ja atribuudid valitud mooduli Geospatiali põhikihti. Kasutaja määrab iga sihtvälja jaoks lähtevälja või vaikeväärtuse ning kinnitab seejärel kogu lähtekihi töötlemise.

Geospatiali seadistusrežiimi sisselülitamine on kirjeldatud juhendis [QGIS-i projekti baaskihtide seadistamine](03_qgis_projekti_baaskihtide_seadistamine.md).

## Oluline enne alustamist

Mapper muudab sihtkihti kohe pärast ülekande kinnitamist. Enne suure andmemahu ülekandmist:

- tee sihtandmetest varukoopia;
- kontrolli, et valitud on õige moodul ja sihtkiht;
- kontrolli lähtekihi objektide arvu;
- veendu, et lähte- ja sihtkihi geomeetriatüübid sobivad;
- kontrolli mõlema kihi koordinaatsüsteemi;
- veendu, et välise ID väljad sisaldavad kordumatuid väärtusi;
- katseta töövoogu võimaluse korral väikese koopiaga.

Mapper töötleb kogu valitud lähtekihti, mitte ainult QGIS-is valitud objekte.

## Eeltingimused

Mapperi kasutamiseks peab:

- **QGIS projekti baaskihtide** kaardil olema aktiivne **Geospatiali abiga seadistus**;
- mooduli kaardil olema valitud kehtiv ja kirjutatav põhikiht;
- QGIS-i projektis olema kehtiv geomeetriaga lähtekiht;
- sihtkihil olema vähemalt üks kaardistatav atribuudiväli.

Mapper ei määra mooduli põhikihti ise. Vali õige sihtkiht mooduli kaardil enne mapperi avamist.

## Mapperi avamine

1. Ava Kavitro **Seaded**.
2. Veendu, et Geospatiali režiim on aktiivne.
3. Leia soovitud mooduli seadistuskaart.
4. Vali väljale **Mooduli kiht** õige Geospatiali sihtkiht.
5. Vajuta jaotises **Geospatiali kihi mapper** nuppu **Ava mapper**.
6. Kontrolli dialoogi ülaosas mooduli ja sihtkihi nime.

Kui nupp ei ole nähtav, ei ole Geospatiali režiim aktiivne. Kui sihtkiht puudub või sellel ei ole kaardistatavaid välju, kuvab Kavitro veateate ega ava vastendamistabelit.

## Lähtekihi valimine

1. Ava väli **Lähtekiht**.
2. Vali olemasolev kiht, millest soovid andmed üle kanda.
3. Kontrolli, et lähtekiht ei oleks sama kiht mis sihtkiht.
4. Oota, kuni Kavitro koostab vastendamistabeli.

Lähtekihi vahetamine koostab tabeli uuesti ja eemaldab eelmise lähtekihi jaoks tehtud käsitsi valikud.

## Vastendamistabel

Tabelis on iga sihtkihi välja kohta üks rida:

| Veerg | Tähendus |
|---|---|
| **Geospatiali väli** | Sihtkihi väli, kuhu väärtus kirjutatakse |
| **Lähteväli** | Lähtekihi väli, millest väärtus loetakse |
| **Vaikeväärtus** | Väärtus, mida kasutatakse puuduva või tühja lähteväärtuse korral |

Sisemisi välju `fid`, `id` ja `geom` mapperis ei kuvata ega vastendata.

## Automaatselt pakutavad väljavasted

Kavitro proovib valida lähtevälja automaatselt, kui:

- välja nimi on sama pärast tühikute, alakriipsude ja muude erimärkide eemaldamist;
- ühe välja normaliseeritud nimi sisaldub teises;
- lähte- ja sihtvälja tüübid sobivad.

Automaatne vaste on ainult soovitus. Kontrolli iga rida enne ülekannet, eriti sarnaste nimedega kuupäeva-, tunnuse- ja staatusevälju.

Tekstiväljale võib Kavitro pakkuda mis tahes tüüpi lähtevälja. Täisarvu-, tõeväärtuse- ja kuupäevaväljade puhul on automaatne sobitamine rangem.

## Lähtevälja käsitsi valimine

Iga sihtvälja real saad:

- valida sobiva lähtevälja;
- valida **Ära kaardista**;
- määrata valikulise vaikeväärtuse.

Kui valitud lähteväli sisaldab objektil väärtust, kasutatakse lähteväärtust. Vaikeväärtust kasutatakse ainult siis, kui lähtevälja ei ole valitud või selle konkreetse objekti väärtus on tühi.

Kui valid **Ära kaardista** ega määra vaikeväärtust, jätab mapper selle sihtvälja muutmata olemasoleval objektil ja tühjaks uuel objektil.

## Vaikeväärtuste määramine

Vaikeväärtuse sisestus sõltub sihtvälja tüübist:

- tekst- ja arvuväljal sisestatakse väärtus tekstikasti;
- tõeväärtuse väljal saab valida **True**, **False** või vaikeväärtuse puudumise;
- kuupäevaväljal märgitakse **Kasuta vaikeväärtust** ja valitakse kuupäev;
- kuupäeva-kellaaja väljal märgitakse **Kasuta vaikeväärtust** ning valitakse kuupäev ja kellaaeg.

Täisarvuväljale mittesobiva vaike- või lähteväärtuse teisendamine võib anda tühja väärtuse. Kontrolli arvuväljade väärtusi enne ja pärast ülekannet.

## Objektide lisamine ja uuendamine

Mapper töötleb lähtekihi kõiki objekte. Käitumine sõltub moodulist ja välise ID olemasolust.

| Moodul | Uuendamiseks kasutatav väline ID |
|---|---|
| Tööd | `ext_job_id` |
| Teostusjoonised | `ext_job_id` |
| Projektid | `ext_project_id` |
| Servituudid | `ext_easement_id`, selle puudumisel `ext_job_id` |
| Kinnistud, lepingud ja kooskõlastused | Automaatset välise ID põhist uuendamist ei kasutata |

Olemasolevat sihtobjekti uuendatakse ainult siis, kui nii lähte- kui sihtkihil on moodulile sobiv välise ID väli ning väärtus vastab olemasolevale sihtobjektile.

Uuendamisel:

- asendatakse objekti geomeetria, kui lähteobjektil on geomeetria;
- kirjutatakse üle kaardistatud väljad, millel on lähte- või vaikeväärtus;
- kaardistamata väljad jäetakse muutmata.

Kui sobivat välist ID-d ei leita, lisatakse uus sihtobjekt. Kinnistute, lepingute ja kooskõlastuste puhul lisatakse mapperiga uued objektid ka siis, kui mõne muu välja väärtus näib olemasolevaga kattuvat. Kontrolli nendes moodulites duplikaatide ohtu eriti hoolikalt.

## Geomeetria ja koordinaatsüsteem

Mapper kopeerib lähteobjekti geomeetria sihtobjektile. Kui lähte- ja sihtkihi koordinaatsüsteemid erinevad ning mõlemad on kehtivad, proovib Kavitro geomeetria sihtkihi koordinaatsüsteemi teisendada.

Mapper ei asenda kasutajapoolset geomeetriakontrolli. Kui kihid kasutavad erinevaid või vigaseid geomeetriatüüpe, võib objekti lisamine ebaõnnestuda või tulemus olla vigane.

## Andmete ülekandmine

1. Kontrolli lähte- ja sihtkihi nime.
2. Kontrolli kõik automaatselt pakutud väljavasted.
3. Määra vajalikud vaikeväärtused.
4. Vajuta **Kanna andmed üle**.
5. Kontrolli kinnituses lähtekihi objektide arvu.
6. Vajuta **OK** ainult siis, kui kiht ja objektide arv on õiged.
7. Oota tulemuse teadet.

Tulemuses kuvatakse:

- **Lisatud** – uued sihtobjektid;
- **Uuendatud** – välise ID järgi leitud ja muudetud sihtobjektid;
- **Muutmata** – objektid, millele ei olnud võimalik või vaja väärtust ega geomeetriat kirjutada;
- **Vead** – objektide lisamise või muudatuste salvestamise probleemid.

## Muudatuste salvestamine QGIS-is

Kui sihtkiht ei olnud enne mapperi käivitamist muutmisrežiimis, käivitab Kavitro redigeerimise ja proovib muudatused ülekande lõpus automaatselt salvestada. Salvestamise ebaõnnestumisel proovib Kavitro selle ülekande muudatused tagasi võtta.

Kui sihtkiht oli juba muutmisrežiimis, lisatakse mapperi muudatused olemasolevasse QGIS-i redigeerimisse ja neid ei salvestata automaatselt. Pärast tulemuse kontrollimist kasuta QGIS-i toimingut **Salvesta kihi muudatused** või tühista kogu redigeerimisseanss.

Seadistuste akna nupp **Hülga** ei tühista mapperiga tehtud andmemuudatusi.

## Piirangud ja ohukohad

- Vastendusvalikuid ei salvestata järgmise mapperi avamise jaoks.
- Mapper töötleb kogu lähtekihti, mitte QGIS-i valikut.
- Sama lähte- ja sihtkihi valimist ei blokeerita; ära kasuta sihtkihti iseenda lähtekihina.
- Ilma sobiva välise ID-ta lisatakse uued objektid ja korduskäivitus võib tekitada duplikaate.
- Korduvad välise ID väärtused lähtekihis võivad anda ootamatu tulemuse.
- Vea korral võivad enne vea tekkimist lisatud või uuendatud objektid olla juba sihtkihti kirjutatud.
- Mapper ei kustuta sihtobjekte, mida lähtekihis enam ei ole.
- Mapper ei kontrolli kõiki andmeallika piiranguid, kohustuslikke välju ega ärireegleid enne ülekannet.

## Levinumad olukorrad

### Mapperi jaotist ei kuvata

Aktiveeri **QGIS projekti baaskihtide** kaardil Geospatiali abiga seadistus ja vajuta **Kinnita**.

### Mapper ei avane

Vali mooduli kaardil kehtiv põhikiht. Sihtkihil peab olema vähemalt üks väli peale sisemiste `fid`, `id` ja `geom` väljade.

### Lähtekihti ei saa valida

Kontrolli, et lähtekiht oleks avatud QGIS-i projektis, kehtiv ja geomeetriaga.

### Automaatne vaste on vale

Vali vastava rea **Lähteväli** käsitsi või kasuta valikut **Ära kaardista**. Automaatne sobitamine põhineb välja nimel ja tüübil, mitte andmete sisul.

### Kõik objektid lisati uuena

Kontrolli, kas moodul toetab välise ID põhist uuendamist ning kas sobiv ID väli on olemas mõlemas kihis. Samuti kontrolli, et ID väärtused ei oleks tühjad.

### Muudatusi ei ole pärast QGIS-i sulgemist alles

Sihtkiht oli mapperi käivitamisel juba muutmisrežiimis. Salvesta kihi muudatused QGIS-is enne projekti sulgemist.

### Ülekanne lõppes vigadega

Kontrolli sihtkihi kirjutusõigust, geomeetriatüüpi, väljade tüüpe ja kohustuslikke väärtusi. Vaata sihtkiht üle ka siis, kui tulemus sisaldab vigu, sest osa objekte võis juba edukalt lisanduda.

## Kontrollnimekiri

Pärast ülekannet kontrolli, et:

- lisatud, uuendatud ja muutmata objektide arv on ootuspärane;
- objektide geomeetria paikneb õiges asukohas;
- välise ID väärtused on säilinud ja kordumatud;
- kuupäeva-, tõeväärtuse- ja arvuväljad sisaldavad õiget tüüpi väärtusi;
- vaikeväärtused rakendusid ainult puuduvatele lähteväärtustele;
- sihtkihis ei tekkinud duplikaate;
- QGIS-i aktiivse redigeerimisseansi muudatused on salvestatud;
- vajaduse korral on Kavitro mooduli põhikiht seadistustes kinnitatud.
