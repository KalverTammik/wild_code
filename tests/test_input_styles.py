from __future__ import annotations

import os
import sys
import unittest
from collections import Counter
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QCoreApplication, QEvent, QPoint
from qgis.PyQt.QtGui import QFont, QFontMetrics
from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QDialog,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QStyle,
    QStyleOptionButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from Kavitro_dev.constants.file_paths import QssPaths, StylePaths
from Kavitro_dev.widgets.theme_manager import ThemeManager

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
# What the QGIS "Blend of Gray" UI theme sets on these subcontrols at application level.
DARK_UI_THEME_BUTTONS = """
QAbstractSpinBox::drop-down { background-color: #000000; border: 1px solid #000000; }
QAbstractSpinBox::up-button { background-color: #000000; }
QAbstractSpinBox::down-button { background-color: #000000; }
QComboBox::drop-down:editable { background-color: #000000; border: 1px solid #000000; }
"""


class _StyledWindowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def _window(self, theme_dir: str) -> QDialog:
        window = QDialog()

        def delete() -> None:
            window.hide()
            window.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

        self.addCleanup(delete)
        ThemeManager.apply_theme(window, theme_dir, [QssPaths.MAIN])
        QVBoxLayout(window)
        return window

    def _show(self, window: QDialog):
        window.resize(320, 260)
        window.show()
        self.app.processEvents()
        return window.grab().toImage()


class TableSelectionStyleTest(_StyledWindowTest):
    def _cell_colors(self, theme_dir: str) -> tuple[str, str]:
        window = self._window(theme_dir)
        table = QTableWidget(2, 1, window)
        table.setItem(0, 0, QTableWidgetItem(""))
        table.setItem(1, 0, QTableWidgetItem(""))
        table.setColumnWidth(0, 120)
        table.selectRow(1)
        window.layout().addWidget(table)
        image = self._show(window)

        def color(row: int) -> str:
            center = table.visualItemRect(table.item(row, 0)).center()
            return image.pixelColor(table.viewport().mapTo(window, center)).name()

        return color(0), color(1)

    def test_no_style_uses_the_state_qt_does_not_have(self) -> None:
        # Qt ignores an unknown state, so ":selected:inactive" painted every cell as selected.
        offenders = [
            str(path.relative_to(PLUGIN_ROOT))
            for path in (PLUGIN_ROOT / "styles").rglob("*.qss")
            if ":inactive" in path.read_text(encoding="utf-8")
        ]

        self.assertEqual(offenders, [])

    def test_dark_table_marks_only_the_selected_row(self) -> None:
        plain, selected = self._cell_colors(StylePaths.DARK)

        self.assertEqual(plain, "#2e2f38")
        self.assertEqual(selected, "#1a6468")

    def test_light_table_selection_stands_out_from_the_window(self) -> None:
        _plain, selected = self._cell_colors(StylePaths.LIGHT)

        self.assertEqual(selected, "#e3f0ff")


