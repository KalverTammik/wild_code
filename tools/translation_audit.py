from __future__ import annotations

import argparse
import ast
import json
import os
import re
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Set, Tuple


UI_TEXT_METHODS = {
    "setText",
    "setWindowTitle",
    "setToolTip",
    "setPlaceholderText",
    "setStatusTip",
    "setWhatsThis",
    "setTitle",
    "setLabelText",
    "setInformativeText",
    "setTextFormat",
}


@dataclass(frozen=True)
class LiteralUsage:
    file: str
    line: int
    kind: str
    text: str
    context: str

    def signature(self) -> Tuple[str, str, str]:
        return (self.file, self.kind, self.text)


@dataclass
class TranslationAudit:
    defined_keys: Set[str]
    en_keys: Set[str]
    et_keys: Set[str]
    used_keys: Set[str]
    translate_unknown: List[LiteralUsage]
    translate_literal: List[LiteralUsage]
    ui_literals: List[LiteralUsage]
    syntax_errors: List[str]

    @property
    def missing_in_en(self) -> List[str]:
        return sorted(self.defined_keys - self.en_keys)

    @property
    def missing_in_et(self) -> List[str]:
        return sorted(self.defined_keys - self.et_keys)

    @property
    def unused_keys(self) -> List[str]:
        return sorted(self.defined_keys - self.used_keys)


class KeyCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.class_keys: Dict[str, Dict[str, str]] = {}

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        class_map: Dict[str, str] = {}
        for stmt in node.body:
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                target = stmt.targets[0]
                if isinstance(target, ast.Name) and isinstance(stmt.value, ast.Constant):
                    if isinstance(stmt.value.value, str):
                        class_map[target.id] = stmt.value.value
        if class_map:
            self.class_keys[node.name] = class_map
        self.generic_visit(node)


class TranslationDictCollector(ast.NodeVisitor):
    def __init__(self, key_classes: Dict[str, Dict[str, str]]) -> None:
        self.key_classes = key_classes
        self.keys: Set[str] = set()

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "TRANSLATIONS":
                if isinstance(node.value, ast.Dict):
                    for key_node in node.value.keys:
                        resolved = resolve_key_node(key_node, self.key_classes)
                        if resolved:
                            self.keys.add(resolved)
        self.generic_visit(node)


class UsageCollector(ast.NodeVisitor):
    def __init__(self, key_classes: Dict[str, Dict[str, str]], file_path: str) -> None:
        self.key_classes = key_classes
        self.file_path = file_path
        self.used_keys: Set[str] = set()
        self.translate_unknown: List[LiteralUsage] = []
        self.translate_literal: List[LiteralUsage] = []
        self.ui_literals: List[LiteralUsage] = []

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if isinstance(node.value, ast.Name):
            class_name = node.value.id
            if class_name in self.key_classes:
                if node.attr in self.key_classes[class_name]:
                    self.used_keys.add(self.key_classes[class_name][node.attr])
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr in {"translate", "translate_static"}:
            self._handle_translate_call(node, func.attr)
        if isinstance(func, ast.Attribute) and func.attr in UI_TEXT_METHODS:
            self._handle_ui_literal(node, func.attr)
        self.generic_visit(node)

    def _handle_translate_call(self, node: ast.Call, method: str) -> None:
        if not node.args:
            return
        arg = node.args[0]
        resolved = resolve_key_node(arg, self.key_classes)
        if resolved:
            self.used_keys.add(resolved)
            return
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            self.translate_literal.append(
                LiteralUsage(
                    file=self.file_path,
                    line=node.lineno,
                    kind="translate_literal",
                    text=arg.value,
                    context=method,
                )
            )
        else:
            self.translate_unknown.append(
                LiteralUsage(
                    file=self.file_path,
                    line=node.lineno,
                    kind="translate_unknown",
                    text=ast.dump(arg, include_attributes=False),
                    context=method,
                )
            )

    def _handle_ui_literal(self, node: ast.Call, method: str) -> None:
        if not node.args:
            return
        arg = node.args[0]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            self.ui_literals.append(
                LiteralUsage(
                    file=self.file_path,
                    line=node.lineno,
                    kind="ui_literal",
                    text=arg.value,
                    context=method,
                )
            )


