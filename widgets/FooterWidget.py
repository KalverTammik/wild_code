from ..config.setup import Version, config
from ..constants.file_paths import ConfigPaths
from ..modules.UrlManager import WebLinks
from .theme_manager import ThemeManager

# Add missing imports
from qgis.PyQt.QtWidgets import QWidget, QHBoxLayout, QLabel
from qgis.PyQt.QtCore import Qt
from qgis.core import Qgis

import datetime
import os

class FooterWidget(QWidget):
    def __init__(self, parent=None, show_left=True, show_right=True):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Automated year for copyright
        current_year = datetime.datetime.now().year

        # Left part: copyright, homepage, privacy, and terms links from config via WebLinks
        if show_left:
            weblinks = WebLinks(config)
            left_label = QLabel(
                f'&copy; {current_year} <b>Valisee</b> | '
                f'<a href="{weblinks.home}">Koduleht</a> | '
                f'<a href="{weblinks.privacy}">Privaatsus</a> | '
                f'<a href="{weblinks.terms}">Kasutustingimused</a>'
            )
            left_label.setOpenExternalLinks(True)
            left_label.setTextFormat(Qt.RichText)
            left_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            layout.addWidget(left_label)
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
        theme_base_dir = os.path.join(os.path.dirname(__file__), '..', 'styles')
        ThemeManager.apply_theme(self, os.path.join(theme_base_dir, 'Dark'), ["main.qss", "footer.qss"])