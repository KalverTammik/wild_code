from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QSizePolicy
)
from ..theme_manager import ThemeManager
from ...constants.module_icons import IconNames
from ...ui.window_state.popup_helpers import PopupHelpers


class TagsWidget(QWidget):
    def __init__(self, tag_names: list, parent=None, compact=False):
        super().__init__(parent)

        # Store tag names (should be a list)
        self.tag_names = tag_names if isinstance(tag_names, list) else []
        self._compact = bool(compact)

        self._tags_container = None
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        # Create the main tags display (compact)
        if self.tag_names:
            # Tags container
            tags_container = QFrame(self)
            tags_container.setObjectName("TagsContainer")
            tags_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            tags_layout = QHBoxLayout(tags_container)
            tags_layout.setContentsMargins(2, 1, 2, 1) if self._compact else tags_layout.setContentsMargins(4, 2, 4, 2)
            tags_layout.setSpacing(0)
            
            # Tags icon
            icon = ThemeManager.get_qicon(IconNames.ICON_TAGS)
            icon_label = QLabel()
            icon_size = 14 if self._compact else 24
            icon_label.setPixmap(icon.pixmap(icon_size, icon_size))
            icon_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            #icon_label.setToolTip("Sildid")
            tags_layout.addWidget(icon_label)

            # Make the container hoverable for showing all tags
            tags_container.setMouseTracking(True)
            tags_container.installEventFilter(self)
            self._tags_container = tags_container

            main_layout.addWidget(tags_container)
            


        self.hover_popup = None
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        PopupHelpers.bind_hide_timeout_attr_for(
            "tags",
            owner=self,
            attr_name="hover_popup",
            timer=self._hide_timer,
            anchor_getter=lambda: self._tags_container,
            event_filter_owner=self,
        )

        self.destroyed.connect(self._on_destroyed)

    def eventFilter(self, obj, event):
        PopupHelpers.handle_popup_hover_event(
            obj,
            event,
            popup_widget=self.hover_popup,
            timer=self._hide_timer,
            anchor_matcher=lambda widget: bool(widget) and widget.objectName() == "TagsContainer",
            on_anchor_enter=self.show_tags_popup,
            delay_ms=PopupHelpers.popup_delay("tags"),
            close_on_deactivate=PopupHelpers.popup_close_on_deactivate("tags"),
            on_popup_deactivate=lambda: PopupHelpers.hide_popup_attr(self, "hover_popup", self._hide_timer, self),
        )
        return super().eventFilter(obj, event)

    def _on_destroyed(self, _obj=None):
        PopupHelpers.stop_hide_timer(self._hide_timer)
        self.hover_popup = PopupHelpers.hide_popup_attr(self, "hover_popup", self._hide_timer, self)

    def show_tags_popup(self, anchor_widget):
        if not self.tag_names:
            return

        self.hover_popup = PopupHelpers.show_popup_for(
            "tags",
            timer=self._hide_timer,
            current_popup=self.hover_popup,
            anchor_widget=anchor_widget,
            popup_factory=lambda: TagPopup(self.tag_names, self.window()),
            event_filter_owner=self,
        )

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

        PopupHelpers.apply_popup_style(self, "tags")

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
        PopupHelpers.apply_popup_style(self, "tags")

        return super().showEvent(event)