def resolve_key_node(node: Optional[ast.AST], key_classes: Dict[str, Dict[str, str]]) -> Optional[str]:
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
        class_name = node.value.id
        attr = node.attr
        class_map = key_classes.get(class_name)
        if class_map and attr in class_map:
            return class_map[attr]
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def parse_translation_keys(path: str) -> Dict[str, Dict[str, str]]:
    with open(path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=path)
    collector = KeyCollector()
    collector.visit(tree)
    return collector.class_keys


def parse_translation_dict(path: str, key_classes: Dict[str, Dict[str, str]]) -> Set[str]:
    with open(path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=path)
    collector = TranslationDictCollector(key_classes)
    collector.visit(tree)
    return collector.keys


def iter_python_files(root: str) -> Iterable[str]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {"__pycache__", ".venv", "venv", ".git"}]
        for filename in filenames:
            if filename.endswith(".py"):
                yield os.path.join(dirpath, filename)


def collect_usage(root: str, key_classes: Dict[str, Dict[str, str]]) -> TranslationAudit:
    defined_keys = set()
    for class_map in key_classes.values():
        defined_keys.update(class_map.values())

    en_keys = parse_translation_dict(os.path.join(root, "languages", "en.py"), key_classes)
    et_keys = parse_translation_dict(os.path.join(root, "languages", "et.py"), key_classes)

    used_keys: Set[str] = set()
    translate_unknown: List[LiteralUsage] = []
    translate_literal: List[LiteralUsage] = []
    ui_literals: List[LiteralUsage] = []
    syntax_errors: List[str] = []

    excluded = {
        os.path.join(root, "languages", "translation_keys.py"),
        os.path.join(root, "languages", "en.py"),
        os.path.join(root, "languages", "et.py"),
    }

    for file_path in iter_python_files(root):
        if file_path in excluded:
            continue
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source, filename=file_path)
        except SyntaxError as exc:
            syntax_errors.append(f"{file_path}: {exc}")
            continue

        collector = UsageCollector(key_classes, file_path)
        collector.visit(tree)
        used_keys.update(collector.used_keys)
        translate_unknown.extend(collector.translate_unknown)
        translate_literal.extend(collector.translate_literal)
        ui_literals.extend(collector.ui_literals)

    return TranslationAudit(
        defined_keys=defined_keys,
        en_keys=en_keys,
        et_keys=et_keys,
        used_keys=used_keys,
        translate_unknown=translate_unknown,
        translate_literal=translate_literal,
        ui_literals=ui_literals,
        syntax_errors=syntax_errors,
    )


def format_report(audit: TranslationAudit) -> str:
    lines: List[str] = []
    lines.append("=== Translation Audit Report ===")
    lines.append(f"Defined keys: {len(audit.defined_keys)}")
    lines.append(f"EN keys: {len(audit.en_keys)}")
    lines.append(f"ET keys: {len(audit.et_keys)}")
    lines.append(f"Used keys: {len(audit.used_keys)}")

    lines.append("")
    lines.append("-- Missing in EN --")
    lines.extend(audit.missing_in_en or ["(none)"])

    lines.append("")
    lines.append("-- Missing in ET --")
    lines.extend(audit.missing_in_et or ["(none)"])

    lines.append("")
    lines.append("-- Unused keys (safe cleanup list) --")
    lines.extend(audit.unused_keys or ["(none)"])

    lines.append("")
    lines.append("-- Translate calls with literal strings --")
    if audit.translate_literal:
        for item in audit.translate_literal:
            lines.append(f"{item.file}:{item.line} [{item.context}] {item.text}")
    else:
        lines.append("(none)")

    lines.append("")
    lines.append("-- Translate calls with unknown expressions --")
    if audit.translate_unknown:
        for item in audit.translate_unknown:
            lines.append(f"{item.file}:{item.line} [{item.context}] {item.text}")
    else:
        lines.append("(none)")

    lines.append("")
    lines.append("-- UI literals (should become keys) --")
    if audit.ui_literals:
        for item in audit.ui_literals:
            lines.append(f"{item.file}:{item.line} [{item.context}] {item.text}")
    else:
        lines.append("(none)")

    if audit.syntax_errors:
        lines.append("")
        lines.append("-- Syntax errors while scanning --")
        lines.extend(audit.syntax_errors)

    return "\n".join(lines)


