from .DatesWidget import DatesWidget
from ...constants.module_icons import MiscIcons
from ...utils.status_color_helper import StatusColorHelper
from ...widgets.theme_manager import styleExtras, IntensityLevels, ThemeShadowColors

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget


class StatusWidget(QWidget):
    def __init__(self, item_data, theme=None, parent=None, show_private_icon=True, lang_manager=None):
        super().__init__(parent)
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addStretch(1)  # push everything right

        if show_private_icon and not item_data.get('isPublic'):
            pub = QLabel()
            pub.setObjectName("ProjectPrivateIcon")
            pub.setToolTip("Privaatne")
            pub.setAlignment(Qt.AlignCenter)
            # themed private icon (using ICON_ADD as requested)
            icon_path = MiscIcons.ICON_IS_PRIVATE
            pm = QPixmap(icon_path)
            if not pm.isNull():
                pub.setPixmap(pm.scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                pub.setText("P")

            pub.setFixedSize(16, 16)
            row.addWidget(pub, 0, Qt.AlignRight | Qt.AlignVCenter)

        status = item_data.get('status', {}) or {}
        name = status.get('name', '-') or '-'
        hex_color = status.get('color', 'cccccc')

        bg, fg, border = StatusColorHelper.upgrade_status_color(hex_color)

        self.status_label = QLabel(name)
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFixedWidth(128)
        self.status_label.setStyleSheet(
            "QLabel#StatusLabel {"
            f"background-color: rgba({bg[0]},{bg[1]},{bg[2]}, 0.95);"
            f"color: rgb({fg[0]},{fg[1]},{fg[2]});"
            f"border: 1px solid rgba({border[0]},{border[1]},{border[2]}, 0.85);"
            "border-radius: 6px;"
            "padding: 3px 10px;"
            "font-weight: 500;"
            "font-size: 11px;"
            "}"
            "QLabel#StatusLabel:hover {"
            f"background-color: rgba({bg[0]},{bg[1]},{bg[2]}, 1.0);"
            "}"
        )
        styleExtras.apply_chip_shadow(
            self.status_label,
            color=ThemeShadowColors.BLUE,
            blur_radius=10,
            x_offset=1,
            y_offset=1,
            alpha_level=IntensityLevels.MEDIUM
        )
        

        row.addWidget(self.status_label, 0, Qt.AlignRight | Qt.AlignVCenter)
        main_layout.addLayout(row)

        # Add DatesWidget underneath the status label
        self.dates_widget = DatesWidget(item_data, lang_manager=lang_manager)
        main_layout.addWidget(self.dates_widget, 0, Qt.AlignRight)

    def retheme(self):
        """Update status styling based on current theme."""
        from ..theme_manager import ThemeManager
        theme = ThemeManager.load_theme_setting()

        styleExtras.apply_chip_shadow(
            self.status_label,
            color=ThemeShadowColors.BLUE,
            blur_radius=10,
            x_offset=1,
            y_offset=1,
            alpha_level=IntensityLevels.MEDIUM
        )

        # Update dates widget theme
        if hasattr(self, 'dates_widget') and self.dates_widget:
            self.dates_widget.retheme()