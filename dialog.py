import gc


from .constants.file_paths import QssPaths
from .constants.module_icons import IconNames
from .constants.settings_keys import SettingsService
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QStackedWidget, QWidget, QMessageBox
from PyQt5.QtGui import QMouseEvent
from .widgets.FooterWidget import FooterWidget
from .widgets.HeaderWidget import HeaderWidget
# Removed unused: from qgis.PyQt.QtWidgets import QDialog as QgisQDialog

from .modules.projects.ProjectsUi import ProjectsModule
from .modules.projects.FolderNamingRuleDialog import FolderNamingRuleDialog
from .modules.contract.ContractUi import ContractsModule
from .modules.coordination.CoordinationModule import CoordinationModule
from .modules.Property.PropertyUI import PropertyModule
from .modules.Settings.SettingsUI import SettingsModule
from .modules.Settings.setting_keys import SettingDialogPlaceholders
from .modules.signaltest.SignalTestModule import SignalTestModule

from .widgets.WelcomePage import WelcomePage

from .utils.help.ShowHelp import ShowHelp
from .widgets.theme_manager import ThemeManager
from .utils.WindowManagerMinMax import WindowManagerMinMax
from .languages.language_manager import LanguageManager
from .languages.translation_keys import TranslationKeys, DialogLabels
from .module_manager import ModuleManager
from .widgets.sidebar import Sidebar
from .utils.dialog_geometry_watcher import DialogGeometryWatcher
from .utils.Folders.foldersHelpers import FolderHelpers
        
from .utils.SessionManager import SessionManager
from .utils.url_manager import Module
from .utils.moduleSwitchHelper import ModuleSwitchHelper
from qgis.core import QgsSettings

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QSizePolicy

from .utils.search.searchHelpers import SearchHeplpers




# Shared managers for all modules
theme_manager = ThemeManager()

