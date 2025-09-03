#!/usr/bin/env python3
"""
SearchResultsWidget Structure Test
==================================

This test file demonstrates the complete structure and build process of SearchResultsWidget.
It shows how the widget is constructed, what each component does, and why the black frame appears.

Run this file to see the widget structure in action.
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QHBoxLayout, QPushButton
)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QColor, QFont


class SearchResultsWidgetDemo(QWidget):
    """
    Demo widget to show SearchResultsWidget structure and build process.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SearchResultsWidget Structure Demo")
        self.setGeometry(100, 100, 800, 600)

        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Title
        title = QLabel("SearchResultsWidget Structure Analysis")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # Create SearchResultsWidget instance for analysis
        self.search_widget = SearchResultsWidget()
        self.search_widget.show_results([
            {
                "type": "documents",
                "total": 5,
                "hits": [
                    {"title": "Document 1", "id": "doc1"},
                    {"title": "Document 2", "id": "doc2"},
                    {"title": "Document 3", "id": "doc3"}
                ]
            },
            {
                "type": "projects",
                "total": 3,
                "hits": [
                    {"title": "Project A", "id": "proj1"},
                    {"title": "Project B", "id": "proj2"}
                ]
            }
        ], None)

        # Analysis sections
        self.create_structure_analysis(main_layout)
        self.create_black_frame_analysis(main_layout)
        self.create_solution_demo(main_layout)

        # Add the actual SearchResultsWidget
        widget_container = QWidget()
        widget_layout = QVBoxLayout(widget_container)
        widget_layout.addWidget(QLabel("Actual SearchResultsWidget:"))
        widget_layout.addWidget(self.search_widget)
        main_layout.addWidget(widget_container)

    def create_structure_analysis(self, parent_layout):
        """Show the widget structure breakdown."""
        group = QWidget()
        layout = QVBoxLayout(group)

        title = QLabel("🔍 Widget Structure Breakdown")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)

        structure_text = """
        SearchResultsWidget Structure:
        ==============================

        1. ROOT WIDGET (QWidget)
           ├── Window Flags: Qt.Popup
           ├── Attributes: WA_TranslucentBackground
           ├── StyleSheet: "background: transparent; border: none;"
           └── Layout: QVBoxLayout (margins: 8,8,8,8)

        2. CHILD WIDGET (QListWidget)
           ├── ObjectName: "searchResultsList"
           ├── Max Size: 450x600
           ├── Scroll Policy: AsNeeded
           └── Items: QListWidgetItem[]

        3. GRAPHICS EFFECT (QGraphicsDropShadowEffect)
           ├── Blur Radius: 20
           ├── Offset: (0, 5)
           └── Color: QColor(0, 0, 0, 60)

        The black frame comes from:
        - QGraphicsDropShadowEffect creating a shadow
        - QWidget's default background/border
        - Qt.Popup window flags creating a window frame
        """

        structure_label = QLabel(structure_text)
        structure_label.setStyleSheet("""
            QLabel {
                background: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 10px;
                font-family: monospace;
                font-size: 10px;
            }
        """)
        layout.addWidget(structure_label)

        parent_layout.addWidget(group)

    def create_black_frame_analysis(self, parent_layout):
        """Explain why the black frame appears."""
        group = QWidget()
        layout = QVBoxLayout(group)

        title = QLabel("🎯 Black Frame Root Cause Analysis")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)

        analysis_text = """
        Why You See Black Frame:
        ========================

        1. QGraphicsDropShadowEffect:
           - Creates a shadow around the widget
           - Uses QColor(0, 0, 0, 60) = black with 60% opacity
           - Blur radius of 20px creates thick shadow

        2. QWidget Default Styling:
           - Even with "background: transparent", QWidget has default borders
           - Qt.Popup windows often have system window frames
           - Layout margins (8px) create space for the shadow

        3. Qt.Popup Window Flags:
           - Creates a separate window (popup)
           - System may add window decorations
           - Compositing issues with translucent backgrounds

        4. QSS Application Order:
           - Inline stylesheets may conflict with theme styles
           - ThemeManager may override your settings
           - Multiple stylesheet applications can cause conflicts
        """

        analysis_label = QLabel(analysis_text)
        analysis_label.setStyleSheet("""
            QLabel {
                background: #ffebee;
                border: 1px solid #f44336;
                border-radius: 5px;
                padding: 10px;
                font-family: monospace;
                font-size: 10px;
            }
        """)
        layout.addWidget(analysis_label)

        parent_layout.addWidget(group)

    def create_solution_demo(self, parent_layout):
        """Show different solutions for the black frame."""
        group = QWidget()
        layout = QVBoxLayout(group)

        title = QLabel("✅ Solution Options")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)

        solutions_text = """
        Solution Options:
        ================

        1. Remove QGraphicsDropShadowEffect:
           # shadow = QGraphicsDropShadowEffect(self)
           # self.setGraphicsEffect(shadow)

        2. Use Qt.ToolTip instead of Qt.Popup:
           self.setWindowFlags(Qt.ToolTip)

        3. Ensure proper stylesheet order:
           self.setStyleSheet("background: transparent; border: none;")
           # Apply after theme styles

        4. Use QWidget attributes:
           self.setAttribute(Qt.WA_NoSystemBackground, True)
           self.setAttribute(Qt.WA_TranslucentBackground, True)

        5. Override paintEvent:
           def paintEvent(self, event):
               # Custom painting without default frame
               pass

        Current Status:
        ===============
        ✓ Qt.Popup window flags
        ✓ WA_TranslucentBackground attribute
        ✓ Inline stylesheet with transparent background
        ✗ QGraphicsDropShadowEffect (commented out)
        """

        solutions_label = QLabel(solutions_text)
        solutions_label.setStyleSheet("""
            QLabel {
                background: #e8f5e8;
                border: 1px solid #4caf50;
                border-radius: 5px;
                padding: 10px;
                font-family: monospace;
                font-size: 10px;
            }
        """)
        layout.addWidget(solutions_label)

        parent_layout.addWidget(group)


