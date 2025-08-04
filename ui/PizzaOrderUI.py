from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox
from ..widgets.theme_manager import ThemeManager
from ..constants.file_paths import FilePaths  # Use FilePaths for theme paths

class PizzaOrderUI(QWidget):
    """
    UI for pizza ordering process.
    """

    def __init__(self):
        super().__init__()
        self.themeManager = ThemeManager()
        self.initUI()

    def initUI(self):
        theme_path = FilePaths.get_file_path(FilePaths.LIGHT_THEME)  # Use FilePaths for the theme path
        self.themeManager.apply_theme(self,theme_path)
        mainLayout = QVBoxLayout(self)

        header = QGroupBox("Pizza Order Process")
        headerLayout = QHBoxLayout()
        headerLayout.addWidget(QLabel("Step-by-step pizza order simulation"))
        header.setLayout(headerLayout)

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

        mainLayout.addWidget(header)
        mainLayout.addWidget(self.statusLabel)
        mainLayout.addLayout(buttonLayout)
        self.setLayout(mainLayout)
