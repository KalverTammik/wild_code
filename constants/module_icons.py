import os
from .base_paths import PLUGIN_ROOT, RESOURCE
from .module_names import SETTINGS_MODULE, PROJECT_CARD_MODULE, PROJECT_FEED_MODULE, JOKE_GENERATOR_MODULE, WEATHER_UPDATE_MODULE, IMAGE_OF_THE_DAY_MODULE, BOOK_QUOTE_MODULE, GPT_ASSISTANT_MODULE, HINNAPAKKUJA_MODULE

class ModuleIconPaths:
    MODULE_ICONS = {
        SETTINGS_MODULE: os.path.join(PLUGIN_ROOT, RESOURCE, "icon.png"),
        PROJECT_CARD_MODULE: os.path.join(PLUGIN_ROOT, RESOURCE, "Valisee.png"),
        PROJECT_FEED_MODULE: os.path.join(PLUGIN_ROOT, RESOURCE, "Valisee_s.png"),
        JOKE_GENERATOR_MODULE: os.path.join(PLUGIN_ROOT, RESOURCE, "eye_icon.png"),
        WEATHER_UPDATE_MODULE: os.path.join(PLUGIN_ROOT, RESOURCE, "weather_icon.png"),
        IMAGE_OF_THE_DAY_MODULE: os.path.join(PLUGIN_ROOT, RESOURCE, "image_of_the_day.png"),
        BOOK_QUOTE_MODULE: os.path.join(PLUGIN_ROOT, RESOURCE, "book_quote.png"),
        GPT_ASSISTANT_MODULE: os.path.join(PLUGIN_ROOT, RESOURCE, "eye_icon.png"),
        HINNAPAKKUJA_MODULE: os.path.join(PLUGIN_ROOT, RESOURCE, "Valisee_u.png"),
    }

    @staticmethod
    def get_module_icon(module_name):
        return ModuleIconPaths.MODULE_ICONS.get(module_name, None)
