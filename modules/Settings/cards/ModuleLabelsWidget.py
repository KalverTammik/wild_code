from typing import Callable, Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox

from ....widgets.theme_manager import ThemeManager
from ....constants.module_icons import IconNames
from ....utils.Folders.foldersHelpers import FolderHelpers
from ....constants.file_paths import QssPaths
from ....languages.translation_keys import SettingDialogPlaceholders

class ModuleLabelsWidget(QFrame):

    labelChanged = pyqtSignal(str, object)


    def __init__(self, module_key: str, module_labels, lang_manager):
        super().__init__()
        self.module_key = module_key
        self.lang_manager = lang_manager
        self._module_labels = module_labels or []
        self._label_widgets = {}
        self._build()


    def _not_defined_jet(self) -> str:
        return self.lang_manager.translate(SettingDialogPlaceholders.UNSET)
    
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

    def _checkbox_value(self, label_def: dict) -> bool:
        if not label_def:
            return False
        raw_value = label_def.get("value")
        if callable(raw_value):
            try:
                raw_value = raw_value()
            except Exception:
                raw_value = False
        if isinstance(raw_value, str):
            lowered = raw_value.strip().lower()
            if lowered in {"true", "1", "yes", "on"}:
                return True
            if lowered in {"false", "0", "no", "off", ""}:
                return False
        return bool(raw_value)

    def _build(self):
        
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 6, 6)
        layout.setSpacing(4)

        for label_def in self._module_labels:
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(6)

            key = label_def.get("key")
            value_widget = None

            title = QLabel(label_def.get("title_value") +":")
            title.setObjectName("modulelabeltitle")
            title.setProperty("modulelabeltitle", "true")
            title.setMinimumWidth(300)
            row.addWidget(title, 0, Qt.AlignLeft)
            
            tool = label_def.get("tool")
            if tool == "button":
                custom_handler: Optional[Callable[[str, str, str], Optional[str]]] = label_def.get("on_click")

                if callable(custom_handler):
                    button = QPushButton()
                    button.setObjectName(f"{key}_button")
                    icon = ThemeManager().get_qicon(IconNames.ICON_SETTINGS)
                    button.setIcon(icon)

                    clear_button = QPushButton()
                    clear_button.setObjectName(f"{key}_clear")
                    icon = ThemeManager().get_qicon(IconNames.CRITICAL)
                    clear_button.setIcon(icon)
                    clear_button.setToolTip(self.lang_manager.translate("Clear value") if self.lang_manager else "Clear value")
                    clear_button.clicked.connect(lambda _, k=key: self._clear_label_value(k))

                    value_label = QLabel(self._label_value(label_def))
                    value_label.setObjectName("modulelabelvalue")
                    value_label.setProperty("modulelabelvalue", "true")
                    value_label.setWordWrap(True)

                    button.clicked.connect(
                        lambda _, k=key, lbl=value_label, fn=custom_handler: self._handle_custom_click(fn, k, lbl)
                    )
                    value_label.setMinimumWidth(200)
                    row.addWidget(value_label, 0, Qt.AlignLeft)
                    row.addWidget(button, 0, Qt.AlignRight)
                    row.addWidget(clear_button, 0, Qt.AlignRight)
                    value_widget = value_label

            if tool == "checkBox":
                checkbox = QCheckBox()  
                checkbox.setObjectName(f"{key}_checkbox")
                checkbox.setChecked(self._checkbox_value(label_def))
                checkbox.stateChanged.connect(
                    lambda _, k=key, cb=checkbox: self._on_checkbox_changed(k, cb)
                )
                row.addWidget(checkbox, 0, Qt.AlignRight)
                value_widget = checkbox
            row.addStretch(1)
            layout.addLayout(row)


            if key and value_widget:
                self._label_widgets[key] = value_widget

        root.addLayout(layout)
        self.retheme()

    def _on_select_folder_clicked(self, key: str, value_label: QLabel) -> None:
        if not key:
            return
        start_path = value_label.text() or ""
        selected = FolderHelpers.select_folder_path(self, start_path=start_path)
        if selected:
            self._update_label_value(key, selected, value_label)

    def _clear_label_value(self, key: str) -> None:
        widget = self._label_widgets.get(key)
        if not widget:
            return
        if isinstance(widget, QLabel):
            widget.setText(self._not_defined_jet())
            widget.setProperty("modulelabelvalue", "false")
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        elif isinstance(widget, QCheckBox):
            widget.blockSignals(True)
            widget.setChecked(False)
            widget.blockSignals(False)
        self.labelChanged.emit(key, "" if isinstance(widget, QLabel) else False)

    def _handle_custom_click(self, handler: Callable[[str, str, str], Optional[str]], key: str, value_label: QLabel) -> None:
        """Run a custom handler; if it returns a value, update label and emit signal."""
        try:
            current = value_label.text() or ""
            new_value = handler(self.module_key, key, current)
            if new_value not in (None, ""):
                self._update_label_value(key, str(new_value), value_label)
        except Exception:
            pass

    def _on_checkbox_changed(self, key: str, checkbox: QCheckBox) -> None:
        if not key:
            return
        value = bool(checkbox.isChecked())
        self._label_widgets[key] = checkbox
        self.labelChanged.emit(key, value)

    def _update_label_value(self, key: str, value: str, widget: QLabel) -> None:
        widget.setText(value)
        self._label_widgets[key] = widget
        self.labelChanged.emit(key, value)

    def set_label_value(self, key: str, value):
        if not key:
            return
        target = self._label_widgets.get(key)
        if target:
            if isinstance(target, QCheckBox):
                target.blockSignals(True)
                target.setChecked(bool(value))
                target.blockSignals(False)
            else:
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



