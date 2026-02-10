
import time
import json
from functools import partial
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QFrame, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import pyqtSignal, QTimer
from ...utils.auth.user_utils import UserUtils
from ...widgets.theme_manager import ThemeManager
from .SettinsUtils.SettingsLogic import SettingsLogic
from ...constants.file_paths import QssPaths
from ...constants.module_icons import IconNames
from ...constants.button_props import ButtonVariant
from ...constants.file_paths import ConfigPaths
from .cards.SettingsUserCard import UserSettingsCard
from .cards.SettingsModuleCard import SettingsModuleCard
from ...utils.url_manager import Module
from ...module_manager import ModuleManager, MODULES_LIST_BY_NAME
from ...languages.translation_keys import TranslationKeys
from ...widgets.theme_manager import styleExtras, ThemeShadowColors
from ...python.workers import FunctionWorker, start_worker
from ...python.GraphQLQueryLoader import GraphQLQueryLoader
from ...python.api_client import APIClient
from ...utils.SessionManager import SessionManager
from ...utils.messagesHelper import ModernMessageDialog
from ...Logs.switch_logger import SwitchLogger
from ...Logs.python_fail_logger import PythonFailLogger
from ...ui.mixins.token_mixin import TokenMixin



from ...languages.language_manager import LanguageManager


