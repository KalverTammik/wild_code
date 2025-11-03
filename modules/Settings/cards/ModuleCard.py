from PyQt5.QtWidgets import QVBoxLayout, QLabel, QFrame, QHBoxLayout, QGroupBox
from PyQt5.QtCore import pyqtSignal
from .BaseCard import BaseCard
from ....widgets.layer_dropdown import LayerTreePicker
from ....widgets.StatusFilterWidget import StatusFilterWidget

from qgis.core import QgsSettings
from ....widgets.TypeFilterWidget import TypeFilterWidget
from ....constants.module_icons import ModuleIconPaths
            

class ModuleCard(BaseCard):
    pendingChanged = pyqtSignal(bool)

    def __init__(self, lang_manager, module_name: str, translated_name: str):
        # Get module icon for the header
        
        icon_path = ModuleIconPaths.get_module_icon(module_name)
        
        super().__init__(lang_manager, translated_name, icon_path)
        self.module_name = module_name
        self._snapshot = None
        
        # Setup reset button in footer
        reset_btn = self.reset_button()
        reset_btn.setToolTip(self.lang_manager.translate("Reset all settings for this module to default values"))
        reset_btn.setVisible(True)
        reset_btn.clicked.connect(self._on_reset_settings)
        
        # Both pickers use the popup tree UX
        self._element_picker = None
        self._archive_picker = None
        # Track originals/pending separately
        self._orig_element_id = ""
        self._orig_archive_id = ""
        self._pend_element_id = ""
        self._pend_archive_id = ""
        self._orig_show_numbers = True
        self._pend_show_numbers = True
        self._orig_status_preferences = set()
        self._pend_status_preferences = set()
        self._orig_type_preferences = set()
        self._pend_type_preferences = set()
        self._build_ui()

    # --- UI ---
    def _build_ui(self):
        cw = self.content_widget()
        cl = QVBoxLayout(cw)
        cl.setContentsMargins(1, 1, 1, 1)
        cl.setSpacing(6)  # Increased spacing between groups for better separation

        # Layer configurations container - arrange main and archive side by side
        layers_container = QFrame(cw)
        layers_container.setObjectName("LayersContainer")
        layers_layout = QHBoxLayout(layers_container)
        layers_layout.setContentsMargins(0, 0, 0, 0)
        layers_layout.setSpacing(8)  # Spacing between main and archive groups

        # Main layer group
        main_group = QGroupBox(self.lang_manager.translate("Modules main layer"), layers_container)
        main_group.setObjectName("MainLayerGroup")
        main_layout = QHBoxLayout(main_group)  # Changed to horizontal layout
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(6)  # Spacing between dropdown and explanation

        # Left side - Element picker
        self._element_picker = LayerTreePicker(main_group, placeholder=self.lang_manager.translate("Select layer"))
        self._element_picker.layerIdChanged.connect(self._on_element_selected)
        self._element_picker.retheme()  # Apply styling immediately after creation
        main_layout.addWidget(self._element_picker, 2)  # Give more space to dropdown

        # Right side - Explanation text
        explanation1 = QLabel("See on teie mooduli põhikiht. Valige kiht, mis sisaldab peamisi andmeid, millega soovite töötada. See säte määrab, millist kihti kasutatakse alusena kõigi mooduli toimingute jaoks.", main_group)
        explanation1.setObjectName("GroupExplanation")
        explanation1.setWordWrap(True)
        explanation1.setStyleSheet("color: #888; font-size: 11px; padding: 4px 0px;")
        explanation1.setMinimumWidth(200)  # Ensure minimum width for readability
        main_layout.addWidget(explanation1, 1)  # Equal space for explanation

        layers_layout.addWidget(main_group)

        # Archive layer group
        archive_group = QGroupBox(self.lang_manager.translate("Archive layer"), layers_container)
        archive_group.setObjectName("ArchiveLayerGroup")
        archive_layout = QHBoxLayout(archive_group)  # Changed to horizontal layout
        archive_layout.setContentsMargins(4, 4, 4, 4)
        archive_layout.setSpacing(6)

        # Left side - Archive picker
        self._archive_picker = LayerTreePicker(archive_group, placeholder=self.lang_manager.translate("Select layer"))
        self._archive_picker.layerIdChanged.connect(self._on_archive_selected)
        self._archive_picker.retheme()  # Apply styling immediately after creation
        archive_layout.addWidget(self._archive_picker, 2)

        # Right side - Explanation text
        explanation2 = QLabel("See valikuline arhiivikiht salvestab ajaloolisi või varukoopia andmeid. Kasutage seda, kui vajate muudatuste või andmete ajalooliste versioonide eraldi kirjet.", archive_group)
        explanation2.setObjectName("GroupExplanation")
        explanation2.setWordWrap(True)
        explanation2.setStyleSheet("color: #888; font-size: 11px; padding: 4px 0px;")
        explanation2.setMinimumWidth(200)
        archive_layout.addWidget(explanation2, 1)

        layers_layout.addWidget(archive_group)

        cl.addWidget(layers_container)

        # Options container - arrange preferences in rows
        options_container = QFrame(cw)
        options_container.setObjectName("OptionsContainer")
        options_layout = QVBoxLayout(options_container)
        options_layout.setContentsMargins(0, 0, 0, 0)
        options_layout.setSpacing(8)  # Spacing between rows

        # First row: Display options and Status preferences side by side
        first_row_container = QFrame(options_container)
        first_row_container.setObjectName("FirstRowContainer")
        first_row_layout = QHBoxLayout(first_row_container)
        first_row_layout.setContentsMargins(0, 0, 0, 0)
        first_row_layout.setSpacing(8)  # Spacing between display and status groups

        # Display options group
        display_group = QGroupBox(self.lang_manager.translate("Display Options"), first_row_container)
        display_group.setObjectName("DisplayOptionsGroup")
        display_layout = QHBoxLayout(display_group)  # Changed to horizontal layout
        display_layout.setContentsMargins(4, 4, 4, 4)
        display_layout.setSpacing(6)

        # Left side - Direct checkbox with proper spacing
        # Checkbox
        from PyQt5.QtWidgets import QCheckBox
        self._show_numbers_checkbox = QCheckBox(self.lang_manager.translate("Show project numbers"), display_group)
        self._show_numbers_checkbox.setObjectName("DisplayCheckbox")
        self._show_numbers_checkbox.setToolTip(self.lang_manager.translate("Display project/contract numbers in item cards"))
        self._show_numbers_checkbox.stateChanged.connect(self._on_show_numbers_changed)

        display_layout.addWidget(self._show_numbers_checkbox, 2)  # Give more space to settings

        # Right side - Explanation text
        display_explanation = QLabel(self.lang_manager.translate("When enabled, project/contract numbers will be displayed in item cards for easy identification."), display_group)
        display_explanation.setObjectName("GroupExplanation")
        display_explanation.setWordWrap(True)
        display_explanation.setStyleSheet("color: #888; font-size: 11px; padding: 4px 0px;")
        display_explanation.setMinimumWidth(200)  # Ensure minimum width for readability
        display_layout.addWidget(display_explanation, 1)  # Equal space for explanation

        first_row_layout.addWidget(display_group)

        # Status preferences group
        status_group = QGroupBox(self.lang_manager.translate("Status Preferences"), first_row_container)
        status_group.setObjectName("StatusPreferencesGroup")
        status_layout = QHBoxLayout(status_group)  # Changed to horizontal layout
        status_layout.setContentsMargins(4, 4, 4, 4)
        status_layout.setSpacing(6)

        # Left side - Status filter widget
        status_container = QFrame(status_group)
        status_container.setObjectName("StatusContainer")
        status_inner_layout = QVBoxLayout(status_container)
        status_inner_layout.setContentsMargins(0, 0, 0, 0)
        status_inner_layout.setSpacing(4)

        # Add the existing StatusFilterWidget
        try:
            self._status_filter_widget = StatusFilterWidget(self.module_name, status_container, debug=True)
            self._status_filter_widget.selectionChanged.connect(self._on_status_selection_changed)
            status_inner_layout.addWidget(self._status_filter_widget)
            # Don't load immediately - wait for settings activation
            self._status_filter_widget._loaded = False
        except Exception as e:
            # If StatusFilterWidget fails to load, create a simple placeholder
            print(f"Failed to create StatusFilterWidget: {e}")
            self._status_filter_widget = None
            error_label = QLabel(self.lang_manager.translate("Status preferences unavailable"))
            error_label.setStyleSheet("color: #999; font-style: italic;")
            status_inner_layout.addWidget(error_label)

        status_layout.addWidget(status_container, 2)  # Give more space to status filter

        # Right side - Explanation text
        status_explanation = QLabel(self.lang_manager.translate("Select statuses you want to prioritize for this module. These will be highlighted in the interface."), status_group)
        status_explanation.setObjectName("GroupExplanation")
        status_explanation.setWordWrap(True)
        status_explanation.setStyleSheet("color: #888; font-size: 11px; padding: 4px 0px;")
        status_explanation.setMinimumWidth(200)  # Ensure minimum width for readability
        status_layout.addWidget(status_explanation, 1)  # Equal space for explanation

        first_row_layout.addWidget(status_group)

        options_layout.addWidget(first_row_container)

        # Second row: Type preferences (only for modules that support types)
        self._supports_types = self._module_supports_types()
        if self._supports_types:
            # Type preferences group
            type_group = QGroupBox(self.lang_manager.translate("Type Preferences"), options_container)
            type_group.setObjectName("TypePreferencesGroup")
            type_layout = QHBoxLayout(type_group)  # Changed to horizontal layout
            type_layout.setContentsMargins(4, 4, 4, 4)
            type_layout.setSpacing(6)

            # Left side - Type filter widget
            type_container = QFrame(type_group)
            type_container.setObjectName("TypeContainer")
            type_inner_layout = QVBoxLayout(type_container)
            type_inner_layout.setContentsMargins(0, 0, 0, 0)
            type_inner_layout.setSpacing(4)

            # Add the existing TypeFilterWidget
            try:
                # Extract base module name for TypeFilterWidget
                base_module_name = "CONTRACT" if "CONTRACT" in str(self.module_name).upper() else str(self.module_name).upper()
                if TypeFilterWidget is not None:
                    self._type_filter_widget = TypeFilterWidget(base_module_name, self.lang_manager, type_container, debug=True)
                    self._type_filter_widget.selectionChanged.connect(self._on_type_selection_changed)
                    type_inner_layout.addWidget(self._type_filter_widget)
                    # Don't load immediately - wait for settings activation
                    self._type_filter_widget._loaded = False
                else:
                    raise Exception("TypeFilterWidget not available")
            except Exception as e:
                # If TypeFilterWidget fails to load, create a simple placeholder
                print(f"Failed to create TypeFilterWidget: {e}")
                self._type_filter_widget = None
                error_label = QLabel(self.lang_manager.translate("Type preferences unavailable"))
                error_label.setStyleSheet("color: #999; font-style: italic;")
                type_inner_layout.addWidget(error_label)

            type_layout.addWidget(type_container, 2)  # Give more space to type filter

            # Right side - Explanation text
            type_explanation = QLabel(self.lang_manager.translate("Select types you want to prioritize for this module. These will be highlighted in the interface."), type_group)
            type_explanation.setObjectName("GroupExplanation")
            type_explanation.setWordWrap(True)
            type_explanation.setStyleSheet("color: #888; font-size: 11px; padding: 4px 0px;")
            type_explanation.setMinimumWidth(200)  # Ensure minimum width for readability
            type_layout.addWidget(type_explanation, 1)  # Equal space for explanation

            options_layout.addWidget(type_group)

        cl.addWidget(options_container)

        # Add stretch to push content up (no footer building here - use base class)
        cl.addStretch(1)

    # --- Lifecycle hooks called by SettingsUI ---
    def on_settings_activate(self, snapshot=None):
        if snapshot is not None:
            self._snapshot = snapshot
            self._element_picker.setSnapshot(snapshot)
            self._archive_picker.setSnapshot(snapshot)
        self._element_picker.on_settings_activate(snapshot=self._snapshot)
        self._archive_picker.on_settings_activate(snapshot=self._snapshot)
        # Ensure styling is applied when settings are activated
        self._element_picker.retheme()
        self._archive_picker.retheme()
        # Load originals (if any) without marking pending
        self._orig_element_id = self._read_saved_layer_id(kind="element")
        self._orig_archive_id = self._read_saved_layer_id(kind="archive")
        self._orig_show_numbers = self._read_show_numbers_setting()
        self._pend_show_numbers = self._orig_show_numbers
        self._show_numbers_checkbox.setChecked(self._orig_show_numbers)
        
        # Load original status preferences
        self._orig_status_preferences = self._load_status_preferences_from_settings()
        self._pend_status_preferences = self._orig_status_preferences.copy()
        
        # Load original type preferences (only if module supports types)
        if self._supports_types:
            self._orig_type_preferences = self._load_type_preferences_from_settings()
            self._pend_type_preferences = self._orig_type_preferences.copy()
        else:
            self._orig_type_preferences = set()
            self._pend_type_preferences = set()
        
        # Initialize status filter widget with saved preferences
        if hasattr(self, '_status_filter_widget') and self._status_filter_widget is not None:
            # Ensure the widget is loaded
            try:
                self._status_filter_widget.ensure_loaded()
                self._status_filter_widget.set_selected_ids(list(self._orig_status_preferences))
            except Exception as e:
                # If loading fails, disable the widget
                print(f"Failed to load status filter widget: {e}")
                self._status_filter_widget.setEnabled(False)
                # Create an error label to show in the widget
                if hasattr(self._status_filter_widget, 'combo'):
                    self._status_filter_widget.combo.clear()
                    self._status_filter_widget.combo.addItem("Failed to load statuses")
        
        # Initialize type filter widget with saved preferences (only if module supports types)
        if self._supports_types and hasattr(self, '_type_filter_widget') and self._type_filter_widget is not None:
            # Ensure the widget is loaded
            try:
                self._type_filter_widget.ensure_loaded()
                self._type_filter_widget.set_selected_ids(list(self._orig_type_preferences))
            except Exception as e:
                # If loading fails, disable the widget
                print(f"Failed to load type filter widget: {e}")
                self._type_filter_widget.setEnabled(False)
                # Create an error label to show in the widget
                if hasattr(self._type_filter_widget, 'type_combo'):
                    self._type_filter_widget.type_combo.clear()
                    self._type_filter_widget.type_combo.addItem("Failed to load types")
        
        # Apply stored selections to pickers so they display the saved layer names
        # Only set if the layer actually exists
        if self._orig_element_id:
            try:
                # Try to set the selection and see if it works
                self._element_picker.setSelectedLayerId(self._orig_element_id)
                # Refresh to ensure the selection is applied
                self._element_picker.refresh()
                # Check if the selection actually took effect
                if not self._element_picker.selectedLayer():
                    # Layer doesn't exist or selection failed, clear the stored value
                    self._orig_element_id = ""
            except Exception:
                self._orig_element_id = ""
                
        if self._orig_archive_id:
            try:
                # Try to set the selection and see if it works
                self._archive_picker.setSelectedLayerId(self._orig_archive_id)
                # Refresh to ensure the selection is applied
                self._archive_picker.refresh()
                # Check if the selection actually took effect
                if not self._archive_picker.selectedLayer():
                    # Layer doesn't exist or selection failed, clear the stored value
                    self._orig_archive_id = ""
            except Exception:
                self._orig_archive_id = ""

        # Update footer display after setting layer selections
        self._update_stored_values_display()

    def on_settings_deactivate(self):
        if self._element_picker:
            self._element_picker.on_settings_deactivate()
        if self._archive_picker:
            self._archive_picker.on_settings_deactivate()

    # --- Persistence ---
    def _settings_key(self, kind: str) -> str:
        # kind in {"element", "archive"}
        return f"wild_code/modules/{self.module_name}/{kind}_layer_id"

    def _read_saved_layer_id(self, kind: str) -> str:
        if not QgsSettings:
            return ""
        try:
            s = QgsSettings()
            return s.value(self._settings_key(kind), "") or ""
        except Exception:
            return ""

    def _write_saved_layer_id(self, kind: str, layer_id: str):
        if not QgsSettings:
            return
        try:
            s = QgsSettings()
            key = self._settings_key(kind)
            if layer_id:
                s.setValue(key, layer_id)
            else:
                s.remove(key)
        except Exception:
            pass

    # --- Apply/Revert/State ---
    def has_pending_changes(self) -> bool:
        el_dirty = bool(self._pend_element_id and self._pend_element_id != self._orig_element_id)
        ar_dirty = bool(self._pend_archive_id and self._pend_archive_id != self._orig_archive_id)
        num_dirty = self._pend_show_numbers != self._orig_show_numbers
        status_dirty = self._pend_status_preferences != self._orig_status_preferences
        type_dirty = self._supports_types and self._pend_type_preferences != self._orig_type_preferences
        return el_dirty or ar_dirty or num_dirty or status_dirty or type_dirty

    def apply(self):
        changed = False
        if self._pend_element_id and self._pend_element_id != self._orig_element_id:
            self._write_saved_layer_id("element", self._pend_element_id)
            self._orig_element_id = self._pend_element_id
            self._element_picker.setSelectedLayerId(self._orig_element_id)
            changed = True
        if self._pend_archive_id and self._pend_archive_id != self._orig_archive_id:
            self._write_saved_layer_id("archive", self._pend_archive_id)
            self._orig_archive_id = self._pend_archive_id
            self._archive_picker.setSelectedLayerId(self._orig_archive_id)
            changed = True

        # Save show numbers setting
        if self._pend_show_numbers != self._orig_show_numbers:
            self._write_show_numbers_setting(self._pend_show_numbers)
            self._orig_show_numbers = self._pend_show_numbers
            # Also save to ThemeManager for immediate access
            try:
                from ....widgets.theme_manager import ThemeManager
                ThemeManager.save_module_setting(self.module_name, "show_numbers", self._pend_show_numbers)
            except Exception:
                pass
            changed = True

        # Save status preferences
        if self._pend_status_preferences != self._orig_status_preferences:
            self._save_status_preferences()
            self._orig_status_preferences = self._pend_status_preferences.copy()
            changed = True

        # Save type preferences (only if module supports types)
        if self._supports_types and self._pend_type_preferences != self._orig_type_preferences:
            self._save_type_preferences()
            self._orig_type_preferences = self._pend_type_preferences.copy()
            changed = True

        self._pend_element_id = ""
        self._pend_archive_id = ""
        self._sync_selected_names()
        self.pendingChanged.emit(False if changed else self.has_pending_changes())

    def revert(self):
        # Restore originals and clear pending
        self._element_picker.setSelectedLayerId(self._orig_element_id)
        self._archive_picker.setSelectedLayerId(self._orig_archive_id)
        self._pend_element_id = ""
        self._pend_archive_id = ""

        # Revert show numbers setting
        self._pend_show_numbers = self._orig_show_numbers
        self._show_numbers_checkbox.setChecked(self._orig_show_numbers)

        # Revert status preferences
        self._pend_status_preferences = self._orig_status_preferences.copy()
        self._restore_status_preferences_ui()

        # Revert type preferences (only if module supports types)
        if self._supports_types:
            self._pend_type_preferences = self._orig_type_preferences.copy()
            self._restore_type_preferences_ui()

        self._sync_selected_names()
        self.pendingChanged.emit(False)

    def _sync_selected_names(self):
        # Update footer with stored values summary (labels removed from UI)
        self._update_stored_values_display()

    def _update_stored_values_display(self):
        """Update footer with flowing text summary of stored values."""
        try:
            # Get layer names directly from pickers instead of removed labels
            def name_for(picker):
                if not picker:
                    return ""
                lyr = picker.selectedLayer()
                try:
                    return lyr.name() if lyr else ""
                except Exception:
                    return ""

            element_name = name_for(self._element_picker)
            archive_name = name_for(self._archive_picker)

            parts = []
            if element_name:
                parts.append(f"📄 Main: {element_name}")
            if archive_name:
                parts.append(f"📁 Archive: {archive_name}")

            if parts:
                values_text = " | ".join(parts)
                self.set_status_text(f"Active layers: {values_text}")
            else:
                self.set_status_text("No layers configured")
        except Exception as e:
            # If there's an error, show a generic message
            self.set_status_text("Settings loaded")

    # --- Show Numbers Setting ---
    def _show_numbers_settings_key(self) -> str:
        return f"wild_code/modules/{self.module_name}/show_numbers"

    def _read_show_numbers_setting(self) -> bool:
        if not QgsSettings:
            return True
        try:
            s = QgsSettings()
            return bool(s.value(self._show_numbers_settings_key(), True))
        except Exception:
            return True

    def _write_show_numbers_setting(self, show_numbers: bool):
        if not QgsSettings:
            return
        try:
            s = QgsSettings()
            key = self._show_numbers_settings_key()
            s.setValue(key, show_numbers)
        except Exception:
            pass

    def _on_show_numbers_changed(self, state):
        self._pend_show_numbers = bool(state)
        self.pendingChanged.emit(self.has_pending_changes())

    def _on_status_selection_changed(self):
        """Handle status selection changes from the StatusFilterWidget."""
        if not self._status_filter_widget or not self._status_filter_widget.isEnabled():
            return
        try:
            selected_ids = self._status_filter_widget.selected_ids()
            self._pend_status_preferences = set(selected_ids) if selected_ids else set()
            self.pendingChanged.emit(self.has_pending_changes())
        except Exception as e:
            print(f"Error handling status selection change: {e}")

    def _on_type_selection_changed(self):
        """Handle type selection changes from the TypeFilterWidget."""
        if not self._supports_types:
            return
        if not self._type_filter_widget or not self._type_filter_widget.isEnabled():
            return
        try:
            selected_ids = self._type_filter_widget.selected_ids()
            self._pend_type_preferences = set(selected_ids) if selected_ids else set()
            self.pendingChanged.emit(self.has_pending_changes())
        except Exception as e:
            print(f"Error handling type selection change: {e}")

    def _on_reset_settings(self):
        """Reset all settings for this module to defaults."""
        try:
            # Reset layer selections
            self._element_picker.setSelectedLayerId("")
            self._archive_picker.setSelectedLayerId("")
            self._pend_element_id = ""
            self._pend_archive_id = ""

            # Reset show numbers to default (True)
            self._pend_show_numbers = True
            self._show_numbers_checkbox.setChecked(True)

            # Reset status preferences
            if hasattr(self, '_status_filter_widget') and self._status_filter_widget is not None and self._status_filter_widget.isEnabled():
                try:
                    self._status_filter_widget.set_selected_ids([])
                except Exception as e:
                    print(f"Error resetting status preferences: {e}")
                self._orig_status_preferences = set()
                self._pend_status_preferences = set()

            # Reset type preferences (only if module supports types)
            if self._supports_types and hasattr(self, '_type_filter_widget') and self._type_filter_widget is not None and self._type_filter_widget.isEnabled():
                try:
                    self._type_filter_widget.set_selected_ids([])
                except Exception as e:
                    print(f"Error resetting type preferences: {e}")
                self._orig_type_preferences = set()
                self._pend_type_preferences = set()

            # Clear any stored settings
            self._write_saved_layer_id("element", "")
            self._write_saved_layer_id("archive", "")
            self._write_show_numbers_setting(True)

            # Clear status preferences
            try:
                from qgis.core import QgsSettings
                s = QgsSettings()
                key = f"wild_code/modules/{self.module_name}/preferred_statuses"
                s.remove(key)
            except Exception:
                pass

            # Clear type preferences (only if module supports types)
            if self._supports_types:
                try:
                    from qgis.core import QgsSettings
                    s = QgsSettings()
                    key = f"wild_code/modules/{self.module_name}/preferred_types"
                    s.remove(key)
                except Exception:
                    pass

            # Update UI
            self._sync_selected_names()
            self._validate_layer_selections()
            self.set_status_text(f"✅ {self.lang_manager.translate('Settings reset to defaults')}", True)

            # Mark as having changes to allow saving
            self.pendingChanged.emit(self.has_pending_changes())

        except Exception as e:
            self.set_status_text(f"❌ {self.lang_manager.translate('Reset failed')}: {str(e)}", True)

    def _load_status_preferences_from_settings(self) -> set:
        """Load status preferences directly from QGIS settings."""
        try:
            from qgis.core import QgsSettings
            s = QgsSettings()
            key = f"wild_code/modules/{self.module_name}/preferred_statuses"
            preferred_statuses = s.value(key, "") or ""

            if preferred_statuses:
                return set(preferred_statuses.split(","))
            return set()
        except Exception:
            return set()

    def _save_status_preferences(self):
        """Save status preferences for this module."""
        try:
            from qgis.core import QgsSettings
            s = QgsSettings()

            key = f"wild_code/modules/{self.module_name}/preferred_statuses"
            if self._pend_status_preferences:
                s.setValue(key, ",".join(self._pend_status_preferences))
            else:
                s.remove(key)

        except Exception:
            pass

    def _restore_status_preferences_ui(self):
        """Restore the UI state of status preferences."""
        if hasattr(self, '_status_filter_widget') and self._status_filter_widget is not None and self._status_filter_widget.isEnabled():
            try:
                self._status_filter_widget.set_selected_ids(list(self._orig_status_preferences))
            except Exception as e:
                print(f"Error restoring status preferences UI: {e}")

    def _load_type_preferences_from_settings(self) -> set:
        """Load type preferences directly from QGIS settings."""
        try:
            from qgis.core import QgsSettings
            s = QgsSettings()
            key = f"wild_code/modules/{self.module_name}/preferred_types"
            preferred_types = s.value(key, "") or ""

            if preferred_types:
                return set(preferred_types.split(","))
            return set()
        except Exception:
            return set()

    def _save_type_preferences(self):
        """Save type preferences for this module."""
        try:
            from qgis.core import QgsSettings
            s = QgsSettings()

            key = f"wild_code/modules/{self.module_name}/preferred_types"
            if self._pend_type_preferences:
                s.setValue(key, ",".join(self._pend_type_preferences))
            else:
                s.remove(key)

        except Exception:
            pass

    def _module_supports_types(self) -> bool:
        """Determine if this module supports type preferences."""
        # Convert module_name to uppercase for comparison
        module_upper = str(self.module_name).upper()
        # CONTRACT modules support types, PROJECT modules do not
        return "CONTRACT" in module_upper

    # --- Handlers ---
    def _on_element_selected(self, layer_id: str):
        self._pend_element_id = layer_id or ""
        self._sync_selected_names()
        self.pendingChanged.emit(self.has_pending_changes())

    def _on_archive_selected(self, layer_id: str):
        self._pend_archive_id = layer_id or ""
        self._sync_selected_names()
        self.pendingChanged.emit(self.has_pending_changes())
