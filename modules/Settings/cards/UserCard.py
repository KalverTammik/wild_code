# user_card.py
from PyQt5.QtCore import pyqtSignal, Qt, QEvent
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QCheckBox
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
    """
    preferredChanged = pyqtSignal(object)

    def __init__(self, lang_manager):
        super().__init__(lang_manager, lang_manager.translate("User"), None)

        cw = self.content_widget()
        cl = QVBoxLayout(cw)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(6)

        # ---------- Info ----------
        self.lbl_id = QLabel("ID: —", cw)
        self.lbl_name = QLabel(self.lang_manager.translate("Name") + ": —", cw)
        self.lbl_email = QLabel(self.lang_manager.translate("Email") + ": —", cw)

        info = QVBoxLayout()
        info.setContentsMargins(0, 0, 0, 0)
        info.setSpacing(2)
        info.addWidget(self.lbl_id)
        info.addWidget(self.lbl_name)
        cl.addLayout(info)

        # ---------- Roles (read-only pills) ----------
        roles_title = QLabel(self.lang_manager.translate("Roles"), cw)
        roles_title.setObjectName("SetupCardSectionTitle")
        cl.addWidget(roles_title)

        self.roles_container = QFrame(cw)
        self.roles_container.setObjectName("RolesPills")
        self.roles_layout = QHBoxLayout(self.roles_container)
        self.roles_layout.setContentsMargins(0, 0, 0, 0)
        self.roles_layout.setSpacing(6)
        cl.addWidget(self.roles_container)

        # Email under roles (matches your screenshot)
        cl.addWidget(self.lbl_email)

        # ---------- Module access (pills + checkboxes) ----------
        pills_title = QLabel(self.lang_manager.translate("Module access"), cw)
        pills_title.setObjectName("SetupCardSectionTitle")
        cl.addWidget(pills_title)

        self.access_container = QFrame(cw)
        self.access_container.setObjectName("AccessPills")
        self.access_layout = QHBoxLayout(self.access_container)
        self.access_layout.setContentsMargins(0, 0, 0, 0)
        self.access_layout.setSpacing(6)
        cl.addWidget(self.access_container)

        # Internal state
        self._check_by_module = {}
        self._pill_click_targets = {}

    # ---------- Public API (SettingsUI uses these) ----------
    def set_user(self, user: dict):
        uid = user.get("id", "—")
        full_name = f"{user.get('firstName', '')} {user.get('lastName', '')}".strip() or "—"
        email = user.get("email", "—")

        self.lbl_id.setText(f"ID: {uid}")
        self.lbl_name.setText(self.lang_manager.translate("Name") + f": {full_name}")
        self.lbl_email.setText(self.lang_manager.translate("Email") + f": {email}")

    def set_roles(self, roles):
        self._clear_layout(self.roles_layout)
        for name in roles or []:
            pill = QFrame(self.roles_container)
            pill.setObjectName("AccessPill")
            pill.setProperty("active", True)
            pill.setProperty("inactive", False)
            pill.style().unpolish(pill); pill.style().polish(pill)

            hl = QHBoxLayout(pill)
            hl.setContentsMargins(6, 0, 6, 0)
            hl.setSpacing(4)

            lbl = QLabel(name, pill)
            hl.addWidget(lbl)
            self.roles_layout.addWidget(pill)

        self.roles_layout.addStretch(1)

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
            hl.setContentsMargins(6, 0, 6, 0)
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

    def retheme(self):
        super().retheme()
        # Repolish dynamic widgets so [active]/[inactive] QSS is reapplied
        self._repolish_pills(self.access_layout)
        self._repolish_pills(self.roles_layout)

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
