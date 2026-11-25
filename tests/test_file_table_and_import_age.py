"""The file table sorts by real date and size and drops stale rows; an older import keeps Kavitro as it is.

From the button audits, fixed 2026-11-23/24:
- the table sorted the shown date text ("9.11" after "10.11") and sizes as text;
- after a failed refresh the old rows (and their preview and delete buttons) stayed;
- an import older than the Kavitro record overwrote it without asking when the address matched.
"""
from __future__ import annotations

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
from qgis.PyQt.QtCore import Qt

from Kavitro_dev.modules.Property.FlowControllers import add_batch_runner
from Kavitro_dev.modules.Property.FlowControllers.property_import_decisions import classify_property_import
from Kavitro_dev.widgets.DataDisplayWidgets.TaskFilesDialog import TaskFilesDialog

_APP = QgsApplication.instance() or QgsApplication([], False)


class FileTableTest(unittest.TestCase):
    FILES = [
        {"uuid": "a", "fileName": "a.pdf", "createdAt": "2026-11-09T10:00:00", "size": 9 * 1024},
        {"uuid": "b", "fileName": "b.pdf", "createdAt": "2026-11-10T10:00:00", "size": 10 * 1024},
        {"uuid": "c", "fileName": "c.pdf", "createdAt": "2025-12-31T10:00:00", "size": 200},
    ]

    def dialog(self) -> TaskFilesDialog:
        dialog = TaskFilesDialog(item_id="t1", initial_files=list(self.FILES))
        self.addCleanup(dialog.deleteLater)
        return dialog

    def column(self, dialog, index=0) -> list[str]:
        return [dialog._table.item(row, index).text() for row in range(dialog._table.rowCount())]

    def test_newest_first_by_the_real_date(self) -> None:
        dialog = self.dialog()
        self.assertEqual(self.column(dialog), ["b.pdf", "a.pdf", "c.pdf"])

    def test_size_sorts_by_bytes(self) -> None:
        dialog = self.dialog()
        dialog._table.sortItems(1, Qt.AscendingOrder)
        self.assertEqual(self.column(dialog), ["c.pdf", "a.pdf", "b.pdf"])

    def test_a_failed_refresh_leaves_no_old_rows(self) -> None:
        dialog = self.dialog()
        dialog._table.selectRow(0)
        dialog._files_loaded(None)
        self.assertEqual(dialog._table.rowCount(), 0)
        self.assertFalse(dialog._delete_button.isEnabled())


class ImportAgeTest(unittest.TestCase):
    DATA = {"cadastralUnit": {"number": "1"}, "address": {"street": "Paju", "houseNumber": ""}}

    @staticmethod
    def info(updated: str) -> dict:
        return {"exists": True, "active_count": 1, "LastUpdated": updated,
                "property": {"id": "861", "cadastralUnitNumber": "1", "displayAddress": "Paju, Martna küla"}}

    def test_an_older_import_is_skipped(self) -> None:
        decision = classify_property_import(self.DATA, "2024-01-01", "", self.info("2025-06-01"))
        self.assertEqual(decision["action"], "skip")

    def test_the_same_date_or_a_newer_import_still_updates(self) -> None:
        for import_date in ("2025-06-01", "2026-01-01"):
            with self.subTest(import_date=import_date):
                decision = classify_property_import(self.DATA, import_date, "", self.info("2025-06-01"))
                self.assertEqual(decision["action"], "update")

    def test_a_skipped_property_is_not_written(self) -> None:
        with patch.object(add_batch_runner.BackendPropertyVerifier, "verify_properties_by_cadastral_number",
                          return_value=self.info("2025-06-01")), \
                patch.object(add_batch_runner.UpdatePropertyData, "update_single_property_item") as update, \
                patch.object(add_batch_runner.MainAddPropertiesFlow, "add_single_property_item") as create:
            result = add_batch_runner.apply_reviewed_backend(self.DATA, [], "2024-01-01", "")
        self.assertIsNone(result)
        update.assert_not_called()
        create.assert_not_called()


if __name__ == "__main__":
    unittest.main()
