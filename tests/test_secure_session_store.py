from __future__ import annotations

import unittest
from pathlib import Path

from utils.secure_session_store import (
    AUTH_ID,
    AUTH_STALE_IDS,
    AUTH_TOKEN_KEY,
    AUTH_USERNAME,
    AUTH_CONFIG_NAME,
    LEGACY_AUTH_PASSWORD_KEY,
    LEGACY_AUTH_CONFIG_NAME,
    LEGACY_AUTH_TOKEN_KEY,
    LEGACY_SESSION_TOKEN,
    SecureSessionStore,
)


class FakeSettings:
    def __init__(self, values=None):
        self.values = dict(values or {})
        self.sync_count = 0

    def value(self, key, default=None, **_kwargs):
        return self.values.get(key, default)

    def setValue(self, key, value):
        self.values[key] = value

    def remove(self, key):
        self.values.pop(key, None)

    def sync(self):
        self.sync_count += 1


class FailingLegacyRemovalSettings(FakeSettings):
    def remove(self, key):
        if key == LEGACY_SESSION_TOKEN:
            raise OSError("settings are read-only")
        super().remove(key)


class FakeConfig:
    def __init__(self, method=""):
        self._id = ""
        self._method = method
        self._name = ""
        self.values = {}

    def clone(self):
        clone = FakeConfig(self._method)
        clone._id = self._id
        clone._name = self._name
        clone.values = dict(self.values)
        return clone

    def copy_from(self, other):
        self._id = other._id
        self._method = other._method
        self._name = other._name
        self.values = dict(other.values)

    def id(self):
        return self._id

    def setId(self, value):
        self._id = value

    def setMethod(self, value):
        self._method = value

    def method(self):
        return self._method

    def setName(self, value):
        self._name = value

    def name(self):
        return self._name

    def setConfig(self, key, value):
        self.values[key] = value

    def config(self, key, default=""):
        return self.values.get(key, default)

    def hasConfig(self, key):
        return key in self.values

    def removeConfig(self, key):
        return 1 if self.values.pop(key, None) is not None else 0


class FakeAuthManager:
    def __init__(self):
        self.configs = {}
        self.next_id = 1
        self.store_fails = False
        self.update_fails = False
        self.remove_fails = set()
        self.base_load_fails = set()
        self.full_load_fails = set()
        self.tuple_results = False
        self.store_tuple_without_mutation = False
        self.omit_access_token_on_full_load = False

    def add_config(self, auth_id, values):
        config = FakeConfig("Basic")
        config.setId(auth_id)
        config.setName("Legacy Kavitro")
        config.values = dict(values)
        self.configs[auth_id] = config

    def loadAuthenticationConfig(self, auth_id, config, full=False):
        failed_ids = self.full_load_fails if full else self.base_load_fails
        if auth_id in failed_ids or auth_id not in self.configs:
            return (False, config) if self.tuple_results else False
        config.copy_from(self.configs[auth_id])
        if full and self.omit_access_token_on_full_load:
            config.removeConfig(AUTH_TOKEN_KEY)
        return (True, config.clone()) if self.tuple_results else True

    def storeAuthenticationConfig(self, config):
        if self.store_fails:
            return (False, config) if self.tuple_results else False
        auth_id = f"auth{self.next_id:03d}"
        self.next_id += 1
        stored = config.clone()
        stored.setId(auth_id)
        self.configs[auth_id] = stored
        if self.tuple_results and self.store_tuple_without_mutation:
            return True, stored.clone()
        config.setId(auth_id)
        return (True, config.clone()) if self.tuple_results else True

    def updateAuthenticationConfig(self, config):
        if self.update_fails:
            return (False, config) if self.tuple_results else False
        self.configs[config.id()] = config.clone()
        return (True, config.clone()) if self.tuple_results else True

    def removeAuthenticationConfig(self, auth_id):
        if auth_id in self.remove_fails:
            return False
        self.configs.pop(auth_id, None)
        return True

    def availableAuthMethodConfigs(self):
        return {auth_id: config.clone() for auth_id, config in self.configs.items()}


