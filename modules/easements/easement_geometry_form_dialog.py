from __future__ import annotations

from typing import Callable

from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import (
    QDateEdit,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ...constants.button_props import ButtonVariant
from ...constants.file_paths import QssPaths
from ...python.api_actions import APIModuleActions
from ...utils.messagesHelper import ModernMessageDialog
from ...utils.url_manager import Module
from ...widgets.form_grid import CompactTextEdit, StackedFormGrid, fit_dialog_to_content
from ...widgets.status_select_widget import StatusSelectWidget
from ...widgets.theme_manager import ThemeManager
from .easement_layer_service import EasementLayerService


def _status_id(status) -> str:
    return str(status.get("id") or "").strip() if isinstance(status, dict) else ""


class EasementGeometryFormDialog(QDialog):
    DIALOG_WIDTH = 620
    STATUS_ESTABLISHED = "Kehtestatud"

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
        status_options: list[dict] | None = None,
        current_status: dict | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._item_data = item_data if isinstance(item_data, dict) else {}
        self._initial_values = initial_values if isinstance(initial_values, dict) else {}
        self._status_options = list(status_options or [])
        # Read from Kavitro as the form opens; the card's copy is used when that failed.
        own_status = current_status if _status_id(current_status) else self._item_data.get("status")
        self._kavitro_status = dict(own_status) if _status_id(own_status) else {}

        self.setObjectName("EasementGeometryFormDialog")
        self.setModal(True)
        self.setWindowTitle("Servituudi ala andmed")

        self._build_ui()
        self._apply_defaults()
        self._on_status_changed()
        self._status.currentChanged.connect(self._on_status_changed)
        ThemeManager.apply_module_style(self, [QssPaths.MAIN, QssPaths.BUTTONS, QssPaths.MODULE_INFO])
        self._status.set_control_height(self._kind.sizeHint().height())
        fit_dialog_to_content(self, self.DIALOG_WIDTH)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        intro = QLabel(
            "Täida servituudi ala kihiandmed enne ala salvestamist. Muudetud staatus salvestatakse ka Kavitrosse. "
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
        buttons.setSpacing(8)
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
        form = StackedFormGrid(tab)
        form.setContentsMargins(0, 12, 0, 0)

        # Created in display order: the Tab key follows creation order.
        self._kind = QLineEdit(tab)
        self._status = StatusSelectWidget(tab)
        self._status.setToolTip("Muudetud staatus salvestatakse Kavitrosse ja kaardikihile.")
        _, self._status_label = form.add_fields(
            (self.FIELD_KIND, self._kind, 6),
            (self.FIELD_STATUS, self._status, 6),
        )
        # The label also names the map value, and that text must not move the other fields.
        self._status_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)

        self._established_date = QDateEdit(tab)
        self._established_date.setCalendarPopup(True)
        self._established_date.setDisplayFormat("yyyy-MM-dd")
        # Shown at the minimum date: a date that will not be saved is left blank.
        self._established_date.setSpecialValueText(" ")
        self._established_date.setDate(QDate.currentDate())
        self._established_date.setToolTip(f"Kuupäev salvestatakse, kui staatusele vastab kihil väärtus {self.STATUS_ESTABLISHED}.")
        self._notary_number = QLineEdit(tab)
        self._source = QLineEdit(tab)
        form.add_fields(
            (self.FIELD_ESTABLISHED_DATE, self._established_date, 4),
            (self.FIELD_NOTARY_NUMBER, self._notary_number, 4),
            (self.FIELD_SOURCE, self._source, 4),
        )

        form.add_separator()

        self._land_owner = QLineEdit(tab)
        self._phone = QLineEdit(tab)
        self._email = QLineEdit(tab)
        form.add_fields(
            (self.FIELD_LAND_OWNER, self._land_owner, 4),
            (self.FIELD_PHONE, self._phone, 4),
            (self.FIELD_EMAIL, self._email, 4),
        )

        form.add_separator()

        self._network = QLineEdit(tab)
        self._protection_width = QLineEdit(tab)
        self._compensation = QLineEdit(tab)
        form.add_fields(
            (self.FIELD_NETWORK, self._network, 4),
            (self.FIELD_PROTECTION_WIDTH, self._protection_width, 4),
            (self.FIELD_COMPENSATION, self._compensation, 4),
        )

        self._note = CompactTextEdit(tab)
        self._note.setAcceptRichText(False)
        self._note.setMinimumHeight(76)
        form.add_text_area(self.FIELD_NOTE, self._note)

        return tab

    def _build_location_tab(self) -> QWidget:
        tab = QWidget(self)
        form = StackedFormGrid(tab)
        form.setContentsMargins(0, 12, 0, 0)

        self._municipality = QLineEdit(tab)
        self._region = QLineEdit(tab)
        form.add_fields(
            (self.FIELD_MUNICIPALITY, self._municipality, 6),
            (self.FIELD_REGION, self._region, 6),
        )

        self._address = QLineEdit(tab)
        self._house_number = QLineEdit(tab)
        form.add_fields(
            (self.FIELD_ADDRESS, self._address, 9),
            (self.FIELD_HOUSE_NUMBER, self._house_number, 3),
        )

        # Full width: an area across several properties lists all of their numbers.
        self._cadastral = QLineEdit(tab)
        form.add_fields((self.FIELD_CADASTRAL, self._cadastral, 12))

        form.setRowStretch(form.rowCount(), 1)
        return tab

    def _layer_status(self) -> str:
        option = self._status.current_option()
        return EasementLayerService.map_backend_status_to_layer_value(option) if option else ""

    def _on_status_changed(self) -> None:
        layer_status = self._layer_status()
        if self._status.current_option() and not layer_status:
            label = f"{self.FIELD_STATUS} (kaardil ei muutu)"
        elif layer_status and layer_status != self._status.currentText():
            label = f"{self.FIELD_STATUS} (kaardil: {layer_status})"
        else:
            label = self.FIELD_STATUS
        self._status_label.setText(label)
        self._sync_established_date()

    def _established_date_is_saved(self) -> bool:
        has_initial_date = bool(str(self._initial_values.get(self.FIELD_ESTABLISHED_DATE) or "").strip())
        return self._layer_status() == self.STATUS_ESTABLISHED or has_initial_date

    def _sync_established_date(self) -> None:
        saved = self._established_date_is_saved()
        self._established_date.setEnabled(saved)
        minimum = self._established_date.minimumDate()
        if not saved:
            self._established_date.setDate(minimum)
        elif self._established_date.date() == minimum:
            self._established_date.setDate(QDate.currentDate())

    def _apply_defaults(self) -> None:
        item = self._item_data
        values = self._initial_values

        self._set_line(self._kind, values.get(self.FIELD_KIND) or ((item.get("type") or {}).get("name") if isinstance(item.get("type"), dict) else ""))
        self._fill_statuses()
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

    def _fill_statuses(self) -> None:
        current_id = _status_id(self._kavitro_status)
        options = list(self._status_options)
        # Also when the list failed to load: the easement's own status must not be replaced by another one.
        if current_id and not any(_status_id(option) == current_id for option in options):
            options.insert(0, dict(self._kavitro_status))
        self._status.set_options(options, selected_id=current_id)

    @staticmethod
    def _set_line(widget: QLineEdit, value) -> None:
        widget.setText(str(value or "").strip())
        # A value longer than its field shows from the start, not from the end.
        widget.setCursorPosition(0)

    def accept(self) -> None:
        # Kavitro first: if it does not take the new status, nothing reaches the map and the form stays open.
        if self._save_status_to_kavitro():
            super().accept()

    def _save_status_to_kavitro(self) -> bool:
        item_id = str(self._item_data.get("id") or "").strip()
        status_id = _status_id(self._status.current_option())
        if not item_id or not status_id or status_id == _status_id(self._kavitro_status):
            return True

        saved = APIModuleActions.update_easement_status(item_id, status_id)
        if saved is None:
            ModernMessageDialog.show_warning(
                "Staatust ei muudetud",
                "Kavitro ei võtnud uut staatust vastu, seega kaardile ei salvestatud midagi. "
                "Proovi uuesti või vali tagasi algne staatus.",
                parent=self,
            )
            return False

        self._kavitro_status = dict(saved)
        return True

    def kavitro_status(self) -> dict:
        """The status the easement has in Kavitro after this form; empty when it is not known."""
        return dict(self._kavitro_status)

    def values(self) -> dict[str, object]:
        established_date = self._established_date.date().toString("yyyy-MM-dd") if self._established_date_is_saved() else ""
        return {
            self.FIELD_KIND: self._kind.text().strip(),
            self.FIELD_STATUS: self._layer_status(),
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
        }

    @classmethod
    def prompt(
        cls,
        *,
        item_data: dict | None = None,
        initial_values: dict | None = None,
        parent=None,
        on_status_changed: Callable[[dict], None] | None = None,
    ) -> dict[str, object] | None:
        item = item_data if isinstance(item_data, dict) else {}
        # Read before the form opens: a slow answer would otherwise put its wait window over the form.
        # The status is read too, because the card can be older than a change made in Kavitro.
        status_options = APIModuleActions.get_module_status_options(Module.EASEMENT.value)
        current_status = APIModuleActions.get_easement_status(str(item.get("id") or ""))
        dialog = cls(
            item_data=item,
            initial_values=initial_values,
            status_options=status_options,
            current_status=current_status,
            parent=parent,
        )
        accepted = dialog.exec_() == QDialog.Accepted

        # Also after Cancel: the status read from Kavitro may be newer than the card's.
        status = dialog.kavitro_status()
        if callable(on_status_changed) and _status_id(status) and _status_id(status) != _status_id(item.get("status")):
            on_status_changed(status)
        return dialog.values() if accepted else None
