# sidebar.py
from PyQt5.QtCore import Qt, QSize, QEasingCurve, QTimer, pyqtSignal, QPoint, QPropertyAnimation
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QPushButton, QToolButton,
    QSpacerItem, QSizePolicy, QGraphicsDropShadowEffect,
)

from ..constants.file_paths import QssPaths
from ..widgets.theme_manager import ThemeManager, Theme, is_dark
from ..languages.language_manager import LanguageManager
from ..constants.module_icons import ModuleIconPaths
from ..utils.url_manager import Module  
from ..languages.translation_keys import TranslationKeys
lang_manager = LanguageManager()
theme_manager = ThemeManager()



class Sidebar(QWidget):
    """A modular sidebar with compact/expanded modes, floating toggle handle, and theme-aware styling."""

    # Click signal with module identifier
    itemClicked = pyqtSignal(str)


    def __init__(self, parent=None):
        super().__init__(parent)

        # --- state ---
        self._pulse_on = False
        self._expanded_width = 130
        self._compact_width = 50
        self._is_compact = False
        self.moduleButtons = {}
        self.buttonTexts = {}
        self._disabled_button = None


        self.setObjectName("SidebarRoot")

        # --- layout root ---
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- main frame (animated and contains nav + spacer + settings) ---
        self.SidebarMainFrame = QFrame(self)
        self.SidebarMainFrame.setObjectName("SidebarMainFrame")
        self.SidebarMainFrame.setFixedWidth(self._expanded_width)
        main_layout.addWidget(self.SidebarMainFrame)
        
        cm = QVBoxLayout(self.SidebarMainFrame)
        cm.setContentsMargins(0, 0, 0, 0)
        cm.setSpacing(6)

        # Navigation frame
        self.SidebarNavFrame = QFrame(self.SidebarMainFrame)
        self.SidebarNavFrame.setObjectName("SidebarNavFrame")
        nav_layout = QVBoxLayout(self.SidebarNavFrame)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)

        cm.addWidget(self.SidebarNavFrame)

        # Spacer pushes settings down
        cm.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Footer (docked meta bar) – replaces previous settingsFrame
        self.footerContainer = QFrame(self.SidebarMainFrame)
        self.footerContainer.setObjectName("SidebarFooterBar")  # Changed to SidebarFooterBar
        footer_layout = QHBoxLayout(self.footerContainer)
        footer_layout.setContentsMargins(0, 6, 6, 0)  # Moved margins here
        footer_layout.setSpacing(0)
        cm.addWidget(self.footerContainer)

        # Settings button directly in footer container
        translate_settings_name = lang_manager.translate(TranslationKeys.MODULE_SETTINGS)

        self.settingsButton = QPushButton(translate_settings_name, self.footerContainer)
        self.settingsButton.setObjectName("SidebarSettingsButton")
        self.settingsButton.setAutoDefault(False)
        self.settingsButton.setDefault(False)
        self.settingsButton.setIcon(QIcon(ModuleIconPaths.get_module_icon(Module.SETTINGS.name)))
        self.settingsButton.clicked.connect(
            lambda checked=False: self._on_button_clicked(Module.SETTINGS.value, self.settingsButton)
        )

        footer_layout.addWidget(self.settingsButton, 0, Qt.AlignLeft)
        # Track for compact toggle & active styling (same as nav buttons)
        self.moduleButtons[Module.SETTINGS.value] = self.settingsButton
        self.buttonTexts[self.settingsButton] = Module.SETTINGS.value

        # --- floating toggle handle (not part of layout) ---
        self.toggleButton = QToolButton(self)
        self.toggleButton.setObjectName("SidebarToggleButton")
        # Prevent button from being triggered by Return key
        self.toggleButton.setAutoRaise(True)
        self.toggleButton.setFixedSize(22, 40)        # slim, tall target

        tooltip = lang_manager.translate(TranslationKeys.SIDEBAR_COLLAPSE_TOOLTIP) or "Collapse Sidebar"
        self.toggleButton.setToolTip(tooltip)
        self.toggleButton.setText("«")                # expanded → show collapse glyph
        self.toggleButton.clicked.connect(self.toggleSidebar)
        self._apply_toggle_shadow()
        self.toggleButton.raise_()

        # --- width animation (animate main frame min width for reliability) ---
        self.animation = QPropertyAnimation(self.SidebarMainFrame, b"minimumWidth")
        self.animation.setDuration(600)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.finished.connect(self._position_toggle)

        # keep min/max equal so layout respects width during animation
        self.SidebarMainFrame.setMinimumWidth(self._expanded_width)
        self.SidebarMainFrame.setMaximumWidth(self._expanded_width)

        # store expanded width after first layout
        QTimer.singleShot(0, self._store_expanded_width)
        QTimer.singleShot(0, self._position_toggle)

        # active pulse (optional)
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._pulse_active)
        self._pulse_timer.start(1400)

        # theme
        self.retheme_sidebar()

