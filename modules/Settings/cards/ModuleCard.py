from PyQt5.QtWidgets import QVBoxLayout, QLabel, QFrame
from .BaseCard import BaseCard

class ModuleCard(BaseCard):
    def __init__(self, lang_manager, module_name: str, translated_name: str):
        super().__init__(lang_manager, translated_name)
        cw = self.content_widget()
        cl = QVBoxLayout(cw); cl.setContentsMargins(0,0,0,0); cl.setSpacing(6)
        placeholder = QFrame(cw)
        placeholder.setObjectName("ModuleSettingsPlaceholder")
        placeholder.setStyleSheet("border: 1px solid #d33; min-height: 64px; border-radius: 6px;")
        pl = QVBoxLayout(placeholder); pl.setContentsMargins(8,8,8,8); pl.setSpacing(6)
        pl.addWidget(QLabel(self.lang_manager.translate("Module settings placeholder"), placeholder))
        cl.addWidget(placeholder)
        self.module_name = module_name
