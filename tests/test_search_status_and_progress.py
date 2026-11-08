"""The search status text comes from a key, and both progress windows have the Kavitro look."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from PyQt5.QtCore import QCoreApplication, QEvent
from PyQt5.QtWidgets import QApplication
from qgis.core import QgsFeature, QgsVectorLayer

from Kavitro_dev.constants.cadastral_fields import Katastriyksus
from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.modules.Settings.cards import SettingsPropertyManagement as card_module
from Kavitro_dev.modules.Settings.cards.SettingsPropertyManagement import PropertyManagementUI
from Kavitro_dev.modules.works.works_create_controller import WorksCreateController
from Kavitro_dev.utils.mapandproperties import property_search_field_service as service_module
from Kavitro_dev.utils.mapandproperties.property_search_field_service import PropertySearchFieldService
from Kavitro_dev.utils.search import UnifiedSearchController as search_module
from Kavitro_dev.utils.search.UnifiedSearchController import UnifiedSearchController


class SearchStatusTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_the_status_says_what_is_searched_in_the_users_language(self) -> None:
        controller = UnifiedSearchController()
        shown = []
        controller.searchStatus.connect(shown.append)

        with patch.object(search_module, "start_worker"):
            controller.search("  Kase tee ")

        expected = LanguageManager().translate(TranslationKeys.SEARCH_STATUS_SEARCHING).format(term="Kase tee")
        self.assertEqual(shown, [expected])


def _property_layer(count: int) -> QgsVectorLayer:
    fields = "&".join(f"field={name}:string" for name in Katastriyksus.search_field_items)
    # Without geometry: a geometry layer makes QGIS write its default style database into the tree.
    layer = QgsVectorLayer(f"None?{fields}", "kinnistud", "memory")
    for number in range(count):
        feature = QgsFeature(layer.fields())
        feature.setAttribute(Katastriyksus.tunnus, f"7840{number}:001:0001")
        layer.dataProvider().addFeature(feature)
    return layer


class SearchFieldServiceTest(unittest.TestCase):
    def test_progress_goes_to_the_caller_and_no_window_is_made_here(self) -> None:
        layer = _property_layer(3)
        seen = []

        ok, error, changed = PropertySearchFieldService.ensure_search_field(
            layer, on_progress=lambda done, total: seen.append((done, total)))

        self.assertEqual((ok, error, changed), (True, "", 3))
        self.assertEqual(seen, [(3, 3)])
        self.assertFalse(hasattr(sys.modules[PropertySearchFieldService.__module__], "QProgressDialog"))

    def test_errors_are_in_the_users_language(self) -> None:
        # In English: the Estonian text it replaced would pass an Estonian check unchanged.
        english = LanguageManager("en")
        with patch.object(service_module, "LanguageManager", return_value=english):
            ok, error, changed = PropertySearchFieldService.ensure_search_field(None)

        self.assertEqual((ok, changed), (False, 0))
        self.assertEqual(error, english.translate(TranslationKeys.PROPERTY_SEARCH_FIELD_LAYER_INVALID))


class SearchFieldProgressWindowTest(unittest.TestCase):
    def test_the_card_shows_the_kavitro_progress_window_and_closes_it(self) -> None:
        lang = LanguageManager()
        card = SimpleNamespace(lang_manager=lang, _update_search_field_button_state=Mock())
        layer = Mock(featureCount=Mock(return_value=500))

        def build(_layer, *, on_progress):
            on_progress(250, 500)
            on_progress(500, 500)
            return True, "", 500

        with patch.object(card_module.ActiveLayersHelper, "resolve_main_property_layer", return_value=layer), \
                patch.object(card_module, "ProgressDialogModern") as window_class, \
                patch.object(card_module.PropertySearchFieldService, "ensure_search_field", side_effect=build), \
                patch.object(card_module, "ModernMessageDialog"):
            PropertyManagementUI._on_generate_search_field_clicked(card)

        window = window_class.return_value
        self.assertEqual(window_class.call_args.kwargs["title"],
                         lang.translate(TranslationKeys.PROPERTY_SEARCH_FIELD_PROGRESS_TITLE))
        self.assertEqual(window_class.call_args.kwargs["maximum"], 500)
        window.cancel_button.hide.assert_called_once()
        self.assertEqual([c.kwargs["value"] for c in window.update.call_args_list], [0, 250, 500])
        window.close.assert_called_once()


class WorksScanProgressTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_the_scan_window_has_the_kavitro_look(self) -> None:
        owner = SimpleNamespace(_lang=LanguageManager())

        window = WorksCreateController._make_scan_progress_widget(owner, parent_window=None, progress_anchor=None)
        self.addCleanup(self._delete, window)

        self.assertEqual(window.objectName(), "ModernMessageDialog")
        self.assertIn("QDialog#ModernMessageDialog", window.styleSheet())

    @staticmethod
    def _delete(window) -> None:
        window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


if __name__ == "__main__":
    unittest.main()