class PluginDialog(QDialog):
    @staticmethod
    def get_instance():
        return PluginDialog._instance
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PluginDialog, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, parent=None):
        super().__init__(parent)

        # Prevent reinitialization ASAP (no side-effects before this)
        if self._initialized:
            return

        self._has_shown = False


        # Managers / services first
        self.lang_manager = LanguageManager()  
        self.moduleManager = ModuleManager()
        self.window_manager = WindowManagerMinMax(self)  
        self._geometry_restored = False

        # Window flags (only once)
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint |
            Qt.WindowCloseButtonHint
        )

        # Title + icon
        self.setWindowTitle(self.lang_manager.translate(TranslationKeys.WILD_CODE_PLUGIN_TITLE))
        icon = theme_manager.get_qicon(IconNames.VALISEE_V_ICON_NAME)
        self.setWindowIcon(icon)

        # Core widgets
        self.moduleStack = QStackedWidget()
        self.moduleStack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


        self._geometry_update_callbacks = []
        self._geometry_watcher = DialogGeometryWatcher(self, on_update=self._notify_geometry_update)

        # Layout
        dialog_layout = QVBoxLayout()
        dialog_layout.setContentsMargins(0, 0, 0, 0)
        dialog_layout.setSpacing(0)

        self.header_widget = HeaderWidget(
            title=self.lang_manager.translate(TranslationKeys.WILD_CODE_PLUGIN_TITLE),
            switch_callback=self.apply_theme_toggle,
            logout_callback=self.logout
        )
        self.header_widget.helpRequested.connect(ShowHelp.show_help_for_module)
        self.header_widget.searchResultClicked.connect(lambda module, item_id, title: SearchHeplpers._on_search_result_clicked(self, module, item_id, title))
        dialog_layout.addWidget(self.header_widget)

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        self.sidebar = Sidebar()
        content_layout.addWidget(self.sidebar)

        center_layout = QVBoxLayout()
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)
        center_layout.addWidget(self.moduleStack)
        self.footer_widget = FooterWidget(show_left=True, show_right=True)
        center_layout.addWidget(self.footer_widget)

        content_widget = QWidget()
        content_widget.setLayout(center_layout)
        content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        content_layout.addWidget(content_widget)

        dialog_layout.addLayout(content_layout)
        self.setLayout(dialog_layout)

        # Initial theme, then modules, then retheme dynamic
        self.current_theme = ThemeManager.set_initial_theme(
            self,
            self.header_widget.switchButton,
            self.header_widget.logoutButton,
            qss_files=[QssPaths.MAIN, QssPaths.COMBOBOX, QssPaths.SIDEBAR, QssPaths.HEADER, QssPaths.FOOTER]
        )

        self.loadModules()
        self._retheme_dynamic_children()
        self.sidebar.itemClicked.connect(lambda moduleName: ModuleSwitchHelper.switch_module(moduleName, dialog=self))

        self.destroyed.connect(self._on_destroyed)

        # Mark fully initialized only at the end
        self._initialized = True


    def _notify_geometry_update(self, x, y, w, h):
        for cb in self._geometry_update_callbacks:
            try:
                cb(x, y, w, h)

            except Exception as e:
                pass

    def subscribe_geometry_updates(self, callback):
        self._geometry_update_callbacks.append(callback)
        # Immediately call with current geometry
        geo = self.geometry()
        callback(geo.x(), geo.y(), geo.width(), geo.height())
        def unsubscribe():
            if callback in self._geometry_update_callbacks:
                self._geometry_update_callbacks.remove(callback)
        return unsubscribe

    def _on_destroyed(self, obj):
        print(f"[dialog] destroyed id={id(self)}")
        PluginDialog._instance = None

    def loadModules(self):
    
        qss_modular = [QssPaths.MAIN, QssPaths.COMBOBOX, QssPaths.SIDEBAR]

        def _pick_folder(_module_key: str, _key: str, current_value: str):
            start_path = current_value or ""
            return FolderHelpers.select_folder_path(self, start_path=start_path)

        def _open_folder_rule(_module_key: str, _key: str, current_value: str):
            print("[DEBUG] Opening folder naming rule dialog")
            dlg = FolderNamingRuleDialog(self.lang_manager, self, initial_rule=current_value or "")
            result = dlg.exec_()
            if result == QDialog.Accepted:
                return dlg.get_rule()
            return current_value
            

            
    
        self.moduleManager.registerModule(
            WelcomePage, 
            Module.HOME.name, 
            lang_manager=self.lang_manager,
        )
        self.moduleManager.registerModule(
            SettingsModule, 
            Module.SETTINGS.name, 
            sidebar_main_item=False
        )
        self.moduleManager.registerModule(
            PropertyModule, 
            Module.PROPERTY.name, 
            qss_files=qss_modular, 
            lang_manager=self.lang_manager,
            supports_archive_layer=True,
            
        )
        self.moduleManager.registerModule(
            ProjectsModule, 
            Module.PROJECT.name, 
            qss_files=qss_modular, 
            language=self.lang_manager,
            supports_statuses=True,
            supports_tags=True,
            module_labels=[
                {"key": SettingDialogPlaceholders.PROJECTS_SOURCE_FOLDER,
                  "title_value": self.lang_manager.translate(DialogLabels.PROJECTS_SOURCE_FOLDER), 
                  "tool": "button",
                  "on_click": _pick_folder},

                {"key": SettingDialogPlaceholders.PROJECTS_TARGET_FOLDER, 
                 "title_value": self.lang_manager.translate(DialogLabels.PROJECTS_TARGET_FOLDER), 
                 "tool": "button",
                 "on_click": _pick_folder},

                {"key": SettingDialogPlaceholders.PROJECTS_PREFERED_FOLDER_NAME_STRUCTURE_RULE,
                    "tool": "button",
                    "title_value": self.lang_manager.translate(DialogLabels.PROJECTS_PREFERED_FOLDER_NAME_STRUCTURE_RULE),
                    "on_click": _open_folder_rule},
            ],
        )
        self.moduleManager.registerModule(
            ContractsModule, 
            Module.CONTRACT.name, 
            qss_files=qss_modular, 
            lang_manager=self.lang_manager,
            supports_types=True,
            supports_statuses=True,
            supports_tags=True,
        )
        self.moduleManager.registerModule(
            CoordinationModule,
            Module.COORDINATION.name,
            qss_files=qss_modular,
            language=self.lang_manager,
            supports_types=True,
            supports_statuses=True,
            supports_tags=True,
            supports_archive_layer=True,
        )
        self.moduleManager.registerModule(
            SignalTestModule,
            Module.SIGNALTEST.name,
            qss_files=qss_modular,
            lang_manager=self.lang_manager,
        )
        
        self.sidebar.populate_from_modules(self.moduleManager)
        
      
    def apply_theme_toggle(self):
        # Use ThemeManager to toggle theme and update icon
        qss_files = [QssPaths.MAIN, QssPaths.COMBOBOX, QssPaths.SIDEBAR, QssPaths.HEADER, QssPaths.MODULE_INFO]
        new_theme = ThemeManager.toggle_theme(
            self,
            self.current_theme,
            self.header_widget.switchButton,
            self.header_widget.logoutButton,
            qss_files=qss_files
        )
        self.current_theme = new_theme

        retheme_targets = (
            ("header_widget", "retheme_header"),
            ("sidebar", "retheme_sidebar"),
            ("projectsModule", "retheme_projects"),
            ("contractsModule", "retheme_contract"),
            ("propertyModule",),  # Uses default "retheme" method
            ("settingsModule", "retheme_settings"),
            ("footer_widget", "retheme_footer"),
        )
        for target in retheme_targets:
            if len(target) == 2:
                attr_name, method_name = target
                self._call_child_retheme(attr_name, method_name)
            else:
                # Single item tuple - use default "retheme" method
                self._call_child_retheme(target[0])

        # Re-theme any dynamically created widgets (like DatesWidget in cards)
        self._retheme_dynamic_children()


    def _call_child_retheme(self, attr_name: str, method_name: str = "retheme") -> None:
        """Call a retheme method on a child widget.
        If method_name is not specified, defaults to 'retheme'.
        """
        try:
            child = getattr(self, attr_name, None)
            if child:
                method = getattr(child, method_name, None)
                if callable(method):
                    method()
        except Exception:
            pass

    def _retheme_dynamic_children(self):
        """Find any child widgets that expose retheme() and call it.
        This is a fallback for dynamic theming discovery.
        """
        try:
            count = 0
            for w in self.findChildren(QWidget):
                rt = getattr(w, 'retheme', None)
                if callable(rt):
                    rt()
                    count += 1
        except Exception:
            pass

    def mouseMoveEvent(self, event: QMouseEvent):
        super().mouseMoveEvent(event)

    def logout(self):
        SessionManager.clear()
        import gc
        gc.collect()
        self.close()

    def showEvent(self, event):
        if not SessionManager().isLoggedIn():
            self.close()
            return
        super().showEvent(event)
        QgsSettings().setValue("session/needs_login", False)
        if self._has_shown and self.moduleManager.getActiveModuleName():
            # Preserve the current active module on subsequent shows
            active_name = self.moduleManager.getActiveModuleName()
            inst = self.moduleManager.getActiveModuleInstance(active_name)
            if inst:
                try:
                    widget = inst.get_widget()
                    if widget:
                        self.moduleStack.setCurrentWidget(widget)
                        self.sidebar.setActiveModuleOnSidebarButton(active_name)
                except Exception:
                    pass
            return

        pref_key = SettingsService().preferred_module().lower() or ""
        if pref_key and pref_key in self.moduleManager.modules:
            ModuleSwitchHelper.switch_module(pref_key, dialog=self)
        else:
            ModuleSwitchHelper.switch_module(Module.HOME.name, dialog=self)
        self._has_shown = True

    def closeEvent(self, event):
        settings = SettingsModule()
        if settings and settings.has_unsaved_changes():
            if not settings.confirm_navigation_away(self):
                event.ignore()
                return

        gc.collect()
        self.hide()
        event.ignore()
