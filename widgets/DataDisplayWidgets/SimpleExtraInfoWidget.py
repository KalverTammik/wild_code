from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QFrame
from PyQt5.QtGui import QFont


class SimpleExtraInfoFrame(QFrame):
    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Simple label with placeholder text
        label = QLabel("Siia tulevad seotud andmed")
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # Style the label to match the design
        font = QFont()
        font.setPointSize(9)
        font.setBold(False)
        label.setFont(font)
        label.setStyleSheet("""
            QLabel {
                color: #666;
                padding: 2px 0px;
            }
        """)

        layout.addWidget(label)


class SimpleExtraInfoWidget(QWidget):
    def __init__(self, item_data, module_type="contract", parent=None):
        super().__init__(parent)
        self.item_data = item_data
        self.module_type = module_type
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Simple label with placeholder text
        label = QLabel("Siia tulevad seotud andmed")
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # Style the label to match the design
        font = QFont()
        font.setPointSize(9)
        font.setBold(False)
        label.setFont(font)
        label.setStyleSheet("""
            QLabel {
                color: #666;
                padding: 2px 0px;
            }
        """)

        layout.addWidget(label)
