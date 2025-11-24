
from .utils.url_manager import Module

from .constants.module_icons import ModuleIconPaths

MODULES_LIST_BY_NAME = []

class ModuleManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, lang_manager=None):
        if not hasattr(self, 'modules'):
            self.modules = {}  # Dictionary to store modules by name
            self.activeModule = None  # Reference to the currently active module
            self.lang_manager = lang_manager
        

    def registerModule(
        self,
        module_class,
        module_name,
        sidebar_main_item=True,
        supports_types=False,
        supports_statuses=False,
        supports_tags=False,
        **init_params,
    ):
        """
        Register a module with its class and init parameters.
        The instance will be created lazily on first activation.
        """
        #print(f"[ModuleManager.registerModule] Registering module: {module_name}")
        self.modules[module_name.lower()] = {
            "module_class": module_class,  # Factory: the class to instantiate
            "init_params": init_params,    # Params for __init__ (e.g., qss_files, lang_manager)
            "instance": None,              # Lazy: created on-demand
            "name": module_name.lower(),
            "icon": ModuleIconPaths.get_module_icon(module_name),
            "display_name": self.lang_manager.translate(module_name.capitalize()),
            "sidebar_main_item": sidebar_main_item,
            "supports_types": supports_types,
            "supports_statuses": supports_statuses,
            "supports_tags": supports_tags,
        }

        if module_name.capitalize() == Module.SETTINGS.value.capitalize() or \
           module_name.capitalize() == Module.HOME.value.capitalize():
            return
        MODULES_LIST_BY_NAME.append(module_name.capitalize())
        #print(f"[ModuleManager.registerModule] Registered module names in MODULES_LIST_BY_NAME: {MODULES_LIST_BY_NAME}")

    def activateModule(self, moduleName):
        """Activate a module by its name, always instantiating a new instance."""
        if moduleName.lower() not in self.modules:
            raise ValueError(f"Module '{moduleName}' not found.")

        module_data = self.modules[moduleName.lower()]
        
        # Deactivate current module if different
        if self.activeModule and self.activeModule != module_data:
            if self.activeModule.get("instance"):
                try:
                    self.activeModule["instance"].deactivate()
                except Exception as e:
                    pass
            # Clear the instance to free memory
            self.activeModule["instance"] = None
        
        # Always create a new instance
        cls = module_data["module_class"]
        params = module_data["init_params"]
        try:
            module_data["instance"] = cls(**params)  # Create new instance
        except Exception as e:
            raise
        
        # Activate the new module
        try:
            self.activeModule = module_data
            module_data["instance"].activate()
        except Exception as e:
            raise

    def getActiveModuleInstance(self, moduleName):
        """Return the instance of the specified active module, or None if not instantiated."""
        if self.activeModule and self.activeModule.get("name") == moduleName.lower():
            return self.activeModule.get("instance")
        return None

    def getActiveModule(self):
        """Return the currently active module."""
        return self.activeModule

    def getModuleSupports(self, moduleName):
        """Return support flags for the specified module."""
        module_data = self.modules.get(moduleName.lower())
        if not module_data:
            return None
        return {
            "types": module_data.get("supports_types", False),
            "statuses": module_data.get("supports_statuses", False),
            "tags": module_data.get("supports_tags", False),
        }
 