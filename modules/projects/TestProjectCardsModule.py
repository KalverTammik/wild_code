from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QFrame, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt

# Dummy project data for testing
TEST_PROJECTS = [
    {
        'name': f'Project {i+1}',
        'number': f'{1000+i}',
        'client': {'displayName': f'Client {i+1}'},
        'members': {'edges': []},
        'status': {'name': 'Active', 'color': '00cc44'},
        'isPublic': True,
        'startAt': None,
        'dueAt': None,
        'createdAt': None,
        'updatedAt': None,
    }
    for i in range(5)
]

class SimpleProjectCard(QFrame):
    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("background: #ffb347; min-height: 80px; border: 2px solid #333;")
        layout = QVBoxLayout(self)
        name = project.get('name', 'No Name')
        number = project.get('number', '-')
        client = project.get('client', {}).get('displayName', '-')
        layout.addWidget(QLabel(f"<b>{name}</b> <span>#{number}</span>"))
        layout.addWidget(QLabel(f"Client: {client}"))
        status = project.get('status', {}).get('name', '-')
        layout.addWidget(QLabel(f"Status: {status}"))

class TestProjectCardsModule(QWidget):
    name = "TestProjectCardsModule"
    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        vbox = QVBoxLayout(content)
        for project in TEST_PROJECTS:
            card = SimpleProjectCard(project)
            vbox.addWidget(card)
        content.setLayout(vbox)
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def activate(self):
        pass

    def deactivate(self):
        pass

    def get_widget(self):
        return self


# For manual testing: create and show the widget if run as script
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    w = TestProjectCardsModule()
    w.show()
    sys.exit(app.exec_())
