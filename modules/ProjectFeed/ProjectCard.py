from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt

class ProjectCard(QWidget):
    def __init__(self, title, description, price, brand, image_url=None, parent=None):
        super().__init__(parent)
        self.setObjectName("ProjectCard")
        self.setStyleSheet("""
            QWidget#ProjectCard {
                background-color: #23272e;
                border-radius: 12px;
                padding: 16px;
                margin-bottom: 12px;
            }
            QLabel {
                color: #fff;
            }
            QPushButton {
                background: #444;
                color: #fff;
                border-radius: 6px;
                padding: 4px 12px;
                margin-right: 8px;
            }
            QPushButton:hover {
                background: #666;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.addWidget(QLabel(f"<b>{title}</b>"))
        layout.addWidget(QLabel(description))
        info = QLabel(f"<i>Brand:</i> {brand} &nbsp; <b>Budget:</b> ${price}")
        layout.addWidget(info)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(QPushButton("Details"))
        btn_layout.addWidget(QPushButton("Mark Complete"))
        btn_layout.addWidget(QPushButton("✎ Edit"))
        btn_layout.addStretch(1)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
