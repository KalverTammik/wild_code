from __future__ import annotations

from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ...constants.button_props import ButtonVariant
from ...constants.file_paths import QssPaths
from ...widgets.theme_manager import ThemeManager


class EasementGeometryFormDialog(QDialog):
    FIELD_KIND = "Liik"
    FIELD_STATUS = "Staatus"
    FIELD_NOTARY_NUMBER = "Notari reg nr"
    FIELD_LAND_OWNER = "Maa omanik"
    FIELD_CADASTRAL = "Katastritunnus"
    FIELD_PHONE = "Telefon"
    FIELD_EMAIL = "E-kiri"
    FIELD_NOTE = "Märkus"
    FIELD_ESTABLISHED_DATE = "Kehtestamise kuupäev"
    FIELD_SOURCE = "Allikas"
    FIELD_NETWORK = "Võrk"
    FIELD_PROTECTION_WIDTH = "Kaitsevööndi laius"
    FIELD_COMPENSATION = "Talumistasu"
    FIELD_MUNICIPALITY = "Vald"
    FIELD_REGION = "Piirkond"
    FIELD_ADDRESS = "Aadress"
    FIELD_HOUSE_NUMBER = "Maja nr"

    def __init__(
        self,
        *,
        item_data: dict | None = None,
        initial_values: dict | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._item_data = item_data if isinstance(item_data, dict) else {}
        self._initial_values = initial_values if isinstance(initial_values, dict) else {}

        self.setObjectName("EasementGeometryFormDialog")
        self.setModal(True)
        self.setWindowTitle("Servituudi ala andmed")
        self.resize(620, 520)

        self._build_ui()
        self._apply_defaults()
        ThemeManager.apply_module_style(self, [QssPaths.MAIN, QssPaths.BUTTONS, QssPaths.MODULE_INFO])

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        title = QLabel("Servituudi ala andmed", self)
        title.setObjectName("ExtraInfoDialogTitle")
        root.addWidget(title)

        intro = QLabel(
            "Täida servituudi ala kihiandmed enne ala salvestamist. "
            "Automaatika täidab seose, pindala ja logiväljad, kui need on arvutatavad.",
            self,
        )
        intro.setWordWrap(True)
        root.addWidget(intro)

        tabs = QTabWidget(self)
        tabs.addTab(self._build_data_tab(), "Andmed")
        tabs.addTab(self._build_location_tab(), "Asukoht")
        root.addWidget(tabs, 1)

        buttons = QHBoxLayout()
        buttons.addStretch(1)

        cancel_btn = QPushButton("Katkesta", self)
        cancel_btn.setProperty("variant", ButtonVariant.GHOST)
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)

        save_btn = QPushButton("Salvesta", self)
        save_btn.setProperty("variant", ButtonVariant.SUCCESS)
        save_btn.clicked.connect(self.accept)
        buttons.addWidget(save_btn)

        for button in (cancel_btn, save_btn):
            button.setAutoDefault(False)
            button.setDefault(False)

        root.addLayout(buttons)

    def _build_data_tab(self) -> QWidget:
        tab = QWidget(self)
        form = QFormLayout(tab)
        form.setContentsMargins(0, 8, 0, 0)
        form.setSpacing(8)

        self._kind = QLineEdit(tab)
        form.addRow("Liik", self._kind)

        self._status = QComboBox(tab)
        self._status.setEditable(True)
        self._status.addItems(["Kehtestatud", "Ootel", "Puudub"])
        form.addRow("Staatus", self._status)

        self._notary_number = QLineEdit(tab)
        form.addRow("Notari reg nr", self._notary_number)

        self._land_owner = QLineEdit(tab)
        form.addRow("Maa omanik", self._land_owner)

        self._cadastral = QLineEdit(tab)
        form.addRow("Katastritunnus", self._cadastral)

        self._phone = QLineEdit(tab)
        form.addRow("Telefon", self._phone)

        self._email = QLineEdit(tab)
        form.addRow("E-kiri", self._email)

        self._established_date = QDateEdit(tab)
        self._established_date.setCalendarPopup(True)
        self._established_date.setDisplayFormat("yyyy-MM-dd")
        self._established_date.setSpecialValueText("")
        self._established_date.setDate(QDate.currentDate())
        form.addRow("Kehtestamise kuupäev", self._established_date)

        self._source = QLineEdit(tab)
        form.addRow("Allikas", self._source)

        self._network = QLineEdit(tab)
        form.addRow("Võrk", self._network)

        self._protection_width = QLineEdit(tab)
        form.addRow("Kaitsevööndi laius", self._protection_width)

        self._compensation = QLineEdit(tab)
        form.addRow("Talumistasu", self._compensation)

        self._note = QTextEdit(tab)
        self._note.setAcceptRichText(False)
        self._note.setFixedHeight(76)
        form.addRow("Märkus", self._note)

        return tab

    def _build_location_tab(self) -> QWidget:
        tab = QWidget(self)
        form = QFormLayout(tab)
        form.setContentsMargins(0, 8, 0, 0)
        form.setSpacing(8)

        self._municipality = QLineEdit(tab)
        form.addRow("Vald", self._municipality)

        self._region = QLineEdit(tab)
        form.addRow("Piirkond", self._region)

        self._address = QLineEdit(tab)
        form.addRow("Aadress", self._address)

        self._house_number = QLineEdit(tab)
        form.addRow("Maja nr", self._house_number)

        self._payable = QCheckBox("Talumistasu arvestatakse", tab)
        form.addRow("", self._payable)

        return tab

    def _apply_defaults(self) -> None:
        item = self._item_data
        values = self._initial_values

        self._set_line(self._kind, values.get(self.FIELD_KIND) or ((item.get("type") or {}).get("name") if isinstance(item.get("type"), dict) else ""))
        self._set_combo_text(self._status, values.get(self.FIELD_STATUS) or ((item.get("status") or {}).get("name") if isinstance(item.get("status"), dict) else "") or "Ootel")
        self._set_line(self._notary_number, values.get(self.FIELD_NOTARY_NUMBER))
        self._set_line(self._land_owner, values.get(self.FIELD_LAND_OWNER))
        self._set_line(self._cadastral, values.get(self.FIELD_CADASTRAL))
        self._set_line(self._phone, values.get(self.FIELD_PHONE))
        self._set_line(self._email, values.get(self.FIELD_EMAIL))
        self._set_line(self._source, values.get(self.FIELD_SOURCE) or "Kavitro")
        self._set_line(self._network, values.get(self.FIELD_NETWORK))
        self._set_line(self._protection_width, values.get(self.FIELD_PROTECTION_WIDTH))
        self._set_line(self._compensation, values.get(self.FIELD_COMPENSATION))
        self._note.setPlainText(str(values.get(self.FIELD_NOTE) or ""))
        self._set_line(self._municipality, values.get(self.FIELD_MUNICIPALITY))
        self._set_line(self._region, values.get(self.FIELD_REGION))
        self._set_line(self._address, values.get(self.FIELD_ADDRESS))
        self._set_line(self._house_number, values.get(self.FIELD_HOUSE_NUMBER))

        established = str(values.get(self.FIELD_ESTABLISHED_DATE) or "").strip()
        if established:
            parsed = QDate.fromString(established, "yyyy-MM-dd")
            if parsed.isValid():
                self._established_date.setDate(parsed)

    @staticmethod
    def _set_line(widget: QLineEdit, value) -> None:
        widget.setText(str(value or "").strip())

    @staticmethod
    def _set_combo_text(widget: QComboBox, value) -> None:
        text = str(value or "").strip()
        if not text:
            return
        index = widget.findText(text)
        if index >= 0:
            widget.setCurrentIndex(index)
        else:
            widget.setEditText(text)

    def values(self) -> dict[str, object]:
        status = self._status.currentText().strip()
        has_initial_established_date = bool(str(self._initial_values.get(self.FIELD_ESTABLISHED_DATE) or "").strip())
        established_date = self._established_date.date().toString("yyyy-MM-dd") if status == "Kehtestatud" or has_initial_established_date else ""
        return {
            self.FIELD_KIND: self._kind.text().strip(),
            self.FIELD_STATUS: status,
            self.FIELD_NOTARY_NUMBER: self._notary_number.text().strip(),
            self.FIELD_LAND_OWNER: self._land_owner.text().strip(),
            self.FIELD_CADASTRAL: self._cadastral.text().strip(),
            self.FIELD_PHONE: self._phone.text().strip(),
            self.FIELD_EMAIL: self._email.text().strip(),
            self.FIELD_NOTE: self._note.toPlainText().strip(),
            self.FIELD_ESTABLISHED_DATE: established_date,
            self.FIELD_SOURCE: self._source.text().strip(),
            self.FIELD_NETWORK: self._network.text().strip(),
            self.FIELD_PROTECTION_WIDTH: self._protection_width.text().strip(),
            self.FIELD_COMPENSATION: self._compensation.text().strip(),
            self.FIELD_MUNICIPALITY: self._municipality.text().strip(),
            self.FIELD_REGION: self._region.text().strip(),
            self.FIELD_ADDRESS: self._address.text().strip(),
            self.FIELD_HOUSE_NUMBER: self._house_number.text().strip(),
            "Talumistasu arvestatakse": self._payable.isChecked(),
        }

    @classmethod
    def prompt(
        cls,
        *,
        item_data: dict | None = None,
        initial_values: dict | None = None,
        parent=None,
    ) -> dict[str, object] | None:
        dialog = cls(item_data=item_data, initial_values=initial_values, parent=parent)
        return dialog.values() if dialog.exec_() == QDialog.Accepted else None
