import os
from .base_paths import PLUGIN_ROOT, CONFIG_DIR, RESOURCE, STYLES, MODULES
try:
    from .module_names import GPT_ASSISTANT_MODULE
except Exception:
    GPT_ASSISTANT_MODULE = None

# GraphQL query folder paths for each module (standards-compliant)
from .base_paths import QUERIES, GRAPHQL, USER_QUERIES, PROJECT_QUERIES, CONTRACT_QUERIES, EASEMENT_QUERIES, TAGS_QUERIES, STATUS_QUERIES, TASK_QUERIES, COORDINATION_QUERIES, SUBMISSION_QUERIES, SPECIFICATION_QUERIES, PROPERTIES_QUERIES

# GraphQL query folder paths for each module (standards-compliant)
class QueryPaths:
    STATUSES = os.path.join(PLUGIN_ROOT, QUERIES, GRAPHQL, STATUS_QUERIES)
    USER = os.path.join(PLUGIN_ROOT, QUERIES, GRAPHQL, USER_QUERIES)
    PROJECT = os.path.join(PLUGIN_ROOT, QUERIES, GRAPHQL, PROJECT_QUERIES)
    CONTRACT = os.path.join(PLUGIN_ROOT, QUERIES, GRAPHQL, CONTRACT_QUERIES)
    STATUS = os.path.join(PLUGIN_ROOT, QUERIES, GRAPHQL, STATUS_QUERIES)
    EASEMENT = os.path.join(PLUGIN_ROOT, QUERIES, GRAPHQL, EASEMENT_QUERIES)
    TAGS = os.path.join(PLUGIN_ROOT, QUERIES, GRAPHQL, TAGS_QUERIES)
    STATUS = os.path.join(PLUGIN_ROOT, QUERIES, GRAPHQL, STATUS_QUERIES)
    TASK = os.path.join(PLUGIN_ROOT, QUERIES, GRAPHQL, TASK_QUERIES)
    COORDINATION = os.path.join(PLUGIN_ROOT, QUERIES, GRAPHQL, COORDINATION_QUERIES)
    SUBMISSION = os.path.join(PLUGIN_ROOT, QUERIES, GRAPHQL, SUBMISSION_QUERIES)
    SPECIFICATION = os.path.join(PLUGIN_ROOT, QUERIES, GRAPHQL, SPECIFICATION_QUERIES)
    ASBUILT = os.path.join(PLUGIN_ROOT, QUERIES, GRAPHQL, TASK_QUERIES)
    PROPERTIE = os.path.join(PLUGIN_ROOT, QUERIES, GRAPHQL, PROPERTIES_QUERIES)
    PROPERTIES = os.path.join(PLUGIN_ROOT, QUERIES, GRAPHQL, PROPERTIES_QUERIES)




# Configuration file paths
class ConfigPaths:
    CONFIG = os.path.join(PLUGIN_ROOT, CONFIG_DIR, "config.json")
    METADATA = os.path.join(PLUGIN_ROOT, "metadata.txt")


# GptAssistant module paths (optional; defined only if module name exists)
if GPT_ASSISTANT_MODULE:
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
    COMBOBOX = "ComboBox.qss"
    MAIN = "main.qss"
    SIDEBAR = "sidebar.qss"
    HEADER = "header.qss"
    FOOTER = "footer.qss"
    DEV_CONTROLS = "DevControls.qss"
    LOGIN = "login.qss"
    MODULE_TOOLBAR = "ModuleToolbar.qss"
    MODULE_CARD = "ModuleCard.qss"
    SETUP_CARD = "SetupCard.qss"
    PILLS = "pills.qss"
    MODULES_MAIN = "ModulesMain.qss"
    TOOLTIP = "tooltip.qss"
    LAYER_TREE_PICKER = "LayerTreePicker.qss"
    SEARCH_RESULTS_WIDGET = "SearchResultsWidget.qss"
    UNIVERSAL_STATUS_BAR = "UniversalStatusBar.qss"
    LIGHT_THEME = os.path.join(PLUGIN_ROOT, STYLES, "LightTheme.qss")
    DARK_THEME = os.path.join(PLUGIN_ROOT, STYLES, "DarkTheme.qss")
    SIDEBAR_THEME = os.path.join(PLUGIN_ROOT, STYLES, "Sidebar.qss")
    LOGIN_THEME = os.path.join(PLUGIN_ROOT, STYLES, "LoginTheme.qss")

# Theme directory paths (for modular theme loading)
class StylePaths:
    DARK = os.path.join(PLUGIN_ROOT, STYLES, "Dark")
    LIGHT = os.path.join(PLUGIN_ROOT, STYLES, "Light")

# QML style file paths (for layer symbology)
class QmlPaths:
    PROPERTIES_BACKGROUND_NEW = os.path.join(PLUGIN_ROOT, "QGIS_styles", "Properties_background_new.qml")
    PROPERTIES_BACKGROUND = os.path.join(PLUGIN_ROOT, "QGIS_styles", "Properties_backgrund.qml")
    MAAMET_IMPORT = os.path.join(PLUGIN_ROOT, "QGIS_styles", "Maa_amet_temp_layer.qml")
    EASETMENT_DRAINAGE = os.path.join(PLUGIN_ROOT, "QGIS_styles", "Easement_Drainage.qml")
    EASEMENT_PROPERTIES = os.path.join(PLUGIN_ROOT, "QGIS_styles", "Easement_Properties.qml")


def get_style(style_name: str) -> str:
    """
    Get QML style file path by name.

    Args:
        style_name: Name of the style (e.g., 'properties_background_new', 'maa_met_import')

    Returns:
        str: Full path to the QML style file

    Raises:
        ValueError: If style name is not recognized
    """
    style_map = {
        'properties_background_new': QmlPaths.PROPERTIES_BACKGROUND_NEW,
        'properties_background': QmlPaths.PROPERTIES_BACKGROUND,
        'maa_amet_import': QmlPaths.MAAMET_IMPORT,
        'easement_drainage': QmlPaths.EASETMENT_DRAINAGE,
        'easement_properties': QmlPaths.EASEMENT_PROPERTIES,
    }

    if style_name not in style_map:
        available_styles = list(style_map.keys())
        raise ValueError(f"Unknown style name '{style_name}'. Available styles: {available_styles}")

    return style_map[style_name]