class SearchResultsWidget(QWidget):
    """
    Simplified SearchResultsWidget for demonstration.
    This shows the exact structure causing the black frame issue.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        print("🔧 Building SearchResultsWidget...")
        print("   Step 1: Setting window flags")

        # WINDOW FLAGS - This creates the popup window
        self.setWindowFlags(Qt.Popup)
        print("   ✓ Qt.Popup flag set (creates separate window)")

        # WIDGET ATTRIBUTES - This enables transparency
        self.setAttribute(Qt.WA_TranslucentBackground)
        print("   ✓ WA_TranslucentBackground attribute set")

        # OBJECT NAME - For stylesheet targeting
        self.setObjectName("searchResultsWidget")
        print("   ✓ Object name set to 'searchResultsWidget'")

        # STYLESHEET - This should make background transparent
        self.setStyleSheet("background: transparent; border: none;")
        print("   ✓ Stylesheet set: 'background: transparent; border: none;'")

        # TRACK STATE
        self.expanded_types = set()
        print("   ✓ Expanded types tracking initialized")

        print("   Step 2: Creating layout")

        # MAIN LAYOUT - This creates margins around content
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)  # Creates 8px margin around content
        layout.setSpacing(0)
        print("   ✓ QVBoxLayout created with 8px margins")

        print("   Step 3: Creating results list")

        # RESULTS LIST - The main content widget
        self.resultsList = QListWidget()
        self.resultsList.setObjectName("searchResultsList")
        self.resultsList.setMaximumHeight(600)
        self.resultsList.setMaximumWidth(450)
        self.resultsList.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.resultsList.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        print("   ✓ QListWidget created with size limits")

        # ADD TO LAYOUT
        layout.addWidget(self.resultsList)
        print("   ✓ QListWidget added to layout")

        print("   Step 4: Graphics effect (COMMENTED OUT)")

        # GRAPHICS EFFECT - This is the main cause of black frame
        # COMMENTED OUT to prevent black shadow
        # shadow = QGraphicsDropShadowEffect(self)
        # shadow.setBlurRadius(20)
        # shadow.setXOffset(0)
        # shadow.setYOffset(5)
        # shadow.setColor(QColor(0, 0, 0, 60))
        # self.setGraphicsEffect(shadow)
        print("   ✓ QGraphicsDropShadowEffect commented out (no black shadow)")

        print("   Step 5: Final setup")

        # HIDE INITIALLY
        self.hide()
        print("   ✓ Widget hidden initially")

        print("🎉 SearchResultsWidget construction complete!")
        print()
        print("Widget Structure Summary:")
        print("========================")
        print("• Root QWidget (Qt.Popup, WA_TranslucentBackground)")
        print("  └─ QVBoxLayout (margins: 8,8,8,8)")
        print("     └─ QListWidget (max: 450x600)")
        print("        └─ QListWidgetItem[] (search results)")
        print()
        print("Black Frame Prevention:")
        print("======================")
        print("• No QGraphicsDropShadowEffect")
        print("• background: transparent stylesheet")
        print("• border: none stylesheet")
        print("• WA_TranslucentBackground attribute")
        print()

    def show_results(self, results, search_field):
        """Show search results in the dropdown."""
        print("📋 Showing search results...")

        if not results:
            print("   No results to show")
            self.hide()
            return

        # Clear previous results
        self.resultsList.clear()
        print(f"   Cleared previous results")

        # Group results by module type and display
        for module_data in results:
            module_type = module_data.get("type", "")
            total_hits = module_data.get("total", 0)
            hits = module_data.get("hits", [])

            if total_hits == 0:
                continue

            print(f"   Processing {module_type}: {total_hits} results")

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
            print(f"   ✓ Added header: {header_text}")

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
                print(f"   ✓ Added result: {title}")

            # Add "show more" if there are more results
            if not is_expanded and len(hits) > 5:
                more_item = QListWidgetItem()
                more_item.setText(f"  -- Show {len(hits) - 5} more --")
                more_item.setData(Qt.UserRole, {"type": "show_more", "module": module_type})
                more_item.setForeground(QColor("#666666"))
                more_item.setFont(QFont("Arial", 9, QFont.StyleItalic))
                self.resultsList.addItem(more_item)
                print(f"   ✓ Added 'show more' option")

        # Position below search field with increased width
        if search_field:
            pos = search_field.mapToGlobal(search_field.rect().bottomLeft())
            # Adjust position to account for increased width (50% increase)
            adjusted_pos = pos - QPoint(110, 0)  # Shift left by half the width increase
            self.move(adjusted_pos)
            self.adjustSize()
            print(f"   ✓ Positioned at {adjusted_pos}")

        print("   ✓ Showing widget")
        self.show()
        self.raise_()

        print("🎉 Search results displayed successfully!")
        print()


def main():
    """Main function to run the demo."""
    print("🚀 Starting SearchResultsWidget Structure Demo")
    print("=" * 50)

    app = QApplication(sys.argv)

    # Create and show the demo
    demo = SearchResultsWidgetDemo()
    demo.show()

    print("📊 Demo window opened - check the analysis sections!")
    print()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
