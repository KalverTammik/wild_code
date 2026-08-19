# QGIS-i projekti baaskihtide seadistamine

Kavitro kasutab QGIS-i projekti baaskihte vee-, kanalisatsiooni- ja muude tehnovõrkude kuvamiseks ning kaarditoimingutes õigete kihtide leidmiseks. Baaskihid saab määrata käsitsi, lasta Kavitrol tuvastada EVEL-i kihistuse või kasutada Geospatiali abiga seadistusrežiimi.

See juhend kirjeldab ka ühise kanalisatsioonikihi tüüpide vastendamist. Seadistuste mooduli üldine kasutamine, salvestamine ja lähtestamine on kirjeldatud juhendis [Kavitro seadistuste mooduli kasutamine](01_seadistuste_mooduli_kasutamine.md).

## Eeltingimused

Enne baaskihtide seadistamist veendu, et:

- avatud on õige QGIS-i projekt;
- vajalikud kihid on projekti laaditud;
- kihid on kehtivad ruumikihid;
- tead, kas kanalisatsiooniliigid asuvad eraldi kihtidel või ühes ühises kihis;
- EVEL-i automaattuvastuse kasutamisel järgivad kihtide nimed EVEL-i või varem toetatud Kavitro kihistust.

Baaskihtide valik salvestatakse avatud QGIS-i projekti. Teise projekti avamisel kasutatakse selle projekti enda baaskihtide seadistust.

## Baaskihtide kaardi avamine

1. Ava QGIS-is Kavitro plugina aken.
2. Vali külgribalt **Seaded**.
3. Leia kaart **QGIS projekti baaskihid**.
4. Kontrolli kaardi ülaosas kuvatavat seadistusrežiimi.

Kasutada saab kahte põhirežiimi:

- **Käsitsi seadistus** – kihid valitakse käsitsi või tuvastatakse EVEL-i kihistuse järgi;
- **Geospatiali abiga seadistus** – käsitsi baaskihiväljad peidetakse ja moodulikaartidel muutub kättesaadavaks Geospatiali andmete vastendamise tööriist.

## Seadistatavad baaskihid

Kaardil saab määrata järgmised QGIS-i kihid:

| Väli | Sisu |
|---|---|
| **Veetorud** | Veevõrgu torustikud |
| **Kanalisatsioonitorud** | Isevoolne või ühine kanalisatsioonitorustike kiht |
| **Survekanalisatsioonitorud** | Survekanalisatsiooni torustikud |
| **Sademeveetorud** | Sademevee torustikud |
| **Reoveepumpla** | Reovee- ja kanalisatsioonipumplad |
| **Purgimissõlm** | Purgimissõlmed |
| **Reoveepuhasti** | Reoveepuhastid |
| **Veejaam** | Veejaamad ja veepumplad |
| **Sademeveepumpla** | Sademeveepumplad |

Kõiki välju ei pea täitma, kui vastavat andmeliiki projektis ei kasutata. Kavitro saab kasutada ainult neid baaskihte, mis on seadistatud ja projektis olemas.

## Baaskihtide käsitsi määramine

Käsitsi seadistamine sobib juhul, kui kihid ei järgi EVEL-i nimetusi või soovid iga kihi ise määrata.

1. Veendu, et kaardi ülaosas on aktiivne **Käsitsi seadistus**.
2. Veendu, et märge **Mul on EVEL kihistus juba seadistatud** ei ole valitud.
3. Ava soovitud baaskihi valik.
4. Vali QGIS-i projektist õige kiht.
5. Korda sama kõigi kasutatavate baaskihtide jaoks.
6. Kontrolli kaardi all kuvatavat kihtide kokkuvõtet.
7. Vajuta seadistuste akna all nuppu **Kinnita**.

Kihtide valikutes kuvatakse QGIS-i projektis olevad geomeetriaga kihid. Kui vajalikku kihti valikus ei ole, kontrolli, et kiht oleks projekti laaditud ja kehtiv.

## EVEL-i kihistuse automaatne tuvastamine

EVEL-i automaattuvastus sobib projektile, kus tehnovõrkude kihid kasutavad EVEL-i või Kavitro toetatud varasemaid kihtide nimetusi.

