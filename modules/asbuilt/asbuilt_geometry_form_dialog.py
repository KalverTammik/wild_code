from __future__ import annotations

from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...constants.button_props import ButtonVariant
from ...constants.file_paths import QssPaths
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...widgets.form_grid import CompactTextEdit, StackedFormGrid, fit_dialog_to_content
from ...widgets.theme_manager import ThemeManager


class AsBuiltGeometryFormDialog(QDialog):
    DIALOG_WIDTH = 620
    NETWORK_COLUMNS = 3
    # Layer field name and the translation key of its label.
    NETWORK_FIELDS = (
        ("Vesi", TranslationKeys.ASBUILT_NETWORK_WATER),
        ("Kanal", TranslationKeys.ASBUILT_NETWORK_SEWER),
        ("Sadevesi", TranslationKeys.ASBUILT_NETWORK_STORMWATER),
        ("Elekter ja tänavavalgustus", TranslationKeys.ASBUILT_NETWORK_ELECTRICITY),
        ("Gaas", TranslationKeys.ASBUILT_NETWORK_GAS),
        ("Side", TranslationKeys.ASBUILT_NETWORK_TELECOM),
    )

    def __init__(self, *, item_data: dict | None = None, lang_manager=None, parent=None) -> None:
        super().__init__(parent)
        self._lang = lang_manager or LanguageManager()
        self._item_data = item_data if isinstance(item_data, dict) else {}
        self._network_checks: dict[str, QCheckBox] = {}

        self.setObjectName("AsBuiltGeometryFormDialog")
        self.setModal(True)
        self.setWindowTitle(self._lang.translate(TranslationKeys.ASBUILT_FORM_TITLE))

        self._build_ui()
        ThemeManager.apply_module_style(self, [QssPaths.MAIN, QssPaths.BUTTONS, QssPaths.MODULE_INFO])
        for combo in self.findChildren(QComboBox):
            ThemeManager.apply_form_combo_popup_style(combo)
        fit_dialog_to_content(self, self.DIALOG_WIDTH)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        intro = QLabel(self._lang.translate(TranslationKeys.ASBUILT_FORM_INTRO), self)
        intro.setWordWrap(True)
        root.addWidget(intro)

        form = StackedFormGrid()
        translate = self._lang.translate

        # Created in display order: the Tab key follows creation order.
        self._work_number = QLineEdit(self)
        self._work_number.setText(self._default_work_number())
        self._object = QLineEdit(self)
        self._object.setText(self._default_object())
        form.add_fields(
            (translate(TranslationKeys.ASBUILT_FIELD_WORK_NUMBER), self._work_number, 4),
            (translate(TranslationKeys.ASBUILT_FIELD_OBJECT), self._object, 8),
        )

        self._survey_date = QDateEdit(self)
        self._survey_date.setCalendarPopup(True)
        self._survey_date.setDisplayFormat("yyyy-MM-dd")
        self._survey_date.setDate(QDate.currentDate())
        self._surveyor = QLineEdit(self)
        self._contact = QLineEdit(self)
        form.add_fields(
            (translate(TranslationKeys.ASBUILT_FIELD_SURVEY_DATE), self._survey_date, 4),
            (translate(TranslationKeys.ASBUILT_FIELD_SURVEYOR), self._surveyor, 4),
            (translate(TranslationKeys.ASBUILT_FIELD_CONTACT), self._contact, 4),
        )

        form.add_separator()

        self._drawing_type = QComboBox(self)
        self._drawing_type.addItem(translate(TranslationKeys.ASBUILT_DRAWING_ASBUILT), "TJ")
        self._drawing_type.addItem(translate(TranslationKeys.ASBUILT_DRAWING_BASE), "GEOALUS")
        self._scale = QComboBox(self)
        self._scale.addItem("1:500", "500")
        self._scale.addItem("1:1000", "1000")
        self._coordinate_system = QComboBox(self)
        self._coordinate_system.addItem("L-EST97", "L-EST97")
        self._coordinate_system.addItem(translate(TranslationKeys.ASBUILT_COORDINATES_TARTU), "Tartu")
        self._height_system = QComboBox(self)
        self._height_system.addItem("EH2000", "EH2000")
        form.add_fields(
            (translate(TranslationKeys.ASBUILT_FIELD_DRAWING), self._drawing_type, 3),
            (translate(TranslationKeys.ASBUILT_FIELD_SCALE), self._scale, 3),
            (translate(TranslationKeys.ASBUILT_FIELD_COORDINATE_SYSTEM), self._coordinate_system, 3),
            (translate(TranslationKeys.ASBUILT_FIELD_HEIGHT_SYSTEM), self._height_system, 3),
        )

        form.add_separator()

        network = QWidget(self)
        network_layout = QGridLayout(network)
        network_layout.setContentsMargins(0, 0, 0, 0)
        # Equal columns with the form's spacing: the boxes line up with the fields of a row of three.
        network_layout.setHorizontalSpacing(StackedFormGrid.SPACING)
        network_layout.setVerticalSpacing(6)
        for column in range(self.NETWORK_COLUMNS):
            network_layout.setColumnStretch(column, 1)
        for index, (field_name, label_key) in enumerate(self.NETWORK_FIELDS):
            checkbox = QCheckBox(translate(label_key), network)
            self._network_checks[field_name] = checkbox
            network_layout.addWidget(checkbox, index // self.NETWORK_COLUMNS, index % self.NETWORK_COLUMNS)
        form.add_fields((translate(TranslationKeys.ASBUILT_FIELD_NETWORK), network, 12))

        self._notes = CompactTextEdit(self)
        self._notes.setAcceptRichText(False)
        self._notes.setPlaceholderText(translate(TranslationKeys.ASBUILT_FORM_NOTES_PLACEHOLDER))
        self._notes.setMinimumHeight(80)
        form.add_text_area(translate(TranslationKeys.ASBUILT_FIELD_NOTES), self._notes)

        root.addLayout(form, 1)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        buttons.addStretch(1)

        cancel_btn = QPushButton(translate(TranslationKeys.GEOMETRY_FORM_CANCEL), self)
        cancel_btn.setProperty("variant", ButtonVariant.GHOST)
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)

        save_btn = QPushButton(translate(TranslationKeys.SAVE), self)
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
