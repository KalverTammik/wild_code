#!/usr/bin/env python3
"""
Visual representation of ModuleCard layout structure
Showing the Display Options section with checkbox
"""
import sys
from PyQt5.QtWidgets import (
    QApplication, QVBoxLayout, QWidget, QLabel, QFrame, QHBoxLayout,
    QGroupBox, QCheckBox
)
from PyQt5.QtCore import Qt

class ModuleCardLayoutDemo(QWidget):
    """Demo showing the ModuleCard layout structure"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ModuleCard Layout Structure - Display Options")
        self.setGeometry(100, 100, 900, 700)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Title
        title = QLabel("ModuleCard Layout Structure")
        title.setStyleSheet("font-weight: bold; font-size: 16px; color: #333;")
        layout.addWidget(title)

        # Main content widget simulation
        content_widget = QFrame(self)
        content_widget.setStyleSheet("border: 1px solid #ccc; border-radius: 5px; background: #f9f9f9;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(8)

        # 1. Layers Container (Main + Archive side by side)
        layers_container = QFrame(content_widget)
        layers_container.setObjectName("LayersContainer")
        layers_container.setStyleSheet("border: 1px solid #007bff; border-radius: 3px; background: #e7f3ff;")
        layers_layout = QHBoxLayout(layers_container)
        layers_layout.setContentsMargins(5, 5, 5, 5)
        layers_layout.setSpacing(8)

        # Main layer group
        main_group = QGroupBox("Modules main layer", layers_container)
        main_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #28a745; border-radius: 3px; margin-top: 5px; } QGroupBox::title { color: #28a745; }")
        main_layout = QHBoxLayout(main_group)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(6)

        main_dropdown = QLabel("[LayerTreePicker - Element]")
        main_dropdown.setStyleSheet("background: white; border: 1px solid #ccc; padding: 5px; border-radius: 3px;")
        main_layout.addWidget(main_dropdown, 2)

        main_explanation = QLabel("See on teie mooduli põhikiht. Valige kiht, mis sisaldab peamisi andmeid...")
        main_explanation.setWordWrap(True)
        main_explanation.setStyleSheet("color: #666; font-size: 10px;")
        main_layout.addWidget(main_explanation, 1)

        layers_layout.addWidget(main_group)

        # Archive layer group
        archive_group = QGroupBox("Archive layer", layers_container)
        archive_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #ffc107; border-radius: 3px; margin-top: 5px; } QGroupBox::title { color: #ffc107; }")
        archive_layout = QHBoxLayout(archive_group)
        archive_layout.setContentsMargins(4, 4, 4, 4)
        archive_layout.setSpacing(6)

        archive_dropdown = QLabel("[LayerTreePicker - Archive]")
        archive_dropdown.setStyleSheet("background: white; border: 1px solid #ccc; padding: 5px; border-radius: 3px;")
        archive_layout.addWidget(archive_dropdown, 2)

        archive_explanation = QLabel("See valikuline arhiivikiht salvestab ajaloolisi või varukoopia andmeid...")
        archive_explanation.setWordWrap(True)
        archive_explanation.setStyleSheet("color: #666; font-size: 10px;")
        archive_layout.addWidget(archive_explanation, 1)

        layers_layout.addWidget(archive_group)

        content_layout.addWidget(layers_container)

        # 2. Options Container (Display + Status side by side)
        options_container = QFrame(content_widget)
        options_container.setObjectName("OptionsContainer")
        options_container.setStyleSheet("border: 1px solid #dc3545; border-radius: 3px; background: #ffeaea;")
        options_layout = QHBoxLayout(options_container)
        options_layout.setContentsMargins(5, 5, 5, 5)
        options_layout.setSpacing(8)

        # Display options group (THIS IS "Kuvamisvalikud")
        display_group = QGroupBox("Display Options (Kuvamisvalikud)", options_container)
        display_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #dc3545; border-radius: 3px; margin-top: 5px; } QGroupBox::title { color: #dc3545; }")
        display_layout = QHBoxLayout(display_group)
        display_layout.setContentsMargins(4, 4, 4, 4)
        display_layout.setSpacing(6)

        # Settings container with CHECKBOX
        settings_container = QFrame(display_group)
        settings_container.setObjectName("SettingsContainer")
        settings_container.setStyleSheet("border: 1px solid #6f42c1; border-radius: 3px; background: #f8f4ff;")
        settings_layout = QVBoxLayout(settings_container)
        settings_layout.setContentsMargins(5, 5, 5, 5)
        settings_layout.setSpacing(4)

        # THE CHECKBOX - This is what the user is asking about
        show_numbers_checkbox = QCheckBox("Show project numbers")
        show_numbers_checkbox.setChecked(True)
        show_numbers_checkbox.setStyleSheet("font-weight: bold; color: #6f42c1;")
        settings_layout.addWidget(show_numbers_checkbox)

        display_layout.addWidget(settings_container, 2)

        # Explanation text
        display_explanation = QLabel("When enabled, project/contract numbers will be displayed in item cards for easy identification.")
        display_explanation.setWordWrap(True)
        display_explanation.setStyleSheet("color: #666; font-size: 10px;")
        display_layout.addWidget(display_explanation, 1)

        options_layout.addWidget(display_group)

        # Status preferences group
        status_group = QGroupBox("Status Preferences", options_container)
        status_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #17a2b8; border-radius: 3px; margin-top: 5px; } QGroupBox::title { color: #17a2b8; }")
        status_layout = QHBoxLayout(status_group)
        status_layout.setContentsMargins(4, 4, 4, 4)
        status_layout.setSpacing(6)

        status_widget = QLabel("[StatusFilterWidget]")
        status_widget.setStyleSheet("background: white; border: 1px solid #ccc; padding: 5px; border-radius: 3px;")
        status_layout.addWidget(status_widget, 2)

        status_explanation = QLabel("Select statuses you want to prioritize for this module. These will be highlighted in the interface.")
        status_explanation.setWordWrap(True)
        status_explanation.setStyleSheet("color: #666; font-size: 10px;")
        status_layout.addWidget(status_explanation, 1)

        options_layout.addWidget(status_group)

        content_layout.addWidget(options_container)

        layout.addWidget(content_widget)

        # Legend
        legend = QLabel(
            "🎨 Layout Legend:\n"
            "🔵 Layers Container (Main + Archive side by side)\n"
            "🟢 Main Layer Group\n"
            "🟡 Archive Layer Group\n"
            "🔴 Options Container (Display + Status side by side)\n"
            "🔴 Display Options Group (Kuvamisvalikud)\n"
            "🟣 Settings Container with CHECKBOX\n"
            "🔵 Status Preferences Group"
        )
        legend.setWordWrap(True)
        legend.setStyleSheet("background: #f8f9f9; border: 1px solid #ddd; padding: 10px; border-radius: 5px; font-size: 11px;")
        layout.addWidget(legend)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ModuleCardLayoutDemo()
    window.show()
    sys.exit(app.exec_())
