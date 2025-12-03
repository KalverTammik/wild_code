from .translation_keys import TranslationKeys, RoleTranslationKeys, ToolbarTranslationKeys

TRANSLATIONS = {
    TranslationKeys.PROJECTS_MODULE_LOADED: "Projects module loaded!",
    TranslationKeys.API_ENDPOINT_NOT_CONFIGURED: "API endpoint not configured.",
    TranslationKeys.CONFIG_ERROR: "Configuration error: {error}",
    TranslationKeys.LOGIN_FAILED: "Login failed: {error}",
    TranslationKeys.NO_API_TOKEN_RECEIVED: "No API token received.",
    TranslationKeys.LOGIN_FAILED_RESPONSE: "Login failed: {error}",
    TranslationKeys.NETWORK_ERROR: "Network error: {error}",
    TranslationKeys.WILD_CODE_PLUGIN_TITLE: "Wild Code Plugin",
    TranslationKeys.USERNAME_LABEL: "Username:",
    TranslationKeys.PASSWORD_LABEL: "Password:",
    TranslationKeys.LOGIN_BUTTON: "Login",
    TranslationKeys.CANCEL_BUTTON: "Cancel",
    TranslationKeys.TOGGLE_PASSWORD: "Show Password",
    TranslationKeys.LANGUAGE_LABEL: "Language:",
    TranslationKeys.MAILABL_LISTENER: "Mailabl Listener",
    TranslationKeys.UNKNOWN_MODULE: "Unknown module: {module}",
    TranslationKeys.QUERY_FILE_NOT_FOUND: "Query file not found: {file}",
    TranslationKeys.SAVE_SETTING: "Save setting",
    TranslationKeys.USER: "User",
    TranslationKeys.ROLES: "Roles",
    TranslationKeys.MODULE_ACCESS: "Preferred module",
    TranslationKeys.CONFIRM: "Confirm",
    TranslationKeys.NAME: "Name",
    TranslationKeys.EMAIL: "Email",
    TranslationKeys.MODULE_SETTINGS_PLACEHOLDER: "Module settings placeholder",
    # Added: Welcome page and layer picker texts
    TranslationKeys.WELCOME: "Welcome",
    TranslationKeys.SELECT_MODULE: "Select a module from the left or open Settings to set your preferred module.",
    TranslationKeys.NO_PROJECT_LOADED_TITLE: "No Project Loaded",
    TranslationKeys.NO_PROJECT_LOADED_MESSAGE: "Please load a QGIS project before using this plugin.",
    TranslationKeys.OPEN_SETTINGS: "Open Settings",
    # Added: ModuleCard/layer picker labels
    TranslationKeys.MODULES_MAIN_LAYER: "Modules main layer",
    TranslationKeys.ARCHIVE_LAYER: "Archive layer",
    TranslationKeys.SELECT_LAYER: "Select layer",
    TranslationKeys.CHOOSE_LAYERS_USED_BY_THIS_MODULE: "Choose layers used by this module (element and archive).",
    TranslationKeys.CHOOSE_PROPERTY_LAYER_FOR_MODULE: "Select a property layer for data operations and management.",
    TranslationKeys.SELECT_A_PROPERTY_LAYER: "Select a property layer...",
    TranslationKeys.PROPERTY_TREE_HEADER: "Property-related data",
    TranslationKeys.PROPERTY_TREE_DEFAULT_MESSAGE: "Select a property on the map",
    TranslationKeys.PROPERTY_TREE_LOADING: "Loading related data...",
    TranslationKeys.PROPERTY_TREE_NO_CONNECTIONS: "No connections found",
    TranslationKeys.PROPERTY_TREE_NO_DATA: "No data available",
    TranslationKeys.PROPERTY_TREE_MODULE_EMPTY: "No records",
    TranslationKeys.PROPERTY_TREE_ROW_NO_TITLE: "Name missing",
    TranslationKeys.PROPERTY_TREE_ROW_UPDATED_PREFIX: "Updated {date}",
    TranslationKeys.LOGOUT_BUTTON_TOOLTIP: "Log out from your account",
    TranslationKeys.SEARCH_TOOLTIP: "This feature is not yet available",
    TranslationKeys.SEARCH_PLACEHOLDER: "Search...",
    TranslationKeys.SEARCH_NO_RESULTS: "No results found for '{term}'",
    TranslationKeys.SIDEBAR_COLLAPSE_TOOLTIP: "Collapse Sidebar",
    TranslationKeys.SIDEBAR_EXPAND_TOOLTIP: "Expand Sidebar",
    TranslationKeys.THEME_SWITCH_TOOLTIP: "Switch between dark and light theme",
    TranslationKeys.DEV_DBG_TOOLTIP: "Toggle developer logs (print) on/off",
    TranslationKeys.DEV_FRAMES_TOOLTIP: "Show/Hide FRAME labels on the home page",
    TranslationKeys.SESSION_EXPIRED: "Your session has expired. Please sign in again.",
    TranslationKeys.SESSION_EXPIRED_TITLE: "Session Expired",
    TranslationKeys.URGENT_GROUP_TITLE: "Urgent!"
    ,TranslationKeys.URGENT_TOOLTIP: "What needs fast attention"
    ,TranslationKeys.STATUS_FILTER: "Filter by Status"
    ,TranslationKeys.TAGS_FILTER: "Filter by Tags"
    ,TranslationKeys.TYPE_FILTER: "Filter by Type"
    ,TranslationKeys.TYPE_GROUP_FILTER: "Filter by Type Group"
    ,TranslationKeys.RESET: "Reset"
    ,TranslationKeys.CONFIRM: "Confirm"
    ,TranslationKeys.RESET_ALL_SETTINGS: "Reset all settings for this module to default values"
    ,TranslationKeys.SETTINGS_RESET_TO_DEFAULTS: "Settings reset to defaults"
    ,TranslationKeys.SHOW_PROJECT_NUMBERS_DESCRIPTION: "When enabled, item numbers will be displayed in cards for easy identification."
    ,TranslationKeys.USER_PROFILE: "User Profile"
    ,TranslationKeys.ROLES_PERMISSIONS: "Roles & Permissions"
    ,TranslationKeys.MODULE_ACCESS: "Module Access"
    ,TranslationKeys.ADMINISTRATOR: "Administrator"
    ,TranslationKeys.EDITOR: "Editor"
    ,TranslationKeys.VIEWER: "Viewer"
    ,TranslationKeys.DASHBOARD: "Dashboard"
    ,TranslationKeys.REPORTS: "Reports"
    ,"settings": "Settings"
    ,"Admin": "Admin"
    ,"User": "User"
    ,"User Information": "User Information"
    ,"Roles": "Roles"
    ,"Preferred module": "Preferred module"
    ,"A Tähe õppimine": "Learning the Letter A"
    ,"B Tähe õppimine": "Learning the Letter B"
    ,"C Tähe õppimine": "Learning the Letter C"
    ,"A täht on eesti tähestiku esimene täht. See on täht, millega algab paljude sõnade ja nimede kirjutamine. Õppides A tähte, teed esimese sammu lugemise ja kirjutamise oskuse poole.": "The letter A is the first letter of the Estonian alphabet. It is the letter with which many words and names begin. By learning the letter A, you take the first step towards reading and writing skills."
    ,"B täht on eesti tähestikus teine täht. Seda kasutatakse paljudes sõnades, näiteks 'banaan' ja 'buss'. B tähe õppimine aitab laiendada sõnavara ja parandada hääldust.": "The letter B is the second letter in the Estonian alphabet. It is used in many words, such as 'banaan' (banana) and 'buss' (bus). Learning the letter B helps expand vocabulary and improve pronunciation."
    ,"C täht esineb eesti keeles peamiselt võõrsõnades, näiteks 'cirkus' või 'cello'. C tähe tundmine aitab mõista ja lugeda rahvusvahelisi sõnu.": "The letter C appears in Estonian mainly in foreign words, such as 'cirkus' (circus) or 'cello'. Knowing the letter C helps understand and read international words."
    ,"Property Management": "Property Management"
    ,"Quick Actions": "Quick Actions"
    ,"Add Shp file": "Add SHP file"
    ,"Add property": "Add property"
    ,"Remove property": "Remove property"
    ,"Load Shapefile": "Load Shapefile"
    ,"Select Shapefile": "Select Shapefile"
    ,"Shapefile loaded successfully": "Shapefile loaded successfully"
    ,"Shapefile loaded message": "Shapefile '{name}' has been successfully loaded in the 'New Properties' group"
    ,"Shapefile loaded with data message": "Shapefile '{name}' has been successfully loaded in the 'New Properties' group ({count} features imported)"
    ,"Invalid Shapefile": "Invalid Shapefile"
    ,"Invalid Shapefile message": "The selected Shapefile is not valid."
    ,"Shapefile load failed": "Shapefile load failed"
    ,"Shapefile load failed message": "Failed to load the Shapefile."
    ,"Shapefile loading error": "Shapefile loading error"
    ,"Importing Shapefile": "Importing Shapefile"
    ,"Processing features": "Processing features"
    ,"Features copied": "Features copied"
    ,"Import complete": "Import complete"
    ,"features imported": "features imported"
    ,"feature imported": "feature imported"
    ,"Initializing...": "Initializing..."
    ,"Cancel": "Cancel"

    ,"Add New Property": "Add New Property"
    ,"Select a property template to add:": "Select a property template to add:"
    ,"Residential Property": "Residential Property"
    ,"Commercial Property": "Commercial Property"
    ,"Industrial Property": "Industrial Property"
    ,"Agricultural Land": "Agricultural Land"
    ,"Vacant Land": "Vacant Land"
    ,"Standard residential property template": "Standard residential property template"
    ,"Commercial building template": "Commercial building template"
    ,"Industrial facility template": "Industrial facility template"
    ,"Agricultural land template": "Agricultural land template"
    ,"Empty land parcel template": "Empty land parcel template"
    ,"Add New Property": "Add New Property"
    ,"Property Details": "Property Details"
    ,"Additional Information": "Additional Information"
    ,"Property Name:": "Property Name:"
    ,"Property Type:": "Property Type:"
    ,"Area (m²):": "Area (m²):"
    ,"Value (€):": "Value (€):"
    ,"Residential": "Residential"
    ,"Commercial": "Commercial"
    ,"Industrial": "Industrial"
    ,"Agricultural": "Agricultural"
    ,"Other": "Other"
    ,"Enter property name": "Enter property name"
    ,"Enter area in m²": "Enter area in m²"
    ,"Enter property value": "Enter property value"
    ,"Enter property address": "Enter property address"
    ,"Enter additional notes or description": "Enter additional notes or description"
    ,"Add Property": "Add Property"
    ,"Property name is required.": "Property name is required."
    ,"Area must be greater than 0.": "Area must be greater than 0."
    ,"Value must be greater than 0.": "Value must be greater than 0."
    ,"Validation Error": "Validation Error"
    ,"Cadastral ID": "Cadastral ID"
    ,"Address": "Address"
    ,"Area (m²)": "Area (m²)"
    ,"Settlement": "Settlement"
    ,"Property Name": "Property Name"
    ,"Property Type": "Property Type"
    ,"Value (€)": "Value (€)"
    ,"Add Property": "Add Property"
    ,"Cancel": "Cancel"
    ,"Save": "Save"
    ,"Delete": "Delete"
    ,"Edit": "Edit"
    ,"Select": "Select"
    ,"Search": "Search"
    ,"Confirm": "Confirm"
    ,TranslationKeys.YES: "Yes"
    ,TranslationKeys.NO: "No"
    ,TranslationKeys.OK: "OK"
    ,TranslationKeys.LOADING: "Loading"
    ,TranslationKeys.SAVING: "Saving"
    ,TranslationKeys.DELETING: "Deleting"
    ,TranslationKeys.SUCCESS: "Success"
    ,TranslationKeys.ERROR: "Error"
    ,"Warning": "Warning"
    ,"This field is required": "This field is required"
    ,"Invalid value": "Invalid value"
    ,"Value must be greater than {min}": "Value must be greater than {min}"
    ,"Value must be less than {max}": "Value must be less than {max}"
    ,TranslationKeys.PROPERTIES: "Properties"
    ,TranslationKeys.CONTRACTS: "Contracts"
    ,TranslationKeys.PROJECTS: "Projects"
    ,TranslationKeys.LETTERS: "Letters"
    ,TranslationKeys.SPECIFICATIONS: "Specifications"
    ,TranslationKeys.EASEMENTS: "Easements"
    ,TranslationKeys.COORDINATIONS: "Coordinations"
    ,TranslationKeys.TASKS: "Tasks"
    ,TranslationKeys.SUBMISSIONS: "Submissions"
    ,TranslationKeys.ORDINANCES: "Ordinances"
    ,TranslationKeys.MODULE_PROPERTY: "Properties"
    ,TranslationKeys.MODULE_CONTRACT: "Contracts"
    ,TranslationKeys.MODULE_PROJECT: "Projects"
    ,TranslationKeys.MODULE_HOME: "Home"
    ,TranslationKeys.MODULE_COORDINATION: "Coordination"
    ,TranslationKeys.MODULE_LETTER: "Letters"
    ,TranslationKeys.MODULE_SPECIFICATION: "Specifications"
    ,TranslationKeys.MODULE_EASEMENT: "Easements"
    ,TranslationKeys.MODULE_ORDINANCE: "Ordinances"
    ,TranslationKeys.MODULE_SUBMISSION: "Submissions"
    ,TranslationKeys.MODULE_TASK: "Tasks"
    ,TranslationKeys.MODULE_ASBUILT: "As-built"
    ,TranslationKeys.MODULE_WORKS: "Works"
    ,TranslationKeys.MODULE_TAGS: "Tags"
    ,TranslationKeys.MODULE_STATUSES: "Statuses"
    ,TranslationKeys.ADD_NEW_PROPERTY: "Property Management"
    ,TranslationKeys.SELECT_PROPERTIES: "Select Properties"
    ,TranslationKeys.CLOSE: "Close"
    ,TranslationKeys.SELECT_ALL: "Select All"
    ,TranslationKeys.CLEAR_SELECTION: "Clear Selection"
    ,TranslationKeys.ADD_SELECTED: "Add Selected"
    ,TranslationKeys.SELECT_COUNTY: "Select County"
    ,TranslationKeys.SELECT_MUNICIPALITY: "Select Municipality"
    ,TranslationKeys.FILTER_BY_LOCATION: "Filter by Location"
    ,TranslationKeys.SELECTED_PROPERTIES_COUNT: "Selected: 0 properties"
    ,TranslationKeys.SELECTED_COUNT_TEMPLATE: "Selected: {count} properties"
    ,TranslationKeys.NO_SELECTION: "No Selection"
    ,TranslationKeys.PLEASE_SELECT_AT_LEAST_ONE_PROPERTY: "Please select at least one property."
    ,TranslationKeys.NO_PROPERTY_LAYER_SELECTED: "No property layer selected. Please select a property layer first."
    ,TranslationKeys.DATA_LOADING_ERROR: "Data Loading Error"
    ,TranslationKeys.FAILED_TO_LOAD_PROPERTY_DATA: "Failed to load property data from layer."
    ,TranslationKeys.PROPERTIES_ADDED: "Properties Added"
    ,TranslationKeys.SELECTED_PROPERTIES_ADDED: "Selected properties have been added."
    ,TranslationKeys.CHOOSE_FROM_MAP: "Choose from map"
    ,TranslationKeys.NO_SELECTION: "No Selection"
    ,TranslationKeys.SELECT_PROPERTY_FIRST: "Please select a property feature on the map first."
    ,TranslationKeys.ERROR: "Error"
    ,TranslationKeys.ERROR_SELECTING_PROPERTY: "Error selecting property"
    ,TranslationKeys.SELECT_SINGLE_PROPERTY_TITLE: "Select Single Property"
    ,TranslationKeys.SELECT_SINGLE_PROPERTY_MESSAGE: "Please select only one property feature on the map."
    ,ToolbarTranslationKeys.OPEN_FOLDER: "Open folder"
    ,ToolbarTranslationKeys.OPEN_ITEM_IN_BROWSER: "Open item in browser"
    ,ToolbarTranslationKeys.SHOW_ITEMS_ON_MAP: "Show items on map"
    ,RoleTranslationKeys.ADMINS: "Admins"
    ,RoleTranslationKeys.ADMINISTRATORS: "Administrators"
    ,RoleTranslationKeys.PROJECT_MANAGERS: "Project Managers"
    ,RoleTranslationKeys.USERS: "Users"
    ,RoleTranslationKeys.MANAGERS: "Managers"
    ,RoleTranslationKeys.EDITORS: "Editors"
    ,RoleTranslationKeys.VIEWERS: "Viewers"
    ,RoleTranslationKeys.GUESTS: "Guests"
    ,TranslationKeys.START: "Start"
    ,TranslationKeys.CREATED: "Created"
    ,TranslationKeys.UPDATED: "Updated"
    ,"Signaltest": "Test Lab"
}
