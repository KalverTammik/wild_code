from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QPushButton, QHBoxLayout
from .ProjectCard import ProjectCard  # Import the ProjectCard class

class ProjectCardUI:
    def __init__(self):
        self.widget = QWidget()
        self.widget.setLayout(QVBoxLayout())
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.card_container = QWidget()
        self.card_container.setLayout(QVBoxLayout())
        self.scroll_area.setWidget(self.card_container)
        self.widget.layout().addWidget(self.scroll_area)
        # Pagination controls
        self.pagination_bar = QHBoxLayout()
        self.prev_button = QPushButton("Previous")
        self.next_button = QPushButton("Next")
        self.pagination_bar.addWidget(self.prev_button)
        self.pagination_bar.addWidget(self.next_button)
        self.widget.layout().addLayout(self.pagination_bar)

    def get_widget(self):
        return self.widget

    def clear_cards(self):
        for i in reversed(range(self.card_container.layout().count())):
            widget = self.card_container.layout().itemAt(i).widget()
            if widget:
                widget.deleteLater()

    def populate_cards(self, data):
        self.clear_cards()
        for item in data:
            card = ProjectCard(
                title=item.get("title", "N/A"),
                description=item.get("description", "N/A"),
                price=item.get("price", 0),
                brand=item.get("brand", "N/A")
            )
            self.card_container.layout().addWidget(card)
