from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QDialog, QTextBrowser, QLabel, QHBoxLayout
import os

class PizzaOrderUI(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pizza Order Module")
        self.setMinimumSize(400, 300)

        # Define buttons and other UI elements
        self.placeOrderBtn = QPushButton("Place Order")
        self.confirmOrderBtn = QPushButton("Confirm Order")
        self.checkInventoryBtn = QPushButton("Check Inventory")
        self.preparePizzaBtn = QPushButton("Prepare Pizza")
        self.packPizzaBtn = QPushButton("Pack Pizza")
        self.deliverPizzaBtn = QPushButton("Deliver Pizza")
        self.confirmDeliveryBtn = QPushButton("Confirm Delivery")
        self.sendFailureNoticeBtn = QPushButton("Send Failure Notice")
        self.helpBtn = QPushButton("Help")
        self.statusLabel = QLabel("Status: Ready")  # Add a status label

        # Top horizontal layout for Help button
        topLayout = QHBoxLayout()
        topLayout.addWidget(self.helpBtn)
        topLayout.addStretch(1)

        # Main vertical layout
        layout = QVBoxLayout()
        layout.addLayout(topLayout)  # Add Help button row at the very top
        layout.addWidget(self.placeOrderBtn)
        layout.addWidget(self.confirmOrderBtn)
        layout.addWidget(self.checkInventoryBtn)
        layout.addWidget(self.preparePizzaBtn)
        layout.addWidget(self.packPizzaBtn)
        layout.addWidget(self.deliverPizzaBtn)
        layout.addWidget(self.confirmDeliveryBtn)
        layout.addWidget(self.sendFailureNoticeBtn)
        layout.addWidget(self.statusLabel)  # Add status label at the bottom
        self.setLayout(layout)

        # Connect signals and slots
        self.helpBtn.clicked.connect(self.showUserManual)

    def showUserManual(self):
        manual_path = os.path.join(
            os.path.dirname(__file__),
            "PizzaOrderModuleUserManual.html"
        )
        dlg = QDialog(self)
        dlg.setWindowTitle("Pizza Order Module - User Manual")
        dlg.resize(600, 500)
        browser = QTextBrowser(dlg)
        browser.setOpenExternalLinks(True)
        if os.path.exists(manual_path):
            with open(manual_path, "r", encoding="utf-8") as f:
                browser.setHtml(f.read())
        else:
            browser.setText("User manual not found.")
        layout = QVBoxLayout(dlg)
        layout.addWidget(browser)
        dlg.setLayout(layout)
        dlg.exec_()