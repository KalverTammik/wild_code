
import os
import json
from ..constants.file_paths import ConfigPaths, PLUGIN_ROOT, CONFIG_DIR
from PyQt5.QtGui import QCursor

config_file_path = ConfigPaths.CONFIG

with open(config_file_path, "r") as json_content:
    config = json.load(json_content)
