import os
import platform
import json
import requests
from qgis.core import Qgis
from qgis.PyQt.QtCore import QVariant
from ..utils.SessionManager import SessionManager
from ..constants.file_paths import ConfigPaths, GraphQLSettings
from ..languages.language_manager import LanguageManager

class APIClient:
    def __init__(self, session_manager=None, config_path=None):
        self.lang = LanguageManager()
        self.session_manager = session_manager or SessionManager()
        self.config_path = ConfigPaths.CONFIG
       
        # Guard to prevent opening multiple login dialogs simultaneously
        if not hasattr(APIClient, '_login_dialog_open'):
            APIClient._login_dialog_open = False


    def send_query(self, query: str, variables: dict = None, require_auth: bool = True):
        payload = {"query": query}

        if variables:
            sanitized_variables = requestBuilder.sanitize_for_json(variables)
            payload["variables"] = sanitized_variables
       

        attempts = 2 if require_auth else 1
        last_error = None

        for attempt in range(1, attempts + 1):
            headers = {
                "Content-Type": "application/json",
                 "User-Agent": f"QGIS/{Qgis.QGIS_VERSION} ({platform.system()} {platform.release()})"
            }

            if require_auth:
                token = self.session_manager.get_token()
                if token:
                    headers["Authorization"] = f"Bearer {token}"
                else:
                    print("[DEBUG] No auth token available!")

            try:
                api_url = GraphQLSettings.graphql_endpoint()
                response = requests.post(api_url, json=payload, headers=headers, timeout=30)

                if response.status_code == 200:
                    data = response.json()
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
        from ..utils.SessionManager import SessionManager

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
                from ..utils.logger import error as log_error
                log_error(f"Failed to open login dialog: {e}")
            except Exception:
                pass
        finally:
            APIClient._login_dialog_open = False


class requestBuilder:
    @staticmethod
    def sanitize_for_json(obj):
        """
        Recursively convert QVariant types to native Python types for JSON serialization.
        """

        if isinstance(obj, dict):
            return {k: requestBuilder.sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [requestBuilder.sanitize_for_json(v) for v in obj]
        elif isinstance(obj, QVariant):
            return None if obj.isNull() else obj.value() 
        elif hasattr(obj, 'value'):
            return obj.value()  # handles QVariant-like types
        return obj
