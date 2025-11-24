# user_card.py
from PyQt5.QtCore import pyqtSignal, Qt, QEvent
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QCheckBox, QButtonGroup
)
from ....languages.translation_keys import TranslationKeys
from .SettingsPropertyManagement import PropertyManagement
from .SettingsBaseCard import SettingsBaseCard  # assumes BaseCard provides: content_widget(), retheme(), etc.


class UserSettingsCard(SettingsBaseCard):
    """
    Product-level user card displaying user info, module access,
    """
    preferredModuleChanged = pyqtSignal(object)
    addShpClicked = pyqtSignal()
    addPropertyClicked = pyqtSignal()
    removePropertyClicked = pyqtSignal()

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

        self._preferred_group = QButtonGroup(self)
        self._preferred_group.setExclusive(True)

        # ---------- Property Management Widget ----------

        self.property_management = PropertyManagement(self.lang_manager)
        # Connect signals from property management widget
        self.property_management.addShpClicked.connect(self.addShpClicked)
        self.property_management.addPropertyClicked.connect(self.addPropertyClicked)
        self.property_management.removePropertyClicked.connect(self.removePropertyClicked)
        cl.addWidget(self.property_management)

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
        for btn in list(self._preferred_group.buttons()):
            self._preferred_group.removeButton(btn)
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
            chk.setObjectName("PreferredModulecb")
            chk.setEnabled(bool(has_access))
            chk.setProperty("moduleName", module_name)
            chk.toggled.connect(lambda checked, btn=chk: self._on_pref_toggled(btn, checked))
            self._preferred_group.addButton(chk)

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
            self.preferredModuleChanged.emit(module_name)
            return
        # Unchecked: if no other is checked, emit None to prefer welcome page
        any_other = any(cb.isChecked() for cb in self._check_by_module.values() if cb is not btn)
        if not any_other:
            self.preferredModuleChanged.emit(None)

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
                self._toggle_checkbox_from_target(cb)
            return True
        return super().eventFilter(obj, event)

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

    def _toggle_checkbox_from_target(self, checkbox):
        if not checkbox:
            return
        if checkbox.isChecked():
            self._preferred_group.setExclusive(False)
            checkbox.setChecked(False)
            self._preferred_group.setExclusive(True)
        else:
            checkbox.click()


