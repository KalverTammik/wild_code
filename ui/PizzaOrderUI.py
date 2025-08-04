from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox
from ..widgets.theme_manager import ThemeManager
from ..constants.file_paths import FilePaths  # Use FilePaths for theme paths
from ..constants.file_paths import FilePaths  # Import FilePaths for user manual path
class PizzaOrderUI(QWidget):
    """
    UI for pizza ordering process.
    """


    def __init__(self):
        super().__init__()
        self.themeManager = ThemeManager()
        self.helpBtn = QPushButton("Help")
        self.initUI()

    def initUI(self):
        theme_path = FilePaths.get_file_path(FilePaths.LIGHT_THEME)  # Use FilePaths for the theme path
        self.themeManager.apply_theme(self, theme_path)
        mainLayout = QVBoxLayout(self)

        # Top horizontal layout for Help button
        topLayout = QHBoxLayout()
        topLayout.addWidget(self.helpBtn)
        topLayout.addStretch(1)
        mainLayout.addLayout(topLayout)

        header = QGroupBox("Pizza Order Process")
        headerLayout = QHBoxLayout()
        headerLayout.addWidget(QLabel("Step-by-step pizza order simulation"))
        header.setLayout(headerLayout)
        mainLayout.addWidget(header)

        self.statusLabel = QLabel("Status: Ready")
        self.statusLabel.setObjectName("statusLabel")

        # Buttons for each BPMN step
        self.placeOrderBtn = QPushButton("Place Order")
        self.confirmOrderBtn = QPushButton("Confirm Order")
        self.checkInventoryBtn = QPushButton("Check Inventory")
        self.preparePizzaBtn = QPushButton("Prepare Pizza")
        self.packPizzaBtn = QPushButton("Pack Pizza")
        self.deliverPizzaBtn = QPushButton("Deliver Pizza")
        self.confirmDeliveryBtn = QPushButton("Confirm Delivery")
        self.sendFailureNoticeBtn = QPushButton("Send Failure Notice")

        # Group buttons
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.placeOrderBtn)
        buttonLayout.addWidget(self.confirmOrderBtn)
        buttonLayout.addWidget(self.checkInventoryBtn)
        buttonLayout.addWidget(self.preparePizzaBtn)
        buttonLayout.addWidget(self.packPizzaBtn)
        buttonLayout.addWidget(self.deliverPizzaBtn)
        buttonLayout.addWidget(self.confirmDeliveryBtn)
        buttonLayout.addWidget(self.sendFailureNoticeBtn)

        mainLayout.addWidget(self.statusLabel)
        mainLayout.addLayout(buttonLayout)
        self.setLayout(mainLayout)

        # Connect signals and slots
        self.helpBtn.clicked.connect(self.showUserManual)

    def showUserManual(self):
        import os
        from PyQt5.QtWidgets import QDialog, QTextBrowser, QVBoxLayout
        manual_path = FilePaths.get_file_path(FilePaths.user_manual)
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
