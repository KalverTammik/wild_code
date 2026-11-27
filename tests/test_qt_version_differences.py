"""Places where Qt5 (QGIS 3) and Qt6 (QGIS 4) differ and the plugin has its own code."""
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from qgis.PyQt.QtCore import QEvent, QPoint, QPointF, Qt
from qgis.PyQt.QtGui import QEnterEvent, QMouseEvent, QTextDocument
from qgis.core import QgsApplication

from Kavitro_dev.utils.qt_events import global_pos
from Kavitro_dev.widgets.DataDisplayWidgets.task_file_external_open import web_attribute, webengine_classes
from Kavitro_dev.widgets.DataDisplayWidgets.TaskFilePreviewDialog import TaskFilePreviewDialog

_APP = QgsApplication.instance() or QgsApplication([], False)


class GlobalPositionTest(unittest.TestCase):
    def test_a_mouse_press_gives_its_screen_position(self) -> None:
        event = QMouseEvent(QEvent.Type.MouseButtonPress, QPointF(2, 3), QPointF(102, 203),
                            Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)

        self.assertEqual(global_pos(event), QPoint(102, 203))

    def test_an_enter_event_gives_its_screen_position(self) -> None:
        event = QEnterEvent(QPointF(1, 1), QPointF(1, 1), QPointF(51, 61))

        self.assertEqual(global_pos(event), QPoint(51, 61))


class RichTextTest(unittest.TestCase):
    def test_markup_stays_text_and_line_breaks_stay(self) -> None:
        value = "<b>fail</b> & 'nimi'\r\nteine rida\n\nneljas"
        document = QTextDocument()
        document.setHtml(TaskFilePreviewDialog._plain_text_as_rich_text(value))

        # QTextDocument writes a <br> as U+2028 in its plain text
        shown = document.toPlainText().replace("\u2028", "\n")
        self.assertEqual(shown, "<b>fail</b> & 'nimi'\nteine rida\n\nneljas")


class WebEngineClassesTest(unittest.TestCase):
    def test_qt6_takes_the_settings_class_from_webengine_core(self) -> None:
        settings = types.SimpleNamespace(WebAttribute=types.SimpleNamespace(PdfViewerEnabled="pdf"))
        widgets = types.SimpleNamespace(QWebEngineView="view")
        core = types.SimpleNamespace(QWebEngineSettings=settings)
        with patch.dict(sys.modules, {"qgis.PyQt.QtWebEngineWidgets": widgets, "qgis.PyQt.QtWebEngineCore": core}):
            self.assertEqual(webengine_classes(), (settings, "view"))
        self.assertEqual(web_attribute(settings, "PdfViewerEnabled"), "pdf")

    def test_an_unscoped_attribute_is_found_and_a_missing_one_is_none(self) -> None:
        settings = types.SimpleNamespace(PluginsEnabled=2)

        self.assertEqual(web_attribute(settings, "PluginsEnabled"), 2)
        self.assertIsNone(web_attribute(settings, "PdfViewerEnabled"))

    def test_without_webengine_the_import_error_reaches_the_caller(self) -> None:
        with patch.dict(sys.modules, {"qgis.PyQt.QtWebEngineWidgets": None}):
            with self.assertRaises(ImportError):
                webengine_classes()


class CardMenuButtonStyleTest(unittest.TestCase):
    def test_both_themes_leave_the_more_icon_the_whole_button(self) -> None:
        for theme in ("Light", "Dark"):
            qss = (Path(__file__).resolve().parents[1] / "styles" / theme / "ModuleCard.qss").read_text(encoding="utf-8")
            self.assertRegex(qss, r"#MoreActionsButton::menu-indicator\s*\{\s*width: 0px;", theme)


if __name__ == "__main__":
    unittest.main()
