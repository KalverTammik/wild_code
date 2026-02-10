from typing import Optional, Iterable

from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QAction, QMenu, QPushButton, QDialog
from ...widgets.DataDisplayWidgets.LinkReviewDialog import LinkReviewDialog

from qgis.utils import iface


from ...languages.translation_keys import ToolbarTranslationKeys
from ...utils.url_manager import OpenLink, loadWebpage, Module
from ...python.api_actions import APIModuleActions
from ...utils.MapTools.item_selector_tools import PropertiesSelectors
from ..theme_manager import ThemeManager
from ...utils.Folders.foldersHelpers import FolderHelpers, FolderEngines
from ...constants.settings_keys import SettingsService
from ...constants.module_icons import IconNames
from ...modules.Settings.setting_keys import SettingDialogPlaceholders
from ...utils.moduleSwitchHelper import ModuleSwitchHelper
from ...constants.button_props import ButtonVariant
from ...utils.messagesHelper import ModernMessageDialog
from ...languages.translation_keys import TranslationKeys
from ...utils.MapTools.map_selection_controller import MapSelectionController
from ...constants.cadastral_fields import Katastriyksus
from ...utils.MapTools.MapHelpers import ActiveLayersHelper, MapHelpers
from ...Logs.python_fail_logger import PythonFailLogger
from ...ui.window_state.DialogCoordinator import get_dialog_coordinator
from ...python.responses import DataDisplayExtractors



def open_item_in_browser(module_name: Optional[str], item_id: Optional[str]) -> None:
    if not module_name or not item_id:
        return
    try:
        wl = OpenLink()
        base = wl.weblink_by_module(module_name)
        if not base:
            return
        base = base.rstrip("/")
        if not base.endswith("s"):
            base = f"{base}s"
        url = f"{base}/{item_id}"
        loadWebpage.open_webpage(url)
    except Exception as exc:
        PythonFailLogger.log_exception(
            exc,
            module=module_name or "general",
            event="module_action_open_browser_failed",
        )


def show_items_on_map(module_name: Optional[str], item_id: Optional[str]) -> None:
    if not module_name or not item_id:
        return
    numbers = APIModuleActions.get_module_item_connected_properties(module_name, item_id)
    if numbers:
        PropertiesSelectors.show_connected_properties_on_map(numbers, module=module_name)


class CardActionButton(QPushButton):
    def __init__(
        self,
        object_name: str,
        icon_name: Optional[str],
        tooltip_text: Optional[str],
        lang_manager,
    ) -> None:
        super().__init__("")
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


class OpenFolderActionButton(CardActionButton):
    def __init__(self, file_path: Optional[str], lang_manager) -> None:
        tooltip = lang_manager.translate(ToolbarTranslationKeys.OPEN_FOLDER) if lang_manager else ""
        super().__init__(
            "OpenFolderButton",
            IconNames.ICON_FOLDERICON,
            tooltip,
            lang_manager,
        )
        enabled = bool(file_path)
        self.setEnabled(enabled)
        if enabled:
            self.clicked.connect(lambda _, path=file_path: FolderHelpers.open_item_folder(path))


