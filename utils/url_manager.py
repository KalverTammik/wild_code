from enum import Enum

from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QDesktopServices

from ..config.setup import config
from ..Logs.python_fail_logger import PythonFailLogger


class Module(Enum):
    PROJECT = "project"
    CONTRACT = "contract"
    COORDINATION = "coordination"
    LETTER = "letter"
    SPECIFICATION = "specification"
    EASEMENT = "easement"
    ORDINANCE = "ordinance"
    SUBMISSION = "submission"

    ASBUILT = "asbuilt"
    WORKS = "works"
    TASK = "task"

    USER = "user"

    PROPERTY = "property"
    SETTINGS = "settings"
    HOME = "home"
    SIGNALTEST = "signaltest"

    STATUSES = "statuses"
    TYPES = "type"


class ModuleSupports(Enum):
    TAGS = "tags"
    STATUSES = "statuses"
    TYPES = "type"


class loadWebpage:
    @staticmethod
    def open_webpage(web_link: str) -> bool:
        if not web_link:
            return False

        try:
            url = QUrl.fromUserInput(web_link)
            if not url.isValid():
                PythonFailLogger.log_exception(
                    ValueError(f"Invalid URL: {web_link}"),
                    module=PythonFailLogger.LOG_MODULE_UI,
                    event=PythonFailLogger.EVENT_OPEN_WEBPAGE_INVALID_URL,
                )
                return False

            if QDesktopServices.openUrl(url):
                return True

            PythonFailLogger.log_exception(
                RuntimeError(f"QDesktopServices.openUrl returned False: {web_link}"),
                module=PythonFailLogger.LOG_MODULE_UI,
                event=PythonFailLogger.EVENT_OPEN_WEBPAGE_FAILED,
            )
            return False
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=PythonFailLogger.LOG_MODULE_UI,
                event=PythonFailLogger.EVENT_OPEN_WEBPAGE_FAILED,
            )
            return False


class OpenLink:
    def __init__(self):
        self.main = config.get("weblink", "")
        self.privacy = config.get("privacy", "")
        self.terms = config.get("terms", "")
        self.maa_amet = config.get("page_maa_amet", "")

    @staticmethod
    def weblink_by_module(module_path: str) -> str:
        base = (OpenLink().main or "").rstrip("/")
        suffix = (module_path or "").lstrip("/").lower()
        if suffix in (Module.WORKS.value, Module.ASBUILT.value):
            suffix = Module.TASK.value
        return f"{base}/{suffix}" if base and suffix else ""
