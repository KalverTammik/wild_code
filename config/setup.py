
import os
import json
from ..constants.file_paths import FilePaths, PLUGIN_ROOT, CONFIG_DIR
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



