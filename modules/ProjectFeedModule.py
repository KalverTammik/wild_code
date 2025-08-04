import requests
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel, QFrame, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt, QTimer
from ..BaseModule import BaseModule
from ..module_manager import PROJECT_FEED_MODULE
class ProjectFeedModule(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = PROJECT_FEED_MODULE

        self.widget = QWidget()
        self.layout = QVBoxLayout(self.widget)

        # Scroll area for infinite scrolling
        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollContent = QWidget()
        self.scrollLayout = QVBoxLayout(self.scrollContent)
        self.scrollArea.setWidget(self.scrollContent)

        # Add scroll area to the main layout
        self.layout.addWidget(self.scrollArea)

        # Loading indicator
        self.loadingLabel = QLabel("Loading more projects...")
        self.loadingLabel.setAlignment(Qt.AlignCenter)
        self.loadingLabel.hide()
        self.layout.addWidget(self.loadingLabel)

        # Infinite scroll variables
        self.currentOffset = 0
        self.isLoading = False
        self.totalCount = None

        # Connect scroll detection
        self.scrollArea.verticalScrollBar().valueChanged.connect(self.onScroll)

        # Initial data load
        self.loadMoreProjects()

    def get_widget(self):
        return self.widget

    def loadMoreProjects(self):
        """Fetch and display the next batch of projects."""
        if self.isLoading or (self.totalCount is not None and self.currentOffset >= self.totalCount):
            return

        self.isLoading = True
        self.loadingLabel.show()

        # Fetch data asynchronously
        QTimer.singleShot(0, self.fetchProjects)

    def fetchProjects(self):
        """Fetch project data from the API."""
        try:
            url = f"https://dummyjson.com/products?limit=10&skip={self.currentOffset}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            # Update total count if available
            if self.totalCount is None:
                self.totalCount = data.get("total", 0)

            # Add project cards to the layout
            for project in data.get("products", []):
                card = ProjectCard(
                    title=project["title"],
                    description=project["description"],
                    client=project["brand"],
                    budget=project["price"],
                    image=project["images"][0] if project["images"] else None
                )
                self.scrollLayout.addWidget(card)

            # Update offset
            self.currentOffset += len(data.get("products", []))
        except Exception as e:
            print(f"[ProjectFeedModule] Error fetching projects: {e}")
        finally:
            self.isLoading = False
            self.loadingLabel.hide()

    def onScroll(self):
        """Detect when the user scrolls near the bottom."""
        scrollbar = self.scrollArea.verticalScrollBar()
        if scrollbar.value() >= scrollbar.maximum() - 50:  # Near the bottom
            self.loadMoreProjects()


class ProjectCard(QFrame):
    def __init__(self, title, description, client, budget, image=None):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)


        layout = QVBoxLayout(self)

        # Title
        titleLabel = QLabel(title)
        titleLabel.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(titleLabel)

        # Description
        descriptionLabel = QLabel(description)
        descriptionLabel.setWordWrap(True)
        layout.addWidget(descriptionLabel)

        # Client and Budget
        infoLayout = QHBoxLayout()
        clientLabel = QLabel(f"Client: {client}")
        budgetLabel = QLabel(f"Budget: ${budget}")
        infoLayout.addWidget(clientLabel)
        infoLayout.addWidget(budgetLabel)
        layout.addLayout(infoLayout)

        # Buttons
        buttonLayout = QHBoxLayout()
        detailsButton = QPushButton("Details")
        markCompleteButton = QPushButton("Mark Complete")
        editButton = QPushButton("✎ Edit")
        buttonLayout.addWidget(detailsButton)
        buttonLayout.addWidget(markCompleteButton)
        buttonLayout.addWidget(editButton)
        layout.addLayout(buttonLayout)
