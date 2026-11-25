"""Code-pattern rules that keep the plugin from growing the same shortcut twice.

Rules (read with ast over every plugin source file outside tests/):
  1. No optional language parameter (`lang_manager=None`, `language=None`, `lang=None`, ...) and no
     `x or LanguageManager()` fallback: `LanguageManager()` follows the one plugin-wide language, so
     a function that needs texts builds it, and one that gets it injected takes it as a required argument.
     The only optional language argument is LanguageManager(language=...) itself, which pins a language.
  2. The task sections (works, as-built, ...) are listed once, in constants/module_names.py. Code that
     needs "the Kavitro entity behind a module" calls backend_module(); it does not write its own
     `(Module.TASK, Module.WORKS, Module.ASBUILT)` list. A list of the sections that is about the map
     layer or the card (not the entity) is named in ALLOWED_SECTION_LISTS with its reason.
  3. Status reading and changing is per entity through StatusActions (get_item_status, update_item_status);
     no `get_easement_status` / `update_task_status` style function per module.

ALLOWED_SECTION_LISTS only shrinks: a listed place that is gone fails until its line is deleted.
"""
import ast
import os
import re
import sys
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT.parent))
SKIP_DIRS = {"tests", "Temporary", "release_repo", "tools", "__pycache__", ".git", ".venv"}

LANGUAGE_PARAMETER_NAMES = {"lang_manager", "lang_mgr", "lang", "language", "_lang", "translator"}
# LanguageManager(language=None) follows the plugin-wide language; a value pins one. That is the whole API.
ALLOWED_OPTIONAL_LANGUAGE_PARAMETERS = {("languages/language_manager.py", "LanguageManager.__init__", "language")}

SECTIONS_FILE = "constants/module_names.py"
# Lists of task sections that are about the map layer or the card, not the Kavitro entity.
ALLOWED_SECTION_LISTS = {
    "ui/map_tools/module_identify_tool.py": "the sections whose items live on a map layer",
    "utils/MapTools/module_item_focus_service.py": "the sections whose layer id field is ext_job_id, and the ones with a layer to focus",
    "widgets/DataDisplayWidgets/ModuleConnectionActions.py": "the sections whose card has no project-folder action",
}

PER_MODULE_STATUS_FUNCTION = re.compile(
    r"^(get|update|set|fetch)_(easement|task|project|contract|coordination|submission|specification|letter|works|asbuilt)_status$"
)


def plugin_sources():
    for dirpath, dirs, files in os.walk(PLUGIN_ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if name.endswith(".py"):
                path = Path(dirpath) / name
                yield path.relative_to(PLUGIN_ROOT).as_posix(), ast.parse(path.read_text(encoding="utf-8"))


def _function_defs(tree):
    """(qualified name, node) for every function and method."""
    def visit(node, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                yield from visit(child, prefix + child.name + ".")
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                yield prefix + child.name, child
                yield from visit(child, prefix + child.name + ".")
            else:
                yield from visit(child, prefix)
    yield from visit(tree, "")


def _is_module_value(node, member: str) -> bool:
    return (
        isinstance(node, ast.Attribute) and node.attr == "value"
        and isinstance(node.value, ast.Attribute) and node.value.attr == member
        and isinstance(node.value.value, ast.Name) and node.value.value.id == "Module"
    )


def _is_none(node) -> bool:
    return isinstance(node, ast.Constant) and node.value is None


def _makes_language_manager(node) -> bool:
    return (
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "LanguageManager"
        and not node.args and not node.keywords
    )


class LanguageParameterRuleTest(unittest.TestCase):
    def test_no_optional_language_parameter(self) -> None:
        found = []
        for rel, tree in plugin_sources():
            for qualified, node in _function_defs(tree):
                arguments = node.args
                positional = arguments.posonlyargs + arguments.args
                defaults = [None] * (len(positional) - len(arguments.defaults)) + list(arguments.defaults)
                pairs = list(zip(positional, defaults)) + list(zip(arguments.kwonlyargs, arguments.kw_defaults))
                for argument, default in pairs:
                    if argument.arg in LANGUAGE_PARAMETER_NAMES and default is not None and _is_none(default):
                        found.append((rel, qualified, argument.arg))
        self.assertEqual(sorted(set(found) - ALLOWED_OPTIONAL_LANGUAGE_PARAMETERS), [])

    def test_the_pinned_language_argument_still_exists(self) -> None:
        sources = dict(plugin_sources())
        names = {qualified for qualified, _node in _function_defs(sources["languages/language_manager.py"])}
        self.assertIn("LanguageManager.__init__", names)

    def test_no_fallback_to_a_new_language_manager(self) -> None:
        found = []
        for rel, tree in plugin_sources():
            for node in ast.walk(tree):
                if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or) and any(_makes_language_manager(v) for v in node.values):
                    found.append((rel, node.lineno))
                if isinstance(node, ast.IfExp) and _makes_language_manager(node.orelse):
                    found.append((rel, node.lineno))
        self.assertEqual(found, [])


class TaskSectionRuleTest(unittest.TestCase):
    @staticmethod
    def section_lists():
        found = {}
        for rel, tree in plugin_sources():
            for node in ast.walk(tree):
                if isinstance(node, (ast.Tuple, ast.Set, ast.List)):
                    members = {name for name in ("WORKS", "ASBUILT") if any(_is_module_value(e, name) for e in node.elts)}
                    if members == {"WORKS", "ASBUILT"}:
                        found.setdefault(rel, []).append(node.lineno)
        return found

    def test_the_sections_are_listed_in_one_place(self) -> None:
        found = set(self.section_lists())
        self.assertEqual(sorted(found - set(ALLOWED_SECTION_LISTS)), [], "use backend_module() / TASK_SECTION_VALUES")

    def test_allowed_section_lists_still_exist(self) -> None:
        found = set(self.section_lists())
        self.assertEqual(sorted(set(ALLOWED_SECTION_LISTS) - found), [], "delete the line from ALLOWED_SECTION_LISTS")

    def test_the_central_list_names_every_section_the_plugin_has(self) -> None:
        from Kavitro_dev.constants.module_names import TASK_SECTION_VALUES, Module, backend_module

        self.assertEqual(TASK_SECTION_VALUES, {Module.TASK.value, Module.WORKS.value, Module.ASBUILT.value})
        for section in TASK_SECTION_VALUES:
            self.assertEqual(backend_module(section), Module.TASK.value)
        self.assertEqual(backend_module("project"), "project")


class StatusFunctionRuleTest(unittest.TestCase):
    def test_no_status_function_per_module(self) -> None:
        found = [
            (rel, qualified)
            for rel, tree in plugin_sources()
            for qualified, _node in _function_defs(tree)
            if PER_MODULE_STATUS_FUNCTION.match(qualified.rsplit(".", 1)[-1])
        ]
        self.assertEqual(found, [], "read and change a status through StatusActions.get_item_status / update_item_status")


if __name__ == "__main__":
    sys.exit(unittest.main())
