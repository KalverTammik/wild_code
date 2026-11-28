# Kujunduse proovimine avalehel

Kui komponendi välimuses tuleb kokku leppida, ehitatakse **ajutine proovipaneel
avalehele**, mida näeb ainult arendusversioon. Valik tehakse päris QGIS-is, päris teema ja
fondiga. Nii valmisid kirjekaardi tunnused ja kontaktid (november 2026).

## Käik

1. **Ideed kõrvuti.** 4–6 eri lahendust samade näidisandmetega, igaüks näidiskaardi sees,
   nummerdatud, et saaks vastata „number 3“.
2. **Kitsendamine.** Valitud suunast tehakse paar teisendit (C → C1, C2), ülejäänud
   visatakse kohe ära.
3. **Peenhäälestus.** Valitud lahendusele lisatakse paneelile seadistid (vahed, polstrid,
   kumerus, eraldaja, näidiste arv). Muutus on näha kohe; kasutaja saadab ekraanipildi
   sobivate väärtustega.
4. **Rakendamine.** Valitud väärtused lähevad komponendi konstantideks ja komponent
   pärisvaatesse. Proovida ka kitsast ja laia akent, pikki nimesid, tühje andmeid,
   heledat ja tumedat teemat ning QGIS 3.40 ja 4.x.
5. **Koristus.** Proovipaneel, kasutamata ideed, ainult paneeli jaoks tehtud seaded,
   tõlkevõtmed, stiilireeglid ja testid eemaldatakse.

Visuaalsete proovide ajal piisab lintimisest ja ühest renderdusest; täistestid
jooksutatakse enne commit'i.

## Paneeli ülesehitus

- Avalehe ühendus: `widgets/WelcomePage.py`, tingimusel `ConfigPaths.IS_DEV` pannakse leht
  `QScrollArea` sisse ja paneel näidikute kohale. `retheme()` edastatakse paneelile;
  serverist lugeval paneelil ka `activate()` ja `deactivate()`.
- Pärisrakendusse minev komponent kirjutatakse kohe eraldi failina; paneel ainult kasutab
  seda. Proovitavad mõõdud antakse komponendile ühe `NamedTuple`-na (`Look`), mille
  vaikeväärtused on hetke eelistus.
- Näidiskaart on `QFrame` numbrimärgi, nime ja proovitava komponendiga; stiil
  `ThemeManager.apply_module_style(...)`. Komponent kannab oma stiililehte ise, sest
  mooduli vaates paneeli QSS-i ei ole.
- Näidisandmed on koodis või loetakse Kavitrost; midagi ei salvestata.

## Valmis näited git'i ajaloos

Commit `cbc36a5` (v2.12.113) sisaldab mõlemat paneeli töötaval kujul:

```
git show cbc36a5:widgets/WelcomePage.py                      # avalehe ühendus
git show cbc36a5:widgets/Contacts/contact_prototype_panel.py # ideed kahes tulbas ja seadistid
git show cbc36a5:widgets/Contacts/contact_styles.py          # kuus ideed ühise baasklassiga
git show cbc36a5:widgets/Tags/tag_prototype_panel.py         # päris andmed serverist ja seadistid
git show cbc36a5:widgets/Tags/tag_chips.py                   # komponent Look-seadetega
```

## Kokkulepitud kujundus

- Üks rida: näha nii palju, kui laiusele mahub (vähemalt üks), ülejäänud „+N“ hüpikus
  samal kujul (`widgets/overflow_row.py`).
- Tunnused: grupi kapsel, tunnuste vahel püstkriips (`widgets/Tags/tag_chips.py`).
- Isikud ja ettevõtted: plaat initsiaalide, nime ja rolliga; isik ümara, ettevõte kandilise
  märgiga (`widgets/DataDisplayWidgets/ContactsWidget.py`).
