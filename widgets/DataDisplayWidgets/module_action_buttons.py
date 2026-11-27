from typing import Optional, Iterable

from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtWidgets import QAction, QMenu, QPushButton, QDialog
from ...widgets.DataDisplayWidgets.LinkReviewDialog import PropertyLinkReviewDialog

from qgis.PyQt import sip
from qgis.utils import iface


from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import ToolbarTranslationKeys
from ...utils.url_manager import OpenLink, loadWebpage
from ...python.api_actions import APIModuleActions
from ...utils.MapTools.item_selector_tools import PropertiesSelectors
from ...ui.theme_manager import ThemeManager
from ...utils.Folders.foldersHelpers import FolderHelpers
from ...constants.module_icons import IconNames
from ...constants.button_props import ButtonVariant
from ...ui.messages_helper import ModernMessageDialog
from ...languages.translation_keys import TranslationKeys
from ...utils.MapTools.module_item_focus_service import ModuleItemFocusService
from ...utils.MapTools.MapSelectionOrchestrator import MapSelectionOrchestrator
from ...constants.cadastral_fields import Katastriyksus
from ...utils.MapTools.MapHelpers import ActiveLayersHelper, MapHelpers
from ...Logs.python_fail_logger import PythonFailLogger
from ...utils.api_error_handling import user_message
from ...ui.window_state.dialog_helpers import DialogHelpers
from ...constants.file_paths import QssPaths
from ...module_manager import ModuleManager
from .MainStatusWidget import MainStatusWidget
from .property_link_removal import confirm_link_removal, unlink_properties_from_card
from ...python.responses import DataDisplayExtractors



def open_item_in_browser(module_name: Optional[str], item_id: Optional[str]) -> bool:
    """Open the record in Kavitro; a missing address or a failed open is shown, not only logged."""
    if not module_name or not item_id:
        return False
    lang = LanguageManager()
    url = ""
    try:
        base = OpenLink().weblink_by_module(module_name)
        if base:
            base = base.rstrip("/")
            if not base.endswith("s"):
                base = f"{base}s"
            url = f"{base}/{item_id}"
            if loadWebpage.open_webpage(url):
                return True
    except Exception as exc:  # button callback: nothing may escape
        PythonFailLogger.log_exception(
            exc,
            module=module_name or "general",
            event="module_action_open_browser_failed",
        )
    message = (lang.translate(TranslationKeys.WEB_PAGE_OPEN_FAILED).format(url=url) if url
               else lang.translate(TranslationKeys.WEB_LINK_MISSING))
    ModernMessageDialog.show_warning(lang.translate(TranslationKeys.WARNING), message)
    return False


def show_items_on_map(module_name: Optional[str], item_id: Optional[str]) -> None:
    if not module_name or not item_id:
        return

    numbers = APIModuleActions.get_module_item_connected_properties(module_name, item_id)
    found: set[str] = set()
    if numbers:
        layer = PropertiesSelectors.show_connected_properties_on_map(numbers, module=module_name)
        found = _selected_cadastral_numbers(layer)
    ModuleItemFocusService.focus_item_on_map(module_name, item_id)
    # The button shows properties only for a record that has links, so an empty list is a failed read.
    _warn_about_missing_properties(numbers, found)


def _selected_cadastral_numbers(layer) -> set[str]:
    if layer is None:
        return set()
    try:
        return {str(feature[Katastriyksus.tunnus] or "").strip() for feature in layer.selectedFeatures()}
    except (KeyError, RuntimeError):  # no cadastral field, or the layer was deleted
        return set()


def _warn_about_missing_properties(numbers: list, found: set) -> None:
    missing = [str(number) for number in numbers or [] if str(number).strip() not in found]
    if numbers and not missing:
        return
    lang = LanguageManager()
    shown = ", ".join(missing[:5])
    if len(missing) > 5:
        shown += lang.translate(TranslationKeys.MORE_COUNT_SUFFIX).format(count=len(missing) - 5)
    if not numbers:
        message = lang.translate(TranslationKeys.MAP_SHOW_LOAD_FAILED)
    elif len(missing) == len(numbers):
        message = lang.translate(TranslationKeys.MAP_SHOW_NONE_FOUND).format(total=len(numbers), missing=shown)
    else:
        message = lang.translate(TranslationKeys.MAP_SHOW_SOME_MISSING).format(
            found=len(numbers) - len(missing), total=len(numbers), missing=shown)
    ModernMessageDialog.show_warning(lang.translate(TranslationKeys.WARNING), message)


