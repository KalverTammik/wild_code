import json
import os
from .base_paths import PLUGIN_ROOT, CONFIG_DIR, RESOURCE, STYLES, TYPE_QUERIES, PYTHON, CONNECTED_DATA
from .base_paths import QUERIES, GRAPHQL, USER_QUERIES, PROJECT_QUERIES, CONTRACT_QUERIES, EASEMENT_QUERIES, TAGS_QUERIES, STATUS_QUERIES, TASK_QUERIES, COORDINATION_QUERIES, SUBMISSION_QUERIES, SPECIFICATION_QUERIES, PROPERTIES_QUERIES

# GraphQL query folder paths for each module (standards-compliant)
class QueryPaths:
    STATUSES = os.path.join(PLUGIN_ROOT,PYTHON, QUERIES, GRAPHQL, STATUS_QUERIES)
    USER = os.path.join(PLUGIN_ROOT, PYTHON, QUERIES, GRAPHQL, USER_QUERIES)
    PROJECT = os.path.join(PLUGIN_ROOT, PYTHON, QUERIES, GRAPHQL, PROJECT_QUERIES)
    CONTRACT = os.path.join(PLUGIN_ROOT, PYTHON, QUERIES, GRAPHQL, CONTRACT_QUERIES)
    STATUS = os.path.join(PLUGIN_ROOT, PYTHON, QUERIES, GRAPHQL, STATUS_QUERIES)
    EASEMENT = os.path.join(PLUGIN_ROOT, PYTHON, QUERIES, GRAPHQL, EASEMENT_QUERIES)
    TAGS = os.path.join(PLUGIN_ROOT, PYTHON, QUERIES, GRAPHQL, TAGS_QUERIES)
    STATUS = os.path.join(PLUGIN_ROOT, PYTHON, QUERIES, GRAPHQL, STATUS_QUERIES)
    TASK = os.path.join(PLUGIN_ROOT, PYTHON, QUERIES, GRAPHQL, TASK_QUERIES)
    COORDINATION = os.path.join(PLUGIN_ROOT, PYTHON, QUERIES, GRAPHQL, COORDINATION_QUERIES)
    SUBMISSION = os.path.join(PLUGIN_ROOT, PYTHON, QUERIES, GRAPHQL, SUBMISSION_QUERIES)
    SPECIFICATION = os.path.join(PLUGIN_ROOT, PYTHON, QUERIES, GRAPHQL, SPECIFICATION_QUERIES)
    ASBUILT = os.path.join(PLUGIN_ROOT, PYTHON, QUERIES, GRAPHQL, TASK_QUERIES)
    PROPERTY = os.path.join(PLUGIN_ROOT, PYTHON, QUERIES, GRAPHQL, PROPERTIES_QUERIES)
    TYPE = os.path.join(PLUGIN_ROOT, PYTHON, QUERIES, GRAPHQL, TYPE_QUERIES)
# Configuration file paths
    PROPERTIES_CONNECTIONFOLDER = os.path.join(PLUGIN_ROOT, PYTHON, QUERIES, GRAPHQL, CONNECTED_DATA)

    def load_query_properties_connected_elements(self, query_file_name):
        path = QueryPaths.PROPERTIES_CONNECTIONFOLDER
        graphql_path = os.path.join(path, query_file_name)
        #print(f"graphql path: {graphql_path}")
        with open(graphql_path, 'r') as file:
            return file.read()


class ConfigPaths:
    CONFIG = os.path.join(PLUGIN_ROOT, CONFIG_DIR, "config.json")
    METADATA = os.path.join(PLUGIN_ROOT, "metadata.txt")

class GraphQLSettings:
    @staticmethod
    def graphql_endpoint():
        with open(os.path.join(PLUGIN_ROOT, CONFIG_DIR, "config.json"), "r") as json_content:
            config = json.load(json_content)
        return config.get('graphql_endpoint', '')

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
    POPUP = "popup.qss"
    TOOLTIP = "tooltip.qss"
    LAYER_TREE_PICKER = "LayerTreePicker.qss"
    SEARCH_RESULTS_WIDGET = "SearchResultsWidget.qss"
    UNIVERSAL_STATUS_BAR = "UniversalStatusBar.qss"
    PROGRESS_DIALOG = "ProgressDialogModern.qss"
    PROPERTIES_UI = "PropertysUIMain.qss"
    DATES = "dates.qss"
    MODULE_INFO = "ModuleInfo.qss"
    MESSAGE_BOX = "MessageBox.qss"
    SETTING_MODULE_LABELS = "ModuleLabelsWidget.qss"

    LOGIN_THEME = os.path.join(PLUGIN_ROOT, STYLES, "LoginTheme.qss")

# Theme directory paths (for modular theme loading)

    def return_plugin_main_files() -> list:
        """Return list of main QSS files for the plugin."""
        qss_files = [QssPaths.MAIN, QssPaths.COMBOBOX, QssPaths.SIDEBAR]

        return [
            QssPaths.MAIN,
            QssPaths.COMBOBOX,
            QssPaths.SIDEBAR,
        ]
    

    def return_module_main_files() -> list:
        """Return list of main QSS files for modules."""
        return [
            QssPaths.MAIN,
            QssPaths.SIDEBAR,
            QssPaths.HEADER,
            QssPaths.FOOTER,
            QssPaths.MODULE_TOOLBAR,
            QssPaths.MODULE_CARD,
            QssPaths.SETUP_CARD,
            QssPaths.PILLS,
            QssPaths.POPUP,
            QssPaths.TOOLTIP,
            QssPaths.LAYER_TREE_PICKER,
            QssPaths.SEARCH_RESULTS_WIDGET,
            QssPaths.PROGRESS_DIALOG,
            QssPaths.PROPERTIES_UI,
            QssPaths.DATES,
            QssPaths.MODULE_INFO

        ]

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



