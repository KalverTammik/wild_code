# Kavitro QGIS Plugin

Kavitro plugin seob QGIS-i kaarditöö Kavitro backendiga. Plugin koondab moodulipõhised töövood ühte QGIS-i aknasse, et kasutaja saaks hallata kinnistuid, projekte, lepinguid, kooskõlastusi, servituute, töid ja teostusandmeid koos kaardikontekstiga.

## Põhivõimekused

- moodulipõhine töölaud Kavitro objektide sirvimiseks ja filtreerimiseks
- sisselogimine ja sessioonihaldus Kavitro backendiga
- GraphQL-põhine andmelaadimine ja pagineeritud listivaated
- QGIS-i kihtide loomine, valimine, aktiveerimine ja sünkroonimine
- kaardilt uute objektide lisamine toetatud moodulites
- tööde geomeetria saatmine backendile ja GIS-is loodud sidumata tööde ülevaatamine
- kasutajapõhised seaded, sh sisestuspaan ja kaardiotsing
- mitmekeelne UI ning ühtne Kavitro stiil

## Arendusmärkmed

Kehtivad refaktoreerimisreeglid on failis [REFACTOR_RULES.md](REFACTOR_RULES.md).
Dokumentatsiooni jaotus ning säilitamisreeglid on kirjas failis
[docs/README.md](docs/README.md).

## Arendus

Toetatud on QGIS 3.40 kuni 4.x (`metadata.txt` ja `metadata.release.txt`).

Testid käivitatakse QGIS-i Pythoniga ilma QGIS-i aknata:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
& "C:\Program Files\QGIS 3.40.13\bin\python-qgis-ltr.bat" tools/run_tests.py [muster]
```

Skript paneb plugina juurkausta ja QGIS-i pluginate kausta `sys.path`-ile ning käivitab
komplekti ajutises kaustas.

- Geomeetriaga mälukihtide testid loovad jooksvasse kausta QGIS-i `symbology-style.db`
  faili; seepärast ei käivitata komplekti plugina kaustas.
- Testid ei tohi saata päris päringuid. Mock'imata päring avab sisselogimisakna, mis
  ilma QGIS-i aknata ei sulgu, ja kogu komplekt jääb seisma.
- Testid ei kirjuta `Logs/` kausta: `PythonFailLogger` loob logifaile alles pärast
  `start_session()`, mida kutsub ainult plugina avamine.
- Kontrolli väljumiskoodi, mitte ainult rida `OK`: lahti jäänud Qt objekt võib protsessi
  lõpus kokku kukkuda.

Lint: `ruff check .` plugina juurkaustas. Reeglid on failis [.ruff.toml](.ruff.toml).

GitHubis käivitab [tests.yml](.github/workflows/tests.yml) iga `main`-i push'i ja pull requesti peale ruffi ning kogu komplekti ametlikes `qgis/qgis:3.40.13-noble` (Qt5) ja `qgis/qgis:4.4` (Qt6) konteinerites. Linuxis jooksevad ka POSIX-i failiõiguste ja sümbollingi testid, mis Windowsis vahele jäävad. Väljalaske töövoog käivitab sama kontrolli enne paketi ehitamist ega avalda midagi, kui see ebaõnnestub.

Sama konteineri saab käivitada ka kohapeal (Docker Desktop), kui kaust on nimega `Kavitro_dev`:

```bash
docker run --rm -e QT_QPA_PLATFORM=offscreen -e PYTHONPATH=/usr/share/qgis/python:/usr/share/qgis/python/plugins \
  -v "<kaust, kus on Kavitro_dev>:/work" -w /work/Kavitro_dev qgis/qgis:3.40.13-noble \
  python3 tools/run_tests.py
```

QGIS 4 jaoks kasuta pilti `qgis/qgis:4.4`. Teadaolevad Qt6 erinevused, mis ootavad lahendamist, on testides märgitud `qt6_stage4`-ga ja jäävad seal vahele.

## Release

Release'i juhendid:

- [RELEASE.md](RELEASE.md) – kasutatav avaldamisprotsess
- [release_setup_reference.md](docs/development/release_setup_reference.md) – detailne
  DEV/LIVE seadistuse referents

## Asset Attribution

Some UI icons are sourced from or based on Icons8 assets. The plugin footer includes an Icons8 attribution link in accordance with Icons8 free-use attribution expectations.

- Icons8: https://icons8.com
