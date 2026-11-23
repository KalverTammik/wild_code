# Tõlked

Kasutajale nähtav tekst tuleb ainult tõlkevõtmest.

- `translation_keys.py`: klass `TranslationKeys`, iga teksti võti.
- `et.py` ja `en.py`: sõnastik `TRANSLATIONS` võtmest tekstini. Toetatud keeled on
  `SUPPORTED_LANGUAGES` (`language_manager.py`), vaikimisi eesti keel.
- `language_manager.py`: `LanguageManager.translate(key)` ja `translate_static(key)`.
  Puuduv võti on viga, mitte varutekst.
- `MaaAmetFieldFormater.py`: Maa-ameti katastriväljade väärtuste kuvavorming (kuupäevad, tekst).

## Uus tekst

1. Lisa võti `TranslationKeys` klassi.
2. Lisa tekst nii `et.py` kui ka `en.py` faili.
3. Kasuta koodis `lang_manager.translate(TranslationKeys.<VÕTI>)`. Ära lisa koodi
   varuteksti (`translate(...) or "..."`) ega anna vidinale teksti otse.

Testid `tests/test_translation_completeness.py` ja `tests/test_translation_keys_in_code.py`
kontrollivad, et igal võtmel on mõlemas keeles tekst, koodis kasutatud võtmed on olemas
ja kasutajale nähtavat teksti ei kirjutata koodi otse.
