from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFrame, QPushButton, QSpacerItem, QSizePolicy, QGraphicsDropShadowEffect, QHBoxLayout
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import pyqtSignal, Qt, QPropertyAnimation, QEasingCurve, QSize
from ..constants.file_paths import QssPaths
from ..widgets.theme_manager import ThemeManager
from ..modules.Settings.SettingsUI import SettingsUI  # Import the SettingsModule
from ..module_manager import ModuleManager, SETTINGS_MODULE
from ..languages.language_manager import LanguageManager

lang_manager = LanguageManager()
theme_manager = ThemeManager()

class Sidebar(QWidget):
    """A modular sidebar component with advanced styling and layout."""
    
    # Custom signal to emit the name of the clicked item
    itemClicked = pyqtSignal(str)
    

    def __init__(self, parent=None):
        super().__init__(parent)

        # Initialize animation for sidebar width (bounce effect) FIRST
        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(300)  # Animation duration in milliseconds
        self.animation.setEasingCurve(QEasingCurve.OutBounce)  # Bounce effect
        # Store the original (expanded) sidebar width after layout is set up
        self._expanded_width = None

        self.setObjectName("Sidebar")
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        # Track module navigation buttons by uniqueIdentifier
        self.moduleButtons = {}
        # Store original button texts for toggling
        self.buttonTexts = {}

        # SidebarMainFrame: holds nav, spacer, settings (vertical)
        self.SidebarMainFrame = QFrame(self)
        self.SidebarMainFrame.setObjectName("SidebarMainFrame")
        self.SidebarMainLayout = QVBoxLayout(self.SidebarMainFrame)
        self.SidebarMainLayout.setContentsMargins(0, 0, 0, 0)
        self.SidebarMainLayout.setSpacing(6)

        # Navigation Items Container
        self.SidebarNavFrame = QFrame(self.SidebarMainFrame)
        self.SidebarNavFrame.setObjectName("SidebarNavFrame")
        self.SidebarNavLayout = QVBoxLayout(self.SidebarNavFrame)
        self.SidebarNavLayout.setContentsMargins(0, 6, 6, 6)
        self.SidebarMainLayout.addWidget(self.SidebarNavFrame)

        # Vertical Spacer
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.SidebarMainLayout.addItem(spacer)

        # Settings Module
        self.settingsFrame = QFrame(self.SidebarMainFrame)
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
        self.settingsButton.setText(settings_name)  # Ensure visible name is set
        self.settingsLayout.addWidget(self.settingsButton)
        self.SidebarMainLayout.addWidget(self.settingsFrame)

        # Add SidebarMainFrame to main layout (left)
        main_layout.addWidget(self.SidebarMainFrame)

        # SidebarRightFrame: toggle button centered, no border/background, icon only
        self.rightFrame = QFrame(self)
        self.rightFrame.setObjectName("SidebarRightFrame")
        self.rightFrame.setFixedWidth(24)
        self.rightFrame.setFixedHeight(24)
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        self.rightFrame.setLayout(right_layout)

        # Toggle button: icon only, no border/background, no padding
        self.toggleButton = QPushButton(self)
        self.toggleButton.setObjectName("SidebarToggleButton")
        self.toggleButton.setFixedSize(24, 24)
        self.toggleButton.setIcon(QIcon())  # Set your icon here, e.g. QIcon(':/icons/sidebar_toggle.svg')
        self.toggleButton.setIconSize(QSize(24, 24))
        self.toggleButton.setToolTip("Collapse Sidebar")
        self.toggleButton.setText("«")  # Set initial text to match expanded state
        self.toggleButton.clicked.connect(self.toggleSidebar)
        right_layout.addStretch(1)
        right_layout.addWidget(self.toggleButton, alignment=Qt.AlignCenter)
        right_layout.addStretch(1)

        # Add SidebarRightFrame to main layout (right)
        main_layout.addWidget(self.rightFrame, alignment=Qt.AlignRight)

        # Now that all widgets/frames are created, set expanded width
        self._set_expanded_width_later()

    def _set_expanded_width_later(self):
        # Use a single-shot timer to set the expanded width after the widget is shown
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, self._store_expanded_width)

    def _store_expanded_width(self):
        self._expanded_width = self.width()
    def applyStyles(self):
        """Apply styles to the sidebar and toggle button using ThemeManager and QSS only."""
        ThemeManager.apply_theme(self, QssPaths.SIDEBAR)



        from ..constants.file_paths import STYLES  # QssPaths already imported at top
        self.theme_base_dir = STYLES
        self.settingsModule = SettingsUI(
            lang_manager,
            theme_manager,
            theme_dir=self.theme_base_dir,
            qss_files=[QssPaths.MAIN, QssPaths.SIDEBAR]
        )

        # Connect the button to show the Settings UI
        self.settingsButton.clicked.connect(self.showSettingsModule)

        # Initialize animation for sidebar width (bounce effect)
        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(300)  # Animation duration in milliseconds
        self.animation.setEasingCurve(QEasingCurve.OutBounce)  # Bounce effect

        # Store the original (expanded) sidebar width after layout is set up
        self._expanded_width = None
        # Now that all widgets/frames are created, set expanded width
        self._set_expanded_width_later()

    def _set_expanded_width_later(self):
        # Use a single-shot timer to set the expanded width after the widget is shown
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, self._store_expanded_width)

    def _store_expanded_width(self):
        self._expanded_width = self.width()

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
        # Only emit if enabled (not active)
        def handler():
            if button.isEnabled():
                self.emitItemClicked(uniqueIdentifier)
        button.clicked.connect(handler)
        self.SidebarNavLayout.addWidget(button)
        self.moduleButtons[uniqueIdentifier] = button

    def setActiveModule(self, module_name):
        """Enable all module buttons except the active one, which is disabled and unclickable."""
        for name, button in self.moduleButtons.items():
            if name == module_name:
                button.setEnabled(False)
                button.setProperty('active', True)
                button.style().unpolish(button)
                button.style().polish(button)
            else:
                button.setEnabled(True)
                button.setProperty('active', False)
                button.style().unpolish(button)
                button.style().polish(button)

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
            self.buttonTexts[self.settingsButton] = self.settingsButton.text()
            self.settingsButton.setText("")
        else:
            # Always restore the settings button name
            settings_name = self.settingsButton.text() if self.settingsButton.text() else self.settingsButton.objectName()
            self.settingsButton.setText(self.buttonTexts.get(self.settingsButton, settings_name))

        # Animate sidebar width for compact/expanded mode
        self.animation.stop()
        self.animation.setStartValue(self.width())
        if not isCompact:
            self.animation.setEndValue(50)
        else:
            # Use stored expanded width if available, else fallback to 200
            self.animation.setEndValue(self._expanded_width if self._expanded_width else 200)
        # Always use bounce effect for both directions
        self.animation.setEasingCurve(QEasingCurve.OutBounce)
        self.animation.start()