1. Märgi **Mul on EVEL kihistus juba seadistatud**.
2. Kavitro otsib projektist tuntud nimedega kihte.
3. Kontrolli kaardi kokkuvõttest, millised kihid leiti.
4. Seadista vajaduse korral ühise kanalisatsioonikihi tüübi väli ja ID-kaardistus.
5. Vajuta **Kinnita**.

Automaattuvastus otsib muu hulgas selliseid nimesid nagu `veetorud`, `TVV_veetorud`, `kanalisatsioonitorud`, `TVV_kanalisatsioonitorud`, `survekanalisatsioonitorud`, `sademeveetorud`, `reoveepumpla`, `purgimissõlm`, `reoveepuhasti`, `veejaam` ja `sademeveepumpla`.

Kui automaattuvastus on sisse lülitatud, ei saa kihte rippmenüüdest käsitsi muuta. Puuduvate või valesti tuvastatud kihtide korral eemalda EVEL-i märge ja kasuta käsitsi seadistamist.

EVEL-i režiim võib survekanalisatsiooni ja sademevee jaoks kasutada sama kanalisatsioonikihti. Sellisel juhul tuleb ühise kihi objektid tüübi välja väärtuste järgi vastendada.

## Eraldi kanalisatsioonikihtide kasutamine

Kui isevoolne kanalisatsioon, survekanalisatsioon ja sademevesi asuvad eraldi QGIS-i kihtidel:

1. Veendu, et valik **Kasuta üht kanalisatsioonikihti tüüpide ID-kaardistusega** ei ole märgitud.
2. Vali eraldi kihid väljadele **Kanalisatsioonitorud**, **Survekanalisatsioonitorud** ja **Sademeveetorud**.
3. Vajuta **Kinnita**.

Selles seadistusviisis ei kasutata tüübi välja ega ID-kaardistust.

## Ühise kanalisatsioonikihi kasutamine

Kasuta ühist kihti juhul, kui erinevad kanalisatsiooniliigid asuvad samas QGIS-i kihis ning on eristatavad atribuudi väärtuse järgi.

1. Vali väljale **Kanalisatsioonitorud** ühine torustike kiht.
2. Märgi **Kasuta üht kanalisatsioonikihti tüüpide ID-kaardistusega**.
3. Vali väljalt **Tüübi väli** atribuut, mille väärtus määrab kanalisatsiooni liigi.
4. Vajuta **Lisa kaardistus**.
5. Vali kaardistuse liik.
6. Sisesta selle liigi üks või mitu ID-d komadega eraldatult.
7. Lisa read kõigi projektis kasutatavate liikide jaoks.
8. Kontrolli kaardi kokkuvõtet ja vajuta **Kinnita**.

Ühise kihi kasutamisel peidetakse eraldi väljad **Survekanalisatsioonitorud** ja **Sademeveetorud**, sest Kavitro leiab need objektid valitud ühiskihist.

### Kaardistatavad kanalisatsiooniliigid

| Liik | Uue rea soovituslik algväärtus |
|---|---:|
| Kanalisatsioon | `10` |
| Kanalisatsioon, surve | `11` |
| Ühisvoolne | `20` |
| Ühisvoolne, surve | `21` |
| Sadevesi | `00` |
| Sadevesi, surve | `01` |
| Drenaaž | `60` |
| Muud | Kõik ülejäänud väärtused |

Need on Kavitro pakutavad algväärtused, mitte kohustuslik standard. Kontrolli alati oma kihi tegelikke atribuudi väärtusi ja muuda ID-sid vastavalt projektile.

Valiku **Muud** korral ei sisestata ID-d. See rida tähistab väärtusi, mida ükski teine kaardistusrida ei hõlma. Sama liiki saab kaardistuses kasutada ainult üks kord.

## Geospatiali abiga seadistus

Geospatiali režiimi sisselülitamiseks:

1. Vajuta **Ühenda Geospatiali kaudu**.
2. Loe kuvatav selgitus läbi.
3. Kinnita dialoog.
4. Vajuta seadistuste akna all **Kinnita**.

Pärast režiimi aktiveerimist:

- kuvatakse olek **Geospatiali abiga seadistus**;
- käsitsi baaskihtide väljad ja EVEL-i valik peidetakse;
- moodulite seadistuskaartidel kuvatakse Geospatiali lähtekihi andmete vastendamise tööriist;
- tööde ajutise kihi loomise tööriist peidetakse.

