"""Record card contacts: tiles with initials and roles, the rest counted behind "+N"."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QCoreApplication, QEvent
from qgis.PyQt.QtWidgets import QFrame, QLabel

from Kavitro_dev.python.responses import DataDisplayExtractors
from Kavitro_dev.ui.theme_manager import ThemeManager
from Kavitro_dev.widgets.DataDisplayWidgets.InfoCardHeader import InfocardHeaderFrame
from Kavitro_dev.widgets.DataDisplayWidgets.ContactsWidget import ClientWidget, ContactsWidget, initials

_APP = QgsApplication.instance() or QgsApplication([], False)


def item(count: int, total: int | None = None) -> dict:
    edges = [{"notes": f"Roll {i}", "node": {"displayName": f"Inimene {i}", "type": "COMPANY" if i == 1 else "PERSON"}}
             for i in range(count)]
    connection = {"edges": edges}
    if total is not None:
        connection["pageInfo"] = {"total": total}
    return {"contacts": connection}


class ContactTilesTest(unittest.TestCase):
    def build(self, data: dict, width: int = 2000) -> ContactsWidget:
        widget = ContactsWidget(data)

        def delete() -> None:
            widget.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

        self.addCleanup(delete)
        widget.resize(width, widget.height())
        widget.reflow()
        return widget

    @staticmethod
    def texts(widget, name: str) -> list[str]:
        return [label.text() for label in widget.findChildren(QLabel, name)]

    @staticmethod
    def on_line(widget) -> list[str]:
        return [tile.findChild(QLabel, "ContactName").text() for tile in widget._tiles if not tile.isHidden()]

    def test_a_wide_line_shows_every_contact_read_and_counts_the_unread(self) -> None:
        widget = self.build(item(5, total=9))

        self.assertEqual(self.on_line(widget), [f"Inimene {i}" for i in range(5)])
        self.assertEqual(widget._mark.text(), "+4")

    def test_widening_brings_the_hidden_contacts_back(self) -> None:
        widget = self.build(item(5), width=10)
        for count in (3, 5):
            widget.resize(widget._width_with_mark(count), widget.height())
            QCoreApplication.processEvents()
            widget.reflow()
            with self.subTest(count=count):
                self.assertEqual(len(self.on_line(widget)), count)
        self.assertTrue(widget._mark.isHidden())

    def test_a_narrow_line_keeps_at_least_one_contact(self) -> None:
        widget = self.build(item(5), width=10)
        self.assertEqual(self.on_line(widget), ["Inimene 0"])
        self.assertEqual(widget._mark.text(), "+4")

        widget.resize(widget.line_width(2) + widget.gap + widget._mark_width(3), widget.height())
        widget.reflow()

        self.assertEqual(self.on_line(widget), ["Inimene 0", "Inimene 1"])
        self.assertEqual(widget._mark.text(), "+3")
        self.assertLess(widget.minimumSizeHint().width(), widget.sizeHint().width())
        # Asking for the sizes leaves the number on the mark as it was.
        self.assertEqual(widget._mark.text(), "+3")

    def test_the_mark_opens_the_rest_as_the_same_tiles(self) -> None:
        widget = self.build(item(5, total=9))
        widget.resize(widget._width_with_mark(3), widget.height())
        widget.reflow()

        widget._show_popup()
        popup = widget._popup
        self.addCleanup(widget._close_popup)

        self.assertEqual(self.texts(popup, "ContactName"), ["Inimene 3", "Inimene 4"])
        self.assertEqual(len(popup.findChildren(QFrame, "ContactTile")), 2)
        self.assertIn("4", self.texts(popup, "ContactRole")[-1])  # four more were not read
        widget.retheme()
        self.assertIsNone(widget._popup)

    def test_no_mark_when_all_are_shown_and_hidden_without_contacts(self) -> None:
        self.assertTrue(self.build(item(2))._mark.isHidden())
        self.assertTrue(self.build(item(0)).isHidden())

    def test_a_company_gets_a_squarer_mark_than_a_person(self) -> None:
        widget = self.build(item(2))

        person, company = widget.findChildren(QLabel, "ContactAvatar")
        self.assertIn("border-radius: 12px", person.styleSheet())
        self.assertIn("border-radius: 6px", company.styleSheet())

    def test_the_client_is_a_tile_that_says_so(self) -> None:
        data = {"client": {"displayName": " Kindel Tugi OÜ ", "type": "COMPANY"}}
        header = InfocardHeaderFrame(data, module_name="projects")
        self.addCleanup(header.deleteLater)

        client = header.findChild(ClientWidget)

        self.assertEqual(self.texts(client, "ContactName"), ["Kindel Tugi OÜ"])
        self.assertEqual(len(self.texts(client, "ContactRole")), 1)
        self.assertIn("border-radius: 6px", client.findChild(QLabel, "ContactAvatar").styleSheet())
        self.assertIsNone(DataDisplayExtractors.extract_client({"client": None}))

    def test_a_long_name_is_cut_on_the_tile_and_whole_in_the_tooltip(self) -> None:
        name = "Väga Pika Nimega Kinnisvaraarenduse ja Halduse Osaühing"
        widget = self.build({"contacts": {"edges": [{"node": {"displayName": name}}]}})

        shown = self.on_line(widget)[0]
        self.assertLessEqual(len(shown), 40)
        self.assertTrue(shown.endswith("…"))
        self.assertEqual(widget._tiles[0].toolTip(), name)

    def test_company_forms_are_not_initials(self) -> None:
        self.assertEqual([initials(name) for name in ("OÜ Parim Notar", "Vahva Kaevur AS", "Mari", "")],
                         ["PN", "VK", "M", "?"])

    def test_the_total_never_counts_fewer_than_were_read(self) -> None:
        self.assertEqual(DataDisplayExtractors.extract_contact_total(item(4, total=1)), 4)
        self.assertEqual(DataDisplayExtractors.extract_contact_total(item(2)), 2)

    def test_the_style_follows_the_theme(self) -> None:
        with patch.object(ThemeManager, "effective_theme", return_value="light"):
            widget = self.build(item(1))
        light = widget.styleSheet()
        with patch.object(ThemeManager, "effective_theme", return_value="dark"):
            widget.retheme()

        self.assertNotEqual(widget.styleSheet(), light)


if __name__ == "__main__":
    unittest.main()
