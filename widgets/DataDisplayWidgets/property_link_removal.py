"""Removing property links from a record (user decision 2026-11-24).

Two ways in: the "Link properties" review marks linked properties for removal, and the card menu
"Remove linked properties" lists them without a map pick. Both ask a named confirmation (default No),
send one request and show success only after Kavitro no longer links them. Layers are not touched.
"""
from __future__ import annotations

from typing import Callable, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout

from ...constants.button_props import ButtonVariant
from ...constants.file_paths import QssPaths
from ...constants.module_names import Module
from ...languages.translation_keys import TranslationKeys
from ...Logs.python_fail_logger import PythonFailLogger
from ...python.api_actions import APIModuleActions
from ...ui.messages_helper import ModernMessageDialog
from ...ui.theme_manager import ThemeManager
from ...utils.api_error_handling import user_message
from ...utils.MapTools.item_selector_tools import PropertiesSelectors

MAX_NAMED = 10


def link_label(entry: dict) -> str:
    number, address = str(entry.get("number") or ""), str(entry.get("address") or "")
    return f"{address} — {number}" if address and number else number or address or str(entry.get("id") or "")


def confirm_link_removal(lang, module: str, item_label: str, entries: list[dict], parent=None) -> bool:
    """Name what goes; an easement also loses the area, price and payment date of each link."""
    names = [link_label(entry) for entry in entries]
    listed = "\n".join(f"• {name}" for name in names[:MAX_NAMED])
    if len(names) > MAX_NAMED:
        listed += "\n" + lang.translate(TranslationKeys.MORE_COUNT_SUFFIX).format(count=len(names) - MAX_NAMED)
    message = lang.translate(TranslationKeys.LINK_REMOVE_CONFIRM).format(
        count=len(entries), pid=item_label, list=listed)
    if APIModuleActions._property_owner_module(module) == Module.EASEMENT.value:
        message += "\n\n" + lang.translate(TranslationKeys.LINK_REMOVE_EASEMENT_WARNING)
    yes, no = lang.translate(TranslationKeys.YES), lang.translate(TranslationKeys.NO)
    choice = ModernMessageDialog.ask_choice_modern(
        lang.translate(TranslationKeys.CONFIRM), message, buttons=[yes, no], parent=parent, default=no, cancel=no,
    )
    return choice == yes


class PropertyUnlinkDialog(QDialog):
    """The record's linked properties with a box each; nothing is ticked at the start."""

    def __init__(self, entries: list[dict], lang, *, module: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("PropertyUnlinkDialog")
        self.setWindowTitle(lang.translate(TranslationKeys.LINK_REMOVE_TITLE))
        self.setModal(True)
        self._module = module
        ThemeManager.apply_module_style(self, [QssPaths.MAIN, QssPaths.BUTTONS])

        layout = QVBoxLayout(self)
        hint = QLabel(lang.translate(TranslationKeys.LINK_REMOVE_HINT), self)
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self._list = QListWidget(self)
        self._list.setMinimumWidth(320)
        for entry in sorted(entries, key=lambda e: link_label(e).lower()):
            item = QListWidgetItem(link_label(entry))
            item.setData(Qt.UserRole, dict(entry))
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self._list.addItem(item)
        layout.addWidget(self._list)

        buttons = QHBoxLayout()
        self._show_button = QPushButton(lang.translate(TranslationKeys.LINK_REMOVE_SHOW_ON_MAP), self)
        self._show_button.setProperty("variant", ButtonVariant.PRIMARY)
        self._show_button.clicked.connect(self._show_checked_on_map)
        buttons.addWidget(self._show_button)
        buttons.addStretch(1)
        cancel = QPushButton(lang.translate(TranslationKeys.CANCEL_BUTTON), self)
        cancel.setProperty("variant", ButtonVariant.GHOST)
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)
        self._remove_button = QPushButton(lang.translate(TranslationKeys.LINK_REMOVE_SELECTED), self)
        self._remove_button.setProperty("variant", ButtonVariant.WARNING)
        self._remove_button.clicked.connect(self.accept)
        buttons.addWidget(self._remove_button)
        layout.addLayout(buttons)

        self._list.itemChanged.connect(self._update_buttons)
        self._update_buttons()

    def checked_entries(self) -> list[dict]:
        return [
            self._list.item(row).data(Qt.UserRole)
            for row in range(self._list.count())
            if self._list.item(row).checkState() == Qt.Checked
        ]

    def _update_buttons(self, *_args) -> None:
        any_checked = bool(self.checked_entries())
        self._remove_button.setEnabled(any_checked)
        self._show_button.setEnabled(any_checked)

    def _show_checked_on_map(self) -> None:
        numbers = [entry["number"] for entry in self.checked_entries() if entry.get("number")]
        if numbers:
            PropertiesSelectors.show_connected_properties_on_map(numbers, module=self._module)