class CardActionButton(QPushButton):
    def __init__(
        self,
        object_name: str,
        icon_name: Optional[str],
        tooltip_text: Optional[str],
        lang_manager,
    ) -> None:
        super().__init__("")
        self._icon_name = icon_name
        self.setObjectName(object_name)
        self.setAutoDefault(False)
        self.setDefault(False)
        self.setProperty("variant", ButtonVariant.ICON)
        self.setFixedSize(22, 20)
        self.setIconSize(QSize(14, 14))
        if icon_name:
            self.setIcon(ThemeManager.get_qicon(icon_name))
        if tooltip_text:
            self.setToolTip(tooltip_text)

    def retheme(self) -> None:
        if self._icon_name:
            self.setIcon(ThemeManager.get_qicon(self._icon_name))
        menu = self.menu()
        if menu is not None:
            ThemeManager.apply_module_style(menu, [QssPaths.POPUP])


class OpenFolderActionButton(CardActionButton):
    def __init__(self, file_path: Optional[str], lang_manager) -> None:
        tooltip = lang_manager.translate(ToolbarTranslationKeys.OPEN_FOLDER) if lang_manager else ""
        super().__init__(
            "OpenFolderButton",
            IconNames.ICON_FOLDERICON,
            tooltip,
            lang_manager,
        )
        self._lang = lang_manager
        self._file_path = ""
        self.clicked.connect(self._open_current_folder)
        self.set_file_path(file_path)

    def _open_current_folder(self, _checked: bool = False) -> None:
        if not self._file_path:
            return
        result = FolderHelpers.open_item_folder(self._file_path)
        keys = {
            FolderHelpers.FOLDER_BLOCKED: (TranslationKeys.WARNING, TranslationKeys.DESCRIPTION_LINK_BLOCKED),
            FolderHelpers.FOLDER_NOT_FOUND: (TranslationKeys.WARNING, TranslationKeys.DESCRIPTION_LINK_NOT_FOUND),
            FolderHelpers.FOLDER_OPEN_FAILED: (TranslationKeys.ERROR, TranslationKeys.DESCRIPTION_LINK_OPEN_FAILED),
        }
        if result in keys:
            lang = self._lang
            title_key, message_key = keys[result]
            ModernMessageDialog.show_warning(
                lang.translate(title_key), lang.translate(message_key).format(target=self._file_path))

    def set_file_path(self, file_path: Optional[str]) -> None:
        """Apply the current item path without recreating its card."""
        self._file_path = str(file_path or "").strip()
        self.setEnabled(bool(self._file_path))

    @property
    def file_path(self) -> str:
        return self._file_path


class OpenWebActionButton(CardActionButton):
    def __init__(self, module_name: Optional[str], item_id: Optional[str], lang_manager) -> None:
        tooltip = lang_manager.translate(ToolbarTranslationKeys.OPEN_ITEM_IN_BROWSER) if lang_manager else ""
        super().__init__(
            "OpenWebpageButton",
            IconNames.KAVITRO_ICON,
            tooltip,
            lang_manager,
        )
        enabled = bool(module_name and item_id)
        self.setEnabled(enabled)
        if enabled:
            self.clicked.connect(
                lambda _, module=module_name, mid=item_id: open_item_in_browser(module, mid)
            )


