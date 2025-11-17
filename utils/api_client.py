import os
import platform
import json
import requests

from .SessionManager import SessionManager
from ..constants.file_paths import ConfigPaths
from ..languages.language_manager import LanguageManager

class APIClient:
    def __init__(self, session_manager=None, config_path=None):
        self.lang = LanguageManager()
        self.session_manager = session_manager or SessionManager()
        self.config_path = config_path or ConfigPaths.CONFIG
        self.api_url = self._load_api_url()
        # Guard to prevent opening multiple login dialogs simultaneously
        if not hasattr(APIClient, '_login_dialog_open'):
            APIClient._login_dialog_open = False

    def _load_api_url(self):
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            api_url = config.get("graphql_endpoint")
            if not api_url:
                raise ValueError(self.lang.translate("api_endpoint_not_configured"))
            return api_url
        except Exception:
            raise RuntimeError(self.lang.translate("config_error"))

    def send_query(self, query: str, variables: dict = None, operation_name: str = None, require_auth: bool = True, timeout: int = 10):
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        if operation_name:
            payload["operationName"] = operation_name

        attempts = 2 if require_auth else 1
        last_error = None

        for attempt in range(1, attempts + 1):
            headers = {
                "Content-Type": "application/json",
                "User-Agent": f"QGIS/{platform.system()} {platform.release()}"
            }

            if require_auth:
                token = self.session_manager.get_token() if hasattr(self.session_manager, 'get_token') else None
                if token:
                    headers["Authorization"] = f"Bearer {token}"
                else:
                    print("[DEBUG] No auth token available!")

            try:
                response = requests.post(self.api_url, json=payload, headers=headers, timeout=timeout)

                if response.status_code == 200:
                    data = response.json()

                    errors = data.get("errors")
                    if errors:
                        print(f"[DEBUG] GraphQL Errors found: {errors}")
                        first_msg = self._extract_error_message(errors)
                        if require_auth and self._errors_include_unauthenticated(errors):
                            if attempt < attempts and self._handle_unauthenticated():
                                continue
                            first_msg = self.lang.translate("session_expired")
                        raise Exception(first_msg)

                    return data.get("data", {})

                # Non-200 HTTP response
                try:
                    body = response.text
                except Exception:
                    body = f"HTTP {response.status_code}"
                raise Exception(self.lang.translate("login_failed_response").format(error=body))

            except Exception as exc:
                msg = str(exc)
                last_error = msg
                if require_auth and msg and "Unauthenticated" in msg:
                    if attempt < attempts and self._handle_unauthenticated():
                        continue
                    msg = self.lang.translate("session_expired")
                raise Exception(msg or self.lang.translate("network_error").format(error=""))

        raise Exception(last_error or self.lang.translate("network_error").format(error=""))

    def _extract_error_message(self, errors):
        try:
            first = errors[0]
            if isinstance(first, dict):
                return first.get("message") or str(first)
            return str(first)
        except Exception:
            try:
                return json.dumps(errors)
            except Exception:
                return self.lang.translate("network_error").format(error="")

    @staticmethod
    def _errors_include_unauthenticated(errors) -> bool:
        for err in errors or []:
            if isinstance(err, dict):
                msg = err.get("message") or ""
            else:
                msg = str(err)
            if msg and "Unauthenticated" in msg:
                return True
        return False

    def _handle_unauthenticated(self) -> bool:
        """Prompt the user to log in again and return True if a retry should be attempted."""
        from .SessionManager import SessionManager

        result = SessionManager.show_session_expired_dialog(lang_manager=self.lang)
        if result == "login":
            self.open_login_dialog()
            token = self.session_manager.get_token() if hasattr(self.session_manager, 'get_token') else None
            return bool(token)
        return False

    def open_login_dialog(self):
        """Open the LoginDialog so the user can re-authenticate after session expiry.

        Uses a class-level guard to avoid spawning multiple dialogs if multiple
        requests fail concurrently. The dialog itself sets the session via
        SessionManager on successful authentication.
        """
        if getattr(APIClient, '_login_dialog_open', False):
            return
        APIClient._login_dialog_open = True
        try:
            from ..login_dialog import LoginDialog  # inline import: avoid circular at module import time
            dlg = LoginDialog()
            dlg.exec_()
        except Exception as e:
            # Best-effort log without raising a secondary exception
            try:
                from .logger import error as log_error
                log_error(f"Failed to open login dialog: {e}")
            except Exception:
                pass
        finally:
            APIClient._login_dialog_open = False
