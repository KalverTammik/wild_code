"""The card's detail handle: which modules get it, how the detail loads, and what runs before it opens."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from qgis.PyQt.QtCore import QCoreApplication, QEvent
from qgis.PyQt.QtWidgets import QApplication, QLabel, QWidget

from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.widgets.DataDisplayWidgets.ExtraInfoWidget import ExtraInfoFrame

DETAIL_MODULES = ("project", "contract", "coordination", "easement", "task", "works", "asbuilt")


class StubDetail(QLabel):
    def __init__(self):
        super().__init__("detail")
        self.retheme_calls = 0

    def retheme(self) -> None:
        self.retheme_calls += 1


class ExtraInfoDetailTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.frames = []

    def tearDown(self) -> None:
        for frame in self.frames:
            frame.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        ExtraInfoFrame._set_expanded_project_frame(None)

    def frame(self, module_name: str) -> ExtraInfoFrame:
        # A child, as on the card: a parentless widget counts as hidden until it is shown.
        card = QWidget()
        self.frames.append(card)
        return ExtraInfoFrame({"id": "item-1", "name": "Nimi"}, module_name, parent=card, lang_manager=LanguageManager("et"))

    def test_modules_with_a_detail_view_get_the_handle(self) -> None:
        for module_name in DETAIL_MODULES:
            with self.subTest(module=module_name):
                frame = self.frame(module_name)
                self.assertFalse(frame.isHidden())
                self.assertIsNotNone(frame._expand_handle)
                self.assertIsNotNone(frame._detail_container)

    def test_other_modules_keep_a_hidden_frame(self) -> None:
        for module_name in ("property", "home", "settings", ""):
            with self.subTest(module=module_name):
                frame = self.frame(module_name)
                self.assertTrue(frame.isHidden())
                self.assertIsNone(frame._expand_handle)
                self.assertIsNone(frame._detail_container)

    def test_detail_loads_once_and_follows_the_theme(self) -> None:
        frame = self.frame("works")
        detail = StubDetail()
        loader = Mock(return_value=detail)
        frame._extra_info_widget.config.detail_loader = loader

        frame._expand_handle.click()
        frame._expand_handle.click()
        frame._expand_handle.click()
        frame.retheme()

        loader.assert_called_once_with()
        self.assertIs(detail.parent(), frame._detail_container)
        self.assertEqual(detail.retheme_calls, 1)

    def test_easement_runs_its_open_action_before_each_open(self) -> None:
        frame = self.frame("easement")
        config = frame._extra_info_widget.config
        config.detail_loader = Mock(return_value=StubDetail())
        config.detail_open_callback = Mock()

        frame._expand_handle.click()
        self.assertEqual(config.detail_open_callback.call_count, 1)
        frame._expand_handle.click()
        self.assertEqual(config.detail_open_callback.call_count, 1, "closing runs nothing")
        frame._expand_handle.click()
        self.assertEqual(config.detail_open_callback.call_count, 2)

    def test_real_easement_config_opens_its_properties_on_the_map(self) -> None:
        frame = self.frame("easement")

        self.assertTrue(callable(frame._extra_info_widget.config.detail_open_callback))


if __name__ == "__main__":
    unittest.main()
