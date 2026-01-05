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
from ...utils.MapTools.MapHelpers import ActiveLayersHelper



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
    except Exception:
        pass


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
        tooltip_key: Optional[str],
        lang_manager,
    ) -> None:
        super().__init__("")
        self.setObjectName(object_name)
        self.setAutoDefault(False)
        self.setDefault(False)
        self.setProperty("variant", ButtonVariant.MODULE_CARD)
        self.setFixedSize(22, 20)
        self.setIconSize(QSize(14, 14))
        if icon_name:
            self.setIcon(ThemeManager.get_qicon(icon_name))
        if tooltip_key:
            self.setToolTip(lang_manager.translate(tooltip_key))


class OpenFolderActionButton(CardActionButton):
    def __init__(self, file_path: Optional[str], lang_manager) -> None:
        super().__init__(
            "OpenFolderButton",
            IconNames.ICON_FOLDERICON,
            ToolbarTranslationKeys.OPEN_FOLDER,
            lang_manager,
        )
        enabled = bool(file_path)
        self.setEnabled(enabled)
        if enabled:
            self.clicked.connect(lambda _, path=file_path: FolderHelpers.open_item_folder(path))


class OpenWebActionButton(CardActionButton):
    def __init__(self, module_name: Optional[str], item_id: Optional[str], lang_manager) -> None:
        super().__init__(
            "OpenWebpageButton",
            IconNames.VALISEE_V_ICON_NAME,
            ToolbarTranslationKeys.OPEN_ITEM_IN_BROWSER,
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
        super().__init__(
            "MoreActionsButton",
            IconNames.ICON_ADD,
            ToolbarTranslationKeys.MORE_ACTIONS,
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
                item_data.get("id"),
                item_data.get("name"),
                item_data.get("projectNumber"),
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
        print(f"Existing linked properties before map selection: {existing_numbers}")

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


        def _open_review_dialog(selected_numbers: list[str]):
            dialog = LinkReviewDialog(existing_numbers, selected_numbers, lang_manager)
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
                        summary += f" … (+{len(refreshed) - 5} more)"
                    missing = (resp or {}).get("missing") if isinstance(resp, dict) else []
                    extra_note = ""
                    if missing:
                        extra_note = "\n\nMissing/not found: " + ", ".join(missing[:5])
                        if len(missing) > 5:
                            extra_note += f" … (+{len(missing) - 5} more)"
                    ModernMessageDialog.show_info(
                        lang_manager.translate(TranslationKeys.SUCCESS),
                        (
                            "Linked properties saved for project {pid}.\n"
                            "Total linked: {count}. {preview}{extra}"
                            ).format(pid=object_id, count=len(refreshed), preview=summary, extra=extra_note),
                    )
                    if callable(self._on_properties_linked):
                        try:
                            self._on_properties_linked(list(refreshed))
                        except Exception:
                            pass
                else:
                    summary = ", ".join(selected_numbers[:5])
                    if len(selected_numbers) > 5:
                        summary += f" … (+{len(selected_numbers) - 5} more)"
                    ModernMessageDialog.show_warning(
                        lang_manager.translate(TranslationKeys.ERROR) or "Error",
                        (
                            "Could not link properties for project {pid}.\n"
                            "Pending selection ({count}): {preview}\n\n"
                            "Details: {err}"
                            ).format(pid=object_id, count=len(selected_numbers), preview=summary, err=resp or "unknown"),
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
                    "No properties were selected from the map.",
                )
                return

            summary = ", ".join(cadastral_numbers[:5])
            if len(cadastral_numbers) > 5:
                summary += f" … (+{len(cadastral_numbers) - 5} veel)"

            _open_review_dialog(cadastral_numbers)

        def _start_selection():
            self._minimize_parent_window_if_safe()
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
                    "Could not start map selection for properties.",
                )
                self._map_selection_controller = None
                self._restore_parent_window()

        _start_selection()

    def _minimize_parent_window_if_safe(self) -> None:
        w = self._resolve_parent_window()
        if w is None:
            return
        try:
            if w.isVisible() and not w.isMinimized():
                w.showMinimized()
                self._parent_window = w
                self._restore_parent_on_close = True
        except Exception:
            pass

    def _restore_parent_window(self) -> None:
        if not self._restore_parent_on_close:
            return
        w = self._parent_window or self._resolve_parent_window()
        if w is None:
            return
        try:
            w.showNormal()
            w.raise_()
            w.activateWindow()
        except Exception:
            pass
        self._restore_parent_on_close = False

    def _resolve_parent_window(self) -> Optional[QDialog]:
        try:
            top = self.window()
            while top is not None and top.parent() not in (None, top):
                top = top.parent()
        except Exception:
            top = None

        if top is None:
            return None

        try:
            qgis_main = iface.mainWindow() if iface is not None else None
        except Exception:
            qgis_main = None

        if qgis_main is not None and top is qgis_main:
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
