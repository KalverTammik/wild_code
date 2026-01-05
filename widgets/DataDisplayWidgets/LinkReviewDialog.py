from PyQt5.QtWidgets import QPushButton, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QWidget

from ...constants.button_props import ButtonVariant
from ...constants.file_paths import QssPaths
from ...languages.translation_keys import TranslationKeys
from ...widgets.theme_manager import ThemeManager


class LinkReviewDialog(QDialog):
    def __init__(self, existing: set[str], selected: list[str], lang_manager) -> None:
        super().__init__()
        self.setObjectName("LinkReviewDialog")
        self.setWindowTitle(lang_manager.translate(TranslationKeys.CHOSE_FROM_MAP))
        self.reselect_requested = False

        ThemeManager.apply_module_style(self, [QssPaths.POPUP, QssPaths.BUTTONS])
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.addWidget(QLabel("Connections"))

        lists = QHBoxLayout()

        existing_list = QListWidget()
        existing_list.addItems(sorted(existing))
        existing_list.setMinimumWidth(200)
        lists.addWidget(self._wrap_with_label("Already linked", existing_list))

        new_set = [n for n in selected if n and n not in existing]
        new_list = QListWidget()
        new_list.addItems(new_set)
        new_list.setMinimumWidth(200)
        lists.addWidget(self._wrap_with_label("New selections", new_list))

        layout.addLayout(lists)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        reselect_btn = QPushButton("Reselect")
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
        v.addWidget(QLabel(text))
        v.addWidget(widget)
        return container

    def _on_reselect(self):
        self.reselect_requested = True
        self.reject()