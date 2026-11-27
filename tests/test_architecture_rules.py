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
  4. Text the user reads comes from the translation tables: no literal sentence passed to a widget text call
     or a message dialog, none returned as the message of an `(ok, message)` result, and every
     LayerEditTexts text is a TranslationKeys member. Layer field names and values of the user's own map
     schema, file names, CSS and log text are not user text and are not checked.
  5. Qt is imported through qgis.PyQt (also sip and uic), never from PyQt5 / PyQt6 or a bare `import sip`:
     only that path works in both QGIS 3 and QGIS 4. Tests and tools follow it too.
  6. No Qt5-only form that Qt6 refuses at run time: `exec_()`, `globalPos()` outside utils/qt_events.py,
     `Qt.convertFromPlainText`, and a Qt enum member without its enum (`Qt.AlignLeft`).
     No Qt class defines `__new__`: a `__new__` singleton crashes PyQt 6.11 (stack overflow).

ALLOWED_SECTION_LISTS only shrinks: a listed place that is gone fails until its line is deleted.
"""
import ast
import functools
import importlib
import os
import re
import sys
import unittest
from pathlib import Path

from qgis.PyQt.QtCore import QT_VERSION

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

# Widget calls whose text argument the user reads.
USER_TEXT_CALLS = {
    "setText", "setToolTip", "setWindowTitle", "setPlaceholderText", "setTitle", "setStatusTip", "setLabelText",
    "addItem", "addItems", "show_warning", "show_info", "show_error", "Info_messages_modern", "pushMessage",
    "QLabel", "QPushButton", "QCheckBox", "QGroupBox", "QAction", "QRadioButton", "setHeaderLabels",
}
# A literal in a user text call that is not a sentence to translate: brand text and the like.
ALLOWED_USER_TEXT_LITERALS = {"widgets/FooterWidget.py": {"| Plugin v"}}

PER_MODULE_STATUS_FUNCTION = re.compile(
    r"^(get|update|set|fetch)_(easement|task|project|contract|coordination|submission|specification|letter|works|asbuilt)_status$"
)


@functools.lru_cache(maxsize=1)
def _parsed_sources():
    sources = []
    for dirpath, dirs, files in os.walk(PLUGIN_ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if name.endswith(".py"):
                path = Path(dirpath) / name
                sources.append((path.relative_to(PLUGIN_ROOT).as_posix(), ast.parse(path.read_text(encoding="utf-8"))))
    return tuple(sources)


def plugin_sources():
    return iter(_parsed_sources())


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


def _call_name(node: ast.Call) -> str:
    func = node.func
    return func.attr if isinstance(func, ast.Attribute) else func.id if isinstance(func, ast.Name) else ""


def _is_sentence(text: str) -> bool:
    """Words a user would read: not a key, a file name, a CSS rule, a path or a bare symbol."""
    stripped = text.strip()
    if re.fullmatch(r"[A-Za-z0-9_\-./:#%{}@|<>=+*&·→ ▾]*", stripped) and " " not in stripped.replace(" · ", "|"):
        return False
    if re.search(r"[{};]|\.png|\.svg|\.qml|\.graphql", stripped):
        return False
    return len(re.findall(r"[A-Za-zÕÄÖÜõäöüšž]{2,}", stripped)) >= 2


class UserTextRuleTest(unittest.TestCase):
    def test_no_literal_sentence_in_a_user_text_call(self) -> None:
        found = []
        for rel, tree in plugin_sources():
            if rel.startswith("languages/"):
                continue
            for node in ast.walk(tree):
                if not (isinstance(node, ast.Call) and _call_name(node) in USER_TEXT_CALLS):
                    continue
                for argument in list(node.args) + [keyword.value for keyword in node.keywords]:
                    for part in ast.walk(argument):
                        if isinstance(part, ast.Constant) and isinstance(part.value, str) and _is_sentence(part.value):
                            if part.value not in ALLOWED_USER_TEXT_LITERALS.get(rel, set()):
                                found.append((rel, part.lineno, part.value[:60]))
        self.assertEqual(found, [], "put the text in languages/ and translate it")

    def test_no_literal_sentence_as_the_message_of_a_result(self) -> None:
        found = []
        for rel, tree in plugin_sources():
            for node in ast.walk(tree):
                if not (isinstance(node, ast.Return) and isinstance(node.value, ast.Tuple) and len(node.value.elts) == 2):
                    continue
                first, second = node.value.elts
                if isinstance(first, ast.Constant) and first.value in (False, None) and isinstance(second, ast.Constant)                         and isinstance(second.value, str) and _is_sentence(second.value):
                    found.append((rel, node.lineno, second.value[:60]))
        self.assertEqual(found, [], "return a translated text, not a literal")

    def test_layer_edit_texts_are_translation_keys(self) -> None:
        found = []
        for rel, tree in plugin_sources():
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and _call_name(node) == "LayerEditTexts":
                    for keyword in node.keywords:
                        if keyword.arg in ("start_failed", "change_failed", "commit_failed"):
                            is_key = isinstance(keyword.value, ast.Attribute) and isinstance(keyword.value.value, ast.Name)                                 and keyword.value.value.id == "TranslationKeys"
                            if not is_key and not (isinstance(keyword.value, ast.IfExp)):
                                found.append((rel, node.lineno, keyword.arg))
        self.assertEqual(found, [])


def _direct_qt_imports(tree):
    """(line, module) for every import that names a Qt binding instead of qgis.PyQt."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and not node.level:
            names = [node.module or ""]
        else:
            continue
        for name in names:
            if name.split(".")[0] in ("PyQt5", "PyQt6", "sip"):
                yield node.lineno, name


