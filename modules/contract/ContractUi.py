from ...ui.ModuleBaseUI import ModuleBaseUI
from PyQt5.QtWidgets import QLabel, QWidget, QVBoxLayout, QScrollArea
from PyQt5.QtCore import Qt, QTimer
from ...widgets.DataDisplayWidgets.ModuleFeedBuilder import ModuleFeedBuilder
from ...constants.file_paths import QssPaths

class ContractUi(ModuleBaseUI):
    """
    UI layer for the Contract module.
    This class builds the QWidget tree and applies theme styles via ThemeManager.
    """
    def __init__(self, lang_manager=None, theme_manager=None, parent=None, logic=None):
        super().__init__(parent)
        self.lang_manager = lang_manager
        self.theme_manager = theme_manager
        self.logic = logic
        # Ensure predictable QSS targeting
        self.setObjectName("ContractModule")

        # Centralized theming
        if self.theme_manager:
            from ...widgets.theme_manager import ThemeManager
            ThemeManager.apply_module_style(self, [QssPaths.MODULES_MAIN])

        # Clear ModuleBaseUI placeholders to let scroll area take full space
        try:
            lay = self.display_area.layout()
            while lay and lay.count():
                item = lay.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()
        except Exception:
            pass

        # Build feed area similar to Projects
        self.feed_content = QWidget()
        from PyQt5.QtWidgets import QSizePolicy
        self.feed_content.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.feed_layout = QVBoxLayout()
        self.feed_content.setLayout(self.feed_layout)
        self.feed_layout.addStretch(1)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.feed_content)
        self.display_area.layout().addWidget(self.scroll_area)

        # Setup contracts feed logic
        from .ContractLogic import ContractsFeedLogic
        self.feed_logic = ContractsFeedLogic("CONTRACT", "ListAllContracts.graphql", lang_manager)

        # Connect scroll event for infinite scroll
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.on_scroll)
        self.scroll_area.verticalScrollBar().rangeChanged.connect(self.on_range_changed)
        self._activated = False

        # Initial load removed; will load on activate()
        # self.load_next_batch()

    def activate(self):
        if not getattr(self, "_activated", False):
            self._activated = True
            self.load_next_batch()

    def retheme_contract(self):
        """
        Re-applies the correct theme and QSS to the contract module UI, forcing a style refresh.
        """
        if self.theme_manager:
            from ...widgets.theme_manager import ThemeManager
            from ...constants.file_paths import QssPaths
            ThemeManager.apply_module_style(self, [QssPaths.MODULES_MAIN])
        # Also restyle cards in the feed
        if hasattr(self, 'feed_layout'):
            for i in range(self.feed_layout.count()):
                w = self.feed_layout.itemAt(i).widget()
                if w:
                    from ...widgets.theme_manager import ThemeManager
                    ThemeManager.apply_module_style(w, [QssPaths.MODULE_CARD])

    def on_scroll(self, value):
        bar = self.scroll_area.verticalScrollBar()
        # Debug: observe scrolling values
        try:
            print(f"[ContractUi] Scroll value={value}, max={bar.maximum()}, has_more={self.feed_logic.has_more}, is_loading={self.feed_logic.is_loading}")
        except Exception:
            pass
        # Allow a small threshold to ensure we trigger near-bottom
        if value >= max(0, bar.maximum() - 2) and self.feed_logic.has_more and not self.feed_logic.is_loading:
            self.load_next_batch()

    def on_range_changed(self, min_val, max_val):
        # When content grows or initial range is set, auto-load if we're effectively at bottom and more is available
        bar = self.scroll_area.verticalScrollBar()
        try:
            print(f"[ContractUi] Range changed: min={min_val}, max={max_val}, current={bar.value()}, has_more={self.feed_logic.has_more}")
        except Exception:
            pass
        if bar.value() >= max(0, max_val - 2) and self.feed_logic.has_more and not self.feed_logic.is_loading:
            # Slight delay to let layout settle
            QTimer.singleShot(0, self.load_next_batch)

    def load_next_batch(self):
        # Fetch and append, then auto-fill if still no scroll
        prev_max = self.scroll_area.verticalScrollBar().maximum()
        items = self.feed_logic.fetch_next_batch()
        try:
            print(f"[ContractUi] Loaded items: {len(items)} (prev_max={prev_max})")
        except Exception:
            pass
        if not items:
            return
        ModuleFeedBuilder.add_items_to_feed(self, items)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        # If after adding there is still no scroll room and more pages are available, auto-load next page
        def _maybe_autofill():
            bar = self.scroll_area.verticalScrollBar()
            if bar.maximum() <= 0 and self.feed_logic.has_more and not self.feed_logic.is_loading:
                try:
                    print("[ContractUi] Auto-filling next batch (no scroll yet)")
                except Exception:
                    pass
                self.load_next_batch()
        QTimer.singleShot(0, _maybe_autofill)
