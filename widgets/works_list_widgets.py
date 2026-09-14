"""Compact Works list menus and reusable card/group presentation."""
from PyQt5.QtCore import QObject, QPoint, QTimer, Qt, pyqtSignal
from PyQt5.QtWidgets import QActionGroup, QHBoxLayout, QMenu, QSizePolicy, QToolButton, QWidget

from ..constants.file_paths import QssPaths
from ..languages.translation_keys import TranslationKeys as K
from ..modules.works.works_list_service import (
    GROUP_FIELDS, LOCAL_SORTS, REMOTE_SORTS, ListChoices, group_loaded_items,
)
from ..ui.module_card_factory import ModuleCardFactory
from .theme_manager import ThemeManager


FIELD_LABELS = {
    "default": K.LIST_SORT_DEFAULT, "title": K.LIST_SORT_TITLE,
    "due": K.LIST_SORT_DUE, "start": K.LIST_SORT_START,
    "created": K.LIST_SORT_CREATED, "updated": K.LIST_SORT_UPDATED,
    "status": K.LIST_SORT_STATUS, "type": K.LIST_SORT_TYPE,
    "priority": K.LIST_SORT_PRIORITY, "responsible": K.LIST_SORT_RESPONSIBLE,
    "none": K.LIST_GROUP_NONE, "deadline": K.LIST_GROUP_DEADLINE,
}


class WorksListControls(QWidget):
    choicesChanged = pyqtSignal(object)
    groupExpansionRequested = pyqtSignal(bool)

    def __init__(self, lang, parent=None):
        super().__init__(parent)
        self.lang = lang
        self.choices = ListChoices()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        self.sort_button = QToolButton(self)
        self.sort_button.setObjectName("FeedSortButton")
        self.sort_button.setText(lang.translate(K.LIST_SORT))
        self.group_button = QToolButton(self)
        self.group_button.setObjectName("FeedGroupButton")
        self.group_button.setText(lang.translate(K.LIST_GROUP))
        for button in (self.sort_button, self.group_button):
            button.setPopupMode(QToolButton.InstantPopup)
            button.setFocusPolicy(Qt.StrongFocus)
            button.setCursor(Qt.PointingHandCursor)
            layout.addWidget(button)
        self.sort_menu = QMenu(self.sort_button)
        self.sort_menu.setToolTipsVisible(True)
        self.sort_button.setMenu(self.sort_menu)
        sort_group = QActionGroup(self)
        self.sort_actions = {}
        default = self.sort_menu.addAction(lang.translate(K.LIST_SORT_DEFAULT))
        self._add_sort_action(default, sort_group, "default", False)
        for fields, section in ((REMOTE_SORTS, K.LIST_SORT_GLOBAL), (LOCAL_SORTS, K.LIST_SORT_LOCAL)):
            self.sort_menu.addSection(lang.translate(section))
            for name in fields:
                title = lang.translate(FIELD_LABELS[name])
                if name in LOCAL_SORTS:
                    title += " · " + lang.translate(K.LIST_SORT_LOCAL).lower()
                submenu = self.sort_menu.addMenu(title)
                for descending, label in zip((False, True), self._direction_labels(name)):
                    self._add_sort_action(submenu.addAction(lang.translate(label)), sort_group, name, descending)
        self.group_menu = QMenu(self.group_button)
        self.group_button.setMenu(self.group_menu)
        group_actions = QActionGroup(self)
        self.group_actions = {}
        for name in GROUP_FIELDS:
            action = self.group_menu.addAction(lang.translate(FIELD_LABELS[name]))
            action.setCheckable(True)
            group_actions.addAction(action)
            action.triggered.connect(lambda _checked=False, field=name: self._choose_group(field))
            self.group_actions[name] = action
        self.group_menu.addSeparator()
        self.expand_action = self.group_menu.addAction(lang.translate(K.LIST_GROUP_EXPAND_ALL))
        self.collapse_action = self.group_menu.addAction(lang.translate(K.LIST_GROUP_COLLAPSE_ALL))
        self.expand_action.triggered.connect(lambda: self.groupExpansionRequested.emit(True))
        self.collapse_action.triggered.connect(lambda: self.groupExpansionRequested.emit(False))
        self.set_choices(self.choices)
        self.retheme()

    def _add_sort_action(self, action, group, name, descending):
        action.setCheckable(True)
        group.addAction(action)
        action.triggered.connect(lambda _checked=False, field=name, reverse=descending: self._choose_sort(field, reverse))
        self.sort_actions[(name, descending)] = action

    @staticmethod
    def _direction_labels(name):
        if name == "priority":
            return K.LIST_SORT_ASC_PRIORITY, K.LIST_SORT_DESC_PRIORITY
        if name in ("due", "start", "created", "updated"):
            return K.LIST_SORT_ASC_DATE, K.LIST_SORT_DESC_DATE
        return K.LIST_SORT_ASC_TEXT, K.LIST_SORT_DESC_TEXT

    def _choose_sort(self, name, descending):
        self.set_choices(ListChoices(name, descending, self.choices.group))
        self.choicesChanged.emit(self.choices)

    def _choose_group(self, name):
        self.set_choices(ListChoices(self.choices.sort, self.choices.descending, name))
        self.choicesChanged.emit(self.choices)

    def set_choices(self, choices):
        self.choices = choices
        self.sort_actions[(choices.sort, choices.descending if choices.sort != "default" else False)].setChecked(True)
        self.group_actions[choices.group].setChecked(True)
        sort_text = self.lang.translate(FIELD_LABELS[choices.sort])
        if choices.sort != "default":
            sort_text += " · " + self.lang.translate(self._direction_labels(choices.sort)[int(choices.descending)])
        sort_text += "\n" + self.lang.translate(K.LIST_SORT_LOCAL if choices.sort in LOCAL_SORTS else K.LIST_SORT_GLOBAL)
        group_text = self.lang.translate(FIELD_LABELS[choices.group])
        if choices.group != "none":
            group_text += "\n" + self.lang.translate(K.LIST_GROUP_SCOPE)
        for button, text, active in ((self.sort_button, sort_text, choices.sort != "default"),
                                     (self.group_button, group_text, choices.group != "none")):
            button.setToolTip(text)
            button.setAccessibleName(button.text() + ": " + text)
            button.setProperty("active", active)
            button.style().unpolish(button)
            button.style().polish(button)
        self.expand_action.setEnabled(choices.group != "none")
        self.collapse_action.setEnabled(choices.group != "none")

    def retheme(self):
        ThemeManager.apply_module_style(self, [QssPaths.MODULE_TOOLBAR])
        for menu in (self.sort_menu, self.group_menu, *self.sort_menu.findChildren(QMenu)):
            menu.setObjectName("CardActionsMenu")
            ThemeManager.apply_module_style(menu, [QssPaths.POPUP])


