from collections import deque
from typing import Any, Callable, Deque, Optional, Tuple

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QFrame, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import pyqtSignal, QTimer
from qgis.core import QgsProject, QgsLayerTreeGroup, QgsLayerTreeLayer

from .SettinsUtils.userUtils import userUtils

from ...widgets.theme_manager import ThemeManager
from .SettinsUtils.SettingsLogic import SettingsLogic
from ...constants.file_paths import QssPaths
from .cards.SettingsUserCard import UserSettingsCard
from .cards.SettingsModuleCard import SettingsModuleCard
from ...utils.url_manager import Module
from ...module_manager import ModuleManager, MODULES_LIST_BY_NAME
from ...languages.translation_keys import TranslationKeys
from ...widgets.theme_manager import styleExtras, ThemeShadowColors
from ...python.workers import FunctionWorker, start_worker


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
            lang_manager=None,
            qss_files=None
        ):
        super().__init__()

        self.name = Module.SETTINGS.name        # Ensure we always use LanguageManager
        
        self.lang_manager = lang_manager
        # Logic layer
        self.logic = SettingsLogic()
        self._cards = []
        self._initialized = False
        self._pending_changes = False
        self._pending_settings = {}
        self._original_settings = {}
        # Global footer controls
        self._footer_frame = None
        self._footer_status = None
        self._footer_confirm = None
        # Modules available for module-specific cards
        self._module_cards = {}
        self._module_metadata = {}  # Store module metadata including supports_types
        self._user_fetch_thread = None
        self._user_fetch_worker = None
        self._user_fetch_request_id = 0
        self._filter_load_queue: Deque[Tuple[str, str, Any]] = deque()
        self._active_filter_entry: Optional[Tuple[str, str, Any, Optional[Callable[[bool], None]]]] = None
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
        user_card = self._build_user_setup_card()
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
        ThemeManager.apply_module_style(self, [QssPaths.SETUP_CARD])


        self._footer_status = QLabel("", self._footer_frame)
        self._footer_status.setObjectName("SettingsFooterStatus")
        self._footer_status.setWordWrap(True)
        self._footer_status.setVisible(False)
        footer_layout.addWidget(self._footer_status, 1)

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

    def _build_user_setup_card(self) -> QWidget:
        card = UserSettingsCard(self.lang_manager)
        card.preferredModuleChanged.connect(self._user_preferred_module_changed)
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
        insert_index = 1
        for module_name in MODULES_LIST_BY_NAME:
            if module_name == Module.HOME.name.capitalize():
                continue
            card = self._generate_module_card(module_name)
            self._module_cards[module_name] = card
            self.cards_layout.insertWidget(insert_index, card)
            self._cards.append(card)
            insert_index += 1

    def _generate_module_card(self, module_name: str) -> QWidget:
 
        translated = self.lang_manager.translate(module_name.capitalize())

        supports = ModuleManager().getModuleSupports(module_name) or {}
        card = SettingsModuleCard(
            self.lang_manager,
            module_name,
            translated,
            supports_types=supports.get("types", False),
            supports_statuses=supports.get("statuses", False),
            supports_tags=supports.get("tags", False),
            logic=self.logic,
            filter_loader=self._request_filter_load,
            filter_cancel=self._cancel_scheduled_filter_loads,
        )
 
        card.pendingChanged.connect(self._update_dirty_state)
 
        return card

    def _activate_module_cards(self):
        snapshot = self._build_layer_snapshot()
        for card in self._module_cards.values():
            try:
                card.on_settings_activate(snapshot=snapshot)
            except Exception as exc:
                print(f"Failed to activate settings card for {getattr(card, 'module_key', 'unknown')}: {exc}")

    # ------------------------------------------------------------------
    # Filter load orchestration (limits concurrent network workers)
    # ------------------------------------------------------------------
    def _request_filter_load(self, module_key: str, kind: str, widget: Any) -> None:
        if widget is None:
            return
        self._filter_load_queue.append((module_key, kind, widget))
        if not self._active_filter_entry:
            self._start_next_filter_load()

    def _start_next_filter_load(self) -> None:
        if self._active_filter_entry:
            return
        while self._filter_load_queue:
            module_key, kind, widget = self._filter_load_queue.popleft()
            if widget is None:
                continue
            if hasattr(widget, "is_loaded") and widget.is_loaded():
                continue
            handler = self._make_filter_load_handler(widget)
            try:
                widget.loadFinished.connect(handler)
            except Exception:
                handler = None
            self._active_filter_entry = (module_key, kind, widget, handler)  # type: ignore[arg-type]
            try:
                widget.reload()
            except Exception:
                self._handle_filter_load_complete(widget)
            return
        self._active_filter_entry = None

    def _make_filter_load_handler(self, widget: Any) -> Callable[[bool], None]:
        def _handler(_success: bool) -> None:
            self._handle_filter_load_complete(widget)

        return _handler

    def _handle_filter_load_complete(self, widget: Any) -> None:
        entry = self._active_filter_entry
        if not entry or entry[2] is not widget:
            return
        handler = entry[3]
        if handler:
            try:
                widget.loadFinished.disconnect(handler)
            except Exception:
                pass
        self._active_filter_entry = None
        QTimer.singleShot(15, self._start_next_filter_load)

    def _cancel_scheduled_filter_loads(self, widget: Any) -> None:
        if widget is None:
            return
        remaining = [entry for entry in self._filter_load_queue if entry[2] is not widget]
        self._filter_load_queue = deque(remaining)
        entry = self._active_filter_entry
        if entry and entry[2] is widget:
            self._handle_filter_load_complete(widget)

    def _clear_filter_load_queue(self) -> None:
        self._filter_load_queue = deque()
        entry = self._active_filter_entry
        if entry:
            widget = entry[2]
            handler = entry[3]
            if handler:
                try:
                    widget.loadFinished.disconnect(handler)
                except Exception:
                    pass
        self._active_filter_entry = None

    def _build_layer_snapshot(self):
        try:
            project = QgsProject.instance() if QgsProject else None
            root = project.layerTreeRoot() if project else None
            if not root:
                return []
            return self._snapshot_from_group(root)
        except Exception:
            return []

    def _snapshot_from_group(self, group_node):
        snapshot = []
        try:
            children = group_node.children()
        except Exception:
            children = []
        for child in children:
            if QgsLayerTreeGroup and isinstance(child, QgsLayerTreeGroup):
                snapshot.append({
                    "type": "group",
                    "name": child.name(),
                    "children": self._snapshot_from_group(child)
                })
            elif QgsLayerTreeLayer and isinstance(child, QgsLayerTreeLayer):
                try:
                    layer = child.layer()
                except Exception:
                    layer = None
                if layer:
                    snapshot.append({
                        "type": "layer",
                        "id": layer.id(),
                        "name": layer.name()
                    })
        return snapshot

    def activate(self):
        """Activates the Settings UI with fresh user data."""
        self._refresh_user_info()

    def _refresh_user_info(self):
        if self._user_fetch_thread is not None:
            self._cancel_user_fetch_worker()

        self._user_fetch_request_id += 1
        self._set_user_labels_loading()

        worker = FunctionWorker(userUtils.fetch_user_payload, self.lang_manager)
        worker.request_id = self._user_fetch_request_id
        worker.finished.connect(self._handle_user_worker_success)
        worker.error.connect(self._handle_user_worker_error)
        self._user_fetch_worker = worker
        self._user_fetch_thread = start_worker(worker, on_thread_finished=self._clear_user_worker_refs)

    def _handle_user_worker_success(self, payload):
        if not self._is_active_user_worker():
            return
        self._apply_user_payload(payload)

    def _handle_user_worker_error(self, message):
        if not self._is_active_user_worker():
            return
        print(f"[SettingsUI] Failed to load user info: {message}")
        self._apply_user_payload({})

    def _is_active_user_worker(self) -> bool:
        worker = self._user_fetch_worker
        if worker is None:
            return False
        request_id = getattr(worker, "request_id", None)
        return request_id == self._user_fetch_request_id

    def _apply_user_payload(self, payload):
        user_data = payload or {}

        userUtils.extract_and_set_user_labels(
            self._user_card.lbl_name,
            self._user_card.lbl_email,
            user_data,
        )
        roles = userUtils.get_roles_list(user_data.get("roles"))
        userUtils.set_roles(self._user_card.lbl_roles, roles)

        abilities = user_data.get("abilities", [])
        subjects = userUtils.abilities_to_subjects(abilities)
        if Module.PROPERTY.value.capitalize() in subjects:
            print("✅ User has Property access!")
            self._has_property_rights = True
        else:
            print("❌ User does NOT have Property access")
            self._has_property_rights = False

        access_map = self.logic.get_module_access_from_abilities(subjects)
        update_permissions = self.logic.get_module_update_permissions(subjects)
        self._user_card.set_access_map(access_map)
        self._user_card.set_update_permissions(update_permissions)

        self.logic.load_original_settings()
        self._user_card.set_preferred(self.logic.get_original_preferred())
        self._set_dirty(False)

        if not self._initialized:
            self._initialized = True
            self._build_module_cards()
        self._activate_module_cards()

    def _set_user_labels_loading(self):
        if not hasattr(self, "_user_card"):
            return
        loading_text = self.lang_manager.translate(TranslationKeys.LOADING) if self.lang_manager else "Loading"
        placeholder = f"{loading_text}…"
        self._user_card.lbl_name.setText(placeholder)
        self._user_card.lbl_email.setText("—")
        self._user_card.lbl_roles.setText("—")

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
        self._clear_filter_load_queue()
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
            try:
                card.apply()
            except Exception as exc:
                print(f"Failed to apply module card settings: {exc}")
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
            mbox.setIcon(QMessageBox.Warning)
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

    # --- Helpers ---
