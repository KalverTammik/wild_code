from ..config.setup import Version, config
from ..constants.file_paths import ConfigPaths
from ..utils.url_manager import WebLinks
from .theme_manager import ThemeManager

# Add missing imports
from qgis.PyQt.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl
from qgis.PyQt.QtCore import Qt
from qgis.core import Qgis

import datetime
import os

class FooterWidget(QWidget):
    def __init__(self, parent=None, show_left=True, show_right=True):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(6, 1, 6, 1)  # left, top, right, bottom
        layout.setSpacing(2)

        # Automated year for copyright
        current_year = datetime.datetime.now().year

        # Left part: copyright, homepage, privacy, and terms links from config via WebLinks
        if show_left:
            weblinks = WebLinks(config)
            left_frame = QWidget()
            left_frame.setObjectName("footerLeftFrame")
            left_frame_layout = QHBoxLayout()
            left_frame_layout.setContentsMargins(0, 0, 0, 0)
            left_frame_layout.setSpacing(0)
            # Copyright label (no links)
            copyright_label = QLabel(f'© {current_year} <b>Valisee</b> | ')
            copyright_label.setObjectName("footerCopyrightLabel")
            copyright_label.setTextFormat(Qt.RichText)
            copyright_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            left_frame_layout.addWidget(copyright_label)
            # Links as flat buttons styled as links

            link_buttons = []
            link_info = [
                (weblinks.home, "Koduleht"),
                (weblinks.privacy, "Privaatsus"),
                (weblinks.terms, "Kasutustingimused")
            ]
            for idx, (url, text) in enumerate(link_info):
                btn = QPushButton(text)
                btn.setObjectName("footerLinkButton")
                btn.setCursor(Qt.PointingHandCursor)
                btn.setFlat(True)
                btn.setFocusPolicy(Qt.NoFocus)
                btn.clicked.connect(lambda checked, u=url: QDesktopServices.openUrl(QUrl(u)))
                link_buttons.append(btn)
                left_frame_layout.addWidget(btn)
                if idx < len(link_info) - 1:
                    sep = QLabel("|")
                    sep.setObjectName("footerLinkSeparator")
                    sep.setAlignment(Qt.AlignVCenter)
                    left_frame_layout.addWidget(sep)
            left_frame.setLayout(left_frame_layout)
            layout.addWidget(left_frame)
        else:
            layout.addStretch(1)

        # Right part: QGIS and plugin version
        if show_right:
            metadata_file = ConfigPaths.METADATA
            qgis_version = Qgis.QGIS_VERSION
            plugin_version = Version.get_plugin_version(metadata_file)
            right_label = QLabel(f"QGIS {qgis_version} | Plugin v{plugin_version}")
            right_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            right_label.setObjectName("footerLabel")
            layout.addWidget(right_label)
        else:
            layout.addStretch(1)

        self.setLayout(layout)

        # Apply footer style using ThemeManager (main + footer QSS)
        from ..constants.file_paths import StylePaths, QssPaths
        theme = ThemeManager.load_theme_setting()
        theme_dir = StylePaths.DARK if theme == "dark" else StylePaths.LIGHT
        ThemeManager.apply_theme(self, theme_dir, [QssPaths.MAIN, QssPaths.FOOTER])