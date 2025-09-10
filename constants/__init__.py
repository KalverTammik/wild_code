# Constants package initialization

# Import key constants for easy access
from .layer_constants import PROPERTY_TAG, NEW_PROPERTIES_GROUP, MAILABL_MAIN_GROUP
from .layer_constants import MEMORY_LAYER_SUFFIX, SHP_LAYER_SUFFIX, PROPERTIES_BACKGROUND_STYLE
from .base_paths import CONFIG_PATH
from .module_names import PROJECTS_MODULE, CONTRACT_MODULE, SETTINGS_MODULE, PROPERTY_MODULE

# Re-export for convenience
__all__ = [
    'PROPERTY_TAG',
    'NEW_PROPERTIES_GROUP',
    'MAILABL_MAIN_GROUP',
    'MEMORY_LAYER_SUFFIX',
    'SHP_LAYER_SUFFIX',
    'PROPERTIES_BACKGROUND_STYLE',
    'CONFIG_PATH',
    'PROJECTS_MODULE',
    'CONTRACT_MODULE',
    'SETTINGS_MODULE',
    'PROPERTY_MODULE'
]
