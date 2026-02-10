
from ...utils.status_color_helper import StatusColorHelper
from ...python.responses import DataDisplayExtractors
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget


class StatusWidget(QWidget):
    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addStretch(1)  # push everything right

        status_info = DataDisplayExtractors.extract_status(item_data)
        name = status_info.name or '-'
        hex_color = status_info.color or 'cccccc'

        bg, fg, border = StatusColorHelper.upgrade_status_color(hex_color)

        self.status_label = QLabel(name)
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFixedWidth(128)
        self.status_label.setStyleSheet(
            "QLabel#StatusLabel {"
            f"background-color: rgba({bg[0]},{bg[1]},{bg[2]}, 0.95);"
            f"color: rgb({fg[0]},{fg[1]},{fg[2]});"
            f"border: 1px solid rgba({border[0]},{border[1]},{border[2]}, 0.85);"
            "border-radius: 6px;"
            "padding: 3px 10px;"
            "font-weight: 500;"
            "font-size: 11px;"
            "}"
            "QLabel#StatusLabel:hover {"
            f"background-color: rgba({bg[0]},{bg[1]},{bg[2]}, 1.0);"
            "}"
        )


        row.addWidget(self.status_label, 0, Qt.AlignRight | Qt.AlignVCenter)
        main_layout.addLayout(row)

