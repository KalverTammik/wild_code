from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame, QHBoxLayout, QPushButton, QCheckBox
from ...languages.language_manager import LanguageManager
from ...widgets.theme_manager import ThemeManager
# from .SettingsLogic import SettingsLogic  # Not needed for mock UI
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
        # self.logic = SettingsLogic()  # Not used in mock phase
        self._cards = []
        self._initialized = False
        self._user_loaded = False
        self._user_labels = {}
        self._pills_container = None
        self._pill_checks = {}
        # Track settings changes
        self._pending_changes = False
        self._pending_settings = {}
        self._original_settings = {}
        self._confirm_btn = None
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

        # Add one mock card to demonstrate UI/UX (no functionality)
        mock = self._build_mock_setup_card()
        self._cards.append(mock)
        self.cards_layout.insertWidget(0, mock)
        # Apply card-specific theming if available
        try:
            ThemeManager.apply_module_style(mock, [QssPaths.SETUP_CARD])
        except Exception:
            pass

    def _build_mock_setup_card(self) -> QWidget:
        card = QFrame(self)
        card.setObjectName("SetupCard")
        card.setFrameShape(QFrame.NoFrame)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)
        # Header
        hdr = QHBoxLayout(); hdr.setContentsMargins(0,0,0,0)
        title = QLabel(self.lang_manager.translate("Layer Setup (Mock)"))
        title.setObjectName("SetupCardTitle")
        desc = QLabel(self.lang_manager.translate("Configure project-related options. This is a mock card for UI/UX only."))
        desc.setObjectName("SetupCardDescription")
        desc.setWordWrap(True)
        hdr.addWidget(title, 0)
        hdr.addStretch(1)
        lay.addLayout(hdr)
        lay.addWidget(desc)
        # Content (placeholder)
        content = QFrame(card); content.setObjectName("SetupCardContent")
        cl = QVBoxLayout(content); cl.setContentsMargins(0,0,0,0); cl.setSpacing(6)
        # User info labels (populated on activate)
        self._user_labels['id'] = QLabel("ID: —")
        self._user_labels['name'] = QLabel(self.lang_manager.translate("Name") + ": —")
        self._user_labels['email'] = QLabel(self.lang_manager.translate("Email") + ": —")
        cl.addWidget(self._user_labels['id'])
        cl.addWidget(self._user_labels['name'])
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
        self._confirm_btn = QPushButton(self.lang_manager.translate("Confirm"))
        self._confirm_btn.setEnabled(False)
        self._confirm_btn.setVisible(False)
        self._confirm_btn.clicked.connect(self._on_confirm_clicked)
        ftr.addWidget(self._confirm_btn)
        lay.addLayout(ftr)
        return card

    def activate(self):
        if not self._initialized:
            self._initialized = True
            # Future: create cards from registry and bind state
            pass
        # Load user data once when activated
        if not getattr(self, '_user_loaded', False):
            try:
                ql = GraphQLQueryLoader(self.lang_manager)
                api = APIClient(self.lang_manager, SessionManager(), ConfigPaths.CONFIG)
                query = ql.load_query("USER", "me.graphql")
                data = api.send_query(query)
                user = data.get("me", {}) or {}
                uid = user.get("id", "—")
                full_name = f"{user.get('firstName', '')} {user.get('lastName', '')}".strip() or "—"
                email = user.get("email", "—")
                # Update labels
                self._user_labels['id'].setText(f"ID: {uid}")
                self._user_labels['name'].setText(self.lang_manager.translate("Name") + f": {full_name}")
                self._user_labels['email'].setText(self.lang_manager.translate("Email") + f": {email}")
                # Update module access pills
                self._update_module_pills(user.get("abilities"))
                # After pills are created, load original settings and sync UI
                self._load_original_settings()
                self._user_loaded = True
            except Exception as e:
                # Show error in place of user data
                self._user_labels['id'].setText(str(e))
        else:
            # Sync UI with original settings when re-activating (in case theme or other events)
            self._apply_selection_to_pills(self._original_settings.get('preferred_module'))
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
        for card in getattr(self, '_cards', []):
            try:
                ThemeManager.apply_module_style(card, [QssPaths.SETUP_CARD])
            except Exception:
                pass

    def _update_module_pills(self, abilities):
        import json
        # Normalize abilities to list of dicts
        if isinstance(abilities, str):
            try:
                abilities = json.loads(abilities)
            except Exception:
                abilities = []
        abilities = abilities or []
        subjects = set()
        for ab in abilities:
            subj = ab.get('subject')
            if isinstance(subj, list) and subj:
                subjects.add(str(subj[0]))
            elif isinstance(subj, str):
                subjects.add(subj)
        # Map subjects to plugin modules we show
        subject_to_module = {
            'Project': PROJECTS_MODULE,
            'Contract': CONTRACT_MODULE,
        }
        # Clear previous pills
        if hasattr(self, '_pills_container') and self._pills_container:
            # remove widgets from layout
            while self._pills_layout.count():
                item = self._pills_layout.takeAt(0)
                w = item.widget()
                if w is not None:
                    w.setParent(None)
        self._pill_checks = {}
        # Build pills
        for subject, module_name in subject_to_module.items():
            has_access = subject in subjects
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
                    # set pending preferred module
                    self._pending_settings['preferred_module'] = m
                else:
                    # if all unchecked, clear pending preferred module
                    if all(not cb.isChecked() for cb in self._pill_checks.values()):
                        self._pending_settings['preferred_module'] = None
                    else:
                        # some other checkbox became checked, handled there
                        pass
                self._update_dirty_state()
            chk.stateChanged.connect(on_changed)
            self._pill_checks[module_name] = chk
            self._pills_layout.addWidget(pill)
        self._pills_layout.addStretch(1)
        # Do not load preference here; handled by _load_original_settings

    # --- Change tracking helpers ---
    def _update_dirty_state(self):
        orig = self._original_settings.get('preferred_module', None)
        curr = self._pending_settings.get('preferred_module', self._get_selected_preferred_from_ui())
        dirty = (curr or None) != (orig or None)
        self._set_dirty(dirty)

    def _set_dirty(self, dirty: bool):
        self._pending_changes = bool(dirty)
        if self._confirm_btn is not None:
            self._confirm_btn.setVisible(self._pending_changes)
            self._confirm_btn.setEnabled(self._pending_changes)

    def has_unsaved_changes(self) -> bool:
        return bool(self._pending_changes)

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
        # keep pending in sync with UI but not dirty
        if module_name is None:
            if 'preferred_module' in self._pending_settings:
                del self._pending_settings['preferred_module']
        else:
            self._pending_settings['preferred_module'] = module_name
        self._set_dirty(False)

    def _load_original_settings(self):
        try:
            from qgis.core import QgsSettings
            s = QgsSettings()
            pref = s.value("wild_code/preferred_module", "") or None
        except Exception:
            pref = None
        self._original_settings['preferred_module'] = pref
        # Sync UI without marking dirty
        self._apply_selection_to_pills(pref)

    def _on_confirm_clicked(self):
        self.apply_pending_changes()

    def apply_pending_changes(self):
        # Persist settings
        try:
            from qgis.core import QgsSettings
            s = QgsSettings()
            pref = self._pending_settings.get('preferred_module', self._get_selected_preferred_from_ui())
            if pref:
                s.setValue("wild_code/preferred_module", pref)
            else:
                s.remove("wild_code/preferred_module")
            # Update originals and clear dirty
            self._original_settings['preferred_module'] = pref
            self._set_dirty(False)
        except Exception:
            # If settings fail to save, keep dirty so user can retry
            pass

    def revert_pending_changes(self):
        # Revert UI to original settings, clear pending
        self._apply_selection_to_pills(self._original_settings.get('preferred_module'))
        self._set_dirty(False)
