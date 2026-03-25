from __future__ import annotations

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget
from qgis.utils import iface

from ...constants.button_props import ButtonSize, ButtonVariant
from ...constants.cadastral_fields import AreaUnit
from ...constants.module_icons import IconNames
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...ui.window_state.dialog_helpers import DialogHelpers
from ...utils.MapTools.item_selector_tools import PropertiesSelectors
from ...utils.url_manager import Module
from ...widgets.EasementPropertyAreaCalculationWidget import EasementPropertyAreaCalculationWidget
from ...widgets.theme_manager import ThemeManager, styleExtras
from ...constants.file_paths import QssPaths


class EasementPropertiesWidget(QWidget):
    _AREA_UNIT_LABELS = {
        AreaUnit.M: "m²",
        AreaUnit.H: "ha",
    }
    _DEFAULT_CURRENCY = "EUR"

    def __init__(self, item_data=None, parent=None, lang_manager=None):
        super().__init__(parent)
        self.setObjectName("ExtraInfoWidget")
        self._item_data = item_data if isinstance(item_data, dict) else {}
        self._lang = lang_manager or LanguageManager()
        self._detail_dialog = None
        self._detail_parent_window = None
        self._build_ui()

    @staticmethod
    def _extract_edges(item_data: dict) -> list[dict[str, object]]:
        properties = item_data.get("properties") if isinstance(item_data.get("properties"), dict) else {}
        edges = properties.get("edges") if isinstance(properties.get("edges"), list) else []
        return [edge for edge in edges if isinstance(edge, dict)]

    @staticmethod
    def _display_label(edge: dict[str, object]) -> str:
        node = edge.get("node") if isinstance(edge.get("node"), dict) else {}
        number = str(node.get("cadastralUnitNumber") or edge.get("cadastralUnitNumber") or "").strip()
        address = str(node.get("displayAddress") or edge.get("displayAddress") or "").strip()
        if address and number and address != number:
            return f"{address} — {number}"
        return address or number or "-"

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._edges = self._extract_edges(self._item_data)
        edges = self._edges
        if not edges:
            self.hide()
            return

        header_card = QFrame(self)
        header_card.setObjectName("PropertyDetailsFrame")
        header_card.setProperty("compact", True)
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(10, 10, 10, 10)
        header_layout.setSpacing(6)
        layout.addWidget(header_card)

        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel(
            self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_PROPERTY_SECTION_TITLE),
            self,
        )
        title.setObjectName("DetailsTitle")
        title_layout.addWidget(title)
        title_layout.addStretch(1)

        expand_btn_frame = QFrame(self)
        expand_btn_frame.setObjectName("ExpandButtonFrame")
        expand_layout = QHBoxLayout(expand_btn_frame)
        expand_layout.setContentsMargins(0, 4, 4, 0)
        expand_layout.setSpacing(0)

        expand_btn = QPushButton(expand_btn_frame)
        expand_btn.setObjectName("ExpandButton")
        expand_btn.setToolTip(self._lang.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_EXTRAINFO_TOOLTIP))
        expand_btn.setFixedSize(22, 22)
        expand_btn.setIcon(ThemeManager.get_qicon(IconNames.ICON_EYE))
        expand_btn.setIconSize(QSize(14, 14))
        expand_btn.setCursor(Qt.PointingHandCursor)
        expand_btn.setAutoDefault(False)
        expand_btn.setDefault(False)
        expand_btn.clicked.connect(self._show_detailed_overview)
        expand_layout.addWidget(expand_btn)
        title_layout.addWidget(expand_btn_frame)

        header_layout.addLayout(title_layout)

        styleExtras.apply_chip_shadow(header_card)
        ThemeManager.apply_module_style(self, [QssPaths.MODULE_INFO, QssPaths.PROPERTIES_UI, QssPaths.BUTTONS])

    def _connected_property_numbers(self) -> list[str]:
        numbers: list[str] = []
        for edge in self._edges:
            node = edge.get("node") if isinstance(edge.get("node"), dict) else {}
            number = str(node.get("cadastralUnitNumber") or edge.get("cadastralUnitNumber") or "").strip()
            if number:
                numbers.append(number)
        return numbers

    def _resolve_parent_window(self):
        try:
            host = self.window()
        except Exception:
            return None
        if host is None:
            return None
        return DialogHelpers.resolve_safe_parent_window(
            host.window(),
            iface_obj=iface,
            module=Module.EASEMENT.value,
            qgis_main_error_event="easement_properties_qgis_main_failed",
        )

    def _restore_parent_window(self) -> None:
        if self._detail_parent_window is None:
            return
        DialogHelpers.exit_map_selection_mode(
            iface_obj=iface,
            parent_window=self._detail_parent_window,
            dialogs=None,
            bring_front=True,
        )
        self._detail_parent_window = None

    def _show_detailed_overview(self) -> None:
        numbers = self._connected_property_numbers()
        if numbers:
            PropertiesSelectors.show_connected_properties_on_map(numbers, module=Module.EASEMENT.value)

        parent_window = self._resolve_parent_window()
        if parent_window is not None:
            DialogHelpers.enter_map_selection_mode(
                iface_obj=iface,
                parent_window=parent_window,
                dialogs=None,
            )
            self._detail_parent_window = parent_window

        if self._detail_dialog is not None:
            try:
                self._detail_dialog.close()
            except Exception:
                pass

        dialog = QDialog(None)
        dialog.setObjectName("ExtraInfoDialog")
        dialog.setWindowTitle(
            f"{self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_PROPERTY_SECTION_TITLE)} - "
            f"{self._lang.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_DETAIL_TITLE_SUFFIX)}"
        )
        dialog.setModal(False)
        dialog.resize(720, 500)
        dialog.finished.connect(lambda _result: self._restore_parent_window())

        layout = QVBoxLayout(dialog)

        title = QLabel(self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_PROPERTY_SECTION_TITLE), dialog)
        title.setObjectName("ExtraInfoDialogTitle")
        layout.addWidget(title)

        scroll_area = QScrollArea(dialog)
        scroll_area.setObjectName("ExtraInfoScroll")
        scroll_area.setWidgetResizable(True)

        content = QWidget(scroll_area)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)

        for edge in self._edges:
            property_card = QFrame(content)
            property_card.setObjectName("PropertyDetailsFrame")
            property_card.setProperty("compact", True)
            property_card_layout = QVBoxLayout(property_card)
            property_card_layout.setContentsMargins(10, 10, 10, 10)
            property_card_layout.setSpacing(6)

            property_widget = EasementPropertyAreaCalculationWidget(
                lang_manager=self._lang,
                edge=edge,
                area_unit_labels=self._AREA_UNIT_LABELS,
                default_currency=self._DEFAULT_CURRENCY,
                show_title=True,
                title_text=self._display_label(edge),
                read_only=True,
                parent=property_card,
            )
            property_card_layout.addWidget(property_widget)
            styleExtras.apply_chip_shadow(property_card)
            content_layout.addWidget(property_card)

        content_layout.addStretch(1)
        scroll_area.setWidget(content)
        layout.addWidget(scroll_area)

        close_btn = QPushButton(self._lang.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_CLOSE), dialog)
        close_btn.setObjectName("ConfirmButton")
        close_btn.setProperty("variant", ButtonVariant.SUCCESS)
        close_btn.setProperty("btnSize", ButtonSize.MEDIUM)
        close_btn.setAutoDefault(False)
        close_btn.setDefault(False)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)

        ThemeManager.apply_module_style(dialog, [QssPaths.MODULE_INFO, QssPaths.PROPERTIES_UI, QssPaths.BUTTONS])
        self._detail_dialog = dialog
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