**Oluline:** praeguses versioonis on see ettevalmistav integratsioonirežiim. Selle sisselülitamine ei vali ega loo projekti baaskihte automaatselt. Režiim reserveerib seadistusala Geospatiali töövoole ja võimaldab moodulikihtidesse andmeid vastendada.

Andmete ülekandmise täpne töövoog ja piirangud on kirjeldatud juhendis [Geospatiali kihtide vastendamine](06_geospatiali_kihtide_vastendamine.md).

Käsitsi seadistusse naasmiseks:

1. Vajuta **Vaata Geospatiali seadistust**.
2. Kinnita Geospatiali režiimi väljalülitamine.
3. Seadista nähtavale ilmunud baaskihid käsitsi või EVEL-i tuvastusega.
4. Vajuta **Kinnita**.

Geospatiali režiimist väljumine ei taasta puuduvaid baaskihte automaatselt.

## Muudatuste salvestamine

Baaskihtide valikud, EVEL-i olek ja kanalisatsioonitüüpide kaardistus jäävad ootele, kuni vajutad seadistuste akna all nuppu **Kinnita**.

Kui lahkud enne kinnitamist, saad valida muudatuste salvestamise, hülgamise või seadistustesse jäämise. Hülgamisel taastatakse viimati salvestatud baaskihtide valikud.

## Baaskihtide lähtestamine

Kaardi **Lähtesta** nupp:

- eemaldab kõik selle projekti salvestatud baaskihtide viited;
- lülitab välja EVEL-i automaattuvastuse;
- eemaldab ühise kanalisatsioonikihi välja ja ID-kaardistuse;
- lülitab välja Geospatiali seadistusrežiimi;
- taastab käsitsi seadistuse tühja oleku.

**Oluline:** lähtestamine rakendub kohe. Seadistustest lahkumisel valik **Hülga** seda tagasi ei võta. Lähtestamine ei kustuta QGIS-i kihte ega nende objekte.

## Levinumad olukorrad

### Vajalikku kihti ei ole valikus

Kontrolli, et kiht oleks avatud projektis, kehtiv ja geomeetriaga. Vajaduse korral lisa kiht QGIS-i projekti ning ava seadistused uuesti.

### EVEL-i automaattuvastus ei leia kihti

Kihi nimi ei vasta toetatud nimetusele või kiht ei ole projekti laaditud. Eemalda EVEL-i märge ja vali kiht käsitsi.

### Kihivalikud on keelatud

Kasutusel on EVEL-i automaattuvastus või Geospatiali režiim. Käsitsi valimiseks eemalda EVEL-i märge või naase Geospatiali režiimist käsitsi seadistusse.

### Ühise kanalisatsioonikihi valikut ei saa märkida

Esmalt vali või tuvasta kiht **Kanalisatsioonitorud**. Ilma ühise põhikihita ei saa tüübi välja ega ID-kaardistust seadistada.

### Survekanalisatsiooni ja sademevee väljad kadusid

Valik **Kasuta üht kanalisatsioonikihti tüüpide ID-kaardistusega** on sisse lülitatud. Need liigid leitakse nüüd ühisest kanalisatsioonikihist tüübi välja alusel.

### Baaskiht töötab ühes projektis, kuid mitte teises

Baaskihtide seosed on projektipõhised. Ava teise projekti **Seaded** ja määra selle projekti baaskihid eraldi.

### Muudatus ei rakendunud

Kontrolli, et vajutasid **Kinnita**. Kui valitud kiht eemaldati projektist, lisa see tagasi või vali teine kiht.

## Kontrollnimekiri

Pärast baaskihtide seadistamist kontrolli, et:

- aktiivne on soovitud seadistusrežiim;
- kõik projektis kasutatavad baaskihid on leitud või käsitsi valitud;
- ühise kanalisatsioonikihi korral on valitud õige tüübi väli;
- kaardistuse ID-d vastavad kihi tegelikele väärtustele;
- muudatused on kinnitatud;
- kaardi kokkuvõttes kuvatakse õiged kihid;
- Kavitro kaarditoimingud leiavad oodatud tehnovõrgu objektid.
