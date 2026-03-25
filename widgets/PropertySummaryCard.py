from __future__ import annotations

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from ..constants.cadastral_fields import Katastriyksus
from ..languages.MaaAmetFieldFormater import format_field


class PropertySummaryCard(QFrame):
    """Reusable property details card styled like the Property module header."""

    def __init__(self, parent=None, *, show_title: bool = False, title_text: str = "Kinnistu andmed"):
        super().__init__(parent)
        self.setObjectName("PropertyHeader")
        self.setFrameStyle(QFrame.StyledPanel)

        header_layout = QVBoxLayout(self)
        header_layout.setContentsMargins(6, 6, 6, 6)
        header_layout.setSpacing(6)

        if show_title:
            details_title = QLabel(title_text)
            details_title.setObjectName("DetailsTitle")
            title_font = QFont()
            title_font.setBold(True)
            title_font.setPointSize(11)
            details_title.setFont(title_font)
            header_layout.addWidget(details_title)

        details_frame = QFrame()
        details_frame.setObjectName("PropertyDetailsFrame")
        details_frame.setProperty("compact", True)
        details_frame.setFrameStyle(QFrame.StyledPanel)
        details_layout = QHBoxLayout(details_frame)
        details_layout.setContentsMargins(6, 6, 6, 6)
        details_layout.setSpacing(12)

        basic_frame = QFrame()
        basic_frame.setObjectName("BasicInfoFrame")
        basic_frame.setFrameStyle(QFrame.Box)
        basic_frame.setLineWidth(2)
        basic_layout = QVBoxLayout(basic_frame)
        basic_layout.setContentsMargins(3, 3, 3, 3)
        basic_layout.setSpacing(6)

        ids_layout = QHBoxLayout()
        tunnus_label = QLabel("Katastritunnus:")
        tunnus_label.setObjectName("InfoLabel")
        ids_layout.addWidget(tunnus_label)
        self.lbl_katastritunnus_value = QLabel("...")
        ids_layout.addWidget(self.lbl_katastritunnus_value)

        reg_label = QLabel("(reg.nr:)")
        reg_label.setObjectName("InfoLabel")
        ids_layout.addSpacing(3)
        ids_layout.addWidget(reg_label)
        self.lbl_kinnistu_value = QLabel("...")
        ids_layout.addWidget(self.lbl_kinnistu_value)
        ids_layout.addStretch()
        basic_layout.addLayout(ids_layout)

        address_layout = QHBoxLayout()
        address_label = QLabel("Aadress:")
        address_label.setObjectName("InfoLabel")
        address_layout.addWidget(address_label)
        self.lbl_address_value = QLabel("...")
        address_layout.addWidget(self.lbl_address_value)
        address_layout.addStretch()
        basic_layout.addLayout(address_layout)

        details_layout.addWidget(basic_frame)

        additional_frame = QFrame()
        additional_frame.setObjectName("AdditionalInfoFrame")
        additional_layout = QVBoxLayout(additional_frame)
        additional_layout.setContentsMargins(6, 6, 6, 6)
        additional_layout.setSpacing(6)

        pindala_layout = QHBoxLayout()
        pindala_label = QLabel("Pindala (m²):")
        pindala_label.setObjectName("InfoLabel")
        pindala_layout.addWidget(pindala_label)
        self.lbl_area_value = QLabel("0.00")
        pindala_layout.addWidget(self.lbl_area_value)
        pindala_layout.addStretch()
        additional_layout.addLayout(pindala_layout)

        siht_layouts = []
        for idx in range(1, 4):
            row = QHBoxLayout()
            label = QLabel(f"Siht {idx}:")
            label.setObjectName("InfoLabel")
            row.addWidget(label)
            value_label = QLabel("...")
            row.addWidget(value_label)
            row.addStretch()
            additional_layout.addLayout(row)
            siht_layouts.append((label, value_label))

        (self.lbl_siht1_label, self.lbl_siht1_value), (
            self.lbl_siht2_label, self.lbl_siht2_value), (
            self.lbl_siht3_label, self.lbl_siht3_value) = siht_layouts

        registr_layout = QHBoxLayout()
        registr_label = QLabel("Moodustatud:")
        registr_label.setObjectName("InfoLabel")
        registr_layout.addWidget(registr_label)
        self.lbl_registr_value = QLabel("...")
        registr_layout.addWidget(self.lbl_registr_value)
        registr_layout.addStretch()
        additional_layout.addLayout(registr_layout)

        muudet_layout = QHBoxLayout()
        muudet_label = QLabel("Viimati muudetud:")
        muudet_label.setObjectName("InfoLabel")
        muudet_layout.addWidget(muudet_label)
        self.lbl_muudet_value = QLabel("...")
        muudet_layout.addWidget(self.lbl_muudet_value)
        muudet_layout.addStretch()
        additional_layout.addLayout(muudet_layout)

        details_layout.addWidget(additional_frame)
        header_layout.addWidget(details_frame)

    @staticmethod
    def _is_not_null(value) -> bool:
        return value is not None and str(value).strip() and str(value).upper() != "NULL"

    @staticmethod
    def _update_siht_label(label_widget, value_widget, field_name, field_value, percentage_field, percentage_value):
        formatted_value = format_field(field_name, field_value)
        if formatted_value == "---":
            label_widget.hide()
            value_widget.hide()
            return

        percentage_text = format_field(percentage_field, percentage_value)
        suffix = f" {percentage_text}" if percentage_text != "---" else ""
        value_widget.setText(f"{formatted_value}{suffix}")
        label_widget.show()
        value_widget.show()

    def clear(self) -> None:
        self.lbl_katastritunnus_value.setText("—")
        self.lbl_kinnistu_value.setText("—")
        self.lbl_address_value.setText("—")
        self.lbl_area_value.setText("—")
        self.lbl_siht1_value.setText("—")
        self.lbl_siht2_value.setText("—")
        self.lbl_siht3_value.setText("—")
        self.lbl_registr_value.setText("—")
        self.lbl_muudet_value.setText("—")
        self.lbl_siht1_label.show()
        self.lbl_siht1_value.show()
        self.lbl_siht2_label.show()
        self.lbl_siht2_value.show()
        self.lbl_siht3_label.show()
        self.lbl_siht3_value.show()

    def set_feature(self, feature) -> None:
        if feature is None:
            self.clear()
            return

        try:
            katastritunnus = feature.attribute(Katastriyksus.tunnus)
            self.lbl_katastritunnus_value.setText(format_field(Katastriyksus.tunnus, katastritunnus))

            l_address = feature.attribute(Katastriyksus.l_aadress)
            ay_name = feature.attribute(Katastriyksus.ay_nimi)
            mk_name = feature.attribute(Katastriyksus.mk_nimi)
            address_parts = []
            if self._is_not_null(l_address):
                address_parts.append(str(l_address))
            if self._is_not_null(ay_name):
                address_parts.append(str(ay_name))
            if self._is_not_null(mk_name):
                address_parts.append(str(mk_name))
            self.lbl_address_value.setText(", ".join(address_parts) if address_parts else "...")

            area = feature.attribute(Katastriyksus.pindala)
            self.lbl_area_value.setText(format_field(Katastriyksus.pindala, area))

            self._update_siht_label(
                self.lbl_siht1_label,
                self.lbl_siht1_value,
                Katastriyksus.siht1,
                feature.attribute(Katastriyksus.siht1),
                Katastriyksus.so_prts1,
                feature.attribute(Katastriyksus.so_prts1),
            )
            self._update_siht_label(
                self.lbl_siht2_label,
                self.lbl_siht2_value,
                Katastriyksus.siht2,
                feature.attribute(Katastriyksus.siht2),
                Katastriyksus.so_prts2,
                feature.attribute(Katastriyksus.so_prts2),
            )
            self._update_siht_label(
                self.lbl_siht3_label,
                self.lbl_siht3_value,
                Katastriyksus.siht3,
                feature.attribute(Katastriyksus.siht3),
                Katastriyksus.so_prts3,
                feature.attribute(Katastriyksus.so_prts3),
            )

            self.lbl_registr_value.setText(format_field(Katastriyksus.registr, feature.attribute(Katastriyksus.registr)))
            self.lbl_muudet_value.setText(format_field(Katastriyksus.muudet, feature.attribute(Katastriyksus.muudet)))
            self.lbl_kinnistu_value.setText(format_field(Katastriyksus.kinnistu, feature.attribute(Katastriyksus.kinnistu)))
        except Exception:
            self.clear()