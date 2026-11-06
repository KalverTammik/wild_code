from __future__ import annotations

import os
import re
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from qgis.core import QgsApplication
from qgis.gui import QgsCheckableComboBox
from qgis.PyQt.QtCore import QCoreApplication, QEvent
from qgis.PyQt.QtWidgets import QComboBox, QStyledItemDelegate

from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.modules.asbuilt.asbuilt_geometry_form_dialog import AsBuiltGeometryFormDialog
from Kavitro_dev.widgets.LocationFilterWidget import LocationFilterWidget
from Kavitro_dev.widgets.select_arrow import SelectArrow
from Kavitro_dev.widgets.theme_manager import ThemeManager

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def plugin_sources():
    for path in PLUGIN_ROOT.rglob("*.py"):
        relative = path.relative_to(PLUGIN_ROOT)
        if relative.parts[0] not in {"tests", "Temporary", ".git"}:
            yield relative, path.read_text(encoding="utf-8")


class StandardComboPopupTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def _delete_later(self, widget) -> None:
        def delete() -> None:
            widget.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

        self.addCleanup(delete)

    def assert_list_popup(self, combo: QComboBox) -> None:
        self.assertIsInstance(combo.itemDelegate(), QStyledItemDelegate)
        self.assertTrue(combo.view().property("kavitroFormPopup"))
        self.assertIn("combobox-popup: 0", combo.styleSheet())

    def test_form_dialog_uses_the_list_popup(self) -> None:
        dialog = AsBuiltGeometryFormDialog(item_data={"id": "1"})
        self._delete_later(dialog)
        combos = dialog.findChildren(QComboBox)
        self.assertTrue(combos)
        for combo in combos:
            with self.subTest(combo=combo.objectName()):
                self.assert_list_popup(combo)

    def test_location_filter_styles_only_its_plain_combos(self) -> None:
        widget = LocationFilterWidget(LanguageManager(language="et"))
        self._delete_later(widget)

        self.assert_list_popup(widget.county_combo)
        self.assert_list_popup(widget.municipality_combo)
        self.assertIsInstance(widget.city_combo, QgsCheckableComboBox)
        self.assertFalse(widget.city_combo.view().property("kavitroFormPopup"))

    def test_settings_retheme_keeps_the_list_popup(self) -> None:
        combo = QComboBox()
        self._delete_later(combo)

        for _ in range(2):
            ThemeManager.apply_combo_popup_style(combo)

        self.assert_list_popup(combo)
        self.assertEqual(len(combo.findChildren(QStyledItemDelegate)), 1)

    def test_every_file_with_a_plain_combo_styles_its_popup(self) -> None:
        created = re.compile(r"\b(QComboBox|QgsFieldComboBox)\(")
        unstyled = [
            str(relative)
            for relative, text in plugin_sources()
            if created.search(text) and "combo_popup_style" not in text
        ]

        self.assertEqual(unstyled, [])


class SelectArrowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def test_no_select_control_draws_a_letter_as_its_arrow(self) -> None:
        letters = [str(relative) for relative, text in plugin_sources() if re.search(r'QLabel\(\s*"v"', text)]

        self.assertEqual(letters, [])

    def test_arrow_is_a_triangle_pointing_down(self) -> None:
        arrow = SelectArrow()
        self.addCleanup(arrow.deleteLater)

        image = arrow.grab().toImage()
        background = image.pixelColor(0, image.height() - 1)
        widths = [
            sum(image.pixelColor(x, y) != background for x in range(image.width()))
            for y in range(image.height())
        ]

        self.assertGreater(widths[0], 5)
        self.assertLessEqual(widths[-1], 3)
        self.assertEqual(widths, sorted(widths, reverse=True))


if __name__ == "__main__":
    unittest.main()
