
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QFrame, QHBoxLayout, QPushButton
from PyQt5.QtCore import pyqtSignal, QTimer
from ...utils.auth.user_utils import UserUtils
from ...widgets.theme_manager import ThemeManager
from .SettinsUtils.SettingsLogic import SettingsLogic
from ...constants.file_paths import QssPaths
from ...constants.module_icons import IconNames
from ...constants.button_props import ButtonVariant
from .settings_user_fetch_service import SettingsUserFetchService
from .settings_card_factory import SettingsCardFactory
from .settings_card_build_service import SettingsCardBuildService
from .cards.SettingsUserCard import UserSettingsCard
from .cards.SettingsProjectBaseLayersCard import SettingsProjectBaseLayersCard
from ...utils.url_manager import Module
from ...languages.translation_keys import TranslationKeys
from ...widgets.theme_manager import styleExtras, ThemeShadowColors
from ...utils.messagesHelper import ModernMessageDialog
from ...Logs.switch_logger import SwitchLogger
from ...Logs.python_fail_logger import PythonFailLogger
from ...ui.mixins.token_mixin import TokenMixin
from ...module_manager import ModuleManager
from .scroll_helper import SettingsScrollHelper



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
        self._project_base_layers_card = None
        self._allowed_modules = []
        self._user_fetch_thread = None
        self._user_fetch_worker = None
        self._settings_loaded_once = False
        self._pending_focus_module = None
        self.user_payload = None
        self.setup_ui()
        # Centralized theming
        self.retheme_settings()

    def _log_settings_exception(self, exc, event: str) -> None:
        PythonFailLogger.log_exception(
            exc,
            module=Module.SETTINGS.value,
            event=event,
        )

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

        self._project_base_layers_card = SettingsProjectBaseLayersCard(self.lang_manager)
        self._project_base_layers_card.pendingChanged.connect(self._update_dirty_state)
        self._project_base_layers_card.geospatialModeChanged.connect(self._on_geospatial_mode_changed)
        self._cards.append(self._project_base_layers_card)
        self.cards_layout.insertWidget(1, self._project_base_layers_card)

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

    def _generate_module_card(self, module_name: str) -> QWidget:
        return SettingsCardFactory.create_module_card(
            lang_manager=self.lang_manager,
            module_name=module_name,
            logic=self.logic,
            on_pending_changed=self._update_dirty_state,
        )

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
        if self._project_base_layers_card is not None:
            self._project_base_layers_card.on_settings_activate()
        self._refresh_user_info()

    def _refresh_user_info(self):
        if self._user_fetch_thread is not None:
            self._cancel_user_fetch_worker()

        self._user_fetch_worker, self._user_fetch_thread = SettingsUserFetchService.start_user_fetch(
            active_token=self._active_token,
            on_success=self._handle_user_worker_success,
            on_error=self._handle_user_worker_error,
            on_finished=self._clear_user_worker_refs,
        )

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

        _, can_create_property = UserUtils.has_property_rights(user_data)

        self._user_card.build_property_managment(can_create_property)
        if self._project_base_layers_card is not None:
            self._user_card.set_geospatial_mode_active(
                self._project_base_layers_card._pend_setup_mode == self._project_base_layers_card.SETUP_MODE_GEOSPATIAL
            )

        subjects = UserUtils.abilities_to_subjects(abilities)

        access_map = self.logic.get_module_access_from_abilities(subjects)

        # Ensure task-backed frontend modules always have settings cards when registered.
        forced_setting_modules = [
            Module.WORKS.value.capitalize(),
            Module.ASBUILT.value.capitalize(),
        ]
        module_manager = ModuleManager()
        for module_name in forced_setting_modules:
            if module_name.lower() in module_manager.modules:
                access_map[module_name] = True

        self._user_card.build_and_set_access_controls(access_map)

        self.update_permissions = self.logic.get_module_update_permissions(subjects)
        allowed_modules = [name for name, allowed in access_map.items() if allowed]
        self._allowed_modules = list(allowed_modules)

        self._ensure_original_settings_loaded()
        preferred_module = self.logic.get_original_preferred()
        self._user_card.set_preferred(preferred_module)

        self._ensure_module_cards(allowed_modules=allowed_modules)
        self._resolve_pending_focus()

    def request_focus_module(self, module_key: str | None) -> None:
        key = (module_key or "").strip().lower()
        if not key:
            return
        self._pending_focus_module = key
        self._resolve_pending_focus()

    def _resolve_pending_focus(self) -> None:
        target_key = (self._pending_focus_module or "").strip().lower()
        if not target_key or not self.is_token_active(None):
            return

        target_card = None
        for name, card in (self._module_cards or {}).items():
            if str(name).strip().lower() == target_key:
                target_card = card
                break

        if target_card is None:
            return

        self._pending_focus_module = None

        def _focus() -> None:
            if not self.is_token_active(None):
                return
            try:
                self.cards_container.updateGeometry()
                self.cards_container.adjustSize()
                self.scroll_area.widget().updateGeometry()
                self.scroll_area.widget().adjustSize()
            except Exception:
                pass
            SettingsScrollHelper.scroll_to_module(self, target_key)

        QTimer.singleShot(0, _focus)

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
        target = set(allowed)

        # Remove disallowed cards
        for name, card in list(self._module_cards.items()):
            if name not in target:
                SettingsCardBuildService.dispose_card(
                    card=card,
                    cards_layout=self.cards_layout,
                    on_pending_changed=self._update_dirty_state,
                    log_error=self._log_settings_exception,
                )
                del self._module_cards[name]

        SettingsCardBuildService.build_missing_cards(
            allowed_modules=allowed,
            module_cards=self._module_cards,
            cards_container=self.cards_container,
            cards_layout=self.cards_layout,
            create_card=self._generate_module_card,
            activate_card=lambda card: card.on_settings_activate(),
            profile_log=lambda event_name, extra: SwitchLogger.log(
                event_name,
                module=Module.SETTINGS.value,
                extra=extra,
            ),
            log_error=self._log_settings_exception,
        )

        # Rebuild cards list: user card first, then project card, then current module cards
        self._cards = [self._user_card]
        if self._project_base_layers_card is not None:
            self._cards.append(self._project_base_layers_card)
        self._cards.extend(self._module_cards.values())

        if self._project_base_layers_card is not None:
            self._on_geospatial_mode_changed(self._project_base_layers_card._pend_setup_mode == self._project_base_layers_card.SETUP_MODE_GEOSPATIAL)

    def _clear_user_worker_refs(self):
        self._user_fetch_thread = None
        self._user_fetch_worker = None


    def _cancel_user_fetch_worker(self, invalidate_request: bool = False):
        if invalidate_request:
            self.bump_token()
        SettingsUserFetchService.cancel_user_fetch(
            worker=self._user_fetch_worker,
            thread=self._user_fetch_thread,
            on_success=self._handle_user_worker_success,
            on_error=self._handle_user_worker_error,
            log_error=self._log_settings_exception,
        )
        self._user_fetch_worker = None
        self._user_fetch_thread = None
     
    def deactivate(self):
        self.mark_deactivated(bump_token=True)
        self._cancel_user_fetch_worker(invalidate_request=False)
        if self._project_base_layers_card is not None:
            try:
                self._project_base_layers_card.on_settings_deactivate()
            except Exception as exc:
                self._log_settings_exception(exc, "settings_project_base_layers_deactivate_failed")
        
        # Deactivate module cards to free memory
        for card in self._module_cards.values():
            try:
                card.on_settings_deactivate()
            except Exception as exc:
                self._log_settings_exception(exc, "settings_card_deactivate_failed")

    def reset(self):
        pass

    def run(self):
        pass

    def get_widget(self):
        """Return self as the widget for module system compatibility."""
        return self

    def retheme(self) -> None:
        self.retheme_settings()

    def retheme_settings(self):
        SwitchLogger.log(
            "settings_retheme_start",
            module=Module.SETTINGS.value,
            extra={
                "theme": ThemeManager.effective_theme(),
                "cards": len(self._cards or []),
            },
        )
        ThemeManager.apply_module_style(self)

        # Re-theme all existing cards through their own hooks so child controls
        # like combo boxes, checkboxes, and nested settings widgets can refresh.
        for card in self._cards:
            card_retheme = getattr(card, "retheme", None)
            if callable(card_retheme):
                card_retheme()
            else:
                ThemeManager.apply_module_style(card, [QssPaths.SETUP_CARD])
            try:
                SwitchLogger.log(
                    "settings_retheme_card",
                    module=Module.SETTINGS.value,
                    extra={
                        "card": type(card).__name__,
                        "tone": str(card.property("cardTone") or ""),
                        "stylesheet_len": len(card.styleSheet() or ""),
                    },
                )
            except Exception:
                continue
        if self._footer_frame is not None:
            ThemeManager.apply_module_style(self._footer_frame, [QssPaths.SETUP_CARD])
        SwitchLogger.log(
            "settings_retheme_done",
            module=Module.SETTINGS.value,
            extra={"theme": ThemeManager.effective_theme()},
        )


    # --- Handling unsaved changes ---
    def apply_pending_changes(self):
        if self._project_base_layers_card is not None:
            self._project_base_layers_card.apply()
        for card in self._module_cards.values():
            card.apply()
        self.logic.apply_pending_changes()

        # Recompute dirty state using both logic + cards
        self._set_dirty(self.has_unsaved_changes())

    def revert_pending_changes(self):
        self.logic.revert_pending_changes()
        self._user_card.revert(self.logic.get_original_preferred())
        if self._project_base_layers_card is not None:
            self._project_base_layers_card.revert()
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

    def _on_geospatial_mode_changed(self, active: bool) -> None:
        if self._user_card is not None:
            self._user_card.set_geospatial_mode_active(bool(active))
        for card in self._module_cards.values():
            set_mode = getattr(card, "set_geospatial_mode_active", None)
            if callable(set_mode):
                set_mode(bool(active))

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
        if self._project_base_layers_card is not None and self._project_base_layers_card.has_pending_changes():
            return True
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
                parent=parent,
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


   
