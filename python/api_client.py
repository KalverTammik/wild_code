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
from ..utils.SessionManager import SESSION_REASON_UNAUTHENTICATED, SessionManager
from ..constants.file_paths import ConfigPaths, GraphQLSettings
from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys
from ..utils.api_error_handling import (
    ApiErrorKind,
    MfaSetupNotifier,
    summarize_connection_error,
    tag_message,
)
from ..Logs.python_fail_logger import PythonFailLogger
from . import api_rate_limit
from .api_rate_limit import ApiRateLimitError, RequestCancelled
from .api_request_task import send_api_request

class APIClient:
    def __init__(self, session_manager=None, config_path=None):
        self.lang = LanguageManager()
        self.session_manager = session_manager or SessionManager()
        self.config_path = ConfigPaths.CONFIG

    def _http_status_error(self, status_code: int) -> str:
        template = self.lang.translate(
            TranslationKeys.SERVER_REQUEST_FAILED,
            fallback="Server request failed (HTTP {status_code}).",
        )
        return tag_message(
            ApiErrorKind.SERVER,
            template.format(status_code=int(status_code)),
        )


    def send_query(
        self,
        query: str,
        variables: dict = None,
        *,
        require_auth: bool = True,
        timeout: int = 30,
        return_raw: bool = False,
        with_success: bool = False,
        retry_network: bool | None = None,
        retry_rate_limits: bool = True,
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

        # Unknown write outcomes require reconciliation, not blind repetition.
        if retry_network is None:
            retry_network = api_rate_limit.mutation_cost(query) == 0
        # Avoid blocking the UI thread with network retries.
        network_attempts = 3 if retry_network and not is_main_thread else 1
        last_error = None

        for attempt in range(1, network_attempts + 1):
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
                response = send_api_request(
                    lambda: requests.post(api_url, json=payload, headers=headers, timeout=timeout),
                    endpoint=api_url, authorization=headers.get('Authorization'),
                    cost=api_rate_limit.mutation_cost(query), is_main_thread=is_main_thread,
                    retry_rate_limits=retry_rate_limits,
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
                        raise Exception(self._tagged_graphql_error(errors))
                    if with_success:
                        return _wrap_success(data)
                    return data if return_raw else data.get("data", {})

                # Never carry an untrusted response body into UI or persistent logs.
                raise Exception(self._http_status_error(response.status_code))

            except (ApiRateLimitError, RequestCancelled):
                raise

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
                    # Runs on worker threads too; SessionManager hands the UI part to the GUI thread.
                    SessionManager.invalidate_session(reason=SESSION_REASON_UNAUTHENTICATED)
                    msg2 = tag_message(
                        ApiErrorKind.AUTH,
                        self.lang.translate(TranslationKeys.SESSION_EXPIRED),
                    )
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

        # A lost upload response can already have created a file. Only a known
        # pre-execution HTTP 429 rejection is safe to retry automatically.
        network_attempts = 1
        last_error = None

        for attempt in range(1, network_attempts + 1):
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

                def send_files():
                    # Each HTTP 429 attempt resends the complete upload.
                    for handle in file_handles:
                        handle.seek(0)
                    return requests.post(api_url, files=files_payload, headers=headers, timeout=timeout)

                response = send_api_request(
                    send_files, endpoint=api_url, authorization=headers.get('Authorization'),
                    cost=api_rate_limit.mutation_cost(query), is_main_thread=is_main_thread,
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
                        raise Exception(self._tagged_graphql_error(errors))
                    return data if return_raw else data.get("data", {})

                # Never carry an untrusted response body into UI or persistent logs.
                raise Exception(self._http_status_error(response.status_code))

            except (ApiRateLimitError, RequestCancelled):
                raise

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
                    # Runs on worker threads too; SessionManager hands the UI part to the GUI thread.
                    SessionManager.invalidate_session(reason=SESSION_REASON_UNAUTHENTICATED)
                    raise Exception(tag_message(
                        ApiErrorKind.AUTH,
                        self.lang.translate(TranslationKeys.SESSION_EXPIRED),
                    ))

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

    def _tagged_graphql_error(self, errors) -> str:
        if self._errors_include_category(errors, "MFA_SETUP_REQUIRED"):
            MfaSetupNotifier.notify()
            return tag_message(
                ApiErrorKind.MFA_SETUP_REQUIRED,
                self.lang.translate(TranslationKeys.MFA_SETUP_REQUIRED),
            )
        if self._errors_include_unauthenticated(errors):
            return tag_message(ApiErrorKind.AUTH, "Unauthenticated")
        message = self._extract_error_message(errors)
        return tag_message(ApiErrorKind.GRAPHQL, message or "GraphQL error")

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

    @staticmethod
    def _errors_include_category(errors, category: str) -> bool:
        for err in errors or []:
            if not isinstance(err, dict):
                continue
            extensions = err.get("extensions")
            if isinstance(extensions, dict) and extensions.get("category") == category:
                return True
        return False


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
