from .translation_keys import (
    TranslationKeys,
    RoleTranslationKeys,
    ToolbarTranslationKeys,
    DialogLabels,
    ToolbarTranslationKeys,
    FolderNamingTranslationKeys,
    SettingDialogPlaceholders,
)

TRANSLATIONS = {
        # Added from translation audit (UI literals)
        TranslationKeys.FOLDER_NAMING_RULE_DIALOG_TITLE: "Folder Naming Rule",
        TranslationKeys.SETTINGS_BASE_CARD_TEXT: "Settings",
        TranslationKeys.SETTINGS_UTILS_DASH: "—",
        TranslationKeys.ADD_UPDATE_PROPERTY_DIALOG_CANCELLING: "Cancelling...",
        TranslationKeys.HEADER_WIDGET_ABI: "Abi",
        TranslationKeys.OVERDUE_DUE_SOON_PILLS_ELLIPSIS: "…",
        TranslationKeys.PROGRESS_DIALOG_MODERN_PERCENT: "0%",
        TranslationKeys.SEARCH_RESULTS_WIDGET_CLOSE_TOOLTIP: "Close search results",
        TranslationKeys.SIDEBAR_LEFT_ARROW: "«",
        TranslationKeys.SIDEBAR_RIGHT_ARROW: "»",
        TranslationKeys.DATA_DISPLAY_WIDGETS_EXTRAINFO_TOOLTIP: "Open detailed overview",
        TranslationKeys.DATA_DISPLAY_WIDGETS_INFOCARDHEADER_TOOLTIP: "Private",
        TranslationKeys.DATA_DISPLAY_WIDGETS_DATES_EMPTY: "No dates available",
        TranslationKeys.DATA_DISPLAY_WIDGETS_DETAIL_TITLE_SUFFIX: "Detailed overview",
        TranslationKeys.DATA_DISPLAY_WIDGETS_CLOSE: "Close",
        TranslationKeys.DATA_DISPLAY_WIDGETS_OVERVIEW_TITLE: "Activity overview",
        TranslationKeys.DATA_DISPLAY_WIDGETS_PROJECT_OVERVIEW_TITLE: "Project activity overview",
        TranslationKeys.DATA_DISPLAY_WIDGETS_CONTRACT_OVERVIEW_TITLE: "Contract activity overview",
        TranslationKeys.DATA_DISPLAY_WIDGETS_COLUMN_DONE: "Done",
        TranslationKeys.DATA_DISPLAY_WIDGETS_COLUMN_IN_PROGRESS: "In progress",
        TranslationKeys.DATA_DISPLAY_WIDGETS_COLUMN_TODO: "To do",
        TranslationKeys.DATA_DISPLAY_WIDGETS_COLUMN_SIGNED: "Signed",
        TranslationKeys.DATA_DISPLAY_WIDGETS_COLUMN_PROCESSING: "Processing",
        TranslationKeys.DATA_DISPLAY_WIDGETS_COLUMN_PENDING: "Pending",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_PLANNING: "Planning",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_COMPILATION: "Compilation",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_REVIEW: "Review",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_APPROVAL: "Approval",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_TESTING: "Testing",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_DOCUMENTING: "Documentation",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_OPTIMIZING: "Optimization",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_PUBLISHING: "Publishing",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_MONITORING: "Monitoring",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_ARCHIVING: "Archiving",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_REPORTING: "Reporting",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_CONTRACT_DRAFTING: "Contract drafting",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_PARTY_CONSENT: "Party consent",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_NOTARIAL_CONFIRM: "Notarial confirmation",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_LEGAL_REVIEW: "Legal review",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_FINANCIAL_CHECK: "Financial check",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_SIGNATURES: "Signatures",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_COMPLETION_CHECK: "Completion check",
        TranslationKeys.DATA_DISPLAY_WIDGETS_PROJECT_DETAIL_CONTENT: """
        <h3>Project Detailed Overview</h3>
        <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>

        <h4>Project Phases</h4>
        <ul>
        <li><b>Planning:</b> Defining the project goals and scope</li>
        <li><b>Compilation:</b> Building project components</li>
        <li><b>Testing:</b> Verifying functionality</li>
        <li><b>Publishing:</b> Final release of the project</li>
        </ul>

        <h4>Project Statistics</h4>
        <p>Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.</p>
        """,
        TranslationKeys.DATA_DISPLAY_WIDGETS_CONTRACT_DETAIL_CONTENT: """
        <h3>Contract Detailed Overview</h3>
        <p>Contract management and legal documentation overview.</p>

        <h4>Contract Phases</h4>
        <ul>
        <li><b>Signed:</b> Legal binding agreements</li>
        <li><b>Processing:</b> Under legal and financial review</li>
        <li><b>Pending:</b> Awaiting signatures or completion</li>
        </ul>
        """,
        TranslationKeys.HEADER_HELP_BUTTON_TOOLTIP: "Help",
        TranslationKeys.NO_PROJECTS_FOUND: "No projects found",
        TranslationKeys.NO_CONTRACTS_FOUND: "No contracts found",
        TranslationKeys.NO_COORDINATIONS_FOUND: "No coordinations found",
        TranslationKeys.NO_VALUES_FOUND: "No values found!",
        TranslationKeys.LOADING: "Loading…",
        TranslationKeys.CLEAR_VALUE: "Clear value",
        TranslationKeys.PROPERTY_ID_PLACEHOLDER: "Property ID",
        TranslationKeys.MISSING_PROPERTY_ID_TITLE: "Missing ID",
        TranslationKeys.MISSING_PROPERTY_ID_BODY: "Please enter a property id.",
        TranslationKeys.PROPERTY_LAYER_FIELD_NOT_FOUND: "Field '{field_name}' not found on the property layer.",
        TranslationKeys.ADD_UPDATE_PROGRESS_PREFIX: "Adding properties",
        TranslationKeys.ADD_UPDATE_PROGRESS_PREFIX_NO_CHECKS: "Adding (no checks)",
        TranslationKeys.ADD_UPDATE_PROGRESS_FINISHED: "Finished",
        TranslationKeys.ADD_UPDATE_PROGRESS_FINISHED_NO_CHECKS: "Finished (no checks)",
        TranslationKeys.ADD_UPDATE_PROGRESS_TEMPLATE: "{prefix} {done}/{total}",
        TranslationKeys.ADD_UPDATE_PROGRESS_CANCELLED_TEMPLATE: "{prefix} - cancelled at {done}/{total}",
        TranslationKeys.DELAY_HELPERS_LOADINGSPINNER_TITLE: "GradientSpinner + dots demo",
    TranslationKeys.PROJECTS_MODULE_LOADED: "Projects module loaded!",
    TranslationKeys.API_ENDPOINT_NOT_CONFIGURED: "API endpoint not configured.",
    TranslationKeys.CONFIG_ERROR: "Configuration error: {error}",
    TranslationKeys.LOGIN_FAILED: "Login failed: {error}",
    TranslationKeys.NO_API_TOKEN_RECEIVED: "No API token received.",
    TranslationKeys.LOGIN_FAILED_RESPONSE: "Login failed: {error}",
    TranslationKeys.NETWORK_ERROR: "Network error: {error}",
    TranslationKeys.KAVITRO_PLUGIN_TITLE: "Kavitro Plugin",
    TranslationKeys.USERNAME_LABEL: "Username:",
    TranslationKeys.PASSWORD_LABEL: "Password:",
    TranslationKeys.LOGIN_BUTTON: "Login",
    TranslationKeys.CANCEL_BUTTON: "Cancel",
    TranslationKeys.TOGGLE_PASSWORD: "Show Password",
    TranslationKeys.LANGUAGE_LABEL: "Language:",
    DialogLabels.LOGIN_SECTION: "User Authentication",
    DialogLabels.SETTINGS_SECTION: "Application Preferences",
    DialogLabels.SESSION_EXPIRED_ERROR: "Session expired. Please log in again.",
    DialogLabels.INVALID_CREDENTIALS_ERROR: "Invalid email or password.",
    TranslationKeys.MAILABL_LISTENER: "Mailabl Listener",
    TranslationKeys.UNKNOWN_MODULE: "Unknown module: {module}",
    TranslationKeys.QUERY_FILE_NOT_FOUND: "Query file not found: {file}",
    TranslationKeys.SAVE_SETTING: "Save setting",
    TranslationKeys.USER: "User",
    TranslationKeys.ROLES: "Roles",
    TranslationKeys.CONFIRM: "Confirm",
    TranslationKeys.NAME: "Name",
    TranslationKeys.EMAIL: "Email",
    TranslationKeys.MODULE_SETTINGS_PLACEHOLDER: "Module settings placeholder",
    TranslationKeys.PREFERRED_MODULE: "Preferred module",
    TranslationKeys.COUNTY: "County",
    TranslationKeys.MUNICIPALITY: "Municipality",
    TranslationKeys.DUE: "Due at",
    TranslationKeys.SEARCHING: "Searching",
    TranslationKeys.SELECT_SETTLEMENTS: "Select Settlements",
    TranslationKeys.HOME_PAGE: "Home page",
    TranslationKeys.SETTINGS_PAGE: "Settings page",
    TranslationKeys.ABOUT_PAGE: "About page",
    TranslationKeys.SWITCH_TO_DARK_MODE: "Switch to dark mode",
    TranslationKeys.SWITCH_TO_LIGHT_MODE: "Switch to light mode",
    # Added: Welcome page and layer picker texts
    TranslationKeys.WELCOME: "Welcome",
    TranslationKeys.SELECT_MODULE: "Select a module from the left or open Settings to set your preferred module.",
    TranslationKeys.NO_PROJECT_LOADED_TITLE: "No Project Loaded",
    TranslationKeys.NO_PROJECT_LOADED_MESSAGE: "Please load a QGIS project before using this plugin.",
    TranslationKeys.PROJECT_FOLDER_MISSING_TITLE: "Project folder setup required",
    TranslationKeys.PROJECT_FOLDER_MISSING_MESSAGE: "Project folders are not set for this module. Opening Settings...",
    TranslationKeys.HOW_SELECT_PROPERTIES: "How do you want to select properties?",
    TranslationKeys.PROPERTY_ARCHIVED_BACKEND_MATCH_TITLE: "Archived backend match",
    TranslationKeys.PROPERTY_ARCHIVED_BACKEND_MATCH_BODY: "Backend has an archived property for cadastral number {tunnus}.\n\nWhat do you want to do?",
    TranslationKeys.PROPERTY_UNARCHIVE_FAILED_TITLE: "Unarchive failed",
    TranslationKeys.PROPERTY_UNARCHIVE_FAILED_BODY: "Failed to unarchive backend property {backend_id} for {tunnus}.",
    TranslationKeys.PROPERTY_BACKEND_UPDATE_FAILED_TITLE: "Backend update failed",
    TranslationKeys.PROPERTY_BACKEND_UPDATE_FAILED_BODY: "Unarchived backend property but failed to update data for {tunnus}.",
    TranslationKeys.PROPERTY_BACKEND_MISSING_TITLE: "Backend missing",
    TranslationKeys.PROPERTY_BACKEND_MISSING_BODY: "Property {tunnus} exists in main layer but is missing from backend.\n\nCreate backend record from import data?",
    TranslationKeys.PROPERTY_BACKEND_MISSING_ARCHIVED_BODY: "Property {tunnus} exists in main layer. Backend has only an archived record for this cadastral number.\n\nCreate a new ACTIVE backend record from import data?",
    TranslationKeys.PROPERTY_BACKEND_EXISTS_MISSING_MAP_TITLE: "Property exists",
    TranslationKeys.PROPERTY_BACKEND_EXISTS_MISSING_MAP_BODY: "Property {tunnus} exists in backend but is missing from main layer.\n\nCopy feature from import layer to main layer?",
    TranslationKeys.PROPERTY_NEWER_IMPORT_TITLE: "Newer import detected",
    TranslationKeys.PROPERTY_NEWER_IMPORT_BODY: "Property {tunnus} exists in backend and main layer, but import appears newer.\n\nArchive/replace existing property?\n- Moves existing main-layer feature to archive layer\n- Marks backend property as archived\n- Replaces main-layer feature with import feature",
    TranslationKeys.PROPERTY_REPLACE_FAILED_TITLE: "Replace failed",
    TranslationKeys.PROPERTY_REPLACE_FAILED_BODY_NO_FEATURE: "Could not locate existing main-layer feature for {tunnus} to archive/replace.",
    TranslationKeys.PROPERTY_REPLACE_FAILED_BODY_DELETE: "Failed to delete existing main-layer feature for {tunnus}.",
    TranslationKeys.PROPERTY_REPLACE_FAILED_BODY_COPY: "Copy import->main failed for {tunnus}: {message}",
    TranslationKeys.PROPERTY_ARCHIVE_LAYER_MISSING_TITLE: "Archive layer missing",
    TranslationKeys.PROPERTY_ARCHIVE_LAYER_MISSING_BODY: "Archive layer is not configured or missing; cannot archive/replace.",
    TranslationKeys.PROPERTY_MAIN_LAYER_MISSING_TITLE: "Main layer missing",
    TranslationKeys.PROPERTY_MAIN_LAYER_MISSING_BODY: "Main property layer is not found/invalid. Please configure it in Settings.",
    TranslationKeys.PROPERTY_ARCHIVE_LAYER_REQUIRED_TITLE: "Archive layer required",
    TranslationKeys.PROPERTY_ARCHIVE_LAYER_REQUIRED_BODY_NO_NAME: "Archive layer is not configured for Properties.\n\nChoose what to do:\n- Open Settings to pick an archive layer\n- Create/load an archive layer inside the same GPKG as MAIN",
    TranslationKeys.PROPERTY_ARCHIVE_LAYER_REQUIRED_BODY_NAME: "Archive layer '{name}' is not found/invalid in the project.\n\nChoose what to do:\n- Open Settings to pick an archive layer\n- Create/load an archive layer inside the same GPKG as MAIN",
    TranslationKeys.PROPERTY_OPEN_SETTINGS_FAILED_TITLE: "Open Settings failed",
    TranslationKeys.PROPERTY_OPEN_SETTINGS_FAILED_BODY: "Could not open Settings module automatically.\n\nError: {error}",
    TranslationKeys.PROPERTY_CANNOT_CREATE_ARCHIVE_TITLE: "Cannot create archive layer",
    TranslationKeys.PROPERTY_CANNOT_CREATE_ARCHIVE_BODY: "Auto-creating an archive layer is only supported when MAIN is a GeoPackage (.gpkg) layer.\n\nPlease configure the archive layer in Settings.",
    TranslationKeys.PROPERTY_INVALID_ARCHIVE_NAME_TITLE: "Invalid name",
    TranslationKeys.PROPERTY_INVALID_ARCHIVE_NAME_BODY: "Archive layer name cannot be empty.",
    TranslationKeys.PROPERTY_ARCHIVE_LAYER_CREATE_FAILED_TITLE: "Archive layer creation failed",
    TranslationKeys.PROPERTY_ARCHIVE_LAYER_CREATE_FAILED_BODY: "Failed to create/load archive layer '{name}'.\n\nError: {error}",
    TranslationKeys.PROPERTY_ARCHIVE_LAYER_CREATE_FAILED_BODY_GENERIC: "Failed to create/load archive layer '{name}'.",
    TranslationKeys.PROPERTY_ARCHIVE_LAYER_NAME_PROMPT_TITLE: "Create/Load archive layer",
    TranslationKeys.PROPERTY_ARCHIVE_LAYER_NAME_PROMPT_LABEL: "Archive layer name:",
    TranslationKeys.RUN_ATTENTION_CHECKS: "Run checks",
    TranslationKeys.YES_TO_ALL: "Yes to all",
    TranslationKeys.ADD_WITHOUT_CHECKS: "Add without checks",
    TranslationKeys.OPEN_SETTINGS: "Open Settings",
    # Added: ModuleCard/layer picker labels
    TranslationKeys.MAIN_PROPERTY_LAYER: "Properties main layer",
    TranslationKeys.ARCHIVE_LAYER: "Archive layer",
    TranslationKeys.SELECT_LAYER: "Select layer",
    TranslationKeys.PROPERTY_LAYER_OVERVIEW: "This is your properties primary layer. Choose the layer containing the core data you work with.",
    TranslationKeys.ARCHIVE_LAYER_DESCRIPTION: "Use an optional archive layer to store historical or backup data versions.",
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
    ,TranslationKeys.FILTERS_REFRESH: "Refresh filters"
    ,TranslationKeys.FILTERS_CLEAR: "Clear filter selections"
    ,TranslationKeys.RESET_ALL_SETTINGS: "Reset all settings for this module to default values"
    ,TranslationKeys.SETTINGS_RESET_TO_DEFAULTS: "Settings reset to defaults"
    ,TranslationKeys.SHOW_PROJECT_NUMBERS_DESCRIPTION: "When enabled, item numbers will be displayed in cards for easy identification."
    ,TranslationKeys.USER_PROFILE: "User Profile"
    ,TranslationKeys.ROLES_PERMISSIONS: "Roles & Permissions"
    ,TranslationKeys.MODULE_ACCESS: "Module Access"
    ,TranslationKeys.ADMINISTRATOR: "Administrator"
    ,TranslationKeys.EDITOR: "Editor"
    ,TranslationKeys.VIEWER: "Viewer"
    ,TranslationKeys.OPEN_MAA_AMET_PAGE: "Open Maa-amet page"
    ,TranslationKeys.DASHBOARD: "Dashboard"
    ,TranslationKeys.REPORTS: "Reports"
    ,TranslationKeys.ADMIN: "Admin"
    ,TranslationKeys.USER_INFORMATION: "User Information"
    ,TranslationKeys.PROPERTY_MANAGEMENT: "Property Management"
    ,TranslationKeys.QUICK_ACTIONS: "Quick Actions"
    ,TranslationKeys.ADD_SHP_FILE: "Add SHP file"
    ,TranslationKeys.ADD_PROPERTY: "Add property"
    ,TranslationKeys.REMOVE_PROPERTY: "Remove property"
    ,TranslationKeys.LOAD_SHAPEFILE: "Load Shapefile"
    ,TranslationKeys.SELECT_SHAPEFILE: "Select Shapefile"
    ,TranslationKeys.SHAPEFILE_LOADED_SUCCESSFULLY: "Shapefile loaded successfully"
    ,TranslationKeys.SHAPEFILE_LOADED_MESSAGE: "Shapefile '{name}' has been successfully loaded in the 'New Properties' group"
    ,TranslationKeys.SHAPEFILE_LOADED_WITH_DATA_MESSAGE: "Shapefile '{name}' has been successfully loaded in the 'New Properties' group ({count} features imported)"
    ,TranslationKeys.INVALID_SHAPEFILE: "Invalid Shapefile"
    ,TranslationKeys.INVALID_SHAPEFILE_MESSAGE: "The selected Shapefile is not valid."
    ,TranslationKeys.SHAPEFILE_LOAD_FAILED: "Shapefile load failed"
    ,TranslationKeys.SHAPEFILE_LOAD_FAILED_MESSAGE: "Failed to load the Shapefile."
    ,TranslationKeys.SHAPEFILE_LOADING_ERROR: "Shapefile loading error"
    ,TranslationKeys.IMPORTING_SHAPEFILE: "Importing Shapefile"
    ,TranslationKeys.PROCESSING_FEATURES: "Processing features"
    ,TranslationKeys.FEATURES_COPIED: "Features copied"
    ,TranslationKeys.IMPORT_COMPLETE: "Import complete"
    ,TranslationKeys.FEATURES_IMPORTED: "features imported"
    ,TranslationKeys.FEATURE_IMPORTED: "feature imported"
    ,TranslationKeys.INITIALIZING: "Initializing..."
    ,TranslationKeys.SELECT_PROPERTY_TEMPLATE: "Select a property template to add:"
    ,TranslationKeys.RESIDENTIAL_PROPERTY: "Residential Property"
    ,TranslationKeys.COMMERCIAL_PROPERTY: "Commercial Property"
    ,TranslationKeys.INDUSTRIAL_PROPERTY: "Industrial Property"
    ,TranslationKeys.AGRICULTURAL_LAND: "Agricultural Land"
    ,TranslationKeys.VACANT_LAND: "Vacant Land"
    ,TranslationKeys.STANDARD_RESIDENTIAL_TEMPLATE: "Standard residential property template"
    ,TranslationKeys.COMMERCIAL_BUILDING_TEMPLATE: "Commercial building template"
    ,TranslationKeys.INDUSTRIAL_FACILITY_TEMPLATE: "Industrial facility template"
    ,TranslationKeys.AGRICULTURAL_LAND_TEMPLATE: "Agricultural land template"
    ,TranslationKeys.EMPTY_LAND_PARCEL_TEMPLATE: "Empty land parcel template"
    ,TranslationKeys.PROPERTY_DETAILS: "Property Details"
    ,TranslationKeys.ADDITIONAL_INFORMATION: "Additional Information"
    ,TranslationKeys.PROPERTY_NAME_LABEL: "Property Name:"
    ,TranslationKeys.PROPERTY_TYPE_LABEL: "Property Type:"
    ,TranslationKeys.AREA_M2: "Area (m²):"
    ,TranslationKeys.VALUE_LABEL: "Value (€):"
    ,TranslationKeys.RESIDENTIAL: "Residential"
    ,TranslationKeys.COMMERCIAL: "Commercial"
    ,TranslationKeys.INDUSTRIAL: "Industrial"
    ,TranslationKeys.AGRICULTURAL: "Agricultural"
    ,TranslationKeys.OTHER: "Other"
    ,TranslationKeys.ENTER_PROPERTY_NAME: "Enter property name"
    ,TranslationKeys.ENTER_AREA: "Enter area in m²"
    ,TranslationKeys.ENTER_PROPERTY_VALUE: "Enter property value"
    ,TranslationKeys.ENTER_PROPERTY_ADDRESS: "Enter property address"
    ,TranslationKeys.ENTER_ADDITIONAL_NOTES_OR_DESCRIPTION: "Enter additional notes or description"
    ,TranslationKeys.ADD_PROPERTY_BUTTON: "Add Property"
    ,TranslationKeys.PROPERTY_NAME_REQUIRED: "Property name is required."
    ,TranslationKeys.AREA_MUST_BE_GREATER_THAN_ZERO: "Area must be greater than 0."
    ,TranslationKeys.VALUE_MUST_BE_GREATER_THAN_ZERO: "Value must be greater than 0."
    ,TranslationKeys.VALIDATION_ERROR: "Validation Error"
    ,TranslationKeys.CADASTRAL_ID: "Cadastral ID"
    ,TranslationKeys.ADDRESS: "Address"
    ,TranslationKeys.AREA: "Area (m²)"
    ,TranslationKeys.SETTLEMENT: "Settlement"
    ,TranslationKeys.PROPERTY_NAME: "Property Name"
    ,TranslationKeys.PROPERTY_TYPE: "Property Type"
    ,TranslationKeys.VALUE: "Value (€)"
    ,TranslationKeys.SAVE: "Save"
    ,TranslationKeys.DELETE: "Delete"
    ,TranslationKeys.EDIT: "Edit"
    ,TranslationKeys.SELECT: "Select"
    ,TranslationKeys.SEARCH: "Search"
    ,TranslationKeys.WARNING: "Warning"
    ,TranslationKeys.THIS_FIELD_IS_REQUIRED: "This field is required"
    ,TranslationKeys.INVALID_VALUE: "Invalid value"
    ,TranslationKeys.VALUE_MUST_BE_GREATER_THAN_MIN: "Value must be greater than {min}"
    ,TranslationKeys.VALUE_MUST_BE_LESS_THAN_MAX: "Value must be less than {max}"
    ,TranslationKeys.YES: "Yes"
    ,TranslationKeys.NO: "No"
    ,TranslationKeys.OK: "OK"
    ,TranslationKeys.SAVING: "Saving"
    ,TranslationKeys.DELETING: "Deleting"
    ,TranslationKeys.SUCCESS: "Success"
    ,TranslationKeys.ERROR: "Error"
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
    ,TranslationKeys.SELECT_PROPERTIES: "Select Properties"
    ,TranslationKeys.CLOSE: "Close"
    ,TranslationKeys.SELECT_ALL: "Select All"
    ,TranslationKeys.CLEAR_SELECTION: "Clear Selection"
    ,TranslationKeys.ADD_SELECTED: "Add Selected"
    ,TranslationKeys.DELETE_BY_ID: "Delete by ID"
    ,TranslationKeys.SELECT_FROM_MAP: "Select from map"
    ,TranslationKeys.SELECT_BY_LOCATION_LIST: "Select by location (list)"
    ,TranslationKeys.RESELECT_FROM_MAP: "Reselect from map"
    ,TranslationKeys.ARCHIVE: "Archive"
    ,TranslationKeys.UNARCHIVE: "Unarchive"
    ,TranslationKeys.UNARCHIVE_EXISTING: "Unarchive existing"
    ,TranslationKeys.CREATE_NEW: "Create new"
    ,TranslationKeys.SKIP: "Skip"
    ,TranslationKeys.CREATE_LOAD_IN_GPKG: "Create/Load in GPKG…"
    ,TranslationKeys.SELECT_COUNTY: "Select County"
    ,TranslationKeys.SELECT_MUNICIPALITY: "Select Municipality"
    ,TranslationKeys.ATTENTION: "Attention"
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
    ,TranslationKeys.CONNECT_PROPERTIES: "connect Prperties"
    ,TranslationKeys.CHOSE_FROM_MAP: "Chose from map"
    ,TranslationKeys.SELECT_PROPERTY_FIRST: "Please select a property feature on the map first."
    ,TranslationKeys.ERROR_SELECTING_PROPERTY: "Error selecting property"
    ,TranslationKeys.SELECT_SINGLE_PROPERTY_TITLE: "Select Single Property"
    ,TranslationKeys.SELECT_SINGLE_PROPERTY_MESSAGE: "Please select only one property feature on the map."
        ,TranslationKeys.MAP_SELECTION_NONE: "No properties were selected from the map."
        ,TranslationKeys.MAP_SELECTION_START_FAILED: "Could not start map selection for properties."
        ,TranslationKeys.LINK_PROPERTIES_SUCCESS: "Linked properties saved for project {pid}.\nTotal linked: {count}. {preview}{extra}"
        ,TranslationKeys.LINK_PROPERTIES_MISSING_NOTE: "Missing/not found: {missing}"
        ,TranslationKeys.LINK_PROPERTIES_ERROR: "Could not link properties for project {pid}.\nPending selection ({count}): {preview}\n\nDetails: {err}"
        ,TranslationKeys.MORE_COUNT_SUFFIX: " … (+{count} more)"
        ,TranslationKeys.LINK_REVIEW_CONNECTIONS_TITLE: "Connections"
        ,TranslationKeys.LINK_REVIEW_ALREADY_LINKED: "Already linked"
        ,TranslationKeys.LINK_REVIEW_NEW_SELECTIONS: "New selections"
        ,TranslationKeys.LINK_REVIEW_RESELECT: "Reselect"
    ,ToolbarTranslationKeys.OPEN_FOLDER: "Open folder"
    ,ToolbarTranslationKeys.OPEN_ITEM_IN_BROWSER: "Open item in browser"
    ,ToolbarTranslationKeys.SHOW_ITEMS_ON_MAP: "Show items on map"
    ,ToolbarTranslationKeys.GENERATE_PROJECT_FOLDER: "Generate project folder"
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
    ,TranslationKeys.CONNECTIONS: "Connections"
    ,TranslationKeys.TAGS_PREFERENCES: "Tags preferences"
    ,TranslationKeys.STATUS_PREFERENCES: "Status preferences"
    ,TranslationKeys.TYPE_PREFERENCES: "Type preferences"
    ,TranslationKeys.SELECT_TYPE_DESCRIPTION: "Select types you want to focus on for this module. These will be highlighted in the interface."
    ,TranslationKeys.SELECT_STATUSES_DESCRIPTION: "Select statuses you want to prioritize for this module. These will be highlighted in the interface."
    ,TranslationKeys.SELECT_TAGS_DESCRIPTION: "Select tags you want to focus on for this module. These will be highlighted in the interface."
    ,DialogLabels.PROJECTS_SOURCE_FOLDER: "Projects source folder"
    ,DialogLabels.PROJECTS_TARGET_FOLDER: "Projects target folder"
    ,DialogLabels.PROJECTS_PHOTO_FOLDER: "Projects photo folder"
    ,DialogLabels.PROJECTS_PREFERED_FOLDER_NAME_STRUCTURE: "Prefered folder name structure"
    ,DialogLabels.PROJECTS_PREFERED_FOLDER_NAME_STRUCTURE_ENABLED: "Enable prefered folder name structure"
    ,DialogLabels.PROJECTS_PREFERED_FOLDER_NAME_STRUCTURE_RULE: "Prefered folder name structure rule"
    ,ToolbarTranslationKeys.MORE_ACTIONS: "More actions"
    ,SettingDialogPlaceholders.UNSET: "Unset"
    ,FolderNamingTranslationKeys.TR_EMPTY: "Empty"
    ,FolderNamingTranslationKeys.TR_PROJECT_NUMBER: "Project Number"
    ,FolderNamingTranslationKeys.TR_PROJECT_NAME: "Project Name"
    ,FolderNamingTranslationKeys.TR_SYMBOL: "Symbol"
    ,FolderNamingTranslationKeys.TR_SYMBOL_TEXT: "Symbol text"
    ,FolderNamingTranslationKeys.TR_PREVIEW_PREFIX: "Preview: "
    ,FolderNamingTranslationKeys.TR_PREVIEW_EMPTY: "(empty)"
    ,FolderNamingTranslationKeys.TR_SYMBOL_REQUIRED: "Symbol text is required."
    ,FolderNamingTranslationKeys.TR_SELECT_AT_LEAST_ONE: "Select at least one slot."
    ,FolderNamingTranslationKeys.TR_INVALID_RULE: "Invalid rule"
    ,TranslationKeys.SIGNALTEST: "SignalTest"
    ,TranslationKeys.TEST_LAB: "Test Lab"
    ,TranslationKeys.SIGNALTEST_DESC: "Load a SHP into a temporary memory layer and compare its fields against the expected property schema."
    ,TranslationKeys.SIGNALTEST_STEP_LOAD: "Load SHP into memory"
    ,TranslationKeys.SIGNALTEST_STEP_REVIEW: "Review the table of logical vs layer fields"
    ,TranslationKeys.SIGNALTEST_STEP_MAP: "If required/optional are missing/unmapped, click 'Open mapper' and align"
    ,TranslationKeys.SIGNALTEST_LOAD_BTN: "Load SHP into memory"
    ,TranslationKeys.SIGNALTEST_MAPPER_BTN: "Open mapper"
    ,TranslationKeys.SIGNALTEST_PANEL_SCHEMA: "Schema vs SHP"
    ,TranslationKeys.SIGNALTEST_PANEL_MAIN: "Main layer vs SHP"
    ,TranslationKeys.SIGNALTEST_PANEL_ARCHIVE: "Archive layer vs SHP"
    ,TranslationKeys.SIGNALTEST_LEGEND_MAPPED: "Mapped"
    ,TranslationKeys.SIGNALTEST_LEGEND_MISSING_REQUIRED: "Missing (required)"
    ,TranslationKeys.SIGNALTEST_LEGEND_UNMAPPED_OPTIONAL: "Unmapped (optional)"
    ,TranslationKeys.SIGNALTEST_LEGEND_EXTRA: "Extra fields"
    ,TranslationKeys.SIGNALTEST_SUMMARY_TEMPLATE: "Required missing: {missing_required} | Optional unmapped: {missing_optional} | Extras: {extras}"
    ,TranslationKeys.SIGNALTEST_MAIN_SUMMARY_TEMPLATE: "Missing in main vs SHP: {missing} | Fields only in main: {extras}"
    ,TranslationKeys.SIGNALTEST_ARCHIVE_SUMMARY_TEMPLATE: "Missing in archive vs SHP: {missing} | Fields only in archive: {extras}"
    ,TranslationKeys.SIGNALTEST_ARCHIVE_NOT_FOUND: "Archive layer not found"
    ,TranslationKeys.SIGNALTEST_TABLE_HEADER_LOGICAL: "Standard fields"
    ,TranslationKeys.SIGNALTEST_TABLE_HEADER_LAYER: "Fields in file"
    ,TranslationKeys.SIGNALTEST_TABLE_HEADER_STATUS: "Result"
    ,TranslationKeys.SIGNALTEST_TABLE_HEADER_NOTE: "Notes"
    ,TranslationKeys.SIGNALTEST_FILE_DIALOG_TITLE: "Select SHP"
    ,TranslationKeys.SIGNALTEST_FILE_DIALOG_FILTER: "Shapefiles (*.shp)"
    ,TranslationKeys.SIGNALTEST_MSG_NO_LAYER_TITLE: "No layer"
    ,TranslationKeys.SIGNALTEST_MSG_NO_LAYER_BODY: "Load a SHP first."
    ,TranslationKeys.SIGNALTEST_MSG_LOAD_FAIL: "Could not load SHP layer."
    ,TranslationKeys.SIGNALTEST_MSG_COPY_FAIL: "Failed to copy SHP to memory layer."
    ,TranslationKeys.SIGNALTEST_MSG_COMPARISON_TITLE: "Field comparison"
    ,TranslationKeys.SIGNALTEST_MSG_COMPARISON_DONE: "Comparison complete. See details below."
    ,TranslationKeys.SIGNALTEST_MSG_MAPPING_SAVED_TITLE: "Mapping saved"
    ,TranslationKeys.SIGNALTEST_MSG_MAPPING_SAVED_BODY: "Field mapping stored on the layer."
    ,TranslationKeys.SIGNALTEST_MSG_MAPPING_NOT_SAVED_TITLE: "Mapping not saved"
    ,TranslationKeys.SIGNALTEST_MSG_MAPPING_NOT_SAVED_BODY: "No changes were applied."
    ,TranslationKeys.SIGNALTEST_MSG_MISSING_FIELD_TITLE: "Missing field"
    ,TranslationKeys.SIGNALTEST_MSG_MISSING_FIELD_BODY: "Please map required field: {field}"
    ,TranslationKeys.SIGNALTEST_STATUS_MAPPED: "Mapped"
    ,TranslationKeys.SIGNALTEST_STATUS_MISSING: "Missing"
    ,TranslationKeys.SIGNALTEST_STATUS_UNMAPPED: "Unmapped"
    ,TranslationKeys.SIGNALTEST_STATUS_EXTRA: "Extra"
    ,TranslationKeys.SIGNALTEST_NOTE_REQUIRED: "required"
    ,TranslationKeys.SIGNALTEST_NOTE_OPTIONAL: "optional"
    ,TranslationKeys.SIGNALTEST_NOTE_EXTRA: "Only in layer"
    ,TranslationKeys.SIGNALTEST_NOTE_TARGET_ONLY: "Only in target layer"
    ,TranslationKeys.SIGNALTEST_LABEL_EXTRA: "<extra>"
    ,TranslationKeys.SIGNALTEST_SOURCE_STORED: "stored mapping"
    ,TranslationKeys.SIGNALTEST_SOURCE_AUTO: "auto"
    ,TranslationKeys.SIGNALTEST_DIALOG_TITLE: "Field Mapper"
    ,TranslationKeys.SIGNALTEST_DIALOG_HINT: "Map plugin logical fields to your layer's fields. Required fields are marked with *.\nSelect the matching SHP field; <None> leaves it unmapped (allowed only for optional)."
    ,TranslationKeys.SIGNALTEST_NONE_OPTION: "<None>"
    ,TranslationKeys.SIGNALTEST_OPTION_TOOLTIP: "Map {logical} to {name}"
    ,TranslationKeys.SIGNALTEST_REQUIRED_SUFFIX: " *"
    ,TranslationKeys.SIGNALTEST_LOGICAL_TOOLTIP: "Plugin logical field: {logical}"
    
}