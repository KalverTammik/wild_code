"""The indicator in a module's toolbar: what the list's filters leave beside the module's whole data,
overdue and due soon clickable. A module with a card of its own on the home page shows it low beside.
The user chooses the design and the colour set; one choice serves every module."""
from __future__ import annotations

from typing import Optional

from qgis.PyQt.QtCore import QSize, Qt, pyqtSignal, pyqtSlot
from qgis.PyQt.QtWidgets import QActionGroup, QHBoxLayout, QMenu, QSizePolicy, QToolButton, QWidget

from ...constants.module_icons import IconNames
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...python.latest_request import LatestRequest
from ...ui.theme_manager import ThemeManager
from ...utils.api_error_handling import user_message
from ...utils.settings_service import SettingsService
from .dashboard_cards import CENTER, FAILED_MARK, LOADING_MARK, TOOLBAR, Brush, CardSpec, HomeCard, Snapshot
from .dashboard_counts import Overview, Selection, fetch_overview
from .indicator_styles import DEFAULT_DESIGN, DEFAULT_PALETTE, DESIGNS, PALETTES, WIDTH, Paint

_GAP = 8


def chosen_style() -> tuple[str, str]:
    """(design, colour set) as the user saved them; the defaults for an unknown or no choice."""
    settings = SettingsService()
    design = str(settings.indicator_design(default=DEFAULT_DESIGN) or "")
    palette = str(settings.indicator_palette(default=DEFAULT_PALETTE) or "")
    return (design if design in DESIGNS else DEFAULT_DESIGN, palette if palette in PALETTES else DEFAULT_PALETTE)


class DueState:
    """What the summary card paints."""

    def __init__(self) -> None:
        self.overview: Optional[Overview] = None
        self.failed = False
        self.active: Optional[tuple[bool, bool]] = None  # (whole data, overdue) the list shows now
        self.design = DEFAULT_DESIGN
        self.cells: dict = {}  # where the last painting put the clickable numbers


def paint_summary(b: Brush, state: DueState) -> None:
    state.cells.clear()
    if state.overview is None:
        b.text((0, 0, b.size[0], b.size[1]), FAILED_MARK if state.failed else LOADING_MARK, 22, b.muted, True, CENTER)
        return
    data = (state.overview.shown, state.overview.whole)
    DESIGNS[state.design].paint(Paint(b, data, state.active, state.cells), *b.size)


class DueSummaryCard(HomeCard):
    clicked = pyqtSignal(bool, bool)  # whole data, overdue

    def __init__(self, module_key: str, parent: Optional[QWidget] = None) -> None:
        spec = CardSpec((module_key,), (WIDTH, DESIGNS[DEFAULT_DESIGN].height), paint_summary)
        super().__init__(spec, DueState(), parent)
        self.setMouseTracking(True)

    def set_design(self, design: str) -> None:
        self.data.design = design
        self.data.cells.clear()
        self.spec = self.spec._replace(size=(WIDTH, DESIGNS[design].height))
        self.setFixedSize(*self.spec.size)
        self.update()

    def cell_at(self, position) -> Optional[tuple[bool, bool]]:
        """The clickable number under the pointer."""
        for key, rect in self.data.cells.items():
            if rect.contains(float(position.x()), float(position.y())):
                return key
        return None

    def mouseMoveEvent(self, event) -> None:  # noqa: N802 - Qt override
        if self.cell_at(event.pos()) is None:
            self.unsetCursor()
        else:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        cell = self.cell_at(event.pos()) if event.button() == Qt.MouseButton.LeftButton else None
        if cell is not None:
            self.clicked.emit(*cell)
        super().mousePressEvent(event)


