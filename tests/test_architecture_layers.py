"""Import-direction rules between the plugin's layers, frozen at their current violations.

Rules (a "->" means "must not import"):
  constants/                     -> any other plugin package (constants only).
  utils/, engines/, python/, feed/ (headless)
                                 -> UI: widgets/, ui/, dialog.py, login_dialog.py, main.py,
                                    module_manager.py (QWidget + ThemeManager), MISPLACED_UI files;
                                    and modules/ (module domain).
  languages/, Logs/ (bottom)     -> the same UI set and modules/.
  modules/<A>/                   -> modules/<B>/ internals. Allowed: modules/task_shared/ (the shared
                                    base) and modules/<B>/<name>_entry.py, B's public interface.
  widgets/                       -> modules/.

Imports are read with ast (module level and inside functions, TYPE_CHECKING included);
relative imports are resolved from the file path.

ALLOWED_VIOLATIONS listed every violation that existed when the test was written; since
v2.12.83 all lists are empty. A new import outside the list fails the test; a listed import
that is gone also fails until its line is deleted, so the lists only shrink. When a file moves, rename its entries.
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


def _is_public_entry(target: str) -> bool:
    """modules.<owner>.<name>_entry: the one file other modules may import from <owner>."""
    parts = target.split(".")
    return len(parts) == 3 and parts[0] == "modules" and parts[2].endswith("_entry")

# UI components that still live under a headless folder. They count as UI (importing them
# from headless code is a violation) and are not checked as headless sources. Delete the
# path here when the file moves to ui/ and rename the matching ALLOWED_VIOLATIONS targets.
MISPLACED_UI = ()

ALLOWED_VIOLATIONS = {
    "constants_imports_only_constants": [
    ],
    "headless_imports_no_ui_or_modules": [
    ],
    "bottom_layer_imports_no_ui_or_modules": [
    ],
    "module_imports_no_other_module": [
    ],
    "widgets_import_no_modules": [
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
                and not _is_public_entry(target)
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

    def test_only_entry_files_are_open_to_other_modules(self):
        edges = {
            ("modules/Settings/a.py", "modules.projects.projects_entry"),
            ("modules/Settings/a.py", "modules.projects.projects_temp_layer_helper"),
            ("modules/Settings/a.py", "modules.projects.sub.thing_entry"),
            ("modules/Settings/a.py", "modules.task_shared.base"),
            ("modules/Settings/a.py", "modules.Settings.other"),
            ("widgets/w.py", "modules.projects.projects_entry"),
        }
        found = find_violations(edges)

        self.assertEqual(sorted(found["module_imports_no_other_module"]), [
            "modules/Settings/a.py -> modules.projects.projects_temp_layer_helper",
            "modules/Settings/a.py -> modules.projects.sub.thing_entry",
        ])
        self.assertEqual(sorted(found["widgets_import_no_modules"]), ["widgets/w.py -> modules.projects.projects_entry"])


if __name__ == "__main__":
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else PLUGIN_ROOT
    for rule, lines in find_violations(collect_edges(root)).items():
        print(f'    "{rule}": [  # {len(lines)}')
        for line in sorted(lines):
            print(f'        "{line}",')
        print("    ],")
