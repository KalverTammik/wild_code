
from .utils.url_manager import Module

from .constants.module_icons import ModuleIconPaths
from .languages.language_manager import LanguageManager
from .widgets.theme_manager import ThemeManager

MODULES_LIST_BY_NAME = []

class ModuleManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'modules'):
            self.modules = {}  # Dictionary to store modules by name
            self.activeModule = None  # Reference to the currently active module
            self.lang_manager = LanguageManager()
        

    def registerModule(
        self,
        module_class,
        module_name,
        sidebar_main_item=True,
        supports_types=False,
        supports_statuses=False,
        supports_tags=False,
        supports_archive_layer=False,
        module_labels=None,
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
            "module_labels": module_labels or [],
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
            except Exception as exc:
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

            # Register module root with centralized retheme engine
            engine = ThemeManager.get_retheme_engine()
            qss_files = params.get("qss_files") if params else None
            widget = self._get_widget_safe(target_instance)
            after_apply = self._pick_retheme_hook(target_instance, key)
            engine.register(widget, qss_files=qss_files or ThemeManager.module_bundle(), after_apply=after_apply)

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

    def getActiveModuleName(self):  
        """Return the name of the currently active module."""
        if self.activeModule:
            return self.activeModule.get("name")
        return None

    def getModuleSupports(self, moduleName):
        """Return support flags for the specified module."""
        module_data = self.modules.get(moduleName.lower())
        if not module_data:
            return None
        
        types = bool(module_data.get("supports_types", False))
        statuses = bool(module_data.get("supports_statuses", False))
        tags = bool(module_data.get("supports_tags", False))
        archive_layer = bool(module_data.get("supports_archive_layer", False))

        return types, statuses, tags, archive_layer

    def getModuleLabels(self, moduleName):
        module_data = self.modules.get(moduleName.lower())
        if not module_data:
            return []
        return module_data.get("module_labels", [])

    @staticmethod
    def _get_widget_safe(instance):
        getter = getattr(instance, "get_widget", None)
        if callable(getter):
            try:
                return getter()
            except Exception:
                return instance
        return instance

    @staticmethod
    def _pick_retheme_hook(instance, key: str):
        candidates = (
            "retheme",
            f"retheme_{key}",
            f"retheme_{key}s",
        )
        for name in candidates:
            method = getattr(instance, name, None)
            if callable(method):
                return lambda _widget, _theme, m=method: m()
        return None
 