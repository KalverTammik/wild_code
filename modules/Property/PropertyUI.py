from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTreeWidget, QTreeWidgetItem, QSplitter, QTextEdit,
    QGroupBox, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QComboBox
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon, QPixmap
from ...languages.language_manager import LanguageManager
from ...widgets.theme_manager import ThemeManager
from ...constants.file_paths import QssPaths

class PropertyUI(QWidget):
    """
    Property module - focused on displaying and managing data for a single property item.
    Features a header area with info/tools and a tree view for property-related data.
    """
    def __init__(self, lang_manager=None, theme_manager=None):
        super().__init__()
        self.name = "PropertyModule"

        # Language manager
        self.lang_manager = lang_manager or LanguageManager()

        # Setup UI
        self.setup_ui()

        # Apply theming
        ThemeManager.apply_module_style(self, [QssPaths.SETUP_CARD])

    def setup_ui(self):
        """Setup the property module interface with header and tree view."""
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        # Create splitter for resizable sections
        splitter = QSplitter(Qt.Vertical)
        root.addWidget(splitter)

        # Header section (top part)
        self.create_header_section(splitter)

        # Tree view section (bottom part)
        self.create_tree_section(splitter)

        # Set initial splitter proportions (header: 30%, tree: 70%)
        splitter.setSizes([200, 500])

    def create_header_section(self, splitter):
        """Create the header area with property info and tools."""
        header_frame = QFrame()
        header_frame.setObjectName("PropertyHeader")
        header_frame.setFrameStyle(QFrame.StyledPanel)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 15, 15, 15)
        header_layout.setSpacing(10)

        # Property title and status
        title_layout = QHBoxLayout()

        # Property ID/Name
        self.property_label = QLabel("Kinnistu: [Vali kinnistu]")
        self.property_label.setObjectName("PropertyTitle")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(14)
        self.property_label.setFont(title_font)
        title_layout.addWidget(self.property_label)

        # Status indicator
        self.status_label = QLabel("Staatus: Aktiivne")
        self.status_label.setObjectName("PropertyStatus")
        title_layout.addStretch()
        title_layout.addWidget(self.status_label)

        header_layout.addLayout(title_layout)

        # Property details in a grid-like layout
        details_group = QGroupBox("Kinnistu andmed")
        details_layout = QVBoxLayout(details_group)

        # Row 1: Basic info
        basic_layout = QHBoxLayout()

        # Katastritunnus
        kat_layout = QVBoxLayout()
        kat_layout.addWidget(QLabel("Katastritunnus:"))
        self.katastritunnus_edit = QLineEdit()
        self.katastritunnus_edit.setPlaceholderText("Sisesta katastritunnus...")
        kat_layout.addWidget(self.katastritunnus_edit)
        basic_layout.addLayout(kat_layout)

        # Omanik
        omanik_layout = QVBoxLayout()
        omanik_layout.addWidget(QLabel("Omanik:"))
        self.omanik_edit = QLineEdit()
        self.omanik_edit.setPlaceholderText("Omaniku nimi...")
        omanik_layout.addWidget(self.omanik_edit)
        basic_layout.addLayout(omanik_layout)

        # Pindala
        pindala_layout = QVBoxLayout()
        pindala_layout.addWidget(QLabel("Pindala (m²):"))
        self.pindala_edit = QLineEdit()
        self.pindala_edit.setPlaceholderText("0.00")
        pindala_layout.addWidget(self.pindala_edit)
        basic_layout.addLayout(pindala_layout)

        details_layout.addLayout(basic_layout)

        # Row 2: Additional info
        additional_layout = QHBoxLayout()

        # Hind
        hind_layout = QVBoxLayout()
        hind_layout.addWidget(QLabel("Hind (€):"))
        self.hind_edit = QLineEdit()
        self.hind_edit.setPlaceholderText("0.00")
        hind_layout.addWidget(self.hind_edit)
        additional_layout.addLayout(hind_layout)

        # Staatus
        staatus_layout = QVBoxLayout()
        staatus_layout.addWidget(QLabel("Staatus:"))
        self.staatus_combo = QComboBox()
        self.staatus_combo.addItems(["Aktiivne", "Müügis", "Müüdud", "Arendamisel"])
        additional_layout.addLayout(staatus_layout)

        # Tüüp
        tyyp_layout = QVBoxLayout()
        tyyp_layout.addWidget(QLabel("Tüüp:"))
        self.tyyp_combo = QComboBox()
        self.tyyp_combo.addItems(["Elamumaa", "Ärimaa", "Põllumaa", "Metsamaa"])
        additional_layout.addLayout(tyyp_layout)

        details_layout.addLayout(additional_layout)

        header_layout.addWidget(details_group)

        splitter.addWidget(header_frame)

    def create_tree_section(self, splitter):
        """Create the tree view area for property-related data."""
        tree_frame = QFrame()
        tree_frame.setObjectName("PropertyTree")
        tree_frame.setFrameStyle(QFrame.StyledPanel)
        tree_layout = QVBoxLayout(tree_frame)
        tree_layout.setContentsMargins(15, 15, 15, 15)
        tree_layout.setSpacing(10)

        # Tree view title
        tree_title = QLabel("Kinnistuga seotud andmed")
        tree_title.setObjectName("TreeTitle")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        tree_title.setFont(title_font)
        tree_layout.addWidget(tree_title)

        # Create tree widget
        self.tree_widget = QTreeWidget()
        self.tree_widget.setObjectName("PropertyTreeWidget")
        self.tree_widget.setHeaderLabels(["Andmetüüp", "Väärtus", "Kuupäev", "Staatus"])

        # Set column widths
        self.tree_widget.setColumnWidth(0, 200)
        self.tree_widget.setColumnWidth(1, 150)
        self.tree_widget.setColumnWidth(2, 120)
        self.tree_widget.setColumnWidth(3, 100)

        # Enable alternating row colors
        self.tree_widget.setAlternatingRowColors(True)

        # Make it expandable
        self.tree_widget.setRootIsDecorated(True)

        tree_layout.addWidget(self.tree_widget)

        # Initialize with sample data
        self.populate_tree_data()

        # Tree control buttons
        controls_layout = QHBoxLayout()

        self.expand_btn = QPushButton("Laienda kõik")
        self.expand_btn.clicked.connect(self.tree_widget.expandAll)
        controls_layout.addWidget(self.expand_btn)

        self.collapse_btn = QPushButton("Ahenda kõik")
        self.collapse_btn.clicked.connect(self.tree_widget.collapseAll)
        controls_layout.addWidget(self.collapse_btn)

        self.refresh_tree_btn = QPushButton("Värskenda puu")
        self.refresh_tree_btn.clicked.connect(self.refresh_tree_data)
        controls_layout.addWidget(self.refresh_tree_btn)

        controls_layout.addStretch()

        tree_layout.addLayout(controls_layout)

        splitter.addWidget(tree_frame)

    def populate_tree_data(self):
        """Populate the tree with sample property-related data."""
        # Clear existing data
        self.tree_widget.clear()

        # Create main categories
        documents = QTreeWidgetItem(self.tree_widget, ["Dokumendid", "", "", ""])
        transactions = QTreeWidgetItem(self.tree_widget, ["Tehingud", "", "", ""])
        assessments = QTreeWidgetItem(self.tree_widget, ["Hindamised", "", "", ""])
        permits = QTreeWidgetItem(self.tree_widget, ["Load", "", "", ""])
        boundaries = QTreeWidgetItem(self.tree_widget, ["Piirid", "", "", ""])

        # Add document items
        doc1 = QTreeWidgetItem(documents, ["Omandiõigus", "Jaan Tamm", "2023-01-15", "Kehtiv"])
        doc2 = QTreeWidgetItem(documents, ["Katastri plaan", "KLM123456", "2023-02-20", "Kehtiv"])
        doc3 = QTreeWidgetItem(documents, ["Ehitusluba", "EL789012", "2023-03-10", "Kehtiv"])

        # Add transaction items
        trans1 = QTreeWidgetItem(transactions, ["Ost", "150000€", "2022-11-05", "Lõpetatud"])
        trans2 = QTreeWidgetItem(transactions, ["Müük", "180000€", "2023-06-15", "Lõpetatud"])

        # Add assessment items
        assess1 = QTreeWidgetItem(assessments, ["Vallasasutus", "165000€", "2023-01-01", "Kehtiv"])
        assess2 = QTreeWidgetItem(assessments, ["Pank", "160000€", "2023-04-01", "Kehtiv"])

        # Add permit items
        permit1 = QTreeWidgetItem(permits, ["Ehitusluba", "EL2023001", "2023-03-15", "Kehtiv"])
        permit2 = QTreeWidgetItem(permits, ["Kasutusluba", "KL2023002", "2023-08-20", "Ootel"])

        # Add boundary items
        bound1 = QTreeWidgetItem(boundaries, ["Põhi piir", "Mõõdetud", "2023-01-10", "Kehtiv"])
        bound2 = QTreeWidgetItem(boundaries, ["Külg piir", "Mõõdetud", "2023-01-12", "Kehtiv"])

        # Expand main categories
        documents.setExpanded(True)
        transactions.setExpanded(True)

    def refresh_tree_data(self):
        """Refresh the tree data."""
        self.populate_tree_data()

    def activate(self):
        """Called when the module becomes active."""
        pass

    def deactivate(self):
        """Called when the module becomes inactive."""
        pass

    def get_widget(self):
        """Return the module's main QWidget."""
        return self
