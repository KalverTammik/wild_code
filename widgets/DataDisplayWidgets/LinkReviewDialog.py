from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QPushButton, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QWidget, QFrame,
)

from ...constants.button_props import ButtonVariant
from ...constants.file_paths import QssPaths
from ...languages.translation_keys import TranslationKeys
from ...ui.theme_manager import ThemeManager, styleExtras


class PropertyLinkReviewDialog(QDialog):
    LIST_MIN_WIDTH = 200

    def __init__(
        self, existing_display: dict[str, str], selected_display: dict[str, str], lang_manager, *, allow_removal: bool = False
    ) -> None:
        """`allow_removal` makes each linked row tickable; `numbers_to_remove` then names the ticked ones."""
        super().__init__()
        self._lang = lang_manager
        self.setObjectName("LinkReviewDialog")
        self.setWindowTitle(lang_manager.translate(TranslationKeys.LINK_REVIEW_CONNECTIONS_TITLE))
        self.reselect_requested = False

        ThemeManager.apply_module_style(self, [QssPaths.MAIN, QssPaths.BUTTONS])
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        lists = QHBoxLayout()

        existing_list = QListWidget()
        for number, label in sorted(existing_display.items(), key=lambda pair: pair[1].lower()):
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, number)
            if allow_removal:
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked)
            else:
                item.setFlags(item.flags() & ~Qt.ItemIsUserCheckable)
            existing_list.addItem(item)
        existing_list.setMinimumWidth(self.LIST_MIN_WIDTH)
        self._existing_list = existing_list
        existing_title = TranslationKeys.LINK_REVIEW_MARK_REMOVE if allow_removal else TranslationKeys.LINK_REVIEW_ALREADY_LINKED
        lists.addWidget(self._wrap_with_label(lang_manager.translate(existing_title), existing_list))

        new_numbers = [n for n in selected_display.keys() if n and n not in existing_display]
        new_items = sorted((selected_display.get(n, n) for n in new_numbers), key=lambda s: s.lower())
        new_list = QListWidget()
        new_list.addItems(new_items)
        new_list.setMinimumWidth(self.LIST_MIN_WIDTH)
        lists.addWidget(
            self._wrap_with_label(
                lang_manager.translate(TranslationKeys.LINK_REVIEW_NEW_SELECTIONS), new_list
            )
        )

        layout.addLayout(lists)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        reselect_btn = QPushButton(lang_manager.translate(TranslationKeys.LINK_REVIEW_RESELECT))
        reselect_btn.setProperty("variant", ButtonVariant.PRIMARY)
        # The links are added to the existing ones; nothing is removed here.
        confirm_btn = QPushButton(lang_manager.translate(TranslationKeys.LINK_REVIEW_ADD_SELECTED))
        confirm_btn.setProperty("variant", ButtonVariant.SUCCESS)
        cancel_btn = QPushButton(lang_manager.translate(TranslationKeys.CANCEL_BUTTON))
        cancel_btn.setProperty("variant", ButtonVariant.WARNING)
        buttons.addWidget(reselect_btn)
        buttons.addWidget(cancel_btn)
        buttons.addWidget(confirm_btn)
        layout.addLayout(buttons)

        reselect_btn.clicked.connect(self._on_reselect)
        cancel_btn.clicked.connect(self.reject)
        confirm_btn.clicked.connect(self.accept)
        self._confirm_btn = confirm_btn
        existing_list.itemChanged.connect(self._update_confirm_text)

    @property
    def numbers_to_remove(self) -> list[str]:
        return [
            str(self._existing_list.item(row).data(Qt.UserRole))
            for row in range(self._existing_list.count())
            if self._existing_list.item(row).checkState() == Qt.Checked
        ]

    def _update_confirm_text(self, *_args) -> None:
        key = TranslationKeys.LINK_REVIEW_SAVE_CHANGES if self.numbers_to_remove else TranslationKeys.LINK_REVIEW_ADD_SELECTED
        self._confirm_btn.setText(self._lang.translate(key))

    def _wrap_with_label(self, text: str, widget: QListWidget) -> QWidget:
        container = QWidget()
        v = QVBoxLayout(container)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(4)
        header = QFrame()
        header.setFrameShape(QFrame.StyledPanel)
        header.setFrameShadow(QFrame.Raised)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 6, 8, 6)
        header_layout.setSpacing(6)
        header_layout.addWidget(QLabel(text))
        styleExtras.apply_chip_shadow(container)
        v.addWidget(header)
        v.addWidget(widget)
        return container

    def _on_reselect(self):
        self.reselect_requested = True
        self.reject()
