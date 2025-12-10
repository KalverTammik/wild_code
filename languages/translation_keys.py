
class TranslationKeys:
    """Centralized translation keys to avoid duplication and maintain consistency"""

    # Module loading and API
    PROJECTS_MODULE_LOADED = "Projects module loaded"
    API_ENDPOINT_NOT_CONFIGURED = "API endpoint not configured"
    CONFIG_ERROR = "Configuration error: {error}"
    LOGIN_FAILED = "Login failed: {error}"
    NO_API_TOKEN_RECEIVED = "No API token received"
    LOGIN_FAILED_RESPONSE = "Login failed: {error}"
    NETWORK_ERROR = "Network error: {error}"

    # Login dialog
    LOGIN_TITLE = "Login"
    LANGUAGE_LABEL = "Language:"
    USERNAME_LABEL = "Username:"
    PASSWORD_LABEL = "Password:"
    LOGIN_BUTTON = "login_button"
    CANCEL_BUTTON = "cancel_button"
    TOGGLE_PASSWORD = "Show Password"

    # Plugin UI
    WILD_CODE_PLUGIN_TITLE = "wild_code_plugin_title"
    HOME_PAGE = "home_page"
    SETTINGS_PAGE = "settings_page"
    ABOUT_PAGE = "about_page"
    MAILABL_LISTENER = "mailabl_listener"
    SWITCH_TO_DARK_MODE = "switch_to_dark_mode"
    SWITCH_TO_LIGHT_MODE = "switch_to_light_mode"
    UNKNOWN_MODULE = "unknown_module: {module}"
    QUERY_FILE_NOT_FOUND = "query_file_not_found: {file}"
    SAVE_SETTING = "save_setting"
    CONFIRM = "confirm"
    MODULE_SETTINGS_PLACEHOLDER = "Module settings placeholder"
    SELECT_MODULE = "Select a module from the left or open Settings to set your preferred module."
    NO_PROJECT_LOADED_TITLE = "No Project Loaded"
    NO_PROJECT_LOADED_MESSAGE = "Please load a QGIS project before using this plugin."

    # Module labels (match Module enum values)
    MODULE_HOME = "home"
    MODULE_PROPERTY = "property"
    MODULE_CONTRACT = "contract"
    MODULE_PROJECT = "project"
    MODULE_SETTINGS = "settings"
    MODULE_COORDINATION = "coordination"
    MODULE_LETTER = "letter"
    MODULE_SPECIFICATION = "specification"
    MODULE_EASEMENT = "easement"
    MODULE_ORDINANCE = "ordinance"
    MODULE_SUBMISSION = "submission"
    MODULE_TASK = "task"
    MODULE_ASBUILT = "asbuilt"
    MODULE_WORKS = "works"
    MODULE_TAGS = "tags"
    MODULE_STATUSES = "statuses"



    PROPERTIES = "Properties"
    CONTRACTS = "Contracts"
    PROJECTS = "Projects"
    LETTERS = "Letters"
    SPECIFICATIONS = "Specifications"
    EASEMENTS = "Easements"
    COORDINATIONS = "Coordinations"
    TASKS = "Tasks"
    SUBMISSIONS = "Submissions"
    ORDINANCES = "Ordinances"




    PROPERTY_TREE_HEADER = "Property-related data"
    PROPERTY_TREE_DEFAULT_MESSAGE = "Select a property on the map"
    PROPERTY_TREE_LOADING = "Loading related data..."
    PROPERTY_TREE_NO_CONNECTIONS = "No connections found"
    PROPERTY_TREE_NO_DATA = "No data available"
    PROPERTY_TREE_MODULE_EMPTY = "No records"
    PROPERTY_TREE_ROW_NO_TITLE = "Name missing"
    PROPERTY_TREE_ROW_UPDATED_PREFIX = "Updated {date}"
    
    # UI tooltips
    LOGOUT_BUTTON_TOOLTIP = "logout_button_tooltip"
    SEARCH_TOOLTIP = "search_tooltip"
    SEARCH_PLACEHOLDER = "search_placeholder"
    SEARCH_NO_RESULTS = "No results found for '{term}'"
    SIDEBAR_COLLAPSE_TOOLTIP = "sidebar_collapse_tooltip"
    SIDEBAR_EXPAND_TOOLTIP = "sidebar_expand_tooltip"
    THEME_SWITCH_TOOLTIP = "theme_switch_tooltip"
    DEV_DBG_TOOLTIP = "dev_dbg_tooltip"
    DEV_FRAMES_TOOLTIP = "dev_frames_tooltip"
    SESSION_EXPIRED = "session_expired"
    SESSION_EXPIRED_TITLE = "session_expired_title"
    URGENT_GROUP_TITLE = "urgent_group_title"
    URGENT_TOOLTIP = "urgent_tooltip"

    # Filters
    STATUS_FILTER = "Status Filter"
    TAGS_FILTER = "Tags Filter"
    TYPE_FILTER = "Type Filter"
    TYPE_GROUP_FILTER = "Type Group Filter"
    RESET = "Reset"



    # Settings
    STATUS_PREFERENCES = "Status Preferences"
    TAGS_PREFERENCES = "Tags Preferences"
    TYPE_PREFERENCES = "Type Preferences"
    SELECT_TYPE_DESCRIPTION = "Types description"
    SELECT_STATUSES_DESCRIPTION = "Statuses description"
    SELECT_TAGS_DESCRIPTION = "Tags description"
    RESET_ALL_SETTINGS = "Reset all settings for this module to default values"
    SETTINGS_RESET_TO_DEFAULTS = "Settings reset to defaults"
    SHOW_PROJECT_NUMBERS_DESCRIPTION = "When enabled, project/contract numbers will be displayed in item cards for easy identification."

    # User roles and permissions
    USER_PROFILE = "User Profile"
    ROLES_PERMISSIONS = "Roles & Permissions"
    MODULE_ACCESS = "Module Access"
    ADMINISTRATOR = "Administrator"
    EDITOR = "Editor"
    VIEWER = "Viewer"
    DASHBOARD = "Dashboard"
    REPORTS = "Reports"
    ADMIN = "Admin"
    USER = "User"
    USER_INFORMATION = "User Information"
    ROLES = "Roles"
    PREFERRED_MODULE = "Preferred module"

    # Learning content
    LEARNING_A_TITLE = "A Tähe õppimine"
    LEARNING_B_TITLE = "B Tähe õppimine"
    LEARNING_C_TITLE = "C Tähe õppimine"
    LEARNING_A_DESCRIPTION = "A täht on eesti tähestiku esimene täht. See on täht, millega algab paljude sõnade ja nimede kirjutamine. Õppides A tähte, teed esimese sammu lugemise ja kirjutamise oskuse poole."
    LEARNING_B_DESCRIPTION = "B täht on eesti tähestikus teine täht. Seda kasutatakse paljudes sõnades, näiteks 'banaan' ja 'buss'. B tähe õppimine aitab laiendada sõnavara ja parandada hääldust."
    LEARNING_C_DESCRIPTION = "C täht esineb eesti keeles peamiselt võõrsõnades, näiteks 'cirkus' või 'cello'. C tähe tundmine aitab mõista ja lugeda rahvusvahelisi sõnu."

    # Property management
    PROPERTY_MANAGEMENT = "Property Management"
    QUICK_ACTIONS = "Quick Actions"
    ADD_SHP_FILE = "Add Shp file"
    ADD_PROPERTY = "Add property"
    REMOVE_PROPERTY = "Remove property"
    LOAD_SHAPEFILE = "Load Shapefile"
    SELECT_SHAPEFILE = "Select Shapefile"
    SHAPEFILE_LOADED_SUCCESSFULLY = "Shapefile loaded successfully"
    SHAPEFILE_LOADED_MESSAGE = "Shapefile loaded message"
    SHAPEFILE_LOADED_WITH_DATA_MESSAGE = "Shapefile loaded with data message"
    INVALID_SHAPEFILE = "Invalid Shapefile"
    INVALID_SHAPEFILE_MESSAGE = "Invalid Shapefile message"
    SHAPEFILE_LOAD_FAILED = "Shapefile load failed"
    SHAPEFILE_LOAD_FAILED_MESSAGE = "Shapefile load failed message"
    SHAPEFILE_LOADING_ERROR = "Shapefile loading error"
    IMPORTING_SHAPEFILE = "Importing Shapefile"
    PROCESSING_FEATURES = "Processing features"
    FEATURES_COPIED = "Features copied"
    IMPORT_COMPLETE = "Import complete"
    FEATURES_IMPORTED = "features imported"
    FEATURE_IMPORTED = "feature imported"
    INITIALIZING = "Initializing..."
    CANCEL = "Cancel"

    ADD_NEW_PROPERTY = "Add New Property"
    SELECT_PROPERTY_TEMPLATE = "Select a property template to add:"
    RESIDENTIAL_PROPERTY = "Residential Property"
    COMMERCIAL_PROPERTY = "Commercial Property"
    INDUSTRIAL_PROPERTY = "Industrial Property"
    AGRICULTURAL_LAND = "Agricultural Land"
    VACANT_LAND = "Vacant Land"
    STANDARD_RESIDENTIAL_TEMPLATE = "Standard residential property template"
    COMMERCIAL_BUILDING_TEMPLATE = "Commercial building template"
    INDUSTRIAL_FACILITY_TEMPLATE = "Industrial facility template"
    AGRICULTURAL_LAND_TEMPLATE = "Agricultural land template"
    EMPTY_LAND_PARCEL_TEMPLATE = "Empty land parcel template"
    PROPERTY_DETAILS = "Property Details"
    ADDITIONAL_INFORMATION = "Additional Information"
    PROPERTY_NAME_LABEL = "Property Name:"
    PROPERTY_TYPE_LABEL = "Property Type:"
    AREA_LABEL = "Area (m²):"
    VALUE_LABEL = "Value (€):"
    RESIDENTIAL = "Residential"
    COMMERCIAL = "Commercial"
    INDUSTRIAL = "Industrial"
    AGRICULTURAL = "Agricultural"
    OTHER = "Other"
    ENTER_PROPERTY_NAME = "Enter property name"
    ENTER_AREA = "Enter area in m²"
    ENTER_PROPERTY_VALUE = "Enter property value"
    ENTER_PROPERTY_ADDRESS = "Enter property address"
    ENTER_ADDITIONAL_NOTES = "Enter additional notes or description"
    ADD_PROPERTY_BUTTON = "Add Property"
    PROPERTY_NAME_REQUIRED = "Property name is required."
    AREA_MUST_BE_GREATER_THAN_ZERO = "Area must be greater than 0."
    VALUE_MUST_BE_GREATER_THAN_ZERO = "Value must be greater than 0."
    VALIDATION_ERROR = "Validation Error"
    CADASTRAL_ID = "Cadastral ID"
    ADDRESS = "Address"
    AREA = "Area (m²)"
    SETTLEMENT = "Settlement"
    PROPERTY_NAME = "Property Name"
    PROPERTY_TYPE = "Property Type"
    VALUE = "Value (€)"
    SAVE = "Save"
    DELETE = "Delete"
    EDIT = "Edit"
    SELECT = "Select"
    SEARCH = "Search"
    SEARCHING = "Searching"
    FIELD_REQUIRED = "This field is required"
    INVALID_VALUE = "Invalid value"
    VALUE_MUST_BE_GREATER_THAN_MIN = "Value must be greater than {min}"
    VALUE_MUST_BE_LESS_THAN_MAX = "Value must be less than {max}"
    NAME = "Name"
    EMAIL = "Email"

    # Welcome and layer setup
    WELCOME = "Welcome"
    SELECT_A_MODULE_FROM_THE_LEFT = "Select a module from the left or open Settings to set your preferred module."
    OPEN_SETTINGS = "Open Settings"
    MODULES_MAIN_LAYER = "Modules main layer"
    ARCHIVE_LAYER = "Archive layer"
    SELECT_LAYER = "Select layer"
    MAIN_LAYER_DESCRIPTION = "Main layer description"
    ARCHIVE_LAYER_DESCRIPTION = "Archive layer description"
    CHOOSE_LAYERS_USED_BY_THIS_MODULE = "Choose layers used by this module (element and archive)."
    CHOOSE_PROPERTY_LAYER_FOR_MODULE = "Select a property layer for data operations and management."

    # Status preferences (extended copy)
    SELECT_STATUSES_YOU_WANT_TO_PRIORITIZE = "Select statuses you want to prioritize for this module. These will be highlighted in the interface."
    SELECT_A_PROPERTY_LAYER = "Select a property layer..."

    # Project numbers

    WHEN_ENABLED_PROJECT_CONTRACT_NUMBERS = "When enabled, project/contract numbers will be displayed in item cards for easy identification."

    # Learning content (seems like test content)
    A_TAHE_OPPIMINE = "A tähe õppimine"
    B_TAHE_OPPIMINE = "B tähe õppimine"
    C_TAHE_OPPIMINE = "C tähe õppimine"
    A_TAHT_ON_EESTI_TAHESTIKU_ESIMENE_TAHT = "A täht on eesti tähestiku esimene täht. See on täht, millega algab paljude sõnade ja nimede kirjutamine. Õppides A tähte, teed esimese sammu lugemise ja kirjutamise oskuse poole."
    B_TAHT_ON_EESTI_TAHESTIKUS_TEINE_TAHT = "B täht on eesti tähestikus teine täht. Seda kasutatakse paljudes sõnades, näiteks 'banaan' ja 'buss'. B tähe õppimine aitab laiendada sõnavara ja parandada hääldust."
    C_TAHT_ESINEB_EESTI_KEELes = "C täht esineb eesti keeles peamiselt võõrsõnades, näiteks 'cirkus' või 'cello'. C tähe tundmine aitab mõista ja lugeda rahvusvahelisi sõnu."

    # Property dialog extensions
    SELECT_PROPERTIES = "Select Properties"
    SELECT_A_PROPERTY_TEMPLATE_TO_ADD = "Select a property template to add:"
    STANDARD_RESIDENTIAL_PROPERTY_TEMPLATE = "Standard residential property template"
    SELECT_ALL = "Select All"
    CLEAR_SELECTION = "Clear Selection"
    ADD_SELECTED = "Add Selected"
    CLOSE = "Close"

    # Property selection filters
    SELECT_COUNTY = "Select County"
    SELECT_MUNICIPALITY = "Select Municipality"
    SELECT_SETTLEMENTS = "Select Settlements"
    FILTER_BY_LOCATION = "Filter by Location"

    # Property state messaging
    SELECTED_PROPERTIES_COUNT = "Selected: 0 properties"
    SELECTED_COUNT_TEMPLATE = "Selected: {count} properties"
    SELECTED_PROPERTIES_ADDED = "Selected properties have been added."
    PROPERTIES_ADDED = "Properties Added"
    NO_SELECTION = "No Selection"
    SELECT_PROPERTY_FIRST = "Please select a property feature on the map first."
    SELECT_SINGLE_PROPERTY_TITLE = "Select Single Property"
    SELECT_SINGLE_PROPERTY_MESSAGE = "Please select only one property feature on the map."
    CHOOSE_FROM_MAP = "Choose from map"

    # Property form helpers
    ENTER_AREA_IN_M2 = "Enter area in m²"
    PROPERTY_NAME_IS_REQUIRED = "Property name is required."
    AREA_MUST_BE_GREATER_THAN_0 = "Area must be greater than 0."
    VALUE_MUST_BE_GREATER_THAN_0 = "Value must be greater than 0."
    VALUE_TOO_SMALL = "Value must be greater than {min}"
    VALUE_TOO_LARGE = "Value must be less than {max}"
    REQUIRED_FIELD = "This field is required"
    PLEASE_SELECT_AT_LEAST_ONE_PROPERTY = "Please select at least one property."

    # Status messages
    LOADING = "Loading"
    SAVING = "Saving"
    DELETING = "Deleting"
    SUCCESS = "Success"
    WARNING = "Warning"

    # Common actions
    YES = "Yes"
    NO = "No"
    OK = "OK"

    # Error messaging
    ERROR = "Error"
    ERROR_SELECTING_PROPERTY = "Error selecting property"
    NO_PROPERTY_LAYER_SELECTED = "No property layer selected. Please select a property layer first."
    DATA_LOADING_ERROR = "Data Loading Error"
    FAILED_TO_LOAD_PROPERTY_DATA = "Failed to load property data from layer."

    # Geography fields
    COUNTY = "County"
    MUNICIPALITY = "Municipality"

    # Parameters
    CONNECTIONS = "Connections"

    # Date labels
    DUE = "DueAt"
    START = "Start"
    CREATED = "Created"
    UPDATED = "Updated"


