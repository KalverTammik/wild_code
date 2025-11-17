from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea
from PyQt5.QtCore import QCoreApplication, pyqtSignal

from ...widgets.theme_manager import ThemeManager
from .SettingsLogic import SettingsLogic
from ...constants.file_paths import QssPaths
from .cards.UserCard import UserCard, userUtils
from .cards.SettingsModuleCard import SettingsModuleCard
from ...constants.layer_constants import PROPERTY_TAG
from ...utils.url_manager import Module
from ...module_manager import MODULES_LIST_BY_NAME

class SettingsModule(QWidget):
    """
    This module supports dynamic theme switching via ThemeManager.apply_module_style.
    Call retheme_settings() to re-apply QSS after a theme change.
    """
    # Signals for user action buttons
    addShpClicked = pyqtSignal()
    addPropertyClicked = pyqtSignal()
    removePropertyClicked = pyqtSignal()

    def __init__(
            self,
            lang_manager=None,
            qss_files=None
        ):
        super().__init__()

        self.name = Module.SETTINGS.name        # Ensure we always use LanguageManager
        
        self.lang_manager = lang_manager
        # Logic layer
        self.logic = SettingsLogic()
        self._cards = []
        self._initialized = False
        self._pending_changes = False
        self._pending_settings = {}
        self._original_settings = {}
        # Confirm buttons across cards
        self._confirm_btns = []  # deprecated for modules; kept for user card only
        self._user_confirm_btn = None
        # Modules available for module-specific cards
        self._module_cards = {}
        self._module_metadata = {}  # Store module metadata including supports_types
        # Selected property layer for operations
        self._selected_property_layer = None        
        self.setup_ui()
        # Centralized theming
        ThemeManager.apply_module_style(self, [QssPaths.SETUP_CARD])

    def setup_ui(self):
        root = QVBoxLayout(self)
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.cards_container = QWidget(self)
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(6, 6, 6, 6)
        self.cards_layout.setSpacing(6)
        self.cards_layout.addStretch(1)
        self.scroll_area.setWidget(self.cards_container)
        root.addWidget(self.scroll_area)

        # Add one User card first
        user_card = self._build_user_setup_card()
        self._cards.append(user_card)
        self.cards_layout.insertWidget(0, user_card)

    def _build_user_setup_card(self) -> QWidget:
        card = UserCard(self.lang_manager)
        card.confirm_button().clicked.connect(self._on_confirm_clicked)
        card.preferredChanged.connect(self._on_user_preferred_changed)
        card.layerSelected.connect(self._on_layer_selected)
        
        self._user_confirm_btn = card.confirm_button()
        self._confirm_btns = [self._user_confirm_btn]
        # Keep references needed for labels and later use
        self._user_card = card
        # Load original settings and set initial layer selection
        self._apply_original_layer_selection()

        return card

    def _build_module_cards(self):
        # Remove existing module cards first
        for name, card in list(self._module_cards.items()):
            card.setParent(None)
        self._module_cards.clear()
        # Rebuild _cards to keep first (user) card, then module cards
        self._cards = self._cards[:1]
        insert_index = 1
        for module_name in MODULES_LIST_BY_NAME:
            if module_name == Module.HOME.name.capitalize():
                continue
            card = self._generate_module_card(module_name)
            self._module_cards[module_name] = card
            self.cards_layout.insertWidget(insert_index, card)
            self._cards.append(card)
            insert_index += 1
            ThemeManager.apply_module_style(card, [QssPaths.SETUP_CARD])
            QCoreApplication.processEvents()

    def _generate_module_card(self, module_name: str) -> QWidget:
 
        translated = self.lang_manager.translate(module_name.capitalize())

        from ...module_manager import ModuleManager
        res = ModuleManager().getModuleSupports(module_name, Types=True, Status=True)
        if res is not None:
            supports_types, supports_statuses = res
            card = SettingsModuleCard(self.lang_manager, module_name, translated, supports_types, supports_statuses)
        else:
            card = SettingsModuleCard(self.lang_manager, module_name, translated)
 
        card.pendingChanged.connect(lambda dirty, cnf_btn=card.confirm_button(): self._on_module_pending_changed(dirty, cnf_btn))
        card.confirm_button().clicked.connect(self._on_confirm_clicked)
 
        return card

    def activate(self):        
        # Load user data once when activated
        abilities = userUtils.load_user(self._user_card.lbl_name,
                                    self._user_card.lbl_email,
                                    self._user_card.lbl_roles,
                                    self.lang_manager)
        subjects = userUtils.abilities_to_subjects(abilities)
        #print(f"[SettingsUI] extracted subjects: {subjects}")
        if Module.PROPERTY.value.capitalize() in subjects:
            print("✅ User has Property access!")
            self._has_property_rights = True
        else:
            print("❌ User does NOT have Property access")
            self._has_property_rights = False
                        
        access_map = self.logic.get_module_access_from_abilities(subjects)
        update_permissions = self.logic.get_module_update_permissions(subjects)
        #print(f"[SettingsUI] Setting access_map: {access_map}")
        self._user_card.set_access_map(access_map)
        self._user_card.set_update_permissions(update_permissions)
        self.logic.load_original_settings()
        # Reflect original preferred; None -> no checkbox selected
        self._user_card.set_preferred(self.logic.get_original_preferred())
        self._set_dirty(False)
        if not self._initialized:
            self._initialized = True
            self._build_module_cards()
     
    def deactivate(self):
        # Deactivate module cards to free memory
        for card in self._module_cards.values():
            try:
                card.on_settings_deactivate()
            except Exception:
                pass

    def reset(self):
        pass

    def run(self):
        pass

    def get_widget(self):
        """Return self as the widget for module system compatibility."""
        return self

    def retheme_settings(self):
        # Re-theme all existing cards
        for card in self._cards:
            ThemeManager.apply_module_style(card, [QssPaths.SETUP_CARD])


    # --- Handling unsaved changes ---
    def apply_pending_changes(self):
        self.logic.apply_pending_changes()

        # Recompute only for user card; module cards update themselves via pendingChanged
        self._set_dirty(self.logic.has_unsaved_changes())

    def revert_pending_changes(self):
        self.logic.revert_pending_changes()
        self._user_card.revert(self.logic.get_original_preferred())
        for card in self._module_cards.values():
            card.revert()
        self._set_dirty(False)

    def _on_user_preferred_changed(self, module_name):
        """Signal handler from UserCard when preferred module checkbox selection changes."""
        # module_name can be a string or None (cleared selection -> Welcome page)
        self.logic.set_pending_preferred(module_name)
        self._update_dirty_state()


    def _on_confirm_clicked(self):
        self.apply_pending_changes()

    def _on_module_pending_changed(self, dirty: bool, confirm_btn):
        try:
            confirm_btn.setVisible(dirty)
            confirm_btn.setEnabled(dirty)
        except Exception:
            pass
        # also update global dirty state to guard navigation
        self._update_dirty_state()

    def _update_dirty_state(self):
        # Combine user-card dirty with module cards dirty
        dirty = self.logic.has_unsaved_changes() or self._any_module_dirty()
        self._set_dirty(dirty)

    def _set_dirty(self, dirty: bool):
        self._pending_changes = bool(dirty)
        # Only toggle the user card confirm here
        btn = self._user_confirm_btn
        if btn is not None:
            try:
                btn.setVisible(self._pending_changes)
                btn.setEnabled(self._pending_changes)
            except Exception:
                pass

    def has_unsaved_changes(self) -> bool:
        # Combine user logic dirty with module card pending state
        try:
            logic_dirty = self.logic.has_unsaved_changes()
            module_dirty = self._any_module_dirty()
            return bool(logic_dirty or module_dirty)
        except Exception:
            # If logic fails, just check module cards
            try:
                return self._any_module_dirty()
            except Exception:
                # If everything fails, assume no changes
                return False

    def _any_module_dirty(self) -> bool:
        """Check if any module cards have pending changes."""
        for card in self._module_cards.values():
            if card.has_pending_changes():
                return True
        return False



    # --- Property Management ---
    def _on_layer_selected(self, layer):
        """Signal handler for layer selection in UserCard."""
        # Remove tag from previously selected layer if it exists
        if self._selected_property_layer and self._selected_property_layer != layer:
            try:
                self._selected_property_layer.setCustomProperty(PROPERTY_TAG, None)
            except Exception as e:
                print(f"Warning: Could not remove property tag from previous layer: {e}")

        if layer:
            #print(f"DEBUG: Layer selected in UserCard: {layer.name()}")
            # Store the selected layer for use in property operations
            self._selected_property_layer = layer
            # Set the property tag on the selected layer
            try:
                layer.setCustomProperty(PROPERTY_TAG, "true")
            except Exception as e:
                print(f"Warning: Could not set property tag on layer: {e}")
            # Set pending layer selection (will be saved on confirm)
            self.logic.set_pending_property_layer_id(layer.id())
            # Update dirty state
            self._update_dirty_state()
        else:
            print("DEBUG: No layer selected in UserCard")
            self._selected_property_layer = None
            # Set pending layer selection to None
            self.logic.set_pending_property_layer_id(None)
            # Update dirty state
            self._update_dirty_state()

    def set_main_property_layer(self, layer):
        """Set the main property layer."""
        if self._user_card and layer:
            self._user_card.layer_selector.setSelectedLayerId(layer.id())
        elif self._user_card:
            self._user_card.layer_selector.clearSelection()

    def clear_main_property_layer(self):
        """Clear the main property layer selection."""
        if self._user_card:
            self._user_card.clear_main_property_layer()

    def confirm_navigation_away(self) -> bool:
        """Handle unsaved changes prompt when navigating away from Settings.
        
        Args:
            parent_dialog: The parent dialog for QMessageBox
            
        Returns:
            True if navigation may proceed, False to cancel
        """
        if not self.has_unsaved_changes():
            return True
            
        try:
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
                self.apply_pending_changes()
                return True
            elif clicked == discard_btn:
                self.revert_pending_changes()
                return True
            else:
                # Cancel
                return False
        except Exception as e:
            print(f"Settings navigation prompt failed: {e}", "error")
            return True

    # --- Helpers ---

    def _apply_original_layer_selection(self):
        """Apply the original property layer selection to the UserCard."""
        try:
            original_layer_id = self.logic.get_original_property_layer_id()
            if original_layer_id and self._user_card:
                self._user_card.layer_selector.setSelectedLayerId(original_layer_id)
                #print(f"Applied original property layer ID: {original_layer_id}")
        except Exception as e:
            print(f"Error applying original layer selection: {e}")