def unlink_properties_from_card(
    *,
    module: str,
    item_id: str,
    item_label: str,
    lang,
    parent=None,
    on_linked_changed: Optional[Callable[[list[str]], None]] = None,
) -> bool:
    """The card menu flow; True when links were removed and confirmed."""
    try:
        entries = APIModuleActions.get_linked_properties(module, item_id)
    except Exception as exc:  # menu action: nothing may escape; nothing was changed
        PythonFailLogger.log_exception(exc, module=module or "general", event="property_unlink_load_failed",
                                       extra={"item_id": item_id})
        ModernMessageDialog.show_warning(
            lang.translate(TranslationKeys.ERROR),
            lang.translate(TranslationKeys.LINK_REMOVE_LOAD_FAILED).format(error=user_message(exc)))
        return False
    if not entries:
        ModernMessageDialog.show_info(lang.translate(TranslationKeys.INFO), lang.translate(TranslationKeys.LINK_REMOVE_NONE))
        return False

    dialog = PropertyUnlinkDialog(entries, lang, module=module, parent=parent)
    if dialog.exec_() != QDialog.Accepted:
        return False
    chosen = dialog.checked_entries()
    if not chosen or not confirm_link_removal(lang, module, item_label, chosen, parent=parent):
        return False
    return remove_links(module=module, item_id=item_id, chosen=chosen, lang=lang, on_linked_changed=on_linked_changed)


def remove_links(*, module: str, item_id: str, chosen: list[dict], lang,
                 on_linked_changed: Optional[Callable[[list[str]], None]] = None) -> bool:
    """Send the removal, check it took and tell the card; the user hears the outcome either way."""
    try:
        linked = APIModuleActions.remove_property_links(module, item_id, [entry["id"] for entry in chosen])
    except Exception as exc:  # menu action: nothing may escape
        PythonFailLogger.log_exception(exc, module=module or "general", event="property_unlink_failed",
                                       extra={"item_id": item_id, "count": len(chosen)})
        ModernMessageDialog.show_warning(
            lang.translate(TranslationKeys.ERROR),
            lang.translate(TranslationKeys.LINK_REMOVE_FAILED).format(error=user_message(exc)))
        return False
    PythonFailLogger.log("property_unlink_done", module=module or "general",
                         extra={"item_id": item_id, "removed": len(chosen), "left": len(linked)})
    numbers = [entry["number"] for entry in linked if entry.get("number")]
    ModernMessageDialog.show_info(
        lang.translate(TranslationKeys.SUCCESS),
        lang.translate(TranslationKeys.LINK_REMOVE_DONE).format(count=len(chosen), total=len(linked)))
    if callable(on_linked_changed):
        try:
            on_linked_changed(numbers)
        except Exception as exc:  # the removal stands; only the card refresh failed
            PythonFailLogger.log_exception(exc, module=module or "general", event="property_unlink_callback_failed")
    return True
