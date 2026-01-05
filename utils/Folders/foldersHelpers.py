
import subprocess
from typing import Optional
import shutil
import os
from PyQt5.QtWidgets import QFileDialog
from ...python.api_client import APIClient
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys

from ...utils.url_manager import Module
from ...modules.Settings.setting_keys import SettingDialogPlaceholders
from ...constants.settings_keys import SettingsService
from ..messagesHelper import ModernMessageDialog

UPDATE_project_properties = 'updateProjectsProperties.graphql'

class FolderEngines:
    @staticmethod
    def generate_project_folder_from_template( project_id, 
                                               project_name, 
                                               project_number,
                                               source_folder,
                                               target_folder
                                               ) -> None:
        text = "Ettevalmistatud struktuuriga projektikaustade genereerimine on mõeldud eelkõige uutele projektidele.\nEnne jätkamist kontrolli ega samasisulist kausta pole juba loodud.\nOled kindel, et soovid jätkata?"
        confirm_title = LanguageManager.translate_static(TranslationKeys.CONFIRM) or "Confirmation"
        yes_label = LanguageManager.translate_static(TranslationKeys.YES) or "Yes"
        no_label = LanguageManager.translate_static(TranslationKeys.NO) or "No"

        overall_confirmation = ModernMessageDialog.ask_yes_no(
            confirm_title,
            text,
            yes_label=yes_label,
            no_label=no_label,
            default=yes_label,
        )

        if overall_confirmation:
            try:
                # Use the FolderNameGenerator to generate the folder name based on the user-defined order
                folder_name = FolderNameGenerator().folder_structure_name_order(project_name, project_number)
                dest_dir = os.path.join(target_folder, folder_name)

                # Check if the target folder with the new name already exists
                if os.path.exists(dest_dir):
                    text = f"Kaust nimega '{folder_name}' on juba sihtkohas olemas."
                    heading = LanguageManager.translate_static(TranslationKeys.WARNING) or "Warning"
                    ModernMessageDialog.show_warning(heading, text)
                else:
                    shutil.copytree(source_folder, dest_dir)
                    
                    # Ask the user for confirmation
                    confirmation = ModernMessageDialog.ask_yes_no(
                        confirm_title,
                        "Oled kindel, et soovid genereeritud kausta lingi lisada Mailablis projektile?",
                        yes_label=yes_label,
                        no_label=no_label,
                        default=yes_label,
                    )


                    if confirmation:
                        # Call the linkUpdater function
                        print(f"project_id {project_id}")
                        Link_updater().update_link(project_id, dest_dir)

                    else:
                        print("Operation canceled by the user.")
            
                    # Display success message using modern dialog box
                    heading = LanguageManager.translate_static(TranslationKeys.SUCCESS) or "Success"
                    text = (f"Kausta '{source_folder}'\n(k.a kaustas sisalduvad alamkaustad ja failid) dubleerimine õnnestus.")
                    text_2 = f"Sihtkohta on genereeritud kaust nimetusega \n'{folder_name}'."
                    ModernMessageDialog.show_info(heading, f"{text}\n\n{text_2}")
                    
            except Exception as e:
                heading = LanguageManager.translate_static(TranslationKeys.WARNING) or "Warning"
                text = f"An error occurred: {e}"
                ModernMessageDialog.show_warning(heading, text)
                        
        else:
            print("Operation canceled by the user.")


class Link_updater:
    def update_link(self, project_id, link):
            
        module = Module.PROJECT.name
        from ...python.GraphQLQueryLoader import GraphQLQueryLoader
        file =  UPDATE_project_properties
        query = GraphQLQueryLoader().load_query_by_module(module, file)
        
        variables = {
                    "input": {
                        "id": project_id,
                        "filesPath": link                            
                    }
                    }
        
        client = APIClient()
        response = client.send_query(query, variables=variables)
        print(response)


class FolderNameGenerator:
    def folder_structure_name_order(self, project_name, project_number):
        service = SettingsService()

        print("[folder_name] start", {"project_name": project_name, "project_number": project_number})

        enabled_raw = service.module_label_value(
            Module.PROJECT.value,
            SettingDialogPlaceholders.PROJECTS_PREFERED_FOLDER_NAME_STRUCTURE_ENABLED,
        )
        print("[folder_name] enabled_raw", enabled_raw)
        rule_raw = service.module_label_value(
            Module.PROJECT.value,
            SettingDialogPlaceholders.PROJECTS_PREFERED_FOLDER_NAME_STRUCTURE_RULE,
        ) or ""
        print("[folder_name] rule_raw", rule_raw)

        rule = str(rule_raw).strip()
        enabled = self._as_bool(enabled_raw)
        print("[folder_name] normalized", {"enabled": enabled, "rule": rule})

        if not enabled or not rule:
            rule = "PROJECT_NUMBER + PROJECT_NAME"
            print("[folder_name] fallback rule", rule)

        components = [c.strip() for c in rule.split(" + ") if c.strip()]
        print("[folder_name] components", components)
        folder_name_parts = []

        for component in components:
            print("[folder_name] component", component)
            if component.startswith("SYMBOL(") and component.endswith(")"):
                symbol = component[len("SYMBOL("):-1]
                print("[folder_name] symbol", symbol)
                if symbol:
                    folder_name_parts.append(symbol)
            elif component == "PROJECT_NUMBER":
                folder_name_parts.append(project_number or "")
            elif component == "PROJECT_NAME":
                folder_name_parts.append(project_name or "")

        if not folder_name_parts:
            folder_name_parts = [project_number or "", project_name or ""]
            print("[folder_name] fallback parts", folder_name_parts)

        folder_name = "".join(folder_name_parts)
        print("[folder_name] result", folder_name)
        return folder_name

    def _as_bool(self, value) -> bool:
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"true", "1", "yes", "on"}:
                return True
            if lowered in {"false", "0", "no", "off", ""}:
                return False
        return bool(value)


class FolderHelpers:
    @staticmethod
    def select_folder_path(parent=None, start_path: str = "") -> Optional[str]:
        options = QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        caption: str = "Select folder"
        directory = QFileDialog.getExistingDirectory(parent, caption, start_path or os.path.expanduser("~"), options)
        return directory or None

    @staticmethod
    def open_item_folder(file_path: Optional[str]) -> None:
        if not file_path:
            return
        target = file_path.replace("/", "\\")
        try:
            if target.lower().startswith("http"):
                subprocess.Popen(["start", "", target], shell=True)
            else:
                subprocess.Popen(["explorer", target], shell=True)
        except Exception:
            pass