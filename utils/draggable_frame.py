from PyQt5.QtWidgets import QFrame
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QMouseEvent

class DraggableFrame(QFrame):
    def __init__(self, parent=None, cursor=Qt.OpenHandCursor):
        super().__init__(parent)
        self._drag_pos = None
        self.setCursor(cursor)  # Set the cursor style

    def init_drag(self, parent):
        self.parent = parent

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.window().frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.LeftButton and self._drag_pos:
            self.window().move(event.globalPos() - self._drag_pos)
            event.accept()