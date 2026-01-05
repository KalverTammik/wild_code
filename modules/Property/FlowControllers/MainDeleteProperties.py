from ....python.api_client import APIClient
from ....languages.translation_keys import TranslationKeys
from ....constants.layer_constants import IMPORT_PROPERTY_TAG
from ....constants.settings_keys import SettingsService
from ....utils.mapandproperties.PropertyTableManager import PropertyTableManager
from ....utils.mapandproperties.PropertyDataLoader import PropertyDataLoader
from ....languages.language_manager import LanguageManager 
from ....utils.MapTools.MapHelpers import MapHelpers
from ....utils.url_manager import Module
from ....python.GraphQLQueryLoader import GraphQLQueryLoader
from ....widgets.theme_manager import ThemeManager
from ....constants.file_paths import QssPaths

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from ....utils.messagesHelper import ModernMessageDialog



class deleteProperty:
    @staticmethod
    def delete_single_item(item: str):

        module = Module.PROPERTY.name

        file =  "deleteProperty.graphql"
        query = GraphQLQueryLoader().load_query_by_module(module, file)


        variables = {
            "id": item  # ID of property i want to delete
            }

        client = APIClient()
        result = client.send_query(query, variables=variables, return_raw=True, with_success=True)

        if result.get("success") is True:
            return True, ""

        err = result.get("error")
        message = f"Failed to delete property with ID {item}."
        if err:
            message = f"{message} Error: {err}"
        return False, message
        
class DeletePropertyUI(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.lang_manager = LanguageManager()

        self.setWindowTitle(
            self.lang_manager.translate(TranslationKeys.REMOVE_PROPERTY) or "Remove property"
        )
        self.setModal(True)
        self.setFixedSize(420, 160)

        ThemeManager.set_initial_theme(
            self,
            None,
            qss_files=[QssPaths.MAIN, QssPaths.SETUP_CARD, QssPaths.COMBOBOX],
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        title = QLabel(
            self.lang_manager.translate(TranslationKeys.REMOVE_PROPERTY) or "Remove property"
        )
        title.setObjectName("FilterTitle")
        layout.addWidget(title)

        self._id_input = QLineEdit(self)
        self._id_input.setPlaceholderText("Property ID")
        self._id_input.setClearButtonEnabled(True)
        self._id_input.setObjectName("PropertyIdInput")
        layout.addWidget(self._id_input)

        btns = QHBoxLayout()
        btns.addStretch(1)

        self._btn_cancel = QPushButton(
            self.lang_manager.translate(TranslationKeys.CANCEL) or "Cancel",
            self,
        )
        self._btn_cancel.setObjectName("ConfirmButton")
        self._btn_cancel.clicked.connect(self.reject)
        btns.addWidget(self._btn_cancel)

        self._btn_confirm = QPushButton(
            self.lang_manager.translate(TranslationKeys.CONFIRM) or "Confirm",
            self,
        )
        self._btn_confirm.setObjectName("ConfirmButton")
        self._btn_confirm.clicked.connect(self._on_confirm_clicked)
        btns.addWidget(self._btn_confirm)

        layout.addLayout(btns)

        self.show()
        self.exec_()

    def _on_confirm_clicked(self) -> None:
        property_id = (self._id_input.text() or "").strip()
        if not property_id:
            ModernMessageDialog.show_warning(
                self.lang_manager.translate("Missing ID") or "Missing ID",
                self.lang_manager.translate("Please enter a property id.") or "Please enter a property id.",
            )
            return

        self._btn_confirm.setEnabled(False)
        self._btn_cancel.setEnabled(False)
        try:
            ok, message = deleteProperty.delete_single_item(property_id)
        
            if not ok:
                ModernMessageDialog.show_warning(
                    self.lang_manager.translate("Delete failed") ,
                    message,
                )
        finally:
            self._btn_confirm.setEnabled(True)
            self._btn_cancel.setEnabled(True)

        if ok:
            ModernMessageDialog.show_info(
                self.lang_manager.translate("Deleted") or "Deleted",
                self.lang_manager.translate("Property deleted successfully.") or "Property deleted successfully.",
            )
            self.accept()
            return