class SecureSessionStoreTest(unittest.TestCase):
    def make_store(self, settings=None, auth_manager=None):
        settings = settings or FakeSettings()
        auth_manager = auth_manager or FakeAuthManager()
        return (
            SecureSessionStore(auth_manager, settings, FakeConfig),
            settings,
            auth_manager,
        )

    def test_new_token_is_verified_and_plaintext_is_removed(self):
        store, settings, auth_manager = self.make_store(
            FakeSettings({LEGACY_SESSION_TOKEN: "plain-token"})
        )

        result = store.save_token("person@example.com", "access-token")

        self.assertTrue(result.success)
        self.assertTrue(result.plaintext_purged)
        self.assertNotIn(LEGACY_SESSION_TOKEN, settings.values)
        self.assertEqual(settings.value(AUTH_USERNAME), "person@example.com")
        config = auth_manager.configs[settings.value(AUTH_ID)]
        self.assertEqual(config.config(AUTH_TOKEN_KEY), "access-token")
        self.assertFalse(config.hasConfig(LEGACY_AUTH_PASSWORD_KEY))
        self.assertFalse(config.hasConfig(LEGACY_AUTH_TOKEN_KEY))

    def test_existing_legacy_config_is_updated_without_changing_id(self):
        settings = FakeSettings(
            {
                AUTH_ID: "legacy1",
                AUTH_USERNAME: "old@example.com",
                LEGACY_SESSION_TOKEN: "current-token",
            }
        )
        auth_manager = FakeAuthManager()
        auth_manager.add_config(
            "legacy1",
            {
                "username": "old@example.com",
                LEGACY_AUTH_PASSWORD_KEY: "stored-password",
                LEGACY_AUTH_TOKEN_KEY: "old-token",
            },
        )
        store, _, _ = self.make_store(settings, auth_manager)

        result = store.save_token("new@example.com", "current-token")

        self.assertTrue(result.success)
        self.assertEqual(result.auth_id, "legacy1")
        config = auth_manager.configs["legacy1"]
        self.assertEqual(config.config(AUTH_TOKEN_KEY), "current-token")
        self.assertEqual(config.config("username"), "new@example.com")
        self.assertFalse(config.hasConfig(LEGACY_AUTH_PASSWORD_KEY))
        self.assertFalse(config.hasConfig(LEGACY_AUTH_TOKEN_KEY))
        self.assertNotIn(LEGACY_SESSION_TOKEN, settings.values)

    def test_load_marks_legacy_secret_fields_for_migration(self):
        settings = FakeSettings({AUTH_ID: "legacy1"})
        auth_manager = FakeAuthManager()
        auth_manager.add_config(
            "legacy1",
            {
                LEGACY_AUTH_PASSWORD_KEY: "stored-password",
                LEGACY_AUTH_TOKEN_KEY: "legacy-token",
            },
        )
        store, _, _ = self.make_store(settings, auth_manager)

        result = store.load_token()

        self.assertTrue(result.success)
        self.assertEqual(result.token, "legacy-token")
        self.assertTrue(result.requires_migration)

    def test_failed_secure_update_does_not_restore_plaintext_fallback(self):
        settings = FakeSettings(
            {AUTH_ID: "legacy1", LEGACY_SESSION_TOKEN: "plain-token"}
        )
        auth_manager = FakeAuthManager()
        auth_manager.add_config(
            "legacy1",
            {LEGACY_AUTH_PASSWORD_KEY: "stored-password"},
        )
        auth_manager.update_fails = True
        store, _, _ = self.make_store(settings, auth_manager)

        result = store.save_token("person@example.com", "access-token")

        self.assertFalse(result.success)
        self.assertTrue(result.plaintext_purged)
        self.assertNotIn(LEGACY_SESSION_TOKEN, settings.values)
        self.assertEqual(settings.value(AUTH_ID), "legacy1")

    def test_unverified_plaintext_cleanup_is_reported(self):
        settings = FailingLegacyRemovalSettings(
            {LEGACY_SESSION_TOKEN: "plain-token"}
        )
        store, _, _ = self.make_store(settings)

        result = store.save_token("person@example.com", "access-token")

        self.assertTrue(result.success)
        self.assertFalse(result.plaintext_purged)
        self.assertEqual(settings.value(LEGACY_SESSION_TOKEN), "plain-token")

    def test_tuple_style_qgis_binding_uses_returned_config_id(self):
        auth_manager = FakeAuthManager()
        auth_manager.tuple_results = True
        auth_manager.store_tuple_without_mutation = True
        store, settings, _ = self.make_store(FakeSettings(), auth_manager)

        result = store.save_token("person@example.com", "access-token")

        self.assertTrue(result.success)
        self.assertEqual(result.auth_id, "auth001")
        self.assertEqual(settings.value(AUTH_ID), "auth001")

    def test_unverifiable_new_config_is_removed_and_not_referenced(self):
        auth_manager = FakeAuthManager()
        auth_manager.omit_access_token_on_full_load = True
        store, settings, _ = self.make_store(FakeSettings(), auth_manager)

        result = store.save_token("person@example.com", "access-token")

        self.assertFalse(result.success)
        self.assertEqual(result.reason, "auth_config_verification_failed")
        self.assertFalse(auth_manager.configs)
        self.assertFalse(settings.value(AUTH_ID, ""))

    def test_replaced_config_is_retained_for_cleanup_retry_when_removal_fails(self):
        settings = FakeSettings({AUTH_ID: "legacy1"})
        auth_manager = FakeAuthManager()
        auth_manager.add_config(
            "legacy1",
            {LEGACY_AUTH_PASSWORD_KEY: "stored-password"},
        )
        auth_manager.base_load_fails.add("legacy1")
        auth_manager.remove_fails.add("legacy1")
        store, _, _ = self.make_store(settings, auth_manager)

        result = store.save_token("person@example.com", "access-token")

        self.assertTrue(result.success)
        self.assertTrue(result.cleanup_pending)
        self.assertEqual(settings.value(AUTH_STALE_IDS), ["legacy1"])
        self.assertNotEqual(settings.value(AUTH_ID), "legacy1")

    def test_all_orphaned_plugin_configs_are_removed_after_verified_store(self):
        settings = FakeSettings()
        auth_manager = FakeAuthManager()
        auth_manager.add_config(
            "legacy1",
            {LEGACY_AUTH_PASSWORD_KEY: "first-password"},
        )
        auth_manager.configs["legacy1"].setName(LEGACY_AUTH_CONFIG_NAME)
        auth_manager.add_config(
            "legacy2",
            {LEGACY_AUTH_PASSWORD_KEY: "second-password"},
        )
        auth_manager.configs["legacy2"].setName(LEGACY_AUTH_CONFIG_NAME)
        auth_manager.add_config("unrelated", {"password": "keep-me"})
        auth_manager.configs["unrelated"].setName("Another service")
        store, _, _ = self.make_store(settings, auth_manager)

        result = store.save_token("person@example.com", "access-token")

        self.assertTrue(result.success)
        current_id = settings.value(AUTH_ID)
        self.assertEqual(auth_manager.configs[current_id].name(), AUTH_CONFIG_NAME)
        self.assertNotIn("legacy1", auth_manager.configs)
        self.assertNotIn("legacy2", auth_manager.configs)
        self.assertIn("unrelated", auth_manager.configs)


class SessionSecretBoundarySourceTest(unittest.TestCase):
    def test_session_manager_never_writes_a_token_to_qgssettings(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "utils" / "SessionManager.py").read_text(encoding="utf-8")
        self.assertNotIn("setValue(SESSION_TOKEN", source)
        self.assertNotIn("settings.value(SESSION_TOKEN, None)", source)

    def test_login_does_not_persist_the_entered_password(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "login_dialog.py").read_text(encoding="utf-8")
        self.assertNotIn("save_credentials", source)
        self.assertNotIn("password, api_token", source)

    def test_property_cache_key_does_not_derive_from_token(self):
        root = Path(__file__).resolve().parents[1]
        source = (
            root / "modules" / "Property" / "property_service.py"
        ).read_text(encoding="utf-8")
        self.assertIn("SessionManager.session_signature()", source)
        self.assertNotIn("[-12:]", source)


if __name__ == "__main__":
    unittest.main()
