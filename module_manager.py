from .constants.file_paths import ModuleIconPaths


# Define module variables for easier maintenance
SETTINGS_MODULE = "SettingsModule"
PROJECT_CARD_MODULE = "ProjectCardModule"
PROJECT_FEED_MODULE = "ProjectFeedModule"
JOKE_GENERATOR_MODULE = "JokeGeneratorModule"
WEATHER_UPDATE_MODULE = "WeatherUpdateModule"
IMAGE_OF_THE_DAY_MODULE = "ImageOfTheDayModule"
BOOK_QUOTE_MODULE = "BookQuoteModule"
WORKFLOW_DESIGNER_MODULE = "WorkflowDesignerModule"


MODULE_NAMES = {
    SETTINGS_MODULE: "Seaded",
    PROJECT_CARD_MODULE: "Edasi/tagasi andmed",
    PROJECT_FEED_MODULE: "Scrollivad andmed",
    JOKE_GENERATOR_MODULE: "Naljad",
    WEATHER_UPDATE_MODULE: "Ilmateade",  # Added missing module
    IMAGE_OF_THE_DAY_MODULE: "Pildi päev",
    BOOK_QUOTE_MODULE: "Raamatu tsitaat",
    WORKFLOW_DESIGNER_MODULE: "Töövoo kujundaja",
}

class ModuleManager:
    def __init__(self):
        self.modules = {}  # Dictionary to store modules by name
        self.activeModule = None  # Reference to the currently active module

    def registerModule(self, module):
        """Register a new module with its icon and human-readable name."""
        self.modules[module.name] = {
            "module": module,
            "icon": ModuleIconPaths.get_module_icon(module.name),
            "display_name": self.get_module_name(module.name),  # Get human-readable name
        }
    def getModuleIcon(self, moduleName):
        """Retrieve the icon for a registered module."""
        module_info = self.modules.get(moduleName, None)
        if module_info:
            return module_info.get("icon", None)
        return None

    @staticmethod
    def get_module_name(module_name):
        """Retrieve the human-readable name for a given module."""
        return MODULE_NAMES.get(module_name, module_name)  # Default to the module_name if not found
    def activateModule(self, moduleName):
        """Activate a module by name."""
        if moduleName in self.modules:
            if self.activeModule:
                self.activeModule["module"].deactivate()  # Deactivate the current module
            self.activeModule = self.modules[moduleName]
            self.activeModule["module"].activate()  # Activate the new module
        else:
            raise ValueError(f"Module '{moduleName}' not found.")

    def getActiveModule(self):
        """Return the currently active module."""
        return self.activeModule
