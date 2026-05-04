from __future__ import annotations

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QCheckBox, QComboBox, QDoubleSpinBox, QGridLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from ..constants.cadastral_fields import AreaUnit
from ..languages.translation_keys import TranslationKeys


class EasementPropertyAreaCalculationWidget(QWidget):
    totalsChanged = pyqtSignal()
    unitChanged = pyqtSignal()

    def __init__(
        self,
        *,
        lang_manager,
        edge: dict[str, object],
        area_unit_labels: dict[str, str],
        default_currency: str,
        show_title: bool = False,
        title_text: str = "",
        read_only: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._lang = lang_manager
        self._edge = edge or {}
        self._area_unit_labels = area_unit_labels or {}
        self._default_currency = str(default_currency or "EUR")
        self._show_title = bool(show_title)
        self._title_text = str(title_text or "")
        self._read_only = bool(read_only)
        self._build_ui()

    @staticmethod
    def _coerce_float(value) -> float | None:
        try:
            if value is None or value == "":
                return None
            return float(value)
        except Exception:
            return None

    def _format_area_display(self, size_value, unit_value: str) -> str:
        numeric = self._coerce_float(size_value)
        if numeric is None:
            return "–"
        if unit_value == AreaUnit.H:
            return f"{numeric:.4f} ha"
        return f"{numeric:.2f} m²"

    def _format_money_display(self, amount_value, currency_code: str) -> str:
        numeric = self._coerce_float(amount_value)
        if numeric is None:
            return "–"
        return f"{numeric:.2f} {currency_code}".strip()

    def _apply_read_only_mode(self) -> None:
        if hasattr(self, "unit_combo"):
            self.unit_combo.setEnabled(False)
        if hasattr(self, "currency_combo"):
            self.currency_combo.setEnabled(False)
        self.payable_checkbox.setEnabled(False)
        self.price_spin.setReadOnly(True)
        self.price_spin.setButtonSymbols(QDoubleSpinBox.NoButtons)
        if hasattr(self, "next_payment_edit"):
            self.next_payment_edit.setReadOnly(True)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        if self._show_title and self._title_text:
            self.title_label = QLabel(self._title_text, self)
            self.title_label.setObjectName("DetailsTitle")
            self.title_label.setWordWrap(True)
            root.addWidget(self.title_label)
        else:
            self.title_label = None

        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(6)
        root.addLayout(layout)

        area_dict = self._edge.get("area") or {}
        unit_value = str(area_dict.get("unit") or AreaUnit.M)
        total_dict = self._edge.get("totalPrice") or {}
        price_dict = self._edge.get("pricePerAreaUnit") or {}
        currency_code = str(price_dict.get("currencyCode") or self._default_currency)
        total_currency_code = str(total_dict.get("currencyCode") or currency_code)
        is_payable = bool(self._edge.get("isPayable"))
        self._current_unit_value = unit_value
        self._current_currency_code = currency_code
        self._current_total_text = ""
        self._current_next_payment_text = str(self._edge.get("nextPaymentDate") or "")

        area_label = QLabel(self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_PROPERTY_AREA), self)
        area_label.setObjectName("InfoLabel")
        layout.addWidget(area_label, 0, 0)

        self.area_value_label = QLabel(self._format_area_display(area_dict.get("size"), unit_value), self)
        layout.addWidget(self.area_value_label, 0, 1)

        price_label = QLabel(self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_PROPERTY_PRICE), self)
        price_label.setObjectName("InfoLabel")
        layout.addWidget(price_label, 0, 2)

        self.price_spin = QDoubleSpinBox(self)
        self.price_spin.setDecimals(2)
        self.price_spin.setRange(0.0, 100000000.0)
        self.price_spin.setSingleStep(0.5)
        self.price_spin.setSpecialValueText("–")
        self.price_spin.setValue(float(price_dict.get("amount") or 0.0))
        layout.addWidget(self.price_spin, 0, 3)

        self.payable_checkbox = QCheckBox(
            self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_PROPERTY_PAYABLE),
            self,
        )
        self.payable_checkbox.setChecked(is_payable)
        layout.addWidget(self.payable_checkbox, 0, 4)

        if is_payable:
            total_title = QLabel(self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_PROPERTY_TOTAL), self)
            total_title.setObjectName("InfoLabel")
            layout.addWidget(total_title, 0, 5)

            total_amount = total_dict.get("amount")
            if total_amount in (None, ""):
                area_size = self._coerce_float(area_dict.get("size"))
                price_amount = self._coerce_float(price_dict.get("amount"))
                if area_size is not None and price_amount is not None:
                    total_amount = area_size * price_amount
            self._current_total_text = self._format_money_display(total_amount, total_currency_code)
            self.total_label = QLabel(self._current_total_text, self)
            layout.addWidget(self.total_label, 0, 6)

            next_payment_label = QLabel(
                self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_PROPERTY_NEXT_PAYMENT),
                self,
            )
            next_payment_label.setObjectName("InfoLabel")
            layout.addWidget(next_payment_label, 1, 0)

            self.next_payment_edit = QLineEdit(self)
            self.next_payment_edit.setPlaceholderText(
                self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_PROPERTY_DATE_PLACEHOLDER)
            )
            self.next_payment_edit.setText(self._current_next_payment_text)
            layout.addWidget(self.next_payment_edit, 1, 1, 1, 2)

        if not self._read_only:
            unit_label = QLabel(self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_PROPERTY_UNIT), self)
            unit_label.setObjectName("InfoLabel")
            layout.addWidget(unit_label, 0, 7)

            self.unit_combo = QComboBox(self)
            for unit_option, unit_label_text in self._area_unit_labels.items():
                self.unit_combo.addItem(unit_label_text, unit_option)
            self.unit_combo.setCurrentIndex(max(0, self.unit_combo.findData(unit_value)))
            layout.addWidget(self.unit_combo, 0, 8)

            currency_label = QLabel(self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_PROPERTY_CURRENCY), self)
            currency_label.setObjectName("InfoLabel")
            layout.addWidget(currency_label, 1, 3)

            self.currency_combo = QComboBox(self)
            self.currency_combo.addItem(currency_code, currency_code)
            if currency_code != self._default_currency:
                self.currency_combo.addItem(self._default_currency, self._default_currency)
            self.currency_combo.setCurrentIndex(max(0, self.currency_combo.findData(currency_code)))
            layout.addWidget(self.currency_combo, 1, 4)

        self.price_spin.valueChanged.connect(self.totalsChanged.emit)
        if hasattr(self, "currency_combo"):
            self.currency_combo.currentIndexChanged.connect(self.totalsChanged.emit)
        if hasattr(self, "unit_combo"):
            self.unit_combo.currentIndexChanged.connect(self._emit_unit_changed)

        if self._read_only:
            self._apply_read_only_mode()

    def _emit_unit_changed(self, _index: int) -> None:
        self.unitChanged.emit()

    def current_unit(self) -> str:
        if hasattr(self, "unit_combo"):
            return str(self.unit_combo.currentData() or AreaUnit.M)
        return str(getattr(self, "_current_unit_value", AreaUnit.M) or AreaUnit.M)

    def price_value(self) -> float:
        return float(self.price_spin.value())

    def currency_code(self) -> str:
        if hasattr(self, "currency_combo"):
            return str(self.currency_combo.currentData() or self._default_currency)
        return str(getattr(self, "_current_currency_code", self._default_currency) or self._default_currency)

    def is_payable(self) -> bool:
        return bool(self.payable_checkbox.isChecked())

    def next_payment_text(self) -> str:
        if hasattr(self, "next_payment_edit"):
            return str(self.next_payment_edit.text() or "").strip()
        return str(getattr(self, "_current_next_payment_text", "") or "").strip()

    def set_area_display(self, text: str) -> None:
        self.area_value_label.setText(str(text or ""))

    def set_total_display(self, text: str) -> None:
        self._current_total_text = str(text or "")
        if hasattr(self, "total_label"):
            self.total_label.setText(self._current_total_text)
