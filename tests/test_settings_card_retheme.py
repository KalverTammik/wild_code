"""A theme switch reaches the filter pickers and a card nested in a settings card.

Found in the user's QGIS test 2026-11-23: after switching dark -> light the tag and type
preference pickers stayed dark, and so did the disabled "Lisa kinnistuid" button of the
property management card that sits inside the property module card.
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from qgis.core import QgsApplication
from PyQt5.QtCore import QCoreApplication, QEvent
from PyQt5.QtWidgets import QPushButton, QVBoxLayout

from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.modules.Settings.cards.SettingsBaseCard import SettingsBaseCard
from Kavitro_dev.ui.theme_manager import ThemeManager
from Kavitro_dev.widgets.Filters.TagsFilterWidget import TagsFilterWidget
from Kavitro_dev.widgets.Filters.TypeFilterWidget import TypeFilterWidget


class SettingsCardRethemeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def setUp(self) -> None:
        self.theme = "dark"
        theme = patch.object(ThemeManager, "effective_theme", side_effect=lambda: self.theme)
        theme.start()
        self.addCleanup(theme.stop)
        lang = LanguageManager(language="et")

        self.card = SettingsBaseCard(lang, "Kooskõlastused")
        self.addCleanup(self.dispose, self.card)
        layout = QVBoxLayout(self.card.content_widget())
        self.tags = TagsFilterWidget("coordination", self.card, settings_logic=Mock(), auto_load=False)
        self.types = TypeFilterWidget("coordination", self.card, settings_logic=Mock(), auto_load=False)
        self.nested = SettingsBaseCard(lang, "Kinnistute haldus")
        self.add_button = QPushButton("Lisa kinnistuid", self.nested)
        self.add_button.setProperty("variant", "success")
        self.add_button.setEnabled(False)
        for widget in (self.tags, self.types, self.nested):
            layout.addWidget(widget)

    @staticmethod
    def dispose(widget) -> None:
        widget.hide()
        widget.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def test_switching_to_light_restyles_the_pickers_and_the_nested_card(self) -> None:
        self.assertIn("#303a42", self.tags._control.styleSheet())
        self.assertIn("#17241d", self.nested.styleSheet())  # dark disabled success button

        self.theme = "light"
        self.card.retheme()

        for picker in (self.tags, self.types):
            with self.subTest(picker=type(picker).__name__):
                self.assertIn("#ffffff", picker._control.styleSheet())
                self.assertNotIn("#303a42", picker._control.styleSheet())
        self.assertIn("#e7f6ee", self.nested.styleSheet())  # light disabled success button
        self.assertNotIn("#17241d", self.nested.styleSheet())

    def test_switching_back_to_dark_follows_too(self) -> None:
        self.theme = "light"
        self.card.retheme()
        self.theme = "dark"
        self.card.retheme()
        self.assertIn("#303a42", self.types._control.styleSheet())
        self.assertIn("#17241d", self.nested.styleSheet())


if __name__ == "__main__":
    unittest.main()
