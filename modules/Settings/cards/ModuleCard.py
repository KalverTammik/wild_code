from PyQt5.QtWidgets import QVBoxLayout, QLabel, QFrame, QHBoxLayout
from PyQt5.QtCore import pyqtSignal
from .BaseCard import BaseCard
from ....widgets.layer_dropdown import LayerTreePicker

try:
    from qgis.core import QgsSettings
except Exception:
    QgsSettings = None  # type: ignore


class ModuleCard(BaseCard):
    pendingChanged = pyqtSignal(bool)

    def __init__(self, lang_manager, module_name: str, translated_name: str):
        super().__init__(lang_manager, translated_name)
        self.module_name = module_name
        self._snapshot = None
        # Both pickers use the popup tree UX
        self._element_picker = None
        self._archive_picker = None
        # Track originals/pending separately
        self._orig_element_id = ""
        self._orig_archive_id = ""
        self._pend_element_id = ""
        self._pend_archive_id = ""
        self._element_name_lbl = None
        self._archive_name_lbl = None
        self._build_ui()

    # --- UI ---
    def _build_ui(self):
        cw = self.content_widget()
        cl = QVBoxLayout(cw)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(10)

        sec1_title = QLabel(self.lang_manager.translate("Element layer"), cw)
        sec1_title.setObjectName("SetupCardSectionTitle")
        cl.addWidget(sec1_title)

        row1 = QHBoxLayout(); row1.setContentsMargins(0,0,0,0); row1.setSpacing(8)
        self._element_picker = LayerTreePicker(cw, placeholder=self.lang_manager.translate("Select layer"))
        self._element_picker.layerIdChanged.connect(self._on_element_selected)
        row1.addWidget(self._element_picker, 1)
        self._element_name_lbl = QLabel("", cw)
        self._element_name_lbl.setObjectName("SetupCardDescription")
        row1.addWidget(self._element_name_lbl, 0)
        cl.addLayout(row1)

        sec2_title = QLabel(self.lang_manager.translate("Archive layer"), cw)
        sec2_title.setObjectName("SetupCardSectionTitle")
        cl.addWidget(sec2_title)

        self._archive_picker = LayerTreePicker(cw, placeholder=self.lang_manager.translate("Select layer"))
        self._archive_picker.layerIdChanged.connect(self._on_archive_selected)
        cl.addWidget(self._archive_picker, 1)
        self._archive_name_lbl = QLabel("", cw)
        self._archive_name_lbl.setObjectName("SetupCardDescription")
        cl.addWidget(self._archive_name_lbl)

        info = QLabel(self.lang_manager.translate("Choose layers used by this module (element and archive)."), cw)
        info.setObjectName("SetupCardDescription")
        cl.addWidget(info)

    # --- Lifecycle hooks called by SettingsUI ---
    def on_settings_activate(self, snapshot=None):
        if snapshot is not None:
            self._snapshot = snapshot
            self._element_picker.setSnapshot(snapshot)
            self._archive_picker.setSnapshot(snapshot)
        self._element_picker.on_settings_activate(snapshot=self._snapshot)
        self._archive_picker.on_settings_activate(snapshot=self._snapshot)
        # Load originals (if any) without marking pending
        self._orig_element_id = self._read_saved_layer_id(kind="element")
        self._orig_archive_id = self._read_saved_layer_id(kind="archive")
        self._pend_element_id = ""
        self._pend_archive_id = ""
        if self._orig_element_id:
            self._element_picker.setSelectedLayerId(self._orig_element_id)
        if self._orig_archive_id:
            self._archive_picker.setSelectedLayerId(self._orig_archive_id)
        self._sync_selected_names()
        self.pendingChanged.emit(self.has_pending_changes())

    def on_settings_deactivate(self):
        if self._element_picker:
            self._element_picker.on_settings_deactivate()
        if self._archive_picker:
            self._archive_picker.on_settings_deactivate()

    # --- Persistence ---
    def _settings_key(self, kind: str) -> str:
        # kind in {"element", "archive"}
        return f"wild_code/settings/modules/{self.module_name}/{kind}_layer_id"

    def _read_saved_layer_id(self, kind: str) -> str:
        if not QgsSettings:
            return ""
        try:
            s = QgsSettings()
            return s.value(self._settings_key(kind), "") or ""
        except Exception:
            return ""

    def _write_saved_layer_id(self, kind: str, layer_id: str):
        if not QgsSettings:
            return
        try:
            s = QgsSettings()
            key = self._settings_key(kind)
            if layer_id:
                s.setValue(key, layer_id)
            else:
                s.remove(key)
        except Exception:
            pass

    # --- Apply/Revert/State ---
    def has_pending_changes(self) -> bool:
        el_dirty = bool(self._pend_element_id and self._pend_element_id != self._orig_element_id)
        ar_dirty = bool(self._pend_archive_id and self._pend_archive_id != self._orig_archive_id)
        return el_dirty or ar_dirty

    def apply(self):
        changed = False
        if self._pend_element_id and self._pend_element_id != self._orig_element_id:
            self._write_saved_layer_id("element", self._pend_element_id)
            self._orig_element_id = self._pend_element_id
            self._element_picker.setSelectedLayerId(self._orig_element_id)
            changed = True
        if self._pend_archive_id and self._pend_archive_id != self._orig_archive_id:
            self._write_saved_layer_id("archive", self._pend_archive_id)
            self._orig_archive_id = self._pend_archive_id
            self._archive_picker.setSelectedLayerId(self._orig_archive_id)
            changed = True
        self._pend_element_id = ""
        self._pend_archive_id = ""
        self._sync_selected_names()
        self.pendingChanged.emit(False if changed else self.has_pending_changes())

    def revert(self):
        # Restore originals and clear pending
        self._element_picker.setSelectedLayerId(self._orig_element_id)
        self._archive_picker.setSelectedLayerId(self._orig_archive_id)
        self._pend_element_id = ""
        self._pend_archive_id = ""
        self._sync_selected_names()
        self.pendingChanged.emit(False)

    def _sync_selected_names(self):
        # Update helper labels with selected layer names
        def name_for(picker):
            lyr = picker.selectedLayer() if picker else None
            try:
                return lyr.name() if lyr else ""
            except Exception:
                return ""
        if self._element_name_lbl:
            self._element_name_lbl.setText(name_for(self._element_picker))
        if self._archive_name_lbl:
            self._archive_name_lbl.setText(name_for(self._archive_picker))

    # --- Handlers ---
    def _on_element_selected(self, layer_id: str):
        self._pend_element_id = layer_id or ""
        self._sync_selected_names()
        self.pendingChanged.emit(self.has_pending_changes())

    def _on_archive_selected(self, layer_id: str):
        self._pend_archive_id = layer_id or ""
        self._sync_selected_names()
        self.pendingChanged.emit(self.has_pending_changes())
