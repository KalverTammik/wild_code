# Help URLs for different modules
# These URLs point to specific help articles for each module
from ..utils.url_manager import Module

HELP_URLS = {
    Module.PROJECT.value: "https://help.kavitro.com/et/articles/10690178-projektid-qgis-pluginas",
    Module.CONTRACT.value: "https://help.kavitro.com/et/articles/10965497-lepingud-qgis-pluginas",
    Module.SETTINGS.value: "https://help.kavitro.com/et/collections/10606065-kavitro-qgis-plugin",  
    Module.PROPERTY.value: "https://help.kavitro.com/et/articles/10963798-kinnistud-qgis-pluginas", 
}

# Default help URL for unknown modules or when no module is active
DEFAULT_HELP_URL = "https://help.kavitro.com/et"
