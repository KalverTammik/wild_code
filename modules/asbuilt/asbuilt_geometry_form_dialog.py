from __future__ import annotations

from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from ...constants.button_props import ButtonVariant
from ...constants.file_paths import QssPaths
from ...widgets.theme_manager import ThemeManager


class AsBuiltGeometryFormDialog(QDialog):
    NETWORK_FIELDS = (
        ("Vesi", "Vesi"),
        ("Kanal", "Kanal"),
        ("Sadevesi", "Sadevesi"),
        ("Elekter ja tänavavalgustus", "Elekter ja tänavavalgustus"),
        ("Gaas", "Gaas"),
        ("Side", "Side"),
    )

    def __init__(self, *, item_data: dict | None = None, parent=None) -> None:
        super().__init__(parent)
        self._item_data = item_data if isinstance(item_data, dict) else {}
        self._network_checks: dict[str, QCheckBox] = {}

        self.setObjectName("AsBuiltGeometryFormDialog")
        self.setModal(True)
        self.setWindowTitle("Teostusjoonise andmed")
        self.resize(620, 520)

        self._build_ui()
        ThemeManager.apply_module_style(self, [QssPaths.MAIN, QssPaths.BUTTONS, QssPaths.MODULE_INFO])

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        title = QLabel("Teostusjoonise andmed", self)
        title.setObjectName("ExtraInfoDialogTitle")
        root.addWidget(title)

        intro = QLabel(
            "Täida kaardile joonistatud teostusjoonise ala põhiandmed. "
            "Need väärtused salvestatakse QGIS kihile enne backend geomeetria uuendamist.",
            self,
        )
        intro.setWordWrap(True)
        root.addWidget(intro)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(8)

        self._work_number = QLineEdit(self)
        self._work_number.setText(self._default_work_number())
        form.addRow("Töö nr", self._work_number)

        self._object = QLineEdit(self)
        self._object.setText(self._default_object())
        form.addRow("Objekt", self._object)

        self._survey_date = QDateEdit(self)
        self._survey_date.setCalendarPopup(True)
        self._survey_date.setDisplayFormat("yyyy-MM-dd")
        self._survey_date.setDate(QDate.currentDate())
        form.addRow("Mõõdistamise kpv", self._survey_date)

        self._surveyor = QLineEdit(self)
        form.addRow("Mõõdistaja", self._surveyor)

        self._contact = QLineEdit(self)
        form.addRow("Kontakt", self._contact)

        self._drawing_type = QComboBox(self)
        self._drawing_type.addItem("Teostusjoonis", "TJ")
        self._drawing_type.addItem("Geoalus", "GEOALUS")
        form.addRow("Joonis", self._drawing_type)

        self._scale = QComboBox(self)
        self._scale.addItem("1:500", "500")
        self._scale.addItem("1:1000", "1000")
        form.addRow("Mõõtkava", self._scale)

        self._coordinate_system = QComboBox(self)
        self._coordinate_system.addItem("L-EST97", "L-EST97")
        self._coordinate_system.addItem("Tartu kohalik", "Tartu")
        form.addRow("Koordinaatsüsteem", self._coordinate_system)

        self._height_system = QComboBox(self)
        self._height_system.addItem("EH2000", "EH2000")
        form.addRow("Kõrgussüsteem", self._height_system)

        root.addLayout(form)

        network_group = QGroupBox("Võrk", self)
        network_layout = QHBoxLayout(network_group)
        network_layout.setContentsMargins(10, 8, 10, 8)
        network_layout.setSpacing(10)
        for field_name, label in self.NETWORK_FIELDS:
            checkbox = QCheckBox(label, network_group)
            self._network_checks[field_name] = checkbox
            network_layout.addWidget(checkbox)
        network_layout.addStretch(1)
        root.addWidget(network_group)

        self._notes = QTextEdit(self)
        self._notes.setAcceptRichText(False)
        self._notes.setPlaceholderText("Mõõdistaja märkused")
        self._notes.setFixedHeight(80)
        root.addWidget(self._notes)

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

    def values(self) -> dict[str, object]:
        values: dict[str, object] = {
            "Töö nr": self._work_number.text().strip(),
            "Objekt": self._object.text().strip(),
            "Mõõdistamise kpv": self._survey_date.date().toString("yyyy-MM-dd"),
            "Mõõdistaja": self._surveyor.text().strip(),
            "Kontakt": self._contact.text().strip(),
            "Joonis": self._drawing_type.currentData(),
            "Mõõtkava": self._scale.currentData(),
            "Koordinaatsüsteem": self._coordinate_system.currentData(),
            "Kõrgussüsteem": self._height_system.currentData(),
            "Mõõdistaja, märkused": self._notes.toPlainText().strip(),
        }
        for field_name, checkbox in self._network_checks.items():
            values[field_name] = checkbox.isChecked()
        return values

    @classmethod
    def prompt(cls, *, item_data: dict | None = None, parent=None) -> dict[str, object] | None:
        dialog = cls(item_data=item_data, parent=parent)
        return dialog.values() if dialog.exec_() == QDialog.Accepted else None

    def _default_work_number(self) -> str:
        payload = self._item_data
        return str(payload.get("number") or payload.get("workNumber") or payload.get("id") or "").strip()

    def _default_object(self) -> str:
        payload = self._item_data
        return str(payload.get("name") or payload.get("title") or "").strip()
