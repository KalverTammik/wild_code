from PyQt5.QtCore import Qt, QPoint, QEvent, QTimer
from PyQt5.QtGui import QColor, QPixmap
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame,
    QSizePolicy, QGraphicsDropShadowEffect, QToolButton
)
from .StatusWidget import StatusWidget
from .MembersView import MembersView
from .ExtraInfoWidget import ExtraInfoFrame
from .TagsWidget import TagsWidget



# Project imports (adjust paths if needed)
from ..theme_manager import ThemeManager
from ...constants.file_paths import QssPaths



# ================== Module Feed ==================
class ModuleFeedBuilder:
    @staticmethod
    def _item_has_tags(item_data: dict) -> bool:
        try:
            names = ModuleFeedBuilder._extract_tag_names(item_data)
            return len(names) > 0
        except Exception as e:
            return False

    @staticmethod
    def _extract_tag_names(item_data: dict):
        tags_edges = ((item_data or {}).get('tags') or {}).get('edges') or []
        names = [((e or {}).get('node') or {}).get('name') for e in tags_edges]
        names = [n.strip() for n in names if isinstance(n, str) and n.strip()]
        return names
    @staticmethod
    def create_item_card(item):
        card = QFrame()
        card.setObjectName("ModuleInfoCard")
        card.setProperty("compact", False)

        main = QHBoxLayout(card)
        main.setContentsMargins(10, 10, 10, 10)
        main.setSpacing(10)

        # Left content
        content = QFrame(); content.setObjectName("CardContent")
        cl = QVBoxLayout(content); cl.setContentsMargins(0, 0, 0, 0); cl.setSpacing(6)

        header_row = QHBoxLayout(); header_row.setContentsMargins(0, 0, 0, 0)
        header_row.addWidget(InfocardHeaderFrame(item), alignment=Qt.AlignTop)
        # Tags hover icon: show popup on hover if item has tags
        if ModuleFeedBuilder._item_has_tags(item):
            header_row.addWidget(TagsHoverButton(item), alignment=Qt.AlignTop)
        header_row.addStretch(1)
        header_row.addWidget(MembersView(item), alignment=Qt.AlignRight | Qt.AlignTop)
        cl.addLayout(header_row)

        cl.addWidget(ExtraInfoFrame(item))
        main.addWidget(content, 1)

        # Right status column
        status_col = QVBoxLayout(); status_col.setContentsMargins(0, 0, 0, 0)
        status_col.addWidget(StatusWidget(item), alignment=Qt.AlignTop | Qt.AlignRight)
        status_col.addStretch(1)
        main.addLayout(status_col)

        # Real drop shadow (subtle)
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 60))
        card.setGraphicsEffect(shadow)

        return card

    @staticmethod
    def add_items_to_feed(module_instance, items):
        """
        Adds item cards to the feed layout of the given module instance.
        Handles all UI updates after adding cards.
        Uses centralized ThemeManager.apply_module_style for card theming.
        """
        for item in items:
            card = ModuleFeedBuilder.create_item_card(item)
            # Centralized theming for card
            ThemeManager.apply_module_style(card, [QssPaths.MODULE_CARD])
            module_instance.feed_layout.addWidget(card)
        # Do not call adjustSize(), show(), or updateGeometry() on feed_content, scroll_area, or widget
        # Let Qt's layout system handle resizing and scrolling


# ================== Elided single-line label ==================
class ElidedLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._full = text or ""
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setWordWrap(False)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setToolTip(self._full)
        self.setObjectName("ElidedLabel")

    def setText(self, text):
        self._full = text or ""
        self.setToolTip(self._full)
        super().setText(self._full)
        self._elide()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._elide()

    def _elide(self):
        fm = self.fontMetrics()
        elided = fm.elidedText(self._full, Qt.ElideRight, max(0, self.width()))
        super().setText(elided)