class WorksListView(QObject):
    changed = pyqtSignal()

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.choices = ListChoices()
        self.items = {}
        self.cards = {}
        self.headers = {}
        self.closed_groups = set()
        self._render_timer = QTimer(self)
        self._render_timer.setSingleShot(True)
        self._render_timer.timeout.connect(self.render)
        self._anchor_timer = QTimer(self)
        self._anchor_timer.setSingleShot(True)
        self._anchor_timer.timeout.connect(self._restore_anchor)
        self._anchor = None

    @property
    def all_collapsed(self):
        return bool(self.headers) and all(key in self.closed_groups for key in self.headers)

    def add_item(self, item, insert_at_top=False):
        key = str(item["id"])
        if key in self.items:
            return
        if insert_at_top:
            self.items = {key: item, **self.items}
        else:
            self.items[key] = item
        if not self._render_timer.isActive():
            self._render_timer.start(16)

    def clear(self):
        self._render_timer.stop()
        self._anchor_timer.stop()
        self._anchor = None
        for widget in (*self.cards.values(), *self.headers.values()):
            self.owner.feed_layout.removeWidget(widget)
            widget.hide()
            widget.deleteLater()
        self.items.clear()
        self.cards.clear()
        self.headers.clear()

    def update_item(self, item):
        item_id = str(item["id"])
        if item_id not in self.items:
            return  # A late edit result must not resurrect a cleared feed.
        self.items[item_id] = dict(item)
        for key in [key for key in self.cards if key[1] == item_id]:
            card = self.cards.pop(key)
            self.owner.feed_layout.removeWidget(card)
            card.hide()
            card.deleteLater()
        self._render_timer.start(0)

    def set_choices(self, choices):
        if self.choices.group != choices.group:
            self.closed_groups.clear()
        self.choices = choices
        self.render(preserve_anchor=False)

    def set_groups_expanded(self, expanded):
        self.closed_groups = set() if expanded else set(self.headers)
        self.render(preserve_anchor=False)
        if expanded and self.owner._activated:
            self.owner._initial_autofill_tick()

    def _toggle_group(self, key):
        if key in self.closed_groups:
            self.closed_groups.remove(key)
        else:
            self.closed_groups.add(key)
        self.render(preserve_anchor=False)
        if key not in self.closed_groups and self.owner._activated:
            self.owner._initial_autofill_tick()

    def render(self, preserve_anchor=True):
        self._render_timer.stop()
        owner = self.owner
        viewport = owner.scroll_area.viewport()
        self._anchor = None
        if preserve_anchor:
            for key, card in self.cards.items():
                y = card.mapTo(viewport, QPoint(0, 0)).y()
                if card.isVisible() and y + card.height() > 0 and y < viewport.height():
                    self._anchor = (key, y)
                    break
        previous_guard = owner._ignore_scroll_event
        owner._ignore_scroll_event = True
        try:
            groups = group_loaded_items(self.items.values(), self.choices, owner.lang_manager)
            old_cards, old_headers = dict(self.cards), dict(self.headers)
            self.cards, self.headers = {}, {}
            position = 1
            for group in groups:
                expanded = group.key not in self.closed_groups
                if self.choices.group != "none":
                    header = old_headers.pop(group.key, None)
                    if header is None:
                        header = QToolButton(owner.feed_content)
                        header.setObjectName("FeedGroupHeader")
                        header.setCheckable(True)
                        header.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
                        header.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
                        header.setFocusPolicy(Qt.StrongFocus)
                        header.clicked.connect(lambda _checked=False, key=group.key: self._toggle_group(key))
                        ThemeManager.apply_module_style(header, [QssPaths.MODULE_TOOLBAR])
                    header.setText(owner.lang_manager.translate(K.LIST_GROUP_COUNT).format(name=group.label, count=len(group.items)))
                    header.setToolTip(header.text() + "\n" + owner.lang_manager.translate(K.LIST_GROUP_SCOPE))
                    header.setChecked(expanded)
                    header.setArrowType(Qt.DownArrow if expanded else Qt.RightArrow)
                    self.headers[group.key] = header
                    if owner.feed_layout.indexOf(header) != position:
                        owner.feed_layout.insertWidget(position, header)
                    header.show()
                    position += 1
                for item in group.items:
                    key = (group.key, str(item["id"]))
                    card = old_cards.pop(key, None)
                    if card is None:
                        # Reuse an existing instance when the grouping changes.
                        reusable = next((old_key for old_key in old_cards if old_key[1] == key[1]), None)
                        card = old_cards.pop(reusable) if reusable is not None else ModuleCardFactory.create_item_card(
                            item, module_name=owner.module_key, lang_manager=owner.lang_manager)
                    self.cards[key] = card
                    card._item_update_handler = owner._on_list_item_updated
                    if owner.feed_layout.indexOf(card) != position:
                        owner.feed_layout.insertWidget(position, card)
                    card.setVisible(expanded)
                    position += 1
            for widget in (*old_cards.values(), *old_headers.values()):
                owner.feed_layout.removeWidget(widget)
                widget.hide()
                widget.deleteLater()
            owner.feed_layout.activate()
            if self._anchor is not None:
                self._anchor_timer.start(0)
        finally:
            owner._ignore_scroll_event = previous_guard
        self.changed.emit()

    def _restore_anchor(self):
        if self._anchor is None:
            return
        key, old_y = self._anchor
        self._anchor = None
        card = self.cards.get(key)
        if card is None or not card.isVisible():
            return
        owner = self.owner
        previous_guard = owner._ignore_scroll_event
        owner._ignore_scroll_event = True
        try:
            y = card.mapTo(owner.scroll_area.viewport(), QPoint(0, 0)).y()
            bar = owner.scroll_area.verticalScrollBar()
            bar.setValue(bar.value() + y - old_y)
        finally:
            owner._ignore_scroll_event = previous_guard

    def retheme(self):
        for header in self.headers.values():
            ThemeManager.apply_module_style(header, [QssPaths.MODULE_TOOLBAR])
