
import time
import json
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QFrame, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import pyqtSignal
from .SettinsUtils.userUtils import userUtils
from ...widgets.theme_manager import ThemeManager
from .SettinsUtils.SettingsLogic import SettingsLogic
from ...constants.file_paths import QssPaths
from ...constants.module_icons import IconNames
from .cards.SettingsUserCard import UserSettingsCard
from .cards.SettingsModuleCard import SettingsModuleCard
from ...utils.url_manager import Module
from ...module_manager import ModuleManager, MODULES_LIST_BY_NAME
from ...languages.translation_keys import TranslationKeys
from ...widgets.theme_manager import styleExtras, ThemeShadowColors
from ...python.workers import FunctionWorker, start_worker



from ...languages.language_manager import LanguageManager


class SettingsModule(QWidget):
    """
    This module supports dynamic theme switching via ThemeManager.apply_module_style.
    Call retheme_settings() to re-apply QSS after a theme change.
    """
    # Signals for user action buttons
    addShpClicked = pyqtSignal()
    addPropertyClicked = pyqtSignal()
    removePropertyClicked = pyqtSignal()

    def __init__(
            self,
        ):
        super().__init__()

        self.name = Module.SETTINGS.name
        
        self.lang_manager = LanguageManager()
        # Logic layer
        self.logic = SettingsLogic()
        self._cards = []
        self._pending_changes = False
        # Global footer controls
        self._footer_frame = None
        self._footer_confirm = None
        # Modules available for module-specific cards
        self._module_cards = {}
        self._user_fetch_thread = None
        self._user_fetch_worker = None
        self._user_fetch_request_id = 0
        self._settings_loaded_once = False
        self.user_payload = None
        self.setup_ui()
        # Centralized theming
        ThemeManager.apply_module_style(self, [QssPaths.SETUP_CARD])

    def setup_ui(self):
        root = QVBoxLayout(self)
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.cards_container = QWidget(self)
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(6, 6, 6, 6)
        self.cards_layout.setSpacing(6)
        self.cards_layout.addStretch(1)
        self.scroll_area.setWidget(self.cards_container)
        root.addWidget(self.scroll_area)

        # Add one User card first
        user_card = self._build_user_setup_card(payload=self.user_payload)
        self._cards.append(user_card)
        self.cards_layout.insertWidget(0, user_card)

        # Footer with shared confirm button
        self._footer_frame = QFrame(self)
        self._footer_frame.setObjectName("SetupCard")
        footer_layout = QHBoxLayout(self._footer_frame)
        footer_layout.setContentsMargins(2, 4, 2, 4)
        footer_layout.setSpacing(10)


        styleExtras.apply_chip_shadow(
            self._footer_frame,
            blur_radius=5,
            x_offset=1,
            y_offset=1,
            color=ThemeShadowColors.RED,
            alpha_level='medium'
        )
        footer_layout.addStretch(1)

        self._footer_confirm = QPushButton(
            self.lang_manager.translate(TranslationKeys.CONFIRM),
            self._footer_frame
        )
        self._footer_confirm.setObjectName("ConfirmButton")
        self._footer_confirm.setVisible(False)
        self._footer_confirm.setEnabled(False)
        self._footer_confirm.clicked.connect(self.apply_pending_changes)
        footer_layout.addWidget(self._footer_confirm, 0)

        root.addWidget(self._footer_frame)
        self._footer_frame.setVisible(False)

    def _build_user_setup_card(self, payload=None) -> QWidget:
        card = UserSettingsCard(self.lang_manager, payload)
        card.setObjectName("SetupCard")
        card.setProperty("cardTone", "user")
        card.preferredModuleChanged.connect(self._user_preferred_module_changed)
    
        self._user_card = card
        return card

    def _build_module_cards(self):
        # Remove existing module cards first
        for name, card in list(self._module_cards.items()):
            card.setParent(None)
        self._module_cards.clear()
        # Rebuild _cards to keep first (user) card, then module cards
        self._cards = self._cards[:1]
        insert_index = 1
        for module_name in MODULES_LIST_BY_NAME:
            if module_name == Module.HOME.name.capitalize():
                continue
            card = self._generate_module_card(module_name)
            self._module_cards[module_name] = card
            self.cards_layout.insertWidget(insert_index, card)
            self._cards.append(card)
            insert_index += 1
        return

    def _generate_module_card(self, module_name: str) -> QWidget:
 
        translated = self.lang_manager.translate(module_name.lower())

        module_manager = ModuleManager()
        supports_types, supports_statuses, supports_tags, supports_archive_layer = module_manager.getModuleSupports(module_name) or {}
        module_labels = module_manager.getModuleLabels(module_name)
        card = SettingsModuleCard(
            self.lang_manager,
            module_name,
            translated,
            supports_types,
            supports_statuses,
            supports_tags,
            supports_archive_layer,
            module_labels=module_labels,
            logic=self.logic,
        )

        card.setObjectName("SetupCard")
        card.setProperty("cardTone", module_name.lower())
 
        card.pendingChanged.connect(self._update_dirty_state)
 
        return card

    def _activate_module_cards(self):
        for card in self._module_cards.values():            
            card.on_settings_activate()
        return

    def activate(self):
        """Activates the Settings UI with fresh user data."""
        self._refresh_user_info()

    def _refresh_user_info(self):
        if self._user_fetch_thread is not None:
            self._cancel_user_fetch_worker()

        self._user_fetch_request_id += 1

        worker = FunctionWorker(userUtils.fetch_user_payload)
        worker.request_id = self._user_fetch_request_id
        worker.finished.connect(self._handle_user_worker_success)
        worker.error.connect(self._handle_user_worker_error)
        self._user_fetch_worker = worker
        self._user_fetch_thread = start_worker(worker, on_thread_finished=self._clear_user_worker_refs)

    def _handle_user_worker_success(self, payload):
        if not self._is_active_user_worker():
            return
        self._on_user_payload_ready(payload or {})

    def _handle_user_worker_error(self, message):
        if not self._is_active_user_worker():
            return
        print(f"[SettingsUI] Failed to load user info: {message}")
        self._on_user_payload_ready({})

    def _is_active_user_worker(self) -> bool:
        worker = self._user_fetch_worker
        if worker is None:
            return False
        request_id = worker.request_id
        return request_id == self._user_fetch_request_id

    def _on_user_payload_ready(self, payload: dict):
        user_data = payload or {}
        self.user_payload = user_data

        self._update_user_header(user_data)

        abilities = user_data.get("abilities", [])
        abilities = json.loads(abilities)

        has_qgis_access, can_create_property  = userUtils.has_property_rights(user_data)

        self._user_card.build_property_managment(can_create_property)

        subjects = userUtils.abilities_to_subjects(abilities)

        access_map = self.logic.get_module_access_from_abilities(subjects)
        self._user_card.build_and_set_access_controls(access_map)

        self.update_permissions = self.logic.get_module_update_permissions(subjects)
        allowed_modules = [name for name, allowed in access_map.items() if allowed]

        self._ensure_original_settings_loaded()
        preferred_module = self.logic.get_original_preferred()
        self._user_card.set_preferred(preferred_module)

        self._ensure_module_cards(
            allowed_modules=allowed_modules,
            access_map=access_map,
            update_permissions=self.update_permissions,
        )
        self._activate_module_cards()

    def _update_user_header(self, user_data: dict):
        userUtils.extract_and_set_user_labels(
            self._user_card.lbl_name,
            self._user_card.lbl_email,
            user_data,
        )
        roles = userUtils.get_roles_list(user_data.get("roles"))
        userUtils.set_roles(self._user_card.lbl_roles, roles)

    def _ensure_original_settings_loaded(self):
        if self._settings_loaded_once:
            return
        self.logic.load_original_settings()
        self._set_dirty(False)
        self._settings_loaded_once = True

    def _ensure_module_cards(self, *, allowed_modules, access_map, update_permissions):
        # Remove disallowed cards
        for name, card in list(self._module_cards.items()):
            if name not in allowed_modules:
                self.cards_layout.removeWidget(card)
                card.setParent(None)
                del self._module_cards[name]

        # Add missing allowed cards
        for module_name in allowed_modules:
            if module_name not in self._module_cards:
                card = self._generate_module_card(module_name)
                self._module_cards[module_name] = card
                self.cards_layout.addWidget(card)
            
        # Rebuild cards list: user card first, then current module cards
        self._cards = [self._user_card] + list(self._module_cards.values())




    def _make_payload_signature(self, payload):
        if not isinstance(payload, dict):
            return (None, tuple(), tuple())
        user_id = payload.get("id")
        try:
            roles_raw = payload.get("roles") or []
            roles_sig = tuple(sorted((str(r) for r in roles_raw), key=str))
        except Exception:
            roles_sig = tuple()
        try:
            abilities_raw = payload.get("abilities") or []
            abilities_sig = tuple(sorted((str(a) for a in abilities_raw), key=str))
        except Exception:
            abilities_sig = tuple()
        return (user_id, roles_sig, abilities_sig)

    def _clear_user_worker_refs(self):
        self._user_fetch_thread = None
        self._user_fetch_worker = None


    def _cancel_user_fetch_worker(self, invalidate_request: bool = False):
        if invalidate_request:
            self._user_fetch_request_id += 1
        worker = self._user_fetch_worker
        thread = self._user_fetch_thread
        if worker is not None:
            try:
                worker.finished.disconnect(self._handle_user_worker_success)
            except Exception:
                pass
            try:
                worker.error.disconnect(self._handle_user_worker_error)
            except Exception:
                pass
        if thread is not None and thread.isRunning():
            thread.quit()
            thread.wait(200)
        self._user_fetch_worker = None
        self._user_fetch_thread = None
     
    def deactivate(self):
        self._cancel_user_fetch_worker(invalidate_request=True)
        
        # Deactivate module cards to free memory
        for card in self._module_cards.values():
            try:
                card.on_settings_deactivate()
            except Exception:
                pass

    def reset(self):
        pass

    def run(self):
        pass

    def get_widget(self):
        """Return self as the widget for module system compatibility."""
        return self

    def retheme_settings(self):
        # Re-theme all existing cards
        for card in self._cards:
            ThemeManager.apply_module_style(card, [QssPaths.SETUP_CARD])
        if self._footer_frame is not None:
            ThemeManager.apply_module_style(self._footer_frame, [QssPaths.SETUP_CARD])


    # --- Handling unsaved changes ---
    def apply_pending_changes(self):
        for card in self._module_cards.values():
            card.apply()
        self.logic.apply_pending_changes()

        # Recompute dirty state using both logic + cards
        self._set_dirty(self.has_unsaved_changes())

    def revert_pending_changes(self):
        self.logic.revert_pending_changes()
        self._user_card.revert(self.logic.get_original_preferred())
        for card in self._module_cards.values():
            card.revert()
        self._set_dirty(False)

    def _user_preferred_module_changed(self, module_name):
        """Signal handler from SettingsUserCard when preferred module checkbox selection changes."""
        # module_name can be a string or None (cleared selection -> Welcome page)
        self.logic.set_user_preferred_module(module_name)
        self._update_dirty_state()


    def _update_dirty_state(self):
        # Combine user-card dirty with module cards dirty
        dirty = self.logic.has_unsaved_changes() or self._any_module_dirty()
        self._set_dirty(dirty)

    def _set_dirty(self, dirty: bool):
        self._pending_changes = bool(dirty)
        if self._footer_confirm is not None:
            self._footer_frame.setVisible(self._pending_changes)
            self._footer_confirm.setVisible(self._pending_changes)
            self._footer_confirm.setEnabled(self._pending_changes)

    def has_unsaved_changes(self) -> bool:
        # Combine user logic dirty with module card pending state
        try:
            logic_dirty = self.logic.has_unsaved_changes()
            module_dirty = self._any_module_dirty()
            return bool(logic_dirty or module_dirty)
        except Exception:
            # If logic fails, just check module cards
            try:
                return self._any_module_dirty()
            except Exception:
                # If everything fails, assume no changes
                return False

    def _any_module_dirty(self) -> bool:
        """Check if any module cards have pending changes."""
        for card in self._module_cards.values():
            if card.has_pending_changes():
                return True
        return False


    def confirm_navigation_away(self) -> bool:
        """Handle unsaved changes prompt when navigating away from Settings.
        
        Args:
            parent_dialog: The parent dialog for QMessageBox
            
        Returns:
            True if navigation may proceed, False to cancel
        """
        if not self.has_unsaved_changes():
            return True
            
        try:
            from PyQt5.QtWidgets import QMessageBox
            
            mbox = QMessageBox(self)
            mbox.setIcon(ThemeManager.get_qicon(IconNames.WARNING))
            mbox.setWindowTitle(self.tr("Unsaved changes"))
            mbox.setText(self.tr("You have unsaved Settings changes."))
            mbox.setInformativeText(self.tr("Do you want to save your changes or discard them?"))
            save_btn = mbox.addButton(self.tr("Save"), QMessageBox.AcceptRole)
            discard_btn = mbox.addButton(self.tr("Discard"), QMessageBox.DestructiveRole)
            cancel_btn = mbox.addButton(self.tr("Cancel"), QMessageBox.RejectRole)
            mbox.setDefaultButton(save_btn)
            mbox.exec_()
            
            clicked = mbox.clickedButton()
            if clicked == save_btn:
                self.apply_pending_changes()
                return True
            elif clicked == discard_btn:
                self.revert_pending_changes()
                return True
            else:
                # Cancel
                return False
        except Exception as e:
            print(f"Settings navigation prompt failed: {e}", "error")
            return True

   
