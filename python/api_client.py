import os
import platform
import json
import time
import mimetypes
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
from ..Logs.python_fail_logger import PythonFailLogger

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
        with_success: bool = False,
    ):
        def _wrap_success(raw_json: dict):
            if return_raw:
                return {"success": True, "response": raw_json, "raw": raw_json, "error": None}
            return {"success": True, "response": (raw_json or {}).get("data", {}), "raw": raw_json, "error": None}

        def _wrap_error(message: str):
            return {"success": False, "response": None, "raw": None, "error": message}

        payload = {"query": query}

        if variables:
            sanitized_variables = requestBuilder.sanitize_for_json(variables)
            payload["variables"] = sanitized_variables
        api_url = GraphQLSettings.graphql_endpoint()
       

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
                "Accept": "application/json",
                "X-Requested-With": "XMLHttpRequest",
                 "User-Agent": f"QGIS/{Qgis.QGIS_VERSION} ({platform.system()} {platform.release()})"
            }

            if require_auth:
                token = self.session_manager.get_token()
                if token:
                    headers["Authorization"] = f"Bearer {token}"
                else:
                    print("[DEBUG] No auth token available!")

            try:
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
                    if with_success:
                        return _wrap_success(data)
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
                    msg2 = tag_message(ApiErrorKind.AUTH, session_text)
                    if with_success:
                        return _wrap_error(msg2)
                    raise Exception(msg2)

                if msg:
                    if with_success:
                        return _wrap_error(msg)
                    raise Exception(msg)

                template = self.lang.translate(TranslationKeys.NETWORK_ERROR) or "Network error: {error}"
                msg2 = tag_message(ApiErrorKind.NETWORK, template.format(error=""))
                if with_success:
                    return _wrap_error(msg2)
                raise Exception(msg2)

        if last_error:
            if with_success:
                return _wrap_error(last_error)
            raise Exception(last_error)
        template = self.lang.translate(TranslationKeys.NETWORK_ERROR) or "Network error: {error}"
        msg2 = tag_message(ApiErrorKind.NETWORK, template.format(error=""))
        if with_success:
            return _wrap_error(msg2)
        raise Exception(msg2)

    @staticmethod
    def _set_nested_variable(container, path: str, value) -> None:
        parts = [segment for segment in str(path or "").split(".") if segment]
        if parts and parts[0] == "variables":
            parts = parts[1:]
        if not parts:
            return

        target = container
        for part in parts[:-1]:
            if isinstance(target, dict):
                next_target = target.get(part)
                if not isinstance(next_target, (dict, list)):
                    next_target = {}
                    target[part] = next_target
                target = next_target
                continue

            if isinstance(target, list):
                try:
                    index = int(part)
                except (TypeError, ValueError):
                    return
                while len(target) <= index:
                    target.append({})
                next_target = target[index]
                if not isinstance(next_target, (dict, list)):
                    next_target = {}
                    target[index] = next_target
                target = next_target
                continue

            return

        last = parts[-1]
        if isinstance(target, dict):
            target[last] = value
            return

        if isinstance(target, list):
            try:
                index = int(last)
            except (TypeError, ValueError):
                return
            while len(target) <= index:
                target.append(None)
            target[index] = value

    def send_multipart_query(
        self,
        query: str,
        variables: dict = None,
        *,
        file_variables: dict[str, str],
        require_auth: bool = True,
        timeout: int = 120,
        return_raw: bool = False,
    ):
        payload_variables = requestBuilder.sanitize_for_json(variables or {})
        prepared_files: dict[str, str] = {}
        for variable_path, file_path in (file_variables or {}).items():
            normalized_path = str(variable_path or "").strip()
            normalized_file_path = str(file_path or "").strip()
            if not normalized_path or not normalized_file_path:
                continue
            prepared_files[normalized_path] = normalized_file_path
            self._set_nested_variable(payload_variables, normalized_path, None)

        if not prepared_files:
            return self.send_query(
                query,
                variables=payload_variables,
                require_auth=require_auth,
                timeout=timeout,
                return_raw=return_raw,
            )

        payload = {
            "query": query,
            "variables": payload_variables,
        }
        api_url = GraphQLSettings.graphql_endpoint()

        is_main_thread = True
        try:
            app = QApplication.instance()
            if app is not None:
                is_main_thread = QThread.currentThread() == app.thread()
        except Exception:
            is_main_thread = True

        auth_attempts = 2 if require_auth else 1
        network_attempts = 3 if not is_main_thread else 1
        attempts = max(auth_attempts, network_attempts)
        last_error = None

        for attempt in range(1, attempts + 1):
            headers = {
                "Accept": "application/json",
                "X-Requested-With": "XMLHttpRequest",
                "User-Agent": f"QGIS/{Qgis.QGIS_VERSION} ({platform.system()} {platform.release()})"
            }

            if require_auth:
                token = self.session_manager.get_token()
                if token:
                    headers["Authorization"] = f"Bearer {token}"

            file_handles = []
            files_payload = {}
            try:
                map_payload: dict[str, list[str]] = {}
                files_payload["operations"] = (None, json.dumps(payload), "application/json")
                files_payload["map"] = (None, json.dumps(map_payload), "application/json")
                for index, (variable_path, file_path) in enumerate(prepared_files.items()):
                    file_key = str(index)
                    map_path = variable_path if variable_path.startswith("variables.") else f"variables.{variable_path}"
                    map_payload[file_key] = [map_path]

                    mime_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
                    handle = open(file_path, "rb")
                    file_handles.append(handle)
                    files_payload[file_key] = (
                        os.path.basename(file_path) or file_key,
                        handle,
                        mime_type,
                    )

                files_payload["map"] = (None, json.dumps(map_payload), "application/json")

                response = requests.post(
                    api_url,
                    files=files_payload,
                    headers=headers,
                    timeout=timeout,
                )

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

            finally:
                for handle in file_handles:
                    try:
                        handle.close()
                    except Exception:
                        pass

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
        """Handle unauthenticated response by invalidating the session."""
        SessionManager.invalidate_session(reason="401")
        return False

    def open_login_dialog(self):
        """Open login dialog via SessionManager (guarded)."""
        SessionManager.request_login(reason="401")


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
