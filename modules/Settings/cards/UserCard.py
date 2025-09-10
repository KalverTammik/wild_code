# user_card.py
from PyQt5.QtCore import pyqtSignal, Qt, QEvent
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QCheckBox, QPushButton
)

from .BaseCard import BaseCard  # assumes BaseCard provides: content_widget(), retheme(), etc.


class UserCard(BaseCard):
    """
    Product-level user card:
      - Info (ID, Name, Email)
      - Roles (read-only pills, reuse AccessPill visuals)
      - Module access (pills with checkbox-like preferred selector, single-selection)

    Signals:
      preferredChanged(object)  -> emits selected module name or None
      moduleSettingsClicked(str) -> emits module name when settings button clicked
      addShpClicked() -> emits when Add SHP file button is clicked
      addPropertyClicked() -> emits when Add property button is clicked
      removePropertyClicked() -> emits when Remove property button is clicked
    """
    preferredChanged = pyqtSignal(object)
    moduleSettingsClicked = pyqtSignal(str)
    addShpClicked = pyqtSignal()
    addPropertyClicked = pyqtSignal()
    removePropertyClicked = pyqtSignal()
    layerSelected = pyqtSignal(object)  # Emits selected layer or None

    def __init__(self, lang_manager):
        super().__init__(lang_manager, lang_manager.translate("User"), None)

        cw = self.content_widget()
        cl = QVBoxLayout(cw)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(8)  # Slightly increased spacing for better visual separation

        # ---------- User Info Card (IMPROVED: Two-column layout with roles) ----------
        user_info_card = QFrame(cw)
        user_info_card.setObjectName("UserInfoCard")

        # Two-column layout for user info
        user_info_main_layout = QHBoxLayout(user_info_card)
        user_info_main_layout.setContentsMargins(10, 8, 10, 8)
        user_info_main_layout.setSpacing(20)  # Space between columns

        # Left column: Basic user info
        left_column = QVBoxLayout()
        left_column.setSpacing(4)

        # Name prominently displayed
        self.lbl_name = QLabel(self.lang_manager.translate("Name") + ": —", user_info_card)
        self.lbl_name.setObjectName("UserName")
        left_column.addWidget(self.lbl_name)

        # Email below name
        self.lbl_email = QLabel(self.lang_manager.translate("Email") + ": —", user_info_card)
        self.lbl_email.setObjectName("UserEmail")
        left_column.addWidget(self.lbl_email)

        left_column.addStretch(1)  # Push content to top
        user_info_main_layout.addLayout(left_column)

        # Right column: Roles
        right_column = QVBoxLayout()
        right_column.setSpacing(4)

        # Roles label
        roles_label = QLabel(self.lang_manager.translate("Roles"), user_info_card)
        roles_label.setObjectName("UserRolesLabel")
        right_column.addWidget(roles_label)

        # Roles value (separate line)
        self.lbl_roles = QLabel("—", user_info_card)
        self.lbl_roles.setObjectName("UserRoles")
        right_column.addWidget(self.lbl_roles)

        right_column.addStretch(1)  # Push content to top
        user_info_main_layout.addLayout(right_column)

        cl.addWidget(user_info_card)

        # ---------- Module access (pills with checkboxes) ----------
        pills_title = QLabel(self.lang_manager.translate("Module access"), cw)
        pills_title.setObjectName("SetupCardSectionTitle")
        cl.addWidget(pills_title)

        self.access_container = QFrame(cw)
        self.access_container.setObjectName("AccessPills")
        self.access_layout = QHBoxLayout(self.access_container)
        self.access_layout.setContentsMargins(0, 0, 0, 0)
        self.access_layout.setSpacing(8)  # Increased spacing for better visual separation
        cl.addWidget(self.access_container)

        # ---------- Property Management Widget ----------
        from .PropertyManagement import PropertyManagement
        self.property_management = PropertyManagement(self.lang_manager)
        # Connect signals from property management widget
        self.property_management.addShpClicked.connect(self._on_add_shp_clicked)
        self.property_management.addPropertyClicked.connect(self._on_add_property_clicked)
        self.property_management.removePropertyClicked.connect(self._on_remove_property_clicked)
        cl.addWidget(self.property_management)

        # ---------- Layer Selector ----------
        layer_selector_title = QLabel(self.lang_manager.translate("Layer Selection"), cw)
        layer_selector_title.setObjectName("SetupCardSectionTitle")
        cl.addWidget(layer_selector_title)

        # Layer selector container
        layer_selector_container = QFrame(cw)
        layer_selector_container.setObjectName("LayerSelector")
        layer_selector_layout = QVBoxLayout(layer_selector_container)
        layer_selector_layout.setContentsMargins(0, 0, 0, 0)
        layer_selector_layout.setSpacing(5)

        # Explanation label
        explanation_label = QLabel(
            self.lang_manager.translate("Select a property layer for data operations and management"),
            layer_selector_container
        )
        explanation_label.setObjectName("LayerSelectorExplanation")
        explanation_label.setWordWrap(True)
        explanation_label.setStyleSheet("font-size: 11px; color: #666;")
        layer_selector_layout.addWidget(explanation_label)

        # Use the existing LayerTreePicker widget
        from ....widgets.layer_dropdown import LayerTreePicker
        self.layer_selector = LayerTreePicker(
            layer_selector_container,
            placeholder=self.lang_manager.translate("Select a property layer...")
        )
        self.layer_selector.setObjectName("PropertyLayerSelector")
        self.layer_selector.layerChanged.connect(self._on_layer_selection_changed)
        layer_selector_layout.addWidget(self.layer_selector)

        cl.addWidget(layer_selector_container)

        # Populate layer selector and load saved selection
        self._populate_layer_selector()
        # Note: Initial layer selection is now handled by SettingsUI

        # Connect to project layer changes
        self._connect_to_project_signals()

        # Internal state
        self._check_by_module = {}
        self._pill_click_targets = {}
        self._update_permissions = {}

    # ---------- Public API (SettingsUI uses these) ----------
    def set_user(self, user: dict):
        # IMPROVED: No longer showing user ID as it doesn't make sense to users
        full_name = f"{user.get('firstName', '')} {user.get('lastName', '')}".strip() or "—"
        email = user.get("email", "—")

        self.lbl_name.setText(f"{full_name}")
        self.lbl_email.setText(f"{email}")

    def set_roles(self, roles):
        # IMPROVED: Display roles on separate line below label
        if roles:
            roles_text = ", ".join(roles)
            self.lbl_roles.setText(roles_text)
        else:
            self.lbl_roles.setText("—")

    def set_update_permissions(self, update_permissions: dict):
        """Set which modules the user can update/modify"""
        self._update_permissions = update_permissions or {}
        print(f"DEBUG: Update permissions set: {self._update_permissions}")

    def set_access_map(self, access_map: dict, label_resolver=None):
        # Clear previous pills and checks
        self._clear_layout(self.access_layout)
        self._check_by_module.clear()
        self._reset_click_targets()

        # Build new pills
        for module_name, has_access in (access_map or {}).items():
            label_text = label_resolver(module_name) if label_resolver else module_name

            pill = QFrame(self.access_container)
            pill.setObjectName("AccessPill")
            pill.setFocusPolicy(Qt.StrongFocus)  # allows focus ring via :focus-within

            hl = QHBoxLayout(pill)
            hl.setContentsMargins(8, 2, 8, 2)  # Consistent padding with roles pills
            hl.setSpacing(6)

            chk = QCheckBox(pill)
            # Keep old objectName so existing QSS (written for radios) continues to apply
            chk.setObjectName("PreferredModuleRadio")
            chk.setEnabled(bool(has_access))
            chk.setProperty("moduleName", module_name)
            chk.toggled.connect(lambda checked, btn=chk: self._on_pref_toggled(btn, checked))

            txt = QLabel(label_text, pill)

            # QSS properties for coloring
            pill.setProperty("active", bool(has_access))
            pill.setProperty("inactive", not has_access)
            pill.style().unpolish(pill); pill.style().polish(pill)

            # Strike text if no access
            f = txt.font()
            f.setStrikeOut(not has_access)
            txt.setFont(f)

            hl.addWidget(chk, 0)
            hl.addWidget(txt, 0)
            
            # Add settings button if user has update permissions for this module
            if has_access and self._update_permissions.get(module_name, False):
                from PyQt5.QtWidgets import QPushButton
                settings_btn = QPushButton("⚙️", pill)
                settings_btn.setObjectName("ModuleSettingsButton")
                settings_btn.setFixedSize(20, 20)
                settings_btn.setToolTip(f"Open {label_text} settings")
                settings_btn.clicked.connect(lambda checked, mod=module_name: self._on_module_settings_clicked(mod))
                hl.addWidget(settings_btn, 0)
            else:
                hl.addStretch(1)

            # Make pill and its label clickable to select
            if has_access:
                self._register_click_target(pill, chk)
                self._register_click_target(txt, chk)

            self._check_by_module[module_name] = chk
            self.access_layout.addWidget(pill)

        self.access_layout.addStretch(1)

    def set_preferred(self, module_name):
        # Programmatic single-selection with checkboxes
        for m, cb in self._check_by_module.items():
            cb.blockSignals(True)
            cb.setChecked(m == module_name)
            cb.blockSignals(False)

    def get_selected_preferred(self):
        for m, cb in self._check_by_module.items():
            if cb.isChecked():
                return m
        return None

    def apply(self):
        """Hook called after settings are applied (if needed later)."""
        pass

    def revert(self, preferred_module_name):
        """Reset UI selection to original preferred module."""
        self.set_preferred(preferred_module_name)

    def _on_module_settings_clicked(self, module_name):
        """Handle module settings button click"""
        print(f"DEBUG: Module settings clicked for: {module_name}")
        self.moduleSettingsClicked.emit(module_name)

    def retheme(self):
        super().retheme()
        # Repolish dynamic widgets so [active]/[inactive] QSS is reapplied
        self._repolish_pills(self.access_layout)

    # ---------- Callbacks ----------
    def _on_pref_toggled(self, btn, checked):
        # Single-selection behavior with ability to select none
        if checked:
            module_name = btn.property("moduleName")
            for m, cb in self._check_by_module.items():
                if cb is btn:
                    continue
                if cb.isChecked():
                    cb.blockSignals(True)
                    cb.setChecked(False)
                    cb.blockSignals(False)
            self.preferredChanged.emit(module_name)
            return
        # Unchecked: if no other is checked, emit None to prefer welcome page
        any_other = any(cb.isChecked() for cb in self._check_by_module.values() if cb is not btn)
        if not any_other:
            self.preferredChanged.emit(None)

    # Clickable pill helpers -----------------------------------------
    def _register_click_target(self, widget, checkbox):
        try:
            widget.installEventFilter(self)
        except Exception:
            pass
        self._pill_click_targets[widget] = checkbox

    def _reset_click_targets(self):
        for w in list(self._pill_click_targets.keys()):
            try:
                w.removeEventFilter(self)
            except Exception:
                pass
        self._pill_click_targets.clear()

    def eventFilter(self, obj, event):
        if obj in getattr(self, '_pill_click_targets', {}) and event.type() == QEvent.MouseButtonRelease:
            cb = self._pill_click_targets.get(obj)
            if cb and cb.isEnabled():
                cb.setChecked(not cb.isChecked())
            return True
        return super().eventFilter(obj, event)

    # ---------- Button Handlers ----------
    def _on_add_shp_clicked(self):
        """Handle Add SHP file button click"""
        self.addShpClicked.emit()

    def _on_add_property_clicked(self):
        """Handle Add property button click"""
        self.addPropertyClicked.emit()

    def _on_remove_property_clicked(self):
        """Handle Remove property button click"""
        self.removePropertyClicked.emit()

    # ---------- Layer Selector Methods ----------
    def _populate_layer_selector(self):
        """Populate the layer selector with available property layers"""
        try:
            # The LayerTreePicker handles its own population from the QGIS project
            # We just need to refresh it
            self.layer_selector.refresh()
        except Exception as e:
            print(f"Error refreshing layer selector: {e}")

    def _connect_to_project_signals(self):
        """Connect to QGIS project signals to respond to layer changes"""
        try:
            from qgis.core import QgsProject
            project = QgsProject.instance()
            if project:
                # Connect to layer addition/removal signals
                project.layersAdded.connect(self._on_project_layers_changed)
                project.layersRemoved.connect(self._on_project_layers_changed)
                project.layersWillBeRemoved.connect(self._on_project_layers_will_be_removed)
                print("Connected to project layer change signals")
        except Exception as e:
            print(f"Error connecting to project signals: {e}")

    def _on_layer_selection_changed(self, layer):
        """Handle layer selection change"""
        if layer:
            layer_id = layer.id()
            self._selected_layer = layer
            print(f"Selected property layer: {layer.name()} (ID: {layer_id})")
            # Note: Saving is now handled by SettingsUI through the pending pattern
        else:
            self._selected_layer = None
            print("No layer selected")

        # Emit signal with selected layer
        self.layerSelected.emit(layer)

    def _on_project_layers_changed(self, layers):
        """Handle when layers are added or removed from the project"""
        print(f"Project layers changed, refreshing layer selector")
        self._populate_layer_selector()
        # Try to restore the previously selected layer if it still exists
        self._restore_saved_selection_if_available()

    def _on_project_layers_will_be_removed(self, layer_ids):
        """Handle when layers are about to be removed"""
        current_selected_id = self.layer_selector.selectedLayerId()
        if current_selected_id and current_selected_id in layer_ids:
            print(f"Selected layer {current_selected_id} is being removed, clearing selection")
            self.layer_selector.clearSelection()
            self._selected_layer = None
            self.layerSelected.emit(None)

    def _restore_saved_selection_if_available(self):
        """Try to restore the saved layer selection if the layer still exists"""
        # Note: This is now handled by SettingsUI through the pending pattern
        pass

    def get_selected_layer(self):
        """Get the currently selected layer"""
        return getattr(self, '_selected_layer', None)

    def get_main_property_layer(self):
        """Get the main property layer (same as selected layer)."""
        return self.get_selected_layer()

    def clear_main_property_layer(self):
        """Clear the main property layer selection."""
        self.layer_selector.clearSelection()
        self._selected_layer = None
        self.layerSelected.emit(None)

    def refresh_layer_selector(self):
        """Refresh the layer selector with current layers"""
        self._populate_layer_selector()

    def showEvent(self, event):
        """Called when the widget is shown - refresh layer selector"""
        super().showEvent(event)
        self.refresh_layer_selector()

    # ---------- Helpers ----------
    @staticmethod
    def _clear_layout(layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)

    @staticmethod
    def _repolish_pills(layout):
        for i in range(layout.count()):
            item = layout.itemAt(i)
            w = item.widget()
            if isinstance(w, QFrame) and w.objectName() == "AccessPill":
                w.style().unpolish(w); w.style().polish(w); w.update()
