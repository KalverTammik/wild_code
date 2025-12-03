from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton, QHBoxLayout, QApplication
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QEvent, QTimer
from PyQt5.QtGui import QColor, QFont
from ..widgets.theme_manager import ThemeManager, styleExtras, ThemeShadowColors
from ..constants.file_paths import QssPaths
from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys

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
        self.setWindowFlags(
                Qt.Popup
                | Qt.FramelessWindowHint
                | Qt.NoDropShadowWindowHint
                )
        self.setAttribute(Qt.WA_TranslucentBackground)  # Enable translucent background
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)  # Keep focus on search field
        self.setModal(False)  # Non-modal dialog
        self.setObjectName("searchResultsWidget")
        # Track expanded state for each module type

        self.expanded_modules = set()

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
        self.resultsList.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.resultsList.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.resultsList.setFocusPolicy(Qt.NoFocus)
        styleExtras.apply_chip_shadow(
            element=self.resultsList,
            blur_radius=16,
            x_offset=1,
            y_offset=2,
            color=ThemeShadowColors.BLUE,
            alpha_level='medium',
        )
        self.resultsList.itemClicked.connect(self._on_item_clicked)

        layout.addWidget(self.resultsList)
        # This prevents crashes during early initialization
        self._event_filter_installed = False
        self._focus_connection_made = False

        # Hide initially
        self.hide()

        # Apply ThemeManager styling for consistent appearance
        self.retheme_search_results()

    def _setup_application_connections(self):
        """Safely setup QApplication event filter and focus connections."""
        if self._event_filter_installed and self._focus_connection_made:
            return

        app = QApplication.instance()
        if app is None:
            return

        if not self._event_filter_installed:
            app.installEventFilter(self)
            self._event_filter_installed = True

        if not self._focus_connection_made:
            app.focusChanged.connect(self._on_application_focus_changed)
            self._focus_connection_made = True

    def show_results(self, results, search_field):
        """
        Show search results below the search field, grouped by module type.

        Args:
            results: Raw search data from API with module types and hits
            search_field: The QLineEdit widget to position below
        """
        # print(f"[DEBUG] SearchResultsWidget.show_results called with {len(results)} module types")
        self.expanded_modules.clear()
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


            # Add module header
            header_item = QListWidgetItem()
            header_text = f"{LanguageManager().translate(module_type.capitalize())} ({total_hits})"
            header_item.setText(header_text)
            header_item.setData(Qt.UserRole, {"type": "header", "module": module_type})

            # Style header
            font = header_item.font()
            font.setBold(True)
            font.setPointSize(font.pointSize() + 1)
            header_item.setFont(font)
            # Color styling handled via stylesheet; keep widget data clean

            self.resultsList.addItem(header_item)

            # Add results (limited to 5 initially, or all if expanded)
            is_expanded = module_type in self.expanded_modules
            display_hits = hits if is_expanded else hits[:5]

            for hit in display_hits:
                result_item = QListWidgetItem()
                title = hit.get("title", "").replace("\n", " ")
                result_item.setText(f"  {title}")
                result_item.setData(Qt.UserRole, {
                    "type": "result",
                    "module": module_type,
                    "id": hit.get("id", ""),
                    "title": hit.get("title", "")
                })
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
            self.set_size(search_field)
        self._refocus_search_field(search_field)

        # print("[DEBUG] Showing grouped search results")
        self.resultsList.viewport().repaint()
        self.show()
        self.raise_()

        # log_debug(f"[DEBUG] SearchResultsWidget shown at position: {self.pos()}, visible: {self.isVisible()}")

    def show_no_results(self, search_term, search_field):
        """
        Show a "no results found" message.

        Args:
            search_term: The search term that returned no results
            search_field: The QLineEdit widget to position below
        """
        # print(f"[DEBUG] SearchResultsWidget.show_no_results called for term: '{search_term}'")

        # Ensure widget is visible (in case it was manually closed)
        self.expanded_modules.clear()
        self.ensure_visible()

        # Setup application connections safely (only when first shown)
        self._setup_application_connections()

        # Clear previous results
        self.resultsList.clear()

        # Add "no results" message
        no_results_item = QListWidgetItem()
        template = LanguageManager().translate(TranslationKeys.SEARCH_NO_RESULTS)
        try:
            message = template.format(term=search_term)
        except (KeyError, IndexError, ValueError):
            message = template
        no_results_item.setText(message)
        no_results_item.setFlags(no_results_item.flags() & ~Qt.ItemIsSelectable)  # Make it non-selectable
        self.resultsList.addItem(no_results_item)

        # Position below search field
        if search_field:
            self.set_size(search_field)
        self._refocus_search_field(search_field)

        # print("[DEBUG] Showing no results message")
        self.show()
        self.raise_()

    def show_status_message(self, message: str, search_field, *, is_error: bool = False):
        """Display a transient status/error message in the results popup."""
        self.expanded_modules.clear()
        self.ensure_visible()
        self._setup_application_connections()

        status_item = None
        if self.resultsList.count() == 1:
            candidate = self.resultsList.item(0)
            if candidate and candidate.data(Qt.UserRole) == "status_message":
                status_item = candidate

        if status_item is None:
            self.resultsList.clear()
            status_item = QListWidgetItem()
            status_item.setData(Qt.UserRole, "status_message")
            status_item.setFlags(status_item.flags() & ~Qt.ItemIsSelectable)
            self.resultsList.addItem(status_item)

        color = "#b3261e" if is_error else "#666666"
        status_item.setText(message)
        status_item.setForeground(QColor(color))

        if search_field:
            self.set_size(search_field)

        self.resultsList.viewport().repaint()
        if not self.isVisible():
            self.show()
            self.raise_()
        self._refocus_search_field(search_field)

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
                    # log_debug(f"[DEBUG] Click outside SearchResultsWidget detected, hiding")
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
            self.expanded_modules.add(module)
            # print(f"[DEBUG] Expanding module: {module}")
            self.refreshRequested.emit()

        elif item_type == "header":
            # Header clicked - toggle expansion
            module = data.get("module", "")
            if module in self.expanded_modules:
                self.expanded_modules.remove(module)
                # print(f"[DEBUG] Collapsing module: {module}")
            else:
                self.expanded_modules.add(module)
                # print(f"[DEBUG] Expanding module: {module}")
            self.refreshRequested.emit()


    def ensure_visible(self):
        """Ensure the widget is visible, useful for search functionality."""
        if not self.isVisible():
            # log_debug(f"[DEBUG] Forcing SearchResultsWidget to show")
            self.show()
            self.raise_()

    def hide_results(self):
        """Hide the search results widget."""
        # log_debug(f"[DEBUG] Hiding SearchResultsWidget, was visible: {self.isVisible()}")
        self.hide()

    def set_size(self, search_field):
        width = int(search_field.width() * 1.5)
        self.setFixedWidth(width)
        pos = search_field.mapToGlobal(search_field.rect().bottomLeft())
        adjusted_pos = pos - QPoint(int(width * 0.25), -5)  # shift by quarter of added width
        self.move(adjusted_pos)

    def retheme_search_results(self):
        """Re-apply QSS styling for dynamic theme switching (following plugin standards)."""
        ThemeManager.apply_module_style(self, [QssPaths.SEARCH_RESULTS_WIDGET])

    def _refocus_search_field(self, search_field):
        if not search_field:
            return
        QTimer.singleShot(0, lambda: search_field.setFocus(Qt.OtherFocusReason))
