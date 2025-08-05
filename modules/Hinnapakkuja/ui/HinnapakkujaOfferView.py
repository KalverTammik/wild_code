"""
HTML offer popup for Hinnapakkuja module (output step)
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTextBrowser, QHBoxLayout
from PyQt5.QtCore import pyqtSignal

class HinnapakkujaOfferView(QWidget):
    exportRequested = pyqtSignal(str)
    editRequested = pyqtSignal()
    saveRequested = pyqtSignal()

    def __init__(self, html_content: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("HinnapakkujaOfferView")
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.htmlView = QTextBrowser(self)
        self.htmlView.setHtml(html_content)
        self.layout.addWidget(self.htmlView)
        # Button row
        self.buttonRow = QHBoxLayout()
        self.exportPdfBtn = QPushButton("Laadi alla PDF")
        self.exportPdfBtn.clicked.connect(lambda: self.exportRequested.emit("pdf"))
        self.exportExcelBtn = QPushButton("Laadi alla Excel")
        self.exportExcelBtn.clicked.connect(lambda: self.exportRequested.emit("excel"))
        self.editBtn = QPushButton("Muuda sisendit")
        self.editBtn.clicked.connect(self.editRequested.emit)
        self.saveBtn = QPushButton("Salvesta projekt")
        self.saveBtn.clicked.connect(self.saveRequested.emit)
        for btn in [self.exportPdfBtn, self.exportExcelBtn, self.editBtn, self.saveBtn]:
            self.buttonRow.addWidget(btn)
        self.layout.addLayout(self.buttonRow)

    def setHtmlContent(self, html: str):
        self.htmlView.setHtml(html)
