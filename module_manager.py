
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
        supports_archive_layer=False,
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
            "display_name": self.lang_manager.translate(module_name.lower()),
            "sidebar_main_item": sidebar_main_item,
            "supports_types": supports_types,
            "supports_statuses": supports_statuses,
            "supports_tags": supports_tags,
            "supports_archive_layer": supports_archive_layer,
        }

        if module_name.capitalize() == Module.SETTINGS.value.capitalize() or \
           module_name.capitalize() == Module.HOME.value.capitalize():
            return
        MODULES_LIST_BY_NAME.append(module_name.capitalize())
        #print(f"[ModuleManager.registerModule] Registered module names in MODULES_LIST_BY_NAME: {MODULES_LIST_BY_NAME}")

    def activateModule(self, moduleName):
        """Activate a module by its name, reusing instances when available."""
        key = moduleName.lower()
        if key not in self.modules:
            raise ValueError(f"Module '{moduleName}' not found.")

        module_data = self.modules[key]
        target_instance = module_data.get("instance")

        # Nothing to do if already active
        if self.activeModule is module_data and target_instance:
            try:
                target_instance.activate()
            except Exception:
                pass
            return

        # Deactivate whatever is currently active
        if self.activeModule and self.activeModule is not module_data:
            current_instance = self.activeModule.get("instance")
            if current_instance:
                try:
                    current_instance.deactivate()
                except Exception:
                    pass

        # Lazily instantiate the target module (only once)
        if target_instance is None:
            cls = module_data["module_class"]
            params = module_data["init_params"]
            target_instance = cls(**params)
            module_data["instance"] = target_instance

        # Activate and mark as current
        self.activeModule = module_data
        try:
            target_instance.activate()
        except Exception as exc:
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
            "archive_layer": module_data.get("supports_archive_layer", False),
        }
 