class ModuleIndicator(QWidget):
    dueClicked = pyqtSignal(bool, bool)  # whole data, overdue

    def __init__(self, module_key: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.module_key = module_key
        self.shown = Selection()
        self.whole = Selection()
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(_GAP)

        self.graphic: Optional[HomeCard] = None
        if module_key in TOOLBAR:
            self.graphic = HomeCard(TOOLBAR[module_key], Snapshot(), self)
            # It gives way to the filters of a narrow window; the numbers beside it stay.
            width, height = self.graphic.spec.size
            self.graphic.setMinimumSize(0, height)
            self.graphic.setMaximumSize(width, height)
            self.graphic.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            row.addWidget(self.graphic, 0, Qt.AlignmentFlag.AlignTop)

        self.summary = DueSummaryCard(module_key, self)
        self.summary.clicked.connect(self.dueClicked.emit)
        row.addWidget(self.summary, 0, Qt.AlignmentFlag.AlignTop)
        row.addWidget(self._build_settings_button(), 0, Qt.AlignmentFlag.AlignTop)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        self._request = LatestRequest(self)
        self._request.finished.connect(self._on_overview)
        self._request.error.connect(self._on_failed)
        self.apply_style()
        self.retheme()

    # --- The user's choice ---------------------------------------------------------
    def _build_settings_button(self) -> QToolButton:
        lang = LanguageManager()
        button = QToolButton(self)
        button.setObjectName("IndicatorSettingsButton")
        button.setAutoRaise(True)
        button.setFixedSize(22, 22)
        button.setIconSize(QSize(14, 14))
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setToolTip(lang.translate(TranslationKeys.INDICATOR_SETTINGS))
        button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        button.setStyleSheet("QToolButton::menu-indicator { image: none; }")
        menu = QMenu(button)
        self.design_actions, self.palette_actions = {}, {}
        for title, choices, actions, save in (
            (TranslationKeys.INDICATOR_DESIGN, DESIGNS, self.design_actions, "indicator_design"),
            (TranslationKeys.INDICATOR_PALETTE, PALETTES, self.palette_actions, "indicator_palette"),
        ):
            menu.addSection(lang.translate(title))
            group = QActionGroup(self)
            for key, choice in choices.items():
                action = menu.addAction(lang.translate(choice.name_key))
                action.setCheckable(True)
                group.addAction(action)
                action.triggered.connect(
                    lambda _checked=False, method=save, value=key: self._choose(method, value))
                actions[key] = action
        button.setMenu(menu)
        self.settings_button = button
        return button

    def _choose(self, method: str, value: str) -> None:
        getattr(SettingsService(), method)(value)
        self.apply_style()

    def apply_style(self) -> None:
        design, palette = chosen_style()
        self.design_actions[design].setChecked(True)
        self.palette_actions[palette].setChecked(True)
        colors = PALETTES[palette]
        for card in (self.graphic, self.summary):
            if card is not None:
                card.colors = (colors.late, colors.soon, colors.fine, colors.total)
        self.summary.set_design(design)
        if self.graphic is not None:
            self.graphic.update()
        self.updateGeometry()

    def showEvent(self, event) -> None:  # noqa: N802 - Qt override
        self.apply_style()  # another module may have changed the choice
        super().showEvent(event)

    # --- The numbers ------------------------------------------------------------------
    def show_selection(self, shown: Selection, whole: Selection) -> None:
        """The list's filters changed (or were applied again): count them."""
        self.shown, self.whole = shown, whole
        self.set_active(None)
        self.summary.data.failed = False
        self.summary.setToolTip(LanguageManager().translate(TranslationKeys.HOME_SHOW_IN_LIST))
        if self.graphic is not None:
            self.graphic.data.failed.clear()
        self._request.submit(fetch_overview, self.module_key, shown, whole)
        self._repaint()

    def set_active(self, cell: Optional[tuple[bool, bool]]) -> None:
        self.summary.data.active = cell
        self.summary.update()

    def active(self) -> Optional[tuple[bool, bool]]:
        return self.summary.data.active

    def cancel(self) -> None:
        self._request.invalidate()

    @pyqtSlot(object)
    def _on_overview(self, overview: Overview) -> None:
        self.summary.data.overview = overview
        if self.graphic is not None:
            self.graphic.data.counts[self.module_key] = overview.shown
        self._repaint()

    @pyqtSlot(str)
    def _on_failed(self, message: str) -> None:
        # A number that could not be read again is not shown as current.
        self.summary.data.overview = None
        self.summary.data.failed = True
        self.summary.setToolTip(user_message(message))
        if self.graphic is not None:
            self.graphic.data.counts.pop(self.module_key, None)
            self.graphic.data.failed.add(self.module_key)
        self._repaint()

    def _repaint(self) -> None:
        for card in (self.graphic, self.summary):
            if card is not None:
                card.update()

    def retheme(self) -> None:
        dark = ThemeManager.effective_theme() == "dark"
        for card in (self.graphic, self.summary):
            if card is not None:
                card.dark = dark
        self.settings_button.setIcon(ThemeManager.get_qicon(IconNames.ICON_SETTINGS))
        self._repaint()
