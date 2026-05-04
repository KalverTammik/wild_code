from __future__ import annotations

from PyQt5.QtWidgets import QFrame, QVBoxLayout, QWidget

from ...constants.cadastral_fields import AreaUnit
from ...languages.language_manager import LanguageManager
from ...utils.MapTools.item_selector_tools import PropertiesSelectors
from ...utils.url_manager import Module
from ...widgets.EasementPropertyAreaCalculationWidget import EasementPropertyAreaCalculationWidget
from ...widgets.theme_manager import styleExtras


class EasementPropertiesWidget(QWidget):
    _AREA_UNIT_LABELS = {
        AreaUnit.M: "m²",
        AreaUnit.H: "ha",
    }
    _DEFAULT_CURRENCY = "EUR"

    def __init__(self, item_data=None, parent=None, lang_manager=None):
        super().__init__(parent)
        self.setObjectName("EasementPropertiesWidget")
        self._item_data = item_data if isinstance(item_data, dict) else {}
        self._lang = lang_manager or LanguageManager()
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
        for edge in edges:
            property_card = QFrame(self)
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
            layout.addWidget(property_card)

        layout.addStretch(1)

    def _connected_property_numbers(self) -> list[str]:
        numbers: list[str] = []
        for edge in self._edges:
            node = edge.get("node") if isinstance(edge.get("node"), dict) else {}
            number = str(node.get("cadastralUnitNumber") or edge.get("cadastralUnitNumber") or "").strip()
            if number:
                numbers.append(number)
        return numbers

    @staticmethod
    def show_connected_properties_on_map(item_data=None) -> None:
        widget = EasementPropertiesWidget(item_data=item_data)
        numbers = widget._connected_property_numbers()
        if numbers:
            PropertiesSelectors.show_connected_properties_on_map(numbers, module=Module.EASEMENT.value)
