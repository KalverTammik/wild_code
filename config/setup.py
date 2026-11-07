
import json
from ..constants.file_paths import ConfigPaths

config_file_path = ConfigPaths.CONFIG

with open(config_file_path, "r") as json_content:
    config = json.load(json_content)