class MoreActionsButton(CardActionButton):
    """A card's "more" menu. The actions its module registers get the button as their host: they use
    `item_data`, `lang_manager`, `safe_parent_window`, `window`, `update_files_path` and `apply_item_status`.
    """

    def __init__(
        self,
        item_data=None,
        module=None,
        on_properties_linked=None,
        on_files_path_updated=None,
    ) -> None:
        lang_manager = LanguageManager()
        tooltip = lang_manager.translate(ToolbarTranslationKeys.MORE_ACTIONS)
        super().__init__(
            "MoreActionsButton",
            IconNames.ICON_ADD,
            tooltip,
            lang_manager,
        )
        item_payload = dict(item_data or {})
        module = getattr(module, "value", module)
        module = str(module or "").strip().lower()
        self.item_data = item_payload
        self.module = module  # Ensure module is passed correctly
        self._map_selection_orchestrator: Optional[MapSelectionOrchestrator] = None
        self._on_properties_linked = on_properties_linked
        self._on_files_path_updated = on_files_path_updated
        self.lang_manager = lang_manager
        self._parent_window: Optional[QDialog] = None
        self._restore_parent_on_close: bool = False

        # Resolve the top-level plugin window (never minimize QGIS main window)
        self._parent_window = self._resolve_parent_window()

        menu = QMenu(self)
        menu.setObjectName("CardActionsMenu")
        menu.setProperty("popupKind", "card-actions")

        actions_class = ModuleManager().getModuleCardActions(module)
        self._module_actions = actions_class(self) if actions_class is not None else None
        for label_key, run in self._module_actions.menu_actions() if self._module_actions is not None else ():
            action = QAction(lang_manager.translate(label_key), self)
            action.triggered.connect(lambda _checked=False, run_action=run: run_action())
            menu.addAction(action)

        action2 = QAction(
            lang_manager.translate(TranslationKeys.CONNECT_PROPERTIES),
            self,
        )
        action2.triggered.connect(
            lambda _: self.start_property_linking()
        )
        menu.addAction(action2)
        remove_action = QAction(lang_manager.translate(TranslationKeys.REMOVE_PROPERTIES), self)
        remove_action.triggered.connect(lambda _: self.start_property_unlinking())
        menu.addAction(remove_action)
        ThemeManager.apply_module_style(menu, [QssPaths.POPUP])
        self.setMenu(menu)

    def update_files_path(self, files_path: str) -> None:
        resolved_path = str(files_path or "").strip()
        if not resolved_path:
            return
        self.item_data["filesPath"] = resolved_path
        if callable(self._on_files_path_updated):
            self._on_files_path_updated(resolved_path)

    def apply_item_status(self, status: dict) -> None:
        # The card and its next actions follow the status Kavitro has now.
        self.item_data["status"] = dict(status)
        if sip.isdeleted(self):
            return
        card = self.parentWidget()
        while card is not None and card.objectName() != "ModuleInfoCard":
            card = card.parentWidget()
        if card is None:
            return
        for status_widget in card.findChildren(MainStatusWidget):
            status_widget.apply_status(self.item_data)

    def start_property_unlinking(self) -> None:
        """The card menu's "Remove linked properties": a list of the links, no map pick."""
        item_id = str(self.item_data.get("id") or "").strip()
        if not item_id:
            return
        unlink_properties_from_card(
            module=self.module,
            item_id=item_id,
            item_label=DataDisplayExtractors.extract_item_name(self.item_data) or item_id,
            lang=self.lang_manager,
            parent=self._parent_window,
            on_linked_changed=self._on_properties_linked,
        )

    def start_property_linking(self) -> None:
        """Start the shared map-selection workflow from any card entry point."""
        self._link_properties_from_map(
            self.module,
            self.item_data,
            self.lang_manager,
        )

    def _link_properties_from_map(self, module, item_data, lang_manager) -> None:
        object_id = (item_data).get("id")

        main_layer = ActiveLayersHelper.resolve_main_property_layer(dialogs=ModernMessageDialog)

        # Clear any prior selection so the map starts clean.
        if main_layer is not None:
            main_layer.removeSelection()

        # With their ids the review can also remove links; a failed read keeps the review add-only.
        existing_ids: dict[str, str] = {}
        try:
            linked_entries = APIModuleActions.get_linked_properties(module, object_id)
            existing_ids = {entry["number"]: entry["id"] for entry in linked_entries if entry.get("number")}
            existing_numbers = set(existing_ids)
        except Exception as exc:  # the add-only review below still works
            PythonFailLogger.log_exception(exc, module=module or "general", event="module_action_linked_ids_failed",
                                           extra={"item_id": object_id})
            existing_numbers = set(
                APIModuleActions.get_module_item_connected_properties(module, object_id) or []
            )

        def _format_label(number: str, feature=None) -> str:
            if feature is not None:
                for fld in (
                    Katastriyksus.l_aadress,
                    Katastriyksus.ay_nimi,
                    Katastriyksus.ov_nimi,
                    Katastriyksus.mk_nimi,
                ):
                    try:
                        val = feature[fld]
                        if val:
                            return f"{val} — {number}"
                    except KeyError:  # the layer has no such field
                        continue
            return number

        existing_display = {}
        if existing_numbers and main_layer is not None:
            existing_feats = MapHelpers.find_features_by_fields_and_values(
                main_layer, Katastriyksus.tunnus, list(existing_numbers)
            )
            for feat in existing_feats:
                try:
                    num = feat[Katastriyksus.tunnus]
                except KeyError:  # the layer has no such field
                    num = None
                if num and num in existing_numbers:
                    existing_display[num] = _format_label(num, feat)
            for num in existing_numbers:
                existing_display.setdefault(num, _format_label(num))
        else:
            for num in existing_numbers:
                existing_display[num] = _format_label(num)

        # If backend already has connections, show them on map to give context before linking.
        if existing_numbers:
            signals_were_blocked = False
            try:
                if main_layer is not None:
                    signals_were_blocked = main_layer.signalsBlocked()
                    main_layer.blockSignals(True)
                PropertiesSelectors.show_connected_properties_on_map(list(existing_numbers), module=module)
            finally:
                if main_layer is not None:
                    main_layer.blockSignals(signals_were_blocked)

        def _missing_note(missing: list[str]) -> str:
            note = lang_manager.translate(TranslationKeys.LINK_PROPERTIES_MISSING_NOTE).format(
                missing=", ".join(missing[:5])
            )
            if len(missing) > 5:
                note += lang_manager.translate(TranslationKeys.MORE_COUNT_SUFFIX).format(count=len(missing) - 5)
            return note

        def _persist_links(selected_numbers: list[str], remove_ids: Optional[list[str]] = None):
            """Link the selection and remove `remove_ids`; a failure is (False, [], {"error": text, "missing": [...]})."""
            missing: list[str] = []
            response = None
            try:
                property_ids, missing = APIModuleActions.resolve_property_ids_by_cadastral(selected_numbers)
                if not property_ids and not remove_ids:
                    # No request failed: none of the selected numbers exist in Kavitro.
                    return False, [], {"error": _missing_note(missing), "missing": missing}
                if remove_ids:
                    # One request for both; success only once Kavitro no longer links the removed ones.
                    APIModuleActions.update_property_links(
                        module, object_id, associate_ids=property_ids, dissociate_ids=remove_ids)
                    linked = APIModuleActions.get_linked_properties(module, object_id)
                    still = [entry["number"] or entry["id"] for entry in linked if entry["id"] in set(remove_ids)]
                    if still:
                        raise RuntimeError(", ".join(still))
                    refreshed = [entry["number"] for entry in linked if entry.get("number")]
                else:
                    response = APIModuleActions.associate_properties(module, object_id, property_ids)
                    # The answer lists the linked properties; read them again only when it holds part of them.
                    refreshed = APIModuleActions.linked_cadastral_numbers_from_response(module, response)
                if refreshed is None:
                    refreshed = APIModuleActions.get_module_item_connected_properties(module, object_id) or []
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module=module or "general",
                    event="module_action_link_properties_failed",
                    extra={"item_id": object_id},
                )
                return False, [], {"error": user_message(exc), "missing": missing}
            return True, refreshed, {"missing": missing, "raw": response}


        def _open_review_dialog(selected_numbers: list[str], selected_feats: list = None):
            selected_display = {}
            if selected_feats:
                for feat in selected_feats:
                    try:
                        num = feat[Katastriyksus.tunnus]
                    except KeyError:  # the layer has no such field
                        num = None
                    if num:
                        selected_display[num] = _format_label(num, feat)
            for num in selected_numbers:
                selected_display.setdefault(num, _format_label(num))

            dialog = PropertyLinkReviewDialog(existing_display, selected_display, lang_manager,
                                              allow_removal=bool(existing_ids))
            result = dialog.exec_()
            if dialog.reselect_requested:
                _start_selection()
                return
            if result == QDialog.Accepted:
                remove_numbers = [number for number in dialog.numbers_to_remove if number in existing_ids]
                if remove_numbers and not confirm_link_removal(
                    lang_manager, module, DataDisplayExtractors.extract_item_name(item_data) or str(object_id),
                    [{"id": existing_ids[n], "number": n, "address": ""} for n in remove_numbers],
                    parent=self._parent_window,
                ):
                    self._map_selection_orchestrator = None
                    self._restore_parent_window()
                    return
                linked_before = set(existing_numbers)
                ok, refreshed, resp = _persist_links(
                    [number for number in selected_numbers if number not in remove_numbers],
                    [existing_ids[number] for number in remove_numbers],
                )
                if ok:
                    # The total alone read like the number just added.
                    added = len([number for number in refreshed if number not in linked_before])
                    already = len([number for number in set(selected_numbers) if number in linked_before])
                    existing_numbers.clear()
                    existing_numbers.update(refreshed)
                    summary = ", ".join(refreshed[:5])
                    if len(refreshed) > 5:
                        summary += lang_manager.translate(TranslationKeys.MORE_COUNT_SUFFIX).format(
                            count=len(refreshed) - 5
                        )
                    missing = (resp or {}).get("missing") if isinstance(resp, dict) else []
                    extra_note = "\n\n" + lang_manager.translate(TranslationKeys.LINK_PROPERTIES_ADDED_NOTE).format(
                        added=added, already=already)
                    if remove_numbers:
                        extra_note += "\n\n" + lang_manager.translate(TranslationKeys.LINK_REMOVED_NOTE).format(
                            removed=len(remove_numbers))
                    if missing:
                        extra_note += "\n\n" + _missing_note(missing)
                    ModernMessageDialog.show_info(
                        lang_manager.translate(TranslationKeys.SUCCESS),
                        lang_manager.translate(TranslationKeys.LINK_PROPERTIES_SUCCESS).format(
                            pid=object_id,
                            count=len(refreshed),
                            preview=summary,
                            extra=extra_note,
                        ),
                    )
                    if callable(self._on_properties_linked):
                        try:
                            self._on_properties_linked(list(refreshed))
                        except Exception as exc:
                            PythonFailLogger.log_exception(
                                exc,
                                module=module or "general",
                                event="module_action_properties_linked_callback_failed",
                            )
                else:
                    summary = ", ".join(selected_numbers[:5])
                    if len(selected_numbers) > 5:
                        summary += lang_manager.translate(TranslationKeys.MORE_COUNT_SUFFIX).format(
                            count=len(selected_numbers) - 5
                        )
                    ModernMessageDialog.show_warning(
                        lang_manager.translate(TranslationKeys.ERROR),
                        lang_manager.translate(TranslationKeys.LINK_PROPERTIES_ERROR).format(
                            pid=object_id,
                            count=len(selected_numbers),
                            preview=summary,
                            err=(resp.get("error") if isinstance(resp, dict) else resp) or "unknown",
                        ),
                    )
            self._map_selection_orchestrator = None
            self._restore_parent_window()

        # Cancel any previous selection controller to avoid dangling signals
        if self._map_selection_orchestrator is not None:
            self._map_selection_orchestrator.cancel()

        orchestrator = MapSelectionOrchestrator(parent=self)
        self._map_selection_orchestrator = orchestrator

        def _on_selected(_layer, features: Iterable):
            # Selection finished; bring the plugin window back before dialogs
            self._restore_parent_window()

            cadastral_numbers = []
            for f in features or []:
                try:
                    tunnus = f[Katastriyksus.tunnus]
                    if tunnus:
                        cadastral_numbers.append(str(tunnus))
                except KeyError:  # the layer has no such field
                    continue

            if not cadastral_numbers:
                ModernMessageDialog.show_warning(
                    lang_manager.translate(TranslationKeys.ERROR),
                    lang_manager.translate(TranslationKeys.MAP_SELECTION_NONE),
                )
                return

            summary = ", ".join(cadastral_numbers[:5])
            if len(cadastral_numbers) > 5:
                summary += lang_manager.translate(TranslationKeys.MORE_COUNT_SUFFIX).format(
                    count=len(cadastral_numbers) - 5
                )

            _open_review_dialog(cadastral_numbers, features)

        def _start_selection():
            started = orchestrator.start_selection_for_layer(
                main_layer,
                on_selected=_on_selected,
                selection_tool="rectangle",
                restore_pan=True,
                min_selected=1,
                max_selected=None,
                clear_filter=False,
                keep_existing_selection=bool(existing_numbers),
                before_start=self._enter_map_selection_mode,
                on_abandoned=self._restore_parent_window,
            )
            if not started:
                ModernMessageDialog.show_warning(
                    lang_manager.translate(TranslationKeys.ERROR),
                    lang_manager.translate(TranslationKeys.MAP_SELECTION_START_FAILED),
                )
                self._map_selection_orchestrator = None
                self._exit_map_selection_mode()

        _start_selection()

    def _restore_parent_window(self) -> None:
        self._exit_map_selection_mode()

    def safe_parent_window(self) -> Optional[QDialog]:
        w = self._resolve_parent_window()
        return DialogHelpers.resolve_safe_parent_window(
            w,
            iface_obj=iface,
            module=self.module or "general",
            qgis_main_error_event="module_action_qgis_main_failed",
        )

    def _enter_map_selection_mode(self) -> None:
        parent_window = self.safe_parent_window()
        DialogHelpers.enter_map_selection_mode(
            iface_obj=iface,
            parent_window=parent_window,
            dialogs=[self],
        )
        if parent_window is not None:
            self._parent_window = parent_window
            self._restore_parent_on_close = True

    def _exit_map_selection_mode(self) -> None:
        if not self._restore_parent_on_close:
            return
        parent_window = self.safe_parent_window() or self._parent_window
        DialogHelpers.exit_map_selection_mode(
            iface_obj=iface,
            parent_window=parent_window,
            dialogs=[self],
        )
        self._restore_parent_on_close = False

    def _resolve_parent_window(self) -> Optional[QDialog]:
        try:
            top = self.window()
            while top is not None and top.parent() not in (None, top):
                top = top.parent()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=self.module or "general",
                event="module_action_resolve_parent_failed",
            )
            top = None

        if top is None:
            return None

        return top


