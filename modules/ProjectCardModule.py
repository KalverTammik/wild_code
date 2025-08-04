import requests  # Add this import for HTTP requests
from ..ui.ProjectCardUI import ProjectCardUI
from ..BaseModule import BaseModule
from ..module_manager import PROJECT_CARD_MODULE

class ProjectCardModule(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = PROJECT_CARD_MODULE  # Add a unique name for the module
        print(f"[ProjectCardModule] Initialized with name: {self.name}")
        self.ui = ProjectCardUI()
        self.page = 0
        self.limit = 5
        # Connect UI signals
        self.ui.prev_button.clicked.connect(self.load_previous_page)
        self.ui.next_button.clicked.connect(self.load_next_page)

    def activate(self):
        print("[ProjectCardModule] Activating module...")
        self.load_data()

    def deactivate(self):
        print("[ProjectCardModule] Deactivating module...")
        self.ui.clear_cards()

    def run(self):
        print("[ProjectCardModule] Running module...")

    def reset(self):
        print("[ProjectCardModule] Resetting module...")
        self.page = 0
        self.load_data()

    def get_widget(self):
        print("[ProjectCardModule] Returning widget...")
        return self.ui.get_widget()

    def load_data(self):
        print(f"[ProjectCardModule] Loading data for page {self.page}...")
        offset = self.page * self.limit
        url = f"https://dummyjson.com/products?limit={self.limit}&skip={offset}"
        print(f"[ProjectCardModule] Fetching data from URL: {url}")
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json().get("products", [])
            print(f"[ProjectCardModule] Data fetched successfully: {len(data)} items")
            self.ui.populate_cards(data)
        else:
            print(f"[ProjectCardModule] Failed to fetch data. Status code: {response.status_code}")
        self.ui.prev_button.setEnabled(self.page > 0)

    def load_previous_page(self):
        print("[ProjectCardModule] Loading previous page...")
        if self.page > 0:
            self.page -= 1
            self.load_data()

    def load_next_page(self):
        print("[ProjectCardModule] Loading next page...")
        self.page += 1
        self.load_data()
