import os
import platform
import json
import time
import requests
from requests import exceptions as requests_exceptions
from qgis.core import Qgis
from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtCore import QThread
from qgis.PyQt.QtWidgets import QApplication
from ..utils.SessionManager import SessionManager
from ..constants.file_paths import ConfigPaths, GraphQLSettings
from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys
from ..utils.api_error_handling import ApiErrorKind, summarize_connection_error, tag_message

class APIClient:
    def __init__(self, session_manager=None, config_path=None):
        self.lang = LanguageManager()
        self.session_manager = session_manager or SessionManager()
        self.config_path = ConfigPaths.CONFIG
       
        # Guard to prevent opening multiple login dialogs simultaneously
        if not hasattr(APIClient, '_login_dialog_open'):
            APIClient._login_dialog_open = False


    def send_query(
        self,
        query: str,
        variables: dict = None,
        *,
        require_auth: bool = True,
        timeout: int = 30,
        return_raw: bool = False,
    ):
        payload = {"query": query}

        if variables:
            sanitized_variables = requestBuilder.sanitize_for_json(variables)
            payload["variables"] = sanitized_variables
       

        # Determine retry behavior.
        is_main_thread = True
        try:
            app = QApplication.instance()
            if app is not None:
                is_main_thread = QThread.currentThread() == app.thread()
        except Exception:
            is_main_thread = True

        auth_attempts = 2 if require_auth else 1
        # Avoid blocking the UI thread with network retries.
        network_attempts = 3 if not is_main_thread else 1
        attempts = max(auth_attempts, network_attempts)
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
                response = requests.post(api_url, json=payload, headers=headers, timeout=timeout)

                if response.status_code in (401, 403):
                    raise Exception(tag_message(ApiErrorKind.AUTH, "Unauthenticated"))

                if response.status_code >= 500:
                    if attempt < network_attempts:
                        time.sleep(0.4 * attempt)
                        continue
                    raise Exception(tag_message(ApiErrorKind.SERVER, f"HTTP {response.status_code}"))

                if response.status_code == 200:
                    data = response.json()
                    errors = data.get("errors")
                    if errors:
                        message = self._extract_error_message(errors)
                        if self._errors_include_unauthenticated(errors):
                            message = tag_message(ApiErrorKind.AUTH, "Unauthenticated")
                        else:
                            message = tag_message(ApiErrorKind.GRAPHQL, message or "GraphQL error")
                        raise Exception(message)
                    return data if return_raw else data.get("data", {})

                # Non-200 HTTP response
                try:
                    body = response.text
                except Exception:
                    body = f"HTTP {response.status_code}"
                template = self.lang.translate(TranslationKeys.LOGIN_FAILED_RESPONSE) or "Login failed: {error}"
                raise Exception(tag_message(ApiErrorKind.SERVER, template.format(error=body)))

            except requests_exceptions.RequestException as exc:
                if attempt < network_attempts:
                    time.sleep(0.4 * attempt)
                    continue
                summary = summarize_connection_error(str(exc))
                template = self.lang.translate(TranslationKeys.NETWORK_ERROR) or "Network error: {error}"
                raise Exception(tag_message(ApiErrorKind.NETWORK, template.format(error=summary)))

            except Exception as exc:
                msg = str(exc)
                last_error = msg

                kind = ApiErrorKind.UNKNOWN
                try:
                    if msg.startswith("[WC-API]") and "[" in msg and "]" in msg:
                        # format: [WC-API][kind] message
                        kind_token = msg.split("]", 2)[1].lstrip("[").rstrip("]").strip().lower()
                        if kind_token in ApiErrorKind._value2member_map_:
                            kind = ApiErrorKind(kind_token)
                except Exception:
                    kind = ApiErrorKind.UNKNOWN

                if require_auth and kind == ApiErrorKind.AUTH:
                    if is_main_thread and attempt < auth_attempts and self._handle_unauthenticated():
                        continue

                    session_text = self.lang.translate(TranslationKeys.SESSION_EXPIRED) or "Session expired"
                    raise Exception(tag_message(ApiErrorKind.AUTH, session_text))

                if msg:
                    raise Exception(msg)

                template = self.lang.translate(TranslationKeys.NETWORK_ERROR) or "Network error: {error}"
                raise Exception(tag_message(ApiErrorKind.NETWORK, template.format(error="")))

        if last_error:
            raise Exception(last_error)
        template = self.lang.translate(TranslationKeys.NETWORK_ERROR) or "Network error: {error}"
        raise Exception(tag_message(ApiErrorKind.NETWORK, template.format(error="")))

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
        if result == True:
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
