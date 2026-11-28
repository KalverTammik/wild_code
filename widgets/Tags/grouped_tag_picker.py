"""A combo-like tag selector: tags under their groups, a search field and check boxes."""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Sequence

from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from ...constants.file_paths import StylePaths
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...python.tag_catalog import Tag, TagCatalog
from ...ui.theme_manager import ThemeManager
from ..Filters.filter_widget_parts import PickerControlBase, PickerPopupBase

_TAG_ID_ROLE = Qt.ItemDataRole.UserRole
_NAMES_IN_SUMMARY = 2


class _TagPickerControl(PickerControlBase):
    CONTROL_NAME = "GroupedTagPickerControl"
    SUMMARY_NAME = "GroupedTagPickerSummary"


class _TagTree(QTreeWidget):
    """Space and Enter tick the current row, as a click does."""

    toggleRequested = pyqtSignal(QTreeWidgetItem)

    def keyPressEvent(self, event) -> None:  # noqa: N802 - Qt override
        if event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter) and self.currentItem() is not None:
            self.toggleRequested.emit(self.currentItem())
            event.accept()
            return
        super().keyPressEvent(event)


class _TagPickerPopup(PickerPopupBase):
    NAME = "GroupedTagPicker"
    MIN_WIDTH = 280
    ROW_NAMES = ()
    TREE_MAX_HEIGHT = 360

    def refresh(self) -> None:
        """Builds the list once; ticking a row only changes check states, so the scroll position stays."""
        lang = self._owner._lang
        self.search = QLineEdit(self._frame)
        self.search.setObjectName("GroupedTagPickerSearch")
        self.search.setPlaceholderText(lang.translate(TranslationKeys.TAG_PICKER_SEARCH))
        self.search.setClearButtonEnabled(True)
        self._frame_layout.addWidget(self.search)

        actions = QHBoxLayout()
        self.count_label = QLabel(self._frame)
        self.count_label.setObjectName("GroupedTagPickerSectionLabel")
        actions.addWidget(self.count_label, 1)
        clear = QPushButton(lang.translate(TranslationKeys.TAG_PICKER_CLEAR), self._frame)
        clear.setObjectName("GroupedTagPickerActionButton")
        clear.setAutoDefault(False)
        clear.clicked.connect(self._owner.clear_selection)
        actions.addWidget(clear)
        self._frame_layout.addLayout(actions)

        self.tree = _TagTree(self._frame)
        self.tree.setObjectName("GroupedTagPickerTree")
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(16)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tree.setExpandsOnDoubleClick(False)
        self.tree.itemClicked.connect(lambda item, _column: self.toggle(item))
        self.tree.toggleRequested.connect(self.toggle)
        self._frame_layout.addWidget(self.tree)

        self.empty_label = QLabel(lang.translate(TranslationKeys.TAG_PICKER_NO_MATCH), self._frame)
        self.empty_label.setObjectName("GroupedTagPickerSectionLabel")
        self.empty_label.setVisible(False)
        self._frame_layout.addWidget(self.empty_label)

        catalog = self._owner.catalog()
        for group, tags in catalog.groups:
            header = self._header(group.name, checkable=True)
            for tag in tags:
                self._leaf(header, tag)
        if catalog.groups and catalog.ungrouped:
            # No box here: one click must not tick every tag that nobody has grouped.
            header = self._header(lang.translate(TranslationKeys.TAG_PICKER_UNGROUPED), checkable=False)
            for tag in catalog.ungrouped:
                self._leaf(header, tag)
        else:
            for tag in catalog.ungrouped:
                self._leaf(self.tree.invisibleRootItem(), tag)
        self.tree.setRootIsDecorated(bool(catalog.groups))
        self.tree.expandAll()
        self.search.textChanged.connect(self._filter)
        self.show_selection()
        self._fit_height()

    def _header(self, text: str, *, checkable: bool) -> QTreeWidgetItem:
        item = QTreeWidgetItem(self.tree, [text])
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        item.setData(0, _TAG_ID_ROLE, None)
        font = item.font(0)
        font.setBold(True)
        item.setFont(0, font)
        if checkable:
            item.setCheckState(0, Qt.CheckState.Unchecked)
        return item

    def _leaf(self, parent: QTreeWidgetItem, tag: Tag) -> None:
        item = QTreeWidgetItem(parent, [tag.name])
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        item.setData(0, _TAG_ID_ROLE, tag.id)
        item.setToolTip(0, tag.name)
        item.setCheckState(0, Qt.CheckState.Unchecked)

    def _top_items(self) -> list[QTreeWidgetItem]:
        return [self.tree.topLevelItem(index) for index in range(self.tree.topLevelItemCount())]

    @staticmethod
    def _children(item: QTreeWidgetItem) -> list[QTreeWidgetItem]:
        return [item.child(index) for index in range(item.childCount())]

    def toggle(self, item: QTreeWidgetItem) -> None:
        tag_id = item.data(0, _TAG_ID_ROLE)
        if tag_id:
            self._owner.set_checked([tag_id], item.checkState(0) != Qt.CheckState.Checked)
            return
        if item.data(0, Qt.ItemDataRole.CheckStateRole) is None:
            item.setExpanded(not item.isExpanded())
            return
        # A group box acts on the tags the search leaves visible.
        shown = [child for child in self._children(item) if not child.isHidden()]
        tick = any(child.checkState(0) != Qt.CheckState.Checked for child in shown)
        self._owner.set_checked([child.data(0, _TAG_ID_ROLE) for child in shown], tick)

    def show_selection(self) -> None:
        selected = set(self._owner.selected_ids())
        for item in self._top_items():
            children = self._children(item)
            if not children:
                if item.data(0, _TAG_ID_ROLE):
                    self._mark(item, item.data(0, _TAG_ID_ROLE) in selected)
                continue
            for child in children:
                self._mark(child, child.data(0, _TAG_ID_ROLE) in selected)
            ticked = sum(child.data(0, _TAG_ID_ROLE) in selected for child in children)
            if item.data(0, Qt.ItemDataRole.CheckStateRole) is not None:
                item.setCheckState(0, Qt.CheckState.Unchecked if not ticked else
                                   Qt.CheckState.Checked if ticked == len(children) else Qt.CheckState.PartiallyChecked)
        self.count_label.setText(
            self._owner._lang.translate(TranslationKeys.TAG_PICKER_SELECTED).format(count=len(selected)))

    @staticmethod
    def _mark(item: QTreeWidgetItem, checked: bool) -> None:
        item.setCheckState(0, Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)

    def _filter(self, text: str) -> None:
        """A match on the group name shows its whole group."""
        needle = text.strip().casefold()
        any_shown = False
        for item in self._top_items():
            children = self._children(item)
            if not children:
                hidden = bool(needle) and needle not in item.text(0).casefold()
                item.setHidden(hidden)
                any_shown = any_shown or not hidden
                continue
            whole_group = needle in item.text(0).casefold()
            visible = 0
            for child in children:
                hidden = not whole_group and needle not in child.text(0).casefold()
                child.setHidden(hidden)
                visible += not hidden
            item.setHidden(not visible)
            if needle:
                item.setExpanded(True)
            any_shown = any_shown or bool(visible)
        self.empty_label.setVisible(not any_shown)
        self.tree.setVisible(any_shown)

    def _fit_height(self) -> None:
        self.tree.ensurePolished()  # the row height comes from the stylesheet
        rows = len(self.tree.findItems("*", Qt.MatchFlag.MatchWildcard | Qt.MatchFlag.MatchRecursive))
        wanted = max(1, rows) * max(1, self.tree.sizeHintForRow(0)) + 2 * self.tree.frameWidth()
        self.tree.setFixedHeight(min(self.TREE_MAX_HEIGHT, wanted))

    def _extra_style(self, colors: dict[str, str]) -> str:
        theme_dir = StylePaths.DARK if ThemeManager.effective_theme() == "dark" else StylePaths.LIGHT
        mark = (Path(theme_dir) / "check_white.svg").as_posix()
        partial = (Path(theme_dir) / "partial_white.svg").as_posix()
        accent = colors["selected_border"]
        tree = "QTreeWidget#GroupedTagPickerTree"
        return (
            f"QLineEdit#GroupedTagPickerSearch {{ background: {colors['panel_bg']}; color: {colors['text']};"
            "border: 1px solid rgba(128,128,128,0.30); border-radius: 6px; padding: 4px 8px; }"
            f"QLineEdit#GroupedTagPickerSearch:focus {{ border-color: {colors['border']}; }}"
            f"{tree} {{ background: transparent; color: {colors['text']}; border: none; outline: none;"
            "font-size: 12px; show-decoration-selected: 0; selection-background-color: transparent; }"
            f"{tree}::item {{ min-height: 20px; padding: 2px 4px; border: 1px solid transparent; border-radius: 6px;"
            f"background: transparent; color: {colors['text']}; }}"
            f"{tree}::branch {{ background: transparent; }}"
            f"{tree}::item:hover {{ background: {colors['hover']}; }}"
            f"{tree}::item:selected {{ background: {colors['selected']}; border-color: {accent};"
            f"color: {colors['text']}; }}"
            f"{tree}::branch:selected, {tree}::branch:hover {{ background: {colors['frame_bg']}; }}"
            f"{tree}::indicator {{ width: 12px; height: 12px; border: 1px solid {colors['muted']}; border-radius: 3px;"
            f"background: {colors['frame_bg']}; image: none; }}"
            f"{tree}::indicator:checked {{ background: {accent}; border-color: {accent}; image: url({mark}); }}"
            f"{tree}::indicator:indeterminate {{ background: {accent}; border-color: {accent};"
            f"image: url({partial}); }}"
        )


