import os
from .base_paths import PLUGIN_ROOT, CONFIG_DIR, RESOURCE, STYLES, MODULES
from .module_names import GPT_ASSISTANT_MODULE

# GraphQL query folder paths for each module (standards-compliant)
from .base_paths import QUERIES, GRAPHQL, USER_QUERIES, PROJECT_QUERIES, CONTRACT_QUERIES, EASEMENT_QUERIES, TAGS_QUERIES, STATUS_QUERIES, TASK_QUERIES, COORDINATION_QUERIES, SUBMISSION_QUERIES, SPECIFICATION_QUERIES, PROPERTIES_QUERIES

# GraphQL query folder paths for each module (standards-compliant)
class QueryPaths:
    USER = os.path.join(PLUGIN_ROOT, QUERIES, GRAPHQL, USER_QUERIES)
    PROJECT = os.path.join(PLUGIN_ROOT, QUERIES, GRAPHQL, PROJECT_QUERIES)
    CONTRACT = os.path.join(PLUGIN_ROOT, QUERIES, GRAPHQL, CONTRACT_QUERIES)
    EASEMENT = os.path.join(PLUGIN_ROOT, QUERIES, GRAPHQL, EASEMENT_QUERIES)
    TAGS = os.path.join(PLUGIN_ROOT, QUERIES, GRAPHQL, TAGS_QUERIES)
    STATUS = os.path.join(PLUGIN_ROOT, QUERIES, GRAPHQL, STATUS_QUERIES)
    TASK = os.path.join(PLUGIN_ROOT, QUERIES, GRAPHQL, TASK_QUERIES)
    COORDINATION = os.path.join(PLUGIN_ROOT, QUERIES, GRAPHQL, COORDINATION_QUERIES)
    SUBMISSION = os.path.join(PLUGIN_ROOT, QUERIES, GRAPHQL, SUBMISSION_QUERIES)
    SPECIFICATION = os.path.join(PLUGIN_ROOT, QUERIES, GRAPHQL, SPECIFICATION_QUERIES)
    ASBUILT = os.path.join(PLUGIN_ROOT, QUERIES, GRAPHQL, TASK_QUERIES)
    PROPERTIE = os.path.join(PLUGIN_ROOT, QUERIES, GRAPHQL, PROPERTIES_QUERIES)




# Data paths (for module data files)


# GptAssistant module paths
class GptAssistantPaths:
    ENV = os.path.join(PLUGIN_ROOT, MODULES, GPT_ASSISTANT_MODULE, '.env')
    README = os.path.join(PLUGIN_ROOT, MODULES, GPT_ASSISTANT_MODULE, 'README_QGIS_OPENAI.txt')



# Resource paths (icons, images, etc.)
class ResourcePaths:
    ICON = os.path.join(PLUGIN_ROOT, RESOURCE, "Valisee_u.png")
    EYE_ICON = os.path.join(PLUGIN_ROOT, RESOURCE, "eye_icon.png")
    LIGHTNESS_ICON = os.path.join(PLUGIN_ROOT, RESOURCE, "brightness.png")
    DARKNESS_ICON = os.path.join(PLUGIN_ROOT, RESOURCE, "darkness.png")
    LOGOUT_BRIGHT = os.path.join(PLUGIN_ROOT, RESOURCE, "logout_bright.png")
    LOGOUT_DARK = os.path.join(PLUGIN_ROOT, RESOURCE, "logout_dark.png")

# QSS file names (for modular theme loading)
class QssPaths:
    MAIN = "main.qss"
    SIDEBAR = "sidebar.qss"
    HEADER = "header.qss"
    FOOTER = "footer.qss"
    LOGIN = "login.qss"
    MODULE_TOOLBAR = "ModuleToolbar.qss"
    MODULE_CARD = "ModuleCard.qss"
    SETUP_CARD = "SetupCard.qss"
    LIGHT_THEME = os.path.join(PLUGIN_ROOT, STYLES, "LightTheme.qss")
    DARK_THEME = os.path.join(PLUGIN_ROOT, STYLES, "DarkTheme.qss")
    SIDEBAR_THEME = os.path.join(PLUGIN_ROOT, STYLES, "Sidebar.qss")
    LOGIN_THEME = os.path.join(PLUGIN_ROOT, STYLES, "LoginTheme.qss")

# Theme directory paths (for modular theme loading)
class StylePaths:
    DARK = os.path.join(PLUGIN_ROOT, STYLES, "Dark")
    LIGHT = os.path.join(PLUGIN_ROOT, STYLES, "Light")

# Config, metadata, manuals, etc.
class ConfigPaths:
    CONFIG = os.path.join(PLUGIN_ROOT, CONFIG_DIR, "config.json")
    METADATA = os.path.join(PLUGIN_ROOT, "metadata.txt")
    USER_MANUAL = os.path.join(PLUGIN_ROOT, MODULES, "PizzaOrderModuleUserManual.html")



