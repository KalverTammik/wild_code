import os
import json
import datetime
from ..constants.file_paths import FilePaths, PLUGIN_ROOT, CONFIG_DIR
from qgis.core import Qgis
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor

config_file_path = os.path.join(PLUGIN_ROOT, CONFIG_DIR, FilePaths.get_file_path(FilePaths.CONFIG))

with open(config_file_path, "r") as json_content:
    config = json.load(json_content)

class Version:
    @staticmethod
    def get_plugin_version(metadata_file):
        with open(metadata_file, 'r') as f:
            for line in f:
                if line.strip().startswith("version="):
                    return line.strip().split('=')[1]

class FooterWidget(QWidget):
    def __init__(self, parent=None, show_left=True, show_right=True):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Automated year for copyright
        current_year = datetime.datetime.now().year

        # Left part: copyright and homepage link
        if show_left:
            left_label = QLabel(f'© Valisee {current_year} | <a href="https://kavitro.com">Kavitro</a>')
            left_label.setOpenExternalLinks(True)
            left_label.setTextFormat(Qt.RichText)
            left_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            layout.addWidget(left_label)
        else:
            layout.addStretch(1)

        # Right part: QGIS and plugin version
        if show_right:
            metadata_file = FilePaths.get_file_path(FilePaths.metadata)
            qgis_version = Qgis.QGIS_VERSION
            plugin_version = Version.get_plugin_version(metadata_file)
            right_label = QLabel(f"QGIS {qgis_version} | Plugin v{plugin_version}")
            right_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            right_label.setObjectName("footerLabel")
            layout.addWidget(right_label)
        else:
            layout.addStretch(1)

        self.setLayout(layout)


