import os

from .constants.module_icons import VALISEE_V_ICON_NAME
from .constants.file_paths import QssPaths
from .constants.settings_keys import SettingsService
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QStackedWidget, QWidget
from PyQt5.QtGui import QMouseEvent
from .widgets.FooterWidget import FooterWidget
from .widgets.HeaderWidget import HeaderWidget
# Removed unused: from qgis.PyQt.QtWidgets import QDialog as QgisQDialog

from .modules.projects.ProjectsUi import ProjectsModule
from .modules.contract.ContractUi import ContractsModule
from .modules.Property.PropertyUI import PropertyModule
from .modules.Settings.SettingsUI import SettingsModule
from .modules.signaltest.SignalTestModule import SignalTestModule

from .widgets.WelcomePage import WelcomePage

from .utils.help.ShowHelp import ShowHelp
from .widgets.theme_manager import ThemeManager
from .utils.WindowManagerMinMax import WindowManagerMinMax
from .languages.language_manager import LanguageManager
from .languages.translation_keys import TranslationKeys
from .module_manager import ModuleManager
from .widgets.sidebar import Sidebar
from .utils.dialog_geometry_watcher import DialogGeometryWatcher
        
from .utils.SessionManager import SessionManager
from .utils.url_manager import Module
from qgis.core import QgsSettings

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QSizePolicy



# Shared managers for all modules
theme_manager = ThemeManager()


# Mapping from unified search "type" values to our internal Module enum.
# Extend this mapping as you add support for more module types.
MODULE_SEARCH_TO_ENUM = {
    "PROJECTS": Module.PROJECT,
    "CONTRACTS": Module.CONTRACT,
    "PROPERTIES": Module.PROPERTY,
}


