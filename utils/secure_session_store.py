"""QGIS Authentication Manager backed storage for Kavitro session tokens.

This module deliberately contains no UI or network code.  It accepts the QGIS
objects as dependencies so the persistence and legacy-migration rules can be
tested without opening a real authentication database.
"""

from typing import Any, NamedTuple, Optional, Tuple


AUTH_ID = "myplugin/auth_id"
AUTH_USERNAME = "myplugin/username"
AUTH_STALE_IDS = "myplugin/stale_auth_ids"

LEGACY_SESSION_TOKEN = "session/token"
AUTH_CONFIG_NAME = "Kavitro session"
LEGACY_AUTH_CONFIG_NAME = "myplugin_session"
AUTH_TOKEN_KEY = "access_token"
LEGACY_AUTH_TOKEN_KEY = "apikey"
LEGACY_AUTH_PASSWORD_KEY = "password"


class SecureTokenLoadResult(NamedTuple):
    success: bool
    token: Optional[str]
    auth_id: str
    requires_migration: bool
    reason: str


class SecureTokenStoreResult(NamedTuple):
    success: bool
    auth_id: str
    cleanup_pending: bool
    plaintext_purged: bool
    reason: str


class SecureSessionStore:
    """Store only the access token in a QGIS protected auth config."""

    def __init__(self, auth_manager: Any, settings: Any, config_factory: Any):
        self.auth_manager = auth_manager
        self.settings = settings
        self.config_factory = config_factory

    @staticmethod
    def _text(value: Any) -> str:
        return str(value or "").strip()

    @staticmethod
    def _call_result(result: Any, fallback_config: Any) -> Tuple[bool, Any]:
        """Normalize QGIS SIP return values across supported bindings."""
        if isinstance(result, tuple):
            success = bool(result[0]) if result else False
            config = fallback_config
            for candidate in result[1:]:
                if hasattr(candidate, "config") and hasattr(candidate, "id"):
                    config = candidate
                    break
            return success, config
        return bool(result), fallback_config

    def _new_config(self, method: Optional[str] = None) -> Any:
        if method:
            try:
                return self.config_factory(method)
            except TypeError:
                config = self.config_factory()
                config.setMethod(method)
                return config
        return self.config_factory()

    def _load_config(self, auth_id: str, *, full: bool) -> Tuple[bool, Any]:
        config = self._new_config()
        try:
            result = self.auth_manager.loadAuthenticationConfig(auth_id, config, full)
        except Exception:
            return False, config
        return self._call_result(result, config)

    @staticmethod
    def _has_config(config: Any, key: str) -> bool:
        try:
            return bool(config.hasConfig(key))
        except (AttributeError, TypeError):
            try:
                return config.config(key, "") != ""
            except TypeError:
                return config.config(key) != ""

    @staticmethod
    def _config_value(config: Any, key: str) -> str:
        try:
            return str(config.config(key, "") or "").strip()
        except TypeError:
            return str(config.config(key) or "").strip()

    @staticmethod
    def _remove_config_value(config: Any, key: str) -> None:
        try:
            config.removeConfig(key)
        except (AttributeError, TypeError):
            config.setConfig(key, "")

    def username(self) -> str:
        return self._text(self.settings.value(AUTH_USERNAME, ""))

    def load_token(self) -> SecureTokenLoadResult:
        auth_id = self._text(self.settings.value(AUTH_ID, ""))
        if not auth_id:
            return SecureTokenLoadResult(False, None, "", False, "auth_id_missing")

        success, config = self._load_config(auth_id, full=True)
        if not success:
            return SecureTokenLoadResult(False, None, auth_id, False, "auth_config_unavailable")

        access_token = self._config_value(config, AUTH_TOKEN_KEY)
        legacy_token = self._config_value(config, LEGACY_AUTH_TOKEN_KEY)
        token = access_token or legacy_token
        if not token:
            return SecureTokenLoadResult(False, None, auth_id, False, "token_missing")

        requires_migration = (
            not access_token
            or self._has_config(config, LEGACY_AUTH_TOKEN_KEY)
            or self._has_config(config, LEGACY_AUTH_PASSWORD_KEY)
        )
        return SecureTokenLoadResult(True, token, auth_id, requires_migration, "")

    def save_token(self, username: str, token: str) -> SecureTokenStoreResult:
        username = self._text(username)
        token = self._text(token)
        if not token:
            return SecureTokenStoreResult(False, "", False, self.purge_legacy_token(), "token_missing")

        existing_id = self._text(self.settings.value(AUTH_ID, ""))
        if existing_id:
            base_loaded, _ = self._load_config(existing_id, full=False)
            if base_loaded:
                full_loaded, config = self._load_config(existing_id, full=True)
                if not full_loaded:
                    return SecureTokenStoreResult(
                        False,
                        existing_id,
                        False,
                        self.purge_legacy_token(),
                        "auth_config_locked",
                    )
                return self._update_existing(existing_id, config, username, token)

        return self._store_new(existing_id, username, token)

    def _prepare_config(self, config: Any, username: str, token: str) -> None:
        config.setName(AUTH_CONFIG_NAME)
        if username:
            config.setConfig("username", username)
        else:
            self._remove_config_value(config, "username")
        config.setConfig(AUTH_TOKEN_KEY, token)
        self._remove_config_value(config, LEGACY_AUTH_TOKEN_KEY)
        self._remove_config_value(config, LEGACY_AUTH_PASSWORD_KEY)

    def _update_existing(
        self,
        auth_id: str,
        config: Any,
        username: str,
        token: str,
    ) -> SecureTokenStoreResult:
        self._prepare_config(config, username, token)
        try:
            updated = self.auth_manager.updateAuthenticationConfig(config)
        except Exception:
            updated = False
        update_succeeded, _ = self._call_result(updated, config)
        if not update_succeeded:
            return SecureTokenStoreResult(
                False,
                auth_id,
                False,
                self.purge_legacy_token(),
                "auth_config_update_failed",
            )

        if not self._verify_config(auth_id, token):
            return SecureTokenStoreResult(
                False,
                auth_id,
                False,
                self.purge_legacy_token(),
                "auth_config_verification_failed",
            )

        plaintext_purged = self._commit_reference(auth_id, username)
        cleanup_pending = self.cleanup_stale_configs()
        return SecureTokenStoreResult(
            True,
            auth_id,
            cleanup_pending,
            plaintext_purged,
            "" if plaintext_purged else "plaintext_cleanup_failed",
        )

    def _store_new(
        self,
        old_auth_id: str,
        username: str,
        token: str,
    ) -> SecureTokenStoreResult:
        config = self._new_config("Basic")
        self._prepare_config(config, username, token)
        try:
            result = self.auth_manager.storeAuthenticationConfig(config)
        except Exception:
            result = False
        stored, returned_config = self._call_result(result, config)
        auth_id = self._text(returned_config.id()) if stored else ""
        if not stored or not auth_id:
            return SecureTokenStoreResult(
                False,
                "",
                False,
                self.purge_legacy_token(),
                "auth_config_store_failed",
            )

        if not self._verify_config(auth_id, token):
            if not self._remove_auth_config(auth_id):
                self._remember_stale_id(auth_id)
            return SecureTokenStoreResult(
                False,
                "",
                False,
                self.purge_legacy_token(),
                "auth_config_verification_failed",
            )

        plaintext_purged = self._commit_reference(auth_id, username)
        if old_auth_id and old_auth_id != auth_id:
            if not self._remove_auth_config(old_auth_id):
                self._remember_stale_id(old_auth_id)
        cleanup_pending = self.cleanup_stale_configs()
        return SecureTokenStoreResult(
            True,
            auth_id,
            cleanup_pending,
            plaintext_purged,
            "" if plaintext_purged else "plaintext_cleanup_failed",
        )

    def _verify_config(self, auth_id: str, expected_token: str) -> bool:
        success, config = self._load_config(auth_id, full=True)
        if not success:
            return False
        return (
            self._config_value(config, AUTH_TOKEN_KEY) == expected_token
            and not self._has_config(config, LEGACY_AUTH_TOKEN_KEY)
            and not self._has_config(config, LEGACY_AUTH_PASSWORD_KEY)
        )

    def _commit_reference(self, auth_id: str, username: str) -> bool:
        self.settings.setValue(AUTH_ID, auth_id)
        if username:
            self.settings.setValue(AUTH_USERNAME, username)
        else:
            self.settings.remove(AUTH_USERNAME)
        return self.purge_legacy_token()

    def purge_legacy_token(self) -> bool:
        """Remove the old plaintext token and verify that no value remains."""
        try:
            self.settings.remove(LEGACY_SESSION_TOKEN)
            self.settings.sync()
            remaining = self._text(self.settings.value(LEGACY_SESSION_TOKEN, ""))
            if remaining:
                self.settings.setValue(LEGACY_SESSION_TOKEN, "")
                self.settings.sync()
                remaining = self._text(self.settings.value(LEGACY_SESSION_TOKEN, ""))
            return not remaining
        except Exception:
            return False

    def _stale_ids(self) -> list:
        raw = self.settings.value(AUTH_STALE_IDS, [])
        if isinstance(raw, str):
            values = [part.strip() for part in raw.split(",")]
        elif isinstance(raw, (list, tuple)):
            values = [self._text(value) for value in raw]
        else:
            values = []
        return [value for value in values if value]

    def _remember_stale_id(self, auth_id: str) -> None:
        auth_id = self._text(auth_id)
        ids = self._stale_ids()
        if auth_id and auth_id not in ids:
            ids.append(auth_id)
        if ids:
            self.settings.setValue(AUTH_STALE_IDS, ids)
        self.settings.sync()

    def cleanup_stale_configs(self) -> bool:
        """Remove replaced and orphaned Kavitro configs; report pending cleanup."""
        current_id = self._text(self.settings.value(AUTH_ID, ""))
        stale_ids = self._stale_ids()
        discovery_failed = False
        try:
            available = self.auth_manager.availableAuthMethodConfigs()
            for auth_id, config in dict(available or {}).items():
                auth_id = self._text(auth_id)
                try:
                    name = self._text(config.name())
                    method = self._text(config.method())
                except Exception:
                    continue
                if (
                    auth_id
                    and auth_id != current_id
                    and method == "Basic"
                    and name in (AUTH_CONFIG_NAME, LEGACY_AUTH_CONFIG_NAME)
                    and auth_id not in stale_ids
                ):
                    stale_ids.append(auth_id)
        except Exception:
            discovery_failed = True

        remaining = []
        for auth_id in stale_ids:
            if auth_id == current_id:
                continue
            if not self._remove_auth_config(auth_id):
                remaining.append(auth_id)
        if remaining:
            self.settings.setValue(AUTH_STALE_IDS, remaining)
        else:
            self.settings.remove(AUTH_STALE_IDS)
        self.settings.sync()
        return bool(remaining) or discovery_failed

    def _remove_auth_config(self, auth_id: str) -> bool:
        try:
            result = self.auth_manager.removeAuthenticationConfig(auth_id)
        except Exception:
            return False
        if isinstance(result, tuple):
            return bool(result[0]) if result else False
        return bool(result)