class GroupedTagPicker(QWidget):
    """The closed control shows the selection; the list opens under it.

    Selected ids the catalog does not know are kept: a preference must not vanish because a list was short.
    """

    selectionChanged = pyqtSignal(list)

    def __init__(self, parent: Optional[QWidget] = None, *, placeholder: str = "") -> None:
        super().__init__(parent)
        self._lang = LanguageManager()
        self._placeholder = placeholder or self._lang.translate(TranslationKeys.SELECT)
        self._catalog = TagCatalog()
        self._selected: set[str] = set()
        self._popup: Optional[_TagPickerPopup] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._control = _TagPickerControl(self)
        self._control.clicked.connect(self._toggle_popup)
        layout.addWidget(self._control)
        self._show_summary()

    def catalog(self) -> TagCatalog:
        return self._catalog

    def set_catalog(self, catalog: TagCatalog) -> None:
        self.close_popup()
        self._catalog = catalog
        self._show_summary()

    def set_status(self, text: str, *, tooltip: str = "") -> None:
        """Text on the closed control while there is no list (loading, a failed read)."""
        self._control.set_summary(text)
        self._control.setToolTip(tooltip or text)

    def selected_names(self) -> list[str]:
        return [tag.name for tag in self._catalog.tags() if tag.id in self._selected]

    def selected_ids(self) -> list[str]:
        """The selected tags of this catalog, in list order."""
        return [tag.id for tag in self._catalog.tags() if tag.id in self._selected]

    def set_selected_ids(self, ids: Sequence[str], emit: bool = False) -> None:
        self._selected = {str(value) for value in ids or []}
        self._after_change(emit)

    def set_checked(self, ids: Sequence[str], checked: bool) -> None:
        if checked:
            self._selected.update(str(value) for value in ids)
        else:
            self._selected.difference_update(str(value) for value in ids)
        self._after_change(True)

    def clear_selection(self) -> None:
        self.set_checked(self.selected_ids(), False)

    def retheme(self) -> None:
        self.close_popup()
        self._control.apply_style()

    def close_popup(self) -> None:
        popup, self._popup = self._popup, None
        if popup is not None:
            try:
                popup.close()
            except RuntimeError:  # already deleted by Qt
                pass

    def _after_change(self, emit: bool) -> None:
        self._show_summary()
        if self._popup is not None:
            self._popup.show_selection()
        if emit:
            self.selectionChanged.emit(self.selected_ids())

    def _show_summary(self) -> None:
        self._control.setEnabled(len(self._catalog) > 0)
        names = self.selected_names()
        if not len(self._catalog):
            text = self._lang.translate(TranslationKeys.TAG_PICKER_NO_TAGS)
        elif not names:
            text = self._placeholder
        else:
            text = ", ".join(names[:_NAMES_IN_SUMMARY])
            if len(names) > _NAMES_IN_SUMMARY:
                text += f"  +{len(names) - _NAMES_IN_SUMMARY}"
        self._control.set_summary(text)
        self._control.setToolTip("\n".join(names))

    def _toggle_popup(self) -> None:
        if self._popup is not None:
            self.close_popup()
            return
        popup = _TagPickerPopup(self, min_width=self._control.width(), parent=self)
        self._popup = popup
        popup.destroyed.connect(lambda *_: setattr(self, "_popup", None))
        popup.move(self._control.mapToGlobal(self._control.rect().bottomLeft()))
        popup.show()
        popup.search.setFocus()
