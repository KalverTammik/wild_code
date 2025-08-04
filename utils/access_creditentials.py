import requests, platform
from qgis.core import QgsSettings, Qgis
from ...config.settings import GraphQLSettings
from .FileLoaderHelper import GraphQLQueryLoader
from ...KeelelisedMuutujad.messages import Headings
from ...utils.messagesHelper import ModernMessageDialog
from ...KeelelisedMuutujad.modules import Module

GRAPHQL_ENDPOINT = GraphQLSettings.graphql_endpoint()




class Version:
    @staticmethod
    def get_plugin_version(metadata_file):
        with open(metadata_file, 'r') as f:
            for line in f:
                if line.strip().startswith("version="):
                    return line.strip().split('=')[1]

