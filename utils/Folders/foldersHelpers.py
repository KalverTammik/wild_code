
import subprocess
from typing import Optional
import shutil
import os
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from ...python.api_client import APIClient
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys

from ...utils.url_manager import Module

UPDATE_project_properties = 'updateProjectsProperties.graphql'

class FolderEngines:
    @staticmethod
    def copy_and_rename_folder(project_id, project_name, project_number):
        text = "Ettevalmistatud struktuuriga projektikaustade genereerimine on mõeldud eelkõige uutele projektidele.\nEnne jätkamist kontrolli ega samasisulist kausta pole juba loodud.\nOled kindel, et soovid jätkata?"

        overall_confirmation = QMessageBox.question(None, "Confirmation", text,
                                            QMessageBox.Yes | QMessageBox.No)

        if overall_confirmation == QMessageBox.Yes:

            source_folder = SettingsDataSaveAndLoad().load_projcets_copy_folder_path_value()
            target_folder = SettingsDataSaveAndLoad().load_target_Folder_path_value()


            try:
                # Use the FolderNameGenerator to generate the folder name based on the user-defined order
                folder_name = FolderNameGenerator().folder_structure_name_order(project_name, project_number)
                
                # Check if the target folder with the new name already exists
                if os.path.exists(os.path.join(os.path.dirname(target_folder), folder_name)):                        
                    text = f"Kaust nimega '{folder_name}' on juba sihtkohas olemas."
                    heading = LanguageManager.translate_static(TranslationKeys.WARNING) or "Warning"
                    QMessageBox.warning(None, heading, text)
                else:
                    shutil.copytree(source_folder, target_folder)
                    os.rename(target_folder, os.path.join(os.path.dirname(target_folder), folder_name))
                    
                    # Ask the user for confirmation
                    confirmation = QMessageBox.question(None, "Confirmation", "Oled kindel, et soovid genereeritud kausta lingi lisada Mailablis projektile?",
                                                        QMessageBox.Yes | QMessageBox.No)


                    if confirmation == QMessageBox.Yes:
                        # Call the linkUpdater function
                        print(f"project_id {project_id}")
                        link = os.path.join(os.path.dirname(target_folder), folder_name)
                        Link_updater().update_link(project_id, link)

                    else:
                        print("Operation canceled by the user.")
            
                    # Display success message using modern dialog box
                    heading = LanguageManager.translate_static(TranslationKeys.SUCCESS) or "Success"
                    text = (f"Kausta '{source_folder}'\n(k.a kaustas sisalduvad alamkaustad ja failid) dubleerimine õnnestus.")
                    text_2 = f"Sihtkohta on genereeritud kaust nimetusega \n'{folder_name}'."
                    QMessageBox.information(None, heading, f"{text}\n\n{text_2}")
                    
            except Exception as e:
                heading = LanguageManager.translate_static(TranslationKeys.WARNING) or "Warning"
                text = f"An error occurred: {e}"
                QMessageBox.warning(None, heading, text)
                        
        else:
            print("Operation canceled by the user.")


class Link_updater:
    def update_link(self, project_id, link):
            
        module = Module.PROJECT
        from ...python.GraphQLQueryLoader import GraphQLQueryLoader
        file =  UPDATE_project_properties
        query = GraphQLQueryLoader.load_query_by_module(module, file)
        
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
        value = SettingsDataSaveAndLoad.load_projects_prefered_folder_name_structure(self)
        print(f"Value: {value}")

        # Split the value into individual components
        components = value.split(" + ")

        # Initialize an empty list to hold the parts of the folder name
        folder_name_parts = []

        # Iterate through each component and construct the folder name parts
        for component in components:
            # Check if the component contains a symbol in parentheses
            if "(" in component and ")" in component:
                # Extract the symbol from the parentheses
                symbol = component.split("(")[-1].split(")")[0]
                # Remove the symbol part from the component
                component = component.replace(f"({symbol})", "")
            else:
                # If no symbol is specified, set it to an empty string
                symbol = ""

            # Check the component type and add the corresponding part to the folder name
            if component == "Projekti number":
                folder_name_parts.append(project_number)
            elif component == "Sümbol":
                folder_name_parts.append(symbol)
            elif component == "Projekti nimetus":
                folder_name_parts.append(project_name)

        # Construct the final folder name by joining the parts
        folder_name = "".join(folder_name_parts)

        # Print the constructed folder name
        heading = LanguageManager.translate_static(TranslationKeys.SUCCESS) or "Success"
        text = f"Folder name preview: {folder_name}"
        QMessageBox.information(None, heading, text)
        #print("Folder name:", folder_name)


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