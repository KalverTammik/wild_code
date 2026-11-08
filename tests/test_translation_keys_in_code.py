"""User-facing text goes through translation keys only.

Every key the code names must exist, or translate() raises KeyError in the user's hands. A key can be named
as a literal (``translate("Reset failed")``) or as an attribute of a key class (``TranslationKeys.X``, also
through an alias such as ``K.X``). The source is read with ast, so strings nested in f-strings count too; a
text search missed those once and a used key was deleted.

translate() has no fallback text (REFACTOR_RULES: keys are resolved strictly), and literal text handed
straight to a widget or dialog is not translated, so both are refused outside a short reasoned list.
"""
from __future__ import annotations

import ast
import os
import re
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT.parent))

from Kavitro_dev.languages import en, et, translation_keys

KEY_CLASSES = {
    name: cls for name, cls in vars(translation_keys).items()
    if isinstance(cls, type) and cls.__module__ == translation_keys.__name__
}
TRANSLATE_CALLS = {"translate", "translate_static"}
SKIPPED_PARTS = {"tests", "tools", ".venv", "Temporary", "release_repo", "docs", "__pycache__"}

# Calls whose first argument is shown to the user as text.
TEXT_SINK_CALLS = {
    "setText", "setToolTip", "setWindowTitle", "setPlaceholderText", "setStatusTip", "setTitle", "setWhatsThis",
    "showMessage", "set_status_text", "setAccessibleName", "setLabelText", "setHeaderLabels", "setTabText", "addTab",
    "setDefaultText", "set_title", "setSuffix", "setPrefix", "addItem", "insertItem", "setItemText",
    "setHorizontalHeaderLabels", "setVerticalHeaderLabels", "add_text_area", "setSpecialValueText", "setFormat",
    "addSection", "addMenu", "setButtonText",
    "QLabel", "QPushButton", "QAction", "QCheckBox", "QRadioButton", "QGroupBox", "QToolButton", "QMenu",
    "QListWidgetItem", "QTreeWidgetItem", "QTableWidgetItem", "QStandardItem",
}
# Calls whose first two arguments are a dialog title and message.
DIALOG_CALLS = {"show_warning", "show_info", "show_error", "ask_yes_no", "ask_choice_modern", "Info_messages_modern",
                "Warning_messages_modern", "Error_messages_modern"}
TEXT_KEYWORDS = {"text", "text1", "text2", "title", "message", "label", "tooltip", "placeholder", "heading"}
LOG_CALLS = {"log", "log_exception", "debug", "info", "warn", "warning", "error", "print", "exception"}
WORD = re.compile(r"[A-Za-zÄÖÜÕäöüõŠšŽž]{2,}")
# Text that stays as it is, with the reason; (file, the literal's text parts).
ALLOWED_UI_TEXT = {
    ("modules/asbuilt/asbuilt_geometry_form_dialog.py", "L-EST97"): "coordinate system name",
    ("modules/asbuilt/asbuilt_geometry_form_dialog.py", "EH2000"): "height system name",
    ("widgets/DataDisplayWidgets/TaskFilePreviewDialog.py", "<b></b><br> •  • "): "markup around file values",
    ("widgets/FooterWidget.py", "QGIS  | Plugin v"): "product names and version numbers",
}


def plugin_sources():
    for path in sorted(PLUGIN_ROOT.rglob("*.py")):
        rel = path.relative_to(PLUGIN_ROOT)
        if rel.parts[0] in SKIPPED_PARTS or rel.parts[0] == "languages":
            continue
        yield rel, ast.parse(path.read_text(encoding="utf-8"))


