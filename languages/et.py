from .translation_keys import TranslationKeys, RoleTranslationKeys, ToolbarTranslationKeys, DialogLabels, ToolbarTranslationKeys

TRANSLATIONS = {
    TranslationKeys.PROJECTS_MODULE_LOADED: "Projektide moodul laaditud!",
    TranslationKeys.API_ENDPOINT_NOT_CONFIGURED: "API lõpp-punkti pole seadistatud.",
    TranslationKeys.CONFIG_ERROR: "Seadistuse viga: {error}",
    TranslationKeys.LOGIN_FAILED: "Sisselogimine ebaõnnestus: {error}",
    TranslationKeys.NO_API_TOKEN_RECEIVED: "API võtit ei saadud.",
    TranslationKeys.LOGIN_FAILED_RESPONSE: "Sisselogimine ebaõnnestus: {error}",
    TranslationKeys.NETWORK_ERROR: "Võrgu viga: {error}",
    TranslationKeys.LOGIN_TITLE: "Logi sisse",
    TranslationKeys.LANGUAGE_LABEL: "Keel:",
    TranslationKeys.USERNAME_LABEL: "Kasutajanimi:",
    TranslationKeys.PASSWORD_LABEL: "Parool:",
    TranslationKeys.LOGIN_BUTTON: "Logi sisse",
    TranslationKeys.CANCEL_BUTTON: "Tühista",
    TranslationKeys.WILD_CODE_PLUGIN_TITLE: "Kavitro",
    TranslationKeys.HOME_PAGE: "Tere tulemast avalehele!",
    TranslationKeys.SETTINGS_PAGE: "Seadete leht",
    TranslationKeys.ABOUT_PAGE: "Teave leht",
    TranslationKeys.MAILABL_LISTENER: "Mailabl Listener",
    TranslationKeys.SWITCH_TO_DARK_MODE: "Lülita tumedale režiimile",
    TranslationKeys.SWITCH_TO_LIGHT_MODE: "Lülita heledale režiimile",
    TranslationKeys.UNKNOWN_MODULE: "Tundmatu moodul: {module}",
    TranslationKeys.QUERY_FILE_NOT_FOUND: "Päringu faili ei leitud: {file}",
    TranslationKeys.SAVE_SETTING: "Salvesta säte",
    TranslationKeys.USER: "Kasutaja",
    TranslationKeys.ROLES: "Rollid",
    TranslationKeys.MODULE_ACCESS: "Eelistatud moodul",
    TranslationKeys.CONFIRM: "Kinnita",
    TranslationKeys.NAME: "Nimi",
    TranslationKeys.EMAIL: "E-post",
    TranslationKeys.MODULE_SETTINGS_PLACEHOLDER: "Mooduli seadete kohatäide",
    TranslationKeys.WELCOME: "Tere tulemast",
    TranslationKeys.SELECT_MODULE: "Vali vasakult moodul või ava Seaded, et määrata eelistatud moodul.",
    TranslationKeys.NO_PROJECT_LOADED_TITLE: "Ühtegi projekti pole avatud",
    TranslationKeys.NO_PROJECT_LOADED_MESSAGE: "Kavitro plugnin nõuab QGIS projektifaili, et töötada. Palun ava või loo uus projekt.",
    TranslationKeys.OPEN_SETTINGS: "Ava Seaded",
    TranslationKeys.MODULES_MAIN_LAYER: "Mooduli põhikiht",
    TranslationKeys.ARCHIVE_LAYER: "Arhiivikiht",
    TranslationKeys.SELECT_LAYER: "Vali kiht",
    TranslationKeys.MAIN_LAYER_DESCRIPTION: "See on mooduli põhikiht. Vali kiht, mis sisaldab põhiandmeid, millega töötad.",
    TranslationKeys.ARCHIVE_LAYER_DESCRIPTION: "Kasuta valikulist arhiivikihti ajalooliste või varuandmete salvestamiseks.",
    TranslationKeys.CHOOSE_LAYERS_USED_BY_THIS_MODULE: "Vali selle mooduli kasutatavad kihid (elemendi ja arhiivi).",
    TranslationKeys.LOGOUT_BUTTON_TOOLTIP: "Logi välja",
    TranslationKeys.SEARCH_TOOLTIP: "Funktsioon veel ei tööta",
    TranslationKeys.SEARCH_PLACEHOLDER: "Otsi...",
    TranslationKeys.SEARCH_NO_RESULTS: "Tulemusi ei leitud: '{term}'",
    TranslationKeys.SIDEBAR_COLLAPSE_TOOLTIP: "Ahenda külgriba",
    TranslationKeys.SIDEBAR_EXPAND_TOOLTIP: "Laienda külgriba",
    TranslationKeys.THEME_SWITCH_TOOLTIP: "Tume/Hele režiim",
    TranslationKeys.DEV_DBG_TOOLTIP: "Lülita arenduslogid (print) sisse/välja",
    TranslationKeys.DEV_FRAMES_TOOLTIP: "Näita/peida FRAME sildid avalehel",
    TranslationKeys.SESSION_EXPIRED: "Teie seanss on aegunud. Palun logige uuesti sisse.",
    TranslationKeys.SESSION_EXPIRED_TITLE: "Seanss aegunud",
    TranslationKeys.STATUS_PREFERENCES: "Eelistatud staatused",
    TranslationKeys.TAGS_PREFERENCES: "Eelistatud tunnused",
    TranslationKeys.TYPE_PREFERENCES: "Eelistatud liigid",
    TranslationKeys.SELECT_TYPE_DESCRIPTION: "Vali liigid, mida soovid selles moodulis eelistada. Need tõstetakse esile",
    TranslationKeys.SELECT_STATUSES_DESCRIPTION: "Vali staatused, mida soovid selles moodulis eelistada. Need tõstetakse esile",
    TranslationKeys.SELECT_TAGS_DESCRIPTION: "Vali tunnused, mida soovid selles moodulis eelistada. Need tõstetakse esile",
    "urgent_group_title": "Kiire!",
    TranslationKeys.URGENT_TOOLTIP: "Vajab kiiret tähelepanu",
    TranslationKeys.STATUS_FILTER: "Staatuste järgi filtreerimine",
    TranslationKeys.TAGS_FILTER: "Tunnuste järgi filtreerimine",
    TranslationKeys.TYPE_FILTER: "Liigi järgi filtreerimine",
    TranslationKeys.TYPE_GROUP_FILTER: "Liigi grupi järgi filtreerimine",
    TranslationKeys.RESET: "Lähtesta",
    TranslationKeys.CONFIRM: "Kinnita",
    TranslationKeys.RESET_ALL_SETTINGS: "Lähtesta kõik selle mooduli seaded vaikimisi väärtustele",
    TranslationKeys.SETTINGS_RESET_TO_DEFAULTS: "Seaded lähtestati vaikimisi väärtustele",
    TranslationKeys.SHOW_PROJECT_NUMBERS_DESCRIPTION: "Sisselülitamisel kuvatakse kannetel numbrid, et neid oleks lihtsam tuvastada.",
    TranslationKeys.USER_PROFILE: "Kasutaja profiil",
    TranslationKeys.ROLES_PERMISSIONS: "Rollid ja õigused",
    TranslationKeys.MODULE_ACCESS: "Mooduli juurdepääs",
    TranslationKeys.ADMINISTRATOR: "Administraator",
    TranslationKeys.EDITOR: "Toimetaja",
    TranslationKeys.VIEWER: "Vaataja",
    TranslationKeys.DASHBOARD: "Töölaud",
    TranslationKeys.REPORTS: "Aruanded",
    "settings": "Seaded",
    TranslationKeys.ADMIN: "Admin",
    TranslationKeys.USER: "Kasutaja",
    TranslationKeys.USER_INFORMATION: "Kasutaja info",
    TranslationKeys.ROLES: "Rollid",
    TranslationKeys.PREFERRED_MODULE: "Eelistatud moodul",
    TranslationKeys.LEARNING_A_TITLE: "A Tähe õppimine",
    TranslationKeys.LEARNING_B_TITLE: "B Tähe õppimine",
    TranslationKeys.LEARNING_C_TITLE: "C Tähe õppimine",
    TranslationKeys.LEARNING_A_DESCRIPTION: "A täht on eesti tähestiku esimene täht. See on täht, millega algab paljude sõnade ja nimede kirjutamine. Õppides A tähte, teed esimese sammu lugemise ja kirjutamise oskuse poole.",
    TranslationKeys.LEARNING_B_DESCRIPTION: "B täht on eesti tähestikus teine täht. Seda kasutatakse paljudes sõnades, näiteks 'banaan' ja 'buss'. B tähe õppimine aitab laiendada sõnavara ja parandada hääldust.",
    TranslationKeys.LEARNING_C_DESCRIPTION: "C täht esineb eesti keeles peamiselt võõrsõnades, näiteks 'cirkus' või 'cello'. C tähe tundmine aitab mõista ja lugeda rahvusvahelisi sõnu.",
    TranslationKeys.PROPERTY_MANAGEMENT: "Kinnistute haldus",
    TranslationKeys.QUICK_ACTIONS: "Kiired toimingud",
    TranslationKeys.ADD_SHP_FILE: "Lisa SHP fail",
    TranslationKeys.ADD_PROPERTY: "Lisa kinnistuid",
    TranslationKeys.REMOVE_PROPERTY: "Eemalda kinnistu",
    TranslationKeys.LOAD_SHAPEFILE: "Laadi Shapefile",
    TranslationKeys.SELECT_SHAPEFILE: "Vali Shapefile fail",
    TranslationKeys.CHOOSE_PROPERTY_LAYER_FOR_MODULE: "Vali kinnistu kiht.",
    TranslationKeys.SELECT_A_PROPERTY_LAYER: "Vali kinnistute kiht...",
    TranslationKeys.PROPERTY_TREE_HEADER: "Kinnistuga seotud andmed",
    TranslationKeys.PROPERTY_TREE_DEFAULT_MESSAGE: "Vali kinnistu kaardilt",
    TranslationKeys.PROPERTY_TREE_LOADING: "Laen seotud andmeid...",
    TranslationKeys.PROPERTY_TREE_NO_CONNECTIONS: "Seoseid ei leitud",
    TranslationKeys.PROPERTY_TREE_NO_DATA: "Andmed puuduvad",
    TranslationKeys.PROPERTY_TREE_MODULE_EMPTY: "Kirjeid ei ole",
    TranslationKeys.PROPERTY_TREE_ROW_NO_TITLE: "Nimetus puudub",
    TranslationKeys.PROPERTY_TREE_ROW_UPDATED_PREFIX: "Uuendatud {date}",
    TranslationKeys.SHAPEFILE_LOADED_SUCCESSFULLY: "Shapefile edukalt laaditud",
    TranslationKeys.SHAPEFILE_LOADED_MESSAGE: "Shapefile '{name}' on edukalt laaditud grupis 'Uued kinnistud'",
    TranslationKeys.SHAPEFILE_LOADED_WITH_DATA_MESSAGE: "Shapefile '{name}' on edukalt laaditud grupis 'Uued kinnistud' ({count} objekti imporditud)",
    TranslationKeys.INVALID_SHAPEFILE: "Vigane Shapefile",
    TranslationKeys.INVALID_SHAPEFILE_MESSAGE: "Valitud Shapefile fail ei ole kehtiv.",
    TranslationKeys.SHAPEFILE_LOAD_FAILED: "Shapefile laadimine ebaõnnestus"
    ,"Shapefile load failed message": "Shapefile faili laadimine ebaõnnestus."
    ,"Shapefile loading error": "Shapefile laadimise viga"
    ,"Importing Shapefile": "Shapefile importimine"
    ,"Processing features": "Objektide töötlemine"
    ,"Features copied": "Objekte kopeeritud"
    ,"Import complete": "Import lõpetatud"
    ,"features imported": "objekti imporditud"
    ,"feature imported": "objekt imporditud"
    ,"Initializing...": "Initsialiseerimine..."
    ,"Cancel": "Katkesta"

    ,"Add New Property": "Lisa uus kinnistu"
    ,"Select a property template to add:": "Vali lisatav kinnistu mall:"
    ,"Residential Property": "Elamukinnistu"
    ,"Commercial Property": "Ärikinnistu"
    ,"Industrial Property": "Tööstuskinnistu"
    ,"Agricultural Land": "Põllumajandusmaa"
    ,"Vacant Land": "Tühi maatükk"
    ,"Standard residential property template": "Standardne elamukinnistu mall"
    ,"Commercial building template": "Ärihoone mall"
    ,"Industrial facility template": "Tööstushoone mall"
    ,"Agricultural land template": "Põllumajandusmaa mall"
    ,"Empty land parcel template": "Tühi maatüki mall"
    ,"Add New Property": "Lisa uus kinnistu"
    ,"Property Details": "Kinnistu andmed"
    ,"Additional Information": "Lisateave"
    ,"Property Name:": "Kinnistu nimi:"
    ,"Property Type:": "Kinnistu tüüp:"
    ,"Area (m²):": "Pindala (m²):"
    ,"Value (€):": "Väärtus (€):"
    ,"Residential": "Elamu"
    ,"Commercial": "Äri"
    ,"Industrial": "Tööstus"
    ,"Agricultural": "Põllumajandus"
    ,"Other": "Muu"
    ,"Enter property name": "Sisesta kinnistu nimi"
    ,"Enter area in m²": "Sisesta pindala m²"
    ,"Enter property value": "Sisesta kinnistu väärtus"
    ,"Enter property address": "Sisesta kinnistu aadress"
    ,"Enter additional notes or description": "Sisesta lisamärkused või kirjeldus"
    ,"Add Property": "Lisa kinnistu"
    ,"Property name is required.": "Kinnistu nimi on kohustuslik."
    ,"Area must be greater than 0.": "Pindala peab olema suurem kui 0."
    ,"Value must be greater than 0.": "Väärtus peab olema suurem kui 0."
    ,"Validation Error": "Valideerimise viga"
    ,"Cadastral ID": "Katastritunnus"
    ,"Address": "Aadress"
    ,"Area (m²)": "Pindala (m²)"
    ,TranslationKeys.SETTLEMENT: "Linn/Asustusüksus"
    ,"Property Name": "Kinnistu nimi"
    ,"Property Type": "Kinnistu tüüp"
    ,"Value (€)": "Väärtus (€)"
    ,"Add Property": "Lisa kinnistu"
    ,"Cancel": "Katkesta"
    ,"Save": "Salvesta"
    ,"Delete": "Kustuta"
    ,"Edit": "Muuda"
    ,"Select": "Vali"
    ,"Search": "Otsi"
    ,"Confirm": "Kinnita"
    ,TranslationKeys.YES: "Jah"
    ,TranslationKeys.NO: "Ei"
    ,TranslationKeys.OK: "OK"
    ,TranslationKeys.LOADING: "Laadimine"
    ,TranslationKeys.SAVING: "Salvestan"
    ,TranslationKeys.DELETING: "Kustutamine"
    ,TranslationKeys.SUCCESS: "Edu"
    ,TranslationKeys.ERROR: "Viga"
    ,"Warning": "Hoiatus"
    ,"This field is required": "See väli on kohustuslik"
    ,"Invalid value": "Vigane väärtus"
    ,"Value must be greater than {min}": "Väärtus peab olema suurem kui {min}"
    ,"Value must be less than {max}": "Väärtus peab olema väiksem kui {max}"
    ,TranslationKeys.PROPERTIES: "Kinnistud"
    ,TranslationKeys.CONTRACTS: "Lepingud"
    ,"Contracts": "Lepingud"
    ,TranslationKeys.PROJECTS: "Projektid"
    ,TranslationKeys.LETTERS: "Kirjad"
    ,TranslationKeys.SPECIFICATIONS: "Tingimused"
    ,TranslationKeys.EASEMENTS: "Servituudid"
    ,TranslationKeys.COORDINATIONS: "Kooskõlastused"
    ,TranslationKeys.TASKS: "Ülesanded"
    ,TranslationKeys.SUBMISSIONS: "Esitused"
    ,TranslationKeys.ORDINANCES: "Käskkirjad"
    ,TranslationKeys.SELECT_SETTLEMENTS: "Vali asustusüksused"
    ,TranslationKeys.ADD_NEW_PROPERTY: "Kinnistute haldamine"
    ,TranslationKeys.SELECT_PROPERTIES: "Vali kinnistud"
    ,TranslationKeys.CLOSE: "Sulge"
    ,TranslationKeys.SELECT_ALL: "Vali kõik"
    ,TranslationKeys.CLEAR_SELECTION: "Tühjenda valik"
    ,TranslationKeys.ADD_SELECTED: "Lisa valitud"
    ,TranslationKeys.SELECT_COUNTY: "Vali maakond"
    ,TranslationKeys.SELECT_MUNICIPALITY: "Vali omavalitsus"
    ,TranslationKeys.FILTER_BY_LOCATION: "Filtreeri asukoha järgi"
    ,TranslationKeys.SELECTED_PROPERTIES_COUNT: "Valitud: 0 kinnistut"
    ,TranslationKeys.SELECTED_COUNT_TEMPLATE: "Valitud: {count} kinnistut"
    ,TranslationKeys.NO_SELECTION: "Valikut pole"
    ,ToolbarTranslationKeys.OPEN_FOLDER: "Ava kaust"
    ,ToolbarTranslationKeys.OPEN_ITEM_IN_BROWSER: "Ava kirje brauseris"
    ,ToolbarTranslationKeys.SHOW_ITEMS_ON_MAP: "Näita kirjeid kaardil"
    ,TranslationKeys.PLEASE_SELECT_AT_LEAST_ONE_PROPERTY: "Palun valige vähemalt üks kinnistu."
    ,TranslationKeys.NO_PROPERTY_LAYER_SELECTED: "Kinnistute kihti pole valitud. Palun valige esmalt kinnistute kiht."
    ,TranslationKeys.DATA_LOADING_ERROR: "Andmete laadimise viga"
    ,TranslationKeys.FAILED_TO_LOAD_PROPERTY_DATA: "Andmete laadimine kihist ebaõnnestus."
    ,TranslationKeys.PROPERTIES_ADDED: "Kinnistud lisatud"
    ,TranslationKeys.SELECTED_PROPERTIES_ADDED: "Valitud kinnistud on lisatud."
    , TranslationKeys.COUNTY: "Maakond"
    ,TranslationKeys.MUNICIPALITY: "Omavalitsus"
    ,TranslationKeys.CHOOSE_FROM_MAP: "Vali kaardilt"
    ,TranslationKeys.NO_SELECTION: "Valikut pole"
    ,TranslationKeys.SELECT_PROPERTY_FIRST: "Palun valige esmalt kaardilt kinnisvara objekt."
    ,TranslationKeys.ERROR_SELECTING_PROPERTY: "Viga kinnisvara valimisel"
    ,TranslationKeys.SELECT_SINGLE_PROPERTY_TITLE: "Vali üks kinnisvara"
    ,TranslationKeys.SELECT_SINGLE_PROPERTY_MESSAGE: "Palun valige kaardilt ainult üks kinnisvara objekt."
    ,TranslationKeys.STATUS_FILTER: "Staatuste järgi filtreerimine"
    ,TranslationKeys.TAGS_FILTER: "Tunnuste järgi filtreerimine"
    ,TranslationKeys.TYPE_FILTER: "Liigi järgi filtreerimine"
    ,TranslationKeys.MODULE_HOME: "Avaleht"
    ,TranslationKeys.MODULE_PROPERTY: "Kinnistud"
    ,TranslationKeys.MODULE_CONTRACT: "Lepingud"
    ,TranslationKeys.MODULE_PROJECT: "Projektid"
    ,TranslationKeys.MODULE_SETTINGS: "Seaded"
    ,TranslationKeys.MODULE_COORDINATION: "Kooskõlastused"
    ,TranslationKeys.MODULE_LETTER: "Kirjad"
    ,TranslationKeys.MODULE_SPECIFICATION: "Tingimused"
    ,TranslationKeys.MODULE_EASEMENT: "Servituudid"
    ,TranslationKeys.MODULE_ORDINANCE: "Käskkirjad"
    ,TranslationKeys.MODULE_SUBMISSION: "Esitused"
    ,TranslationKeys.MODULE_TASK: "Ülesanded"
    ,TranslationKeys.MODULE_ASBUILT: "Teostusjoonised"
    ,TranslationKeys.MODULE_WORKS: "Tööd"
    ,TranslationKeys.MODULE_TAGS: "Tunnused"
    ,TranslationKeys.MODULE_STATUSES: "Staatused"
    ,RoleTranslationKeys.ADMINS: "Admin"
    ,RoleTranslationKeys.ADMINISTRATORS: "Administraatorid"
    ,RoleTranslationKeys.PROJECT_MANAGERS: "Projektijuht"
    ,RoleTranslationKeys.USERS: "Kasuta"
    ,RoleTranslationKeys.MANAGERS: "Vastutaja"
    ,RoleTranslationKeys.EDITORS: "Muutja"
    ,RoleTranslationKeys.VIEWERS: "Vaataja"
    ,RoleTranslationKeys.GUESTS: "Külaline"
    ,TranslationKeys.START: "Algus"
    ,TranslationKeys.CREATED: "Loodud"
    ,TranslationKeys.UPDATED: "Muudetud"
    ,"Signaltest": "Signaalitester"
    ,TranslationKeys.CONNECTIONS: "Otsin seoseid"
    ,DialogLabels.PROJECTS_SOURCE_FOLDER: "Projektide lähtekaust"
    ,DialogLabels.PROJECTS_TARGET_FOLDER: "Projektide sihtkaust"
    ,ToolbarTranslationKeys.MORE_ACTIONS: "Rohkem toiminguid"
}
