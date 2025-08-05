"""
Dialog UI for Hinnapakkuja module (hinnapakkumise koostaja)
"""
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QWidget
from PyQt5.QtCore import pyqtSignal

class HinnapakkujaDialog(QDialog):
    # Signals for actions
    inputSubmitted = pyqtSignal(dict)
    editRequested = pyqtSignal()
    exportRequested = pyqtSignal(str)
    saveRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HinnapakkujaDialog")
        self.setWindowTitle("Hinnapakkumise koostaja")
        self.setMinimumWidth(600)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        # Placeholder for dynamic content
        self.contentWidget = QWidget(self)
        self.layout.addWidget(self.contentWidget)
        # TODO: Add theme application via ThemeManager

    def setContentWidget(self, widget: QWidget):
        if self.contentWidget:
            self.layout.removeWidget(self.contentWidget)
            self.contentWidget.deleteLater()
        self.contentWidget = widget
        self.layout.insertWidget(0, self.contentWidget)
