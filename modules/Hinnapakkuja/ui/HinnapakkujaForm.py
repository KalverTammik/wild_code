"""
Questionnaire form for Hinnapakkuja module (input step)
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QSpinBox, QCheckBox, QComboBox, QPushButton, QLabel, QHBoxLayout)
from PyQt5.QtCore import pyqtSignal

class HinnapakkujaForm(QWidget):
    formSubmitted = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HinnapakkujaForm")
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.formLayout = QFormLayout()
        self.layout.addLayout(self.formLayout)
        # Apartment count
        self.apartmentsSpin = QSpinBox()
        self.apartmentsSpin.setMinimum(1)
        self.formLayout.addRow("Korterite arv", self.apartmentsSpin)
        # Staircases
        self.staircasesSpin = QSpinBox()
        self.staircasesSpin.setMinimum(1)
        self.formLayout.addRow("Trepikodade arv", self.staircasesSpin)
        # Floors
        self.floorsSpin = QSpinBox()
        self.floorsSpin.setMinimum(1)
        self.formLayout.addRow("Korruste arv", self.floorsSpin)
        # Bathrooms
        self.bathroomsSpin = QSpinBox()
        self.bathroomsSpin.setMinimum(1)
        self.formLayout.addRow("Vannitubade arv tüüpkorteris", self.bathroomsSpin)
        # Separate WC
        self.separateWcCheck = QCheckBox("Eraldi WC olemas")
        self.formLayout.addRow(self.separateWcCheck)
        # Kitchen water point
        self.kitchenWaterCheck = QCheckBox("Köögis veepunkt")
        self.formLayout.addRow(self.kitchenWaterCheck)
        # Underfloor heating
        self.underfloorHeatingCheck = QCheckBox("Põrandaküte")
        self.formLayout.addRow(self.underfloorHeatingCheck)
        # Heating zones and collector branches
        self.heatingZonesSpin = QSpinBox()
        self.heatingZonesSpin.setMinimum(0)
        self.collectorBranchesSpin = QSpinBox()
        self.collectorBranchesSpin.setMinimum(0)
        self.formLayout.addRow("Kütetsoonide arv", self.heatingZonesSpin)
        self.formLayout.addRow("Kollektori harude arv", self.collectorBranchesSpin)
        # Supplier
        self.supplierCombo = QComboBox()
        self.supplierCombo.addItems(["FEB", "Onninen", "Tekamerk"])
        self.formLayout.addRow("Soovitav tarnija", self.supplierCombo)
        # Material type
        self.materialCombo = QComboBox()
        self.materialCombo.addItems(["PEX", "PE", "Multilayer"])
        self.formLayout.addRow("Materjalitüüp", self.materialCombo)
        # Add 10% reserve
        self.reserveCheck = QCheckBox("Lisa 10% varu")
        self.formLayout.addRow(self.reserveCheck)
        # Submit button
        self.submitBtn = QPushButton("Koosta pakkumus")
        self.submitBtn.setObjectName("PrimaryButton")
        self.submitBtn.clicked.connect(self.submitForm)
        self.layout.addWidget(self.submitBtn)

    def submitForm(self):
        data = {
            "apartments": self.apartmentsSpin.value(),
            "staircases": self.staircasesSpin.value(),
            "floors": self.floorsSpin.value(),
            "bathrooms": self.bathroomsSpin.value(),
            "separate_wc": self.separateWcCheck.isChecked(),
            "kitchen_water": self.kitchenWaterCheck.isChecked(),
            "underfloor_heating": self.underfloorHeatingCheck.isChecked(),
            "heating_zones": self.heatingZonesSpin.value(),
            "collector_branches": self.collectorBranchesSpin.value(),
            "supplier": self.supplierCombo.currentText(),
            "material": self.materialCombo.currentText(),
            "reserve": self.reserveCheck.isChecked()
        }
        self.formSubmitted.emit(data)
