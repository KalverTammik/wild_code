"""The plugin language follows the Kavitro account: normalising, one plugin-wide choice, remembering it, failing safe."""
from __future__ import annotations

import importlib
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1].parent))

manager_module = importlib.import_module("Kavitro_dev.languages.language_manager")
preference_module = importlib.import_module("Kavitro_dev.languages.language_preference")
keys_module = importlib.import_module("Kavitro_dev.languages.translation_keys")

LanguageManager = manager_module.LanguageManager
TranslationKeys = keys_module.TranslationKeys


class FakeSettings:
    def __init__(self, stored: str = "", fail: bool = False):
        self.stored = stored
        self.fail = fail

    def language(self, value=None):
        if self.fail:
            raise RuntimeError("settings store broken")
        if value is None:
            return self.stored
        self.stored = value
        return value


class LanguageTestCase(unittest.TestCase):
    def setUp(self) -> None:
        manager_module.set_current_language("et")
        self.addCleanup(manager_module.set_current_language, "et")


class NormalizeLanguageTest(unittest.TestCase):
    def test_supported_codes_survive_case_and_region_suffix(self) -> None:
        for raw, expected in (("et", "et"), ("EN", "en"), (" en-GB ", "en"), ("et_EE", "et")):
            with self.subTest(raw=raw):
                self.assertEqual(manager_module.normalize_language(raw), expected)

    def test_unknown_or_empty_values_give_none(self) -> None:
        for raw in (None, "", "   ", "fi", "english", 7):
            with self.subTest(raw=raw):
                self.assertIsNone(manager_module.normalize_language(raw))


class PluginWideLanguageTest(LanguageTestCase):
    def test_default_is_estonian(self) -> None:
        self.assertEqual(LanguageManager().language, "et")

    def test_manager_without_a_language_follows_the_plugin_language(self) -> None:
        follower = LanguageManager()
        key = TranslationKeys.LOGIN_BUTTON
        estonian = follower.translate(key)

        manager_module.set_current_language("en")

        self.assertEqual(follower.language, "en")
        self.assertEqual(follower.translate(key), LanguageManager("en").translate(key))
        self.assertNotEqual(follower.translate(key), estonian)

    def test_manager_with_a_language_is_pinned(self) -> None:
        pinned = LanguageManager("et")
        manager_module.set_current_language("en")
        self.assertEqual(pinned.language, "et")

    def test_translate_static_uses_the_plugin_language(self) -> None:
        manager_module.set_current_language("en")
        key = TranslationKeys.LOGIN_BUTTON
        self.assertEqual(LanguageManager.translate_static(key), LanguageManager("en").translate(key))

    def test_unsupported_language_falls_back_to_estonian(self) -> None:
        manager_module.set_current_language("en")
        manager_module.set_current_language("fi")
        self.assertEqual(manager_module.get_current_language(), "et")

    def test_both_languages_translate_every_key(self) -> None:
        keys = {v for k, v in vars(TranslationKeys).items() if not k.startswith("_") and isinstance(v, str)}
        for language in manager_module.SUPPORTED_LANGUAGES:
            manager = LanguageManager(language)
            for key in keys:
                manager.translate(key)  # a gap raises KeyError

    def test_a_missing_key_raises_in_every_language_and_names_it(self) -> None:
        for language in manager_module.SUPPORTED_LANGUAGES:
            with self.subTest(language=language):
                with self.assertRaises(KeyError) as raised:
                    LanguageManager(language).translate("no_such_key")
                self.assertIn("no_such_key", str(raised.exception))
                self.assertIn(language, str(raised.exception))

    def test_translate_takes_no_fallback(self) -> None:
        import inspect

        for function in (LanguageManager.translate, LanguageManager.translate_static):
            self.assertEqual([p for p in inspect.signature(function).parameters if p != "self"], ["key"])


class RememberedLanguageTest(LanguageTestCase):
    def test_restore_applies_the_stored_language(self) -> None:
        self.assertEqual(preference_module.restore_saved_language(FakeSettings("en")), "en")
        self.assertEqual(manager_module.get_current_language(), "en")

    def test_restore_with_nothing_stored_or_a_broken_store_keeps_estonian(self) -> None:
        self.assertEqual(preference_module.restore_saved_language(FakeSettings("")), "et")
        self.assertEqual(preference_module.restore_saved_language(FakeSettings(fail=True)), "et")

    def test_account_language_is_applied_and_remembered(self) -> None:
        settings = FakeSettings()
        self.assertEqual(preference_module.apply_account_language("en_GB", settings), "en")
        self.assertEqual(manager_module.get_current_language(), "en")
        self.assertEqual(settings.stored, "en")

    def test_unusable_account_language_changes_nothing(self) -> None:
        manager_module.set_current_language("en")
        settings = FakeSettings("en")
        for raw in (None, "", "fi"):
            with self.subTest(raw=raw):
                self.assertIsNone(preference_module.apply_account_language(raw, settings))
                self.assertEqual(manager_module.get_current_language(), "en")

    def test_a_broken_settings_store_does_not_undo_the_applied_language(self) -> None:
        self.assertEqual(preference_module.apply_account_language("en", FakeSettings(fail=True)), "en")
        self.assertEqual(manager_module.get_current_language(), "en")


class FetchAccountLanguageTest(LanguageTestCase):
    def fetch(self, answer=None, error: Exception | None = None):
        loader = MagicMock()
        loader.load_query_by_module.return_value = "query"
        client = MagicMock()
        if error is not None:
            client.send_query.side_effect = error
        else:
            client.send_query.return_value = answer
        return preference_module.fetch_account_language(loader, client), loader, client

    def test_reads_the_language_of_the_signed_in_user(self) -> None:
        language, loader, client = self.fetch({"me": {"language": "et"}})
        self.assertEqual(language, "et")
        loader.load_query_by_module.assert_called_once_with("user", "me_language.graphql")
        client.send_query.assert_called_once_with("query")

    def test_missing_or_null_language_gives_none(self) -> None:
        for answer in ({"me": {"language": None}}, {"me": None}, {}, None, "junk"):
            with self.subTest(answer=answer):
                self.assertIsNone(self.fetch(answer)[0])

    def test_a_failing_request_gives_none_instead_of_raising(self) -> None:
        self.assertIsNone(self.fetch(error=RuntimeError("down"))[0])

    def test_adopt_applies_what_the_server_said(self) -> None:
        loader = MagicMock()
        loader.load_query_by_module.return_value = "query"
        client = MagicMock()
        client.send_query.return_value = {"me": {"language": "en"}}
        self.assertEqual(preference_module.adopt_account_language(loader, client, FakeSettings()), "en")
        self.assertEqual(manager_module.get_current_language(), "en")


if __name__ == "__main__":
    unittest.main()
