"""Import-direction rules between the plugin's layers, frozen at their current violations.

Rules (a "->" means "must not import"):
  constants/                     -> any other plugin package (constants only).
  utils/, engines/, python/, feed/ (headless)
                                 -> UI: widgets/, ui/, dialog.py, login_dialog.py, main.py,
                                    module_manager.py (QWidget + ThemeManager), MISPLACED_UI files;
                                    and modules/ (module domain).
  languages/, Logs/ (bottom)     -> the same UI set and modules/.
  modules/<A>/                   -> modules/<B>/ internals (modules/task_shared/ is the shared base).
  widgets/                       -> modules/.

Imports are read with ast (module level and inside functions, TYPE_CHECKING included);
relative imports are resolved from the file path.

ALLOWED_VIOLATIONS lists every violation that existed when the test was written. A new
import outside the list fails the test; a listed import that is gone also fails until its
line is deleted, so the lists only shrink. When a file moves, rename its entries.
Run this file directly to print the current violations in list format.
"""
import ast
import os
import sys
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_PACKAGE = PLUGIN_ROOT.name
SKIP_DIRS = {"tests", "Temporary", "release_repo", "tools", "__pycache__", ".git", ".venv"}

HEADLESS_PACKAGES = ("utils", "engines", "python", "feed")
BOTTOM_PACKAGES = ("languages", "Logs")
UI_PACKAGES = ("widgets", "ui")
UI_ROOT_MODULES = ("dialog", "login_dialog", "main", "module_manager")
SHARED_MODULE_PACKAGES = ("task_shared",)

# UI components that still live under a headless folder. They count as UI (importing them
# from headless code is a violation) and are not checked as headless sources. Delete the
# path here when the file moves to ui/ and rename the matching ALLOWED_VIOLATIONS targets.
MISPLACED_UI = ()

ALLOWED_VIOLATIONS = {
    "constants_imports_only_constants": [
        "constants/settings_keys.py -> Logs.python_fail_logger",
    ],
    "headless_imports_no_ui_or_modules": [
        "engines/LayerCreationEngine.py -> widgets.ProgressDialogModern",
        "utils/MapTools/module_feature_controllers.py -> ui.window_state.dialog_helpers",
        "utils/MapTools/module_feature_controllers.py -> ui.messages_helper",
        "utils/MapTools/module_identify_tool.py -> dialog",
        "utils/MapTools/module_identify_tool.py -> module_manager",
        "utils/MapTools/module_identify_tool.py -> ui.window_state.dialog_helpers",
        "utils/MapTools/module_identify_tool.py -> ui.messages_helper",
        "utils/SHPLayerLoader.py -> ui.messages_helper",
        "utils/help/ShowHelp.py -> module_manager",
        "utils/moduleSwitchHelper.py -> module_manager",
        "utils/moduleSwitchHelper.py -> modules.Settings.settings_setup_guard",
        "utils/moduleSwitchHelper.py -> ui.messages_helper",
        "utils/property/PropertyDataLoader.py -> widgets.DateHelpers",
        "utils/search/searchHelpers.py -> ui.messages_helper",
    ],
    "bottom_layer_imports_no_ui_or_modules": [
    ],
    "module_imports_no_other_module": [
        "modules/Settings/EasementStatusMappingDialog.py -> modules.easements.easement_layer_service",
        "modules/Settings/cards/SettingsModuleCard.py -> modules.projects.project_board_status_rules",
        "modules/Settings/cards/SettingsModuleCard.py -> modules.projects.projects_temp_layer_helper",
        "modules/Settings/cards/SettingsModuleCard.py -> modules.works.works_temp_layer_helper",
        "modules/Settings/cards/SettingsPropertyManagement.py -> modules.Property.property_entry",
        "modules/Settings/settings_setup_guard.py -> modules.projects.project_board_status_rules",
        "modules/projects/project_board_overview_service.py -> modules.Property.query_coordinator",
        "modules/projects/projects_card_actions.py -> modules.Settings.settings_setup_guard",
    ],
    "widgets_import_no_modules": [
        "widgets/DataDisplayWidgets/ModuleConfig.py -> modules.projects.project_board_overview_service",
        "widgets/DataDisplayWidgets/ModuleConfig.py -> modules.projects.project_board_widgets",
        "widgets/DataDisplayWidgets/StatusWidget.py -> modules.works.works_sync_service",
        "widgets/Filters/NotStartedStatusFilterWidget.py -> modules.projects.project_board_status_rules",
        "widgets/works_list_widgets.py -> modules.works.works_list_service",
    ],
}


def _plugin_files(root):
    found = {}
    for directory, dirs, names in os.walk(root):
        dirs[:] = [name for name in dirs if name not in SKIP_DIRS]
        for name in names:
            if name.endswith(".py"):
                path = Path(directory) / name
                found[path.relative_to(root).as_posix()] = path
    return found


