# pylint: disable=missing-class-docstring
# pylint: disable=relative-beyond-top-level
# pylint: disable=no-name-in-module


from PyQt5.QtCore import QCoreApplication
from datetime import datetime
from ...queries.python.FileLoaderHelper import GraphqlEasements, GraphQLQueryLoader
from ...queries.python.query_tools import requestBuilder
from ...KeelelisedMuutujad.modules import Module
from ...KeelelisedMuutujad.messages import Headings, HoiatusTexts
from ...utils.TableUtilys.MainModuleTaibleBiulder import ModuleTableBuilder
from ...utils.DataExtractors.DataModelHelpers import DataModelBuilder
from ...utils.ProgressHelper import ProgressDialogModern

class Constants:
    package_size = 25
    sleep_duration = 2 #time for sleep
    total_fetched = 0
    items_for_page_minimum = 1
    items_for_page_medium = 25
    items_for_page_large = 50
    sleepPackage = items_for_page_medium
    

header_id = 'ID'
header_number = 'Number'
header_name = 'Nimetus'
header_deadline = 'Tähtaeg'
header_color = 'Color'
header_creator = 'Looja'
header_property_number = 'Kataster'
header_properties_icon ='propertiesIcon'
header_parent_id = 'Parent_id'
header_webLinkButton = 'web_link_button'
header_Documents = 'Dokumendid'
header_file_path = "file_path_button"
header_statuses = 'Staatus'

class EasementssMain:
    @staticmethod
    def load_main_easements_by_type_and_status (self, table, types, statuses, language="et"):

        #Adding progress
        progress = ProgressDialogModern(title="Katastri laadimine", value=0)
        progress.update(1, purpouse="Servituutide laadimine", text1="Palun oota...")

        model = queryHandling._model_for_easments_by_types_and_statuses(self, types, statuses, language)
        progress.update(value=50)
        #print(model)        
        if model is not None:
            module = Module.EASEMENT
            ModuleTableBuilder.setup(table, model, module, language)
            progress.update(value=98)
        else:            
            text = HoiatusTexts().ostingu_tulemused_puuduvad
            heading = Headings().warningSimple
            print(f"{heading}, {text}")
        progress.close()

    def load_easemenets_by_number(search_values, table, language="et", module=None ):
        #Adding progress
        progress = ProgressDialogModern(title="Katastri laadimine", value=0)
        progress.update(1, purpouse="Servituutide laadimine", text1="Palun oota...")

        model = queryHandling._model_for_easments_search_results(search_values, language)
        progress.update(value=50)
        
        if model is not None:
            module = Module.EASEMENT
            ModuleTableBuilder.setup(table, model, module, language)
            progress.update(value=98)
        
        else:            
            text = HoiatusTexts().ostingu_tulemused_puuduvad
            heading = Headings().warningSimple
            print(f"{heading}, {text}")
        progress.close()
        
    def load_easements_details(id):
        module = Module.EASEMENT
        query_name =  GraphqlEasements.EASEMENT_DETAILS
        query = GraphQLQueryLoader.load_query_by_module(module, query_name)
        variables = {
            "id": id
        }
        response = requestBuilder.construct_and_send_request(query, variables)

        if response.status_code == 200:
            
            table_rows = EasementsQueries.extract_Easements_details(response.json())
            return table_rows
        else:
            #print(f"Error: {response.status_code}")
            return None

    

class queryHandling:
    def __init__(self):
        self.header_id = header_id
        self.header_number = header_number
        self.header_name = header_name
        self.header_deadline = header_deadline
        self.header_color = header_color
        self.header_creator = header_creator
        self.header_property_number = header_property_number
        self.header_properties_icon = header_properties_icon
        self.header_parent_id = header_parent_id
        self.header_webLinkButton = header_webLinkButton
        self.header_Documents = header_Documents
        self.header_file_path = header_file_path
        self.header_statuses = header_statuses
        
    @staticmethod
    def _model_for_easments_by_types_and_statuses(self, types, statuses, language):

        data = EasementsQueries.query_easements_by_type_and_status_elements(self, types, statuses)
        model = DataModelBuilder.build_model_from_records(data, language)
        return model  


    def _model_for_easments_search_results(search_values, language):
       
        data = EasementsQueries.query_easements_by_number(None,search_values)
        model = DataModelBuilder.build_model_from_records(data, language)
        return model
    

