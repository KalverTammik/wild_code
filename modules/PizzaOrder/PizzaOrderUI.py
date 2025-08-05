from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, QLineEdit, QTextEdit, QCheckBox, QHBoxLayout, QMessageBox
from ...languages.language_manager import LanguageManager
from ...widgets.theme_manager import ThemeManager
from .PizzaOrderLogic import PizzaOrderLogic

class PizzaOrderUI(QWidget):
    def __init__(self, lang_manager: LanguageManager, theme_manager: ThemeManager, theme_dir=None, qss_files=None):
        super().__init__()
        self.name = "PizzaOrderModule"
        self.lang_manager = lang_manager
        self.theme_manager = theme_manager
        from ...constants.file_paths import StylePaths
        self.theme_dir = theme_dir or StylePaths.DARK
        from ...constants.file_paths import QssPaths
        self.qss_files = qss_files or [QssPaths.MAIN, QssPaths.SIDEBAR]
        self.logic = PizzaOrderLogic()
        self.setup_ui()
        if self.theme_dir:
            self.theme_manager.apply_theme(self, self.theme_dir, qss_files=self.qss_files)
        else:
            raise ValueError("theme_dir must be provided to PizzaOrderUI for theme application.")

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.pizzaCombo = QComboBox()
        self.pizzaCombo.addItems([
            self.lang_manager.translate("pizza_margherita"),
            self.lang_manager.translate("pizza_pepperoni"),
            self.lang_manager.translate("pizza_veggie")
        ])
        self.toppingCheese = QCheckBox(self.lang_manager.translate("topping_cheese"))
        self.toppingMushrooms = QCheckBox(self.lang_manager.translate("topping_mushrooms"))
        self.toppingOlives = QCheckBox(self.lang_manager.translate("topping_olives"))
        self.nameEdit = QLineEdit()
        self.nameEdit.setPlaceholderText(self.lang_manager.translate("customer_name"))
        self.addressEdit = QTextEdit()
        self.addressEdit.setPlaceholderText(self.lang_manager.translate("customer_address"))
        self.orderButton = QPushButton(self.lang_manager.translate("order_button"))
        self.orderButton.clicked.connect(self.on_order)
        layout.addWidget(QLabel(self.lang_manager.translate("select_pizza")))
        layout.addWidget(self.pizzaCombo)
        layout.addWidget(QLabel(self.lang_manager.translate("select_toppings")))
        layout.addWidget(self.toppingCheese)
        layout.addWidget(self.toppingMushrooms)
        layout.addWidget(self.toppingOlives)
        layout.addWidget(QLabel(self.lang_manager.translate("customer_info")))
        layout.addWidget(self.nameEdit)
        layout.addWidget(self.addressEdit)
        layout.addWidget(self.orderButton)
        self.setLayout(layout)

    def on_order(self):
        pizza = self.pizzaCombo.currentText()
        toppings = []
        if self.toppingCheese.isChecked():
            toppings.append(self.lang_manager.translate("topping_cheese"))
        if self.toppingMushrooms.isChecked():
            toppings.append(self.lang_manager.translate("topping_mushrooms"))
        if self.toppingOlives.isChecked():
            toppings.append(self.lang_manager.translate("topping_olives"))
        name = self.nameEdit.text()
        address = self.addressEdit.toPlainText()
        self.logic.set_pizza(pizza)
        self.logic.set_toppings(toppings)
        self.logic.set_customer_info(name, address)
        if self.logic.is_order_valid():
            summary = self.logic.get_order_summary()
            QMessageBox.information(self, self.lang_manager.translate("order_success_title"), self.lang_manager.translate("order_success_message").format(**summary))
            self.logic.reset()
            self.nameEdit.clear()
            self.addressEdit.clear()
            self.toppingCheese.setChecked(False)
            self.toppingMushrooms.setChecked(False)
            self.toppingOlives.setChecked(False)
        else:
            QMessageBox.warning(self, self.lang_manager.translate("order_error_title"), self.lang_manager.translate("order_error_message"))

    def activate(self):
        pass
    def deactivate(self):
        pass
    def reset(self):
        self.logic.reset()
        self.nameEdit.clear()
        self.addressEdit.clear()
        self.toppingCheese.setChecked(False)
        self.toppingMushrooms.setChecked(False)
        self.toppingOlives.setChecked(False)
    def run(self):
        pass
    def get_widget(self):
        return self