def _module_name(rel_path):
    parts = rel_path[:-3].split("/")
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _imported_modules(rel_path, source, known_modules):
    """Plugin-internal modules a file imports, as dotted names relative to the plugin root."""
    tree = ast.parse(source, rel_path)
    package = rel_path.split("/")[:-1]
    prefix = PLUGIN_PACKAGE + "."
    targets = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(prefix):
                    targets.add(alias.name[len(prefix):])
            continue
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.level == 0:
            if not node.module or not (node.module + ".").startswith(prefix):
                continue
            base = node.module.split(".")[1:]
        else:
            up = node.level - 1
            if up > len(package):
                continue
            base = package[: len(package) - up]
            if node.module:
                base = base + node.module.split(".")
        for alias in node.names:
            # `from pkg import submodule` targets the submodule, `from mod import Name` the module.
            candidate = ".".join(base + [alias.name])
            targets.add(candidate if candidate in known_modules else ".".join(base))
    return targets


def collect_edges(root=PLUGIN_ROOT):
    files = _plugin_files(root)
    known = {_module_name(rel) for rel in files}
    edges = set()
    for rel, path in files.items():
        source = path.read_text(encoding="utf-8-sig")
        for target in _imported_modules(rel, source, known):
            if target:
                edges.add((rel, target))
    return edges


def _top(name):
    return name.split(".")[0]


def _misplaced_ui_modules():
    return {_module_name(path) for path in MISPLACED_UI}


def _is_ui_or_modules(target):
    if target in _misplaced_ui_modules():
        return True
    top = _top(target)
    return top in UI_PACKAGES or top in UI_ROOT_MODULES or top == "modules"


def _module_owner(dotted):
    parts = dotted.split(".")
    return parts[1] if len(parts) > 1 and parts[0] == "modules" else None


def find_violations(edges):
    misplaced = set(MISPLACED_UI)
    rules = {name: set() for name in ALLOWED_VIOLATIONS}
    for source, target in edges:
        line = f"{source} -> {target}"
        source_top = source.split("/")[0]
        if source_top == "constants" and _top(target) != "constants":
            rules["constants_imports_only_constants"].add(line)
        if source_top in HEADLESS_PACKAGES and source not in misplaced and _is_ui_or_modules(target):
            rules["headless_imports_no_ui_or_modules"].add(line)
        if source_top in BOTTOM_PACKAGES and _is_ui_or_modules(target):
            rules["bottom_layer_imports_no_ui_or_modules"].add(line)
        if source_top == "modules":
            source_owner = _module_owner(_module_name(source))
            target_owner = _module_owner(target)
            if (
                source_owner
                and target_owner
                and source_owner != target_owner
                and target_owner not in SHARED_MODULE_PACKAGES
            ):
                rules["module_imports_no_other_module"].add(line)
        if source_top == "widgets" and _top(target) == "modules":
            rules["widgets_import_no_modules"].add(line)
    return rules


class ArchitectureLayersTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.violations = find_violations(collect_edges())

    def _check_rule(self, rule):
        current = self.violations[rule]
        allowed = set(ALLOWED_VIOLATIONS[rule])
        new = sorted(current - allowed)
        gone = sorted(allowed - current)
        messages = []
        if new:
            messages.append(
                f"New import breaks rule '{rule}' (fix the import, do not extend the list):\n  "
                + "\n  ".join(new)
            )
        if gone:
            messages.append(
                f"Violation is gone, remove it from ALLOWED_VIOLATIONS['{rule}'] so the count only shrinks:\n  "
                + "\n  ".join(gone)
            )
        if messages:
            self.fail("\n".join(messages))

    def test_allowed_lists_have_no_duplicates(self):
        for rule, lines in ALLOWED_VIOLATIONS.items():
            self.assertEqual(len(lines), len(set(lines)), f"duplicate entries in {rule}")

    def test_misplaced_ui_files_exist(self):
        missing = [path for path in MISPLACED_UI if not (PLUGIN_ROOT / path).is_file()]
        self.assertEqual(missing, [], "file moved or deleted: remove it from MISPLACED_UI")

    def test_constants_imports_only_constants(self):
        self._check_rule("constants_imports_only_constants")

    def test_headless_imports_no_ui_or_modules(self):
        self._check_rule("headless_imports_no_ui_or_modules")

    def test_bottom_layer_imports_no_ui_or_modules(self):
        self._check_rule("bottom_layer_imports_no_ui_or_modules")

    def test_module_imports_no_other_module(self):
        self._check_rule("module_imports_no_other_module")

    def test_widgets_import_no_modules(self):
        self._check_rule("widgets_import_no_modules")


if __name__ == "__main__":
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else PLUGIN_ROOT
    for rule, lines in find_violations(collect_edges(root)).items():
        print(f'    "{rule}": [  # {len(lines)}')
        for line in sorted(lines):
            print(f'        "{line}",')
        print("    ],")
