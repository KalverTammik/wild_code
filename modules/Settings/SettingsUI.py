from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea
from ...languages.language_manager import LanguageManager
from ...widgets.theme_manager import ThemeManager
from .SettingsLogic import SettingsLogic
from ...constants.file_paths import QssPaths
from .cards.UserCard import UserCard
from .cards.ModuleCard import ModuleCard

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
        # Legacy attributes removed after refactor
        # self._user_labels = {}
        # self._pills_container = None
        # self._pill_checks = {}
        # self._roles_container = None
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
        card = UserCard(self.lang_manager)
        # Wire confirm button
        card.confirm_button().clicked.connect(self._on_confirm_clicked)
        # When user selects a preferred module, update logic + dirty state
        card.preferredChanged.connect(self._on_user_preferred_changed)
        self._confirm_btns.append(card.confirm_button())
        # Keep references needed for labels and later use
        self._user_card = card
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
        translated = self.lang_manager.sidebar_button(module_name)
        card = ModuleCard(self.lang_manager, module_name, translated)
        card.confirm_button().clicked.connect(self._on_confirm_clicked)
        self._confirm_btns.append(card.confirm_button())
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
                # Update labels
                self._user_card.set_user(user)
                # Update roles and module access pills
                role_names = self.logic.parse_roles(user.get("roles"))
                self._user_card.set_roles(role_names)
                access_map = self.logic.get_module_access_from_abilities(user.get("abilities"))
                self._user_card.set_access_map(access_map, label_resolver=self.lang_manager.sidebar_button)
                # After pills are created, load original settings and sync UI
                self._load_original_settings()
                self._user_loaded = True
            except Exception as e:
                # Show error in place of user data
                self._user_card.lbl_id.setText(str(e))
        else:
            # Sync UI with original settings when re-activating
            self._user_card.set_preferred(self.logic.get_original_preferred())
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
        # Each card manages its own SetupCard styling
        for card in list(getattr(self, '_cards', [])) + list(getattr(self, '_module_cards', {}).values()):
            try:
                card.retheme()
            except Exception:
                ThemeManager.apply_module_style(card, [QssPaths.SETUP_CARD])

    def apply_pending_changes(self):
        # Persist settings via logic
        self.logic.apply_pending_changes()
        # Let card perform any post-apply UI sync
        self._user_card.apply()
        self._set_dirty(self.logic.has_unsaved_changes())

    def revert_pending_changes(self):
        # Revert UI to original settings, clear pending
        self.logic.revert_pending_changes()
        self._user_card.revert(self.logic.get_original_preferred())
        self._set_dirty(False)

    def _load_original_settings(self):
        """Load original settings from logic and reflect in UserCard without marking dirty."""
        self.logic.load_original_settings()
        self._user_card.set_preferred(self.logic.get_original_preferred())
        self._set_dirty(False)

    def _on_user_preferred_changed(self, module_name):
        """Signal handler from UserCard when preferred module checkbox selection changes."""
        self.logic.set_pending_preferred(module_name)
        self._update_dirty_state()

    def _on_confirm_clicked(self):
        self.apply_pending_changes()

    def _update_dirty_state(self):
        self._set_dirty(self.logic.has_unsaved_changes())

    def _set_dirty(self, dirty: bool):
        self._pending_changes = bool(dirty)
        for btn in getattr(self, '_confirm_btns', []):
            try:
                btn.setVisible(self._pending_changes)
                btn.setEnabled(self._pending_changes)
            except Exception:
                pass

    def has_unsaved_changes(self) -> bool:
        return self.logic.has_unsaved_changes()
