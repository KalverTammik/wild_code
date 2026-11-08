"""Filters go straight into the toolbar's left grid."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from PyQt5.QtCore import QCoreApplication, QEvent
from PyQt5.QtWidgets import QApplication, QComboBox, QWidget

from Kavitro_dev.ui.ToolbarArea import ModuleToolbarArea


class ToolbarLeftSlotTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.host = QWidget()
        self.toolbar = ModuleToolbarArea(self.host)

    def tearDown(self) -> None:
        self.host.hide()
        self.host.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def test_filter_sits_in_the_left_grid_without_a_wrapper(self) -> None:
        first, second = QComboBox(), QComboBox()

        self.toolbar.add_left(first)
        self.toolbar.add_left(second)

        self.assertEqual(self.toolbar._left_widgets, [first, second])
        for widget in (first, second):
            self.assertIs(widget.parent(), self.toolbar._left)
            self.assertGreaterEqual(self.toolbar._left_layout.indexOf(widget), 0)

    def test_missing_widget_is_ignored(self) -> None:
        self.toolbar.add_left(None)

        self.assertEqual(self.toolbar._left_widgets, [])


if __name__ == "__main__":
    unittest.main()