# ================== Header (name + number + client) ==================
class InfocardHeaderFrame(QFrame):
    def __init__(self, item_data, parent=None, compact=False):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        self.setObjectName("InfocardHeaderFrame")
        self.setProperty("compact", compact)

        root = QHBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(8 if not compact else 6)

        # Left column
        left = QFrame(self); left.setObjectName("HeaderLeft")
        leftL = QVBoxLayout(left); leftL.setContentsMargins(0, 0, 0, 0); leftL.setSpacing(2 if not compact else 1)

        name = item_data.get('name', 'No Name') or 'No Name'
        number = item_data.get('number', '-')
        client = (item_data.get('client') or {}).get('displayName')

        # Name row: elided name + pill badge number
        nameRow = QHBoxLayout(); nameRow.setContentsMargins(0,0,0,0); nameRow.setSpacing(8 if not compact else 6)

        self.nameLabel = ElidedLabel(name)
        self.nameLabel.setObjectName("ProjectNameLabel")
        self.nameLabel.setToolTip(name)
        nameRow.addWidget(self.nameLabel, 1, Qt.AlignVCenter)

        self.numberBadge = QLabel(str(number))
        self.numberBadge.setObjectName("ProjectNumberBadge")
        self.numberBadge.setAlignment(Qt.AlignCenter)
        self.numberBadge.setMinimumWidth(36)
        nameRow.addWidget(self.numberBadge, 0, Qt.AlignVCenter)

        leftL.addLayout(nameRow)

        # Client row (optional)
        if client:
            clientRow = QHBoxLayout(); clientRow.setContentsMargins(0,0,0,0); clientRow.setSpacing(6)
            self.clientIcon = QLabel("👤"); self.clientIcon.setObjectName("ClientIcon"); self.clientIcon.setFixedWidth(14)
            clientRow.addWidget(self.clientIcon, 0, Qt.AlignVCenter)

            self.clientLabel = ElidedLabel(client)
            self.clientLabel.setObjectName("ProjectClientLabel")
            self.clientLabel.setToolTip(client)
            clientRow.addWidget(self.clientLabel, 1, Qt.AlignVCenter)

            leftL.addLayout(clientRow)

        root.addWidget(left, 1, Qt.AlignVCenter)


# ================== Tags Popup and Hover Button ==================
class TagPopup(QWidget):
    """
    Lightweight popup that hosts a TagsWidget for the given item.
    Shown near a trigger button; themed with QssPaths.PILLS.
    Behavior:
    - Created only when an item actually has tags (by TagsHoverButton).
    - Reparented to the top-level window for correct z-order in QGIS.
    - Non-activating tool window; visibility is controlled by the hover button timers.
    """
    def __init__(self, item_data: dict, parent=None):
        # Use a tool window that we close manually, avoids Qt.Popup auto-close behavior
        super().__init__(parent, flags=Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setObjectName("TagsPopup")
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.NoFocus)
        self.setMouseTracking(True)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(6)

        try:
            names = ModuleFeedBuilder._extract_tag_names(item_data)
            # If there are no tags, close immediately; otherwise, build and add the widget.
            if not names:
                QTimer.singleShot(0, self.close)
            else:
                self._tags = TagsWidget(item_data, self)
                lay.addWidget(self._tags)
        except Exception as e:
            QTimer.singleShot(0, self.close)

        # Apply pills styling to the popup contents
        ThemeManager.apply_module_style(self, [QssPaths.PILLS])

    def show_near(self, anchor_widget: QWidget):
        if not anchor_widget:
            self.adjustSize()
            self.show()
            self.raise_()
            return
        try:
            # Ensure the popup is parented to the same top-level window (fixes z-order in QGIS)
            top = anchor_widget.window() if hasattr(anchor_widget, 'window') else None
            if top is not None and self.parent() is not top:
                self.setParent(top, self.windowFlags())
            # Force layout calculation before sizing/placing
            try:
                self.layout().activate()
            except Exception:
                pass
            self.adjustSize()
            # Place directly below the button to minimize cursor gap
            gpos = anchor_widget.mapToGlobal(QPoint(0, anchor_widget.height()))
            self.move(gpos)
        except Exception:
            pass
        self.show()
        try:
            self.raise_()
        except Exception:
            pass

    def showEvent(self, event):
        # Re-apply styling and retheme inner tags each time it shows (handles theme changes)
        try:
            ThemeManager.apply_module_style(self, [QssPaths.PILLS])
            if hasattr(self, "_tags") and self._tags is not None:
                try:
                    self._tags.retheme()
                except Exception:
                    pass
        except Exception:
            pass
        return super().showEvent(event)

    def closeEvent(self, event):
        return super().closeEvent(event)

    # Direct focus/enter/leave handlers removed; hover is tracked via eventFilter installed by the button.

    # Allow external observer to receive enter/leave from popup and its children
    def install_hover_filters(self, observer):
        try:
            self.installEventFilter(observer)
            for w in self.findChildren(QWidget):
                try:
                    w.installEventFilter(observer)
                except Exception:
                    pass
        except Exception:
            pass