class SettingsModule(TokenMixin, QWidget):
    """
    This module supports dynamic theme switching via ThemeManager.apply_module_style.
    Call retheme_settings() to re-apply QSS after a theme change.
    """
    # Signals for user action buttons
    addShpClicked = pyqtSignal()
    addPropertyClicked = pyqtSignal()

    def __init__(
            self,
        ):
        QWidget.__init__(self)
        TokenMixin.__init__(self)

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
        self._allowed_modules = []
        self._user_fetch_thread = None
        self._user_fetch_worker = None
        self._settings_loaded_once = False
        self.user_payload = None
        self._pending_module_queue = []
        self._pending_allowed_set = set()
        self._pending_build_active = False
        self.setup_ui()
        # Centralized theming
        self.retheme_settings()

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
        self._footer_confirm.setProperty("variant", ButtonVariant.PRIMARY)
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

    def _build_module_cards(self, allowed_modules=None):
        """Build module cards only for allowed modules (no full rebuild)."""
        allowed = list(allowed_modules or self._allowed_modules or [])
        self._ensure_module_cards(allowed_modules=allowed)
        return

    def _generate_module_card(self, module_name: str) -> QWidget:
 
        translated = self.lang_manager.translate_module_name(module_name)

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

    def sync_module_archive_layer_dropdown(self, module_key: str, layer_name: str, *, force: bool = True) -> bool:
        """Best-effort: update a module card's archive-layer dropdown to match persisted settings."""

        key = (module_key or "").strip().lower()
        if not key:
            return False

        for card in (self._module_cards or {}).values():
            try:
                if getattr(card, "module_key", "") == key:
                    return bool(card.sync_archive_layer_selection(layer_name, force=force))
            except Exception:
                continue

        return False

    def activate(self):
        """Activates the Settings UI with fresh user data."""
        self.mark_activated(self._active_token)
        self._refresh_user_info()

    def _refresh_user_info(self):
        if self._user_fetch_thread is not None:
            self._cancel_user_fetch_worker()

        query_loader = GraphQLQueryLoader()
        api_client = APIClient(SessionManager(), ConfigPaths.CONFIG)
        fetcher = partial(UserUtils.fetch_user_payload, query_loader, api_client)
        worker = FunctionWorker(fetcher)
        worker.active_token = self._active_token
        worker.finished.connect(self._handle_user_worker_success)
        worker.error.connect(self._handle_user_worker_error)
        self._user_fetch_worker = worker
        self._user_fetch_thread = start_worker(worker, on_thread_finished=self._clear_user_worker_refs)

    def _handle_user_worker_success(self, payload):
        if not self.is_token_active(getattr(self._user_fetch_worker, "active_token", None)):
            return
        self._on_user_payload_ready(payload or {})

    def _handle_user_worker_error(self, message):
        if not self.is_token_active(getattr(self._user_fetch_worker, "active_token", None)):
            return
        PythonFailLogger.log_exception(
            Exception(str(message)),
            module=Module.SETTINGS.value,
            event="settings_user_fetch_failed",
        )
        self._on_user_payload_ready({})


    def _on_user_payload_ready(self, payload: dict):
        user_data = payload or {}
        self.user_payload = user_data

        self._update_user_header(user_data)

        abilities = UserUtils.parse_abilities(user_data.get("abilities", []))

        has_qgis_access, can_create_property  = UserUtils.has_property_rights(user_data)

        self._user_card.build_property_managment(can_create_property)

        subjects = UserUtils.abilities_to_subjects(abilities)

        access_map = self.logic.get_module_access_from_abilities(subjects)
        self._user_card.build_and_set_access_controls(access_map)

        self.update_permissions = self.logic.get_module_update_permissions(subjects)
        allowed_modules = [name for name, allowed in access_map.items() if allowed]
        self._allowed_modules = list(allowed_modules)

        self._ensure_original_settings_loaded()
        preferred_module = self.logic.get_original_preferred()
        self._user_card.set_preferred(preferred_module)

        self._ensure_module_cards(allowed_modules=allowed_modules)

    def _update_user_header(self, user_data: dict):
        dash = self.lang_manager.translate(TranslationKeys.SETTINGS_UTILS_DASH)
        header = UserUtils.extract_user_header(user_data, dash)
        self._user_card.lbl_name.setText(header["full_name"])
        self._user_card.lbl_email.setText(header["email"])
        roles = UserUtils.get_roles_list(user_data.get("roles"))
        roles_text = ", ".join(roles) if roles else dash
        self._user_card.lbl_roles.setText(roles_text)

    def _ensure_original_settings_loaded(self):
        if self._settings_loaded_once:
            return
        self.logic.load_original_settings()
        self._set_dirty(False)
        self._settings_loaded_once = True

    def _ensure_module_cards(self, *, allowed_modules):
        allowed = [name for name in (allowed_modules or []) if name]
        current = set(self._module_cards.keys())
        target = set(allowed)

        # Remove disallowed cards
        for name, card in list(self._module_cards.items()):
            if name not in target:
                self._dispose_module_card(card)
                del self._module_cards[name]

        # Queue missing allowed cards for incremental build
        self._pending_allowed_set = set(allowed)
        self._pending_module_queue = [name for name in allowed if name not in self._module_cards]
        if not self._pending_build_active:
            self._pending_build_active = True
            QTimer.singleShot(0, self._build_next_module_card)

        # Rebuild cards list: user card first, then current module cards
        self._cards = [self._user_card] + list(self._module_cards.values())

    def _build_next_module_card(self) -> None:
        while self._pending_module_queue:
            module_name = self._pending_module_queue.pop(0)
            if module_name in self._module_cards:
                continue
            if module_name not in self._pending_allowed_set:
                continue
            card = self._generate_module_card(module_name)
            self._module_cards[module_name] = card
            try:
                self.cards_container.setUpdatesEnabled(False)
            except Exception:
                pass
            try:
                insert_at = max(0, self.cards_layout.count() - 1)
                self.cards_layout.insertWidget(insert_at, card)
            finally:
                try:
                    self.cards_container.setUpdatesEnabled(True)
                    self.cards_container.update()
                except Exception:
                    pass
            try:
                card.on_settings_activate()
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module=Module.SETTINGS.value,
                    event="settings_card_activate_failed",
                )
            self._cards = [self._user_card] + list(self._module_cards.values())
            QTimer.singleShot(0, self._build_next_module_card)
            return

        self._pending_build_active = False

    def _dispose_module_card(self, card: QWidget) -> None:
        if not card:
            return
        try:
            if hasattr(card, "on_settings_deactivate"):
                card.on_settings_deactivate()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.SETTINGS.value,
                event="settings_card_deactivate_failed",
            )
        try:
            if hasattr(card, "pendingChanged"):
                card.pendingChanged.disconnect(self._update_dirty_state)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.SETTINGS.value,
                event="settings_card_disconnect_failed",
            )
        try:
            self.cards_layout.removeWidget(card)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.SETTINGS.value,
                event="settings_card_remove_failed",
            )
        try:
            card.setParent(None)
            card.deleteLater()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.SETTINGS.value,
                event="settings_card_delete_failed",
            )




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
            self.bump_token()
        worker = self._user_fetch_worker
        thread = self._user_fetch_thread
        if worker is not None:
            try:
                worker.finished.disconnect(self._handle_user_worker_success)
            except Exception:
                PythonFailLogger.log_exception(
                    Exception("settings_disconnect_finished_failed"),
                    module=Module.SETTINGS.value,
                    event="settings_disconnect_finished_failed",
                )
            try:
                worker.error.disconnect(self._handle_user_worker_error)
            except Exception:
                PythonFailLogger.log_exception(
                    Exception("settings_disconnect_error_failed"),
                    module=Module.SETTINGS.value,
                    event="settings_disconnect_error_failed",
                )
        if thread is not None and thread.isRunning():
            thread.quit()
            thread.wait(200)
        self._user_fetch_worker = None
        self._user_fetch_thread = None
     
    def deactivate(self):
        self.mark_deactivated(bump_token=True)
        self._cancel_user_fetch_worker(invalidate_request=False)
        
        # Deactivate module cards to free memory
        for card in self._module_cards.values():
            try:
                card.on_settings_deactivate()
            except Exception:
                PythonFailLogger.log_exception(
                    Exception("settings_card_deactivate_failed"),
                    module=Module.SETTINGS.value,
                    event="settings_card_deactivate_failed",
                )

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
            # If everything fails, assume dirty to avoid data loss
            return True

    def _any_module_dirty(self) -> bool:
        """Check if any module cards have pending changes."""
        for card in self._module_cards.values():
            if card.has_pending_changes():
                return True
        return False


    def confirm_navigation_away(self, parent=None) -> bool:
        """Handle unsaved changes prompt when navigating away from Settings.
        
        Args:
            parent: Parent dialog for the prompt (optional).

        Returns:
            True if navigation may proceed, False to cancel.
        """
        if not self.has_unsaved_changes():
            return True
            
        try:
            title = self.tr("Unsaved changes")
            text = self.tr("You have unsaved Settings changes.")
            detail = self.tr("Do you want to save your changes or discard them?")
            save_label = self.lang_manager.translate(TranslationKeys.SAVE)
            discard_label = self.tr("Discard")
            cancel_label = self.lang_manager.translate(TranslationKeys.CANCEL_BUTTON)
            choice = ModernMessageDialog.ask_choice_modern(
                title,
                f"{text}\n\n{detail}",
                buttons=[save_label, discard_label, cancel_label],
                default=save_label,
                cancel=cancel_label,
                icon_name=IconNames.WARNING,
            )

            if choice == save_label:
                self.apply_pending_changes()
                return True
            if choice == discard_label:
                self.revert_pending_changes()
                return True
            return False
        except Exception as e:
            PythonFailLogger.log_exception(
                e,
                module=Module.SETTINGS.value,
                event="settings_navigation_prompt_failed",
            )
            return False

    def is_token_active(self, token: int | None) -> bool:
        return super().is_token_active(token)

   
