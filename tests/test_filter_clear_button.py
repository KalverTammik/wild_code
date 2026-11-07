"""The shared filter clear button must reload the feed in every module that uses it."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from PyQt5.QtCore import QCoreApplication, QEvent
from PyQt5.QtWidgets import QApplication

from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.module_manager import ModuleManager
from Kavitro_dev.modules.asbuilt.AsBuiltUi import AsBuiltModule
from Kavitro_dev.modules.easements.EasementsUi import EasementsModule
from Kavitro_dev.modules.projects.ProjectsUi import ProjectsModule
from Kavitro_dev.python.api_client import APIClient
from Kavitro_dev.widgets.Filters import filter_refresh_helper as helper_module


def delete_now(widget) -> None:
    widget.hide()
    widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


class FilterClearButtonTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        for patcher in (
            patch.object(ModuleManager, "getModuleSupports", return_value=(False, False, False, False)),
            patch.object(APIClient, "send_query", side_effect=AssertionError("Unexpected API call")),
            patch("requests.sessions.Session.request", side_effect=AssertionError("Unexpected network request")),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def assert_clear_reloads_feed(self, module) -> None:
        self.addCleanup(delete_now, module)
        # The real engine would page through the API; the test only needs to see the reload request.
        module.feed_load_engine = Mock()

        with patch.object(helper_module.PythonFailLogger, "log_exception") as log_exception:
            module._refresh_helper._on_clear_clicked()

        log_exception.assert_not_called()
        module.feed_load_engine.schedule_load.assert_called_once()

    def test_projects_clear_reloads_feed(self) -> None:
        self.assert_clear_reloads_feed(ProjectsModule(language=LanguageManager("et")))

    def test_asbuilt_clear_reloads_feed(self) -> None:
        self.assert_clear_reloads_feed(AsBuiltModule(lang_manager=LanguageManager("et")))

    def test_easements_clear_reloads_feed(self) -> None:
        self.assert_clear_reloads_feed(EasementsModule(lang_manager=LanguageManager("et")))


if __name__ == "__main__":
    unittest.main()
