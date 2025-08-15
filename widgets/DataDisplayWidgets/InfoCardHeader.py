from PyQt5.QtCore import Qt, QPoint, QEvent, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame,
    QSizePolicy, QToolButton
)

from ..theme_manager import ThemeManager
from ...constants.file_paths import QssPaths
from ...constants.module_icons import MiscIcons


def _extract_tag_names(item_data: dict):
    tags_edges = ((item_data or {}).get('tags') or {}).get('edges') or []
    names = [((e or {}).get('node') or {}).get('name') for e in tags_edges]
    names = [n.strip() for n in names if isinstance(n, str) and n.strip()]
    return names


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


class TagPopup(QWidget):
    def __init__(self, item_data: dict, parent=None):
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
            names = _extract_tag_names(item_data)
            if not names:
                QTimer.singleShot(0, self.close)
            else:
                from .TagsWidget import TagsWidget  # local import to avoid cycles
                self._tags = TagsWidget(item_data, self)
                lay.addWidget(self._tags)
        except Exception:
            QTimer.singleShot(0, self.close)

        ThemeManager.apply_module_style(self, [QssPaths.PILLS])

    def show_near(self, anchor_widget: QWidget):
        if not anchor_widget:
            self.adjustSize(); self.show(); self.raise_(); return
        try:
            top = anchor_widget.window() if hasattr(anchor_widget, 'window') else None
            if top is not None and self.parent() is not top:
                self.setParent(top, self.windowFlags())
            try:
                self.layout().activate()
            except Exception:
                pass
            self.adjustSize()
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
    def __init__(self, item_data: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("TagsHoverButton")
        self._item = item_data
        self._popup = None
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._maybe_hide_popup)
        self._hide_delay_ms = 600

        try:
            icon = ThemeManager.get_qicon(ThemeManager.ICON_INFO)
            self.setIcon(icon)
            from PyQt5.QtCore import QSize
            self.setIconSize(QSize(14, 14))
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

        self._over_button = False
        self._over_popup = False

    def enterEvent(self, e):
        self._over_button = True
        if self._hide_timer.isActive():
            self._hide_timer.stop()
        self._show_popup()
        return super().enterEvent(e)

    def leaveEvent(self, e):
        self._over_button = False
        self._hide_timer.start(self._hide_delay_ms)
        return super().leaveEvent(e)

    def _ensure_popup(self):
        if self._popup is not None:
            try:
                if not self._popup.isVisible():
                    self._popup.deleteLater(); self._popup = None
            except Exception:
                self._popup = None
        if self._popup is None:
            self._popup = TagPopup(self._item)
            try:
                self._popup.destroyed.connect(lambda _=None: setattr(self, "_popup", None))
            except Exception:
                pass
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
        self._show_popup()

    def _maybe_hide_popup(self):
        if not self._over_button and not self._over_popup and self._popup and self._popup.isVisible():
            self._popup.close()

    def eventFilter(self, obj, event):
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

        # Name row: optional private icon + elided name + number badge + optional tags hover
        nameRow = QHBoxLayout(); nameRow.setContentsMargins(0,0,0,0); nameRow.setSpacing(8 if not compact else 6)

        if not item_data.get('isPublic'):
            privateIcon = QLabel(); privateIcon.setObjectName("ProjectPrivateIcon")
            privateIcon.setToolTip("Privaatne")
            try:
                pm = QPixmap(MiscIcons.ICON_IS_PRIVATE)
                if not pm.isNull():
                    privateIcon.setPixmap(pm.scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                else:
                    privateIcon.setText("P")
            except Exception:
                privateIcon.setText("P")
            privateIcon.setFixedSize(16, 16)
            nameRow.addWidget(privateIcon, 0, Qt.AlignVCenter)

        nameLabel = ElidedLabel(name); nameLabel.setObjectName("ProjectNameLabel"); nameLabel.setToolTip(name)
        nameRow.addWidget(nameLabel, 1, Qt.AlignVCenter)

        numberBadge = QLabel(str(number)); numberBadge.setObjectName("ProjectNumberBadge")
        numberBadge.setAlignment(Qt.AlignCenter); numberBadge.setMinimumWidth(36)
        nameRow.addWidget(numberBadge, 0, Qt.AlignVCenter)

        # Tags hover (only if tags exist)
        try:
            if _extract_tag_names(item_data):
                nameRow.addWidget(TagsHoverButton(item_data), 0, Qt.AlignVCenter)
        except Exception:
            pass

        leftL.addLayout(nameRow)

        # Client row (optional)
        if client:
            clientRow = QHBoxLayout(); clientRow.setContentsMargins(0,0,0,0); clientRow.setSpacing(6)
            clientIcon = QLabel("👤"); clientIcon.setObjectName("ClientIcon"); clientIcon.setFixedWidth(14)
            clientRow.addWidget(clientIcon, 0, Qt.AlignVCenter)

            clientLabel = ElidedLabel(client); clientLabel.setObjectName("ProjectClientLabel"); clientLabel.setToolTip(client)
            clientRow.addWidget(clientLabel, 1, Qt.AlignVCenter)

            leftL.addLayout(clientRow)

        root.addWidget(left, 1, Qt.AlignVCenter)
