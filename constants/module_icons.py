import os
from .base_paths import PLUGIN_ROOT, RESOURCE
from .module_names import SETTINGS_MODULE, PROJECT_CARD_MODULE, PROJECT_FEED_MODULE,  GPT_ASSISTANT_MODULE, USER_TEST_MODULE, DIALOG_SIZE_WATCHER_MODULE

class ModuleIconPaths:
    MODULE_ICONS = {
        SETTINGS_MODULE: os.path.join(PLUGIN_ROOT, RESOURCE, "icon.png"),
        PROJECT_CARD_MODULE: os.path.join(PLUGIN_ROOT, RESOURCE, "Valisee.png"),
        PROJECT_FEED_MODULE: os.path.join(PLUGIN_ROOT, RESOURCE, "Valisee_s.png"),
        GPT_ASSISTANT_MODULE: os.path.join(PLUGIN_ROOT, RESOURCE, "eye_icon.png"),
        USER_TEST_MODULE: os.path.join(PLUGIN_ROOT, RESOURCE, "Valisee_u.png"),
        DIALOG_SIZE_WATCHER_MODULE: os.path.join(PLUGIN_ROOT, RESOURCE, "Valisee_u.png"),  # Use default icon
    }

    @staticmethod
    def get_module_icon(module_name):
        return ModuleIconPaths.MODULE_ICONS.get(module_name, None)