def write_json_report(path: str, audit: TranslationAudit) -> None:
    def serialize_usage(items: List[LiteralUsage]) -> List[dict]:
        return [
            {
                "file": item.file,
                "line": item.line,
                "kind": item.kind,
                "text": item.text,
                "context": item.context,
            }
            for item in items
        ]

    payload = {
        "defined_keys": sorted(audit.defined_keys),
        "en_keys": sorted(audit.en_keys),
        "et_keys": sorted(audit.et_keys),
        "used_keys": sorted(audit.used_keys),
        "missing_in_en": audit.missing_in_en,
        "missing_in_et": audit.missing_in_et,
        "unused_keys": audit.unused_keys,
        "translate_literal": serialize_usage(audit.translate_literal),
        "translate_unknown": serialize_usage(audit.translate_unknown),
        "ui_literals": serialize_usage(audit.ui_literals),
        "syntax_errors": audit.syntax_errors,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def next_audit_txt_path(root: str) -> str:
    tools_dir = os.path.join(root, "tools")
    os.makedirs(tools_dir, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    pattern = re.compile(rf"^translation_audit_{date_str}_(\d{{3}})\.txt$")
    serials: List[int] = []
    for name in os.listdir(tools_dir):
        match = pattern.match(name)
        if match:
            try:
                serials.append(int(match.group(1)))
            except ValueError:
                continue
    next_serial = (max(serials) + 1) if serials else 1
    filename = f"translation_audit_{date_str}_{next_serial:03d}.txt"
    return os.path.join(tools_dir, filename)


def write_txt_report(root: str, report_text: str) -> str:
    path = next_audit_txt_path(root)
    with open(path, "w", encoding="utf-8") as f:
        f.write(report_text)
        f.write("\n")
    return path


def read_baseline(path: str) -> Set[Tuple[str, str, str]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    signatures: Set[Tuple[str, str, str]] = set()
    for item in data.get("literal_signatures", []):
        if isinstance(item, list) and len(item) == 3:
            signatures.add((item[0], item[1], item[2]))
    return signatures


def write_baseline(path: str, audit: TranslationAudit) -> None:
    signatures = {item.signature() for item in audit.translate_literal + audit.ui_literals}
    payload = {"literal_signatures": sorted(list(signatures))}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit translation keys and usage.")
    parser.add_argument(
        "--root",
        default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        help="Project root directory",
    )
    parser.add_argument("--json", dest="json_path", help="Write JSON report to path")
    parser.add_argument("--baseline", help="Baseline JSON file for literal checks")
    parser.add_argument(
        "--write-baseline",
        dest="write_baseline",
        help="Write baseline JSON file from current literals",
    )
    args = parser.parse_args()

    translation_keys_path = os.path.join(args.root, "languages", "translation_keys.py")
    key_classes = parse_translation_keys(translation_keys_path)

    audit = collect_usage(args.root, key_classes)
    report_text = format_report(audit)
    print(report_text)
    txt_path = write_txt_report(args.root, report_text)
    print(f"\nSaved text report: {txt_path}")

    if args.json_path:
        write_json_report(args.json_path, audit)

    if args.write_baseline:
        write_baseline(args.write_baseline, audit)

    if args.baseline:
        baseline_signatures = read_baseline(args.baseline)
        current_signatures = {item.signature() for item in audit.translate_literal + audit.ui_literals}
        new_literals = sorted(current_signatures - baseline_signatures)
        if new_literals:
            print("\nNew literal UI strings found (not in baseline):")
            for file_path, kind, text in new_literals:
                print(f"{file_path} [{kind}] {text}")
            return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
