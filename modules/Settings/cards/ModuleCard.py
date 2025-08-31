from PyQt5.QtWidgets import QVBoxLayout, QLabel, QFrame, QHBoxLayout, QGroupBox
from PyQt5.QtCore import pyqtSignal
from .BaseCard import BaseCard
from ....widgets.layer_dropdown import LayerTreePicker

try:
    from qgis.core import QgsSettings
except Exception:
    QgsSettings = None  # type: ignore


class ModuleCard(BaseCard):
    pendingChanged = pyqtSignal(bool)

    def __init__(self, lang_manager, module_name: str, translated_name: str):
        # Get module icon for the header
        icon_path = None
        try:
            from ....constants.module_icons import ModuleIconPaths
            icon_path = ModuleIconPaths.get_module_icon(module_name)
        except Exception:
            pass

        super().__init__(lang_manager, translated_name, icon_path)
        self.module_name = module_name
        self._snapshot = None
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
        self._build_ui()

    # --- UI ---
    def _build_ui(self):
        cw = self.content_widget()
        cl = QVBoxLayout(cw)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(16)  # Increased spacing between groups for better separation

        # Main layer group
        main_group = QGroupBox(self.lang_manager.translate("Modules main layer"), cw)
        main_group.setObjectName("MainLayerGroup")
        main_layout = QHBoxLayout(main_group)  # Changed to horizontal layout
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(12)  # Spacing between dropdown and explanation

        # Left side - Element picker
        self._element_picker = LayerTreePicker(main_group, placeholder=self.lang_manager.translate("Select layer"))
        self._element_picker.layerIdChanged.connect(self._on_element_selected)
        main_layout.addWidget(self._element_picker, 2)  # Give more space to dropdown

        # Right side - Explanation text
        explanation1 = QLabel("See on teie mooduli põhikiht. Valige kiht, mis sisaldab peamisi andmeid, millega soovite töötada. See säte määrab, millist kihti kasutatakse alusena kõigi mooduli toimingute jaoks.", main_group)
        explanation1.setObjectName("GroupExplanation")
        explanation1.setWordWrap(True)
        explanation1.setStyleSheet("color: #888; font-size: 11px; padding: 4px 0px;")
        explanation1.setMinimumWidth(200)  # Ensure minimum width for readability
        main_layout.addWidget(explanation1, 1)  # Equal space for explanation

        cl.addWidget(main_group)

        # Archive layer group
        archive_group = QGroupBox(self.lang_manager.translate("Archive layer"), cw)
        archive_group.setObjectName("ArchiveLayerGroup")
        archive_layout = QHBoxLayout(archive_group)  # Changed to horizontal layout
        archive_layout.setContentsMargins(8, 8, 8, 8)
        archive_layout.setSpacing(12)

        # Left side - Archive picker
        self._archive_picker = LayerTreePicker(archive_group, placeholder=self.lang_manager.translate("Select layer"))
        self._archive_picker.layerIdChanged.connect(self._on_archive_selected)
        archive_layout.addWidget(self._archive_picker, 2)

        # Right side - Explanation text
        explanation2 = QLabel("See valikuline arhiivikiht salvestab ajaloolisi või varukoopia andmeid. Kasutage seda, kui vajate muudatuste või andmete ajalooliste versioonide eraldi kirjet.", archive_group)
        explanation2.setObjectName("GroupExplanation")
        explanation2.setWordWrap(True)
        explanation2.setStyleSheet("color: #888; font-size: 11px; padding: 4px 0px;")
        explanation2.setMinimumWidth(200)
        archive_layout.addWidget(explanation2, 1)

        cl.addWidget(archive_group)

        # Display options group
        display_group = QGroupBox(self.lang_manager.translate("Display Options"), cw)
        display_group.setObjectName("DisplayOptionsGroup")
        display_layout = QVBoxLayout(display_group)
        display_layout.setContentsMargins(8, 16, 8, 8)  # Increased top margin to avoid overlap
        display_layout.setSpacing(8)

        # Show numbers checkbox
        from PyQt5.QtWidgets import QCheckBox
        self._show_numbers_checkbox = QCheckBox(self.lang_manager.translate("Show project numbers"), display_group)
        self._show_numbers_checkbox.setToolTip(self.lang_manager.translate("Display project/contract numbers in item cards"))
        self._show_numbers_checkbox.stateChanged.connect(self._on_show_numbers_changed)
        display_layout.addWidget(self._show_numbers_checkbox)

        cl.addWidget(display_group)

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
        # Load originals (if any) without marking pending
        self._orig_element_id = self._read_saved_layer_id(kind="element")
        self._orig_archive_id = self._read_saved_layer_id(kind="archive")
        self._orig_show_numbers = self._read_show_numbers_setting()
        self._pend_show_numbers = self._orig_show_numbers
        self._show_numbers_checkbox.setChecked(self._orig_show_numbers)
        
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
        return el_dirty or ar_dirty or num_dirty

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

    # --- Handlers ---
    def _on_element_selected(self, layer_id: str):
        self._pend_element_id = layer_id or ""
        self._sync_selected_names()
        self.pendingChanged.emit(self.has_pending_changes())

    def _on_archive_selected(self, layer_id: str):
        self._pend_archive_id = layer_id or ""
        self._sync_selected_names()
        self.pendingChanged.emit(self.has_pending_changes())
