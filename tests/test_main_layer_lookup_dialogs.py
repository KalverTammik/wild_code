"""Main-layer lookups show a warning only through the dialogs their caller hands in.

`resolve_main_layer`, `prepare_layer_for_draw` and `ActiveLayersHelper.resolve_main_property_layer` used to take
`silent`. They now take a required `dialogs` argument: `ModernMessageDialog` where the user should be told,
`None` where the lookup must stay quiet. Callers that are mocked in other tests do not check keywords, so the
static test below pins which call sites warn and which do not.
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

from qgis.core import QgsApplication

from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.modules.asbuilt.asbuilt_layer_service import AsBuiltLayerService
from Kavitro_dev.modules.works.works_layer_service import WorksLayerService
from Kavitro_dev.utils.MapTools.MapHelpers import ActiveLayersHelper, MapHelpers
from Kavitro_dev.ui.messages_helper import ModernMessageDialog

MAP_HELPERS = sys.modules[ActiveLayersHelper.__module__]
LOOKUP_CALLS = {"resolve_main_layer", "prepare_layer_for_draw", "resolve_main_property_layer"}
# The same methods plus the hook the works service overrides; each must take `dialogs` and not `silent`.
LOOKUP_DEFINITIONS = LOOKUP_CALLS | {"_main_layer_is_ready"}
SKIPPED_TOP_LEVEL = {"tests", "tools", ".venv", "Temporary", "release_repo", "docs", ".git"}
SERVICE_FILES = (
    "utils/layers/module_layer_service_base.py",
    "modules/works/works_layer_service.py",
    "utils/MapTools/MapHelpers.py",
)

# (calls that pass ModernMessageDialog, calls that pass None) per file. A new call site must be added here on
# purpose, so nobody makes a lookup noisy or quiet by accident.
EXPECTED_CALL_SITES = {
    "modules/Property/FlowControllers/add_batch_runner.py": (0, 2),
    "modules/Property/widgets/property_ui.py": (1, 0),
    "modules/Property/widgets/property_ui_tools.py": (1, 0),
    "modules/easements/easement_status_mapping_dialog.py": (0, 2),
    "modules/Settings/cards/SettingsPropertyManagement.py": (2, 3),
    "modules/asbuilt/asbuilt_feature_map_controller.py": (2, 0),
    "modules/asbuilt/asbuilt_layer_service.py": (0, 1),
    "modules/easements/easement_attach_existing_controller.py": (1, 0),
    "modules/easements/preview_dialog/final_save_mixin.py": (0, 1),
    "modules/easements/preview_dialog/property_editor_mixin.py": (1, 0),
    "modules/projects/project_preview_dialog.py": (2, 1),
    "modules/projects/projects_feature_map_controller.py": (2, 0),
    "modules/works/works_card_actions.py": (1, 0),
    "modules/works/works_create_controller.py": (2, 2),
    "modules/works/works_pending_gis_review.py": (1, 0),
    "modules/works/works_layer_service.py": (0, 1),
    "modules/works/works_reposition_controller.py": (1, 0),
    "modules/works/works_sync_service.py": (0, 2),
    "modules/Property/FlowControllers/property_shp_import_flow.py": (0, 1),
    "modules/Property/dialogs/add_property/add_run_mixin.py": (0, 1),
    "modules/Property/dialogs/add_property/attention_checks_mixin.py": (1, 0),
    "widgets/DataDisplayWidgets/module_action_buttons.py": (1, 0),
}


def plugin_sources():
    """(relative posix path, parsed tree) of every plugin module, without tests, tools and virtualenvs."""
    for folder, dirs, files in os.walk(PLUGIN_ROOT):
        relative_folder = Path(folder).relative_to(PLUGIN_ROOT)
        dirs[:] = sorted(
            d for d in dirs
            if d != "__pycache__" and not (relative_folder == Path(".") and d in SKIPPED_TOP_LEVEL)
        )
        for name in sorted(files):
            if name.endswith(".py"):
                path = Path(folder) / name
                yield path.relative_to(PLUGIN_ROOT).as_posix(), ast.parse(path.read_text(encoding="utf-8"))


def called_name(node: ast.Call) -> str:
    return node.func.attr if isinstance(node.func, ast.Attribute) else ""


def names_modern_message_dialog(node: ast.expr) -> bool:
    if isinstance(node, ast.Name):
        return node.id == "ModernMessageDialog"
    return isinstance(node, ast.Attribute) and node.attr == "ModernMessageDialog"


class QgsAppCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)


class ActiveLayersHelperDialogsTest(QgsAppCase):
    def setUp(self) -> None:
        self.settings = patch.object(MAP_HELPERS, "SettingsService").start()
        self.addCleanup(patch.stopall)
        # The real dialog is stubbed, so a call that ignores `dialogs` can never open a window.
        self.real_dialog = patch.object(ModernMessageDialog, "show_warning").start()

    def resolve(self, found, **options):
        with patch.object(MapHelpers, "resolve_layer", return_value=found):
            return ActiveLayersHelper.resolve_main_property_layer(**options)

    def test_missing_layer_warns_through_the_given_dialogs(self) -> None:
        dialogs = Mock()
        self.assertIsNone(self.resolve(None, dialogs=dialogs))
        dialogs.show_warning.assert_called_once_with(
            LanguageManager().translate(TranslationKeys.ERROR),
            LanguageManager().translate(TranslationKeys.PROPERTY_MAIN_LAYER_MISSING),
        )
        self.real_dialog.assert_not_called()

    def test_missing_layer_without_dialogs_stays_quiet(self) -> None:
        self.assertIsNone(self.resolve(None, dialogs=None))
        self.real_dialog.assert_not_called()

    def test_found_layer_is_returned_without_a_dialog(self) -> None:
        layer = Mock()
        dialogs = Mock()
        self.assertIs(self.resolve(layer, dialogs=dialogs), layer)
        dialogs.show_warning.assert_not_called()
        self.real_dialog.assert_not_called()

    def test_the_layer_is_looked_up_by_the_property_module_setting(self) -> None:
        self.settings.return_value.module_main_layer_name.return_value = "layer-7"
        with patch.object(MapHelpers, "resolve_layer", return_value=None) as lookup:
            ActiveLayersHelper.resolve_main_property_layer(dialogs=None)
        lookup.assert_called_once_with("layer-7")


class DialogsAreRequiredTest(QgsAppCase):
    """A caller that forgets the argument fails loudly instead of silently showing nothing."""

    def test_lookups_cannot_be_called_without_saying_who_shows_the_warning(self) -> None:
        for call in (
            lambda: ActiveLayersHelper.resolve_main_property_layer(),
            lambda: AsBuiltLayerService.resolve_main_layer(),
            lambda: AsBuiltLayerService.prepare_layer_for_draw(),
            lambda: WorksLayerService.resolve_main_layer(),
        ):
            with self.subTest(call=call), self.assertRaises(TypeError):
                call()


class LookupCallSitesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = dict(plugin_sources())

    def classify(self, tree: ast.AST) -> dict[str, int]:
        """Counts the lookup calls of a module by what they pass as `dialogs`."""
        counts = {"dialogs": 0, "none": 0, "forwarded": 0, "missing": 0, "silent": 0, "other": 0}
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or called_name(node) not in LOOKUP_DEFINITIONS:
                continue
            keywords = {keyword.arg: keyword.value for keyword in node.keywords}
            if "silent" in keywords:
                counts["silent"] += 1
            value = keywords.get("dialogs")
            if value is None:
                counts["missing"] += 1
            elif names_modern_message_dialog(value):
                counts["dialogs"] += 1
            elif isinstance(value, ast.Constant) and value.value is None:
                counts["none"] += 1
            elif isinstance(value, ast.Name) and value.id == "dialogs":
                counts["forwarded"] += 1
            else:
                counts["other"] += 1
        return counts

    def test_no_call_passes_silent_or_leaves_dialogs_out(self) -> None:
        for rel, tree in self.sources.items():
            counts = self.classify(tree)
            with self.subTest(file=rel):
                self.assertEqual((counts["silent"], counts["missing"], counts["other"]), (0, 0, 0), counts)

    def test_each_file_warns_and_stays_quiet_where_it_did_before(self) -> None:
        found = {}
        for rel, tree in self.sources.items():
            counts = self.classify(tree)
            if counts["dialogs"] or counts["none"]:
                found[rel] = (counts["dialogs"], counts["none"])
        self.assertEqual(found, EXPECTED_CALL_SITES)

    def test_only_the_shared_base_forwards_its_own_dialogs(self) -> None:
        for rel, tree in self.sources.items():
            forwarded = self.classify(tree)["forwarded"]
            with self.subTest(file=rel):
                self.assertEqual(forwarded, 2 if rel == SERVICE_FILES[0] else 0)

    def test_lookup_methods_take_a_required_dialogs_and_no_silent(self) -> None:
        defined = []
        for rel in SERVICE_FILES:
            for node in ast.walk(self.sources[rel]):
                if not isinstance(node, ast.FunctionDef) or node.name not in LOOKUP_DEFINITIONS:
                    continue
                defined.append((rel, node.name))
                names = [argument.arg for argument in node.args.kwonlyargs]
                with self.subTest(file=rel, function=node.name):
                    self.assertNotIn("silent", [a.arg for a in node.args.args + node.args.kwonlyargs])
                    self.assertIn("dialogs", names)
                    # kw_defaults holds None for a keyword-only argument that has no default.
                    self.assertIsNone(node.args.kw_defaults[names.index("dialogs")])
        self.assertEqual(
            sorted(defined),
            sorted([
                (SERVICE_FILES[0], "resolve_main_layer"),
                (SERVICE_FILES[0], "_main_layer_is_ready"),
                (SERVICE_FILES[0], "prepare_layer_for_draw"),
                (SERVICE_FILES[1], "_main_layer_is_ready"),
                (SERVICE_FILES[2], "resolve_main_property_layer"),
            ]),
        )

    def test_services_import_no_dialog_module(self) -> None:
        for rel in SERVICE_FILES:
            imported = []
            for node in ast.walk(self.sources[rel]):
                if isinstance(node, ast.ImportFrom):
                    imported += [node.module or ""] + [alias.name for alias in node.names]
                elif isinstance(node, ast.Import):
                    imported += [alias.name for alias in node.names]
            with self.subTest(file=rel):
                self.assertFalse([name for name in imported if name.endswith("messages_helper")], imported)
                self.assertNotIn("ModernMessageDialog", imported)
                names = {node.id for node in ast.walk(self.sources[rel]) if isinstance(node, ast.Name)}
                self.assertNotIn("ModernMessageDialog", names)


if __name__ == "__main__":
    unittest.main()
