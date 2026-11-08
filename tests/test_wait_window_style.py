"""The API wait window has the Kavitro look even when it opens over the QGIS window during a map pick."""
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
from PyQt5.QtWidgets import QApplication, QWidget

from Kavitro_dev import main as main_module
from Kavitro_dev.python import api_request_task
from Kavitro_dev.python.api_request_task import set_wait_window_style
from Kavitro_dev.utils.messagesHelper import ModernMessageDialog


class WaitWindowStyleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.addCleanup(set_wait_window_style, None)
        # Stands in for the QGIS main window, which is the active one while the map is picked.
        self.qgis_window = QWidget()
        self.addCleanup(self._delete, self.qgis_window)

    @staticmethod
    def _delete(widget: QWidget) -> None:
        widget.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def open_wait_window(self) -> api_request_task._RequestDialog:
        with patch.object(api_request_task.QApplication, "activeWindow", return_value=self.qgis_window):
            window = api_request_task._RequestDialog()
        self.addCleanup(self._delete, window)
        return window

    def test_over_the_qgis_window_it_looks_like_the_kavitro_messages(self) -> None:
        set_wait_window_style(ModernMessageDialog.style_as_message)

        window = self.open_wait_window()

        self.assertIs(window.parent(), self.qgis_window)
        self.assertEqual(window.objectName(), "ModernMessageDialog")
        self.assertIn("QDialog#ModernMessageDialog", window.styleSheet())
        self.assertEqual(window.property("messageType"), "message")

    def test_without_a_registered_style_qt_draws_it(self) -> None:
        window = self.open_wait_window()

        self.assertEqual(window.styleSheet(), "")

    def test_the_plugin_registers_the_style_at_start_and_removes_it_at_unload(self) -> None:
        plugin = main_module.WildCodePlugin(Mock())
        plugin._crash_logger = Mock()
        with patch.object(main_module, "QAction"):
            plugin.initGui()
        self.assertIs(api_request_task._wait_window_style, ModernMessageDialog.style_as_message)

        with patch.object(main_module.PluginDialog, "get_instance", return_value=None):
            plugin.unload()
        self.assertIsNone(api_request_task._wait_window_style)


if __name__ == "__main__":
    unittest.main()
