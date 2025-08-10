from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame, QHBoxLayout, QPushButton, QCheckBox
from ...languages.language_manager import LanguageManager
from ...widgets.theme_manager import ThemeManager
from .SettingsLogic import SettingsLogic
from ...constants.file_paths import QssPaths
from ...constants.module_names import PROJECTS_MODULE, CONTRACT_MODULE
from ...utils.GraphQLQueryLoader import GraphQLQueryLoader
from ...utils.api_client import APIClient
from ...constants.file_paths import QueryPaths, ConfigPaths
from ...utils.SessionManager import SessionManager

class SettingsUI(QWidget):
    """
    This module supports dynamic theme switching via ThemeManager.apply_module_style.
    Call retheme_settings() to re-apply QSS after a theme change.
    """
    def __init__(self, lang_manager=None, theme_manager=None, theme_dir=None, qss_files=None):
        super().__init__()
        from ...module_manager import SETTINGS_MODULE
        self.name = SETTINGS_MODULE
        # Ensure we always use LanguageManager
        if lang_manager is None:
            self.lang_manager = LanguageManager()
        elif not hasattr(lang_manager, 'sidebar_button'):
            language = getattr(lang_manager, 'language', None)
            self.lang_manager = LanguageManager(language=language) if language else LanguageManager()
        else:
            self.lang_manager = lang_manager
        self.theme_manager = theme_manager
        # Logic layer
        self.logic = SettingsLogic()
        self._cards = []
        self._initialized = False
        self._user_loaded = False
        self._user_labels = {}
        self._pills_container = None
        self._pill_checks = {}
        # Roles UI storage
        self._roles_container = None
        # Track settings changes (UI-level for buttons visibility)
        self._pending_changes = False
        self._pending_settings = {}
        self._original_settings = {}
        # Confirm buttons across cards
        self._confirm_btns = []
        # Modules available for module-specific cards
        self._available_modules = []
        self._module_cards = {}
        self.setup_ui()
        # Centralized theming
        ThemeManager.apply_module_style(self, [QssPaths.MAIN])

    def setup_ui(self):
        root = QVBoxLayout(self)
        # Scrollable area for setup cards
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.cards_container = QWidget(self)
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(12, 12, 12, 12)
        self.cards_layout.setSpacing(12)
        self.cards_layout.addStretch(1)
        self.scroll_area.setWidget(self.cards_container)
        root.addWidget(self.scroll_area)

        # Add one User card first
        user_card = self._build_user_setup_card()
        self._cards.append(user_card)
        self.cards_layout.insertWidget(0, user_card)
        # Apply card-specific theming if available
        try:
            ThemeManager.apply_module_style(user_card, [QssPaths.SETUP_CARD])
        except Exception:
            pass

        # Build module-specific cards if already known
        if self._available_modules:
            self._build_module_cards()

    def _build_user_setup_card(self) -> QWidget:
        card = QFrame(self)
        card.setObjectName("SetupCard")
        card.setFrameShape(QFrame.NoFrame)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)
        # Header
        hdr = QHBoxLayout(); hdr.setContentsMargins(0,0,0,0)
        # Show translated User name on the left
        title = QLabel(self.lang_manager.translate("User"))
        title.setObjectName("SetupCardTitle")
        hdr.addWidget(title, 0)
        hdr.addStretch(1)
        lay.addLayout(hdr)
        # Content
        content = QFrame(card); content.setObjectName("SetupCardContent")
        cl = QVBoxLayout(content); cl.setContentsMargins(0,0,0,0); cl.setSpacing(6)
        # User info labels (populated on activate)
        self._user_labels['id'] = QLabel("ID: —")
        self._user_labels['name'] = QLabel(self.lang_manager.translate("Name") + ": —")
        self._user_labels['email'] = QLabel(self.lang_manager.translate("Email") + ": —")
        cl.addWidget(self._user_labels['id'])
        cl.addWidget(self._user_labels['name'])
        # Roles section (directly after Name)
        roles_title = QLabel(self.lang_manager.translate("Roles"))
        roles_title.setObjectName("SetupCardSectionTitle")
        cl.addWidget(roles_title)
        self._roles_container = QFrame(content)
        self._roles_container.setObjectName("RolesPills")
        self._roles_layout = QHBoxLayout(self._roles_container)
        self._roles_layout.setContentsMargins(0,0,0,0)
        self._roles_layout.setSpacing(6)
        cl.addWidget(self._roles_container)
        # Email shown after roles
        cl.addWidget(self._user_labels['email'])
        # Module access pills section (populated on activate)
        pills_title = QLabel(self.lang_manager.translate("Module access"))
        pills_title.setObjectName("SetupCardSectionTitle")
        cl.addWidget(pills_title)
        self._pills_container = QFrame(content)
        self._pills_container.setObjectName("AccessPills")
        self._pills_layout = QHBoxLayout(self._pills_container)
        self._pills_layout.setContentsMargins(0,0,0,0)
        self._pills_layout.setSpacing(6)
        cl.addWidget(self._pills_container)
        lay.addWidget(content)
        # Footer actions: Confirm button appears when there are pending changes
        ftr = QHBoxLayout(); ftr.setContentsMargins(0,6,0,0)
        ftr.addStretch(1)
        confirm_btn = QPushButton(self.lang_manager.translate("Confirm"))
        confirm_btn.setEnabled(False)
        confirm_btn.setVisible(False)
        confirm_btn.clicked.connect(self._on_confirm_clicked)
        ftr.addWidget(confirm_btn)
        self._confirm_btns.append(confirm_btn)
        lay.addLayout(ftr)
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

    def _build_module_card(self, module_name: str) -> QWidget:
        card = QFrame(self)
        card.setObjectName("SetupCard")
        card.setFrameShape(QFrame.NoFrame)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)
        # Header
        hdr = QHBoxLayout(); hdr.setContentsMargins(0,0,0,0)
        title = QLabel(self.lang_manager.sidebar_button(module_name))
        title.setObjectName("SetupCardTitle")
        hdr.addWidget(title, 0)
        hdr.addStretch(1)
        lay.addLayout(hdr)
        # Content placeholder with red border
        content = QFrame(card)
        content.setObjectName("ModuleSettingsPlaceholder")
        content.setStyleSheet("border: 1px solid #d33; min-height: 64px; border-radius: 6px;")
        cl = QVBoxLayout(content); cl.setContentsMargins(8,8,8,8); cl.setSpacing(6)
        placeholder_lbl = QLabel(self.lang_manager.translate("Module settings placeholder"), content)
        cl.addWidget(placeholder_lbl)
        lay.addWidget(content)
        # Footer confirm button for this card (same behavior)
        ftr = QHBoxLayout(); ftr.setContentsMargins(0,6,0,0)
        ftr.addStretch(1)
        confirm_btn = QPushButton(self.lang_manager.translate("Confirm"))
        confirm_btn.setEnabled(False)
        confirm_btn.setVisible(False)
        confirm_btn.clicked.connect(self._on_confirm_clicked)
        ftr.addWidget(confirm_btn)
        self._confirm_btns.append(confirm_btn)
        lay.addLayout(ftr)
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
            # Build module cards if modules were provided before initialization
            if self._available_modules:
                self._build_module_cards()
        # Load user data once when activated
        if not getattr(self, '_user_loaded', False):
            try:
                user = self.logic.load_user(self.lang_manager)
                uid = user.get("id", "—")
                full_name = f"{user.get('firstName', '')} {user.get('lastName', '')}".strip() or "—"
                email = user.get("email", "—")
                # Update labels
                self._user_labels['id'].setText(f"ID: {uid}")
                self._user_labels['name'].setText(self.lang_manager.translate("Name") + f": {full_name}")
                self._user_labels['email'].setText(self.lang_manager.translate("Email") + f": {email}")
                # Update roles and module access pills
                role_names = self.logic.parse_roles(user.get("roles"))
                self._update_roles(role_names)
                self._update_module_pills(user.get("abilities"))
                # After pills are created, load original settings and sync UI
                self._load_original_settings()
                self._user_loaded = True
            except Exception as e:
                # Show error in place of user data
                self._user_labels['id'].setText(str(e))
        else:
            # Sync UI with original settings when re-activating
            self._apply_selection_to_pills(self.logic.get_original_preferred())
            self._set_dirty(False)

    def deactivate(self):
        pass

    def reset(self):
        pass

    def run(self):
        pass

    def get_widget(self):
        return self

    def retheme_settings(self):
        """
        Re-applies the correct theme and QSS to the settings UI and setup cards.
        """
        ThemeManager.apply_module_style(self, [QssPaths.MAIN])
        # Apply SetupCard styling to all current cards (user + modules)
        for card in list(getattr(self, '_cards', [])) + list(getattr(self, '_module_cards', {}).values()):
            try:
                ThemeManager.apply_module_style(card, [QssPaths.SETUP_CARD])
            except Exception:
                pass
        # Repolish dynamic styled widgets (pills) so properties reapply
        self._repolish_dynamic_widgets()

    def _repolish_dynamic_widgets(self):
        """Force Qt to re-evaluate style for dynamic-property-based pills after theme change."""
        def repolish(widget):
            try:
                widget.style().unpolish(widget)
                widget.style().polish(widget)
                widget.update()
            except Exception:
                pass
        # Access pills
        if getattr(self, '_pills_container', None):
            for i in range(self._pills_layout.count()):
                item = self._pills_layout.itemAt(i)
                w = item.widget()
                if isinstance(w, QFrame) and w.objectName() == 'AccessPill':
                    repolish(w)
        # Role pills
        if getattr(self, '_roles_container', None):
            for i in range(self._roles_layout.count()):
                item = self._roles_layout.itemAt(i)
                w = item.widget()
                if isinstance(w, QFrame) and w.objectName() == 'AccessPill':
                    repolish(w)

    def _update_roles(self, roles):
        # roles is a list of role names
        # Clear previous
        if hasattr(self, '_roles_layout'):
            while self._roles_layout.count():
                item = self._roles_layout.takeAt(0)
                w = item.widget()
                if w is not None:
                    w.setParent(None)
        # Build role pills (reuse AccessPill styling)
        for name in roles or []:
            pill = QFrame(self._roles_container)
            pill.setObjectName("AccessPill")
            pill.setProperty('active', True)
            pill.setProperty('inactive', False)
            pill.style().unpolish(pill); pill.style().polish(pill)
            hl = QHBoxLayout(pill); hl.setContentsMargins(6,0,6,0); hl.setSpacing(4)
            lbl = QLabel(name, pill)
            hl.addWidget(lbl)
            self._roles_layout.addWidget(pill)
        self._roles_layout.addStretch(1)

    def _update_module_pills(self, abilities):
        # Build pills based on access returned by logic
        access = self.logic.get_module_access_from_abilities(abilities)
        # Clear previous pills
        if hasattr(self, '_pills_container') and self._pills_container:
            while self._pills_layout.count():
                item = self._pills_layout.takeAt(0)
                w = item.widget()
                if w is not None:
                    w.setParent(None)
        self._pill_checks = {}
        # Build pills
        for module_name, has_access in access.items():
            label_text = self.lang_manager.sidebar_button(module_name)
            pill = QFrame(self._pills_container)
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
            # connect exclusivity + pending changes tracking (do NOT save immediately)
            def on_changed(state, m=module_name, cbox=chk):
                if state:  # checked
                    # uncheck others
                    for other_m, other_c in self._pill_checks.items():
                        if other_m != m and other_c.isChecked():
                            other_c.blockSignals(True)
                            other_c.setChecked(False)
                            other_c.blockSignals(False)
                    # set pending preferred module via logic
                    self.logic.set_pending_preferred(m)
                else:
                    # if all unchecked, clear pending preferred module
                    selected = self._get_selected_preferred_from_ui()
                    self.logic.set_pending_preferred(selected)
                self._update_dirty_state()
            chk.stateChanged.connect(on_changed)
            self._pill_checks[module_name] = chk
            self._pills_layout.addWidget(pill)
        self._pills_layout.addStretch(1)
        # Do not load preference here; handled by _load_original_settings

    # --- Change tracking helpers ---
    def _update_dirty_state(self):
        self._set_dirty(self.logic.has_unsaved_changes())

    def _set_dirty(self, dirty: bool):
        self._pending_changes = bool(dirty)
        # Toggle all confirm buttons across cards
        for btn in getattr(self, '_confirm_btns', []):
            try:
                btn.setVisible(self._pending_changes)
                btn.setEnabled(self._pending_changes)
            except Exception:
                pass

    def has_unsaved_changes(self) -> bool:
        return self.logic.has_unsaved_changes()

    def _get_selected_preferred_from_ui(self):
        for m, cb in self._pill_checks.items():
            if cb.isChecked():
                return m
        return None

    def _apply_selection_to_pills(self, module_name):
        # apply selection programmatically without toggling dirty
        for m, cb in self._pill_checks.items():
            cb.blockSignals(True)
            cb.setChecked(m == module_name)
            cb.blockSignals(False)
        # keep logic pending in sync with UI but not dirty
        self.logic.set_pending_preferred(module_name)
        self._set_dirty(False)

    def _load_original_settings(self):
        self.logic.load_original_settings()
        self._apply_selection_to_pills(self.logic.get_original_preferred())

    def _on_confirm_clicked(self):
        self.apply_pending_changes()

    def apply_pending_changes(self):
        # Persist settings via logic
        self.logic.apply_pending_changes()
        self._set_dirty(self.logic.has_unsaved_changes())

    def revert_pending_changes(self):
        # Revert UI to original settings, clear pending
        self.logic.revert_pending_changes()
        self._apply_selection_to_pills(self.logic.get_original_preferred())