class InputButtonStyleTest(_StyledWindowTest):
    def setUp(self) -> None:
        self.app.setStyleSheet(DARK_UI_THEME_BUTTONS)
        self.addCleanup(self.app.setStyleSheet, "")

    def _inputs(self, window: QDialog) -> dict:
        editable = QComboBox(window)
        editable.setEditable(True)
        date = QDateEdit(window)
        date.setCalendarPopup(True)
        stamp = QDateTimeEdit(window)
        stamp.setCalendarPopup(True)
        inputs = {"date": date, "date and time": stamp, "number": QDoubleSpinBox(window), "editable combo": editable}
        for widget in inputs.values():
            window.layout().addWidget(widget)
        return inputs

    def test_input_buttons_blend_into_the_field(self) -> None:
        for theme_dir in (StylePaths.LIGHT, StylePaths.DARK):
            window = self._window(theme_dir)
            inputs = self._inputs(window)
            image = self._show(window)
            for name, widget in inputs.items():
                origin = widget.mapTo(window, QPoint(0, 0))
                field = image.pixelColor(origin.x() + widget.width() // 2, origin.y() + 4)
                # A column at the right edge of the button, clear of its arrow and the rounded corner.
                x = origin.x() + widget.width() - 4
                column = {image.pixelColor(x, origin.y() + y).name() for y in range(6, widget.height() - 6)}
                with self.subTest(theme=theme_dir, input=name):
                    self.assertEqual(column, {field.name()})

    def test_all_inputs_have_the_same_height(self) -> None:
        window = self._window(StylePaths.LIGHT)
        inputs = self._inputs(window)
        line = QLineEdit(window)
        window.layout().addWidget(line)
        self._show(window)

        for name, widget in inputs.items():
            with self.subTest(input=name):
                self.assertEqual(widget.height(), line.height())


class CalendarStyleTest(_StyledWindowTest):
    def _main_color(self, theme_dir: str) -> str:
        window = self._window(theme_dir)
        date = QDateEdit(window)
        date.setCalendarPopup(True)
        window.layout().addWidget(date)
        self._show(window)
        image = date.calendarWidget().grab().toImage()
        pixels = Counter(
            image.pixelColor(x, y).name()
            for x in range(0, image.width(), 2)
            for y in range(image.height() // 3, image.height(), 2)
        )
        return pixels.most_common(1)[0][0]

    def test_calendar_days_use_the_surface_of_the_theme(self) -> None:
        self.assertEqual(self._main_color(StylePaths.LIGHT), "#ffffff")
        self.assertEqual(self._main_color(StylePaths.DARK), "#2e2f38")


class TabStyleTest(_StyledWindowTest):
    PADDING = 28

    def test_tab_is_wide_enough_for_its_text_in_the_weight_it_is_painted_with(self) -> None:
        for theme_dir in (StylePaths.LIGHT, StylePaths.DARK):
            window = self._window(theme_dir)
            tabs = QTabWidget(window)
            for text in ("Andmed", "Asukoht"):
                tabs.addTab(QWidget(), text)
            window.layout().addWidget(tabs)
            self._show(window)
            bar = tabs.tabBar()
            bold = QFont(bar.font())
            bold.setWeight(QFont.Bold)
            for index in range(bar.count()):
                text = bar.tabText(index)
                with self.subTest(theme=theme_dir, tab=text):
                    self.assertEqual(bar.font().weight(), QFont.Bold)
                    self.assertGreaterEqual(bar.tabRect(index).width(), QFontMetrics(bold).horizontalAdvance(text) + self.PADDING)


class CheckboxStyleTest(_StyledWindowTest):
    # Stands in for the QGIS UI theme's images, which used to cover the plugin's check box style.
    UI_THEME_IMAGES = "".join(
        f"QCheckBox::indicator:{state} {{ image: url({(PLUGIN_ROOT / 'styles' / 'Light' / 'check.png').as_posix()}); }}"
        for state in ("unchecked", "checked", "unchecked:disabled", "checked:disabled")
    )
    SURFACE = {StylePaths.LIGHT: "#ffffff", StylePaths.DARK: "#303a42"}
    CHECKED = {StylePaths.LIGHT: "#0078d4", StylePaths.DARK: "#09908f"}

    def setUp(self) -> None:
        self.app.setStyleSheet(self.UI_THEME_IMAGES)
        self.addCleanup(self.app.setStyleSheet, "")

    def _indicator_colors(self, checkbox: QCheckBox, window: QDialog) -> Counter:
        image = self._show(window)
        option = QStyleOptionButton()
        checkbox.initStyleOption(option)
        rect = checkbox.style().subElementRect(QStyle.SE_CheckBoxIndicator, option, checkbox)
        origin = checkbox.mapTo(window, rect.topLeft())
        return Counter(
            image.pixelColor(origin.x() + x, origin.y() + y).name()
            for x in range(2, rect.width() - 2)
            for y in range(2, rect.height() - 2)
        )

    def _checkbox(self, theme_dir: str, *, checked: bool, enabled: bool = True) -> tuple[QCheckBox, QDialog]:
        window = self._window(theme_dir)
        checkbox = QCheckBox("Valik", window)
        checkbox.setChecked(checked)
        checkbox.setEnabled(enabled)
        window.layout().addWidget(checkbox)
        return checkbox, window

    def test_every_theme_has_the_check_mark_its_style_points_to(self) -> None:
        for theme_dir in (StylePaths.LIGHT, StylePaths.DARK):
            self.assertTrue((Path(theme_dir) / "check_white.svg").exists(), theme_dir)

    def test_unchecked_box_shows_the_plugin_surface_and_no_image(self) -> None:
        for theme_dir, surface in self.SURFACE.items():
            colors = self._indicator_colors(*self._checkbox(theme_dir, checked=False))
            with self.subTest(theme=theme_dir):
                self.assertEqual(set(colors), {surface})

    def test_checked_box_is_filled_and_has_a_white_mark(self) -> None:
        for theme_dir, fill in self.CHECKED.items():
            colors = self._indicator_colors(*self._checkbox(theme_dir, checked=True))
            with self.subTest(theme=theme_dir):
                self.assertEqual(colors.most_common(1)[0][0], fill)
                self.assertGreater(colors["#ffffff"], 0)

    def test_disabled_checked_box_still_shows_its_mark(self) -> None:
        for theme_dir, fill in self.CHECKED.items():
            colors = self._indicator_colors(*self._checkbox(theme_dir, checked=True, enabled=False))
            with self.subTest(theme=theme_dir):
                self.assertNotEqual(colors.most_common(1)[0][0], fill)
                self.assertGreater(colors["#ffffff"], 0)

    def test_preferred_module_box_stays_visible_on_its_pill(self) -> None:
        for theme_dir in (StylePaths.LIGHT, StylePaths.DARK):
            window = self._window(theme_dir)
            ThemeManager.apply_theme(window, theme_dir, [QssPaths.MAIN, QssPaths.SETUP_CARD])
            card = QFrame(window)
            card.setObjectName("SetupCard")
            pills = QFrame(card)
            pills.setObjectName("AccessPills")
            pill = QFrame(pills)
            pill.setObjectName("AccessPill")
            checkbox = QCheckBox(pill)
            checkbox.setObjectName("PreferredModulecb")
            QHBoxLayout(pill).addWidget(checkbox)
            QHBoxLayout(pills).addWidget(pill)
            QHBoxLayout(card).addWidget(pills)
            window.layout().addWidget(card)
            image = self._show(window)
            option = QStyleOptionButton()
            checkbox.initStyleOption(option)
            rect = checkbox.style().subElementRect(QStyle.SE_CheckBoxIndicator, option, checkbox)
            origin = checkbox.mapTo(window, rect.topLeft())
            edge = image.pixelColor(origin.x() + rect.width() // 2, origin.y()).name()
            inside = image.pixelColor(origin.x() + rect.width() // 2, origin.y() + rect.height() // 2).name()
            with self.subTest(theme=theme_dir):
                self.assertNotEqual(edge, inside)


if __name__ == "__main__":
    unittest.main()