class ShowOnMapActionButton(CardActionButton):
    LINK_MODE = "link-properties"
    SHOW_MODE = "show-properties"

    def __init__(
        self,
        module_name: Optional[str],
        item_id: Optional[str],
        lang_manager,
        *,
        has_connections: Optional[int] = None,
    ) -> None:
        tooltip = (
            lang_manager.translate(ToolbarTranslationKeys.SHOW_CONNECTED_PROPERTIES_ON_MAP)
            if lang_manager
            else ToolbarTranslationKeys.SHOW_CONNECTED_PROPERTIES_ON_MAP
        )
        super().__init__(
            "ShowOnMapButton",
            IconNames.ICON_SHOW_ON_MAP,
            tooltip,
            lang_manager,
        )
        self._module_name = str(module_name or "").strip().lower()
        self._item_id = str(item_id or "").strip()
        self._lang_manager = lang_manager
        self._link_properties_callback = None
        self._connection_count = 0
        self.clicked.connect(self._handle_click)
        self.set_connection_count(has_connections)

    def _translate(self, key: str) -> str:
        if self._lang_manager:
            return self._lang_manager.translate(key)
        return str(key or "")

    def _apply_visual_state(self) -> None:
        has_connections = self._connection_count > 0
        if has_connections:
            self._icon_name = IconNames.ICON_SHOW_ON_MAP
            tooltip_key = ToolbarTranslationKeys.SHOW_CONNECTED_PROPERTIES_ON_MAP
            mode = self.SHOW_MODE
        else:
            self._icon_name = IconNames.ICON_CONNECT_PROPERTIES
            tooltip_key = ToolbarTranslationKeys.CONNECT_MISSING_PROPERTIES
            mode = self.LINK_MODE

        self.setIcon(ThemeManager.get_qicon(self._icon_name))
        action_label = self._translate(tooltip_key)
        self.setToolTip(action_label)
        self.setAccessibleName(action_label)
        self.setProperty("connectionMode", mode)
        can_execute = bool(self._module_name and self._item_id)
        if not has_connections:
            can_execute = can_execute and callable(self._link_properties_callback)
        self.setEnabled(can_execute)

    def set_connection_count(self, connection_count: Optional[int]) -> None:
        try:
            self._connection_count = max(0, int(connection_count or 0))
        except (TypeError, ValueError):
            self._connection_count = 0
        self._apply_visual_state()

    def set_link_properties_callback(self, callback) -> None:
        self._link_properties_callback = callback if callable(callback) else None
        self._apply_visual_state()

    def _handle_click(self, _checked: bool = False) -> None:
        if self._connection_count > 0:
            show_items_on_map(
                self._module_name,
                self._item_id,
            )
            return
        if callable(self._link_properties_callback):
            self._link_properties_callback()

    @property
    def connection_mode(self) -> str:
        return self.SHOW_MODE if self._connection_count > 0 else self.LINK_MODE
