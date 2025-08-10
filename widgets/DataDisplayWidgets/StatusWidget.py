from .DatesWidget import DatesWidget
from ...constants.module_icons import MiscIcons
from ...utils.apply_chip_shadow import apply_chip_shadow
from ...utils.status_color_helper import StatusColorHelper


from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget, QFrame


class StatusWidget(QWidget):
    def __init__(self, item_data, theme=None, parent=None):
        super().__init__(parent)
        # Outer layout holding a debug container frame
        outer_layout = QVBoxLayout(self); outer_layout.setContentsMargins(0, 0, 0, 0)

        container = QFrame(self)
        container.setObjectName("StatusDebugContainer")
        container.setStyleSheet(
            "QFrame#StatusDebugContainer {"
            "  border: 2px dashed #FF00FF;"          # vibrant magenta
            "  background-color: rgba(255,0,255,0.04);"
            "}"
        )

        main_layout = QVBoxLayout(container); main_layout.setContentsMargins(0, 0, 0, 0)

        row = QHBoxLayout(); row.setContentsMargins(0, 0, 0, 0)
        row.addStretch(1)  # push everything right

        if not item_data.get('isPublic'):
            pub = QLabel()
            pub.setObjectName("ProjectPrivateIcon")
            pub.setToolTip("Privaatne")
            pub.setAlignment(Qt.AlignCenter)
            # themed private icon (using ICON_ADD as requested)
            icon_path = MiscIcons.ICON_IS_PRIVATE
            print(f"[StatusWidget] Using private icon: {icon_path}")
            pm = QPixmap(icon_path)
            if not pm.isNull():
                print("[StatusWidget] Setting private icon pixmap")
                pub.setPixmap(pm.scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                print("[StatusWidget] Private icon pixmap is null, using default")
                pub.setText("P")

            pub.setFixedSize(16, 16)
            row.addWidget(pub, 0, Qt.AlignRight | Qt.AlignVCenter)

        status = item_data.get('status', {}) or {}
        name = status.get('name', '-') or '-'
        hex_color = status.get('color', 'cccccc')

        bg, fg, border = StatusColorHelper.upgrade_status_color(hex_color)

        self.status_label = QLabel(name)
        self.status_label.setObjectName("ProjectStatusLabel")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFixedWidth(128)
        self.status_label.setStyleSheet(
            "QLabel#ProjectStatusLabel {"
            f"background-color: rgba({bg[0]},{bg[1]},{bg[2]}, 0.95);"
            f"color: rgb({fg[0]},{fg[1]},{fg[2]});"
            f"border: 1px solid rgba({border[0]},{border[1]},{border[2]}, 0.85);"
            "border-radius: 10px;"
            "padding: 3px 10px;"
            "font-weight: 500;"
            "font-size: 11px;"
            "}"
            "QLabel#ProjectStatusLabel:hover {"
            f"background-color: rgba({bg[0]},{bg[1]},{bg[2]}, 1.0);"
            "}"
        )
        apply_chip_shadow(self.status_label, theme)

        row.addWidget(self.status_label, 0, Qt.AlignRight | Qt.AlignVCenter)
        main_layout.addLayout(row)

        # Wrap DatesWidget in its own debug frame (green) and align to the right
        dates_wrap = QFrame(self)
        dates_wrap.setObjectName("DatesDebugFrame")
        dates_wrap.setStyleSheet(
            "QFrame#DatesDebugFrame {"
            "  border: 2px solid #00C853;"            # vibrant green
            "  background-color: rgba(0,200,83,0.04);"
            "}"
        )
        dw_layout = QVBoxLayout(dates_wrap); dw_layout.setContentsMargins(0, 0, 0, 0)
        dw_layout.addWidget(DatesWidget(item_data))

        main_layout.addWidget(dates_wrap, 0, Qt.AlignRight)

        # Add the debug container to the outer layout
        outer_layout.addWidget(container)