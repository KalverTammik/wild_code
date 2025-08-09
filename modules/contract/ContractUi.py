from ...ui.ModuleBaseUI import ModuleBaseUI
from PyQt5.QtWidgets import QLabel, QWidget, QVBoxLayout, QScrollArea
from PyQt5.QtCore import Qt
from ...widgets.ModuleFeedBuilder import ModuleFeedBuilder
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
            from ...constants.file_paths import QssPaths
            ThemeManager.apply_module_style(self, [QssPaths.MAIN])


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
        self._activated = False

        # Initial load
        self.load_next_batch()

    def retheme_contract(self):
        """
        Re-applies the correct theme and QSS to the contract module UI, forcing a style refresh.
        """
        if self.theme_manager:
            from ...widgets.theme_manager import ThemeManager
            from ...constants.file_paths import QssPaths
            ThemeManager.apply_module_style(self, [QssPaths.MAIN])
        # Also restyle cards in the feed
        if hasattr(self, 'feed_layout'):
            for i in range(self.feed_layout.count()):
                w = self.feed_layout.itemAt(i).widget()
                if w:
                    from ...widgets.theme_manager import ThemeManager
                    ThemeManager.apply_module_style(w, [QssPaths.MODULE_CARD])

    def on_scroll(self, value):
        bar = self.scroll_area.verticalScrollBar()
        if value == bar.maximum() and self.feed_logic.has_more and not self.feed_logic.is_loading:
            self.load_next_batch()

    def load_next_batch(self):
        items = self.feed_logic.fetch_next_batch()
        ModuleFeedBuilder.add_items_to_feed(self, items)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
