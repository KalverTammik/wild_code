import os
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QFrame, QLineEdit, QVBoxLayout, QListWidget, QListWidgetItem
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer
from .theme_manager import IntensityLevels, ThemeManager, is_dark, styleExtras, ThemeShadowColors
from ..constants.button_props import ButtonVariant, ButtonSize
from ..constants.file_paths import QssPaths
from ..constants.module_icons import IconNames

# from ..utils.logger import debug as log_debug
from ..languages.language_manager import LanguageManager
from .SearchResultsWidget import SearchResultsWidget
from ..utils.search.UnifiedSearchController import UnifiedSearchController


class HeaderWidget(QWidget):
    """
    This widget supports dynamic theme switching via ThemeManager.apply_module_style.
    Call retheme_header() to re-apply QSS after a theme change.
    """
    helpRequested = pyqtSignal()
    searchResultClicked = pyqtSignal(str, str, str)  # module, id, title
    
    def __init__(self, title, switch_callback, logout_callback, parent=None, compact=False):
        super().__init__(parent)

        # Outer frame (lets us draw the bottom glow/separator via QSS)
        frame = QFrame(self)
        frame.setObjectName("headerWidgetFrame")

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 6 if not compact else 4, 10, 6 if not compact else 4)
        layout.setSpacing(10)

        # Title (fixed width is okay if you want consistent center balance)
        self.titleLabel = QLabel(title)
        self.titleLabel.setObjectName("headerTitleLabel")
        self.titleLabel.setFixedWidth(180)
        self.titleLabel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.titleFrame = QFrame()
        self.titleFrame.setObjectName("headerTitleFrame")
        frame_layout = QHBoxLayout(self.titleFrame)
        frame_layout.setContentsMargins(8, 2, 8, 2)
        frame_layout.setSpacing(6)
        frame_layout.addWidget(self.titleLabel)
        
        # Help button next to title
        self.helpButton = QPushButton()
        self.helpButton.setObjectName("headerHelpButton")
        self.helpButton.setFixedSize(45, 24)
        # Prevent help button from being the default button that triggers on Return key
        self.helpButton.setAutoDefault(False)
        self.helpButton.setDefault(False)
        self.helpButton.setProperty("variant", ButtonVariant.GHOST)
        self.helpButton.setProperty("btnSize", ButtonSize.SMALL)
        
        # Add help icon and text
        self.helpButton.setIcon(ThemeManager.get_qicon(IconNames.ICON_HELP))
        self.helpButton.setIconSize(QSize(18, 18))
        self.helpButton.setText("Abi")
                    
        # Add tooltip
        tooltip = LanguageManager().translate("help_button_tooltip")
        if tooltip:
            self.helpButton.setToolTip(tooltip)
        
        self.helpButton.clicked.connect(self._emit_help)
        frame_layout.addWidget(self.helpButton)
        layout.addWidget(self.titleFrame, 0, Qt.AlignLeft | Qt.AlignVCenter)

        # Search (center)
        self.searchEdit = QLineEdit()

        placeholder = LanguageManager().translate("search_placeholder")
        self.searchEdit.setPlaceholderText(placeholder)
        self.searchEdit.setObjectName("headerSearchEdit")
        self.searchEdit.setFixedWidth(220)
        
        styleExtras.apply_chip_shadow(
            element=self.searchEdit, 
            color=ThemeShadowColors.GRAY,
            blur_radius=15, 
            x_offset=1, 
            y_offset=1, 
            alpha_level=IntensityLevels.MEDIUM
            )
        # Rakenda tooltip keelefailist
        tooltip = LanguageManager().translate("search_tooltip")
        self.searchEdit.setToolTip(tooltip)
        
        # Initialize search functionality
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._perform_search)
        self.searchEdit.textChanged.connect(self._on_search_text_changed)
        self.searchEdit.returnPressed.connect(self._perform_search)
        
        # Ensure search field maintains focus and handles Return key properly
        self.searchEdit.setFocusPolicy(Qt.StrongFocus)
        
        # Lazy initialization - SearchResultsWidget will be created only when first needed
        self._search_results = None
        self.search_controller = UnifiedSearchController(self)
        self.search_controller.searchSucceeded.connect(self._on_search_success)
        self.search_controller.searchFailed.connect(self._on_search_error)
        self.search_controller.searchStatus.connect(self._on_search_status)
        
        layout.addWidget(self.searchEdit, 1, Qt.AlignHCenter | Qt.AlignVCenter)
        
        # Right: theme switch + logout
        self.switchButton = QPushButton()
        self.switchButton.setObjectName("themeSwitchButton")
        # Prevent button from being triggered by Return key
        self.switchButton.setAutoDefault(False)
        self.switchButton.setDefault(False)
        self.switchButton.setProperty("variant", ButtonVariant.GHOST)
        self.switchButton.clicked.connect(switch_callback)
        # Rakenda tooltip keelefailist
        tooltip = LanguageManager().translate("theme_switch_tooltip")
        self.switchButton.setToolTip(tooltip)
        layout.addWidget(self.switchButton, 0, Qt.AlignRight | Qt.AlignVCenter)

        self.logoutButton = QPushButton("Logout")
        self.logoutButton.setObjectName("logoutButton")
        # Prevent button from being triggered by Return key
        self.logoutButton.setAutoDefault(False)
        self.logoutButton.setDefault(False)
        self.logoutButton.setProperty("variant", ButtonVariant.DANGER)
        self.logoutButton.clicked.connect(logout_callback)

        # Rakenda tooltip keelefailist
        tooltip = LanguageManager().translate("logout_button_tooltip")
        self.logoutButton.setToolTip(tooltip)
        layout.addWidget(self.logoutButton, 0, Qt.AlignRight | Qt.AlignVCenter)

        # Outer zero-margin wrapper (consistent with footer structure)
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(frame)

        self.retheme_header()


    @property
    def search_results_widget(self):
        """Lazy getter for SearchResultsWidget - creates it only when first accessed."""
        if self._search_results is None:

            self._search_results = SearchResultsWidget(self)
            self._search_results.setVisible(False)
            self._search_results.resultClicked.connect(self._on_search_result_clicked)
            self._search_results.refreshRequested.connect(self._on_refresh_requested)
            # log_debug("[DEBUG] SearchResultsWidget created and connected")
        return self._search_results

    def retheme_header(self):
        ThemeManager.apply_module_style(self,[QssPaths.MAIN, QssPaths.BUTTONS, QssPaths.HEADER])
        theme = ThemeManager.effective_theme()
        ThemeManager._update_header_icons(theme, self.switchButton, self.logoutButton)

    def set_title(self, text):
        '''
        Set the header title text form dialog.
        '''
        self.titleLabel.setText(text)

    def _emit_help(self):
        """Emit help requested signal."""
        self.helpRequested.emit()

    def _on_search_text_changed(self, text):
        """Handle search text changes with debouncing."""
        # print(f"[DEBUG] Search text changed: '{text}' (length: {len(text)})")
        # Hide results if text is too short
        if len(text.strip()) < 3:
            # print("[DEBUG] Search text too short, hiding results and stopping timer")
            self.search_results_widget.hide_results()
            self._search_timer.stop()
            self.search_controller.invalidate()
            return
            
        # Restart timer for debounced search
        # print("[DEBUG] Starting search timer (1.5s delay)")
        self._search_timer.start(500)  # 1.5 second delay
    
    def _perform_search(self):
        """Execute the search query in a worker thread."""
        query = self.searchEdit.text().strip()
        if len(query) < 3:
            self.search_results_widget.hide_results()
            return

        self.search_controller.search(query)
    
    def _on_search_result_clicked(self, module, item_id, title):
        """Handle search result selection."""
        # Emit signal for parent to handle navigation
        self.searchResultClicked.emit(module, item_id, title)

    def _on_refresh_requested(self):
        """Handle refresh request from search results widget."""
        # Re-show the current search results with updated expansion state
        query = self.searchEdit.text().strip()
        if len(query) >= 3:
            # print(f"[DEBUG] Refreshing search results for '{query}'")
            self._perform_search()

    def _on_search_status(self, message: str) -> None:
        self.search_results_widget.show_status_message(message, self.searchEdit)

    def _on_search_success(self, search_data) -> None:
        if search_data and any(module.get("total", 0) > 0 for module in search_data):
            self.search_results_widget.show_results(search_data, self.searchEdit)
        else:
            query = self.searchEdit.text().strip()
            self.search_results_widget.show_no_results(query, self.searchEdit)

    def _on_search_error(self, message: str) -> None:
        friendly = message or "Otsing ebaõnnestus"
        self.search_results_widget.show_status_message(friendly, self.searchEdit, is_error=True)
