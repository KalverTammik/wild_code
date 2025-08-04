from ..BaseModule import BaseModule
from .PizzaOrderLogic import PizzaOrderLogic
from ..ui.PizzaOrderUI import PizzaOrderUI

class PizzaOrderModule(BaseModule):
    """
    Pizza Order Module for simulating pizza order BPMN process.
    """

    def __init__(self):
        super().__init__()
        self.name = "PIZZA_ORDER_MODULE"
        self.logic = PizzaOrderLogic()
        self.widget = PizzaOrderUI()
        self.setupConnections()

    def setupConnections(self):
        self.widget.placeOrderBtn.clicked.connect(self.runPlaceOrder)
        self.widget.confirmOrderBtn.clicked.connect(self.runConfirmOrder)
        self.widget.checkInventoryBtn.clicked.connect(self.runCheckInventory)
        self.widget.preparePizzaBtn.clicked.connect(self.runPreparePizza)
        self.widget.packPizzaBtn.clicked.connect(self.runPackPizza)
        self.widget.deliverPizzaBtn.clicked.connect(self.runDeliverPizza)
        self.widget.confirmDeliveryBtn.clicked.connect(self.runConfirmDelivery)
        self.widget.sendFailureNoticeBtn.clicked.connect(self.runSendFailureNotice)

    def activate(self):
        """
        Activate the module.
        """
        self.widget.statusLabel.setText("Status: Activated")

    def deactivate(self):
        """
        Deactivate the module.
        """
        self.widget.statusLabel.setText("Status: Deactivated")

    def run(self):
        """
        Run the main process.
        """
        self.widget.statusLabel.setText("Status: Running pizza order process")

    def reset(self):
        """
        Reset the module state.
        """
        self.widget.statusLabel.setText("Status: Ready")

    def get_widget(self):
        """
        Return the main widget for this module.
        """
        return self.widget

    def runPlaceOrder(self):
        self.logic.placeOrder({})
        self.widget.statusLabel.setText("Order placed.")

    def runConfirmOrder(self):
        self.logic.confirmOrder()
        self.widget.statusLabel.setText("Order confirmed.")

    def runCheckInventory(self):
        self.logic.checkInventory()
        self.widget.statusLabel.setText("Inventory checked.")

    def runPreparePizza(self):
        self.logic.preparePizza()
        self.widget.statusLabel.setText("Pizza prepared.")

    def runPackPizza(self):
        self.logic.packPizza()
        self.widget.statusLabel.setText("Pizza packed.")

    def runDeliverPizza(self):
        self.logic.deliverPizza()
        self.widget.statusLabel.setText("Pizza delivered.")

    def runConfirmDelivery(self):
        self.logic.confirmDelivery()
        self.widget.statusLabel.setText("Delivery confirmed.")

    def runSendFailureNotice(self):
        self.logic.sendFailureNotice()
        self.widget.statusLabel.setText("Failure notice sent.")