class OpenWebActionButton(CardActionButton):
    def __init__(self, module_name: Optional[str], item_id: Optional[str], lang_manager) -> None:
        tooltip = lang_manager.translate(ToolbarTranslationKeys.OPEN_ITEM_IN_BROWSER) if lang_manager else ""
        super().__init__(
            "OpenWebpageButton",
            IconNames.VALISEE_V_ICON_NAME,
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
    def __init__(self, lang_manager=None, item_data=None, module=None, on_properties_linked=None) -> None:
        tooltip = lang_manager.translate(ToolbarTranslationKeys.MORE_ACTIONS) if lang_manager else ""
        super().__init__(
            "MoreActionsButton",
            IconNames.ICON_ADD,
            tooltip,
            lang_manager,
        )
        self._item_data = item_data
        self.module = module  # Ensure module is passed correctly
        self._map_selection_controller: Optional[MapSelectionController] = None
        self._on_properties_linked = on_properties_linked
        self._parent_window: Optional[QDialog] = None
        self._restore_parent_on_close: bool = False

        # Resolve the top-level plugin window (never minimize QGIS main window)
        self._parent_window = self._resolve_parent_window()

        menu = QMenu(self)

        if module == Module.PROJECT.value:
            action1 = QAction(
                lang_manager.translate(ToolbarTranslationKeys.GENERATE_PROJECT_FOLDER),
                self,
            )
            action1.triggered.connect(self._generate_project_folder(module, item_data, lang_manager))
            menu.addAction(action1)

        action2 = QAction(
            lang_manager.translate(TranslationKeys.CONNECT_PROPERTIES),
            self,
        )
        action2.triggered.connect(
            lambda _, mod=module, data=item_data, lm=lang_manager: self._link_properties_from_map(mod, data, lm)
        )
        menu.addAction(action2)
        self.setMenu(menu)
    @staticmethod
    def _generate_project_folder(module, item_data, lang_manager):
        def handler():            
            svc = SettingsService()
            folder_to_copy = svc.module_label_value(module, SettingDialogPlaceholders.PROJECTS_SOURCE_FOLDER)
            target_folder = svc.module_label_value(module, SettingDialogPlaceholders.PROJECTS_TARGET_FOLDER)
            if not folder_to_copy or not target_folder:
                ModernMessageDialog.show_warning(
                    lang_manager.translate(TranslationKeys.PROJECT_FOLDER_MISSING_TITLE),
                    lang_manager.translate(TranslationKeys.PROJECT_FOLDER_MISSING_MESSAGE),
                )

                ModuleSwitchHelper.switch_module(
                    Module.SETTINGS.name,
                    focus_module=module,
                )
                return
            FolderEngines.generate_project_folder_from_template(
                DataDisplayExtractors.extract_item_id(item_data),
                DataDisplayExtractors.extract_item_name(item_data),
                DataDisplayExtractors.extract_project_number(item_data),
                source_folder=folder_to_copy,
                target_folder=target_folder,
            )

        return handler

    def _link_properties_from_map(self, module, item_data, lang_manager) -> None:
        object_id = (item_data).get("id")

        main_layer = ActiveLayersHelper.resolve_main_property_layer(silent=False)

        # Clear any prior selection so the map starts clean.
        if main_layer is not None:
            main_layer.removeSelection()

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
                    except Exception:
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
                except Exception:
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

        def _persist_links(selected_numbers: list[str]):
            property_ids, missing = APIModuleActions.resolve_property_ids_by_cadastral(selected_numbers)
            if not property_ids:
                raise Exception(f"No property ids resolved for selection: {missing}")
            response = APIModuleActions.associate_properties(module, object_id, property_ids)
            refreshed = APIModuleActions.get_module_item_connected_properties(module, object_id) or []
            return True, refreshed, {"missing": missing, "raw": response}


        def _open_review_dialog(selected_numbers: list[str], selected_feats: list = None):
            selected_display = {}
            if selected_feats:
                for feat in selected_feats:
                    try:
                        num = feat[Katastriyksus.tunnus]
                    except Exception:
                        num = None
                    if num:
                        selected_display[num] = _format_label(num, feat)
            for num in selected_numbers:
                selected_display.setdefault(num, _format_label(num))

            dialog = LinkReviewDialog(existing_display, selected_display, lang_manager)
            result = dialog.exec_()
            if dialog.reselect_requested:
                _start_selection()
                return
            if result == QDialog.Accepted:
                ok, refreshed, resp = _persist_links(selected_numbers)
                if ok:
                    existing_numbers.clear()
                    existing_numbers.update(refreshed)
                    summary = ", ".join(refreshed[:5])
                    if len(refreshed) > 5:
                        summary += lang_manager.translate(TranslationKeys.MORE_COUNT_SUFFIX).format(
                            count=len(refreshed) - 5
                        )
                    missing = (resp or {}).get("missing") if isinstance(resp, dict) else []
                    extra_note = ""
                    if missing:
                        missing_preview = ", ".join(missing[:5])
                        extra_note = "\n\n" + lang_manager.translate(TranslationKeys.LINK_PROPERTIES_MISSING_NOTE).format(missing=missing_preview)
                        if len(missing) > 5:
                            extra_note += lang_manager.translate(TranslationKeys.MORE_COUNT_SUFFIX).format(
                                count=len(missing) - 5
                            )
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
                            err=resp or "unknown",
                        ),
                    )
            self._map_selection_controller = None
            self._restore_parent_window()

        # Cancel any previous selection controller to avoid dangling signals
        if self._map_selection_controller is not None:
            self._map_selection_controller.cancel_selection()

        controller = MapSelectionController()
        self._map_selection_controller = controller

        def _on_selected(_layer, features: Iterable):
            # Selection finished; bring the plugin window back before dialogs
            self._restore_parent_window()

            cadastral_numbers = []
            for f in features or []:
                try:
                    tunnus = f[Katastriyksus.tunnus]
                    if tunnus:
                        cadastral_numbers.append(str(tunnus))
                except Exception:
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
            self._enter_map_selection_mode()
            started = controller.start_selection(
                main_layer,
                on_selected=_on_selected,
                selection_tool="rectangle",
                restore_pan=True,
                min_selected=1,
                max_selected=None,
                clear_filter=False,
                keep_existing_selection=bool(existing_numbers),
            )
            if not started:
                ModernMessageDialog.show_warning(
                    lang_manager.translate(TranslationKeys.ERROR),
                    lang_manager.translate(TranslationKeys.MAP_SELECTION_START_FAILED),
                )
                self._map_selection_controller = None
                self._exit_map_selection_mode()

        _start_selection()

    def _minimize_parent_window_if_safe(self) -> None:
        self._enter_map_selection_mode()

    def _restore_parent_window(self) -> None:
        self._exit_map_selection_mode()

    def _get_safe_parent_window(self) -> Optional[QDialog]:
        w = self._resolve_parent_window()
        if w is None:
            return None
        try:
            qgis_main = iface.mainWindow() if iface is not None else None
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=self.module or "general",
                event="module_action_qgis_main_failed",
            )
            qgis_main = None
        if qgis_main is not None and w is qgis_main:
            return None
        return w

    def _enter_map_selection_mode(self) -> None:
        coordinator = get_dialog_coordinator(iface)
        parent_window = self._get_safe_parent_window()
        coordinator.enter_map_selection_mode(parent=parent_window, dialogs=[self])
        if parent_window is not None:
            self._parent_window = parent_window
            self._restore_parent_on_close = True

    def _exit_map_selection_mode(self) -> None:
        if not self._restore_parent_on_close:
            return
        coordinator = get_dialog_coordinator(iface)
        parent_window = self._get_safe_parent_window() or self._parent_window
        coordinator.exit_map_selection_mode(parent=parent_window, dialogs=[self])
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
    def __init__(
        self,
        module_name: Optional[str],
        item_id: Optional[str],
        lang_manager,
        *,
        has_connections: Optional[bool] = None,
    ) -> None:
        super().__init__(
            "ShowOnMapButton",
            IconNames.ICON_SHOW_ON_MAP,
            ToolbarTranslationKeys.SHOW_ITEMS_ON_MAP,
            lang_manager,
        )
        can_execute = bool(module_name and item_id)
        if has_connections is False:
            can_execute = False
        self.setEnabled(can_execute)
        if module_name and item_id:
            self.clicked.connect(
                lambda _, module=module_name, mid=item_id: show_items_on_map(module, mid)
            )
