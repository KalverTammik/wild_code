"""Every translation key must be answerable in both languages.

Complementary to, not a repeat of, the two checks that already exist:
`PropertyLocationRulesTest.test_property_table_headers_come_from_translations_in_both_languages`
covers only the four property-table header keys, and the login-dialog language test
covers only that dialog's own labels. This file takes the whole `TranslationKeys`
catalogue and asks a different question: is any key present in one language file but
not the other, and is any key missing from both? A strict lookup raises on a missing
key, so a gap is a crash in the other language, not a cosmetic fallback.
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from Kavitro_dev.languages import en as en_module
from Kavitro_dev.languages import et as et_module
from Kavitro_dev.languages.translation_keys import TranslationKeys

# Gaps found when this test was written (maintenance step 9) were fixed rather than
# tolerated: `MODULE_SETTINGS` now has an English answer, and the five legacy keys
# that named their own English fallback text (CANCEL, AREA_LABEL,
# ENTER_ADDITIONAL_NOTES, FIELD_REQUIRED, REQUIRED_FIELD) were unused anywhere in the
# codebase and were deleted. These sets stay empty; the assertions below compare for
# equality, so any new gap fails loudly instead of being silently tolerated.
KNOWN_MISSING_FROM_BOTH: set = set()
KNOWN_MISSING_FROM_EN: set = set()
KNOWN_MISSING_FROM_ET: set = set()


def declared_keys() -> set:
    """Every string constant declared on TranslationKeys."""
    return {value for name, value in vars(TranslationKeys).items()
            if not name.startswith('_') and isinstance(value, str)}


class TranslationCompletenessTest(unittest.TestCase):
    def setUp(self) -> None:
        self.keys = declared_keys()
        self.et = set(et_module.TRANSLATIONS)
        self.en = set(en_module.TRANSLATIONS)

    def test_the_catalogue_is_not_empty(self) -> None:
        """Guards the reflection above: a rename must not quietly make this test vacuous."""
        self.assertGreater(len(self.keys), 500)
        self.assertGreater(len(self.et), 500)
        self.assertGreater(len(self.en), 500)

    def test_no_key_is_translated_in_only_one_language(self) -> None:
        """A key either both languages answer, or neither -- never exactly one."""
        self.assertEqual(self.et - self.en, KNOWN_MISSING_FROM_EN)
        self.assertEqual(self.en - self.et, KNOWN_MISSING_FROM_ET)

    def test_every_declared_key_is_answered_by_estonian(self) -> None:
        self.assertEqual(self.keys - self.et, KNOWN_MISSING_FROM_BOTH | KNOWN_MISSING_FROM_ET)

    def test_every_declared_key_is_answered_by_english(self) -> None:
        self.assertEqual(self.keys - self.en, KNOWN_MISSING_FROM_BOTH | KNOWN_MISSING_FROM_EN)


if __name__ == '__main__':
    unittest.main()
