import os
from ...KeelelisedMuutujad.modules import Module


class GraphQLQueryLoader:
    CURRENT_DIR = os.path.abspath(__file__)
    PLUGIN_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..', '..'))
    PROPERTIES_CONNECTIONFOLDER = 'queries/graphql/properties/Connected_data'

    @staticmethod
    def load_query_by_module(module: Module, filename: str) -> str:

        folders = {
            Module.PROPERTIE: QueryFolders.PROPERTIES_FOLDER,
            Module.USER: QueryFolders.USER_FOLDER,
            Module.EASEMENT: QueryFolders.EASEMENTS_FOLDER,
            Module.PROJECT: QueryFolders.PROJECTS_FOLDER,
            Module.CONTRACT: QueryFolders.CONTRACTS_FOLDER,
            Module.TAGS: QueryFolders.TAGS_FOLDER,
            Module.STATUSES: QueryFolders.STATUS_FOLDERS,
            Module.TASK: QueryFolders.TASK_FOLDER,
            Module.ASBUILT: QueryFolders.TASK_FOLDER,
            Module.COORDINATION: QueryFolders.COORDINATIONS_FOLDER
        }

        folder = folders.get(module)
        if not folder:
            raise ValueError(f"Unknown module: {module}")

        graphql_path = os.path.join(GraphQLQueryLoader.PLUGIN_DIR, folder, filename)
        with open(graphql_path, 'r') as file:
            return file.read()


class QueryFolders:
    PROPERTIES_FOLDER = 'queries/graphql/properties'
    PROPERTIES_WHERE_FOLDER = 'queries/graphql/properties/WHERE'
    PROPERTIES_CONNECTIONS = 'queries/graphql/properties/Connected_data'
    USER_FOLDER = 'queries/graphql/user'
    EASEMENTS_FOLDER = 'queries/graphql/easements'
    PROJECTS_FOLDER = 'queries/graphql/projects'
    CONTRACTS_FOLDER = 'queries/graphql/contracts'
    TAGS_FOLDER = 'queries/graphql/tags'
    STATUS_FOLDERS = 'queries/graphql/statuses'
    TASK_FOLDER = 'queries/graphql/tasks'
    COORDINATIONS_FOLDER = 'queries/graphql/coordinations'

class GraphqlProjects:

    Q_Where_By_status_Projects = 'W_project_status.graphql'
    Q_where_Projects_related_properties = 'W_projects_id.graphql'
    UPDATE_project_properties = 'update_project_properties.graphql'
    Projects_tags = 'projects_tags.graphql'
    Q_Properties_related_projects = 'propertiesrelated_projects.graphql'
    PROJECT_DETAILS = "project_details.graphql"

class GraphqlProperties:
    PROPERTIES_TAGS = 'Tags.graphql'
    UPDATE_TAGS = 'UpdateTags.graphql'
    UPDAT_STREET_NAME = 'UpdateStreetName.graphql'
    UPDATE_DETAILS = 'Update_property.graphql'

    W_properties_number = 'id_number.graphql'
    W_properties_number_improwed = 'id_number.graphql'
    W_properties_Address_County = 'ADDRESS_County.graphql'
    W_properties_Address_State = 'ADDRESS_State.graphql'
    W_properties_Address_City = 'ADDRESS_City.graphql'
    W_properties_ID_CadastralNR = 'ADDRESS_ID_CadastralNR.graphql'
    ADD_Selected_properties = 'Add_property.graphql'
    ADD_properties_purpose = 'Add_purpose.graphql'
    UPDATE_project_properties = 'update_project_properties.graphql'
    CHECK_properties_Mylabl = 'Properties_ID_Cadastral.graphql'
    #delete
    D_ALL_properties = 'deleteProperty.graphql'


    def load_query_properties_connected_elements(self, query_file_name):
        path = GraphQLQueryLoader.PROPERTIES_CONNECTIONFOLDER
        graphql_path = os.path.join(GraphQLQueryLoader.PLUGIN_DIR, path, query_file_name)
        #print(f"graphql path: {graphql_path}")
        with open(graphql_path, 'r') as file:
            return file.read()

class GraphqlContracts:

    ALL_CONTRACTS = 'contracts.graphql'
    CONTRACTS_MINIMAL = 'contracts_minimal.graphql'
    RELATED_PROPERTIES = 'W_contract_id.graphql'
    BY_CADASTRAL = 'propertiesrelated_contracts.graphql'
    UPDATE_CONTRACT_PROPERTIES = 'update_contract_properties.graphql'
    CONTRACT_TYPES = 'contract_types.graphql'
    STATUS = 'contracts_type_status.graphql'
    CONTRACT_DETAILS = "contract_details.graphql"

class GraphqlEasements:
    EASEMENT_TYPES = 'easements_types.graphql'
    STATUS = 'easements_type_status.graphql'
    UPDATE_EASEMENTS_PROPERTIES = 'update_easements_properties.graphql'
    RELATED_PROPERTIES = 'W_easement_id.graphql'
    Q_All_EASEMENTS = 'easements.graphql'
    EASEMENT_DETAILS = "easement_details.graphql"


class GraphqlTags:
    CREATE_TAG = 'CreateTag.graphql'
    TAGS_BY_MODULE = 'TagsByModule.graphql'
    TAGS_ID_BY_MODULE_AND_NAME = 'IDByModuleAndName.graphql'

class GraphqlTasks:
    TYPES = 'task_types.graphql'
    AsBUILT = "AsBuiltTasks.graphql"
    UPDATE_TASK_PROPERTIES = "update_task_properties.graphql"
    RELATED_PROPERTIES = "tasks_related_properties.graphql"
    TaskById = "TaskById.graphql"
    updatedescription ="update_task_properties.graphql"
    TASK_DETAILS =  "task_details.graphql"
    TASK_DETAILS_2 =  "task_details copy.graphql"
    CREATE_TASK = "create_task.graphql"

class GraphqlCoordinations:
    COORDINATIONS = 'coordinations_type_status.graphql'
    UPDATE_PROPERTIES ="update_coordination_properties.graphql"
    RELATED_PROPERTIES = "coordination_related_properties.graphql"
    RELATED_NOTES = "coordination_details.graphql"

class GraphqlStatuses:
    STATUSES = 'statuses.graphql'

class GraphqlUser:
    Q_All_Users = 'users.graphql'
    Q_Where_user = 'users_where.graphql'
    Q_me = 'me.graphql'

class GraphqlSubmissions:
    SUBMISSION_DETAILS = "submission_details.graphql"

class GraphqlSpecifications:
    SPETCIFICATIONS_DETAILS = "specification_details.graphql" 