def literal_text(node):
    """The visible text of a str constant or f-string, or None."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(v.value for v in node.values if isinstance(v, ast.Constant) and isinstance(v.value, str))
    return None


def call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return node.func.id if isinstance(node.func, ast.Name) else ""


def is_translate_call(node) -> bool:
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in TRANSLATE_CALLS


def key_class_aliases(module: ast.Module) -> dict:
    aliases = {}
    for node in ast.walk(module):
        if isinstance(node, ast.ImportFrom) and (node.module or "").endswith("translation_keys"):
            for alias in node.names:
                if alias.name in KEY_CLASSES:
                    aliases[alias.asname or alias.name] = alias.name
    return aliases


class TranslationKeysInCodeTest(unittest.TestCase):
    maxDiff = None

    def test_literal_keys_exist_in_both_languages(self) -> None:
        missing = []
        for rel, module in plugin_sources():
            for node in ast.walk(module):
                if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
                    continue
                if node.func.attr not in TRANSLATE_CALLS or not node.args:
                    continue
                key = node.args[0]
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    for name, table in (("et", et.TRANSLATIONS), ("en", en.TRANSLATIONS)):
                        if key.value not in table:
                            missing.append(f"{rel}:{node.lineno} {key.value!r} missing in {name}")
        self.assertEqual(missing, [])

    def test_key_class_attributes_exist(self) -> None:
        missing = []
        for rel, module in plugin_sources():
            aliases = key_class_aliases(module)
            for node in ast.walk(module):
                if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in aliases:
                    cls = KEY_CLASSES[aliases[node.value.id]]
                    if not hasattr(cls, node.attr):
                        missing.append(f"{rel}:{node.lineno} {cls.__name__}.{node.attr}")
        self.assertEqual(missing, [])

    def test_translate_has_no_fallback_text(self) -> None:
        found = []
        for rel, module in plugin_sources():
            for node in ast.walk(module):
                if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or) and is_translate_call(node.values[0]):
                    if any(literal_text(value) is not None for value in node.values[1:]):
                        found.append(f"{rel}:{node.lineno} translate(...) or '...'")
                elif is_translate_call(node):
                    fallback = node.args[1] if len(node.args) > 1 else next(
                        (k.value for k in node.keywords if k.arg == "fallback"), None)
                    if fallback is not None and literal_text(fallback) is not None:
                        found.append(f"{rel}:{node.lineno} translate(key, '...')")
                elif isinstance(node, ast.IfExp) and any(is_translate_call(b) for b in (node.body, node.orelse)):
                    if any(WORD.search(literal_text(b) or "") for b in (node.body, node.orelse)):
                        found.append(f"{rel}:{node.lineno} '...' if ... else translate(...)")
        self.assertEqual(found, [])

    def test_no_literal_text_reaches_the_user(self) -> None:
        found = []
        for rel, module in plugin_sources():
            for node in ast.walk(module):
                if not isinstance(node, ast.Call):
                    continue
                name = call_name(node)
                if name in LOG_CALLS and name not in DIALOG_CALLS:
                    continue
                candidates = []
                if name in TEXT_SINK_CALLS:
                    candidates += node.args[:1]
                if name in DIALOG_CALLS:
                    candidates += node.args[:2]
                if name == "add_fields":
                    candidates += [arg.elts[0] for arg in node.args if isinstance(arg, ast.Tuple) and arg.elts]
                candidates += [k.value for k in node.keywords if k.arg in TEXT_KEYWORDS]
                for arg in candidates:
                    text = literal_text(arg)
                    if text and WORD.search(text) and (rel.as_posix(), text) not in ALLOWED_UI_TEXT:
                        found.append(f"{rel}:{node.lineno} {text[:60]!r}")
        self.assertEqual(found, [])

    def test_each_key_is_defined_once(self) -> None:
        """A second definition replaces the first without a word, so one of the two texts is never shown."""
        found = []
        keys = ast.parse((PLUGIN_ROOT / "languages" / "translation_keys.py").read_text(encoding="utf-8"))
        for node in keys.body:
            if isinstance(node, ast.ClassDef):
                names = [t.id for s in node.body if isinstance(s, ast.Assign) for t in s.targets
                         if isinstance(t, ast.Name)]
                found += [f"{node.name}.{name}" for name in sorted(set(names)) if names.count(name) > 1]
        # Two attributes with the same value are one entry in the tables, whatever their names.
        for language in ("et", "en"):
            source = ast.parse((PLUGIN_ROOT / "languages" / f"{language}.py").read_text(encoding="utf-8"))
            aliases = key_class_aliases(source)
            for table in (node for node in ast.walk(source) if isinstance(node, ast.Dict)):
                seen = {}
                for key in table.keys:
                    if isinstance(key, ast.Attribute) and isinstance(key.value, ast.Name) and key.value.id in aliases:
                        value = getattr(KEY_CLASSES[aliases[key.value.id]], key.attr)
                    elif isinstance(key, ast.Constant):
                        value = key.value
                    else:
                        continue
                    if value in seen:
                        found.append(f"{language}.py:{key.lineno} {ast.unparse(key)} repeats {seen[value]}")
                    seen.setdefault(value, ast.unparse(key))
        self.assertEqual(found, [])

    def test_the_scan_sees_the_code(self) -> None:
        """Guards the scan itself: a path change must not make the two tests above vacuous."""
        sources = list(plugin_sources())
        self.assertGreater(len(sources), 150)
        self.assertTrue(any(key_class_aliases(module) for _rel, module in sources))


if __name__ == "__main__":
    unittest.main()
