from PyQt5.QtWidgets import QPushButton

class ButtonHelper:
    @staticmethod
    def create_button(text, tooltip=None, on_click=None, parent=None):
        """
        Create a styled QPushButton.

        :param text: The text to display on the button.
        :param tooltip: The tooltip text for the button (optional).
        :param on_click: The function to connect to the button's clicked signal (optional).
        :param parent: The parent widget for the button (optional).
        :return: A styled QPushButton instance.
        """
        button = QPushButton(text, parent)
        # Prevent button from being triggered by Return key
        button.setAutoDefault(False)
        button.setDefault(False)
        if tooltip:
            button.setToolTip(tooltip)
        if on_click:
            button.clicked.connect(on_click)
        return button
