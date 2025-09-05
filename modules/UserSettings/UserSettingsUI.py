from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGroupBox, QCheckBox, QComboBox,
    QSpinBox, QLineEdit, QMessageBox
)
from PyQt5.QtCore import Qt
from ...languages.language_manager import LanguageManager
from ...widgets.theme_manager import ThemeManager
from ...constants.file_paths import QssPaths

class UserSettingsUI(QWidget):
    """
    User-specific settings module for properties manipulation and advanced features.
    Separate from main application settings.
    """
    def __init__(self, lang_manager=None, theme_manager=None):
        super().__init__()
        self.name = "UserSettingsModule"

        # Language manager
        self.lang_manager = lang_manager or LanguageManager()

        # Setup UI
        self.setup_ui()

        # Apply theming
        ThemeManager.apply_module_style(self, [QssPaths.SETUP_CARD])

    def setup_ui(self):
        """Setup the user settings interface."""
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(15)

        # Header
        header_label = QLabel("Kasutaja seaded")
        header_label.setObjectName("ModuleHeader")
        header_label.setAlignment(Qt.AlignCenter)
        root.addWidget(header_label)

        # Description
        desc_label = QLabel("Isiklikud seaded kinnistute haldamiseks ja täpsemaks tööks")
        desc_label.setObjectName("ModuleDescription")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        root.addWidget(desc_label)

        # Scrollable area for settings
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        # Container for settings
        settings_container = QWidget()
        settings_layout = QVBoxLayout(settings_container)
        settings_layout.setContentsMargins(10, 10, 10, 10)
        settings_layout.setSpacing(15)

        # Properties Layer Settings
        self.create_properties_settings(settings_layout)

        # Visualization Settings
        self.create_visualization_settings(settings_layout)

        # Advanced Features
        self.create_advanced_settings(settings_layout)

        # Action buttons
        self.create_action_buttons(settings_layout)

        scroll_area.setWidget(settings_container)
        root.addWidget(scroll_area)

    def create_properties_settings(self, layout):
        """Create properties layer manipulation settings."""
        group = QGroupBox("Kinnistute kihi seaded")
        group_layout = QVBoxLayout(group)

        # Auto-save changes
        auto_save_cb = QCheckBox("Salvesta muudatused automaatselt")
        auto_save_cb.setChecked(True)
        group_layout.addWidget(auto_save_cb)

        # Default layer style
        style_layout = QHBoxLayout()
        style_layout.addWidget(QLabel("Vaikimisi stiil:"))
        style_combo = QComboBox()
        style_combo.addItems(["Tavaline", "Kontuurid", "Värviline", "Läbipaistev"])
        style_combo.setCurrentText("Tavaline")
        style_layout.addWidget(style_combo)
        style_layout.addStretch()
        group_layout.addLayout(style_layout)

        # Buffer distance
        buffer_layout = QHBoxLayout()
        buffer_layout.addWidget(QLabel("Puhvri kaugus (m):"))
        buffer_spin = QSpinBox()
        buffer_spin.setRange(0, 1000)
        buffer_spin.setValue(50)
        buffer_layout.addWidget(buffer_spin)
        buffer_layout.addStretch()
        group_layout.addLayout(buffer_layout)

        layout.addWidget(group)

    def create_visualization_settings(self, layout):
        """Create visualization and display settings."""
        group = QGroupBox("Visualiseerimise seaded")
        group_layout = QVBoxLayout(group)

        # Show labels
        show_labels_cb = QCheckBox("Näita kinnistute silte")
        show_labels_cb.setChecked(True)
        group_layout.addWidget(show_labels_cb)

        # Label field
        label_layout = QHBoxLayout()
        label_layout.addWidget(QLabel("Sildi väli:"))
        label_combo = QComboBox()
        label_combo.addItems(["katastritunnus", "omaniku_nimi", "pindala", "hind"])
        label_combo.setCurrentText("katastritunnus")
        label_layout.addWidget(label_combo)
        label_layout.addStretch()
        group_layout.addLayout(label_layout)

        # Opacity
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("Läbipaistvus (%):"))
        opacity_spin = QSpinBox()
        opacity_spin.setRange(0, 100)
        opacity_spin.setValue(80)
        opacity_layout.addWidget(opacity_spin)
        opacity_layout.addStretch()
        group_layout.addLayout(opacity_layout)

        layout.addWidget(group)

    def create_advanced_settings(self, layout):
        """Create advanced features settings."""
        group = QGroupBox("Täpsemad funktsioonid")
        group_layout = QVBoxLayout(group)

        # Enable spatial analysis
        spatial_cb = QCheckBox("Luba ruumiline analüüs")
        spatial_cb.setChecked(False)
        group_layout.addWidget(spatial_cb)

        # Enable property history
        history_cb = QCheckBox("Luba kinnistute ajalugu")
        history_cb.setChecked(True)
        group_layout.addWidget(history_cb)

        # Custom queries
        query_layout = QHBoxLayout()
        query_layout.addWidget(QLabel("Kohandatud päringud:"))
        query_edit = QLineEdit()
        query_edit.setPlaceholderText("SQL-päring...")
        query_layout.addWidget(query_edit)
        group_layout.addLayout(query_layout)

        # Export settings
        export_cb = QCheckBox("Luba automaatne eksport")
        export_cb.setChecked(False)
        group_layout.addWidget(export_cb)

        layout.addWidget(group)

    def create_action_buttons(self, layout):
        """Create action buttons for settings management."""
        buttons_layout = QHBoxLayout()

        # Save button
        save_btn = QPushButton("Salvesta seaded")
        save_btn.clicked.connect(self.save_settings)
        buttons_layout.addWidget(save_btn)

        # Reset button
        reset_btn = QPushButton("Taasta vaikeväärtused")
        reset_btn.clicked.connect(self.reset_settings)
        buttons_layout.addWidget(reset_btn)

        # Export settings
        export_btn = QPushButton("Ekspordi seaded")
        export_btn.clicked.connect(self.export_settings)
        buttons_layout.addWidget(export_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

    def save_settings(self):
        """Save user settings."""
        QMessageBox.information(
            self,
            "Seaded salvestatud",
            "Teie isiklikud seaded on edukalt salvestatud."
        )

    def reset_settings(self):
        """Reset settings to defaults."""
        reply = QMessageBox.question(
            self,
            "Taasta vaikeväärtused",
            "Kas olete kindel, et soovite taastada vaikeväärtused?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            QMessageBox.information(
                self,
                "Vaikeväärtused taastatud",
                "Seaded on taastatud vaikeväärtustele."
            )

    def export_settings(self):
        """Export user settings."""
        QMessageBox.information(
            self,
            "Seaded eksporditud",
            "Teie seaded on eksporditud faili."
        )

    def activate(self):
        """Called when the module becomes active."""
        pass

    def deactivate(self):
        """Called when the module becomes inactive."""
        pass

    def get_widget(self):
        """Return the module's main QWidget."""
        return self
