import os
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QFrame, QLineEdit, QVBoxLayout, QListWidget, QListWidgetItem
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer, QEvent
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from PyQt5.QtGui import QColor, QIcon, QFont

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
        frame_layout.setSpacing(5)
        frame_layout.addWidget(self.titleLabel)
        
        # Help button next to title
        self.helpButton = QPushButton()
        self.helpButton.setObjectName("headerHelpButton")
        self.helpButton.setFixedSize(45, 24)
        # Prevent help button from being the default button that triggers on Return key
        self.helpButton.setAutoDefault(False)
        self.helpButton.setDefault(False)
        # Add help icon and text
        try:
            from wild_code.constants.module_icons import ModuleIconPaths, ICON_HELP
            help_icon_path = ModuleIconPaths.themed(ICON_HELP)
            if help_icon_path:
                self.helpButton.setIcon(QIcon(help_icon_path))
                self.helpButton.setIconSize(QSize(18, 18))
                self.helpButton.setText("Abi")
            else:
                self.helpButton.setText("Abi")
        except Exception:
            self.helpButton.setText("Abi")
        
        # Add tooltip
        try:
            from wild_code.languages.language_manager import LanguageManager
            lang_manager = LanguageManager()
            tooltip = lang_manager.translations.get("help_button_tooltip", "")
            if tooltip:
                self.helpButton.setToolTip(tooltip)
        except Exception:
            pass
        
        self.helpButton.clicked.connect(self._emit_help)
        frame_layout.addWidget(self.helpButton)
        layout.addWidget(self.titleFrame, 0, Qt.AlignLeft | Qt.AlignVCenter)

        # Search (center)
        self.searchEdit = QLineEdit()
        try:
            from wild_code.languages.language_manager import LanguageManager
            lang_manager = LanguageManager()
            placeholder = lang_manager.translations.get("search_placeholder", "search_placeholder")
            self.searchEdit.setPlaceholderText(placeholder)
        except Exception:
            self.searchEdit.setPlaceholderText("search_placeholder")
        self.searchEdit.setObjectName("headerSearchEdit")
        self.searchEdit.setFixedWidth(220)
        shadow = QGraphicsDropShadowEffect(self.searchEdit)
        shadow.setBlurRadius(14)                  # softer spread
        shadow.setXOffset(0)
        shadow.setYOffset(1)
        shadow.setColor(QColor(9, 144, 143, 60))   # teal accent glow (rgb, alpha)
        self.searchEdit.setGraphicsEffect(shadow)
        # Rakenda tooltip keelefailist
        try:
            from wild_code.languages.language_manager import LanguageManager
            lang_manager = LanguageManager()
            tooltip = lang_manager.translations.get("search_tooltip", "search_tooltip")
            self.searchEdit.setToolTip(tooltip)
        except Exception:
            self.searchEdit.setToolTip("search_tooltip")
        
        # Initialize search functionality
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._perform_search)
        self.searchEdit.textChanged.connect(self._on_search_text_changed)
        self.searchEdit.returnPressed.connect(self._perform_search)
        
        # Ensure search field maintains focus and handles Return key properly
        self.searchEdit.setFocusPolicy(Qt.StrongFocus)
        
        # print("[DEBUG] HeaderWidget search setup complete")
        
        # Lazy initialization - SearchResultsWidget will be created only when first needed
        self._search_results = None
        
        layout.addWidget(self.searchEdit, 1, Qt.AlignHCenter | Qt.AlignVCenter)
        
        # Right: Dev controls + theme switch + logout
        # Optional callbacks set by parent controller
        self.on_toggle_debug = None
        self.on_toggle_frame_labels = None

        # Dev controls extracted into dedicated widget
        from .DevControlsWidget import DevControlsWidget
        self.devControls = DevControlsWidget()
        self.devControls.toggleDebugRequested.connect(self._emit_debug_toggle)
        self.devControls.toggleFrameLabelsRequested.connect(self._emit_frame_labels_toggle)
        layout.addWidget(self.devControls, 0, Qt.AlignRight | Qt.AlignVCenter)

        # Right: theme switch + logout
        self.switchButton = QPushButton()
        self.switchButton.setObjectName("themeSwitchButton")
        # Prevent button from being triggered by Return key
        self.switchButton.setAutoDefault(False)
        self.switchButton.setDefault(False)
        self.switchButton.clicked.connect(switch_callback)
        # Rakenda tooltip keelefailist
        try:
            from wild_code.languages.language_manager import LanguageManager
            lang_manager = LanguageManager()
            tooltip = lang_manager.translations.get("theme_switch_tooltip", "theme_switch_tooltip")
            self.switchButton.setToolTip(tooltip)
        except Exception:
            self.switchButton.setToolTip("theme_switch_tooltip")
        layout.addWidget(self.switchButton, 0, Qt.AlignRight | Qt.AlignVCenter)

        self.logoutButton = QPushButton("Logout")
        self.logoutButton.setObjectName("logoutButton")
        # Prevent button from being triggered by Return key
        self.logoutButton.setAutoDefault(False)
        self.logoutButton.setDefault(False)
        self.logoutButton.clicked.connect(logout_callback)
        # Rakenda tooltip keelefailist
        try:
            from wild_code.languages.language_manager import LanguageManager
            lang_manager = LanguageManager()
            tooltip = lang_manager.translations.get("logout_button_tooltip", "logout_button_tooltip")
            self.logoutButton.setToolTip(tooltip)
        except Exception:
            self.logoutButton.setToolTip("logout_button_tooltip")
        layout.addWidget(self.logoutButton, 0, Qt.AlignRight | Qt.AlignVCenter)

        # Outer zero-margin wrapper (consistent with footer structure)
        outer = QHBoxLayout(self)

        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(frame)

        # Apply theme (main + header)
        from .theme_manager import ThemeManager
        from wild_code.constants.file_paths import QssPaths
        ThemeManager.apply_module_style(self, [QssPaths.MAIN, QssPaths.HEADER])
        # Ensure DevControls' own QSS is applied last so its specific rules override header's generic QPushButton
        try:
            self.devControls.retheme()
        except Exception:
            pass

    @property
    def search_results_widget(self):
        """Lazy getter for SearchResultsWidget - creates it only when first accessed."""
        if self._search_results is None:
            print("[DEBUG] Lazy loading SearchResultsWidget...")
            from .SearchResultsWidget import SearchResultsWidget
            self._search_results = SearchResultsWidget(self)
            self._search_results.setVisible(False)
            self._search_results.resultClicked.connect(self._on_search_result_clicked)
            self._search_results.refreshRequested.connect(self._on_refresh_requested)
            print("[DEBUG] SearchResultsWidget created and connected")
        return self._search_results


    def _emit_debug_toggle(self, enabled: bool):
        cb = getattr(self, 'on_toggle_debug', None)
        if callable(cb):
            try:
                cb(bool(enabled))
            except Exception:
                pass

    def _emit_frame_labels_toggle(self, enabled: bool):
        cb = getattr(self, 'on_toggle_frame_labels', None)
        if callable(cb):
            try:
                cb(bool(enabled))
            except Exception:
                pass

    def set_switch_icon(self, icon):
        self.switchButton.setIcon(icon)
        self.switchButton.setText("")

    def set_logout_icon(self, icon):
        self.logoutButton.setIcon(icon)
        self.logoutButton.setText("")

    def retheme_header(self):
        from .theme_manager import ThemeManager
        from wild_code.constants.file_paths import QssPaths
        ThemeManager.apply_module_style(self, [QssPaths.MAIN, QssPaths.HEADER])
        try:
            self.devControls.retheme()
        except Exception:
            pass

    def set_title(self, text):
        self.titleLabel.setText(text)

    def _open_home(self):
        pass  # home nupp eemaldatud (kasuta külgriba Avaleht nuppu)
        # Emit a custom signal or call a callback to open the welcome page
        if hasattr(self, 'open_home_callback') and callable(self.open_home_callback):
            self.open_home_callback()

    def set_dev_states(self, debug_enabled: bool, frames_enabled: bool):
        """Initialize or update the dev controls' checked states."""
        try:
            self.devControls.set_states(bool(debug_enabled), bool(frames_enabled))
        except Exception:
            pass

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
            return
            
        # Restart timer for debounced search
        # print("[DEBUG] Starting search timer (1.5s delay)")
        self._search_timer.start(1500)  # 1.5 second delay
    
    def _perform_search(self):
        """Execute the search query."""
        query = self.searchEdit.text().strip()
        # print(f"[DEBUG] Performing search for query: '{query}'")
        if len(query) < 3:
            # print("[DEBUG] Query too short, aborting search")
            return
            
        try:
            # print("[DEBUG] Importing required modules for search")
            # Import required modules
            from ..utils.api_client import APIClient
            from ..utils.GraphQLQueryLoader import GraphQLQueryLoader
            from ..languages.language_manager import LanguageManager
            
            # Create language manager for GraphQL loader
            lang_manager = LanguageManager()
            query_loader = GraphQLQueryLoader(lang_manager)
            # print("[DEBUG] Loading search query from GraphQL loader")
            search_query = query_loader.load_query("user", "search.graphql")
            
            if not search_query:
                # print("Warning: Could not load search query")
                return
                
            # Execute search
            api_client = APIClient(lang_manager)
            # Use the working term or original query
            variables = {
                "input": {
                    "term": query,
                    "types": [
                        "PROPERTIES", "PROJECTS", "TASKS",
                        "SUBMISSIONS", "EASEMENTS",
                        "COORDINATIONS", "SPECIFICATIONS", "ORDINANCES",
                        "CONTRACTS"
                    ],

                    ##### ALL POSSIBLE SEARCH TYPES ######
                    #"types": [
                    #    "PROPERTIES", "CONTACTS", "TASKS", "PROJECTS",
                    #    "METERS", "LETTERS", "SUBMISSIONS", "EASEMENTS",
                    #    "COORDINATIONS", "SPECIFICATIONS", "ORDINANCES",
                    #    "CONTRACTS", "PRODUCTS", "INVOICES", "EXPENSES", "QUOTES"
                    #],

                    "limit": 5
                }
            }
            # print(f"[DEBUG] Sending GraphQL query with variables: {variables}")
            
            result = api_client.send_query(search_query, variables, operation_name=None)
            print(f"[DEBUG] Raw API response: {result}")
            # print(f"[DEBUG] Response type: {type(result)}")
            
            if result and "data" in result and "search" in result["data"]:
                search_data = result["data"]["search"]
                # print(f"[DEBUG] Processing unified search results: {len(search_data)} module types")

                # Let SearchResultsWidget process the results
                processed_results = self.search_results_widget.process_unified_search_results(search_data)
                # print(f"[DEBUG] Processed {len(processed_results)} total search results")

                # Show results
                if processed_results:
                    # print("[DEBUG] Showing search results")
                    self.search_results_widget.show_results(processed_results, self.searchEdit)
                else:
                    # print(f"[DEBUG] No results found for '{query}', showing no results message")
                    self.search_results_widget.show_no_results(query, self.searchEdit)

            elif result and "search" in result:
                # Handle direct search response (no data wrapper)
                search_data = result["search"]
                # print(f"[DEBUG] Processing direct search results: {len(search_data)} module types")

                # Let SearchResultsWidget process the results with raw data
                processed_results = self.search_results_widget.process_unified_search_results(search_data)
                # print(f"[DEBUG] Processed {len(processed_results)} total search results")

                # Show results with raw search data for grouping
                if any(module.get("total", 0) > 0 for module in search_data):
                    # print("[DEBUG] Showing search results")
                    self.search_results_widget.show_results(search_data, self.searchEdit)
                else:
                    # print(f"[DEBUG] No results found for '{query}', showing no results message")
                    self.search_results_widget.show_no_results(query, self.searchEdit)

        except Exception as e:
            # print(f"Search error: {e}")
            # import traceback
            # traceback.print_exc()
            self.search_results_widget.hide_results()
    
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
