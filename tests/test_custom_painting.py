"""Every widget the plugin paints itself is painted once on the running Qt.

Qt 6 closes QGIS on an exception inside paintEvent (the spinner did that with a QPoint), so each
one is rendered here with the exception hook collecting what would have ended the session.
"""
from __future__ import annotations

import ast
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QCoreApplication, QEvent

from Kavitro_dev.widgets.DataDisplayWidgets.MembersView import AvatarBubble
from Kavitro_dev.widgets.DelayHelpers.glow_progress_bar import GlowProgressBar
from Kavitro_dev.widgets.DelayHelpers.LoadingSpinner import GradientSpinner
from Kavitro_dev.widgets.home.dashboard_cards import PAGE, HomeCard, Snapshot
from Kavitro_dev.widgets.select_arrow import SelectArrow

_APP = QgsApplication.instance() or QgsApplication([], False)
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
PAINTED = {"AvatarBubble", "GlowProgressBar", "GradientSpinner", "HomeCard", "SelectArrow"}


class CustomPaintingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.failures: list[str] = []
        patcher = patch.object(sys, "excepthook", lambda kind, value, _tb: self.failures.append(f"{kind.__name__}: {value}"))
        patcher.start()
        self.addCleanup(patcher.stop)

    def _paint(self, widget) -> None:
        def delete() -> None:
            widget.hide()
            widget.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

        self.addCleanup(delete)
        widget.show()
        QCoreApplication.processEvents()
        widget.grab()
        self.assertEqual(self.failures, [], type(widget).__name__)

    def test_every_painted_widget_is_covered_here(self) -> None:
        found = set()
        for folder in ("modules", "ui", "utils", "widgets"):
            for path in (PLUGIN_ROOT / folder).rglob("*.py"):
                for node in ast.walk(ast.parse(path.read_text(encoding="utf-8-sig"))):
                    if isinstance(node, ast.ClassDef) and any(
                            isinstance(item, ast.FunctionDef) and item.name == "paintEvent" for item in node.body):
                        found.add(node.name)
        self.assertEqual(found, PAINTED, "paint the new widget in this module too")

    def test_loading_spinner_with_both_texts(self) -> None:
        spinner = GradientSpinner(text="Laadin", sub_text="oota")
        spinner.setAngle(90)
        self._paint(spinner)

    def test_progress_bar_in_every_state(self) -> None:
        for state in (GlowProgressBar.IDLE, GlowProgressBar.RUNNING, GlowProgressBar.ERROR):
            with self.subTest(state=state):
                bar = GlowProgressBar()
                bar.resize(200, 22)
                bar.setRange(0, 10)
                bar.setValue(4)
                bar.setState(state)
                self._paint(bar)

    def test_home_card_before_its_numbers_arrive(self) -> None:
        # The other states are painted in test_home_dashboard.
        self._paint(HomeCard(PAGE[0][0][0], Snapshot()))

    def test_unassigned_avatar(self) -> None:
        self._paint(AvatarBubble("-", unassigned=True))

    def test_select_arrow_enabled_and_disabled(self) -> None:
        for enabled in (True, False):
            arrow = SelectArrow()
            arrow.setEnabled(enabled)
            self._paint(arrow)


if __name__ == "__main__":
    unittest.main()
