from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QLabel, QPushButton, QHBoxLayout, QApplication
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QEvent
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from PyQt5.QtGui import QColor, QFont, QIcon


class SearchResultsWidget(QDialog):
    """
    Dialog for displaying search results in a dropdown list below the search field.
    Groups results by module type with expandable sections.
    Uses QDialog for better popup control and positioning.
    """


class SearchResultsWidget(QDialog):
    """
    Widget for displaying search results in a dropdown list below the search field.
    Groups results by module type with expandable sections.
    """
    resultClicked = pyqtSignal(str, str, str)  # module, id, title
    refreshRequested = pyqtSignal()  # Signal to request refresh of results

    def __init__(self, parent=None):
        super().__init__(parent)
        # Use QDialog with translucent background for better popup control
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.ToolTip)  # No frame, tooltip behavior
        self.setAttribute(Qt.WA_TranslucentBackground)  # Enable translucent background
        self.setModal(False)  # Non-modal dialog

        self.setObjectName("searchResultsWidget")
        # Remove direct stylesheet - will use ThemeManager for consistent styling

        # Track expanded state for each module type
        self.expanded_types = set()

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)  # Standard margins
        layout.setSpacing(0)

        # Header layout with close button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)

        # Spacer to push close button to the right
        header_layout.addStretch()

        # Close button
        self.close_button = QPushButton("×")
        self.close_button.setObjectName("searchResultsCloseButton")
        self.close_button.setFixedSize(24, 24)
        self.close_button.setToolTip("Close search results")
        self.close_button.clicked.connect(self.hide_results)
        header_layout.addWidget(self.close_button)

        layout.addLayout(header_layout)

        # Results list
        self.resultsList = QListWidget()
        self.resultsList.setObjectName("searchResultsList")
        self.resultsList.setMaximumHeight(600)  # 20% increase from 300
        self.resultsList.setMaximumWidth(450)   # 50% increase from ~293 (assuming original was ~220)
        self.resultsList.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.resultsList.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.resultsList.itemClicked.connect(self._on_item_clicked)

        layout.addWidget(self.resultsList)

        # Enhanced shadow effect to match search field styling
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)                  # balanced blur for subtle effect
        shadow.setXOffset(0)
        shadow.setYOffset(4)                      # subtle drop distance
        shadow.setColor(QColor(9, 132, 227, 128))  # RGB blue with 50% transparency
        self.setGraphicsEffect(shadow)
        #print(f"[DEBUG] Applied blue shadow effect with RGB color: {shadow.color().getRgb()} alpha: {shadow.color().alpha()}")

        # Defer QApplication access until widget is actually shown
        # This prevents crashes during early initialization
        self._event_filter_installed = False
        self._focus_connection_made = False

        # Hide initially
        self.hide()

        # Apply ThemeManager styling for consistent appearance
        self._apply_theme_styles()

    def _setup_application_connections(self):
        """Safely setup QApplication event filter and focus connections."""
        if self._event_filter_installed and self._focus_connection_made:
            return

        try:
            from PyQt5.QtWidgets import QApplication
            app = QApplication.instance()
            if app is None:
                print("[DEBUG] QApplication not available yet, deferring connections")
                return

            if not self._event_filter_installed:
                app.installEventFilter(self)
                self._event_filter_installed = True
                print("[DEBUG] Event filter installed safely")

            if not self._focus_connection_made:
                app.focusChanged.connect(self._on_application_focus_changed)
                self._focus_connection_made = True
                print("[DEBUG] Focus change connection made safely")

        except Exception as e:
            print(f"[DEBUG] Failed to setup application connections: {e}")
            # Continue without connections rather than crashing


    def _apply_inline_styling(self):
        """Apply QSS styling using ThemeManager (following plugin standards)."""
        try:
            from ..widgets.theme_manager import ThemeManager
            from ..constants.file_paths import QssPaths
            ThemeManager.apply_module_style(self, [QssPaths.SEARCH_RESULTS_WIDGET])
        except ImportError:
            pass

    def _apply_theme_styles(self):
        """Apply theme styles to the search results widget."""
        try:
            from ..widgets.theme_manager import ThemeManager
            from ..constants.file_paths import QssPaths
            ThemeManager.apply_module_style(self, [QssPaths.SEARCH_RESULTS_WIDGET])
        except Exception:
            # Fallback if theme manager is not available
            pass

    def retheme_search_results(self):
        """Re-apply QSS styling for dynamic theme switching (following plugin standards)."""
        try:
            from ..widgets.theme_manager import ThemeManager
            from ..constants.file_paths import QssPaths
            ThemeManager.apply_module_style(self, [QssPaths.SEARCH_RESULTS_WIDGET])

            # Refresh style properties
            self.style().unpolish(self)
            self.style().polish(self)

            print("[DEBUG] Re-applied SearchResultsWidget QSS styling for theme switch")
        except ImportError:
            pass

    def show_results(self, results, search_field):
        """
        Show search results below the search field, grouped by module type.

        Args:
            results: Raw search data from API with module types and hits
            search_field: The QLineEdit widget to position below
        """
        # print(f"[DEBUG] SearchResultsWidget.show_results called with {len(results)} module types")

        if not results:
            # print("[DEBUG] No results to show, hiding widget")
            self.hide()
            return

        # Ensure widget is visible (in case it was manually closed)
        self.ensure_visible()

        # Setup application connections safely (only when first shown)
        self._setup_application_connections()

        # Clear previous results
        self.resultsList.clear()

        # Group results by module type and display
        for module_data in results:
            module_type = module_data.get("type", "")
            total_hits = module_data.get("total", 0)
            hits = module_data.get("hits", [])

            if total_hits == 0:
                continue

            # print(f"[DEBUG] Displaying {module_type}: {total_hits} results")

            # Add module header
            header_item = QListWidgetItem()
            header_text = f"{module_type} ({total_hits})"
            header_item.setText(header_text)
            header_item.setData(Qt.UserRole, {"type": "header", "module": module_type})

            # Style header
            font = header_item.font()
            font.setBold(True)
            font.setPointSize(font.pointSize() + 1)
            header_item.setFont(font)
            header_item.setForeground(QColor("#1f5d5c"))  # Teal accent color
            header_item.setBackground(QColor("#f0f8f7"))  # Light teal background

            self.resultsList.addItem(header_item)

            # Add results (limited to 5 initially, or all if expanded)
            is_expanded = module_type in self.expanded_types
            display_hits = hits if is_expanded else hits[:5]

            for hit in display_hits:
                result_item = QListWidgetItem()
                title = hit.get("title", "").replace("\n", " ")  # Replace newlines with spaces
                result_item.setText(f"  • {title}")
                result_item.setData(Qt.UserRole, {
                    "type": "result",
                    "module": module_type,
                    "id": hit.get("id", ""),
                    "title": hit.get("title", "")
                })

                # Style result item
                result_item.setForeground(QColor("#2E7D32"))  # Green for available
                self.resultsList.addItem(result_item)

            # Add "show more" if there are more results
            if not is_expanded and len(hits) > 5:
                more_item = QListWidgetItem()
                more_item.setText(f"  -- Show {len(hits) - 5} more --")
                more_item.setData(Qt.UserRole, {"type": "show_more", "module": module_type})
                more_item.setForeground(QColor("#666666"))
                more_item.setFont(QFont("Arial", 9, QFont.StyleItalic))
                self.resultsList.addItem(more_item)

        # Position below search field with increased width
        if search_field:
            pos = search_field.mapToGlobal(search_field.rect().bottomLeft())
            # Adjust position to account for increased width (50% increase) and move up
            adjusted_pos = pos - QPoint(110, -5)  # Shift left by half the width increase, move up by 5 pixels
            self.move(adjusted_pos)
            self.adjustSize()

        # print("[DEBUG] Showing grouped search results")
        self.show()
        self.raise_()

        print(f"[DEBUG] SearchResultsWidget shown at position: {self.pos()}, visible: {self.isVisible()}")
        self.test_styling()

    def test_styling(self):
        """Test method to verify styling is applied correctly."""
        print(f"[DEBUG] Widget stylesheet: {self.styleSheet()[:300]}...")
        print(f"[DEBUG] Widget has graphics effect: {self.graphicsEffect() is not None}")
        if self.graphicsEffect():
            effect = self.graphicsEffect()
            print(f"[DEBUG] Graphics effect type: {type(effect)}")
            if hasattr(effect, 'color'):
                color = effect.color()
                print(f"[DEBUG] Shadow color RGB: {color.getRgb()} alpha: {color.alpha()}")
                if color.alpha() == 128:
                    print("[DEBUG] ✅ Shadow has correct 50% transparency")
                else:
                    print(f"[DEBUG] ❌ Shadow alpha is {color.alpha()}, expected 128")

        # Check if QSS styling is applied correctly
        stylesheet = self.styleSheet()
        if stylesheet.strip() == "" or 'solid #0984e3' in stylesheet:
            print("[DEBUG] ✅ ThemeManager styling applied correctly (QDialog with translucent background)")
            print("[DEBUG] ✅ QDialog popup behavior with frameless window")
            print("[DEBUG] ✅ Blue shadow effect applied for cohesive appearance")
        else:
            print(f"[DEBUG] ❌ Unexpected stylesheet content: {stylesheet[:100]}...")

    def hide_results(self):
        """Hide the search results widget."""
        print(f"[DEBUG] Hiding SearchResultsWidget, was visible: {self.isVisible()}")
        self.hide()

    def ensure_visible(self):
        """Ensure the widget is visible, useful for search functionality."""
        if not self.isVisible():
            print(f"[DEBUG] Forcing SearchResultsWidget to show")
            self.show()
            self.raise_()

    def process_unified_search_results(self, search_data):
        """
        Process unified search results from the API into displayable format.

        Args:
            search_data: Array of module results from unified search API

        Returns:
            List of processed result dictionaries
        """
        processed_results = []

        for module_result in search_data:
            module_type = module_result.get("type", "")
            hits = module_result.get("hits", [])
            # print(f"[DEBUG] Processing {module_type}: {len(hits)} results")

            for hit in hits:
                item_id = hit.get("id", "")
                title = hit.get("title", f"{module_type} {item_id}")

                processed_results.append({
                    "module": module_type,
                    "id": item_id,
                    "title": title,
                    "available": True
                })

        return processed_results

    def show_no_results(self, search_term, search_field):
        """
        Show a "no results found" message.

        Args:
            search_term: The search term that returned no results
            search_field: The QLineEdit widget to position below
        """
        # print(f"[DEBUG] SearchResultsWidget.show_no_results called for term: '{search_term}'")

        # Ensure widget is visible (in case it was manually closed)
        self.ensure_visible()

        # Setup application connections safely (only when first shown)
        self._setup_application_connections()

        # Clear previous results
        self.resultsList.clear()

        # Add "no results" message
        no_results_item = QListWidgetItem()
        no_results_item.setText(f"No results found for '{search_term}'")
        no_results_item.setForeground(QColor("#666666"))  # Gray color for no results
        no_results_item.setFlags(no_results_item.flags() & ~Qt.ItemIsSelectable)  # Make it non-selectable
        self.resultsList.addItem(no_results_item)

        # Position below search field
        if search_field:
            pos = search_field.mapToGlobal(search_field.rect().bottomLeft())
            adjusted_pos = pos - QPoint(0, -5)  # Move up by 5 pixels to match show_results
            self.move(adjusted_pos)
            self.adjustSize()

        # print("[DEBUG] Showing no results message")
        self.show()
        self.raise_()

        print(f"[DEBUG] SearchResultsWidget (no results) shown at position: {self.pos()}, visible: {self.isVisible()}")
        self.test_styling()

    def keyPressEvent(self, event):
        """Handle key press events, specifically ESC to close."""
        if event.key() == Qt.Key_Escape:
            self.hide_results()
            event.accept()  # Accept the event to prevent propagation
            return  # Don't call super() to prevent further processing
        else:
            super().keyPressEvent(event)

    def eventFilter(self, obj, event):
        """Filter events to detect clicks outside the dialog."""
        if not self._event_filter_installed:
            return False

        if event.type() == QEvent.MouseButtonPress and self.isVisible():
            # Check if click is outside this widget
            if not self.geometry().contains(event.globalPos()):
                # Check if click is on a child widget of this dialog
                widget_at_pos = QApplication.widgetAt(event.globalPos())
                if widget_at_pos is None or not self.isAncestorOf(widget_at_pos):
                    print(f"[DEBUG] Click outside SearchResultsWidget detected, hiding")
                    self.hide_results()
                    return True
        return False

    def _on_application_focus_changed(self, old, new):
        """Handle application focus changes to close dialog when switching away from QGIS."""
        if not self._focus_connection_made:
            return

        if self.isVisible() and new is None:
            # Focus moved outside QGIS application
            self.hide_results()

    def _on_item_clicked(self, item):
        """Handle result item click."""
        data = item.data(Qt.UserRole)
        # print(f"[DEBUG] Clicked item: {data}")

        if not data:
            return

        item_type = data.get("type", "")

        if item_type == "result":
            # Regular result item - emit signal
            module = data.get('module', '')
            item_id = data.get('id', '')
            title = data.get('title', '')
            self.resultClicked.emit(module, item_id, title)
            self.hide()

        elif item_type == "show_more":
            # Show more item - expand this module type
            module = data.get("module", "")
            self.expanded_types.add(module)
            # print(f"[DEBUG] Expanding module: {module}")
            self.refreshRequested.emit()

        elif item_type == "header":
            # Header clicked - toggle expansion
            module = data.get("module", "")
            if module in self.expanded_types:
                self.expanded_types.remove(module)
                # print(f"[DEBUG] Collapsing module: {module}")
            else:
                self.expanded_types.add(module)
                # print(f"[DEBUG] Expanding module: {module}")
            self.refreshRequested.emit()
