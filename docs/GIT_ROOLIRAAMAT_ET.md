# GIT ROOLIRAAMAT (ET) – Commitid, harud ja muudatuste tasakaalustamine

Eesmärk: selged reeglid, et me saaksime „mõlemast maailmast parima“ – väiksed, arusaadavad committid, puhas lineaarne ajalugu ja konfliktide kiire lahendamine VS Code’i kaudu.

---

## TL;DR reegelkaart
- Tee väikesed, iseseisvad committid; üks loogiline muudatus per commit.
- Kirjuta selged sõnumid: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `build:`, `chore:`.
- Enne push’i: Pull (Rebase) → lahenda konfliktid → test → push.
- Konflikti korral ava Merge Editor ja kasuta „Accept Both“, kui mõlemad poolikud sisud on vajalikud – seejärel korrasta käsitsi.
- Ära muuda QGIS-i globaalseid seadeid ega stiile; commit’i ainult plugina muudatused.

---

## Haru strateegia
- `main`: stabiilne ja release’iks valmis. Hoia ajalugu lineaarne (rebase, mitte merge-commit).
- `feature/*`: iga eraldi töö/teema jaoks oma haru.
- Kriitilised fixid: `fix/*` harud; kiire PR → rebase → merge.

Soovi korral avalda PR isegi väikese muudatusega – lihtsam üle vaadata ja tagasi kerida.

---

## Commit reeglid
- Üks commit = üks mõtestatud muudatus (nt üks failiplokk, üks bugfix või üks docs-uuendus).
- Väldi mass-formatting’ut koos sisumuudatustega.
- Sõnumi formaat:
  - Pealkiri (kuni ~72 märki): `type(scope?): lühikirjeldus`
  - Keha (valikuline): „miks“ ja „kuidas“, viide BUGS.md või taskile.
- Näited:
  - `fix(settings): eelistatud mooduli salvestus ei kandu uuele kasutajale`
  - `docs: lisa HOIATUS teema lekkimise vastu (global setStyleSheet)`
  - `refactor: tõsta inline import ülaossa (WelcomePage, ModuleFeedBuilder)`

---

## Sünkroonimine (balancing changes)
VS Code Source Control UI:
1. Commit: Stage → kirjuta sõnum → Commit.
2. Pull (Rebase): … menüü → Pull (Rebase). See toob kolleegi muudatused ja „mängib“ sinu commitid peale – tulemuseks puhtam ajalugu.
3. Konfliktid: ava Merge Editor; vali „Accept Current/Incoming/Both“ vastavalt; paranda tekst; salvesta; „Mark as resolved“ → Commit.
4. Push: „Sync Changes“ või … → Push.

Soovitused:
- Sea vaikimisi rebase: Settings → `git.pullRebase` = true.
- Kui alustad suuremat tööd: loo haru (Status Bar → Branch → Create new branch…).

---

## Konfliktide lahendamine (VS Code)
- „Merge Changes“ loendis klõpsa fail → avaneb kolmikvaade.
- Vali hunkide kaupa:
  - Accept Current = Sinu versioon
  - Accept Incoming = Kolleegi versioon
  - Accept Both = Mõlemad plokid (järeltoimetus vajalik)
- Eemalda konfliktimärgid/duplikaadid, loe läbi, käivita kiire kontroll (Problems paneel), salvesta.
- „Mark as resolved“ → Commit.

Erinõuanded tekstile, mis peab mahtuma „mõlemast maailmast“:
- Kasuta „Accept Both“, koonda sisu, eemalda kordused, ühtlusta sõnastus.
- Hoia kronoloogiat: uued reeglid/hoiatused lõpus, baseline reeglid ees.

---

## Stash ja puhtad tööalad
- Kui pead kiiresti haru vahetama: Source Control → … → Stash → Stash.
- Hiljem: … → Stash → Apply (või Pop) ja jätka.

---

## Revert ja Cherry-pick
- Revert: kui commit põhjustas regressiooni, tee „Revert Commit“ (Timeline või SCM … menüüst), test ja push.
- Cherry-pick: vali commit ajaloost (Timeline), „Cherry-pick“ teisele harule (kasulik kuumade fixide portimiseks).

---

## Failide erijuhised (QGIS plugin)
- Ära commiti `__pycache__/`, `.pyc`, lokaalseid ehitusfaile ega ide-konfiguratsioone (va .vscode, kui tiimiga kokku lepitud).
- Teema ja QSS:
  - ÄRA kasuta globaalset `QApplication.setStyleSheet` (teema lekib QGIS-i). Kasuta `ThemeManager.apply_module_style` ja `ThemeManager.apply_tooltip_style` (ainult QToolTip palett).
- Ressursid (pildid/ikoonid): lisa vaid vajalikud; hoia teemapõhised variandid `resources/icons/Light|Dark`.
- Dokumentatsioon: hoia muutused eraldi commit’is (nt BUGS.md, copilot-prompt.md, docs/).

---

## Kontrollnimekiri enne push’i
- [ ] Kood jookseb (min kontroll); pole süntaksivigu.
- [ ] Commitid on väikesed ja selgete sõnumitega.
- [ ] Pull (Rebase) tehtud; konfliktid lahendatud.
- [ ] Ei ole kogemata globaalseid muudatusi (nt teema lekkeid, mass-formatt).
- [ ] BUGS.md/IDEAS.md uuendatud, kui teema seda puudutab.

---

## VS Code’i praktilised seaded
- `git.pullRebase = true` – hoiab ajaloo lineaarse.
- `diffEditor.ignoreTrimWhitespace = true` – vähendab tühikukonflikte.
- `files.eol = "\n"` (kui tiimiga kokku lepitud) – ühtlustab reavahetused.
- `git.enableSmartCommit = true` – lubab kiire commit’i, kui kõik staged.

---

## Näidistsõnumid (ET)
- `fix(theme): peata QGIS-i globaalne tumenemine; piirdu QToolTip paletiga`
- `docs(copilot): lisa HOIATUS globaalsete stiililehtede vastu`
- `refactor(widgets): tõsta inline import’id faili algusesse`
- `feat(settings): eelistatud mooduli uuendus ja retheme`()

---

Küsimused või ettepanekud? Lisa need IDEAS.md faili või ava eraldi teema PR-is (review annab kõige kiirema tagasiside).
