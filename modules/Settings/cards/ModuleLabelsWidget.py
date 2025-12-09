from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from ....widgets.theme_manager import ThemeManager
from ....constants.module_icons import ModuleIcons
from ....utils.Folders.foldersHelpers import FolderHelpers
from ....constants.file_paths import QssPaths

class ModuleLabelsWidget(QFrame):

    labelChanged = pyqtSignal(str, str)


    def __init__(self, module_key: str, module_labels, lang_manager):
        super().__init__()
        self.module_key = module_key
        self.lang_manager = lang_manager
        self._module_labels = module_labels or []
        self._label_widgets = {}
        self._build()


    def _not_defined_jet(self) -> str:
        return "Määramata"
    
    def _label_value(self, label_def: dict) -> str:
        if not label_def:
            return self._not_defined_jet()
        raw_value = label_def.get("value")
        if callable(raw_value):
            try:
                raw_value = raw_value()
            except Exception:
                raw_value = None
        if raw_value is None or raw_value == "":
            return self._not_defined_jet()
        return str(raw_value)

    def _build(self):
        
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 6)
        layout.setSpacing(4)

        for label_def in self._module_labels:
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(6)

            key = label_def.get("key")

            title = QLabel(label_def.get("title_value"))
            title.setObjectName("modulelabeltitle")
            title.setProperty("modulelabeltitle", "true")

            value_label = QLabel(self._label_value(label_def))
            value_label.setObjectName("modulelabelvalue")
            value_label.setProperty("modulelabelvalue", "true")
            value_label.setWordWrap(True)

            button = QPushButton("Muuda ...")
            button.setObjectName(f"{key}_button")
            icon = ThemeManager().get_qicon(ModuleIcons.ICON_SETTINGS)
            button.setIcon(icon)

            button.clicked.connect(lambda _, k=key, lbl=value_label: self._on_select_folder_clicked(k, lbl))
            
            row.addWidget(title, 0, Qt.AlignLeft)
            row.addWidget(value_label, 0, Qt.AlignLeft)
            row.addWidget(button, 0, Qt.AlignRight)
            row.addStretch(1)
            layout.addLayout(row)

            if key:
                self._label_widgets[key] = value_label

        root.addLayout(layout)
        self.retheme()

    def _on_select_folder_clicked(self, key: str, value_label: QLabel) -> None:
        if not key:
            return
        start_path = value_label.text() or ""
        selected = FolderHelpers.select_folder_path(self, start_path=start_path)
        if selected:
            value_label.setText(selected)
            self._label_widgets[key] = value_label
            self.labelChanged.emit(key, selected)

    def set_label_value(self, key: str, value):
        if not key:
            return
        target = self._label_widgets.get(key)
        if target:
            is_defined = value not in (None, "")
            target.setText(str(value) if is_defined else self._not_defined_jet())
            target.setProperty("modulelabelvalue", "true" if is_defined else "false")
            target.style().unpolish(target)
            target.style().polish(target)

    @property
    def label_widgets(self):
        return self._label_widgets
    
    def retheme(self) -> None:
        ThemeManager.apply_module_style(self, [QssPaths.SETTING_MODULE_LABELS])
        #styleExtras.apply_chip_shadow(self)