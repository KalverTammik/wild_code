# user_card.py
import sys
from typing import List, Dict, Set
from PyQt5.QtCore import pyqtSignal, Qt, QEvent
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QCheckBox
)
from ....utils.url_manager import Module
from ....constants.file_paths import ConfigPaths
from ....utils.GraphQLQueryLoader import GraphQLQueryLoader
from ....utils.SessionManager import SessionManager
from ....utils.api_client import APIClient
from ....languages.translation_keys import TranslationKeys
from PyQt5.QtWidgets import QPushButton
from .PropertyManagement import PropertyManagement
from .BaseCard import BaseCard  # assumes BaseCard provides: content_widget(), retheme(), etc.
from ....widgets.LayerDropdownWidget import LayerTreePicker


class UserCard(BaseCard):
    """
    Product-level user card displaying user info, module access,
    """
    preferredChanged = pyqtSignal(object)
    addShpClicked = pyqtSignal()
    addPropertyClicked = pyqtSignal()
    removePropertyClicked = pyqtSignal()
    layerSelected = pyqtSignal(object)  # Emits selected layer or None

    def __init__(self, lang_manager):
        super().__init__(lang_manager, lang_manager.translate(TranslationKeys.USER), None)

        cw = self.content_widget()
        cl = QVBoxLayout(cw)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(8)  # Slightly increased spacing for better visual separation

        user_info_card = QFrame(cw)
        user_info_card.setObjectName("SettingsMainInfoCard")

        # Two-column layout for user info
        user_info_main_layout = QHBoxLayout(user_info_card)
        user_info_main_layout.setContentsMargins(6, 6, 6, 6)
        user_info_main_layout.setSpacing(10)  # Space between columns

        # Left column: Basic user info
        left_column = QVBoxLayout()
        left_column.setSpacing(4)

        # Name prominently displayed
        self.lbl_name = QLabel(self.lang_manager.translate(TranslationKeys.NAME) + ": —", user_info_card)
        self.lbl_name.setObjectName("UserName")
        left_column.addWidget(self.lbl_name)

        # Email below name
        self.lbl_email = QLabel(self.lang_manager.translate(TranslationKeys.EMAIL) + ": —", user_info_card)
        self.lbl_email.setObjectName("UserEmail")
        left_column.addWidget(self.lbl_email)

        left_column.addStretch(1)  # Push content to top
        user_info_main_layout.addLayout(left_column)

        # Right column: Roles
        right_column = QVBoxLayout()
        right_column.setSpacing(4)

        # Roles label
        roles_label = QLabel(self.lang_manager.translate(TranslationKeys.ROLES), user_info_card)
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
        module_access_frame = QFrame(cw)
        module_access_frame.setObjectName("SettingsMainInfoCard")
        module_access_layout = QVBoxLayout(module_access_frame)
        module_access_layout.setContentsMargins(0, 0, 0, 0)
        module_access_layout.setSpacing(2)

        pills_title = QLabel(self.lang_manager.translate(TranslationKeys.MODULE_ACCESS), module_access_frame)
        pills_title.setObjectName("SetupCardSectionTitle")
        module_access_layout.addWidget(pills_title)

        self.access_container = QFrame(module_access_frame)
        self.access_container.setObjectName("AccessPills")

        self.access_layout = QHBoxLayout(self.access_container)
        self.access_layout.setContentsMargins(0, 0, 0, 0)
        self.access_layout.setSpacing(8)  # Increased spacing for better visual separation
        module_access_layout.addWidget(self.access_container)

        cl.addWidget(module_access_frame)

        # ---------- Property Management Widget ----------

        self.property_management = PropertyManagement(self.lang_manager)
        # Connect signals from property management widget
        self.property_management.addShpClicked.connect(self.addShpClicked)
        self.property_management.addPropertyClicked.connect(self.addPropertyClicked)
        self.property_management.removePropertyClicked.connect(self.removePropertyClicked)
        cl.addWidget(self.property_management)

        # ---------- Layer Selector ----------
        layer_selector_title = QLabel(self.lang_manager.translate(TranslationKeys.SELECT_LAYER), cw)
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
            self.lang_manager.translate(TranslationKeys.CHOOSE_PROPERTY_LAYER_FOR_MODULE),
            layer_selector_container
        )
        explanation_label.setObjectName("LayerSelectorExplanation")
        explanation_label.setWordWrap(True)
        layer_selector_layout.addWidget(explanation_label)

        # Use the existing LayerTreePicker widget
        self.layer_selector = LayerTreePicker(
            layer_selector_container,
            placeholder=self.lang_manager.translate(TranslationKeys.SELECT_A_PROPERTY_LAYER)
        )
        self.layer_selector.setObjectName("PropertyLayerSelector")
        self.layer_selector.layerChanged.connect(self._on_layer_selection_changed)
        layer_selector_layout.addWidget(self.layer_selector)

        cl.addWidget(layer_selector_container)

        # Populate layer selector and load saved selection
        self._populate_layer_selector()

        # Connect to project layer changes
        self._connect_to_project_signals()

        # Internal state
        self._check_by_module = {}
        self._pill_click_targets = {}
        self._update_permissions = {}

    # ---------- Public API (SettingsUI uses these) ----------

    def set_update_permissions(self, update_permissions: dict):
        """Set which modules the user can update/modify"""
        self._update_permissions = update_permissions or {}
        #print(f"DEBUG: Update permissions set: {self._update_permissions}")

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
            pill.setStyleSheet("QFrame { border: 2px dotted red; }")  # DEBUG: Ugly border to see pill boundaries

            hl = QHBoxLayout(pill)
            hl.setContentsMargins(8, 2, 8, 2)  # Consistent padding with roles pills
            hl.setSpacing(6)

            chk = QCheckBox(pill)
            # Keep old objectName so existing QSS (written for radios) continues to apply
            chk.setObjectName("PreferredModulecb")
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
            
            # Module access is now handled through ModuleCard - no settings button needed
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

    def revert(self, preferred_module_name):
        """Reset UI selection to original preferred module."""
        self.set_preferred(preferred_module_name)

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
                #print("Connected to project layer change signals")
        except Exception as e:
            print(f"Error connecting to project signals: {e}")

    def _on_layer_selection_changed(self, layer):
        """Handle layer selection change"""
        if layer:
            layer_id = layer.id()
            self._selected_layer = layer
            #print(f"Selected property layer: {layer.name()} (ID: {layer_id})")
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


