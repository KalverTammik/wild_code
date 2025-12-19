# SettingsUI refaktor – user payload ja module cardid

## Eesmärk

Lihtsustada `SettingsUI` loogikat nii, et:
- **User payload** määrab, milliseid **moodulikaardid** üldse ehitatakse ja kuvatakse.
- `activate()` käitumine oleks selge: käivitab user payloadi laadimise ja vajadusel algse settingsi laadimise.
- Vähendada flag’ide ja ülemäära keeruka state’i hulka (`_initialized`, `_module_cards_activated`, `_last_payload_signature`, jne).
- Jaotada vastutused väiksemateks, loogilisteks meetoditeks.

---

## Praegune olukord (lühikokkuvõte)

Praegu on voog sisuliselt selline:

1. `__init__` / `setup_ui`:
   - Ehitatakse põhiskeletid (scroll area, container, layout).
   - Luakse user card (ilma payloadita).
   - **Module cards ei ehitata veel**.
   - Teema rakendatakse (`ThemeManager.apply_module_style`).

2. `activate()`:
   - Kutsub `_refresh_user_info()`.

3. `_refresh_user_info()`:
   - Tühistab eelmise worker’i (kui olemas).
   - Näitab "Loading..." user infol.
   - Käivitab taustal `userUtils.fetch_user_payload` (FunctionWorker).
   - `finished` signaal → `_handle_user_worker_success`.

4. `_handle_user_worker_success` → `_apply_user_payload`:
   - Salvestab `user_payload`.
   - Arvutab payloadi signatuuri, võrdleb eelmisega.
   - Uuendab user card’i (nimi, email, rollid).
   - Võtab `abilities`, teeb `subjects`, ehitab `access_map` ja `update_permissions`.
   - Seob permissions user card’iga.
   - Laeb originaalsed settingsid esimesel korral.
   - Ehitab module cards (kui mitte veel ehitatud).
   - Aktiveerib module cards (kui payload muutus / pole varem tehtud).

**Probleem:** `_apply_user_payload` teeb korraga liiga palju:

- User pea (nimi, email, rollid).
- Permissions (abilities → subjects → access map).
- Module cardide ehitamise otsus.
- Module cardide aktiveerimise otsus.
- Originaalsete settingsite laadimine.
- Erinevate flag’ide (`_initialized`, `_module_cards_activated`, `_settings_loaded_once`, `_last_payload_signature`) haldamine.

See teeb koodi raskesti loetavaks ja tekitab tunde, et süsteem on "over-engineered", kuigi põhiidee (payload → lubatud moodulid) on õige.

---

## Põhiprintsiip: user payload määrab, milliseid kaarte ehitada

Sinu loogika, millega nõustume:

> **User payload** (täpsemalt `abilities` → `subjects` → `access_map`) määrab,
> millistele moodulitele kasutajal on ligipääs. Module card luuakse **ainult siis**, kui see moodul on kasutajale lubatud.

Ehk pipeline on:

```text
payload
  → abilities
    → subjects
      → access_map (ja/või allowed_modules)
        → ehita ainult lubatud module cards
```

Seda me **säilitame**. Refaktor ei muuda seda põhimõtet, ainult struktuuri.

---

## Soovitatud uus struktuur

### 1. `activate()`

`activate()` roll oleks väga kitsas ja selge:

```python
def activate(self):
    """Kasutaja avab Settings UI → laadime värske user info."""
    self._refresh_user_info()
```

Vajadusel võib siin olla ka:

- Esmakordsel avamisel algsete settingsite laadimine (`logic.load_original_settings()`),
- Aga seda saab teha ka payloadi saabumise hetkel (vt allpool).

### 2. Workerist tulles: `_handle_user_worker_success`

Selle asemel, et otse `_apply_user_payload`, võiks olla vahemeetod, mis:

- Kontrollib, kas see worker on endiselt viimane (`request_id` võrdlus),
- Ja seejärel suunab payloadi edasi kesksele handlerile:

```python
def _handle_user_worker_success(self, payload: dict):
    if not self._is_latest_request():
        return

    self._on_user_payload_ready(payload or {})
```

### 3. Uus keskne meetod: `_on_user_payload_ready`

Siin jaotame vastutuse selgelt alammooduliteks:

