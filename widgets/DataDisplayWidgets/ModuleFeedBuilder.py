from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFrame,
    QGraphicsDropShadowEffect
)
from .StatusWidget import StatusWidget
from .MembersView import MembersView
from .ExtraInfoWidget import ExtraInfoFrame
from .InfoCardHeader import InfocardHeaderFrame
from ..theme_manager import ThemeManager
from ...constants.file_paths import QssPaths


# ================== Module Feed ==================
class ModuleFeedBuilder:
    @staticmethod
    def _item_has_tags(item_data: dict) -> bool:
        try:
            names = ModuleFeedBuilder._extract_tag_names(item_data)
            return len(names) > 0
        except Exception:
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
        content = QFrame()
        content.setObjectName("CardContent")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(6)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(0)
        header_row.addWidget(InfocardHeaderFrame(item), alignment=Qt.AlignTop)
        header_row.addStretch(1)
        header_row.addWidget(MembersView(item), alignment=Qt.AlignRight | Qt.AlignTop)
        cl.addLayout(header_row)

        cl.addWidget(ExtraInfoFrame(item))
        main.addWidget(content, 1)

        # Right status column
        status_col = QVBoxLayout()
        status_col.setContentsMargins(0, 0, 0, 0)
        # Hide private icon here; it's shown in the header component
        status_col.addWidget(StatusWidget(item, show_private_icon=False), alignment=Qt.AlignTop | Qt.AlignRight)
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
    def add_items_to_feed(parent_ui, items):
        """Append cards for given items into parent_ui.feed_layout above the stretch, with theming."""
        if not items:
            return
        layout = getattr(parent_ui, 'feed_layout', None)
        if layout is None:
            return
        insert_index = max(0, layout.count() - 1)
        added = 0
        for item in items:
            try:
                card = ModuleFeedBuilder.create_item_card(item)
                # Apply theme styling to each card
                try:
                    ThemeManager.apply_module_style(card, [QssPaths.MODULE_CARD])
                except Exception:
                    pass
                layout.insertWidget(insert_index, card)
                insert_index += 1
                added += 1
            except Exception as e:
                # Skip bad item but keep feed responsive
                try:
                    print(f"[ModuleFeedBuilder] Failed to build card: {e}")
                except Exception:
                    pass
        # One-line debug for added count
        try:
            print(f"[ModuleFeedBuilder] Added {added} card(s)")
        except Exception:
            pass


