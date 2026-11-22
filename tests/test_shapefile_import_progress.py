"""Shapefile import progress and the help button after the headless cleanup.

The layer engine used to open its own progress window. It now only reports
ShapefileImportProgress to an optional callback, and the property SHP import flow shows
the window. ShowHelp used to ask ModuleManager for the active module; the plugin dialog
now passes the module name in.
"""
from __future__ import annotations

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

from qgis.core import QgsApplication, QgsFeature, QgsGeometry, QgsPointXY, QgsProject, QgsVectorLayer

from Kavitro_dev.constants.help_urls import DEFAULT_HELP_URL, HELP_URLS
from Kavitro_dev.constants.module_names import Module
from Kavitro_dev.engines.LayerCreationEngine import (
    LayerCreationEngine,
    MailablGroupFolders,
    ShapefileImportProgress,
)
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.modules.Property.FlowControllers import property_shp_import_flow as flow_module
from Kavitro_dev.modules.Property.FlowControllers.property_shp_import_flow import (
    SHPLayerLoader,
    SHPLoadStatus,
    _ImportProgressWindow,
)
from Kavitro_dev.utils.help import ShowHelp as show_help_module
from Kavitro_dev.utils.help.ShowHelp import ShowHelp

_APP = QgsApplication.instance() or QgsApplication([], False)
if QgsApplication.instance() is _APP:
    QgsApplication.initQgis()

LAYER_NAME = "progress_test_source"


def _source_layer(count: int) -> QgsVectorLayer:
    layer = QgsVectorLayer("Point?crs=EPSG:3301&field=name:string", LAYER_NAME, "memory")
    features = []
    for index in range(count):
        feature = QgsFeature(layer.fields())
        feature.setAttributes([f"f{index}"])
        feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(index, index)))
        features.append(feature)
    layer.dataProvider().addFeatures(features)
    return layer


class EngineProgressReportsTest(unittest.TestCase):
    def setUp(self):
        self.engine = LayerCreationEngine()
        self.reports = []

    def tearDown(self):
        project = QgsProject.instance()
        for layer in project.mapLayersByName(f"{LAYER_NAME}_memory"):
            project.removeMapLayer(layer.id())
        group = project.layerTreeRoot().findGroup(MailablGroupFolders.MAILABL_MAIN)
        if group is not None:
            project.layerTreeRoot().removeChildNode(group)

    def _import(self, source, **kwargs):
        return self.engine.import_shapefile_to_memory_layer(
            shp_layer=source,
            layer_name=LAYER_NAME,
            group_name=MailablGroupFolders.NEW_PROPERTIES,
            **kwargs,
        )

    def test_reports_copying_then_finalizing_then_complete(self):
        layer = self._import(_source_layer(5), on_progress=self.reports.append, batch_size=2,
                             progress_update_interval=2)

        self.assertIsNotNone(layer)
        self.assertEqual(layer.featureCount(), 5)
        self.assertEqual(
            [(r.stage, r.done, r.total, r.copied) for r in self.reports],
            [
                (ShapefileImportProgress.COPYING, 1, 5, 0),
                (ShapefileImportProgress.COPYING, 3, 5, 2),
                (ShapefileImportProgress.COPYING, 5, 5, 4),
                (ShapefileImportProgress.FINALIZING, 5, 5, 5),
                (ShapefileImportProgress.COMPLETE, 5, 5, 5),
            ],
        )

    def test_works_without_a_callback(self):
        layer = self._import(_source_layer(3))

        self.assertIsNotNone(layer)
        self.assertEqual(layer.featureCount(), 3)

    def test_an_empty_source_sends_no_reports(self):
        layer = self._import(_source_layer(0), on_progress=self.reports.append)

        self.assertIsNotNone(layer)
        self.assertEqual(self.reports, [])

    def test_a_failing_callback_fails_the_import(self):
        def fail(_report):
            raise RuntimeError("window gone")

        with patch("Kavitro_dev.engines.LayerCreationEngine.PythonFailLogger") as logger:
            layer = self._import(_source_layer(2), on_progress=fail)

        self.assertIsNone(layer)
        self.assertEqual(logger.log_exception.call_args.kwargs["event"], "layer_import_failed")


class _Lang:
    def translate(self, key):
        if key == TranslationKeys.LAYER_IMPORT_PROGRESS:
            return f"<{key}>" + " {done}/{total} {percent}%"
        if key in (TranslationKeys.LAYER_IMPORT_COPIED, TranslationKeys.LAYER_IMPORT_IMPORTED):
            return f"<{key}>" + " {count}"
        return f"<{key}>"


