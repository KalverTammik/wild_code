import os
from .constants.file_paths import StylePaths, QssPaths
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget, QWidget
from PyQt5.QtGui import QMouseEvent
from .widgets.FooterWidget import FooterWidget
from .widgets.HeaderWidget import HeaderWidget
# Removed unused: from qgis.PyQt.QtWidgets import QDialog as QgisQDialog
from qgis.core import QgsMessageLog, Qgis

from .login_dialog import LoginDialog
from .widgets.theme_manager import ThemeManager
from .languages.language_manager import LanguageManager
from .module_manager import ModuleManager, SETTINGS_MODULE
from .widgets.sidebar import Sidebar
from .utils.SessionManager import SessionManager
from .widgets.WelcomePage import WelcomePage

# Shared managers for all modules
lang_manager = LanguageManager()
theme_manager = ThemeManager()


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

        self._geometry_restored = False
        self._debug = False  # toggle to True for verbose logs
        # Enable debug via env or QGIS settings key wild_code/debug
        try:
            from qgis.core import QgsSettings
            dbg_env = os.environ.get("WILDCODE_DEBUG", "0").strip().lower() in ("1", "true", "yes")
            dbg_cfg = str(QgsSettings().value("wild_code/debug", "0")).strip().lower() in ("1", "true", "yes")
            self._debug = bool(dbg_env or dbg_cfg)
        except Exception:
            pass
        if self._debug:
            print("[PluginDialog] __init__ start; debug=ON")
            try:
                ThemeManager.set_debug(True)
            except Exception:
                pass
        self.setWindowTitle(lang_manager.translate("wild_code_plugin_title"))
        from PyQt5.QtWidgets import QSizePolicy
        self.moduleManager = ModuleManager()
        self.moduleStack = QStackedWidget()
        self.moduleStack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.sidebar = Sidebar()
        self.sidebar.itemClicked.connect(self.switchModule)

        # Create welcome page (default view)
        self.welcomePage = WelcomePage(lang_manager=lang_manager, theme_manager=theme_manager)
        self.welcomePage.openSettingsRequested.connect(lambda: self.switchModule(SETTINGS_MODULE))
        # Hide internal debug toggle on WelcomePage; we control via header
        try:
            self.welcomePage.debug_btn.setVisible(False)
        except Exception:
            pass

        # Geometry watcher and update subscribers
        self._geometry_update_callbacks = []
        from wild_code.utils.dialog_geometry_watcher import DialogGeometryWatcher
        self._geometry_watcher = DialogGeometryWatcher(
            self,
            on_update=self._notify_geometry_update
        )

        # Main vertical layout for the dialog
        dialog_layout = QVBoxLayout()
        dialog_layout.setContentsMargins(0, 0, 0, 0)
        dialog_layout.setSpacing(0)

        # Header at the absolute top
        self.header_widget = HeaderWidget(
            title=lang_manager.translate("wild_code_plugin_title"),
            switch_callback=self.toggle_theme,
            logout_callback=self.logout
        )
    # Avalehe nupp päises eemaldatud – kasutame külgriba Avaleht nuppu
        self.header_widget.open_home_callback = self._show_welcome
        # Wire header dev callbacks
        self.header_widget.on_toggle_debug = self._on_header_debug_toggle
        self.header_widget.on_toggle_frame_labels = self._on_header_frames_toggle

        dialog_layout.addWidget(self.header_widget)


        # Central content area (sidebar + main content + right sidebar)
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addWidget(self.sidebar)

        # Center layout: stacked widget + footer
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
        if self._debug:
            print("[PluginDialog] UI skeleton built (header/sidebar/stack/footer)")
        

        self.theme_base_dir = StylePaths.DARK  # Default to dark theme dir; switch as needed
        # Load and apply the theme from QGIS settings (persistent)
        self.current_theme = ThemeManager.set_initial_theme(
            self,
            self.header_widget.switchButton,
            self.theme_base_dir,
            qss_files=[QssPaths.MAIN, QssPaths.SIDEBAR, QssPaths.HEADER, QssPaths.FOOTER]
        )
        if self._debug:
            print(f"[PluginDialog] initial theme loaded: {self.current_theme}")
        self.loadModules()
        # Ensure welcome page is present as the first page in the stack
        try:
            self.moduleStack.insertWidget(0, self.welcomePage)
            self.moduleStack.setCurrentWidget(self.welcomePage)
        except Exception:
            pass
        if self._debug:
            try:
                count = self.moduleStack.count()
            except Exception:
                count = "?"
            print(f"[PluginDialog] welcome page set; moduleStack count={count}")
        self.destroyed.connect(self._on_destroyed)
        # Initialize dev states (debug and frame labels) from settings
        try:
            from qgis.core import QgsSettings
            s = QgsSettings()
            debug_enabled = str(s.value("wild_code/debug", "0")).strip().lower() in ("1", "true", "yes") or bool(os.environ.get("WILDCODE_DEBUG", "0").strip().lower() in ("1", "true", "yes"))
            frames_enabled = str(s.value("wild_code/welcome_frame_labels", "1")).strip().lower() in ("1", "true", "yes")
        except Exception:
            debug_enabled = getattr(self, "_debug", False)
            frames_enabled = True
        try:
            if hasattr(self, 'header_widget'):
                self.header_widget.set_dev_states(debug_enabled, frames_enabled)
        except Exception:
            pass
        # Apply initial dev settings
        self._apply_debug_mode(debug_enabled)
        self._apply_frame_labels(frames_enabled)

    def _notify_geometry_update(self, x, y, w, h):
        for cb in self._geometry_update_callbacks:
            try:
                cb(x, y, w, h)

            except Exception as e:
                pass
        if self._debug:
            print(f"[PluginDialog] geometry update x={x} y={y} w={w} h={h}")

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
        if self._debug:
            print("[PluginDialog] destroyed; singleton cleared")

    def _apply_debug_mode(self, enabled: bool):
        self._debug = bool(enabled)
        try:
            ThemeManager.set_debug(bool(enabled))
        except Exception:
            pass
        # Persist
        try:
            from qgis.core import QgsSettings
            QgsSettings().setValue("wild_code/debug", "1" if enabled else "0")
        except Exception:
            pass
        if getattr(self, "_debug", False):
            print(f"[PluginDialog] debug mode set to {enabled}")

    def _apply_frame_labels(self, enabled: bool):
        # Forward to WelcomePage component
        try:
            if hasattr(self, 'welcomePage') and self.welcomePage:
                self.welcomePage.set_debug(bool(enabled))
        except Exception:
            pass
        # Persist
        try:
            from qgis.core import QgsSettings
            QgsSettings().setValue("wild_code/welcome_frame_labels", "1" if enabled else "0")
        except Exception:
            pass
        if getattr(self, "_debug", False):
            print(f"[PluginDialog] welcome frame labels set to {enabled}")

    def _on_header_debug_toggle(self, enabled: bool):
        self._apply_debug_mode(enabled)

    def _on_header_frames_toggle(self, enabled: bool):
        self._apply_frame_labels(enabled)


    def loadModules(self):
        if getattr(self, "_debug", False):
            print("[PluginDialog] loadModules called")

        from .modules.projects.ProjectsUi import ProjectsModule
        from .modules.contract.ContractUi import ContractUi
        from .modules.Settings.SettingsUI import SettingsUI

        qss_modular = [QssPaths.MAIN, QssPaths.SIDEBAR]
        self.settingsModule = SettingsUI(lang_manager, theme_manager, theme_dir=self.theme_base_dir, qss_files=qss_modular)
        self.projectsModule = ProjectsModule(lang_manager=lang_manager, theme_manager=theme_manager, theme_dir=self.theme_base_dir, qss_files=qss_modular)
        self.contractUI = ContractUi(lang_manager=lang_manager, theme_manager=theme_manager)

        self.moduleManager.registerModule(self.settingsModule)
        self.moduleManager.registerModule(self.projectsModule)

        # Register ContractUi directly with module manager-like structure
        class _ContractWrap:
            def __init__(self, widget):
                self.name = "ContractModule"
                self._w = widget
            def get_widget(self):
                return self._w
            def activate(self):
                if hasattr(self._w, 'activate'):
                    self._w.activate()
            def deactivate(self):
                pass
            def retheme_contract(self):
                if hasattr(self._w, 'retheme_contract'):
                    self._w.retheme_contract()

        self.contractModule = _ContractWrap(self.contractUI)
        self.moduleManager.registerModule(self.contractModule)

        if getattr(self, "_debug", False):
            print("[PluginDialog] Registered modules:")
            for moduleName in self.moduleManager.modules:
                print(f"  - {moduleName}")

        for moduleName, moduleInfo in self.moduleManager.modules.items():
            iconPath = moduleInfo["icon"]
            displayName = moduleInfo["display_name"]
            widget = moduleInfo["module"].get_widget() if hasattr(moduleInfo["module"], "get_widget") else moduleInfo["module"]
            # Ensure widget is an instance, not a class
            if isinstance(widget, type):
                widget = widget()
            if getattr(self, "_debug", False):
                print(f"[PluginDialog] Adding sidebar item: displayName={displayName}, moduleName={moduleName}, iconPath={iconPath}")
            if widget is not None:
                # Do not add Settings to the top module list; it's accessible via header/button
                if moduleName != SETTINGS_MODULE:
                    self.sidebar.addItem(displayName, moduleName, iconPath)
                    # Track modules visible in sidebar for settings module cards
                    try:
                        self._sidebar_modules.append(moduleName)
                    except AttributeError:
                        self._sidebar_modules = [moduleName]
                self.moduleStack.addWidget(widget)

        # Inform Settings module which module cards to show (only those visible in sidebar)
        try:
            visible = getattr(self, '_sidebar_modules', [])
            if hasattr(self, 'settingsModule') and hasattr(self.settingsModule, 'set_available_modules'):
                self.settingsModule.set_available_modules(visible)
                if getattr(self, "_debug", False):
                    print(f"[PluginDialog] settings available modules: {visible}")
        except Exception:
            pass

    def _confirm_unsaved_settings_if_needed(self, target_module) -> bool:
        """Check for unsaved changes in Settings and prompt the user.
        Returns True if navigation may proceed, False to cancel.
        """
        try:
            from PyQt5.QtWidgets import QMessageBox
            settings_widget = getattr(self, 'settingsModule', None)
            if not settings_widget:
                return True
            # Only prompt when currently in Settings and navigating away
            active = self.moduleManager.getActiveModule()
            if not active or active.get('name') != SETTINGS_MODULE or target_module == SETTINGS_MODULE:
                return True
            has_changes = False
            if hasattr(settings_widget, 'has_unsaved_changes') and callable(settings_widget.has_unsaved_changes):
                has_changes = settings_widget.has_unsaved_changes()
            if not has_changes:
                return True
            # Ask user
            mbox = QMessageBox(self)
            mbox.setIcon(QMessageBox.Warning)
            mbox.setWindowTitle(self.tr("Unsaved changes"))
            mbox.setText(self.tr("You have unsaved Settings changes."))
            mbox.setInformativeText(self.tr("Do you want to save your changes or discard them?"))
            save_btn = mbox.addButton(self.tr("Save"), QMessageBox.AcceptRole)
            discard_btn = mbox.addButton(self.tr("Discard"), QMessageBox.DestructiveRole)
            cancel_btn = mbox.addButton(self.tr("Cancel"), QMessageBox.RejectRole)
            mbox.setDefaultButton(save_btn)
            mbox.exec_()
            clicked = mbox.clickedButton()
            if clicked == save_btn:
                if hasattr(settings_widget, 'apply_pending_changes'):
                    settings_widget.apply_pending_changes()
                if getattr(self, "_debug", False):
                    print("[PluginDialog] settings: user chose Save; changes applied")
                return True
            elif clicked == discard_btn:
                if hasattr(settings_widget, 'revert_pending_changes'):
                    settings_widget.revert_pending_changes()
                if getattr(self, "_debug", False):
                    print("[PluginDialog] settings: user chose Discard; changes reverted")
                return True
            else:
                if getattr(self, "_debug", False):
                    print("[PluginDialog] settings: user cancelled navigation")
                return False
        except Exception as e:
            QgsMessageLog.logMessage(f"Prompt failed: {e}", "Wild Code", level=Qgis.Warning)
            return True

    def switchModule(self, moduleName):
        # Intercept navigation for unsaved Settings changes
        if not self._confirm_unsaved_settings_if_needed(moduleName):
            return
        # Home shortcut
        if moduleName == "__HOME__":
            self._show_welcome()
            if hasattr(self, 'sidebar'):
                self.sidebar.clearActive()
                # mark home visually active if method exists
                if hasattr(self.sidebar, 'setHomeActive'):
                    self.sidebar.setHomeActive()
            return
        if getattr(self, "_debug", False):
            print(f"[PluginDialog] switchModule requested: {moduleName}")
        try:
            self.moduleManager.activateModule(moduleName)
            activeModule = self.moduleManager.getActiveModule()
            if activeModule:
                self.moduleStack.setCurrentWidget(activeModule["module"].get_widget())
                # Set header title to module display name
                display_name = activeModule.get("display_name", moduleName)
                self.header_widget.set_title(display_name)
                # Update sidebar active state (also mark Settings button when selected)
                if hasattr(self, 'sidebar'):
                    self.sidebar.setActiveModule(moduleName)
                # Update/repaint
                self.moduleStack.update()
                self.moduleStack.repaint()
                if getattr(self, "_debug", False):
                    print(f"[PluginDialog] switched to: {display_name} ({moduleName})")
            else:
                self._show_welcome()
        except Exception as e:
            QgsMessageLog.logMessage(f"Error switching module: {e}", "Wild Code", level=Qgis.Critical)

    def _show_welcome(self):
        try:
            self.moduleStack.setCurrentWidget(self.welcomePage)
            self.header_widget.set_title(lang_manager.translate("Welcome"))
            if hasattr(self, 'sidebar'):
                self.sidebar.clearActive()
                if hasattr(self.sidebar, 'setHomeActive'):
                    self.sidebar.setHomeActive()
            # Ensure welcome page text uses the current language
            self.welcomePage.retranslate(lang_manager)
            if getattr(self, "_debug", False):
                print("[PluginDialog] showing WelcomePage")
        except Exception:
            pass

    def toggle_theme(self):
        # Use ThemeManager to toggle theme and update icon
        qss_files = [QssPaths.MAIN, QssPaths.SIDEBAR, QssPaths.HEADER]
        if getattr(self, "_debug", False):
            print(f"[PluginDialog] toggle_theme from={self.current_theme}")
        new_theme = ThemeManager.toggle_theme(
            self,
            self.current_theme,
            self.header_widget.switchButton,
            self.theme_base_dir,
            qss_files=qss_files
        )
        self.current_theme = new_theme
        if getattr(self, "_debug", False):
            print(f"[PluginDialog] theme now={self.current_theme}; retheming widgets…")
        # Restyle header after theme toggle
        if hasattr(self, 'header_widget'):
            self.header_widget.retheme_header()
        # Restyle sidebar after theme toggle
        if hasattr(self, 'sidebar'):
            self.sidebar.retheme_sidebar()
        # Restyle project cards after theme toggle
        if hasattr(self, 'projectsModule'):
            self.projectsModule.rethem_project()
        # Restyle contract module after theme toggle
        if hasattr(self, 'contractUI') and hasattr(self.contractUI, 'retheme_contract'):
            self.contractUI.retheme_contract()
        # Restyle settings module after theme toggle
        if hasattr(self, 'settingsModule'):
            self.settingsModule.retheme_settings()
        # Update welcome page texts using current language
        try:
            if hasattr(self, 'welcomePage'):
                self.welcomePage.retranslate(lang_manager)
        except Exception:
            pass
        # Restyle footer after theme toggle
        if hasattr(self, 'footer_widget'):
            self.footer_widget.retheme_footer()
        # Generic retheme pass: call retheme() on any child that provides it
        self._retheme_dynamic_children()


    def _retheme_dynamic_children(self):
        """Find any child widgets that expose retheme() and call it.
        Avoids importing specific widget classes in the dialog.
        """
        try:
            count = 0
            for w in self.findChildren(QWidget):
                rt = getattr(w, 'retheme', None)
                if callable(rt):
                    rt()
                    count += 1
            if getattr(self, "_debug", False):
                print(f"[PluginDialog] retheme sweep done; widgets updated={count}")
        except Exception:
            pass

    def mousePressEvent(self, event: QMouseEvent):
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        super().mouseMoveEvent(event)

    def create_button_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Button Dialog")
        layout = QVBoxLayout(dialog)
        label = QLabel("This is a custom dialog with buttons.", dialog)
        layout.addWidget(label)
        self.okButton = QPushButton("OK", dialog)
        self.cancelButton = QPushButton("Cancel", dialog)
        layout.addWidget(self.okButton)
        layout.addWidget(self.cancelButton)
        ThemeManager.apply_theme(dialog)
        return dialog

    def logout(self):
        SessionManager.clear()
        if getattr(self, "_debug", False):
            print("[PluginDialog] logout; session cleared; closing dialog")
        self.close()

    def showEvent(self, event):
        # Geometry is now handled by the persistent watcher
        if not SessionManager().isLoggedIn():
            self.close()
        else:
            # On first show, if a preferred module exists, activate it; else show welcome
            if not hasattr(self, '_preferred_checked'):
                self._preferred_checked = True
                try:
                    from qgis.core import QgsSettings
                    s = QgsSettings()
                    pref = s.value("wild_code/preferred_module", "")
                    if getattr(self, "_debug", False):
                        print(f"[PluginDialog] showEvent; preferred_module='{pref}'")
                    if pref and pref in self.moduleManager.modules:
                        self.switchModule(pref)
                    else:
                        self._show_welcome()
                except Exception:
                    self._show_welcome()
        super().showEvent(event)

    def closeEvent(self, event):
        # Prompt on close if Settings has unsaved changes
        try:
            settings_widget = getattr(self, 'settingsModule', None)
            if settings_widget and hasattr(settings_widget, 'has_unsaved_changes') and settings_widget.has_unsaved_changes():
                from PyQt5.QtWidgets import QMessageBox
                mbox = QMessageBox(self)
                mbox.setIcon(QMessageBox.Warning)
                mbox.setWindowTitle(self.tr("Unsaved changes"))
                mbox.setText(self.tr("You have unsaved Settings changes."))
                mbox.setInformativeText(self.tr("Do you want to save your changes or discard them?"))
                save_btn = mbox.addButton(self.tr("Save"), QMessageBox.AcceptRole)
                discard_btn = mbox.addButton(self.tr("Discard"), QMessageBox.DestructiveRole)
                cancel_btn = mbox.addButton(self.tr("Cancel"), QMessageBox.RejectRole)
                mbox.setDefaultButton(save_btn)
                mbox.exec_()
                clicked = mbox.clickedButton()
                if clicked == save_btn:
                    if hasattr(settings_widget, 'apply_pending_changes'):
                        settings_widget.apply_pending_changes()
                    event.accept()
                elif clicked == discard_btn:
                    if hasattr(settings_widget, 'revert_pending_changes'):
                        settings_widget.revert_pending_changes()
                    event.accept()
                else:
                    event.ignore()
                    return
        except Exception as e:
            QgsMessageLog.logMessage(f"Close prompt failed: {e}", "Wild Code", level=Qgis.Warning)
        super().closeEvent(event)

    def handleSessionExpiration(self):
        self.close()
        loginDialog = LoginDialog()
