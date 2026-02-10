from __future__ import annotations

import os
from typing import List, Optional, Tuple

from PyQt5.QtWidgets import QComboBox, QDialog, QLineEdit
from ...languages.translation_keys import FolderNamingTranslationKeys, TranslationKeys
from PyQt5.uic import loadUi
from ...utils.messagesHelper import ModernMessageDialog

INTERNAL_PROJECT_NAME = "PROJECT_NAME"
INTERNAL_PROJECT_NUMBER = "PROJECT_NUMBER"
INTERNAL_SYMBOL = "SYMBOL"

# use FolderNamingTranslationKeys from languages.translation_keys.py

class FolderNamingRuleDialog(QDialog):
    """Three-slot rule builder dialog for project folder names."""

    SAMPLE_PROJECT_NUMBER = "(24)AR-3-1"
    SAMPLE_PROJECT_NAME = "Minu lemmik projekt"

    def __init__(self, lang_manager=None, parent=None, initial_rule: str = ""):
        super().__init__(parent)
        self.lang_manager = lang_manager
        self._result_rule: str = initial_rule or ""

        ui_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "FolderNamingRuleDialog.ui"))
        widget = loadUi(ui_path, self)
        comboSlot1 = widget.comboSlot1
        comboSlot2 = widget.comboSlot2
        comboSlot3 = widget.comboSlot3
        
        symbolText1 = widget.symbolText1
        symbolText2 = widget.symbolText2
        symbolText3 = widget.symbolText3


        self.setWindowTitle(self.lang_manager.translate(TranslationKeys.FOLDER_NAMING_RULE_DIALOG_TITLE))

        self.slot_rows: List[Tuple[QComboBox, QLineEdit]] = [
            (comboSlot1, symbolText1),
            (comboSlot2, symbolText2),
            (comboSlot3, symbolText3),
        ]

        for idx, (combo, symbol_input) in enumerate(self.slot_rows):
            if combo is None:
                print(f"[WARN] comboSlot{idx + 1} missing")
            else:
                print(f"[DEBUG] Combo is present; populating")
                combo.clear()
                # Use literal labels to avoid translation side-effects hiding items
                combo.addItem(self.lang_manager.translate(FolderNamingTranslationKeys.TR_EMPTY), None)
                combo.addItem(self.lang_manager.translate(FolderNamingTranslationKeys.TR_PROJECT_NUMBER), INTERNAL_PROJECT_NUMBER)
                combo.addItem(self.lang_manager.translate(FolderNamingTranslationKeys.TR_PROJECT_NAME), INTERNAL_PROJECT_NAME)
                combo.addItem(self.lang_manager.translate(FolderNamingTranslationKeys.TR_SYMBOL), INTERNAL_SYMBOL)
                combo.setCurrentIndex(0)
                combo.currentIndexChanged.connect(lambda _, i=idx: self._on_slot_changed(i))
            if symbol_input is None:
                print(f"[WARN] symbolText{idx + 1} missing")
            else:
                symbol_input.setPlaceholderText(self.lang_manager.translate(FolderNamingTranslationKeys.TR_SYMBOL_TEXT))
                symbol_input.setVisible(False)
                symbol_input.setEnabled(False)
                symbol_input.textChanged.connect(lambda _: self._update_preview())

        self.preview_label = widget.previewLabel

        from PyQt5.QtWidgets import QDialogButtonBox
        buttons = widget.buttonBox
        if buttons:
            buttons.accepted.connect(self._on_accept)
            buttons.rejected.connect(self.reject)

        self._apply_rule(initial_rule)
        self._update_preview()

    # --- Helpers ---------------------------------------------------------


    def _on_slot_changed(self, index: int) -> None:
        combo, symbol_input = self.slot_rows[index]
        if not combo or not symbol_input:
            return
        is_symbol = combo.currentData() == INTERNAL_SYMBOL
        symbol_input.setVisible(is_symbol)
        symbol_input.setEnabled(is_symbol)
        self._update_preview()

    def _apply_rule(self, rule: str) -> None:
        parts = self._parse_rule(rule)
        for idx, (combo, symbol_input) in enumerate(self.slot_rows):
            if not combo or not symbol_input:
                continue
            selected_key, symbol_text = parts[idx]
            if selected_key is None:
                combo.setCurrentIndex(0)
                symbol_input.clear()
            else:
                combo_index = combo.findData(selected_key)
                combo.setCurrentIndex(combo_index if combo_index >= 0 else 0)
                if symbol_text:
                    symbol_input.setText(symbol_text)
                else:
                    symbol_input.clear()
                is_symbol = selected_key == INTERNAL_SYMBOL
                symbol_input.setVisible(is_symbol)
                symbol_input.setEnabled(is_symbol)

    def _parse_rule(self, rule: str) -> List[Tuple[Optional[str], str]]:
        slots: List[Tuple[Optional[str], str]] = [(None, ""), (None, ""), (None, "")]
        if not rule:
            return slots

        components = [c.strip() for c in str(rule).split(" + ") if c.strip()]
        for idx in range(min(3, len(components))):
            comp = components[idx]
            if comp == INTERNAL_PROJECT_NUMBER:
                slots[idx] = (INTERNAL_PROJECT_NUMBER, "")
            elif comp == INTERNAL_PROJECT_NAME:
                slots[idx] = (INTERNAL_PROJECT_NAME, "")
            elif comp.startswith(f"{INTERNAL_SYMBOL}(") and comp.endswith(")"):
                text = comp[len(INTERNAL_SYMBOL) + 1 : -1]
                slots[idx] = (INTERNAL_SYMBOL, text)
        return slots

    def _serialize_rule(self) -> str:
        pieces: List[str] = []
        for combo, symbol_input in self.slot_rows:
            if not combo or not symbol_input:
                continue
            key = combo.currentData()
            if key is None:
                continue
            if key == INTERNAL_SYMBOL:
                text = (symbol_input.text() or "").strip()
                if not text:
                    continue
                pieces.append(f"{INTERNAL_SYMBOL}({text})")
            elif key in {INTERNAL_PROJECT_NAME, INTERNAL_PROJECT_NUMBER}:
                pieces.append(key)
        return " + ".join(pieces)

    def _update_preview(self) -> None:
        samples = {
            INTERNAL_PROJECT_NUMBER: self.SAMPLE_PROJECT_NUMBER,
            INTERNAL_PROJECT_NAME: self.SAMPLE_PROJECT_NAME,
        }
        preview_parts: List[str] = []
        for combo, symbol_input in self.slot_rows:
            if not combo:
                continue
            key = combo.currentData()
            if key is None:
                continue
            if key == INTERNAL_SYMBOL:
                if not symbol_input:
                    continue
                text = (symbol_input.text() or "").strip()
                if text:
                    preview_parts.append(text)
            else:
                preview_parts.append(samples.get(key, ""))
        preview = "".join(preview_parts) if preview_parts else self.lang_manager.translate(FolderNamingTranslationKeys.TR_PREVIEW_EMPTY)
        if self.preview_label:
            self.preview_label.setText(self.lang_manager.translate(FolderNamingTranslationKeys.TR_PREVIEW_PREFIX) + preview)

    def _validate(self) -> Optional[str]:
        any_slot = False
        for combo, symbol_input in self.slot_rows:
            if not combo:
                continue
            key = combo.currentData()
            if key is None:
                continue
            if key == INTERNAL_SYMBOL and symbol_input and not (symbol_input.text() or "").strip():
                return self.lang_manager.translate(FolderNamingTranslationKeys.TR_SYMBOL_REQUIRED)
            any_slot = True
        if not any_slot:
            return self.lang_manager.translate(FolderNamingTranslationKeys.TR_SELECT_AT_LEAST_ONE)
        return None

    def _on_accept(self) -> None:
        error = self._validate()
        if error:
            ModernMessageDialog.show_warning(
                self.lang_manager.translate(FolderNamingTranslationKeys.TR_INVALID_RULE),
                error,
            )
            return
        self._result_rule = self._serialize_rule()
        self.accept()

    def get_rule(self) -> str:
        return self._result_rule or ""


def parse_rule_to_slots(rule: str) -> List[Tuple[Optional[str], str]]:
    return FolderNamingRuleDialog(None)._parse_rule(rule)
