"""Ending a map pick without picking brings the plugin window back.

Found in the button audits (properties, projects, contracts, works), fixed 2026-11-23: Escape, a right-click or
choosing another map tool left the window minimised and the flow waiting. The one-click tools now cancel on
a tool change too, and the rectangle selection ends on all three and tells its caller.
"""
from __future__ import annotations

import ast
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT.parent))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from qgis.core import QgsApplication, QgsFeature, QgsGeometry, QgsPointXY, QgsVectorLayer
from qgis.gui import QgsMapCanvas, QgsMapToolPan
from qgis.PyQt.QtCore import QEvent, QPoint, QPointF, Qt
from qgis.PyQt.QtGui import QKeyEvent, QMouseEvent
from qgis.PyQt.QtTest import QTest
from qgis.PyQt.QtWidgets import QApplication

from Kavitro_dev.Logs.python_fail_logger import PythonFailLogger
from Kavitro_dev.utils.MapTools import map_selection_controller as controller_module
from Kavitro_dev.utils.MapTools.canvas_click_tool import SingleClickMapTool

_APP = QgsApplication.instance() or QgsApplication([], False)


def release(button) -> Mock:
    event = Mock()
    event.button.return_value = button
    event.pos.return_value = QPoint(5, 5)
    return event


class CanvasCase(unittest.TestCase):
    def setUp(self) -> None:
        self.canvas = QgsMapCanvas()
        self.pan = QgsMapToolPan(self.canvas)

        def close() -> None:
            self.canvas.unsetMapTool(self.canvas.mapTool())
            QApplication.processEvents()
            self.canvas.deleteLater()
            QApplication.processEvents()

        self.addCleanup(close)


class SingleClickToolTest(CanvasCase):
    def tool(self, on_selected=None):
        self.selected, self.cancelled = [], []
        tool = SingleClickMapTool(self.canvas, on_selected or self.selected.append, lambda: self.cancelled.append(1))
        self.canvas.setMapTool(tool)
        return tool

    def test_another_map_tool_cancels_the_pick(self) -> None:
        self.tool()
        self.canvas.setMapTool(self.pan)
        QApplication.processEvents()
        self.assertEqual(self.cancelled, [1])

    def test_escape_and_right_click_cancel_once(self) -> None:
        tool = self.tool()
        tool.keyPressEvent(QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier))
        tool.canvasReleaseEvent(release(Qt.MouseButton.RightButton))
        self.canvas.setMapTool(self.pan)
        QApplication.processEvents()
        self.assertEqual(self.cancelled, [1])

    def test_a_finished_pick_is_not_cancelled_by_the_callers_cleanup(self) -> None:
        def done(point) -> None:
            self.selected.append(point)
            self.canvas.setMapTool(self.pan)  # the caller removes the tool while handling the click

        tool = self.tool(on_selected=done)
        tool.canvasReleaseEvent(release(Qt.MouseButton.LeftButton))
        QApplication.processEvents()
        self.assertEqual((len(self.selected), self.cancelled), (1, []))

    def test_a_kept_tool_takes_another_click(self) -> None:
        # "Nothing found here" keeps the tool for the next click.
        tool = self.tool()
        tool.canvasReleaseEvent(release(Qt.MouseButton.LeftButton))
        tool.canvasReleaseEvent(release(Qt.MouseButton.LeftButton))
        self.assertEqual(len(self.selected), 2)
        self.canvas.setMapTool(self.pan)
        QApplication.processEvents()
        self.assertEqual(self.cancelled, [1])


class RectangleSelectionTest(CanvasCase):
    def setUp(self) -> None:
        super().setUp()
        self.layer = QgsVectorLayer("Point?crs=EPSG:3301", "kinnistud", "memory")
        feature = QgsFeature(self.layer.fields())
        feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(1, 1)))
        self.layer.dataProvider().addFeatures([feature])
        self.select_tool = QgsMapToolPan(self.canvas)  # stands in for QGIS' rectangle select tool
        fake_iface = Mock()
        fake_iface.mapCanvas.return_value = self.canvas
        fake_iface.actionSelectRectangle.return_value.trigger.side_effect = lambda: self.canvas.setMapTool(
            self.select_tool)
        for target, name, value in (
            (controller_module, "iface", fake_iface),
            (controller_module.MapHelpers, "ensure_layer_visible", None),
        ):
            patcher = patch.object(target, name, value) if value is not None else patch.object(target, name)
            patcher.start()
            self.addCleanup(patcher.stop)
        for name in ("log", "log_exception"):
            patcher = patch.object(PythonFailLogger, name)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.controller = controller_module.MapSelectionController()
        self.selected, self.abandoned = [], []
        self.assertTrue(self.controller.start_selection(
            self.layer, on_selected=lambda _layer, features: self.selected.append(features),
            on_abandoned=lambda: self.abandoned.append(1),
        ))
        self.addCleanup(self.controller.cancel_selection)

    def test_another_map_tool_ends_the_selection(self) -> None:
        self.canvas.setMapTool(self.pan)
        self.assertEqual(self.abandoned, [1])
        self.layer.selectByIds([next(self.layer.getFeatures()).id()])
        QTest.qWait(150)
        self.assertEqual(self.selected, [])  # no longer listening

    def test_escape_ends_the_selection(self) -> None:
        QApplication.sendEvent(self.canvas, QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier))
        self.assertEqual(self.abandoned, [1])

    def test_right_click_ends_the_selection(self) -> None:
        event = QMouseEvent(QEvent.Type.MouseButtonRelease, QPointF(3, 3), Qt.MouseButton.RightButton, Qt.MouseButton.RightButton, Qt.KeyboardModifier.NoModifier)
        QApplication.sendEvent(self.canvas.viewport(), event)
        self.assertEqual(self.abandoned, [1])

    def test_a_completed_selection_is_not_abandoned_by_the_pan_tool(self) -> None:
        controller_module.iface.actionPan.return_value.trigger.side_effect = lambda: self.canvas.setMapTool(self.pan)
        self.layer.selectByIds([next(self.layer.getFeatures()).id()])
        QTest.qWait(150)
        self.assertEqual(len(self.selected), 1)
        self.assertEqual(self.abandoned, [])
        self.assertIs(self.canvas.mapTool(), self.pan)

    def test_a_cancel_by_the_caller_is_not_an_abandon(self) -> None:
        self.controller.cancel_selection()
        self.canvas.setMapTool(self.pan)
        self.assertEqual(self.abandoned, [])


class EveryCallerRestoresItsWindowTest(unittest.TestCase):
    def test_each_rectangle_selection_names_what_to_do_when_abandoned(self) -> None:
        missing = []
        for path in sorted(PLUGIN_ROOT.rglob("*.py")):
            rel = path.relative_to(PLUGIN_ROOT)
            if rel.parts[0] in {"tests", "tools", ".venv", "Temporary", "docs"}:
                continue
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                        and node.func.attr == "start_selection_for_layer"
                        and "on_abandoned" not in {k.arg for k in node.keywords}):
                    missing.append(f"{rel}:{node.lineno}")
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
