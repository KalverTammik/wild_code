from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea
from PyQt5.QtCore import QCoreApplication, pyqtSignal
from ...languages.language_manager import LanguageManager
from ...widgets.theme_manager import ThemeManager
from .SettingsLogic import SettingsLogic
from ...constants.file_paths import QssPaths
from .cards.UserCard import UserCard
from .cards.ModuleCard import ModuleCard
from ...constants.layer_constants import PROPERTY_TAG

class SettingsUI(QWidget):
    """
    This module supports dynamic theme switching via ThemeManager.apply_module_style.
    Call retheme_settings() to re-apply QSS after a theme change.
    """
    # Signals for user action buttons
    addShpClicked = pyqtSignal()
    addPropertyClicked = pyqtSignal()
    removePropertyClicked = pyqtSignal()
    def __init__(self, qss_files=None):
        super().__init__()
        from ...module_manager import SETTINGS_MODULE
        self.name = SETTINGS_MODULE
        # Ensure we always use LanguageManager
        
        self.lang_manager = LanguageManager()
        # Logic layer
        self.logic = SettingsLogic()
        self._cards = []
        self._initialized = False
        self._user_loaded = False
        self._pending_changes = False
        self._pending_settings = {}
        self._original_settings = {}
        # Confirm buttons across cards
        self._confirm_btns = []  # deprecated for modules; kept for user card only
        self._user_confirm_btn = None
        # Modules available for module-specific cards
        self._available_modules = []
        self._module_cards = {}
        # Selected property layer for operations
        self._selected_property_layer = None
        self.setup_ui()
        # Centralized theming
        ThemeManager.apply_module_style(self, [QssPaths.SETUP_CARD])

    def setup_ui(self):
        root = QVBoxLayout(self)
        # Scrollable area for setup cards
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
        # Apply card-specific theming if available

        ThemeManager.apply_module_style(self, [QssPaths.SETUP_CARD])

        # Build module-specific cards if already known
        if self._available_modules:
            self._build_module_cards()

    def retheme_settings(self):
 
        # Apply main module styling
        ThemeManager.apply_module_style(self, [QssPaths.SETUP_CARD])


    def _build_user_setup_card(self) -> QWidget:
        card = UserCard(self.lang_manager)
        # Wire confirm button
        card.confirm_button().clicked.connect(self._on_confirm_clicked)
        # When user selects a preferred module, update logic + dirty state
        card.preferredChanged.connect(self._on_user_preferred_changed)
        # When user clicks module settings button
        card.moduleSettingsClicked.connect(self._on_module_settings_clicked)
        # Connect action buttons
        card.addShpClicked.connect(self._on_add_shp_clicked)
        card.addPropertyClicked.connect(self._on_add_property_clicked)
        card.removePropertyClicked.connect(self._on_remove_property_clicked)
        # Connect layer selection
        card.layerSelected.connect(self._on_layer_selected)
        # Track only the user confirm here
        self._user_confirm_btn = card.confirm_button()
        self._confirm_btns = [self._user_confirm_btn]
        # Keep references needed for labels and later use
        self._user_card = card

        # Load original settings and set initial layer selection
        self._load_original_settings()
        self._apply_original_layer_selection()

        return card

    def _build_module_cards(self):
        # Remove existing module cards first
        for name, card in list(self._module_cards.items()):
            card.setParent(None)
        self._module_cards.clear()
        # Rebuild _cards to keep first (user) card, then module cards
        self._cards = self._cards[:1]
        # Insert after the first card (user card)
        insert_index = 1
        for module_name in self.logic.get_available_modules():
            card = self._build_module_card(module_name)
            self._module_cards[module_name] = card
            self.cards_layout.insertWidget(insert_index, card)
            self._cards.append(card)
            insert_index += 1
            try:
                ThemeManager.apply_module_style(card, [QssPaths.SETUP_CARD])
            except Exception:
                pass
            QCoreApplication.processEvents()

    def _build_module_card(self, module_name: str) -> QWidget:
        translated = self.lang_manager.sidebar_button(module_name)
        card = ModuleCard(self.lang_manager, module_name, translated)
        card.confirm_button().clicked.connect(self._on_confirm_clicked)
        # wire pending state from module cards to their own confirm buttons
        try:
            card.pendingChanged.connect(lambda dirty, cnf_btn=card.confirm_button(): self._on_module_pending_changed(dirty, cnf_btn))
        except Exception:
            pass
        # Do NOT add module confirm buttons to global list
        return card

    def set_available_modules(self, module_names):
        # Expect a list of internal module names to show cards for
        module_names = module_names or []
        # Keep local for building cards
        seen = set()
        ordered = []
        for n in module_names:
            if n not in seen:
                seen.add(n)
                ordered.append(n)
        self._available_modules = ordered
        # Inform logic for access calculation
        self.logic.set_available_modules(ordered)
        if getattr(self, '_initialized', False):
            self._build_module_cards()

    def activate(self):
        if not self._initialized:
            self._initialized = True
            if self._available_modules:
                self._build_module_cards()
        # Build a single shared snapshot of the layer tree for all ModuleCards
        try:
            from ...widgets.layer_dropdown import build_snapshot_from_project
            shared_snapshot = build_snapshot_from_project()
        except Exception:
            shared_snapshot = []
        # Load user data once when activated
        if not getattr(self, '_user_loaded', False):
            try:
                user = self.logic.load_user(self.lang_manager)
                self._user_card.set_user(user)
                role_names = self.logic.parse_roles(user.get("roles"))
                self._user_card.set_roles(role_names)
                access_map = self.logic.get_module_access_from_abilities(user.get("abilities"))
                update_permissions = self.logic.get_module_update_permissions(user.get("abilities"))
                self._user_card.set_access_map(access_map, label_resolver=self.lang_manager.sidebar_button)
                self._user_card.set_update_permissions(update_permissions)
                self._load_original_settings()
                # Reflect original preferred; None -> no checkbox selected
                self._user_card.set_preferred(self.logic.get_original_preferred())
                self._user_loaded = True
            except Exception as e:
                # IMPROVED: Since we no longer display user ID, show error in status instead
                self._user_card.set_status_text(f"Error loading user: {str(e)}", visible=True)
        else:
            # Ensure UI shows the current original preferred
            self._user_card.set_preferred(self.logic.get_original_preferred())
            self._set_dirty(False)
        # Activate module cards (lazy layer menus)
        for card in getattr(self, '_module_cards', {}).values():
            try:
                if hasattr(card, 'on_settings_activate'):
                    card.on_settings_activate(snapshot=shared_snapshot)
            except Exception:
                pass

    def deactivate(self):
        # Deactivate module cards to free memory
        for card in getattr(self, '_module_cards', {}).values():
            try:
                if hasattr(card, 'on_settings_deactivate'):
                    card.on_settings_deactivate()
            except Exception:
                pass

    def reset(self):
        pass

    def run(self):
        pass

    def get_widget(self):
        return self



    def apply_pending_changes(self):
        self.logic.apply_pending_changes()
        self._user_card.apply()
        for card in getattr(self, '_module_cards', {}).values():
            try:
                if hasattr(card, 'apply'):
                    card.apply()
            except Exception:
                pass
        # Recompute only for user card; module cards update themselves via pendingChanged
        self._set_dirty(self.logic.has_unsaved_changes())

    def revert_pending_changes(self):
        self.logic.revert_pending_changes()
        self._user_card.revert(self.logic.get_original_preferred())
        for card in getattr(self, '_module_cards', {}).values():
            try:
                if hasattr(card, 'revert'):
                    card.revert()
            except Exception:
                pass
        self._set_dirty(False)

    def _any_module_dirty(self) -> bool:
        for card in getattr(self, '_module_cards', {}).values():
            try:
                if hasattr(card, 'has_pending_changes') and card.has_pending_changes():
                    return True
            except Exception:
                pass
        return False

    def _on_user_preferred_changed(self, module_name):
        """Signal handler from UserCard when preferred module checkbox selection changes."""
        # module_name can be a string or None (cleared selection -> Welcome page)
        self.logic.set_pending_preferred(module_name)
        self._update_dirty_state()

    def _on_module_settings_clicked(self, module_name):
        """Signal handler from UserCard when module settings button is clicked."""
        print(f"DEBUG: Opening settings for module: {module_name}")
        
        # For Property module, show a welcome message
        if module_name == PROPERTY_MODULE:
            from PyQt5.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Property Settings")
            msg.setText("Welcome to Property Settings!\n\nHere you can configure property-related settings.")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        else:
            print(f"Settings for {module_name} not implemented yet")

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

    def _on_add_shp_clicked(self):
        """Signal handler for Add SHP file button."""
        #print("DEBUG: Add SHP file button clicked")
        # Use the clean SHPLayerLoader pattern
        from ...utils.SHPLayerLoader import SHPLayerLoader

        loader = SHPLayerLoader(self)
        success = loader.load_shp_layer()

        if success:
            print("SHP imported as memory layer in 'Uued kinnistud', ready for your workflows.")
            # After successful SHP loading, open the Add Property dialog
            self._open_add_property_dialog()

    def _open_add_property_dialog(self):
        """Open the Add Property dialog after SHP loading"""
        try:
            from ...widgets.AddUpdatePropertyDialog import AddPropertyDialog

            dialog = AddPropertyDialog(self)
            dialog.propertyAdded.connect(self._on_property_from_dialog_added)
            dialog.exec_()

        except Exception as e:
            print(f"Error opening add property dialog: {e}")

    def _on_property_from_dialog_added(self, property_data):
        """Handle property added from dialog after SHP loading"""
        print(f"Property added after SHP loading: {property_data}")
        # Here you can add logic to associate the property with the loaded SHP layer

    def _on_add_property_clicked(self):
        """Signal handler for Add property button."""
        print("DEBUG: Add property button clicked")
        # Emit signal for parent to handle
        self.addPropertyClicked.emit()
        # Property addition logic is now handled by PropertyManagement widget

    def _on_remove_property_clicked(self):
        """Signal handler for Remove property button."""
        print("DEBUG: Remove property button clicked")
        # Emit signal for parent to handle
        self.removePropertyClicked.emit()
        # Property removal logic is now handled by PropertyManagement widget

    def _update_dirty_state(self):
        # Combine user-card dirty with module cards dirty
        dirty = self.logic.has_unsaved_changes() or self._any_module_dirty()
        self._set_dirty(dirty)

    def _set_dirty(self, dirty: bool):
        self._pending_changes = bool(dirty)
        # Only toggle the user card confirm here
        btn = getattr(self, '_user_confirm_btn', None)
        if btn is not None:
            try:
                btn.setVisible(self._pending_changes)
                btn.setEnabled(self._pending_changes)
            except Exception:
                pass

    def has_unsaved_changes(self) -> bool:
        # Combine user logic dirty with module card pending state
        try:
            return bool(self.logic.has_unsaved_changes() or self._any_module_dirty())
        except Exception:
            return self.logic.has_unsaved_changes()


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

    # --- Helpers ---
    def _load_original_settings(self):
        """Load original settings (preferred module) into logic."""
        try:
            self.logic.load_original_settings()
        except Exception:
            # Ignore; default None is acceptable
            pass

    def _apply_original_layer_selection(self):
        """Apply the original property layer selection to the UserCard."""
        try:
            original_layer_id = self.logic.get_original_property_layer_id()
            if original_layer_id and self._user_card:
                self._user_card.layer_selector.setSelectedLayerId(original_layer_id)
                #print(f"Applied original property layer ID: {original_layer_id}")
        except Exception as e:
            print(f"Error applying original layer selection: {e}")
