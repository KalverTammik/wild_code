# sidebar.py
from PyQt5.QtCore import Qt, QSize, QEasingCurve, QTimer, pyqtSignal, QPoint, QPropertyAnimation
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QPushButton, QToolButton,
    QSpacerItem, QSizePolicy, QGraphicsDropShadowEffect, QLabel
)

from ..constants.file_paths import QssPaths
from ..widgets.theme_manager import ThemeManager
from ..module_manager import ModuleManager, SETTINGS_MODULE
from ..languages.language_manager import LanguageManager
from ..constants.module_icons import ModuleIconPaths

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
        self._expanded_width = 220
        self._compact_width = 50
        self._is_compact = False
        self.moduleButtons = {}
        self.buttonTexts = {}
        self._shadows_applied = False

        self.setObjectName("SidebarRoot")

        # --- layout root ---
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- left container we animate ---
        self.container = QFrame(self)
        self.container.setObjectName("SidebarContainer")
        self.container.setFixedWidth(self._expanded_width)
        main_layout.addWidget(self.container)

        # Inside container: main frame (nav + spacer + settings)
        self.SidebarMainFrame = QFrame(self.container)
        self.SidebarMainFrame.setObjectName("SidebarMainFrame")
        cm = QVBoxLayout(self.SidebarMainFrame)
        cm.setContentsMargins(0, 0, 0, 0)
        cm.setSpacing(6)

        # Navigation frame
        self.SidebarNavFrame = QFrame(self.SidebarMainFrame)
        self.SidebarNavFrame.setObjectName("SidebarNavFrame")
        nav_layout = QVBoxLayout(self.SidebarNavFrame)
        nav_layout.setContentsMargins(0, 6, 6, 6)
        nav_layout.setSpacing(4)

        # Home (Avaleht) button at very top
        try:
            home_label = lang_manager.sidebar_button("HOME")
        except Exception:
            home_label = "Avaleht"
        if not home_label:
            home_label = "Avaleht"
        self.homeButton = QPushButton(home_label, self.SidebarNavFrame)
        self.homeButton.setObjectName("SidebarHomeButton")
        # Prevent button from being triggered by Return key
        self.homeButton.setAutoDefault(False)
        self.homeButton.setDefault(False)
        # Assign themed icon if available
        try:
            home_icon_path = ModuleIconPaths.get_module_icon("__HOME__")
            if home_icon_path:
                self.homeButton.setIcon(QIcon(home_icon_path))
        except Exception:
            pass
        # Ainult Avalehe nupu ikooni mõõt (22x22)
        try:
            self.homeButton.setIconSize(QSize(22, 22))
        except Exception:
            pass
        self.homeButton.clicked.connect(lambda: self.emitItemClicked("__HOME__"))
        nav_layout.addWidget(self.homeButton)
        # Track for compact toggle & active styling
        self.moduleButtons["__HOME__"] = self.homeButton
        self.buttonTexts[self.homeButton] = home_label
        cm.addWidget(self.SidebarNavFrame)

        # Spacer pushes settings down
        cm.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Footer (docked meta bar) – replaces previous settingsFrame
        self.footerContainer = QFrame(self.SidebarMainFrame)
        self.footerContainer.setObjectName("SidebarFooterContainer")
        footer_layout = QVBoxLayout(self.footerContainer)
        footer_layout.setContentsMargins(0, 6, 6, 6)  # Ühtlustatud nav raamiga
        footer_layout.setSpacing(0)
        cm.addWidget(self.footerContainer)

        # Footer bar with settings button
        self.footerBar = QFrame(self.footerContainer)
        self.footerBar.setObjectName("SidebarFooterBar")
        self.footerBar.setContentsMargins(0, 0, 0, 0)  # Eemalda vaikimisi veerised
        fl = QHBoxLayout(self.footerBar)
        fl.setContentsMargins(0, 6, 6, 6)  # Ühtlustatud vasak serv moodulitega
        fl.setSpacing(6)
        footer_layout.addWidget(self.footerBar)

        # Settings button inside footer bar
        settings_name = lang_manager.sidebar_button(SETTINGS_MODULE)
        settings_icon_path = ModuleIconPaths.get_module_icon(SETTINGS_MODULE)
        self.settingsButton = QPushButton(settings_name, self.footerBar)
        self.settingsButton.setObjectName("SidebarSettingsButton")
        # Prevent button from being triggered by Return key
        self.settingsButton.setAutoDefault(False)
        self.settingsButton.setDefault(False)
        if settings_icon_path:
            self.settingsButton.setIcon(QIcon(settings_icon_path))
        try:
            self.settingsButton.setIconSize(QSize(22, 22))  # Ühtlustatud ikooni suurus
        except Exception:
            pass
        # Connect settings button to directly show settings module
        self.settingsButton.clicked.connect(self.showSettingsModule)
        fl.addWidget(self.settingsButton, 0, Qt.AlignLeft)
        # Track for compact toggle & active styling (same as nav buttons)
        self.moduleButtons[SETTINGS_MODULE] = self.settingsButton
        self.buttonTexts[self.settingsButton] = settings_name

        # Mount main frame into container
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(self.SidebarMainFrame)

        # --- floating toggle handle (not part of layout) ---
        self.toggleButton = QToolButton(self)
        self.toggleButton.setObjectName("SidebarToggleButton")
        # Prevent button from being triggered by Return key
        self.toggleButton.setAutoRaise(True)
        self.toggleButton.setFixedSize(22, 44)        # slim, tall target
        try:
            tooltip = lang_manager.translations.get("sidebar_collapse_tooltip", "sidebar_collapse_tooltip")
            self.toggleButton.setToolTip(tooltip)
        except Exception:
            self.toggleButton.setToolTip("sidebar_collapse_tooltip")
        self.toggleButton.setText("«")                # expanded → show collapse glyph
        self.toggleButton.clicked.connect(self.toggleSidebar)
        self._apply_toggle_shadow()
        self.toggleButton.raise_()

        # --- width animation (animate container min width for reliability) ---
        self.animation = QPropertyAnimation(self.container, b"minimumWidth")
        self.animation.setDuration(280)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.finished.connect(self._position_toggle)

        # keep min/max equal so layout respects width during animation
        self.container.setMinimumWidth(self._expanded_width)
        self.container.setMaximumWidth(self._expanded_width)

        # store expanded width after first layout
        QTimer.singleShot(0, self._store_expanded_width)
        QTimer.singleShot(0, self._position_toggle)

        # active pulse (optional)
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._pulse_active)
        self._pulse_timer.start(1400)

        # theme
        self.retheme_sidebar()

    # ---------- external API ----------
    def addItem(self, displayName, uniqueIdentifier, iconPath=None):
        import sys
        print(f"[Sidebar] Adding button: {displayName} ({uniqueIdentifier})", file=sys.stderr)
        btn = QPushButton(displayName, self.SidebarNavFrame)
        btn.setObjectName("SidebarNavButton")
        # Prevent button from being triggered by Return key
        btn.setAutoDefault(False)
        btn.setDefault(False)
        if iconPath:
            btn.setIcon(QIcon(iconPath))
        # Projekte nupp ikooni ühtlustatud suurus 22x22
        if uniqueIdentifier in ('ProjectsModule', 'ContractModule', 'PropertyModule'):
            try:
                btn.setIconSize(QSize(22, 22))  # Ühtlustatud ikooni suurus
            except Exception:
                pass

        def handler():
            if btn.isEnabled():
                print(f"[Sidebar] Button clicked: {uniqueIdentifier}", file=sys.stderr)
                self.emitItemClicked(uniqueIdentifier)

        btn.clicked.connect(handler)
        self.SidebarNavFrame.layout().addWidget(btn)
        self.moduleButtons[uniqueIdentifier] = btn
        self.buttonTexts[btn] = displayName

    def setActiveModule(self, module_name):
        for name, btn in self.moduleButtons.items():
            active = (name == module_name)
            btn.setEnabled(True)
            btn.setProperty('active', active)
            btn.style().unpolish(btn); btn.style().polish(btn)

    def clearActive(self):
        """Clear active state on all sidebar buttons (used when showing Welcome page)."""
        for btn in self.moduleButtons.values():
            btn.setProperty('active', False)
            btn.style().unpolish(btn); btn.style().polish(btn)

    def setHomeActive(self):
        if hasattr(self, 'homeButton'):
            self.homeButton.setProperty('active', True)
            self.homeButton.style().unpolish(self.homeButton); self.homeButton.style().polish(self.homeButton)

    def emitItemClicked(self, itemName):
        self.itemClicked.emit(itemName)

    def showSettingsModule(self):
        # Switch to the registered Settings module in the main stack
        self.emitItemClicked(SETTINGS_MODULE)

    def retheme_sidebar(self):
        ThemeManager.apply_module_style(self, [QssPaths.SIDEBAR])

        if not self._shadows_applied:
            self._apply_section_shadows()
            self._shadows_applied = True

        # refresh [compact="true"] rules
        self.setProperty("compact", self._is_compact)
        self.style().unpolish(self); self.style().polish(self)
        self._position_toggle()

        # refresh settings icon for current theme
        if hasattr(self, 'settingsButton'):
            icon_path = ModuleIconPaths.get_module_icon(SETTINGS_MODULE)
            if icon_path:
                self.settingsButton.setIcon(QIcon(icon_path))

        # refresh module nav icons for current theme
        for uniqueIdentifier, btn in self.moduleButtons.items():
            themed_icon = ModuleIconPaths.get_module_icon(uniqueIdentifier)
            if themed_icon:
                btn.setIcon(QIcon(themed_icon))
            if uniqueIdentifier in ('ProjectsModule', 'ContractModule', '__HOME__', 'PropertyModule', 'SettingsModule'):
                try:
                    btn.setIconSize(QSize(22, 22))  # Tagame ühtluse ka teema vahetusel
                except Exception:
                    pass
        # Settings ikooni värskendus ja suurus
        if hasattr(self, 'settingsButton'):
            try:
                self.settingsButton.setIconSize(QSize(22, 22))
            except Exception:
                pass

    # ---------- internals ----------
    def _apply_section_shadows(self):
        # soft inner shadows for nav + settings
        for frame in (self.SidebarNavFrame, getattr(self, 'footerBar', None)):
            if frame is None:
                continue
            sh = QGraphicsDropShadowEffect(self)
            sh.setBlurRadius(18)
            sh.setOffset(0, 4)
            sh.setColor(QColor(0, 0, 0, 40))  # subtle; fine for both themes
            frame.setGraphicsEffect(sh)

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
        self._expanded_width = max(self._expanded_width, self.container.width())
        self.container.setMinimumWidth(self._expanded_width)
        self.container.setMaximumWidth(self._expanded_width)
        self._position_toggle()

    def _position_toggle(self):
        """Float the handle at the vertical center of the sidebar’s right edge."""
        cont = self.container.geometry()
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
            self.settingsButton.setText("")
            self.toggleButton.setText("»")
            try:
                tooltip = lang_manager.translations.get("sidebar_expand_tooltip", "sidebar_expand_tooltip")
                self.toggleButton.setToolTip(tooltip)
            except Exception:
                self.toggleButton.setToolTip("sidebar_expand_tooltip")
        else:
            self.settingsButton.setText(self.buttonTexts.get(self.settingsButton, self.settingsButton.text()))
            self.toggleButton.setText("«")
            try:
                tooltip = lang_manager.translations.get("sidebar_collapse_tooltip", "sidebar_collapse_tooltip")
                self.toggleButton.setToolTip(tooltip)
            except Exception:
                self.toggleButton.setToolTip("sidebar_collapse_tooltip")

        start_w = self.container.width()
        end_w = self._compact_width if self._is_compact else self._expanded_width

        # animate min width; clamp max so layout cooperates
        self.animation.stop()
        self.container.setMaximumWidth(end_w)
        self.animation.setStartValue(start_w)
        self.animation.setEndValue(end_w)
        self.animation.start()

        # also set fixed widths immediately so mouse hit-tests feel right
        self.container.setMinimumWidth(end_w)
        self.container.setMaximumWidth(end_w)

        # refresh style for [compact="true"]
        self.style().unpolish(self); self.style().polish(self)
        QTimer.singleShot(0, self._position_toggle)

        # ensure all buttons update their styles
        for btn in self.moduleButtons.values():
            btn.style().unpolish(btn); btn.style().polish(btn)
        if hasattr(self, 'homeButton'):
            self.homeButton.style().unpolish(self.homeButton); self.homeButton.style().polish(self.homeButton)
        if hasattr(self, 'settingsButton'):
            self.settingsButton.style().unpolish(self.settingsButton); self.settingsButton.style().polish(self.settingsButton)

    # keep the handle centered when the widget resizes
    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._position_toggle()