# In Sidebar.py (new method)
    def populate_from_modules(self, module_manager):
        for module_name, module_info in module_manager.modules.items():
            if not module_info.get("sidebar_main_item", True):
                continue
            icon_path = module_info["icon"]
            display_name = module_info["display_name"]
            # Assuming Sidebar handles widget stacking separately or via callback
            self.addItem(display_name, module_name, icon_path)

    def addItem(self, displayName, uniqueIdentifier, iconPath):

        btn = QPushButton(displayName, self.SidebarNavFrame)
        btn.setObjectName("SidebarNavButton")
        # Prevent button from being triggered by Return key
        btn.setAutoDefault(False)
        btn.setDefault(False)
        btn.setIcon(ThemeManager.get_qicon(iconPath))
        btn.setIconSize(QSize(16, 16))  # Ühtlustatud ikooni suurus

        btn.clicked.connect(
            lambda checked=False, name=uniqueIdentifier, button=btn: self._on_button_clicked(name, button)
        )
        self.SidebarNavFrame.layout().addWidget(btn)
        self.moduleButtons[uniqueIdentifier] = btn
        self.buttonTexts[btn] = displayName

    def _on_button_clicked(self, module_name, btn):
        if not btn.isEnabled():
            return
        self.emitItemClicked(module_name)

    def _set_disabled_button(self, btn):
        # Re-enable the previously disabled button before locking the new one
        if self._disabled_button and self._disabled_button is not btn:
            self._disabled_button.setEnabled(True)
        btn.setEnabled(False)
        self._disabled_button = btn

    def setActiveModuleOnSidebarButton(self, module_name):
        module_key = module_name.lower()
        target_found = False
        for name, btn in self.moduleButtons.items():
            active = (name == module_key)
            if active:
                target_found = True
                self._set_disabled_button(btn)
            elif btn is not self._disabled_button:
                btn.setEnabled(True)
            btn.setProperty('active', active)
            btn.style().unpolish(btn); btn.style().polish(btn)
        if not target_found and self._disabled_button:
            self._disabled_button.setEnabled(True)
            self._disabled_button = None

    def clearActive(self):
        """Clear active state on all sidebar buttons (used when showing Welcome page)."""
        for btn in self.moduleButtons.values():
            btn.setProperty('active', False)
            btn.setEnabled(True)
            btn.style().unpolish(btn); btn.style().polish(btn)
        self._disabled_button = None

    def setHomeActive(self):
        self.homeButton.setProperty('active', True)
        self.homeButton.style().unpolish(self.homeButton); self.homeButton.style().polish(self.homeButton)

    def emitItemClicked(self, itemName):
        # Handle both Module enum and string inputs

        if hasattr(itemName, 'value'):
            self.itemClicked.emit(itemName.value)
        else:
            self.itemClicked.emit(itemName)

    def retheme_sidebar(self):
        ThemeManager.apply_module_style(self, [QssPaths.SIDEBAR])

    def _apply_toggle_shadow(self):
        sh = QGraphicsDropShadowEffect(self.toggleButton)
        sh.setBlurRadius(12)
        sh.setXOffset(0)
        sh.setYOffset(2)
        sh.setColor(QColor(0, 0, 0, 80))
        self.toggleButton.setGraphicsEffect(sh)

    def _pulse_active(self):
        self._pulse_on = not self._pulse_on
        for btn in self.moduleButtons.values():
            if btn.property('active'):
                btn.setProperty('pulse', self._pulse_on)
                btn.style().unpolish(btn); btn.style().polish(btn)
        # also pulse home if active
        if hasattr(self, 'homeButton') and self.homeButton.property('active'):
            self.homeButton.setProperty('pulse', self._pulse_on)
            self.homeButton.style().unpolish(self.homeButton); self.homeButton.style().polish(self.homeButton)

    def _store_expanded_width(self):
        self._expanded_width = max(self._expanded_width, self.SidebarMainFrame.width())
        self.SidebarMainFrame.setMinimumWidth(self._expanded_width)
        self.SidebarMainFrame.setMaximumWidth(self._expanded_width)
        self._position_toggle()

    def _position_toggle(self):
        """Float the handle at the vertical center of the sidebar’s right edge."""
        cont = self.SidebarMainFrame.geometry()
        x = cont.right() - self.toggleButton.width() // 2
        y = self.height() // 2 - self.toggleButton.height() // 2
        self.toggleButton.move(QPoint(max(0, x), max(0, y)))
        self.toggleButton.raise_()

    def toggleSidebar(self):
        self._is_compact = not self._is_compact
        self.setProperty("compact", self._is_compact)

        # texts visibility
        for btn, original in self.buttonTexts.items():
            btn.setText("" if self._is_compact else original)

        # settings button
        if self._is_compact:
            self.toggleButton.setText("»")
            self.toggleButton.setToolTip(lang_manager.translate(TranslationKeys.SIDEBAR_EXPAND_TOOLTIP) or "Expand Sidebar")
        else:
            self.toggleButton.setText("«")
            self.toggleButton.setToolTip(lang_manager.translate(TranslationKeys.SIDEBAR_COLLAPSE_TOOLTIP) or "Collapse Sidebar")

        start_w = self.SidebarMainFrame.width()
        end_w = self._compact_width if self._is_compact else self._expanded_width

        # animate min width; clamp max so layout cooperates
        self.animation.stop()
        self.SidebarMainFrame.setMaximumWidth(end_w)
        self.animation.setStartValue(start_w)
        self.animation.setEndValue(end_w)
        self.animation.start()

        # also set fixed widths immediately so mouse hit-tests feel right
        self.SidebarMainFrame.setMinimumWidth(end_w)
        self.SidebarMainFrame.setMaximumWidth(end_w)

        # refresh style for [compact="true"]
        self.style().unpolish(self); self.style().polish(self)
        QTimer.singleShot(0, self._position_toggle)


    # keep the handle centered when the widget resizes
    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._position_toggle()
