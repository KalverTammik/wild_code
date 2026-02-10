import gc
from functools import partial
from .Logs.switch_logger import SwitchLogger
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .languages.language_manager import LanguageManager
    from .module_manager import ModuleManager
from .constants.module_icons import IconNames
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QStackedWidget, QWidget
from PyQt5.QtGui import QMouseEvent
from .widgets.FooterWidget import FooterWidget
from .widgets.HeaderWidget import HeaderWidget
# Removed unused: from qgis.PyQt.QtWidgets import QDialog as QgisQDialog

from .utils.help.ShowHelp import ShowHelp
from .widgets.theme_manager import ThemeManager
from .ui.window_state.WindowManagerMinMax import WindowManagerMinMax
from .languages.language_manager import LanguageManager
from .languages.translation_keys import TranslationKeys
from .module_manager import ModuleManager
from .widgets.sidebar import Sidebar
from .ui.window_state.dialog_geometry_watcher import DialogGeometryWatcher
from .ui.window_state.dialog_helpers import DialogHelpers
from .utils.SessionManager import SessionUIController
from .ui.modules_registry import ModulesRegistry
        
from .utils.url_manager import Module
from .utils.moduleSwitchHelper import ModuleSwitchHelper

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QSizePolicy

from .utils.search.searchHelpers import SearchUIController
from .modules.Settings.settings_ui_controller import SettingsUIController




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
        self.lang_manager: "LanguageManager" = LanguageManager()
        self.moduleManager: "ModuleManager" = ModuleManager()
        self.retheme_engine = ThemeManager.get_retheme_engine()
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
        self.setWindowTitle(self.lang_manager.translate(TranslationKeys.KAVITRO_PLUGIN_TITLE))
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
            title=self.lang_manager.translate(TranslationKeys.KAVITRO_PLUGIN_TITLE),
            switch_callback=self.apply_theme_toggle,
            logout_callback=self.logout
        )
        self.header_widget.helpRequested.connect(ShowHelp.show_help_for_module)
        self.header_widget.searchResultClicked.connect(
            partial(SearchUIController.handle_search_result, self)
        )
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
            qss_files=None  # use centralized app bundle
        )

        # Register shell widgets for centralized retheming
        self.retheme_engine.register(self, qss_files=ThemeManager.app_bundle())
        self.retheme_engine.register(self.header_widget, qss_files=ThemeManager.app_bundle())
        self.retheme_engine.register(self.sidebar, qss_files=ThemeManager.module_bundle())
        self.retheme_engine.register(self.footer_widget, qss_files=ThemeManager.app_bundle())

        self.loadModules()
        self.sidebar.itemClicked.connect(self._on_sidebar_item_clicked)
        ModuleSwitchHelper.set_dialog_resolver(PluginDialog.get_instance)
        ModuleSwitchHelper.set_settings_confirm_handler(DialogHelpers.confirm_settings_navigation)
        ModuleSwitchHelper.set_settings_focus_handler(DialogHelpers.focus_settings_section)

        self.destroyed.connect(self._on_destroyed)

        # Mark fully initialized only at the end
        self._initialized = True


    def _notify_geometry_update(self, x, y, w, h):
        for cb in self._geometry_update_callbacks:
            try:
                cb(x, y, w, h)

            except Exception as e:
                SwitchLogger.log(
                    "dialog_geometry_callback_failed",
                    module=Module.HOME.value,
                    extra={"error": str(e)},
                )

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
        ModulesRegistry.register_all(self.moduleManager, self)

    def _on_sidebar_item_clicked(self, moduleName):
        ModuleSwitchHelper.switch_module(moduleName, dialog=self)

             
    def apply_theme_toggle(self):
        # Use ThemeManager to toggle theme and update icon
        new_theme = ThemeManager.toggle_theme(
            self,
            self.current_theme,
            self.header_widget.switchButton,
            self.header_widget.logoutButton,
            qss_files=None  # use centralized app bundle
        )
        self.current_theme = new_theme
        self.retheme_engine.retheme_all()

    def mouseMoveEvent(self, event: QMouseEvent):
        super().mouseMoveEvent(event)

    def logout(self):
        SessionUIController.logout(self)

    def showEvent(self, event):
        if not SessionUIController.ensure_logged_in(self):
            return
        if hasattr(self, "footer_widget") and self.footer_widget:
            try:
                self.footer_widget.refresh_versions()
            except Exception:
                pass
        super().showEvent(event)
        SessionUIController.after_show(self)

    def closeEvent(self, event):
        if getattr(self, "_force_close", False):
            event.accept()
            return
        if not SettingsUIController.can_close(self):
            event.ignore()
            return

        gc.collect()
        self.showMinimized()
        event.ignore()
