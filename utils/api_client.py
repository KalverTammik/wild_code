import os
import platform
import json
import requests

from .SessionManager import SessionManager
from ..constants.file_paths import ConfigPaths

class APIClient:
    def __init__(self, lang, session_manager=None, config_path=None):
        self.lang = lang
        self.session_manager = session_manager or SessionManager()
        self.config_path = config_path or ConfigPaths.CONFIG
        self.api_url = self._load_api_url()

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

    def send_query(self, query: str, variables: dict = None, require_auth: bool = True, timeout: int = 10):
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"QGIS/{platform.system()} {platform.release()}"
        }
        if require_auth:
            token = self.session_manager.get_token() if hasattr(self.session_manager, 'get_token') else None
            if token:
                headers["Authorization"] = f"Bearer {token}"
        try:
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=timeout)
            if response.status_code == 200:
                data = response.json()
                if "errors" in data:
                    # Print and raise the raw GraphQL errors for debugging
                    print("GraphQL errors:", data["errors"])
                    raise Exception(f"GraphQL errors: {data['errors']}")
                return data.get("data", {})
            else:
                raise Exception(self.lang.translate("login_failed_response").format(error=response.text))
        except Exception as e:
            # Print the raw exception for debugging
            import traceback
            import sys
            tb = traceback.format_exc()
            print(f"APIClient Exception: {e}\n{tb}", file=sys.stderr)
            raise Exception(self.lang.translate("network_error").format(error=str(e)))
