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
        # Ensure minimum height for proper text display
        self.setMinimumHeight(16)

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
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.NoFocus)
        self.setMouseTracking(True)

        # Apply theme-aware enhanced styling
        theme = ThemeManager.load_theme_setting() if hasattr(ThemeManager, 'load_theme_setting') else 'light'

        if theme == 'dark':
            self.setStyleSheet("""
                QWidget#TagsPopup {
                    background-color: rgba(33, 37, 43, 0.95) !important;
                    border: 2px solid rgba(9, 144, 143, 0.4) !important;
                    border-radius: 8px !important;
                    box-shadow: 0 4px 16px rgba(0,0,0,0.3), 0 2px 8px rgba(9, 144, 143, 0.15) !important;
                }
                QLabel#TagsPopupHeader {
                    font-size: 11px !important;
                    font-weight: 600 !important;
                    color: rgba(197,197,210,0.8) !important;
                    margin-bottom: 4px !important;
                    background: transparent !important;
                }
            """)
        else:  # light theme
            self.setStyleSheet("""
                QWidget#TagsPopup {
                    background-color: rgba(255, 255, 255, 0.95) !important;
                    border: 2px solid rgba(9, 144, 143, 0.3) !important;
                    border-radius: 8px !important;
                    box-shadow: 0 4px 16px rgba(0,0,0,0.15), 0 2px 8px rgba(9, 144, 143, 0.1) !important;
                }
                QLabel#TagsPopupHeader {
                    font-size: 11px !important;
                    font-weight: 600 !important;
                    color: rgba(36,41,46,0.8) !important;
                    margin-bottom: 4px !important;
                    background: transparent !important;
                }
            """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(8)

        try:
            names = _extract_tag_names(item_data)
            if not names:
                QTimer.singleShot(0, self.close)
            else:
                # Use CompactTagsWidget for better display
                from .TagsWidget import CompactTagsWidget
                self._tags = CompactTagsWidget(item_data, max_visible=10)  # Show more in popup
                lay.addWidget(self._tags)

                # Add a subtle header
                header = QLabel(f"Tags ({len(names)})")
                header.setObjectName("TagsPopupHeader")
                lay.insertWidget(0, header)
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
            # Reapply theme-aware styling to ensure it takes precedence
            theme = ThemeManager.load_theme_setting() if hasattr(ThemeManager, 'load_theme_setting') else 'light'

            if theme == 'dark':
                self.setStyleSheet("""
                    QWidget#TagsPopup {
                        background-color: rgba(33, 37, 43, 0.95) !important;
                        border: 2px solid rgba(9, 144, 143, 0.4) !important;
                        border-radius: 8px !important;
                        box-shadow: 0 4px 16px rgba(0,0,0,0.3), 0 2px 8px rgba(9, 144, 143, 0.15) !important;
                    }
                    QLabel#TagsPopupHeader {
                        font-size: 11px !important;
                        font-weight: 600 !important;
                        color: rgba(197,197,210,0.8) !important;
                        margin-bottom: 4px !important;
                        background: transparent !important;
                    }
                """)
            else:  # light theme
                self.setStyleSheet("""
                    QWidget#TagsPopup {
                        background-color: rgba(255, 255, 255, 0.95) !important;
                        border: 2px solid rgba(9, 144, 143, 0.3) !important;
                        border-radius: 8px !important;
                        box-shadow: 0 4px 16px rgba(0,0,0,0.15), 0 2px 8px rgba(9, 144, 143, 0.1) !important;
                    }
                    QLabel#TagsPopupHeader {
                        font-size: 11px !important;
                        font-weight: 600 !important;
                        color: rgba(36,41,46,0.8) !important;
                        margin-bottom: 4px !important;
                        background: transparent !important;
                    }
                """)

            # Apply CSS theme as well
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

        # Get tag count for better icon indication
        tags_edges = ((item_data or {}).get('tags') or {}).get('edges') or []
        tag_count = len([e for e in tags_edges if ((e or {}).get('node') or {}).get('name')])

        # Use a more intuitive icon - tags/label icon
        try:
            # Try to get a tags icon, fallback to info if not available
            icon = ThemeManager.get_qicon(ThemeManager.ICON_INFO)
            self.setIcon(icon)
            from PyQt5.QtCore import QSize
            self.setIconSize(QSize(12, 12))  # Smaller, more subtle
        except Exception:
            self.setText("🏷️")  # Fallback emoji

        # Set tooltip with tag count
        self.setToolTip(f"Tags ({tag_count}) - hover to view")
        self.setAutoRaise(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(18, 18)  # Smaller button
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.NoFocus)

        # Style the button to be more subtle
        self.setStyleSheet("""
            QToolButton#TagsHoverButton {
                border: none;
                background: transparent;
                color: rgba(197,197,210,0.7);
                border-radius: 2px;
                padding: 1px;
            }
            QToolButton#TagsHoverButton:hover {
                background: rgba(9,144,143,0.1);
                color: rgba(9,144,143,0.9);
            }
        """)

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
    def __init__(self, item_data, parent=None, compact=False, module_name=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        self.setObjectName("InfocardHeaderFrame")
        self.setProperty("compact", compact)
        self.module_name = module_name or "default"

        root = QHBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(6 if not compact else 4)

        # Left column
        left = QFrame(self); left.setObjectName("HeaderLeft")
        leftL = QVBoxLayout(left); leftL.setContentsMargins(0, 0, 0, 0); leftL.setSpacing(1 if not compact else 0)

        name = item_data.get('name', 'No Name') or 'No Name'
        number = item_data.get('number', '-')
        client = (item_data.get('client') or {}).get('displayName')

        # Check if numbers should be shown for this module
        show_numbers = self._should_show_numbers()

        # Name row: conditional layout based on number display setting
        nameRow = QHBoxLayout(); nameRow.setContentsMargins(0,0,0,0); nameRow.setSpacing(6 if not compact else 4)

        if not item_data.get('isPublic'):
            privateIcon = QLabel(); privateIcon.setObjectName("ProjectPrivateIcon")
            privateIcon.setToolTip("Privaatne")
            try:
                pm = QPixmap(MiscIcons.ICON_IS_PRIVATE)
                if not pm.isNull():
                    privateIcon.setPixmap(pm.scaled(14, 14, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                else:
                    privateIcon.setText("P")
            except Exception:
                privateIcon.setText("P")
            privateIcon.setFixedSize(14, 14)
            nameRow.addWidget(privateIcon, 0, Qt.AlignVCenter)

        # If showing numbers, display them before the name
        if show_numbers and number and number != '-':
            numberBadge = QLabel(str(number)); numberBadge.setObjectName("ProjectNumberBadge")
            numberBadge.setAlignment(Qt.AlignCenter); numberBadge.setMinimumWidth(24 if not compact else 20)
            nameRow.addWidget(numberBadge, 0, Qt.AlignVCenter)

        nameLabel = ElidedLabel(name); nameLabel.setObjectName("ProjectNameLabel"); nameLabel.setToolTip(name)
        nameRow.addWidget(nameLabel, 1, Qt.AlignVCenter)

        # When not showing numbers, don't display them at all (no stretch needed)

        # Tags hover (only if tags exist) - back to icon approach for space efficiency
        try:
            if _extract_tag_names(item_data):
                nameRow.addWidget(TagsHoverButton(item_data), 0, Qt.AlignVCenter)
        except Exception:
            pass

        leftL.addLayout(nameRow)

        # Client row (optional)
        if client:
            clientRow = QHBoxLayout(); clientRow.setContentsMargins(0,0,0,0); clientRow.setSpacing(4)
            clientIcon = QLabel("👤"); clientIcon.setObjectName("ClientIcon"); clientIcon.setFixedWidth(12)
            clientRow.addWidget(clientIcon, 0, Qt.AlignVCenter)

            clientLabel = ElidedLabel(client); clientLabel.setObjectName("ProjectClientLabel"); clientLabel.setToolTip(client)
            clientRow.addWidget(clientLabel, 1, Qt.AlignVCenter)

            leftL.addLayout(clientRow)

        root.addWidget(left, 1, Qt.AlignVCenter)

    def _should_show_numbers(self):
        """Check if numbers should be displayed for this module."""
        try:
            from ..theme_manager import ThemeManager
            show_numbers = ThemeManager.load_module_setting(self.module_name, "show_numbers", True)
            return bool(show_numbers)
        except Exception:
            return True  # Default to showing numbers if there's an error
