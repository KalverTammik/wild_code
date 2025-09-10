import requests, platform, json, os
from qgis.core import QgsSettings, Qgis
from .FileLoaderHelper import GraphQLQueryLoader
from ...KeelelisedMuutujad.messages import Headings
from ...utils.messagesHelper import ModernMessageDialog
from ...KeelelisedMuutujad.modules import Module
from ...constants.file_paths import ConfigPaths

def _load_graphql_endpoint():
    """Load GraphQL endpoint from config file."""
    try:
        with open(ConfigPaths.CONFIG, "r", encoding="utf-8") as f:
            config = json.load(f)
        api_url = config.get("graphql_endpoint")
        if not api_url:
            return "https://api.example.com/graphql"  # fallback
        return api_url
    except Exception:
        return "https://api.example.com/graphql"  # fallback

GRAPHQL_ENDPOINT = _load_graphql_endpoint()




class Version:
    @staticmethod
    def get_plugin_version(metadata_file):
        with open(metadata_file, 'r') as f:
            for line in f:
                if line.strip().startswith("version="):
                    return line.strip().split('=')[1]

