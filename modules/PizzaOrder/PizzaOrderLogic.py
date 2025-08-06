class PizzaOrderLogic:
    def __init__(self):
        self.reset()

    def reset(self):
        self.selected_pizza = None
        self.selected_toppings = []
        self.customer_name = ""
        self.address = ""

    def set_pizza(self, pizza):
        self.selected_pizza = pizza

    def set_toppings(self, toppings):
        self.selected_toppings = toppings

    def set_customer_info(self, name, address):
        self.customer_name = name
        self.address = address

    def get_order_summary(self):
        return {
            "pizza": self.selected_pizza,
            "toppings": self.selected_toppings,
            "customer_name": self.customer_name,
            "address": self.address
        }

    def is_order_valid(self):
        return bool(self.selected_pizza and self.customer_name and self.address)
