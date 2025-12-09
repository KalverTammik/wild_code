import os

# Base directory of the plugin
BASE_DIR = os.path.dirname(__file__)
PLUGIN_ROOT = os.path.dirname(os.path.dirname(__file__))

CONFIG_DIR = "config"
RESOURCE = "resources"
STYLES = "styles"
MODULES = "modules"
DATA_DIR = "data"
QUERIES = 'queries'
PYTHON = 'python'
GRAPHQL = 'graphql'
USER_QUERIES = 'user'
PROJECT_QUERIES = 'projects'
CONTRACT_QUERIES = 'contracts'
EASEMENT_QUERIES = 'easements'
TAGS_QUERIES = 'tags'
STATUS_QUERIES = 'statuses'
TASK_QUERIES = 'tasks'
COORDINATION_QUERIES = 'coordinations'
SUBMISSION_QUERIES = 'submissions'
SPECIFICATION_QUERIES = 'specifications'
PROPERTIES_QUERIES = 'properties'
TYPE_QUERIES = 'types'
CONNECTED_DATA = "connectedData"

ICON_FOLDER = "icons"

TO_BE_DELETED = "Kasutusel"

# Configuration path
CONFIG_PATH = os.path.join(PLUGIN_ROOT, CONFIG_DIR)