class EasementsQueries:    
    def query_easements_by_type_and_status_elements(self, type_values, statuses):
        #print(f"type_values: '{type_values}'")
        #print(statuses)
        # Load the project query using the loader instance

        module = Module.EASEMENT

        query_name = GraphqlEasements.STATUS
        query = GraphQLQueryLoader.load_query_by_module(module, query_name)  

        # Set the desired total number of items to fetch
        desired_total_items = None  # Adjust this to your desired value
        items_for_page = 50  # Adjust this to your desired value
        #items_for_properties_page = 50
        end_cursor = None  # Initialize end_cursor before the loop
        total_fetched = 0        # Initialize an empty list to store fetched items        
        fetched_items = []
    
        while (desired_total_items is None or total_fetched < desired_total_items):
            variables = {
                "first": items_for_page,
                "after": end_cursor if end_cursor else None,
                "search": None,
                "where": {
                "AND": [
                    {
                    "column": "TYPE",
                    "operator": "IN",
                    "value": type_values
                    },
                    {
                    "column": "STATUS",
                    "operator": "IN",
                    "value": statuses
                    }
                ]
                },
                "orderBy": [
                {
                    "column": "NAME",
                    "order": "ASC"
                }
                ],
                "trashed": "WITHOUT"
                }

            response = requestBuilder.construct_and_send_request(query, variables)

            if response.status_code == 200:
                data = response.json()
                #print("data")
                #print(data)
                fetched_data = data.get("data", {}).get("easements", {}).get("edges", [])
                pageInfo = data.get("data", {}).get("easements", {}).get("pageInfo", {})
                end_cursor = pageInfo.get("endCursor")
                hasNextPage = pageInfo.get("hasNextPage")
                fetched_items.extend(fetched_data)
                total_fetched += len(fetched_data)

                # Check whether the last page of projects has been reached
                if not end_cursor or (desired_total_items is not None and total_fetched >= desired_total_items or not hasNextPage):
                    break

            else:
                #print(f"Error: {response.status_code}")
                return None

            QCoreApplication.processEvents()

        # Return only the desired number of items
        return fetched_items[:desired_total_items]
    
    @staticmethod
    def query_easements_by_number(self, easement_number):
        #print(statuses)
        # Load the project query using the loader instance

        module = Module.EASEMENT

        query_name = GraphqlEasements.STATUS
        query = GraphQLQueryLoader.load_query_by_module(module, query_name)  

        # Set the desired total number of items to fetch
        desired_total_items = None  # Adjust this to your desired value
        items_for_page = 50  # Adjust this to your desired value
        #items_for_properties_page = 50
        end_cursor = None  # Initialize end_cursor before the loop
        total_fetched = 0        # Initialize an empty list to store fetched items
        fetched_items = []

        
        while (desired_total_items is None or total_fetched < desired_total_items):
            variables = {
                "first": items_for_page,
                "after": end_cursor if end_cursor else None,
                "where": {
                    "AND": [
                        {"column": "NUMBER", "operator": "IN", "value": [easement_number]}
                    ]
                }
            }

            response = requestBuilder.construct_and_send_request(query, variables)

            if response.status_code == 200:
                data = response.json()
                #print("data")
                #print(data)
                fetched_data = data.get("data", {}).get("easements", {}).get("edges", [])
                pageInfo = data.get("data", {}).get("easements", {}).get("pageInfo", {})
                #print(f"propesties_end_cursor: '{properties_end_cursor}'")
                end_cursor = pageInfo.get("endCursor")
                hasNextPage = pageInfo.get("hasNextPage")
                fetched_items.extend(fetched_data)
                total_fetched += len(fetched_data)

                # Check whether the last page of projects has been reached
                if not end_cursor or (desired_total_items is not None and total_fetched >= desired_total_items or not hasNextPage):
                    break

            else:
                #print(f"Error: {response.status_code}")
                return None

            QCoreApplication.processEvents()

        # Return only the desired number of items
        return fetched_items[:desired_total_items]

    @staticmethod
    def extract_Easements_details(node: dict) -> str:
        label_color = "#BBB"
        value_color = "#EEE"

        label_width = "25%"
        value_width = "30%"

        c = node.get("data", {}).get("easement", {})

        def safe(key: str) -> str:
            return c.get(key) or ""

        # Status + color label
        status_data = c.get("status", {})
        status_name = status_data.get("name", "")
        status_color = status_data.get("color", "#CCC")
        status_display = f'<span style="background-color:#{status_color}; padding:2px 6px; border-radius:4px;">{status_name}</span>' if status_name else ""

        # Type
        type_name = c.get("type", {}).get("name", "")

        # Notarized
        notarized = "Jah" if c.get("isNotarized") else "Ei"

        # Dates
        def fmt_date(date_str: str) -> str:
            try:
                return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d.%m.%Y")
            except Exception:
                return ""

        effective_date = fmt_date(c.get("effectiveAt", ""))
        due_date = ""
        raw_due = c.get("dueAt")
        if raw_due:
            try:
                due_dt = datetime.strptime(raw_due, "%Y-%m-%d")
                days_remaining = (due_dt - datetime.today()).days
                due_date = f"{due_dt.strftime('%d.%m.%Y')} ({days_remaining} päeva)"
            except Exception:
                due_date = ""

        # File link (optional fallback if empty)
        files_link = c.get("filesPath", "")
        file_html = f'<a href="{files_link}" style="color:{value_color}; text-decoration:underline;">Ava dokumendid</a>' if files_link else ""

        table_rows = f"""
        <tr>
            <td width="{label_width}"><font color="{label_color}"><b>📁 Easement nr:</b></font></td>
            <td width="{value_width}"><font color="{value_color}"><b>{safe("number")}</b></font></td>
        </tr>
        <tr>
            <td width="{label_width}"><font color="{label_color}"><b>🔤 Nimetus:</b></font></td>
            <td width="80%" colspan="3"><font color="{value_color}"><b>{safe("name")}</b></font></td>        
        <tr>
            <td width="{label_width}"><font color="{label_color}"><b>📂 Tüüp:</b></font></td>
            <td width="{value_width}"><font color="{value_color}"><b>{type_name}</b></font></td>
        </tr>
        <tr>
            <td width="{label_width}"><font color="{label_color}"><b>✍️ Notariaalne:</b></font></td>
            <td width="{value_width}"><font color="{value_color}"><b>{notarized}</b></font></td>
            <td width="{label_width}"><font color="{label_color}"><b>📄 Notari nr:</b></font></td>
            <td width="{value_width}"><font color="{value_color}"><b>{safe("notarialNumber")}</b></font></td>
        </tr>
        <tr>
            <td width="{label_width}"><font color="{label_color}"><b>🟢 Kehtib alates:</b></font></td>
            <td width="{value_width}"><font color="{value_color}"><b>{effective_date}</b></font></td>
            <td width="{label_width}"><font color="{label_color}"><b>📆 Tähtaeg:</b></font></td>
            <td width="{value_width}"><font color="{value_color}"><b>{due_date}</b></font></td>
        </tr>
        """
        return table_rows

