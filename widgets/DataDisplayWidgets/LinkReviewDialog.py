from PyQt5.QtWidgets import QPushButton, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QWidget, QFrame

from ...constants.button_props import ButtonVariant
from ...constants.file_paths import QssPaths
from ...languages.translation_keys import TranslationKeys
from ...widgets.theme_manager import ThemeManager, styleExtras


class LinkReviewDialog(QDialog):
    def __init__(self, existing_display: dict[str, str], selected_display: dict[str, str], lang_manager) -> None:
        super().__init__()
        self.setObjectName("LinkReviewDialog")
        self.setWindowTitle(lang_manager.translate(TranslationKeys.CHOSE_FROM_MAP))
        self.reselect_requested = False

        ThemeManager.apply_module_style(self, [QssPaths.MAIN, QssPaths.BUTTONS])
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        lists = QHBoxLayout()

        existing_list = QListWidget()
        existing_items = sorted(existing_display.values(), key=lambda s: s.lower())
        existing_list.addItems(existing_items)
        existing_list.setMinimumWidth(200)
        lists.addWidget(
            self._wrap_with_label(
                lang_manager.translate(TranslationKeys.LINK_REVIEW_ALREADY_LINKED), existing_list
            )
        )

        new_numbers = [n for n in selected_display.keys() if n and n not in existing_display]
        new_items = sorted((selected_display.get(n, n) for n in new_numbers), key=lambda s: s.lower())
        new_list = QListWidget()
        new_list.addItems(new_items)
        new_list.setMinimumWidth(200)
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
        confirm_btn = QPushButton(lang_manager.translate(TranslationKeys.CONFIRM))
        confirm_btn.setProperty("variant", ButtonVariant.SUCCESS)
        cancel_btn = QPushButton(lang_manager.translate(TranslationKeys.CANCEL))
        cancel_btn.setProperty("variant", ButtonVariant.WARNING)
        buttons.addWidget(reselect_btn)
        buttons.addWidget(cancel_btn)
        buttons.addWidget(confirm_btn)
        layout.addLayout(buttons)

        reselect_btn.clicked.connect(self._on_reselect)
        cancel_btn.clicked.connect(self.reject)
        confirm_btn.clicked.connect(self.accept)

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