class ImportProgressWindowTest(unittest.TestCase):
    def setUp(self):
        dialog_patch = patch.object(flow_module, "ProgressDialogModern")
        events_patch = patch.object(flow_module, "QCoreApplication")
        self.dialog_class = dialog_patch.start()
        self.events = events_patch.start()
        self.addCleanup(dialog_patch.stop)
        self.addCleanup(events_patch.stop)
        self.parent = object()
        self.window = _ImportProgressWindow(self.parent, _Lang())

    def test_no_report_means_no_window(self):
        self.window.close()

        self.dialog_class.assert_not_called()

    def test_first_report_opens_one_window_with_the_total(self):
        self.window(ShapefileImportProgress(ShapefileImportProgress.COPYING, 1, 4, 0))
        self.window(ShapefileImportProgress(ShapefileImportProgress.COPYING, 3, 4, 2))

        self.dialog_class.assert_called_once_with(title=f"<{TranslationKeys.LAYER_IMPORT_TITLE}>", maximum=4, parent=self.parent)
        self.dialog_class.return_value.show.assert_called_once_with()

    def test_each_stage_shows_its_texts(self):
        dialog = self.dialog_class.return_value
        self.window(ShapefileImportProgress(ShapefileImportProgress.COPYING, 1, 4, 0))
        self.window(ShapefileImportProgress(ShapefileImportProgress.FINALIZING, 4, 4, 4))
        self.window(ShapefileImportProgress(ShapefileImportProgress.COMPLETE, 4, 4, 4))

        calls = [c.kwargs for c in dialog.update.call_args_list]
        copied = f"<{TranslationKeys.LAYER_IMPORT_COPIED}>"
        self.assertEqual(
            calls,
            [
                {"value": 1, "text1": f"<{TranslationKeys.LAYER_IMPORT_PROGRESS}> 1/4 25%", "text2": f"{copied} 0"},
                {"value": 4, "text1": f"<{TranslationKeys.LAYER_IMPORT_FINAL_TOUCHES}>", "text2": f"{copied} 4"},
                {
                    "value": 4,
                    "text1": f"<{TranslationKeys.LAYER_IMPORT_COMPLETE}>",
                    "text2": f"<{TranslationKeys.LAYER_IMPORT_IMPORTED}> 4",
                },
            ],
        )
        # Events are processed while copying and finalizing, not after the final report.
        self.assertEqual(self.events.processEvents.call_count, 2)

    def test_close_closes_the_window_once(self):
        self.window(ShapefileImportProgress(ShapefileImportProgress.COPYING, 1, 2, 0))
        self.window.close()
        self.window.close()

        self.dialog_class.return_value.close.assert_called_once_with()


class LoaderClosesProgressWindowTest(unittest.TestCase):
    def _loader(self, import_side_effect):
        loader = SHPLayerLoader.__new__(SHPLayerLoader)
        loader.parent = None
        loader.target_group = MailablGroupFolders.NEW_PROPERTIES
        loader.lang_manager = _Lang()
        loader.engine = Mock()
        loader.engine.import_shapefile_to_memory_layer.side_effect = import_side_effect
        loader._get_shp_file_path = Mock(return_value="C:/data/source.shp")
        loader._choose_bootstrap_path = Mock(return_value=(False, ""))
        loader._resolve_import_result = Mock(return_value=None)
        return loader

    @staticmethod
    def _report_then(result):
        def run(**kwargs):
            kwargs["on_progress"](ShapefileImportProgress(ShapefileImportProgress.COPYING, 1, 2, 0))
            if isinstance(result, Exception):
                raise result
            return result
        return run

    def _patches(self):
        source = Mock()
        source.isValid.return_value = True
        return (
            patch.object(flow_module, "QgsVectorLayer", return_value=source),
            patch.object(flow_module, "ProgressDialogModern"),
            patch.object(flow_module, "QCoreApplication"),
            patch.object(flow_module, "PythonFailLogger"),
        )

    def test_window_is_closed_after_a_failed_import(self):
        p1, p2, p3, p4 = self._patches()
        with p1, p2 as dialog_class, p3, p4:
            result = self._loader(self._report_then(None)).load_shp_layer()

        self.assertEqual(result.status, SHPLoadStatus.FAILED)
        dialog_class.return_value.close.assert_called_once_with()

    def test_window_is_closed_when_the_engine_raises(self):
        p1, p2, p3, p4 = self._patches()
        with p1, p2 as dialog_class, p3, p4:
            with self.assertRaises(RuntimeError):
                self._loader(self._report_then(RuntimeError("boom"))).load_shp_layer()

        dialog_class.return_value.close.assert_called_once_with()

    def test_engine_gets_the_progress_window_not_a_parent_widget(self):
        p1, p2, p3, p4 = self._patches()
        with p1, p2, p3, p4:
            loader = self._loader(self._report_then(None))
            loader.load_shp_layer()

        kwargs = loader.engine.import_shapefile_to_memory_layer.call_args.kwargs
        self.assertNotIn("parent_widget", kwargs)
        self.assertIsInstance(kwargs["on_progress"], _ImportProgressWindow)


class ShowHelpTest(unittest.TestCase):
    def _opened(self, module_name):
        with patch.object(show_help_module.loadWebpage, "open_webpage") as open_webpage:
            ShowHelp.show_help_for_module(module_name)
        open_webpage.assert_called_once()
        return open_webpage.call_args.args[0]

    def test_module_with_its_own_page(self):
        self.assertEqual(self._opened(Module.PROPERTY.value), HELP_URLS[Module.PROPERTY.value])

    def test_home_opens_the_plugin_collection(self):
        self.assertEqual(
            self._opened(Module.HOME.value),
            "https://help.kavitro.com/et/collections/10606065-kavitro-qgis-plugin",
        )

    def test_unknown_module_opens_the_default_page(self):
        self.assertEqual(self._opened("NO_SUCH_MODULE"), HELP_URLS.get("NO_SUCH_MODULE", DEFAULT_HELP_URL))

    def test_no_active_module_opens_the_default_page(self):
        self.assertEqual(self._opened(None), DEFAULT_HELP_URL)
        self.assertEqual(self._opened(""), DEFAULT_HELP_URL)

    def test_help_does_not_look_up_the_module_itself(self):
        self.assertFalse(hasattr(show_help_module, "ModuleManager"))


if __name__ == "__main__":
    unittest.main()
