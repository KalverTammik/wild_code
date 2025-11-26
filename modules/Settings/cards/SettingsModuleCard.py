from PyQt5.QtWidgets import QVBoxLayout, QLabel, QFrame, QHBoxLayout, QGroupBox
from PyQt5.QtCore import pyqtSignal, Qt
from .SettingsBaseCard import SettingsBaseCard
from ....widgets.LayerDropdownWidget import LayerDropdown
from ....widgets.StatusFilterWidget import StatusFilterWidget
from ....widgets.TypeFilterWidget import TypeFilterWidget
from ....widgets.TagsFilterWidget import TagsFilterWidget
from ....constants.module_icons import ModuleIconPaths
from ....utils.url_manager import Module
from ....widgets.theme_manager import styleExtras, ThemeShadowColors
from ....constants.settings_keys import SettingsService
from ....utils.MapTools.MapHelpers import MapHelpers


class SettingsModuleCard(SettingsBaseCard):
    pendingChanged = pyqtSignal(bool)

    def __init__(
        self,
        lang_manager,
        module_name: str,
        translated_name: str,
        supports_types: bool = False,
        supports_statuses: bool = False,
        supports_tags: bool = False,
        logic=None,
    ):
        # Ikon pealkirjale
        icon_path = ModuleIconPaths.get_module_icon(module_name)
        super().__init__(lang_manager, translated_name, icon_path)

        # Kasuta kanonilist võtmekuju (lowercase) KÕIKJAL
        self.module_key = (module_name).lower().strip()  # võtmekuju (nt "property")
        self.supports_archive = self.module_key == Module.PROPERTY.value

        self.supports_types = supports_types
        self.supports_statuses = supports_statuses
        self.supports_tags = supports_tags
        self.logic = logic
        self._settings = SettingsService()
        self._snapshot = None


        # Layer pickers
        self._layer_selector = None
        self._archive_picker = None

        # Originaal vs pending
        self._orig_element_name = ""
        self._orig_archive_name = ""
        self._pend_element_name = ""
        self._pend_archive_name = ""
        self._orig_status_preferences = set()
        self._pend_status_preferences = set()
        self._orig_type_preferences = set()
        self._pend_type_preferences = set()
        self._orig_tag_preferences = set()
        self._pend_tag_preferences = set()

        # Filtrite viidad
        self._status_filter_widget: StatusFilterWidget | None = None
        self._type_filter_widget: TypeFilterWidget | None = None
        self._tags_filter_widget: TagsFilterWidget | None = None

        self._build_ui()

    # --- UI ---
    def _build_ui(self):
        cw = self.content_widget()
        cl = QVBoxLayout(cw)
        cl.setContentsMargins(1, 1, 1, 1)
        cl.setSpacing(6)

        # Layers container
        layers_container = QFrame(cw)
        layers_container.setObjectName("LayersContainer")
        layers_layout = QHBoxLayout(layers_container)
        layers_layout.setContentsMargins(0, 0, 0, 0)
        layers_layout.setSpacing(8)

        # Main layer group
        primary_layer_group = QGroupBox(self.lang_manager.translate("Modules main layer"), layers_container)
        primary_layer_group.setObjectName("MainLayerGroup")
        main_layout = QHBoxLayout(primary_layer_group)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(6)

        # Container for layer selector with chip shadow
        layer_selector_container = QFrame(primary_layer_group)
        layer_selector_container.setObjectName("LayerSelectorContainer")
        layer_selector_layout = QVBoxLayout(layer_selector_container)
        layer_selector_layout.setContentsMargins(4, 2, 4, 2)
        layer_selector_layout.setSpacing(0)

        # Apply chip shadow to the container
        try:
            styleExtras.apply_chip_shadow(
                layer_selector_container,
                blur_radius=5,
                x_offset=1,
                y_offset=1,
                color=ThemeShadowColors.ACCENT,
                alpha_level='medium'
            )
        except Exception:
            pass

        self._layer_selector = LayerDropdown(layer_selector_container, placeholder=self.lang_manager.translate("Select layer"))
        self._layer_selector.layerIdChanged.connect(self._on_element_selected)
        self._layer_selector.retheme()
        layer_selector_layout.addWidget(self._layer_selector)

        main_layout.addWidget(layer_selector_container, 2)

        primary_layer_explanation = QLabel(
            "See on teie mooduli põhikiht. Valige kiht, mis sisaldab peamisi andmeid, millega soovite töötada. "
            "See säte määrab, millist kihti kasutatakse alusena kõigi mooduli toimingute jaoks.",
            primary_layer_group
        )
        primary_layer_explanation.setObjectName("GroupExplanation")
        primary_layer_explanation.setWordWrap(True)
        primary_layer_explanation.setStyleSheet("color: #888; font-size: 11px; padding: 4px 0px;")
        primary_layer_explanation.setMinimumWidth(200)
        main_layout.addWidget(primary_layer_explanation, 1)
        layers_layout.addWidget(primary_layer_group)

        if self.supports_archive:
            archived_layers_section = QGroupBox(self.lang_manager.translate("Archive layer"), layers_container)
            archived_layers_section.setObjectName("ArchiveLayerGroup")
            archived_layer_layout = QHBoxLayout(archived_layers_section)
            archived_layer_layout.setContentsMargins(4, 4, 4, 4)
            archived_layer_layout.setSpacing(6)

            archive_picker_container = QFrame(archived_layers_section)
            archive_picker_container.setObjectName("ArchivePickerContainer")
            archive_picker_layout = QVBoxLayout(archive_picker_container)
            archive_picker_layout.setContentsMargins(2, 2, 2, 2)
            archive_picker_layout.setSpacing(0)

            try:
                styleExtras.apply_chip_shadow(
                    archive_picker_container,
                    blur_radius=5,
                    x_offset=1,
                    y_offset=1,
                    color=ThemeShadowColors.ACCENT,
                    alpha_level='medium'
                )
            except Exception:
                pass

            self._archive_picker = LayerDropdown(archive_picker_container, placeholder=self.lang_manager.translate("Select layer"))
            self._archive_picker.layerIdChanged.connect(self._on_archive_selected)
            self._archive_picker.retheme()
            archive_picker_layout.addWidget(self._archive_picker)

            archived_layer_layout.addWidget(archive_picker_container, 2)

            archive_layer_explanation = QLabel(
                "See valikuline arhiivikiht salvestab ajaloolisi või varukoopia andmeid. "
                "Kasutage seda, kui vajate muudatuste või andmete ajalooliste versioonide eraldi kirjet.",
                archived_layers_section
            )
            archive_layer_explanation.setObjectName("GroupExplanation")
            archive_layer_explanation.setWordWrap(True)
            archive_layer_explanation.setStyleSheet("color: #888; font-size: 11px; padding: 4px 0px;")
            archive_layer_explanation.setMinimumWidth(200)
            archived_layer_layout.addWidget(archive_layer_explanation, 1)
            layers_layout.addWidget(archived_layers_section)

        cl.addWidget(layers_container)

        # Options container
        options_container = QFrame(cw)
        options_container.setObjectName("OptionsContainer")
        options_layout = QVBoxLayout(options_container)
        options_layout.setContentsMargins(0, 0, 0, 0)
        options_layout.setSpacing(8)

        # 1. rida – Status preferences
        first_row_container = QFrame(options_container)
        first_row_container.setObjectName("FirstRowContainer")
        first_row_layout = QHBoxLayout(first_row_container)
        first_row_layout.setContentsMargins(0, 0, 0, 0)
        first_row_layout.setSpacing(8)
        options_layout.addWidget(first_row_container)

        if self.supports_statuses:
            status_group = QGroupBox(self.lang_manager.translate("Status Preferences"), first_row_container)
            status_group.setObjectName("StatusPreferencesGroup")
            status_layout = QHBoxLayout(status_group)
            status_layout.setContentsMargins(4, 4, 4, 4)
            status_layout.setSpacing(6)

            status_container = QFrame(status_group)
            status_container.setObjectName("StatusContainer")
            status_inner_layout = QVBoxLayout(status_container)
            status_inner_layout.setContentsMargins(0, 0, 0, 0)
            status_inner_layout.setSpacing(4)

            # Avalik API: ensure_loaded(); ära kutsu _populate() ega näpi .combo
            self._status_filter_widget = StatusFilterWidget(
                self.module_key,
                status_container,
            )
            self._status_filter_widget.ensure_loaded()
            self._status_filter_widget.selectionChanged.connect(self._on_status_selection_changed)
            status_inner_layout.addWidget(self._status_filter_widget)

            status_layout.addWidget(status_container, 2)

            status_explanation = QLabel(
                self.lang_manager.translate("Select statuses you want to prioritize for this module. These will be highlighted in the interface."),
                status_group
            )
            status_explanation.setObjectName("GroupExplanation")
            status_explanation.setWordWrap(True)
            status_explanation.setStyleSheet("color: #888; font-size: 11px; padding: 4px 0px;")
            status_explanation.setMinimumWidth(200)
            status_layout.addWidget(status_explanation, 1)

            first_row_layout.addWidget(status_group)

        if self.supports_tags:
            tags_group = QGroupBox(self.lang_manager.translate("Tag Preferences"), first_row_container)
            tags_group.setObjectName("TagPreferencesGroup")
            tags_layout = QHBoxLayout(tags_group)
            tags_layout.setContentsMargins(4, 4, 4, 4)
            tags_layout.setSpacing(6)

            tags_container = QFrame(tags_group)
            tags_container.setObjectName("TagsContainer")
            tags_inner_layout = QVBoxLayout(tags_container)
            tags_inner_layout.setContentsMargins(0, 0, 0, 0)
            tags_inner_layout.setSpacing(4)

            self._tags_filter_widget = TagsFilterWidget(
                self.module_key,
                self.lang_manager,
                tags_container,
            )
            self._tags_filter_widget.selectionChanged.connect(self._on_tags_selection_changed)
            tags_inner_layout.addWidget(self._tags_filter_widget)

            tags_layout.addWidget(tags_container, 2)

            tags_explanation = QLabel(
                self.lang_manager.translate("Select tags you want to focus on for this module."),
                tags_group,
            )
            tags_explanation.setObjectName("GroupExplanation")
            tags_explanation.setWordWrap(True)
            tags_explanation.setStyleSheet("color: #888; font-size: 11px; padding: 4px 0px;")
            tags_explanation.setMinimumWidth(200)
            tags_layout.addWidget(tags_explanation, 1)

            first_row_layout.addWidget(tags_group)

        # 2. rida – Type preferences (kui toetatud)
        if self.supports_types:
            type_group = QGroupBox(self.lang_manager.translate("Type Preferences"), options_container)
            type_group.setObjectName("TypePreferencesGroup")
            type_layout = QHBoxLayout(type_group)
            type_layout.setContentsMargins(4, 4, 4, 4)
            type_layout.setSpacing(6)

            type_container = QFrame(type_group)
            type_container.setObjectName("TypeContainer")
            type_inner_layout = QVBoxLayout(type_container)
            type_inner_layout.setContentsMargins(0, 0, 0, 0)
            type_inner_layout.setSpacing(4)

            self._type_filter_widget = TypeFilterWidget(
                self.module_key,
                type_container,
            )
            self._type_filter_widget.ensure_loaded()
            self._type_filter_widget.selectionChanged.connect(self._on_type_selection_changed)
            type_inner_layout.addWidget(self._type_filter_widget)

            type_layout.addWidget(type_container, 2)

            type_explanation = QLabel(
                self.lang_manager.translate("Select types you want to prioritize for this module. These will be highlighted in the interface."),
                type_group
            )
            type_explanation.setObjectName("GroupExplanation")
            type_explanation.setWordWrap(True)
            type_explanation.setStyleSheet("color: #888; font-size: 11px; padding: 4px 0px;")
            type_explanation.setMinimumWidth(200)
            type_layout.addWidget(type_explanation, 1)

            options_layout.addWidget(type_group)

        cl.addWidget(options_container)
        cl.addStretch(1)

        # Reset nupp jaluses
        reset_btn = self.reset_button()
        reset_btn.setToolTip(self.lang_manager.translate("Reset all settings for this module to default values"))
        reset_btn.setVisible(True)
        reset_btn.clicked.connect(self._on_reset_settings)


    # --- Lifecycle hooks (SettingsUI) ---
    def on_settings_activate(self, snapshot=None):
        if snapshot is not None:
            self._snapshot = snapshot
            self._layer_selector.setSnapshot(snapshot)
            if self.supports_archive and self._archive_picker:
                self._archive_picker.setSnapshot(snapshot)
        self._layer_selector.on_settings_activate(snapshot=self._snapshot)
        if self.supports_archive and self._archive_picker:
            self._archive_picker.on_settings_activate(snapshot=self._snapshot)
        self._layer_selector.retheme()
        if self.supports_archive and self._archive_picker:
            self._archive_picker.retheme()

        # Lae algsed layer-nimed
        self._orig_element_name = self._read_saved_layer_value(kind="element")
        self._orig_archive_name = self._read_saved_layer_value(kind="archive")
        self._pend_element_name = self._orig_element_name
        self._pend_archive_name = self._orig_archive_name

        # Lae status/type eelistused
        self._orig_status_preferences = self._load_status_preferences_from_settings()
        self._pend_status_preferences = set(self._orig_status_preferences)

        if self.supports_types:
            self._orig_type_preferences = self._load_type_preferences_from_settings()
            self._pend_type_preferences = set(self._orig_type_preferences)
        else:
            self._orig_type_preferences = set()
            self._pend_type_preferences = set()

        if self.supports_tags:
            self._orig_tag_preferences = self._load_tag_preferences_from_settings()
            self._pend_tag_preferences = set(self._orig_tag_preferences)
        else:
            self._orig_tag_preferences = set()
            self._pend_tag_preferences = set()

        # Rakenda eelistused filtritesse
        if self.supports_statuses and self._status_filter_widget:
            try:
                self._status_filter_widget.ensure_loaded()
                self._set_filter_ids(self._status_filter_widget, list(self._orig_status_preferences))
            except Exception as e:
                print(f"Failed to load status filter widget: {e}")
                self._status_filter_widget.setEnabled(False)

        if self.supports_types and self._type_filter_widget:
            try:
                self._type_filter_widget.ensure_loaded()
                self._set_filter_ids(self._type_filter_widget, list(self._orig_type_preferences))
            except Exception as e:
                print(f"Failed to load type filter widget: {e}")
                self._type_filter_widget.setEnabled(False)

        if self.supports_tags and self._tags_filter_widget:
            try:
                self._tags_filter_widget.ensure_loaded()
                self._set_filter_ids(self._tags_filter_widget, list(self._orig_tag_preferences))
            except Exception as e:
                print(f"Failed to load tags filter widget: {e}")
                self._tags_filter_widget.setEnabled(False)

        # Taasta layeri valikud (vaid kui kiht on olemas)
        self._restore_layer_selection(self._layer_selector, self._orig_element_name)
        if self.supports_archive and self._archive_picker:
            self._restore_layer_selection(self._archive_picker, self._orig_archive_name)

        self._update_stored_values_display()

    def on_settings_deactivate(self):
        if self._layer_selector:
            self._layer_selector.on_settings_deactivate()
        if self.supports_archive and self._archive_picker:
            self._archive_picker.on_settings_deactivate()

    # --- Persistence helpers -------------------------------------------------
    def _read_saved_layer_value(self, kind: str) -> str:
        try:
            if kind == "element":
                return self._settings.module_main_layer_id(self.module_key) or ""
            if kind == "archive":
                if not self.supports_archive:
                    return ""
                return self._settings.module_archive_layer_id(self.module_key) or ""
        except Exception:
            pass
        return ""

    def _write_saved_layer_value(self, kind: str, layer_name: str):
        try:
            if kind == "element":
                if layer_name:
                    self._settings.module_main_layer_id(self.module_key, value=layer_name)
                else:
                    self._settings.module_main_layer_id(self.module_key, clear=True)
            else:
                if not self.supports_archive:
                    return
                if layer_name:
                    self._settings.module_archive_layer_id(self.module_key, value=layer_name)
                else:
                    self._settings.module_archive_layer_id(self.module_key, clear=True)
        except Exception:
            pass

    # --- Apply/Revert/State ---
    def has_pending_changes(self) -> bool:
        el_dirty = self._pend_element_name != self._orig_element_name
        ar_dirty = self._pend_archive_name != self._orig_archive_name
        status_dirty = self._pend_status_preferences != self._orig_status_preferences
        type_dirty = bool(self.supports_types) and self._pend_type_preferences != self._orig_type_preferences
        tag_dirty = bool(self.supports_tags) and self._pend_tag_preferences != self._orig_tag_preferences
        return el_dirty or ar_dirty or status_dirty or type_dirty or tag_dirty

    def apply(self):
        changed = False

        if self._pend_element_name != self._orig_element_name:
            self._write_saved_layer_value("element", self._pend_element_name)
            self._orig_element_name = self._pend_element_name
            self._restore_layer_selection(self._layer_selector, self._orig_element_name)
            changed = True

        if self.supports_archive and (self._pend_archive_name != self._orig_archive_name):
            self._write_saved_layer_value("archive", self._pend_archive_name)
            self._orig_archive_name = self._pend_archive_name
            if self._archive_picker:
                self._restore_layer_selection(self._archive_picker, self._orig_archive_name)
            changed = True

        # Save status prefs
        if self._pend_status_preferences != self._orig_status_preferences:
            self._save_status_preferences()
            self._orig_status_preferences = set(self._pend_status_preferences)
            changed = True

        # Save tag prefs
        if self.supports_tags and (self._pend_tag_preferences != self._orig_tag_preferences):
            self._save_tag_preferences()
            self._orig_tag_preferences = set(self._pend_tag_preferences)
            changed = True

        # Save type prefs
        if self.supports_types and (self._pend_type_preferences != self._orig_type_preferences):
            self._save_type_preferences()
            self._orig_type_preferences = set(self._pend_type_preferences)
            changed = True

        # Reset pending layer ids
        self._pend_element_name = self._orig_element_name
        self._pend_archive_name = self._orig_archive_name

        self._sync_selected_names()
        self.pendingChanged.emit(False if changed else self.has_pending_changes())

    def revert(self):
        # Layers
        self._restore_layer_selection(self._layer_selector, self._orig_element_name)
        if self.supports_archive and self._archive_picker:
            self._restore_layer_selection(self._archive_picker, self._orig_archive_name)
        self._pend_element_name = self._orig_element_name
        self._pend_archive_name = self._orig_archive_name

        # Status prefs
        self._pend_status_preferences = set(self._orig_status_preferences)
        self._restore_status_preferences_ui()

        # Tag prefs
        if self.supports_tags:
            self._pend_tag_preferences = set(self._orig_tag_preferences)
            self._restore_tag_preferences_ui()

        # Type prefs
        if self.supports_types:
            self._pend_type_preferences = set(self._orig_type_preferences)
            self._restore_type_preferences_ui()

        self._sync_selected_names()
        self.pendingChanged.emit(False)

    def _sync_selected_names(self):
        self._update_stored_values_display()

    def _update_stored_values_display(self):
        """Footeris voolav kokkuvõte salvestatud väärtustest."""
        try:
            def display_for(picker, fallback_name: str) -> str:
                try:
                    if picker:
                        lyr = picker.selectedLayer()
                        if lyr:
                            return lyr.name()
                except Exception:
                    pass
                return fallback_name or ""

            element_name = display_for(self._layer_selector, self._pend_element_name or self._orig_element_name)
            archive_name = ""
            if self.supports_archive:
                archive_name = display_for(self._archive_picker, self._pend_archive_name or self._orig_archive_name)

            parts = []
            if element_name:
                parts.append(f"📄 Main: {element_name}")
            if archive_name:
                parts.append(f"📁 Archive: {archive_name}")

            if parts:
                values_text = " | ".join(parts)
                self.set_status_text(f"Active layers: {values_text}")
            else:
                self.set_status_text("No layers configured")
        except Exception:
            self.set_status_text("Settings loaded")

    # --- Show Numbers Setting (kasuta module_key) ---
    def _read_show_numbers_setting(self) -> bool:
        try:
            value = self._settings.module_show_numbers(self.module_key)
            if value is None:
                return True
            return bool(value)
        except Exception:
            return True

    def _write_show_numbers_setting(self, show_numbers: bool):
        try:
            self._settings.module_show_numbers(self.module_key, value=show_numbers)
        except Exception:
            pass

    # --- Filtri handlerid ---
    def _on_type_selection_changed(self, texts=None, ids=None):
        """TypeFilterWidget forwarder -> uuenda pendingut."""
        if not self.supports_types or not self._type_filter_widget or not self._type_filter_widget.isEnabled():
            return
        try:
            selected_ids = ids
            ids = selected_ids if selected_ids is not None else self._type_filter_widget.selected_ids()
            self._pend_type_preferences = set(ids) if ids else set()
            self.pendingChanged.emit(self.has_pending_changes())
        except Exception as e:
            print(f"Error handling type selection change: {e}")

    def _on_status_selection_changed(self, texts=None, ids=None):
        """StatusFilterWidget forwarder -> uuenda pendingut + anna logic'ule teada."""
        if not self._status_filter_widget or not self._status_filter_widget.isEnabled():
            return
        try:
            selected_ids = ids
            ids = selected_ids if selected_ids is not None else self._status_filter_widget.selected_ids()
            self._pend_status_preferences = {str(v) for v in ids} if ids else set()
            self.pendingChanged.emit(self.has_pending_changes())
        except Exception as e:
            print(f"Error handling status selection change: {e}")

    def _on_tags_selection_changed(self, texts=None, ids=None):
        if not self.supports_tags or not self._tags_filter_widget or not self._tags_filter_widget.isEnabled():
            return
        try:
            selected_ids = ids
            ids = selected_ids if selected_ids is not None else self._tags_filter_widget.selected_ids()
            self._pend_tag_preferences = {str(v) for v in ids} if ids else set()
            self.pendingChanged.emit(self.has_pending_changes())
        except Exception as e:
            print(f"Error handling tag selection change: {e}")

    def _on_reset_settings(self):
        """Reset all settings for this module to defaults."""
        try:
            # Layers
            self._layer_selector.clearSelection()
            if self.supports_archive and self._archive_picker:
                self._archive_picker.clearSelection()
            self._pend_element_name = ""
            self._pend_archive_name = ""

            # Status
            if self._status_filter_widget and self._status_filter_widget.isEnabled():
                self._set_filter_ids(self._status_filter_widget, [])
            self._orig_status_preferences = set()
            self._pend_status_preferences = set()

            # Tags
            if self.supports_tags and self._tags_filter_widget and self._tags_filter_widget.isEnabled():
                self._set_filter_ids(self._tags_filter_widget, [])
            self._orig_tag_preferences = set()
            self._pend_tag_preferences = set()

            # Types
            if self.supports_types and self._type_filter_widget and self._type_filter_widget.isEnabled():
                self._set_filter_ids(self._type_filter_widget, [])
            self._orig_type_preferences = set()
            self._pend_type_preferences = set()

            # Clear stored settings
            self._write_saved_layer_value("element", "")
            self._write_saved_layer_value("archive", "")

            # Clear prefs in settings
            try:
                self._settings.module_preferred_statuses(self.module_key, clear=True)
                if self.supports_tags:
                    self._settings.module_preferred_tags(self.module_key, clear=True)
                if self.supports_types:
                    self._settings.module_preferred_types(self.module_key, clear=True)
            except Exception:
                pass

            self._sync_selected_names()
            self._validate_layer_selections()
            self.set_status_text(f"✅ {self.lang_manager.translate('Settings reset to defaults')}", True)
            self.pendingChanged.emit(self.has_pending_changes())
        except Exception as e:
            self.set_status_text(f"❌ {self.lang_manager.translate('Reset failed')}: {str(e)}", True)

    # --- Eelistused (settings) ---
    def _load_status_preferences_from_settings(self) -> set:
        try:
            preferred_statuses = self._settings.module_preferred_statuses(self.module_key) or ""
            return set(p.strip() for p in str(preferred_statuses).split(",") if p.strip())
        except Exception:
            return set()

    def _save_status_preferences(self):
        try:
            if self._pend_status_preferences:
                value = ",".join(sorted(str(v) for v in self._pend_status_preferences))
                self._settings.module_preferred_statuses(self.module_key, value=value)
            else:
                self._settings.module_preferred_statuses(self.module_key, clear=True)
        except Exception:
            pass

    def _restore_status_preferences_ui(self):
        if self._status_filter_widget and self._status_filter_widget.isEnabled():
            try:
                self._set_filter_ids(self._status_filter_widget, list(self._orig_status_preferences))
            except Exception as e:
                print(f"Error restoring status preferences UI: {e}")

    def _load_tag_preferences_from_settings(self) -> set:
        if not self.supports_tags:
            return set()
        try:
            preferred_tags = self._settings.module_preferred_tags(self.module_key) or ""
            return set(p.strip() for p in str(preferred_tags).split(",") if p.strip())
        except Exception:
            return set()

    def _save_tag_preferences(self):
        if not self.supports_tags:
            return
        try:
            if self._pend_tag_preferences:
                value = ",".join(sorted(str(v) for v in self._pend_tag_preferences))
                self._settings.module_preferred_tags(self.module_key, value=value)
            else:
                self._settings.module_preferred_tags(self.module_key, clear=True)
        except Exception:
            pass

    def _restore_tag_preferences_ui(self):
        if not self.supports_tags:
            return
        if self._tags_filter_widget and self._tags_filter_widget.isEnabled():
            try:
                self._set_filter_ids(self._tags_filter_widget, list(self._orig_tag_preferences))
            except Exception as e:
                print(f"Error restoring tag preferences UI: {e}")

    def _load_type_preferences_from_settings(self) -> set:
        try:
            preferred_types = self._settings.module_preferred_types(self.module_key) or ""
            return set(p.strip() for p in str(preferred_types).split(",") if p.strip())
        except Exception:
            return set()

    def _save_type_preferences(self):
        try:
            if self._pend_type_preferences:
                value = ",".join(sorted(self._pend_type_preferences))
                self._settings.module_preferred_types(self.module_key, value=value)
            else:
                self._settings.module_preferred_types(self.module_key, clear=True)
        except Exception:
            pass

    def _restore_type_preferences_ui(self):
        if self._type_filter_widget and self._type_filter_widget.isEnabled():
            try:
                self._set_filter_ids(self._type_filter_widget, list(self._orig_type_preferences))
            except Exception as e:
                print(f"Error restoring type preferences UI: {e}")

    def _restore_layer_selection(self, picker, stored_name: str):
        """Resolve a stored layer name and update the picker selection."""
        if not picker:
            return
        resolved_id = MapHelpers.resolve_layer_id(stored_name)
        if not resolved_id:
            picker.clearSelection()
            return
        try:
            picker.setSelectedLayerId(resolved_id)
            picker.refresh()
            if not picker.selectedLayer():
                picker.clearSelection()
        except Exception:
            picker.clearSelection()

    # --- Layer valiku handlerid ---
    def _on_element_selected(self, layer_id: str):
        self._pend_element_name = MapHelpers.layer_name_from_id(layer_id) if layer_id else ""
        self._sync_selected_names()
        self.pendingChanged.emit(self.has_pending_changes())

    def _on_archive_selected(self, layer_id: str):
        if not self.supports_archive:
            return
        self._pend_archive_name = MapHelpers.layer_name_from_id(layer_id) if layer_id else ""
        self._sync_selected_names()
        self.pendingChanged.emit(self.has_pending_changes())

    # --- Abid ---
    def _set_filter_ids(self, widget, ids: list[str]):
        """Apply stored IDs to a filter widget without triggering runtime emissions."""
        widget.set_selected_ids(ids, emit=False)
