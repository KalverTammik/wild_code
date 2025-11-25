from PyQt5.QtCore import Qt, QPoint, QEvent
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
)
from ..theme_manager import ThemeManager
from ...constants.file_paths import QssPaths


class TagsWidget(QWidget):
    def __init__(self, tag_names: list, parent=None):
        super().__init__(parent)

        # Store tag names (should be a list)
        self.tag_names = tag_names if isinstance(tag_names, list) else []

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        # Create the main tags display (compact)
        if self.tag_names:
            # Tags container
            tags_container = QFrame(self)
            tags_container.setObjectName("TagsContainer")
            tags_layout = QHBoxLayout(tags_container)
            tags_layout.setContentsMargins(4, 2, 4, 2)
            
            # Tags icon
            icon = ThemeManager.get_qicon(ThemeManager.ICON_LIST)
            icon_label = QLabel()
            icon_label.setPixmap(icon.pixmap(12, 12))
            #icon_label.setToolTip("Sildid")
            tags_layout.addWidget(icon_label)

            # Make the container hoverable for showing all tags
            tags_container.setMouseTracking(True)
            tags_container.installEventFilter(self)

            main_layout.addWidget(tags_container)
            


        self.hover_popup = None

    def __del__(self):
        """Ensure proper cleanup when the widget is destroyed."""
        try:
            self.hide_tags_popup()
        except Exception:
            pass

    def eventFilter(self, obj, event):
        try:
            if obj and obj.objectName() == "TagsContainer":
                if event.type() == QEvent.Enter:
                    self.show_tags_popup(obj)
                elif event.type() == QEvent.Leave:
                    self.hide_tags_popup()
        except Exception:
            pass
        return super().eventFilter(obj, event)

    def show_tags_popup(self, anchor_widget):
        if not self.tag_names:
            return

        # Clean up any existing popup
        self.hide_tags_popup()

        # Create popup widget with all tags
        self.hover_popup = TagPopup(self.tag_names, self.window())

        # Position popup near the anchor widget
        self.hover_popup.adjustSize()
        pos = anchor_widget.mapToGlobal(QPoint(4, 0))
        self.hover_popup.move(pos)
        self.hover_popup.show()
        self.hover_popup.raise_()

    def hide_tags_popup(self):
        try:
            if self.hover_popup:
                if not self.hover_popup.isVisible():
                    self.hover_popup = None
                    return

                # Disconnect any event filters
                try:
                    self.hover_popup.removeEventFilter(self)
                except Exception:
                    pass

                # Close and delete the popup
                self.hover_popup.close()
                self.hover_popup.deleteLater()
                self.hover_popup = None
        except Exception:
            self.hover_popup = None

    @staticmethod
    def _extract_tag_names(item_data: dict):
        tags_edges = ((item_data or {}).get('tags') or {}).get('edges') or []
        names = [((e or {}).get('node') or {}).get('name') for e in tags_edges]
        names = [n.strip() for n in names if isinstance(n, str) and n.strip()]
        return names


class TagPopup(QWidget):
    def __init__(self, tags: list, parent=None):
        super().__init__(parent, flags=Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setObjectName("TagsPopup")
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.NoFocus)
        self.setMouseTracking(True)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(8)

        # Create a widget to display all tags
        self._tags_display = self._create_tags_display(tags)
        lay.addWidget(self._tags_display)

        ThemeManager.apply_module_style(self, [QssPaths.POPUP])

    def _create_tags_display(self, tag_names):
        """Create a widget that displays all tags in a vertical layout."""
        container = QWidget()
        container.setObjectName("TagsContainer")
        container.setAttribute(Qt.WA_TranslucentBackground, True)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        # Show all tags without limit
        for tag_name in tag_names:
            tag_bubble = self._create_tag_bubble(tag_name)
            layout.addWidget(tag_bubble)

        return container

    def _create_tag_bubble(self, tag_name: str):
        """Create a tag bubble for the popup."""
        # Create a frame to hold the label for proper QSS targeting
        frame = QFrame(self)
        frame.setObjectName("PopupFrame")
        frame.setProperty("role", "tag")

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        bubble = QLabel(frame)
        bubble.setObjectName("Value")
        bubble.setText(tag_name)
        bubble.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        bubble.setToolTip(tag_name)

        layout.addWidget(bubble)

        return frame

    def showEvent(self, event):
        ThemeManager.apply_module_style(self, [QssPaths.POPUP])

        return super().showEvent(event)