```python
def _on_user_payload_ready(self, payload: dict):
    self.user_payload = payload

    # 1) User header – nimi, email, rollid
    self._update_user_header(payload)

    # 2) Abilities → subjects → access & permissions
    subjects = userUtils.abilities_to_subjects(payload.get("abilities"))
    access_map = self.logic.get_module_access_from_abilities(subjects)
    update_permissions = self.logic.get_module_update_permissions(subjects)

    # 3) Allowed modules – milliseid kaarte ehitada / hoida
    allowed_modules = self.logic.get_allowed_modules_from_access_map(access_map)

    self._ensure_module_cards(
        allowed_modules=allowed_modules,
        access_map=access_map,
        update_permissions=update_permissions,
    )

    # 4) Preferred module & original settings
    self._ensure_original_settings_loaded()
    preferred = self.logic.get_original_preferred()
    self.user_card.set_preferred_module(preferred)
```

### 4. `_ensure_module_cards` – koht, kus payload → kaardid loogika elab

Selles meetodis elabki sinu soovitud reegel: **ehita ainult need kaardid, mis payload lubab**.

```python
def _ensure_module_cards(
    self,
    allowed_modules: list[str],
    access_map: dict,
    update_permissions: dict,
):
    """Sünkroniseeri UI module cards vastavalt allowed_modules listile."""

    # 1) Eemalda kaardid, mis pole enam lubatud
    for module_name, card in list(self._module_cards.items()):
        if module_name not in allowed_modules:
            self.cards_layout.removeWidget(card)
            card.setParent(None)
            del self._module_cards[module_name]

    # 2) Lisa kaardid, mis on lubatud, kuid mida pole veel
    for module_name in allowed_modules:
        if module_name not in self._module_cards:
            card = self._build_module_card(module_name)
            self._module_cards[module_name] = card
            self.cards_layout.addWidget(card)

        card = self._module_cards[module_name]

        # 3) Rakenda õigused ja update-permissions olemasolevatele kaartidele
        if hasattr(card, "apply_access"):
            card.apply_access(access_map.get(module_name))

        if hasattr(card, "apply_update_permissions"):
            card.apply_update_permissions(update_permissions.get(module_name))

        # soovi korral:
        # if hasattr(card, "on_settings_activate"):
        #     card.on_settings_activate(self.logic.get_settings_for_module(module_name))
```

Sellise struktuuri juures:

- **User payload saabumine *otsustab*, millised kaardid on lubatud** – täpselt nagu sa tahtsid.
- Samas on kogu see loogika konteineris (`_ensure_module_cards`), mitte segamini user headeri ja settingsi laadimisega.

### 5. Originaalsed settingsid: `_ensure_original_settings_loaded`

Selleks, et mitte iga payloadi korral uuesti seadeid laadida, võib jääda üks lihtne flag:

```python
def _ensure_original_settings_loaded(self):
    if getattr(self, "_settings_loaded_once", False):
        return

    self.logic.load_original_settings()
    self._settings_loaded_once = True
```

See meetod on kutsutav seestpoolt igal payloadi saabumise korral, ilma et väliskood peaks flag’idega jongleerima.

---

## Mis muutub lihtsamaks?

1. **Selge flow:**  
   `activate()` → `_refresh_user_info()` → worker → `_on_user_payload_ready()` → puhastatud alamfunktsioonid.

2. **Vastutuste eraldamine:**
   - `_update_user_header(payload)` – ainult user info UI.
   - `abilities_to_subjects`, `get_module_access_from_abilities` – ainult õigused.
   - `_ensure_module_cards(...)` – ainult module cardide CRUD (create / update / remove) vastavalt allowed_modules’ile.
   - `_ensure_original_settings_loaded()` – ainult üks kord originaalsete seadete laadimine.

3. **Flag’ide vähendamine:**
   - `_initialized` ja `_module_cards_activated` võivad suure tõenäosusega kaduda, sest:
     - module cards on tuletatud ainult `allowed_modules` põhjal;
     - „aktiveerimine“ tähendab lihtsalt seda, et neile rakendatakse access & settings igal payloadi uuendusel.

4. **Loetavus:**
   - `_apply_user_payload` ei ole enam „kõik ühes“ supersupp, vaid loogiliselt jaotatud sammud.

---

## Kokkuvõte

- Sinu mõte: *“user payload saabumine defineerib milliseid mooduli kaart võib ehitada”* on **täiesti õige ja see jääb alles**.
- Refaktor keskendub sellele, et:
  - see loogika elaks **ühes selges kohas** (`_ensure_module_cards`),
  - `activate()` ja payloadi käsitlus oleksid selgelt loetavad,
  - ei oleks üht mega-funktsiooni, mis teeb kõike korraga.

Seda faili saad kasutada nii:
- arutlemiseks tiimiga, miks ja kuidas refaktor teha;
- Git commit’i kirjeldusena („refactor SettingsUI user payload & module cards lifecycle“);
- tulevaseks self-dokuks, miks `SettingsUI` eluiga on just nii üles ehitatud.