class QtImportRuleTest(unittest.TestCase):
    def test_qt_is_imported_through_qgis(self) -> None:
        found = []
        for dirpath, dirs, files in os.walk(PLUGIN_ROOT):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS - {"tests", "tools"}]
            for name in files:
                if name.endswith(".py"):
                    path = Path(dirpath) / name
                    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
                    rel = path.relative_to(PLUGIN_ROOT).as_posix()
                    found.extend((rel, line, module) for line, module in _direct_qt_imports(tree))
        self.assertEqual(found, [], "import from qgis.PyQt")

    def test_the_rule_sees_every_form_of_the_import(self) -> None:
        tree = ast.parse("import sip\nfrom PyQt5 import uic\nimport PyQt6.QtCore\nfrom qgis.PyQt import sip\n")
        self.assertEqual([line for line, _module in _direct_qt_imports(tree)], [1, 2, 3])


QT5_ONLY_ATTRIBUTES = {"exec_", "globalPos", "convertFromPlainText"}
GLOBAL_POS_OWNER = "utils/qt_events.py"


def _qt_classes(tree):
    """name -> class for what the file imports from qgis.PyQt."""
    classes = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("qgis.PyQt"):
            try:
                module = importlib.import_module(node.module)
            except ImportError:
                continue
            for alias in node.names:
                value = getattr(module, alias.name, None)
                if isinstance(value, type):
                    classes[alias.asname or alias.name] = value
    return classes


def _unscoped_enum_members(tree):
    """(line, text) for `Class.Member` where the member belongs to an enum nested in the class."""
    classes = _qt_classes(tree)
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in classes):
            continue
        owner = classes[node.value.id]
        # QGIS keeps QVariant.<Type> in both versions; moving to QMetaType is a separate step.
        if node.value.id == "QVariant":
            continue
        value = getattr(owner, node.attr, None)
        kind = type(value)
        if value is None or isinstance(value, type) or kind is owner:
            continue
        if getattr(owner, kind.__name__, None) is kind:
            yield node.lineno, f"{node.value.id}.{node.attr}"


class Qt6RuleTest(unittest.TestCase):
    def test_no_qt5_only_attribute(self) -> None:
        found = [
            (rel, node.lineno, node.attr)
            for rel, tree in plugin_sources()
            for node in ast.walk(tree)
            if isinstance(node, ast.Attribute) and node.attr in QT5_ONLY_ATTRIBUTES
            and not (node.attr == "globalPos" and rel == GLOBAL_POS_OWNER)
        ]
        self.assertEqual(found, [])

    def test_no_qt_class_defines_new(self) -> None:
        found = [
            (rel, node.name)
            for rel, tree in plugin_sources()
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef)
            and any(isinstance(base, ast.Name) and base.id in _qt_classes(tree) for base in node.bases)
            and any(isinstance(item, ast.FunctionDef) and item.name == "__new__" for item in node.body)
        ]
        self.assertEqual(found, [])

    def test_every_qt_enum_member_names_its_enum(self) -> None:
        found = [(rel, line, text) for rel, tree in plugin_sources() for line, text in _unscoped_enum_members(tree)]
        self.assertEqual(found, [], "write Qt.AlignmentFlag.AlignLeft, not Qt.AlignLeft")

    def test_the_enum_rule_sees_an_unscoped_member(self) -> None:
        tree = ast.parse(
            "from qgis.PyQt.QtCore import Qt, QEvent\n"
            "a = Qt.AlignmentFlag.AlignLeft\n"
            "b = QEvent.Type.Enter\n"
            "c = Qt.AlignLeft\n"
            "d = QEvent.Enter\n"
        )
        # PyQt6 has no unscoped members at all, so there the rule has nothing to see.
        expected = [] if QT_VERSION >= 0x060000 else [4, 5]
        self.assertEqual(sorted(line for line, _text in _unscoped_enum_members(tree)), expected)


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
