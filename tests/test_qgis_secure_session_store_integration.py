from __future__ import annotations

import os
import tempfile
import unittest

from utils.secure_session_store import (
    AUTH_ID,
    AUTH_TOKEN_KEY,
    LEGACY_AUTH_CONFIG_NAME,
    LEGACY_AUTH_PASSWORD_KEY,
    LEGACY_SESSION_TOKEN,
    SecureSessionStore,
)


try:
    from qgis.core import QgsApplication, QgsAuthMethodConfig

    QGIS_AVAILABLE = True
except ImportError:
    QgsApplication = None
    QgsAuthMethodConfig = None
    QGIS_AVAILABLE = False

RUN_QGIS_AUTH_INTEGRATION = (
    QGIS_AVAILABLE
    and os.environ.get("KAVITRO_RUN_QGIS_AUTH_INTEGRATION_TEST") == "1"
)


class MemorySettings:
    def __init__(self, values=None):
        self.values = dict(values or {})

    def value(self, key, default=None, **_kwargs):
        return self.values.get(key, default)

    def setValue(self, key, value):
        self.values[key] = value

    def remove(self, key):
        self.values.pop(key, None)

    def sync(self):
        pass


@unittest.skipUnless(
    RUN_QGIS_AUTH_INTEGRATION,
    "isolated QGIS auth integration test was not explicitly enabled",
)
class QgisSecureSessionStoreIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls.auth_db_dir = tempfile.TemporaryDirectory()
        os.environ["QGIS_AUTH_DB_DIR_PATH"] = cls.auth_db_dir.name
        cls.app = QgsApplication([], False)
        cls.app.initQgis()
        cls.auth_manager = QgsApplication.authManager()
        if not cls.auth_manager.setMasterPassword("kavitro-test-master-password", True):
            raise RuntimeError("Could not initialize isolated QGIS authentication database")

    @classmethod
    def tearDownClass(cls):
        cls.app.exitQgis()
        cls.auth_db_dir.cleanup()

    def test_real_qgis_auth_config_round_trip_removes_legacy_password(self):
        legacy_config = QgsAuthMethodConfig("Basic")
        legacy_config.setName(LEGACY_AUTH_CONFIG_NAME)
        legacy_config.setConfig("username", "legacy@example.com")
        legacy_config.setConfig(LEGACY_AUTH_PASSWORD_KEY, "legacy-password")
        legacy_result = self.auth_manager.storeAuthenticationConfig(legacy_config)
        legacy_success, stored_legacy_config = legacy_result
        self.assertTrue(legacy_success)
        legacy_id = stored_legacy_config.id()
        self.assertTrue(legacy_id)

        settings = MemorySettings({LEGACY_SESSION_TOKEN: "legacy-plaintext-token"})
        store = SecureSessionStore(
            self.auth_manager,
            settings,
            QgsAuthMethodConfig,
        )

        result = store.save_token("integration@example.com", "integration-access-token")

        self.assertTrue(result.success)
        self.assertNotIn(LEGACY_SESSION_TOKEN, settings.values)
        auth_id = settings.value(AUTH_ID)
        self.assertTrue(auth_id)

        loaded = store.load_token()
        self.assertTrue(loaded.success)
        self.assertEqual(loaded.token, "integration-access-token")

        success, config = self.auth_manager.loadAuthenticationConfig(
            auth_id,
            QgsAuthMethodConfig(),
            True,
        )
        self.assertTrue(success)
        self.assertEqual(config.config(AUTH_TOKEN_KEY), "integration-access-token")
        self.assertFalse(config.hasConfig(LEGACY_AUTH_PASSWORD_KEY))
        self.assertNotIn(legacy_id, self.auth_manager.configIds())
        self.assertTrue(self.auth_manager.removeAuthenticationConfig(auth_id))


if __name__ == "__main__":
    unittest.main()
