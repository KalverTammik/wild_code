"""The pending GIS dialog's title: its own name and a rule for it in both themes."""
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

from qgis.PyQt.QtCore import QCoreApplication, QEvent
from qgis.PyQt.QtGui import QFont, QPalette
from qgis.PyQt.QtWidgets import QApplication, QLabel

from Kavitro_dev.constants.file_paths import QssPaths, StylePaths
from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.modules.works.works_pending_gis_dialog import WorksPendingGisDialog
from Kavitro_dev.widgets.theme_manager import Theme, ThemeManager

TITLE_NAME = "WorksPendingGisTitle"
THEMES = {Theme.LIGHT: (StylePaths.LIGHT, "#333333"), Theme.DARK: (StylePaths.DARK, "#e2e8f0")}


class WorksPendingGisDialogTitleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.lang = LanguageManager(language="et")

    def _dialog(self, theme: str) -> WorksPendingGisDialog:
        # The dialog styles itself once, when it is built, so the theme is chosen before that.
        with patch.object(ThemeManager, "effective_theme", return_value=theme):
            dialog = WorksPendingGisDialog(rows=[], on_open=Mock(), lang_manager=self.lang)

        def delete() -> None:
            dialog.hide()
            dialog.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

        self.addCleanup(delete)
        return dialog

    def test_title_label_has_a_name_of_its_own(self) -> None:
        title = self._dialog(Theme.LIGHT).findChild(QLabel, TITLE_NAME)

        self.assertIsNotNone(title)
        self.assertEqual(title.text(), self.lang.translate(TranslationKeys.WORKS_PENDING_GIS_DIALOG_TITLE))

    def test_both_themes_style_the_title(self) -> None:
        for theme, (theme_dir, color) in THEMES.items():
            with self.subTest(theme=theme):
                qss = (Path(theme_dir) / QssPaths.MODULE_INFO).read_text(encoding="utf-8")
                self.assertIn(f"QLabel#{TITLE_NAME}", qss)

                title = self._dialog(theme).findChild(QLabel, TITLE_NAME)
                title.ensurePolished()

                self.assertGreater(title.font().weight(), QFont.Normal)
                self.assertEqual(title.font().pixelSize(), 14)
                self.assertEqual(title.palette().color(QPalette.WindowText).name(), color)


if __name__ == "__main__":
    unittest.main()