class userUtils:
    @staticmethod
    def load_user(lbl_name: QLabel, lbl_email: QLabel, lbl_roles: QLabel, lang_manager) -> Dict:
        
        name = Module.USER.value
        query_file = "me.graphql"

        ql = GraphQLQueryLoader(lang_manager)
        api = APIClient(SessionManager(), ConfigPaths.CONFIG)
        query = ql.load_query(name, query_file)
        data = api.send_query(query)
        user_data = data.get("me", {}) or {}
        userUtils.extract_and_set_user_labels(lbl_name, lbl_email, user_data)

        roles = userUtils.get_roles_list(user_data.get("roles"))
        userUtils.set_roles(lbl_roles, roles)
        abilities = user_data.get("abilities", [])
        return abilities

    @staticmethod
    def abilities_to_subjects(abilities) -> Set[str]:

        import json
        abilities = abilities or []
        if isinstance(abilities, str):
            try:
                abilities = json.loads(abilities)
            except Exception:
                abilities = []
        subjects = set()
        #print(f"DEBUG: Parsed abilities: {abilities}")
        for ab in abilities:
            subj = ab.get('subject')
            if isinstance(subj, list) and subj:
                subjects.add(str(subj[0]))
            elif isinstance(subj, str):
                subjects.add(subj)
        return subjects

    @staticmethod
    def extract_and_set_user_labels(lbl_name: QLabel, lbl_email: QLabel, user: dict):

        full_name = f"{user.get('firstName', '')} {user.get('lastName', '')}".strip() or "—"
        #print(f"[userUtils] Full name extracted: {full_name}")
        email = user.get("email", "—")

        lbl_name.setText(f"{full_name}")
        lbl_email.setText(f"{email}")

    @staticmethod
    def get_roles_list(roles_data) -> List[str]:
        roles = roles_data or []
        if isinstance(roles, str):
            roles = []
        names: List[str] = []
        for r in roles:
            name = r.get('displayName') or r.get('name') or str(r.get('id') or '')
            if name:
                names.append(name)
        return names

    @staticmethod
    def set_roles(lbl_roles: QLabel, roles: list):
        # IMPROVED: Display roles on separate line below label
        if roles:
            roles_text = ", ".join(roles)
            lbl_roles.setText(roles_text)
        else:
            lbl_roles.setText("—")