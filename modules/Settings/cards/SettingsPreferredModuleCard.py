from PyQt5.QtWidgets import QVBoxLayout, QLabel, QComboBox, QHBoxLayout
from PyQt5.QtCore import pyqtSignal, QTimer
from .SettingsBaseCard import SettingsBaseCard
from ....utils.url_manager import Module
from ....constants.settings_keys import SettingsService
from ....languages.translation_keys import TranslationKeys
from ....widgets.theme_manager import ThemeManager, Theme, is_dark
class PreferredModuleCard(SettingsBaseCard):
    """Card for setting the user's preferred module that opens by default."""

    pendingChanged = pyqtSignal(bool)

    def __init__(self, lang_manager):
        super().__init__(lang_manager, "Eelistatud moodul")
        self._original_preferred = ""
        self._pending_preferred = ""
        self._settings = SettingsService()

        # Setup the card content
        self._setup_content()

        # Apply theme after content is set up
        self.retheme()

        # Load current settings
        self._load_current_settings()

    def retheme(self):
        """Apply theme and set label colors for dark mode."""
        super().retheme()  # Apply QSS first
        # Delay setting label colors to ensure QSS is applied
        QTimer.singleShot(0, self._apply_label_colors)

    def _apply_label_colors(self):
        """Apply label colors after QSS is processed."""
        if is_dark(ThemeManager.effective_theme()):
            self.desc_label.setStyleSheet("color: #ffffff !important;")
            self.label.setStyleSheet("color: #ffffff !important;")
            self.current_label.setStyleSheet("color: #ffffff !important;")
        else:
            # Reset to default for light mode (black text)
            self.desc_label.setStyleSheet("color: #000000;")
            self.label.setStyleSheet("color: #000000;")
            self.current_label.setStyleSheet("color: #000000;")

    def _setup_content(self):
        """Setup the card content with module selection."""
        layout = QVBoxLayout(self._content)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Description
        self.desc_label = QLabel("Vali moodul, mis avaneb vaikimisi rakenduse käivitamisel:")
        self.desc_label.setWordWrap(True)
        layout.addWidget(self.desc_label)

        # Module selection
        selection_layout = QHBoxLayout()
        self.label = QLabel("Eelistatud moodul:")
        selection_layout.addWidget(self.label)

        self.module_combo = QComboBox()
        self.module_combo.addItem("Avaleht", Module.HOME)
        self.module_combo.addItem("Projektid", Module.PROJECT)
        self.module_combo.addItem("Lepingud", Module.CONTRACT)
        self.module_combo.addItem("Seaded", Module.SETTINGS)
        self.module_combo.addItem("Kinnistu", Module.PROPERTY)

        self.module_combo.currentTextChanged.connect(self._on_module_changed)
        selection_layout.addWidget(self.module_combo)
        selection_layout.addStretch()
        layout.addLayout(selection_layout)

        # Current selection display
        self.current_label = QLabel()
        self.current_label.setObjectName("CurrentSelectionLabel")
        layout.addWidget(self.current_label)

        layout.addStretch()

    def _load_current_settings(self):
        """Load the current preferred module setting."""
        try:
            preferred_module = self._settings.preferred_module(default=Module.HOME.name) or Module.HOME.name
            self._original_preferred = preferred_module
            self._pending_preferred = preferred_module

            # Set the combo box to the current value
            for i in range(self.module_combo.count()):
                if self.module_combo.itemData(i).name == preferred_module:
                    self.module_combo.setCurrentIndex(i)
                    break

            self._update_current_label()
        except Exception as e:
            print(f"Error loading preferred module setting: {e}")
            # Default to home
            self._original_preferred = Module.HOME.name
            self._pending_preferred = Module.HOME.name

    def _on_module_changed(self):
        """Handle module selection change."""
        current_data = self.module_combo.currentData()
        current_name = current_data.name if hasattr(current_data, 'name') else str(current_data)
        if current_name != self._pending_preferred:
            self._pending_preferred = current_name
            self.pendingChanged.emit(self._has_pending_changes())
            self._update_current_label()

    def _update_current_label(self):
        """Update the current selection display label."""
        module_names = {
            Module.HOME.name: "Avaleht",
            Module.PROJECT.name: "Projektid",
            Module.CONTRACT.name: "Lepingud",
            Module.SETTINGS.name: "Seaded",
            Module.PROPERTY.name: "Kinnistu"
        }

        current_name = module_names.get(self._pending_preferred, "Avaleht")
        self.current_label.setText(f"Praegune valik: {current_name}")

    def _has_pending_changes(self):
        """Check if there are pending changes."""
        return self._pending_preferred != self._original_preferred

    def apply_changes(self):
        """Apply the pending changes."""
        try:
            if self._has_pending_changes():
                self._settings.preferred_module(value=self._pending_preferred)
                self._original_preferred = self._pending_preferred
                self.pendingChanged.emit(False)
                return True
        except Exception as e:
            print(f"Error saving preferred module setting: {e}")
        return False

    def discard_changes(self):
        """Discard pending changes."""
        self._pending_preferred = self._original_preferred
        # Reset combo box to original value
        for i in range(self.module_combo.count()):
            if self.module_combo.itemData(i).name == self._original_preferred:
                self.module_combo.setCurrentIndex(i)
                break
        self._update_current_label()
        self.pendingChanged.emit(False)

    def has_pending_changes(self):
        """Public method to check for pending changes."""
        return self._has_pending_changes()

    def get_preferred_module(self):
        """Get the currently selected preferred module."""
        return self._pending_preferred
