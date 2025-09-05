#!/usr/bin/env python3
"""
Demo showing the improved checkbox styling in Display Options
"""
import sys
from PyQt5.QtWidgets import (
    QApplication, QVBoxLayout, QWidget, QLabel, QFrame, QHBoxLayout,
    QGroupBox, QCheckBox
)
from PyQt5.QtCore import Qt

class CheckboxStylingDemo(QWidget):
    """Demo showing improved checkbox styling"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Checkbox Styling Demo - Before vs After")
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Title
        title = QLabel("Checkbox Styling Improvements")
        title.setStyleSheet("font-weight: bold; font-size: 16px; color: #333;")
        layout.addWidget(title)

        # Demo container
        demo_container = QFrame(self)
        demo_container.setStyleSheet("""
            QFrame { border: 1px solid #ccc; border-radius: 5px; background: #f9f9f9; }
        """)
        demo_layout = QHBoxLayout(demo_container)
        demo_layout.setSpacing(20)

        # BEFORE (problematic styling)
        before_group = QGroupBox("BEFORE - Issues Fixed", demo_container)
        before_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dc3545;
                border-radius: 3px;
                margin-top: 5px;
                background: rgba(255,255,255,0.02);
            }
            QGroupBox::title { color: #dc3545; }
        """)
        before_layout = QHBoxLayout(before_group)
        before_layout.setContentsMargins(4, 4, 4, 4)
        before_layout.setSpacing(6)

        # Problematic container (no padding)
        before_container = QFrame(before_group)
        before_container.setStyleSheet("""
            QFrame {
                border: 1px solid rgba(255,255,255,0.3);
                background: rgba(255,255,255,0.1);
            }
        """)
        before_settings_layout = QVBoxLayout(before_container)
        before_settings_layout.setContentsMargins(0, 0, 0, 0)  # No padding!
        before_settings_layout.setSpacing(0)

        before_checkbox = QCheckBox("Show item numbers")
        before_checkbox.setChecked(True)
        # No specific styling - uses defaults
        before_settings_layout.addWidget(before_checkbox)

        before_layout.addWidget(before_container, 2)

        before_explanation = QLabel("❌ Checkbox too close to border\n❌ Dark background from default styling\n❌ No proper spacing")
        before_explanation.setWordWrap(True)
        before_explanation.setStyleSheet("color: #dc3545; font-size: 10px;")
        before_layout.addWidget(before_explanation, 1)

        demo_layout.addWidget(before_group)

        # AFTER (improved styling)
        after_group = QGroupBox("AFTER - Issues Fixed", demo_container)
        after_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #28a745;
                border-radius: 3px;
                margin-top: 5px;
                background: rgba(255,255,255,0.02);
            }
            QGroupBox::title { color: #28a745; }
        """)
        after_layout = QHBoxLayout(after_group)
        after_layout.setContentsMargins(4, 4, 4, 4)
        after_layout.setSpacing(6)

        # Improved container with proper styling
        after_container = QFrame(after_group)
        after_container.setObjectName("SettingsContainer")
        after_container.setStyleSheet("""
            QFrame#SettingsContainer {
                background: rgba(255,255,255,0.02);
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 4px;
                padding: 8px;
                margin: 2px 0px;
            }
            QFrame#SettingsContainer QCheckBox {
                background: transparent;
                border: none;
                padding: 4px 0px;
                margin: 2px 0px;
                color: #333;
                font-size: 12px;
            }
            QFrame#SettingsContainer QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid rgba(0,0,0,0.3);
                border-radius: 3px;
                background: rgba(255,255,255,0.8);
            }
            QFrame#SettingsContainer QCheckBox::indicator:checked {
                background: rgba(15, 118, 110, 0.8);
                border-color: #0f766e;
            }
        """)
        after_settings_layout = QVBoxLayout(after_container)
        after_settings_layout.setContentsMargins(6, 6, 6, 6)  # Proper padding!
        after_settings_layout.setSpacing(4)

        after_checkbox = QCheckBox("Show item numbers")
        after_checkbox.setChecked(True)
        after_settings_layout.addWidget(after_checkbox)

        after_layout.addWidget(after_container, 2)

        after_explanation = QLabel("✅ Proper spacing from borders\n✅ Clean background styling\n✅ Consistent with theme\n✅ Better visual hierarchy")
        after_explanation.setWordWrap(True)
        after_explanation.setStyleSheet("color: #28a745; font-size: 10px;")
        after_layout.addWidget(after_explanation, 1)

        demo_layout.addWidget(after_group)

        layout.addWidget(demo_container)

        # Summary
        summary = QLabel(
            "🎯 Key Improvements:\n"
            "• Added proper padding (6px margins) around checkbox\n"
            "• Styled SettingsContainer with subtle background and border\n"
            "• Customized checkbox appearance to match theme\n"
            "• Improved indicator styling with proper colors\n"
            "• Better visual separation and hierarchy"
        )
        summary.setWordWrap(True)
        summary.setStyleSheet("background: #e7f3ff; border: 1px solid #007bff; padding: 10px; border-radius: 5px; font-size: 11px;")
        layout.addWidget(summary)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CheckboxStylingDemo()
    window.show()
    sys.exit(app.exec_())
