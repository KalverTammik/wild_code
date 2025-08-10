from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QFrame, QCheckBox
from .BaseCard import BaseCard

class UserCard(BaseCard):
    preferredChanged = pyqtSignal(object)  # emits selected module name or None

    def __init__(self, lang_manager):
        super().__init__(lang_manager, lang_manager.translate("User"))
        # Build specific content
        cw = self.content_widget()
        cl = QVBoxLayout(cw); cl.setContentsMargins(0,0,0,0); cl.setSpacing(6)
        self.lbl_id = QLabel("ID: —", cw)
        self.lbl_name = QLabel(self.lang_manager.translate("Name") + ": —", cw)
        self.lbl_email = QLabel(self.lang_manager.translate("Email") + ": —", cw)
        cl.addWidget(self.lbl_id)
        cl.addWidget(self.lbl_name)
        # Roles
        roles_title = QLabel(self.lang_manager.translate("Roles"), cw)
        roles_title.setObjectName("SetupCardSectionTitle")
        cl.addWidget(roles_title)
        self.roles_container = QFrame(cw)
        self.roles_container.setObjectName("RolesPills")
        self.roles_layout = QHBoxLayout(self.roles_container)
        self.roles_layout.setContentsMargins(0,0,0,0)
        self.roles_layout.setSpacing(6)
        cl.addWidget(self.roles_container)
        # Email after roles
        cl.addWidget(self.lbl_email)
        # Module access section
        pills_title = QLabel(self.lang_manager.translate("Module access"), cw)
        pills_title.setObjectName("SetupCardSectionTitle")
        cl.addWidget(pills_title)
        self.access_container = QFrame(cw)
        self.access_container.setObjectName("AccessPills")
        self.access_layout = QHBoxLayout(self.access_container)
        self.access_layout.setContentsMargins(0,0,0,0)
        self.access_layout.setSpacing(6)
        cl.addWidget(self.access_container)
        # Internal state
        self._pill_checks = {}

    # Public API used by SettingsUI
    def set_user(self, user: dict):
        uid = user.get("id", "—")
        full_name = f"{user.get('firstName', '')} {user.get('lastName', '')}".strip() or "—"
        email = user.get("email", "—")
        self.lbl_id.setText(f"ID: {uid}")
        self.lbl_name.setText(self.lang_manager.translate("Name") + f": {full_name}")
        self.lbl_email.setText(self.lang_manager.translate("Email") + f": {email}")

    def set_roles(self, roles):
        # Clear previous
        while self.roles_layout.count():
            item = self.roles_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
        # Build role pills (reuse AccessPill styling)
        for name in roles or []:
            pill = QFrame(self.roles_container)
            pill.setObjectName("AccessPill")
            pill.setProperty('active', True)
            pill.setProperty('inactive', False)
            pill.style().unpolish(pill); pill.style().polish(pill)
            hl = QHBoxLayout(pill); hl.setContentsMargins(6,0,6,0); hl.setSpacing(4)
            lbl = QLabel(name, pill)
            hl.addWidget(lbl)
            self.roles_layout.addWidget(pill)
        self.roles_layout.addStretch(1)

    def set_access_map(self, access_map: dict, label_resolver=None):
        # Clear previous
        while self.access_layout.count():
            item = self.access_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
        self._pill_checks = {}
        # Build pills
        for module_name, has_access in (access_map or {}).items():
            label_text = label_resolver(module_name) if label_resolver else module_name
            pill = QFrame(self.access_container)
            pill.setObjectName("AccessPill")
            hl = QHBoxLayout(pill); hl.setContentsMargins(6,0,6,0); hl.setSpacing(4)
            chk = QCheckBox(pill)
            chk.setObjectName("PreferredModuleCheck")
            chk.setEnabled(has_access)
            txt = QLabel(label_text, pill)
            # set dynamic properties for QSS coloring
            if has_access:
                pill.setProperty('active', True)
                pill.setProperty('inactive', False)
                f = txt.font(); f.setStrikeOut(False); txt.setFont(f)
            else:
                pill.setProperty('active', False)
                pill.setProperty('inactive', True)
                f = txt.font(); f.setStrikeOut(True); txt.setFont(f)
            pill.style().unpolish(pill); pill.style().polish(pill)
            hl.addWidget(chk)
            hl.addWidget(txt)
            hl.addStretch(1)

            def on_changed(state, m=module_name, cbox=chk):
                if state:  # checked
                    # uncheck others
                    for other_m, other_c in self._pill_checks.items():
                        if other_m != m and other_c.isChecked():
                            other_c.blockSignals(True)
                            other_c.setChecked(False)
                            other_c.blockSignals(False)
                # emit currently selected preferred (or None)
                self.preferredChanged.emit(self.get_selected_preferred())
            chk.stateChanged.connect(on_changed)
            self._pill_checks[module_name] = chk
            self.access_layout.addWidget(pill)
        self.access_layout.addStretch(1)

    def set_preferred(self, module_name):
        # apply selection programmatically without emitting signal
        for m, cb in self._pill_checks.items():
            cb.blockSignals(True)
            cb.setChecked(m == module_name)
            cb.blockSignals(False)

    def get_selected_preferred(self):
        for m, cb in self._pill_checks.items():
            if cb.isChecked():
                return m
        return None

    def apply(self):
        """Hook called after settings are applied. Keep for future if UI needs post-apply sync."""
        pass

    def revert(self, preferred_module_name):
        """Hook called on revert to reset UI selection to original preferred module."""
        self.set_preferred(preferred_module_name)

    def retheme(self):
        super().retheme()
        # repolish dynamic widgets
        def repolish(widget):
            try:
                widget.style().unpolish(widget)
                widget.style().polish(widget)
                widget.update()
            except Exception:
                pass
        # Access pills
        for i in range(self.access_layout.count()):
            item = self.access_layout.itemAt(i)
            w = item.widget()
            if isinstance(w, QFrame) and w.objectName() == 'AccessPill':
                repolish(w)
        # Role pills
        for i in range(self.roles_layout.count()):
            item = self.roles_layout.itemAt(i)
            w = item.widget()
            if isinstance(w, QFrame) and w.objectName() == 'AccessPill':
                repolish(w)
