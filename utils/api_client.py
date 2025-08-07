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
        print("[APIClient] Preparing to send query...")
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        print(f"[APIClient] Payload: {payload}")
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"QGIS/{platform.system()} {platform.release()}"
        }
        print(f"[APIClient] Headers before auth: {headers}")
        if require_auth:
            print("[APIClient] Authentication required, attempting to get token...")
            token = self.session_manager.get_token() if hasattr(self.session_manager, 'get_token') else None
            print(f"[APIClient] Token obtained: {token}")
            if token:
                headers["Authorization"] = f"Bearer {token}"
        print(f"[APIClient] Final headers: {headers}")
        print(f"[APIClient] Sending POST to {self.api_url}")
        try:
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=timeout)
            print(f"[APIClient] Response status code: {response.status_code}")
            print(f"[APIClient] Response text: {response.text}")
            if response.status_code == 200:
                data = response.json()
                print(f"[APIClient] Response JSON: {data}")
                if "errors" in data:
                    print(f"[APIClient] GraphQL errors: {data['errors']}")
                    raise Exception(self.lang.translate("graphql_error").format(error=str(data["errors"])))
                return data.get("data", {})
            else:
                print(f"[APIClient] Non-200 response: {response.text}")
                raise Exception(self.lang.translate("login_failed_response").format(error=response.text))
        except Exception as e:
            print(f"[APIClient] Exception occurred: {e}")
            raise Exception(self.lang.translate("network_error").format(error=str(e)))
