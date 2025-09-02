from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLabel
from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from PyQt5.QtGui import QColor, QFont


class SearchResultsWidget(QWidget):
    """
    Widget for displaying search results in a dropdown list below the search field.
    Groups results by module type with expandable sections.
    """
    resultClicked = pyqtSignal(str, str, str)  # module, id, title
    refreshRequested = pyqtSignal()  # Signal to request refresh of results

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup)
        self.setObjectName("searchResultsWidget")

        # Track expanded state for each module type
        self.expanded_types = set()

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Results list
        self.resultsList = QListWidget()
        self.resultsList.setObjectName("searchResultsList")
        self.resultsList.setMaximumHeight(360)  # 20% increase from 300
        self.resultsList.setMaximumWidth(440)   # 50% increase from ~293 (assuming original was ~220)
        self.resultsList.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.resultsList.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.resultsList.itemClicked.connect(self._on_item_clicked)

        layout.addWidget(self.resultsList)

        # Shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)

        # Hide initially
        self.hide()

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
            # Adjust position to account for increased width (50% increase)
            adjusted_pos = pos - QPoint(110, 0)  # Shift left by half the width increase
            self.move(adjusted_pos)
            self.adjustSize()

        # print("[DEBUG] Showing grouped search results")
        self.show()
        self.raise_()

    def hide_results(self):
        """Hide the search results widget."""
        self.hide()

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
            self.move(pos)
            self.adjustSize()

        # print("[DEBUG] Showing no results message")
        self.show()
        self.raise_()

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
