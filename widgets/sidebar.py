from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFrame, QPushButton, QSpacerItem, QSizePolicy, QGraphicsDropShadowEffect
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import pyqtSignal, Qt, QPropertyAnimation, QEasingCurve
from ..constants.file_paths import QssPaths
from ..widgets.theme_manager import ThemeManager
from ..modules.Settings.SettingsUI import SettingsUI  # Import the SettingsModule
from ..module_manager import ModuleManager, SETTINGS_MODULE
from ..languages.language_manager import LanguageManager

# Shared managers for all modules
lang_manager = LanguageManager()
theme_manager = ThemeManager()

class Sidebar(QWidget):
    """A modular sidebar component with advanced styling and layout."""
    
    # Custom signal to emit the name of the clicked item
    itemClicked = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("Sidebar")
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(6)
        
        # Navigation Items Container
        self.SidebarNavFrame = QFrame(self)
        self.SidebarNavFrame.setObjectName("SidebarNavFrame")
        self.SidebarNavLayout = QVBoxLayout(self.SidebarNavFrame)
        self.SidebarNavLayout.setContentsMargins(0, 6, 6, 6)
        self.layout().addWidget(self.SidebarNavFrame)
        
        # Vertical Spacer
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout().addItem(spacer)

        # Settings Module
        self.settingsFrame = QFrame(self)
        self.settingsFrame.setObjectName("SettingsFrame")
        self.settingsLayout = QVBoxLayout(self.settingsFrame)
        self.settingsLayout.setContentsMargins(0, 6, 6, 6)
        # Create an instance of ModuleManager
        module_manager = ModuleManager()

        # Get the display name and icon for the Settings module
        settings_name = module_manager.get_module_name(SETTINGS_MODULE)
        settings_icon = module_manager.getModuleIcon(SETTINGS_MODULE)

        # Create the Settings button
        self.settingsButton = QPushButton(settings_name, self.settingsFrame)
        if settings_icon:
            self.settingsButton.setIcon(QIcon(settings_icon))
        self.settingsLayout.addWidget(self.settingsButton)
        self.layout().addWidget(self.settingsFrame)



        from ..constants.file_paths import  QssPaths, STYLES
        self.theme_base_dir = STYLES
        self.settingsModule = SettingsUI(
            lang_manager,
            theme_manager,
            theme_dir=self.theme_base_dir,
            qss_files=[QssPaths.MAIN, QssPaths.SIDEBAR]
        )

        # Connect the button to show the Settings UI
        self.settingsButton.clicked.connect(self.showSettingsModule)

    def showSettingsModule(self):
        self.settingsModule.show()

        # Apply shadow effect to SidebarNavFrame
        nav_shadow = QGraphicsDropShadowEffect(self)
        nav_shadow.setBlurRadius(20)
        nav_shadow.setOffset(0, 5)
        nav_shadow.setColor(QColor(192, 192, 192))  # Light gray shadow to match background
        self.SidebarNavFrame.setGraphicsEffect(nav_shadow)

        # Apply shadow effect to SettingsFrame
        settings_shadow = QGraphicsDropShadowEffect(self)
        settings_shadow.setBlurRadius(20)
        settings_shadow.setOffset(0, 5)
        settings_shadow.setColor(QColor(192, 192, 192))  # Light gray shadow to match background
        self.settingsFrame.setGraphicsEffect(settings_shadow)

        # Store original button texts for toggling
        self.buttonTexts = {}

        # Add settings button to the buttonTexts dictionary
        self.buttonTexts[self.settingsButton] = self.settingsButton.text()


        # Special right frame for toggle button (furthest right in sidebar layout)
        self.rightFrame = QFrame(self)
        self.rightFrame.setObjectName("SidebarRightFrame")
        self.rightFrame.setFixedWidth(32)
        self.rightFrame.setLayout(QVBoxLayout())
        self.rightFrame.layout().setContentsMargins(0, 20, 0, 0)
        self.rightFrame.layout().setSpacing(0)

        self.toggleButton = QPushButton("«", self.rightFrame)
        self.toggleButton.setObjectName("ToggleButton")
        self.toggleButton.setFixedSize(28, 28)
        self.toggleButton.setToolTip("Collapse Sidebar")
        self.toggleButton.clicked.connect(self.toggleSidebar)
        self.rightFrame.layout().addWidget(self.toggleButton, alignment=Qt.AlignTop | Qt.AlignHCenter)

        # Remove rightFrame from settings area if present, and add to sidebar layout as last widget
        # (If already present, this is a no-op)
        if self.rightFrame.parent() is not self:
            self.rightFrame.setParent(self)
        # Remove if already in layout (avoid duplicates)
        layout = self.layout()
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            if item and item.widget() is self.rightFrame:
                layout.takeAt(i)
        layout.addWidget(self.rightFrame, alignment=Qt.AlignRight)

        # Initialize animation for sidebar width
        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(300)  # Animation duration in milliseconds
        self.animation.setEasingCurve(QEasingCurve.OutBounce)  # Bounce effect

        # Apply Styles
        self.applyStyles()

    def applyStyles(self):
        """Apply styles to the sidebar using ThemeManager."""
        ThemeManager.apply_theme(self, QssPaths.SIDEBAR)


    def addItem(self, displayName, uniqueIdentifier, iconPath=None):
        """Add a navigation item to the sidebar with an optional icon."""
        button = QPushButton(displayName, self.SidebarNavFrame)
        if iconPath:
            button.setIcon(QIcon(iconPath))  # Set the icon if provided
        # Emit the unique identifier (module class name) when the button is clicked
        button.clicked.connect(lambda: self.emitItemClicked(uniqueIdentifier))
        self.SidebarNavLayout.addWidget(button)

    def emitItemClicked(self, itemName):
        """Emit the custom signal with the clicked item's name."""
        self.itemClicked.emit(itemName)

    def toggleSidebar(self):
        """Toggle between expanded and compact sidebar modes."""
        isCompact = self.toggleButton.text() == "»"  # Check current state

        # Update toggle button text
        self.toggleButton.setText("«" if isCompact else "»")
        self.toggleButton.setToolTip("Expand Sidebar" if isCompact else "Collapse Sidebar")

        # Toggle button text visibility
        for i in range(self.SidebarNavLayout.count()):
            widget = self.SidebarNavLayout.itemAt(i).widget()
            if isinstance(widget, QPushButton):
                if not isCompact:
                    # Store original text and hide it
                    self.buttonTexts[widget] = widget.text()
                    widget.setText("")
                else:
                    # Restore original text
                    widget.setText(self.buttonTexts.get(widget, ""))

        # Handle settings button separately
        if not isCompact:
            self.settingsButton.setText("")
        else:
            self.settingsButton.setText(self.buttonTexts.get(self.settingsButton, ""))

        # Animate sidebar width for compact/expanded mode
        self.animation.stop()
        self.animation.setStartValue(self.width())
        self.animation.setEndValue(50 if not isCompact else 200)
        self.animation.start()
