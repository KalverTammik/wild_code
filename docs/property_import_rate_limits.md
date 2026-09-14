# Kinnistute impordi päringupiirangud

Kontrollitud 15.09.2026. API dokumentatsioon:

- [Päringu- ja muutmistoimingute piirangud](https://kavitro.dev/docs/basics/rateLimits)
- [Veakäsitlus](https://kavitro.dev/docs/concepts/errors)
- [Kinnistu loomise sisend](https://kavitro.dev/docs/graphql/reference/inputs/create-property-input)
- [Kinnistu uuendamise sisend](https://kavitro.dev/docs/graphql/reference/inputs/update-property-input)

Autenditud päringute piir on dokumentatsiooni järgi 500 minutis tokeni kohta. Muutmistoimingutel on eraldi piirid: 40 minutis kasutaja ja 300 minutis konto kohta. Loendatakse GraphQL-i juurtaseme muutmisvälju, mitte HTTP ümbriseid. Serveri vastusepäised on määravad ka siis, kui piirid muutuvad.

Praegune API ei võimalda sihtotstarbeid `createProperty` ega `updateProperty` sisendis saata. Kinnistu andmete ja sihtotstarvete salvestamiseks jääb kaks muutmistoimingut. Üheks ühendamine eeldab backend'i sisendite laiendamist. Kahe muutmisvälja samasse HTTP-päringusse pakkimine muutmistoimingute eelarvet ei vähenda.

## Rakendatud käitumine

Hooldusprojekti eeskujul alustatakse taustatöös vaikimisi kuni 30 muutmistoiminguga minutis, vähemalt kahe sekundi pikkuse vahega. Ühine piiraja arvestab iga tegelikku katset, serveri üld-, kasutaja- ja kontolimiidi päiseid ning teiste plugina klientide päringuid. Kasutaja/konto täpse võtme puudumisel jagatakse kohalikke muutmispiire konservatiivselt sama serveriaadressi kõigi klientide vahel. Üldpäringute eelarve on tokeni põhine; tokenit ei logita.

Ajutine HTTP 429 koos `Retry-After` väärtusega jätab sama füüsilise päringu korduskatsete tsüklisse. Kontrollitud impordis jätkub see kuni õnnestumise või katkestamiseni. Kui loomine õnnestus ja sihtotstarbe päring sai 429, korratakse ainult sihtotstarbe päringut. Kasutaja näeb ooteaega ja automaatse jätkamise teadet; QGIS-i kasutajaliidese lõim ei maga.

`TOO_MANY_MUTATIONS` vastus ilma `Retry-After` päiseta tähendab dokumentatsiooni järgi ühe päringu liiga suurt mahtu. Sellist päringut muutmata ei korrata. Püsiv salvestusviga peatab kontrollitud impordi, näitab veaga kinnistut ja ülejäänud töötlemata kannete arvu. Võrguvea või kadunud loomise vastuse korral ei korrata loomist pimesi, sest server võis selle juba täita.

Katkestamine peatab oote ja järgmised saatmised. Juba saadetud HTTP päringut ei katkestata jõuga. Kui kinnistu mitmeosalise salvestamise järgmine etapp jääb katkestamisel saatmata, jääb kinnistu töötlemata arvestusse; järgmisel kontrollil tuleb tuvastada selle tegelik backend'i seis.

Senised kasutajaliidese lõimes töötavad üksiktoimingud ei oota keskse piiraja sees. Need arvestatakse ühisesse eelarvesse, kuid ennetav paus ja automaatne korduskatsete tsükkel rakenduvad taustatööle. Teadaoleva serveripiirangu korral tagastatakse kasutajaliidese lõimele kohe viga. Kontrollimata lisamise vana interaktiivne töövoog ei muutu selle parandusega taustatööks.

## Kontrollimine

Automaattestid asendavad HTTP vastused ja aja; päris backend'i ei muudeta. Kaetud on kasutaja- ja kontolimiidid, vastusepäised, järjestikused 429 vastused, sama etapi kordamine, vastuse ID kontroll, katkestamine ning Qt edenemine. Õnnestumise aluseks on serveri edukas mutatsioonivastus õige kirje ID-ga, mitte eraldi hilisem andmete tagasilugemine.

Kasutajakatses saab pärast arendusplugina uuesti laadimist kontrollida väikest ülevaadatud valikut: paus peab olema nähtav, õnnestumiste arv peab kasvama alles pärast kinnistu kõigi etappide lõppu ja ebaõnnestunud toiming ei tohi jääda märkamatult vahele. Katkestamist saab proovida oote ajal. LIVE-paketti tuleb parandus avaldada eraldi versioonina.