class PluginDialog(QDialog):
    @staticmethod
    def get_instance():
        return PluginDialog._instance
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PluginDialog, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, parent=None):
        super().__init__(parent)

        # Prevent reinitialization ASAP (no side-effects before this)
        if getattr(self, '_initialized', False):
            return


        # Managers / services first
        self.lang_manager = LanguageManager()  # single instance
        self.moduleManager = ModuleManager(lang_manager=self.lang_manager)
        self.window_manager = WindowManagerMinMax(self)  # single window manager
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
        icon = theme_manager.get_qicon(VALISEE_V_ICON_NAME)
        self.setWindowIcon(icon)

        # Core widgets
        self.moduleStack = QStackedWidget()
        self.moduleStack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.sidebar = Sidebar()
        self.sidebar.itemClicked.connect(self.switchModule)

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
        self.header_widget.helpRequested.connect(self._on_help_requested)
        # When a search result is clicked in the header search, route it either
        # to the appropriate module (PROJECTS / CONTRACTS / PROPERTIES, ...)
        # or to SignalTestModule if no handler exists yet.
        self.header_widget.searchResultClicked.connect(self._on_search_result_clicked)
        dialog_layout.addWidget(self.header_widget)

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
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

        self.destroyed.connect(self._on_destroyed)

        # Mark fully initialized only at the end
        self._initialized = True


    def _on_search_result_clicked(self, module: str, item_id: str, title: str) -> None:
        """Handle a search result click coming from HeaderWidget.

        If we have a corresponding module UI, switch there and open the item
        WITHOUT triggering the normal feed loader. Otherwise, fall back to
        SignalTestModule to inspect the payload.
        """
        try:
            target_enum = MODULE_SEARCH_TO_ENUM.get(module.upper())

            if target_enum is not None:
                target_name = target_enum.name

                # Switch to mapped module (e.g. PROJECT, CONTRACT, PROPERTY)
                self.switchModule(target_name)

                instance = self.moduleManager.getActiveModuleInstance(target_name)
                if instance is None:
                    return

                # Convention: modules expose open_item_from_search(module, id, title)
                if hasattr(instance, "open_item_from_search"):
                    instance.open_item_from_search(module, item_id, title)
                else:
                    # No special handler yet; show payload in signal tester
                    self._show_in_signal_tester(module, item_id, title)
            else:
                # Unknown / unsupported module → show in signal tester
                self._show_in_signal_tester(module, item_id, title)

        except Exception:
            # As a last resort, try to display in signal tester and otherwise ignore
            try:
                self._show_in_signal_tester(module, item_id, title)
            except Exception:
                pass


    def _show_in_signal_tester(self, module: str, item_id: str, title: str) -> None:
        """Switch to SignalTestModule and display the clicked search payload."""
        try:
            self.switchModule(Module.SIGNALTEST.name)
            instance = self.moduleManager.getActiveModuleInstance(Module.SIGNALTEST.name)
            if instance and hasattr(instance, "show_external_signal_payload"):
                instance.show_external_signal_payload(
                    source="header_search_result",
                    module=module,
                    item_id=item_id,
                    title=title,
                )
        except Exception:
            pass


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
        PluginDialog._instance = None

    def loadModules(self):
    
        qss_modular = [QssPaths.MAIN, QssPaths.COMBOBOX, QssPaths.SIDEBAR]
    
        self.moduleManager.registerModule(
            WelcomePage, 
            Module.HOME.name, 
            lang_manager=self.lang_manager,
        )
        self.moduleManager.registerModule(
            SettingsModule, 
            Module.SETTINGS.name, 
            lang_manager=self.lang_manager,
            sidebar_main_item=False
        )
        self.moduleManager.registerModule(
            PropertyModule, 
            Module.PROPERTY.name, 
            qss_files=qss_modular, 
            lang_manager=self.lang_manager,
        )
        self.moduleManager.registerModule(
            ProjectsModule, 
            Module.PROJECT.name, 
            qss_files=qss_modular, 
            language=self.lang_manager,
            supports_statuses=True,
            supports_tags=True,
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
            SignalTestModule,
            Module.SIGNALTEST.name,
            qss_files=qss_modular,
            lang_manager=self.lang_manager,
        )
        

        
         # Signal connections and special setup moved to switchModule for lazy loading

        self.sidebar.populate_from_modules(self.moduleManager)


    def _confirm_unsaved_settings(self) -> bool:
        """Check for unsaved changes in Settings and prompt the user.
        Returns True if navigation may proceed, False to cancel.
        """
        # Get current active module
        active = self.moduleManager.getActiveModule()
        active_name = active.get('name') if active else None

        # Only prompt when currently in Settings and navigating away
        if active_name == Module.SETTINGS.name:
            # Use the settings module instance, not the dialog
            return self.settingsModule.confirm_navigation_away()
        
        # Allow navigation in all other cases
        return True


    def switchModule(self, moduleName):
        import sys
        if not self._confirm_unsaved_settings():
            return

        previous_module = self.moduleManager.getActiveModule()
        previous_module_name = previous_module.get("name") if previous_module else None

        try:
            self.moduleManager.activateModule(moduleName)
            instance = self.moduleManager.getActiveModuleInstance(moduleName)
            if instance is None:
                self._show_welcome()
                raise ValueError(f"Failed to get instance of module '{moduleName}' after activation.")

            # Hook up per-module signals and keep references you use later
            if moduleName == Module.PROPERTY.name:
                instance.property_selected_from_map.connect(self.window_manager._minimize_window)
                instance.property_selection_completed.connect(self.window_manager._restore_window)
            elif moduleName == Module.SETTINGS.name:
                self.settingsModule = instance

            widget = instance.get_widget()
            if self.moduleStack.indexOf(widget) == -1:
                self.moduleStack.addWidget(widget)
            self.moduleStack.setCurrentWidget(widget)

            # Prefer a module display name or a translation map instead of .capitalize()
            display_title = moduleName.lower()
            print(f"Setting header title to: {display_title}")
            self.header_widget.set_title(self.lang_manager.translate(display_title))

            self.sidebar.setActiveModuleOnSidebarButton(moduleName)
            print(f"Switched to module: {moduleName}")
            self.moduleStack.update()
            self.moduleStack.repaint()

        except Exception:
            if previous_module_name:
                self.sidebar.setActiveModuleOnSidebarButton(previous_module_name)
            import traceback
            traceback.print_exc(file=sys.stderr)

    def _show_welcome(self):
        self.switchModule(Module.HOME.name)
      
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
        pref_key = SettingsService().preferred_module().lower() or ""
        if pref_key and pref_key in self.moduleManager.modules:
            self.switchModule(pref_key)
        else:
            self._show_welcome()


    def closeEvent(self, event):
        try:
            settings = getattr(self, 'settingsModule', None)
            if settings and settings.has_unsaved_changes():
                if not settings.confirm_navigation_away(self):
                    event.ignore()
                    return
        except Exception as e:
            print(f"Close prompt failed: {e} - {self.lang_manager.translate_static(TranslationKeys.WILD_CODE_PLUGIN_TITLE)}")

        import gc
        gc.collect()

        # Treat close like a hide so the singleton instance and state
        # are preserved; reopening via the toolbar will simply show it again.
        self.hide()
        event.ignore()

    def _on_help_requested(self):
        active_module = self.moduleManager.getActiveModule()
        ShowHelp.show_help_for_module(active_module)