class TagsHoverButton(QToolButton):
    """
    Small icon button; on hover shows TagPopup with TagsWidget.
    Behavior:
    - On hover enter: creates/shows TagPopup near the icon; stops hide timer.
    - On hover leave: starts a short hide timer to allow moving into the popup.
    - An event filter on the popup and its children keeps it open while hovered.
    """
    def __init__(self, item_data: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("TagsHoverButton")
        self._item = item_data
        self._popup = None
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._maybe_hide_popup)
        self._hide_delay_ms = 600

        # Icon (theme-aware)
        try:
            icon = ThemeManager.get_qicon(ThemeManager.ICON_INFO)
            self.setIcon(icon)
            self.setIconSize(self._best_icon_size())
        except Exception:
            pass
        self.setToolTip("Tags")
        self.setAutoRaise(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(20, 20)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.NoFocus)
        try:
            self.clicked.connect(self._on_clicked)
        except Exception:
            pass

        # Track hover state
        self._over_button = False
        self._over_popup = False

    def _best_icon_size(self):
        # Keep icon crisp in small button
        from PyQt5.QtCore import QSize
        return QSize(14, 14)

    def enterEvent(self, e):
        self._over_button = True
        if self._hide_timer.isActive():
            self._hide_timer.stop()
        self._show_popup()
        return super().enterEvent(e)

    def leaveEvent(self, e):
        self._over_button = False
        # Defer hide slightly to allow moving into popup
        self._hide_timer.start(self._hide_delay_ms)
        return super().leaveEvent(e)

    def _ensure_popup(self):
        if self._popup is not None:
            try:
                # If popup was closed, isVisible() will be False but we can still reuse; recreate for fresh theme
                # To keep it simple and always fresh on hover, recreate when not visible
                if not self._popup.isVisible():
                    self._popup.deleteLater()
                    self._popup = None
            except Exception:
                self._popup = None
        if self._popup is None:
            self._popup = TagPopup(self._item)
            # Clear cache when destroyed
            try:
                self._popup.destroyed.connect(lambda _=None: setattr(self, "_popup", None))
            except Exception:
                pass
            # Observe hover over popup
            self._popup.install_hover_filters(self)
        return self._popup

    def _show_popup(self):
        pop = self._ensure_popup()
        if pop is None:
            return
        pop.show_near(self)
        try:
            pop.raise_()
        except Exception:
            pass

    def _on_clicked(self):
        # Fallback explicit show on click
        self._show_popup()

    def _maybe_hide_popup(self):
        if not self._over_button and not self._over_popup and self._popup and self._popup.isVisible():
            self._popup.close()

    def eventFilter(self, obj, event):
        # Track pointer over popup or any child window/widget of the popup
        try:
            is_popup_or_child = (obj is self._popup) or (hasattr(obj, 'window') and obj.window() is self._popup)
        except Exception:
            is_popup_or_child = (obj is self._popup)
        if is_popup_or_child:
            if event.type() == QEvent.Enter:
                self._over_popup = True
                if self._hide_timer.isActive():
                    self._hide_timer.stop()
                return True
            if event.type() == QEvent.Leave:
                self._over_popup = False
                self._hide_timer.start(350)
                return True
        return super().eventFilter(obj, event)


