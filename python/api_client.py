import os
import platform
import json
import re
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
from ..Logs.python_fail_logger import PythonFailLogger
from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys
from ..utils.api_error_handling import (
    ApiError,
    ApiErrorKind,
    MfaSetupNotifier,
    summarize_connection_error,
)
from . import api_rate_limit
from .api_rate_limit import ApiRateLimitError, RequestCancelled
from .api_request_task import send_api_request

class APIClient:
    # A server category is a short code; anything else in the body stays out of the UI and the logs.
    _CATEGORY_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{1,63}$")

    def __init__(self, session_manager=None, config_path=None):
        self.lang = LanguageManager()
        self.session_manager = session_manager or SessionManager()
        self.config_path = ConfigPaths.CONFIG

    def _http_status_error(self, status_code: int) -> ApiError:
        template = self.lang.translate(TranslationKeys.SERVER_REQUEST_FAILED)
        return ApiError(ApiErrorKind.SERVER, template.format(status_code=int(status_code)))

    def _forbidden_error(self, response) -> ApiError:
        reason = self._forbidden_reason(response)
        PythonFailLogger.log("api_request_forbidden", module="api", extra={"reason": reason})
        return ApiError(
            ApiErrorKind.SERVER,
            self.lang.translate(TranslationKeys.SERVER_REQUEST_REFUSED).format(reason=reason),
        )

    def _network_error(self, summary: str = "") -> ApiError:
        template = self.lang.translate(TranslationKeys.NETWORK_ERROR)
        return ApiError(ApiErrorKind.NETWORK, template.format(error=summary))

    @classmethod
    def _forbidden_reason(cls, response) -> str:
        if "challenge" in str(response.headers.get("cf-mitigated", "")).lower():
            return "Cloudflare challenge"
        try:
            body = response.json()
        except ValueError:
            body = None
        extensions = []
        if isinstance(body, dict):
            errors = body.get("errors")
            if isinstance(errors, list):
                extensions = [error.get("extensions") for error in errors if isinstance(error, dict)]
            extensions.append(body.get("extensions"))
        for extension in extensions:
            category = str(extension.get("category") or "") if isinstance(extension, dict) else ""
            if cls._CATEGORY_PATTERN.match(category):
                return category
        return "HTTP 403"

    @staticmethod
    def _on_gui_thread() -> bool:
        try:
            app = QApplication.instance()
            if app is not None:
                return QThread.currentThread() == app.thread()
        except Exception:
            pass
        return True

    def _request_headers(self, require_auth: bool, *, json_body: bool) -> dict:
        headers = {}
        if json_body:
            headers["Content-Type"] = "application/json"
        headers.update({
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": f"QGIS/{Qgis.QGIS_VERSION} ({platform.system()} {platform.release()})",
        })
        if require_auth:
            token = self.session_manager.get_token()
            if token:
                headers["Authorization"] = f"Bearer {token}"
        return headers

    def _execute(
        self,
        query: str,
        prepare_send,
        *,
        require_auth: bool,
        attempts: int,
        json_body: bool,
        is_main_thread: bool,
        retry_rate_limits: bool = True,
    ) -> dict:
        """Send one request and return the whole JSON body, or raise.

        ``prepare_send(api_url, headers)`` returns the callable that does the
        HTTP post. Server errors (5xx) and connection errors are tried again
        up to ``attempts`` times. Rate limits and cancellation pass through
        unchanged; every other failure becomes an ``ApiError`` or keeps its
        own text.
        """
        api_url = GraphQLSettings.graphql_endpoint()
        cost = api_rate_limit.mutation_cost(query)
        for attempt in range(1, attempts + 1):
            headers = self._request_headers(require_auth, json_body=json_body)
            try:
                send = prepare_send(api_url, headers)
                response = send_api_request(
                    send,
                    endpoint=api_url, authorization=headers.get("Authorization"),
                    cost=cost, is_main_thread=is_main_thread,
                    retry_rate_limits=retry_rate_limits,
                )

                if response.status_code == 401:
                    raise ApiError(ApiErrorKind.AUTH, "HTTP 401 Unauthenticated")
                if response.status_code == 403:
                    # Cloudflare, an IP rule or missing access refuse with 403; the session itself is fine.
                    raise self._forbidden_error(response)
                if response.status_code >= 500:
                    if attempt < attempts:
                        time.sleep(0.4 * attempt)
                        continue
                    raise ApiError(ApiErrorKind.SERVER, f"HTTP {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    errors = data.get("errors")
                    if errors:
                        raise self._graphql_error(errors)
                    return data

                # Never carry an untrusted response body into UI or persistent logs.
                raise self._http_status_error(response.status_code)

            except (ApiRateLimitError, RequestCancelled):
                raise

            except requests_exceptions.RequestException as exc:
                if attempt < attempts:
                    time.sleep(0.4 * attempt)
                    continue
                raise self._network_error(summarize_connection_error(str(exc))) from exc

            except ApiError as exc:
                if require_auth and exc.kind == ApiErrorKind.AUTH:
                    # Named before the message turns into the general expiry text, so the log tells why.
                    PythonFailLogger.log("api_session_rejected", module="auth", extra={"cause": str(exc)})
                    # Runs on worker threads too; SessionManager hands the UI part to the GUI thread.
                    SessionManager.invalidate_session(reason=SESSION_REASON_UNAUTHENTICATED)
                    raise ApiError(
                        ApiErrorKind.AUTH,
                        self.lang.translate(TranslationKeys.SESSION_EXPIRED),
                    ) from exc
                raise

            except Exception as exc:
                # Anything else (a body that is no JSON, an unreadable upload) keeps its own text.
                message = str(exc)
                if message:
                    raise Exception(message) from exc
                raise self._network_error() from exc

        raise self._network_error()

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
        payload = {"query": query}
        if variables:
            payload["variables"] = requestBuilder.sanitize_for_json(variables)

        is_main_thread = self._on_gui_thread()
        # Unknown write outcomes require reconciliation, not blind repetition.
        if retry_network is None:
            retry_network = api_rate_limit.mutation_cost(query) == 0
        # Avoid blocking the UI thread with network retries.
        attempts = 3 if retry_network and not is_main_thread else 1

        def prepare_send(api_url, headers):
            return lambda: requests.post(api_url, json=payload, headers=headers, timeout=timeout)

        try:
            data = self._execute(
                query, prepare_send,
                require_auth=require_auth, attempts=attempts, json_body=True,
                is_main_thread=is_main_thread, retry_rate_limits=retry_rate_limits,
            )
        except (ApiRateLimitError, RequestCancelled):
            raise
        except ApiError as exc:
            # A connection failure is raised even here; only the server's answer is wrapped.
            if not with_success or isinstance(exc.__cause__, requests_exceptions.RequestException):
                raise
            return {"success": False, "response": None, "raw": None, "error": str(exc)}
        except Exception as exc:
            if not with_success:
                raise
            return {"success": False, "response": None, "raw": None, "error": str(exc)}

        if with_success:
            response = data if return_raw else (data or {}).get("data", {})
            return {"success": True, "response": response, "raw": data, "error": None}
        return data if return_raw else data.get("data", {})

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
        file_handles = []

        def prepare_send(api_url, headers):
            map_payload: dict[str, list[str]] = {}
            files_payload = {"operations": (None, json.dumps(payload), "application/json")}
            for index, (variable_path, file_path) in enumerate(prepared_files.items()):
                file_key = str(index)
                map_path = variable_path if variable_path.startswith("variables.") else f"variables.{variable_path}"
                map_payload[file_key] = [map_path]

                mime_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
                handle = open(file_path, "rb")
                file_handles.append(handle)
                files_payload[file_key] = (os.path.basename(file_path) or file_key, handle, mime_type)
            files_payload["map"] = (None, json.dumps(map_payload), "application/json")

            def send_files():
                # Each HTTP 429 attempt resends the complete upload.
                for handle in file_handles:
                    handle.seek(0)
                return requests.post(api_url, files=files_payload, headers=headers, timeout=timeout)

            return send_files

        try:
            # A lost upload response can already have created a file. Only a known
            # pre-execution HTTP 429 rejection is safe to retry automatically.
            data = self._execute(
                query, prepare_send,
                require_auth=require_auth, attempts=1, json_body=False,
                is_main_thread=self._on_gui_thread(),
            )
        finally:
            for handle in file_handles:
                try:
                    handle.close()
                except Exception:
                    pass
        return data if return_raw else data.get("data", {})

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
                return self.lang.translate(TranslationKeys.NETWORK_ERROR).format(error="")

    def _graphql_error(self, errors) -> ApiError:
        if self._errors_include_category(errors, "MFA_SETUP_REQUIRED"):
            MfaSetupNotifier.notify()
            return ApiError(
                ApiErrorKind.MFA_SETUP_REQUIRED,
                self.lang.translate(TranslationKeys.MFA_SETUP_REQUIRED),
            )
        if self._errors_include_unauthenticated(errors):
            return ApiError(ApiErrorKind.AUTH, "GraphQL Unauthenticated")
        message = self._extract_error_message(errors)
        return ApiError(ApiErrorKind.GRAPHQL, message or "GraphQL error")

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