class DialogLabels:

    LOGIN_TITLE = "Login"
    SETTINGS_TITLE = "Settings"
    LOGIN_SECTION = "User Authentication"
    SETTINGS_SECTION = "Application Preferences"

    # Login dialog labels
    LANGUAGE_LABEL = "Language:"
    USERNAME_LABEL = "Username:"
    PASSWORD_LABEL = "Password:"
    LOGIN_BUTTON = "Login"
    SESSION_ACTIVE_ERROR = "A session is already active. Please log out first."
    SESSION_EXPIRED_ERROR = "Session expired. Please log in again."
    INVALID_CREDENTIALS_ERROR = "Invalid email or password."

    #Setting dialog labels
    PROJECTS_SOURCE_FOLDER = "Projects source folder"
    PROJECTS_TARGET_FOLDER = "Projects target folder"
    PROJECTS_PHOTO_FOLDER = "Projects photo folder"
    PROJECTS_PREFERED_FOLDER_NAME_STRUCTURE = "name structure"
    PROJECTS_PREFERED_FOLDER_NAME_STRUCTURE_ENABLED = "name structure enabled"
    PROJECTS_PREFERED_FOLDER_NAME_STRUCTURE_RULE = "name structure rule"

class RoleTranslationKeys:
    ADMINS = "Admins"
    ADMINISTRATORS = "Administraatorid"
    PROJECT_MANAGERS = "Projektijuhid"
    USERS = "Kasutajad"
    MANAGERS = "Juhid"
    EDITORS = "Toimetajad"
    VIEWERS = "Vaatajad"
    GUESTS = "Külalised"

class ToolbarTranslationKeys:
    OPEN_FOLDER = "Open Folder"
    OPEN_ITEM_IN_BROWSER = "Open Item in Browser"
    SHOW_ITEMS_ON_MAP = "Show Items on Map"
    MORE_ACTIONS = "More Actions"

class FolderNamingTranslationKeys:
    TR_FOLDER_NAMING_RULE = "Folder naming rule"
    TR_EMPTY = "Empty"
    TR_PROJECT_NUMBER = "Project Number"
    TR_PROJECT_NAME = "Project Name"
    TR_SYMBOL = "Symbol"
    TR_SYMBOL_TEXT = "Symbol text"
    TR_PREVIEW_PREFIX = "Preview: "
    TR_PREVIEW_EMPTY = "(empty)"
    TR_SYMBOL_REQUIRED = "Symbol text is required."
    TR_SELECT_AT_LEAST_ONE = "Select at least one slot."
    TR_INVALID_RULE = "Invalid rule"

class SettingDialogPlaceholders:
    UNSET = "Unset"
