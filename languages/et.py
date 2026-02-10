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
        TranslationKeys.FOLDER_NAMING_RULE_DIALOG_TITLE: "Kausta nimetamise reegel",
        TranslationKeys.SETTINGS_BASE_CARD_TEXT: "Seaded",
        TranslationKeys.SETTINGS_UTILS_DASH: "—",
        TranslationKeys.ADD_UPDATE_PROPERTY_DIALOG_CANCELLING: "Katkestamine...",
        TranslationKeys.HEADER_WIDGET_ABI: "Abi",
        TranslationKeys.OVERDUE_DUE_SOON_PILLS_ELLIPSIS: "…",
        TranslationKeys.PROGRESS_DIALOG_MODERN_PERCENT: "0%",
        TranslationKeys.SEARCH_RESULTS_WIDGET_CLOSE_TOOLTIP: "Sulge otsingutulemused",
        TranslationKeys.SIDEBAR_LEFT_ARROW: "«",
        TranslationKeys.SIDEBAR_RIGHT_ARROW: "»",
        TranslationKeys.DATA_DISPLAY_WIDGETS_EXTRAINFO_TOOLTIP: "Ava detailne ülevaade",
        TranslationKeys.DATA_DISPLAY_WIDGETS_INFOCARDHEADER_TOOLTIP: "Privaatne",
        TranslationKeys.DATA_DISPLAY_WIDGETS_DATES_EMPTY: "Kuupäevad puuduvad",
        TranslationKeys.DATA_DISPLAY_WIDGETS_DETAIL_TITLE_SUFFIX: "Detailne ülevaade",
        TranslationKeys.DATA_DISPLAY_WIDGETS_CLOSE: "Sulge",
        TranslationKeys.DATA_DISPLAY_WIDGETS_OVERVIEW_TITLE: "Tegevuste ülevaade",
        TranslationKeys.DATA_DISPLAY_WIDGETS_PROJECT_OVERVIEW_TITLE: "Projekti tegevuste ülevaade",
        TranslationKeys.DATA_DISPLAY_WIDGETS_CONTRACT_OVERVIEW_TITLE: "Lepingu tegevuste ülevaade",
        TranslationKeys.DATA_DISPLAY_WIDGETS_COLUMN_DONE: "Tehtud",
        TranslationKeys.DATA_DISPLAY_WIDGETS_COLUMN_IN_PROGRESS: "Töös",
        TranslationKeys.DATA_DISPLAY_WIDGETS_COLUMN_TODO: "Tegemata",
        TranslationKeys.DATA_DISPLAY_WIDGETS_COLUMN_SIGNED: "Allkirjastatud",
        TranslationKeys.DATA_DISPLAY_WIDGETS_COLUMN_PROCESSING: "Töötlemisel",
        TranslationKeys.DATA_DISPLAY_WIDGETS_COLUMN_PENDING: "Ootel",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_PLANNING: "Planeerimine",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_COMPILATION: "Koostamine",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_REVIEW: "Ülevaatamine",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_APPROVAL: "Kinnitamine",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_TESTING: "Testimine",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_DOCUMENTING: "Dokumenteerimine",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_OPTIMIZING: "Optimeerimine",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_PUBLISHING: "Avaldamine",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_MONITORING: "Jälgimine",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_ARCHIVING: "Arhiveerimine",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_REPORTING: "Raporteerimine",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_CONTRACT_DRAFTING: "Lepingu koostamine",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_PARTY_CONSENT: "Osapoolte nõusolek",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_NOTARIAL_CONFIRM: "Notariaalne kinnitamine",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_LEGAL_REVIEW: "Juriidiline ülevaatus",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_FINANCIAL_CHECK: "Finantskontroll",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_SIGNATURES: "Osapoolte allkirjad",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_COMPLETION_CHECK: "Täitmise kontroll",
        TranslationKeys.DATA_DISPLAY_WIDGETS_PROJECT_DETAIL_CONTENT: """
        <h3>Projekti Detailne Ülevaade</h3>
        <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>

        <h4>Projekti Faasid</h4>
        <ul>
        <li><b>Planeerimine:</b> Projekti eesmärkide ja ulatuse määramine</li>
        <li><b>Koostamine:</b> Projekti komponentide arendamine</li>
        <li><b>Testimine:</b> Funktsionaalsuse kontrollimine</li>
        <li><b>Avaldamine:</b> Projekti lõplik väljastamine</li>
        </ul>

        <h4>Projekti Statistika</h4>
        <p>Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.</p>
        """,
        TranslationKeys.DATA_DISPLAY_WIDGETS_CONTRACT_DETAIL_CONTENT: """
        <h3>Lepingu Detailne Ülevaade</h3>
        <p>Contract management and legal documentation overview.</p>

        <h4>Lepingu Faasid</h4>
        <ul>
        <li><b>Allkirjastatud:</b> Legal binding agreements</li>
        <li><b>Töötlemisel:</b> Under legal and financial review</li>
        <li><b>Ootel:</b> Awaiting signatures or completion</li>
        </ul>
        """,
        TranslationKeys.HEADER_HELP_BUTTON_TOOLTIP: "Abi",
        TranslationKeys.NO_PROJECTS_FOUND: "Projekte ei leitud",
        TranslationKeys.NO_CONTRACTS_FOUND: "Lepinguid ei leitud",
        TranslationKeys.NO_COORDINATIONS_FOUND: "Kooskõlastusi ei leitud",
        TranslationKeys.NO_VALUES_FOUND: "Väärtusi ei leitud!",
        TranslationKeys.LOADING: "Laadimine…",
        TranslationKeys.CLEAR_VALUE: "Tühjenda väärtus",
        TranslationKeys.PROPERTY_ID_PLACEHOLDER: "Kinnistu ID",
        TranslationKeys.MISSING_PROPERTY_ID_TITLE: "ID puudub",
        TranslationKeys.MISSING_PROPERTY_ID_BODY: "Palun sisesta kinnistu ID.",
        TranslationKeys.PROPERTY_LAYER_FIELD_NOT_FOUND: "Väli '{field_name}' puudub kinnistute kihil.",
        TranslationKeys.ADD_UPDATE_PROGRESS_PREFIX: "Kinnistute lisamine",
        TranslationKeys.ADD_UPDATE_PROGRESS_PREFIX_NO_CHECKS: "Lisamine (ilma kontrollideta)",
        TranslationKeys.ADD_UPDATE_PROGRESS_FINISHED: "Lõpetatud",
        TranslationKeys.ADD_UPDATE_PROGRESS_FINISHED_NO_CHECKS: "Lõpetatud (ilma kontrollideta)",
        TranslationKeys.ADD_UPDATE_PROGRESS_TEMPLATE: "{prefix} {done}/{total}",
        TranslationKeys.ADD_UPDATE_PROGRESS_CANCELLED_TEMPLATE: "{prefix} - katkestati {done}/{total} juures",
        TranslationKeys.DELAY_HELPERS_LOADINGSPINNER_TITLE: "GradientSpinner + täpid demo",
    TranslationKeys.PROJECTS_MODULE_LOADED: "Projektide moodul laaditud!",
    TranslationKeys.API_ENDPOINT_NOT_CONFIGURED: "API lõpp-punkti pole seadistatud.",
    TranslationKeys.CONFIG_ERROR: "Seadistuse viga: {error}",
    TranslationKeys.LOGIN_FAILED: "Sisselogimine ebaõnnestus: {error}",
    TranslationKeys.NO_API_TOKEN_RECEIVED: "API võtit ei saadud.",
    TranslationKeys.LOGIN_FAILED_RESPONSE: "Sisselogimine ebaõnnestus: {error}",
    TranslationKeys.NETWORK_ERROR: "Võrgu viga: {error}",
    TranslationKeys.LOGIN_TITLE: "Logi sisse",
    TranslationKeys.LANGUAGE_LABEL: "Keel:",
    DialogLabels.LOGIN_SECTION: "Kasutaja autentimine",
    DialogLabels.SETTINGS_SECTION: "Rakenduse eelistused",
    DialogLabels.SESSION_EXPIRED_ERROR: "Seanss on aegunud. Palun logi uuesti sisse.",
    DialogLabels.INVALID_CREDENTIALS_ERROR: "Vale e-post või parool.",
    TranslationKeys.USERNAME_LABEL: "Kasutajanimi:",
    TranslationKeys.PASSWORD_LABEL: "Parool:",
    TranslationKeys.LOGIN_BUTTON: "Logi sisse",
    TranslationKeys.CANCEL_BUTTON: "Tühista",
    TranslationKeys.KAVITRO_PLUGIN_TITLE: "Kavitro",
    TranslationKeys.MAILABL_LISTENER: "Mailabl Listener",
    TranslationKeys.UNKNOWN_MODULE: "Tundmatu moodul: {module}",
    TranslationKeys.QUERY_FILE_NOT_FOUND: "Päringu faili ei leitud: {file}",
    TranslationKeys.SAVE_SETTING: "Salvesta säte",
    TranslationKeys.USER: "Kasutaja",
    TranslationKeys.ROLES: "Rollid",
    TranslationKeys.CONFIRM: "Kinnita",
    TranslationKeys.NAME: "Nimi",
    TranslationKeys.EMAIL: "E-post",
    TranslationKeys.MODULE_SETTINGS_PLACEHOLDER: "Mooduli seadete kohatäide",
    TranslationKeys.PREFERRED_MODULE: "Eelistatud moodul",
    TranslationKeys.COUNTY: "Maakond",
    TranslationKeys.MUNICIPALITY: "Omavalitsus",
    TranslationKeys.DUE: "Tähtaeg",
    TranslationKeys.SEARCHING: "Otsimine",
    TranslationKeys.HOME_PAGE: "Avaleht",
    TranslationKeys.SETTINGS_PAGE: "Seadete leht",
    TranslationKeys.ABOUT_PAGE: "Teave",
    TranslationKeys.SWITCH_TO_DARK_MODE: "Lülita tumedale režiimile",
    TranslationKeys.SWITCH_TO_LIGHT_MODE: "Lülita heledale režiimile",
    TranslationKeys.TOGGLE_PASSWORD: "Näita parooli",
    TranslationKeys.WELCOME: "Tere tulemast",
    TranslationKeys.SELECT_MODULE: "Vali vasakult moodul või ava Seaded, et määrata eelistatud moodul.",
    TranslationKeys.NO_PROJECT_LOADED_TITLE: "Ühtegi projekti pole avatud",
    TranslationKeys.NO_PROJECT_LOADED_MESSAGE: "Kavitro plugnin nõuab QGIS projektifaili, et töötada. Palun ava või loo uus projekt.",
    TranslationKeys.PROJECT_FOLDER_MISSING_TITLE: "Projektikausta seadistus vajalik",
    TranslationKeys.PROJECT_FOLDER_MISSING_MESSAGE: "Projekti kaustad pole selle mooduli jaoks määratud. Avan Seaded...",
    TranslationKeys.HOW_SELECT_PROPERTIES: "Kuidas soovid kinnistuid valida?",
    TranslationKeys.PROPERTY_ARCHIVED_BACKEND_MATCH_TITLE: "Arhiveeritud kanne olemas",
    TranslationKeys.PROPERTY_ARCHIVED_BACKEND_MATCH_BODY: "Taustasüsteemis on arhiveeritud kinnistu katastrinumbriga {tunnus}.\n\nMida soovid teha?",
    TranslationKeys.PROPERTY_UNARCHIVE_FAILED_TITLE: "Lahtiarhiveerimine ebaõnnestus",
    TranslationKeys.PROPERTY_UNARCHIVE_FAILED_BODY: "Taustasüsteemi kinnistu {backend_id} lahtiarhiveerimine {tunnus} jaoks ebaõnnestus.",
    TranslationKeys.PROPERTY_BACKEND_UPDATE_FAILED_TITLE: "Taustasüsteemi uuendus ebaõnnestus",
    TranslationKeys.PROPERTY_BACKEND_UPDATE_FAILED_BODY: "Taustasüsteemi kinnistu lahtiarhiveeriti, kuid andmete uuendamine {tunnus} jaoks ebaõnnestus.",
    TranslationKeys.PROPERTY_BACKEND_MISSING_TITLE: "Taustasüsteemis puudub",
    TranslationKeys.PROPERTY_BACKEND_MISSING_BODY: "Kinnistu {tunnus} on põhikihis, kuid puudub taustasüsteemis.\n\nKas luua taustasüsteemi kirje importandmetest?",
    TranslationKeys.PROPERTY_BACKEND_MISSING_ARCHIVED_BODY: "Kinnistu {tunnus} on põhikihis. Taustasüsteemis on ainult arhiveeritud kirje selle katastrinumbriga.\n\nKas luua uus AKTIIVNE kirje taustasüsteemi importandmetest?",
    TranslationKeys.PROPERTY_BACKEND_EXISTS_MISSING_MAP_TITLE: "Kinnistu olemas",
    TranslationKeys.PROPERTY_BACKEND_EXISTS_MISSING_MAP_BODY: "Kinnistu {tunnus} on taustasüsteemis olemas, kuid puudub põhikihis.\n\nKas kopeerida objekt importkihist põhikihti?",
    TranslationKeys.PROPERTY_NEWER_IMPORT_TITLE: "Uuem import tuvastatud",
    TranslationKeys.PROPERTY_NEWER_IMPORT_BODY: "Kinnistu {tunnus} on taustasüsteemis ja põhikihis, kuid import paistab uuem.\n\nKas arhiveerida/asendada olemasolev kinnistu?\n- Tõstab olemasoleva objekti arhiivikihile\n- Märgib taustasüsteemi kinnistu arhiveerituks\n- Asendab põhikihi objekti importkihist võetuga",
    TranslationKeys.PROPERTY_REPLACE_FAILED_TITLE: "Asendamine ebaõnnestus",
    TranslationKeys.PROPERTY_REPLACE_FAILED_BODY_NO_FEATURE: "Olemasolevat objekti {tunnus} arhiveerimiseks/asendamiseks ei leitud.",
    TranslationKeys.PROPERTY_REPLACE_FAILED_BODY_DELETE: "Olemasoleva objekti kustutamine põhikihist {tunnus} ebaõnnestus.",
    TranslationKeys.PROPERTY_REPLACE_FAILED_BODY_COPY: "Impordi kopeerimine põhikihile ebaõnnestus {tunnus}: {message}",
    TranslationKeys.PROPERTY_ARCHIVE_LAYER_MISSING_TITLE: "Arhiivikiht puudub",
    TranslationKeys.PROPERTY_ARCHIVE_LAYER_MISSING_BODY: "Arhiivikiht on seadistamata või puudub; arhiveerimine/asendamine ei ole võimalik.",
    TranslationKeys.PROPERTY_MAIN_LAYER_MISSING_TITLE: "Põhikiht puudub",
    TranslationKeys.PROPERTY_MAIN_LAYER_MISSING_BODY: "Põhikinnistute kiht puudub või on vigane. Palun seadista Seadetes.",
    TranslationKeys.PROPERTY_ARCHIVE_LAYER_REQUIRED_TITLE: "Arhiivikiht on nõutud",
    TranslationKeys.PROPERTY_ARCHIVE_LAYER_REQUIRED_BODY_NO_NAME: "Arhiivikiht pole kinnistute jaoks seadistatud.\n\nVali edasine:\n- Ava Seaded arhiivikihi valimiseks\n- Loo/laadi arhiivikiht samasse GPKG-sse nagu MAIN",
    TranslationKeys.PROPERTY_ARCHIVE_LAYER_REQUIRED_BODY_NAME: "Arhiivikiht '{name}' ei leidu/projektis on vigane.\n\nVali edasine:\n- Ava Seaded arhiivikihi valimiseks\n- Loo/laadi arhiivikiht samasse GPKG-sse nagu MAIN",
    TranslationKeys.PROPERTY_OPEN_SETTINGS_FAILED_TITLE: "Seadete avamine ebaõnnestus",
    TranslationKeys.PROPERTY_OPEN_SETTINGS_FAILED_BODY: "Seadete moodulit ei õnnestunud automaatselt avada.\n\nViga: {error}",
    TranslationKeys.PROPERTY_CANNOT_CREATE_ARCHIVE_TITLE: "Arhiivikihti ei saa luua",
    TranslationKeys.PROPERTY_CANNOT_CREATE_ARCHIVE_BODY: "Arhiivikihi automaatne loomine on toetatud ainult siis, kui MAIN on GeoPackage (.gpkg) kiht.\n\nPalun seadista arhiivikiht Seadetes.",
    TranslationKeys.PROPERTY_INVALID_ARCHIVE_NAME_TITLE: "Vigane nimi",
    TranslationKeys.PROPERTY_INVALID_ARCHIVE_NAME_BODY: "Arhiivikihi nimi ei tohi olla tühi.",
    TranslationKeys.PROPERTY_ARCHIVE_LAYER_CREATE_FAILED_TITLE: "Arhiivikihi loomine ebaõnnestus",
    TranslationKeys.PROPERTY_ARCHIVE_LAYER_CREATE_FAILED_BODY: "Arhiivikihi '{name}' loomine/laadimine ebaõnnestus.\n\nViga: {error}",
    TranslationKeys.PROPERTY_ARCHIVE_LAYER_CREATE_FAILED_BODY_GENERIC: "Arhiivikihi '{name}' loomine/laadimine ebaõnnestus.",
    TranslationKeys.PROPERTY_ARCHIVE_LAYER_NAME_PROMPT_TITLE: "Loo/Laadi arhiivikiht",
    TranslationKeys.PROPERTY_ARCHIVE_LAYER_NAME_PROMPT_LABEL: "Arhiivikihi nimi:",
    TranslationKeys.RUN_ATTENTION_CHECKS: "Käivita kontroll",
    TranslationKeys.YES_TO_ALL: "Jah kõigile",
    TranslationKeys.ADD_WITHOUT_CHECKS: "Lisa ilma kontrollita",
    TranslationKeys.OPEN_SETTINGS: "Ava Seaded",
    TranslationKeys.MAIN_PROPERTY_LAYER: "Kinnistute põhikiht",
    TranslationKeys.ARCHIVE_LAYER: "Arhiivikiht",
    TranslationKeys.SELECT_LAYER: "Vali kiht",
    TranslationKeys.PROPERTY_LAYER_OVERVIEW: "See on kinnistute põhikiht.\nVali kiht, mis kajastab ettevõtte peamist kinnistute kaardikihti.",
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
    TranslationKeys.FILTERS_REFRESH: "Värskenda filtreid",
    TranslationKeys.FILTERS_CLEAR: "Tühjenda filtrivalikud",
    TranslationKeys.RESET_ALL_SETTINGS: "Lähtesta kõik selle mooduli seaded vaikimisi väärtustele",
    TranslationKeys.SETTINGS_RESET_TO_DEFAULTS: "Seaded lähtestati vaikimisi väärtustele",
    TranslationKeys.SHOW_PROJECT_NUMBERS_DESCRIPTION: "Sisselülitamisel kuvatakse kannetel numbrid, et neid oleks lihtsam tuvastada.",
    TranslationKeys.USER_PROFILE: "Kasutaja profiil",
    TranslationKeys.ROLES_PERMISSIONS: "Rollid ja õigused",
    TranslationKeys.MODULE_ACCESS: "Mooduli juurdepääs",
    TranslationKeys.ADMINISTRATOR: "Administraator",
    TranslationKeys.EDITOR: "Toimetaja",
    TranslationKeys.VIEWER: "Vaataja",
    TranslationKeys.OPEN_MAA_AMET_PAGE: "Ava Maa-ameti leht",
    TranslationKeys.DASHBOARD: "Töölaud",
    TranslationKeys.REPORTS: "Aruanded",
    TranslationKeys.ADMIN: "Admin",
    TranslationKeys.USER_INFORMATION: "Kasutaja info",
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
    ,TranslationKeys.SHAPEFILE_LOAD_FAILED_MESSAGE: "Shapefile faili laadimine ebaõnnestus."
    ,TranslationKeys.SHAPEFILE_LOADING_ERROR: "Shapefile laadimise viga"
    ,TranslationKeys.IMPORTING_SHAPEFILE: "Shapefile importimine"
    ,TranslationKeys.PROCESSING_FEATURES: "Objektide töötlemine"
    ,TranslationKeys.FEATURES_COPIED: "Objekte kopeeritud"
    ,TranslationKeys.IMPORT_COMPLETE: "Import lõpetatud"
    ,TranslationKeys.FEATURES_IMPORTED: "objekti imporditud"
    ,TranslationKeys.FEATURE_IMPORTED: "objekt imporditud"
    ,TranslationKeys.INITIALIZING: "Initsialiseerimine..."
    ,TranslationKeys.SELECT_PROPERTY_TEMPLATE: "Vali lisatav kinnistu mall:"
    ,TranslationKeys.RESIDENTIAL_PROPERTY: "Elamukinnistu"
    ,TranslationKeys.COMMERCIAL_PROPERTY: "Ärikinnistu"
    ,TranslationKeys.INDUSTRIAL_PROPERTY: "Tööstuskinnistu"
    ,TranslationKeys.AGRICULTURAL_LAND: "Põllumajandusmaa"
    ,TranslationKeys.VACANT_LAND: "Tühi maatükk"
    ,TranslationKeys.STANDARD_RESIDENTIAL_TEMPLATE: "Standardne elamukinnistu mall"
    ,TranslationKeys.COMMERCIAL_BUILDING_TEMPLATE: "Ärihoone mall"
    ,TranslationKeys.INDUSTRIAL_FACILITY_TEMPLATE: "Tööstushoone mall"
    ,TranslationKeys.AGRICULTURAL_LAND_TEMPLATE: "Põllumajandusmaa mall"
    ,TranslationKeys.EMPTY_LAND_PARCEL_TEMPLATE: "Tühi maatüki mall"
    ,TranslationKeys.PROPERTY_DETAILS: "Kinnistu andmed"
    ,TranslationKeys.ADDITIONAL_INFORMATION: "Lisateave"
    ,TranslationKeys.PROPERTY_NAME_LABEL: "Kinnistu nimi:"
    ,TranslationKeys.PROPERTY_TYPE_LABEL: "Kinnistu tüüp:"
    ,TranslationKeys.AREA_M2: "Pindala (m²):"
    ,TranslationKeys.VALUE_LABEL: "Väärtus (€):"
    ,TranslationKeys.RESIDENTIAL: "Elamu"
    ,TranslationKeys.COMMERCIAL: "Äri"
    ,TranslationKeys.INDUSTRIAL: "Tööstus"
    ,TranslationKeys.AGRICULTURAL: "Põllumajandus"
    ,TranslationKeys.OTHER: "Muu"
    ,TranslationKeys.ENTER_PROPERTY_NAME: "Sisesta kinnistu nimi"
    ,TranslationKeys.ENTER_AREA: "Sisesta pindala m²"
    ,TranslationKeys.ENTER_PROPERTY_VALUE: "Sisesta kinnistu väärtus"
    ,TranslationKeys.ENTER_PROPERTY_ADDRESS: "Sisesta kinnistu aadress"
    ,TranslationKeys.ENTER_ADDITIONAL_NOTES_OR_DESCRIPTION: "Sisesta lisamärkused või kirjeldus"
    ,TranslationKeys.ADD_PROPERTY_BUTTON: "Lisa kinnistu"
    ,TranslationKeys.PROPERTY_NAME_REQUIRED: "Kinnistu nimi on kohustuslik."
    ,TranslationKeys.AREA_MUST_BE_GREATER_THAN_ZERO: "Pindala peab olema suurem kui 0."
    ,TranslationKeys.VALUE_MUST_BE_GREATER_THAN_ZERO: "Väärtus peab olema suurem kui 0."
    ,TranslationKeys.VALIDATION_ERROR: "Valideerimise viga"
    ,TranslationKeys.CADASTRAL_ID: "Katastritunnus"
    ,TranslationKeys.ADDRESS: "Aadress"
    ,TranslationKeys.AREA: "Pindala (m²)"
    ,TranslationKeys.SETTLEMENT: "Linn/Asustusüksus"
    ,TranslationKeys.PROPERTY_NAME: "Kinnistu nimi"
    ,TranslationKeys.PROPERTY_TYPE: "Kinnistu tüüp"
    ,TranslationKeys.VALUE: "Väärtus (€)"
    ,TranslationKeys.SAVE: "Salvesta"
    ,TranslationKeys.DELETE: "Kustuta"
    ,TranslationKeys.EDIT: "Muuda"
    ,TranslationKeys.SELECT: "Vali"
    ,TranslationKeys.SEARCH: "Otsi"
    ,TranslationKeys.WARNING: "Hoiatus"
    ,TranslationKeys.THIS_FIELD_IS_REQUIRED: "See väli on kohustuslik"
    ,TranslationKeys.INVALID_VALUE: "Vigane väärtus"
    ,TranslationKeys.VALUE_MUST_BE_GREATER_THAN_MIN: "Väärtus peab olema suurem kui {min}"
    ,TranslationKeys.VALUE_MUST_BE_LESS_THAN_MAX: "Väärtus peab olema väiksem kui {max}"
    ,TranslationKeys.YES: "Jah"
    ,TranslationKeys.NO: "Ei"
    ,TranslationKeys.OK: "OK"
    ,TranslationKeys.SAVING: "Salvestan"
    ,TranslationKeys.DELETING: "Kustutamine"
    ,TranslationKeys.SUCCESS: "Edu"
    ,TranslationKeys.ERROR: "Viga"
    ,TranslationKeys.PROPERTIES: "Kinnistud"
    ,TranslationKeys.CONTRACTS: "Lepingud"
    ,TranslationKeys.PROJECTS: "Projektid"
    ,TranslationKeys.LETTERS: "Kirjad"
    ,TranslationKeys.SPECIFICATIONS: "Tingimused"
    ,TranslationKeys.EASEMENTS: "Servituudid"
    ,TranslationKeys.COORDINATIONS: "Kooskõlastused"
    ,TranslationKeys.TASKS: "Ülesanded"
    ,TranslationKeys.SUBMISSIONS: "Esitused"
    ,TranslationKeys.ORDINANCES: "Käskkirjad"
    ,TranslationKeys.SELECT_SETTLEMENTS: "Vali asustusüksused"
    ,TranslationKeys.SELECT_PROPERTIES: "Vali kinnistud"
    ,TranslationKeys.CLOSE: "Sulge"
    ,TranslationKeys.SELECT_ALL: "Vali kõik"
    ,TranslationKeys.CLEAR_SELECTION: "Tühjenda valik"
    ,TranslationKeys.ADD_SELECTED: "Lisa valitud"
    ,TranslationKeys.DELETE_BY_ID: "Kustuta ID järgi"
    ,TranslationKeys.SELECT_FROM_MAP: "Vali kaardilt"
    ,TranslationKeys.SELECT_BY_LOCATION_LIST: "Vali asukoha järgi (loend)"
    ,TranslationKeys.RESELECT_FROM_MAP: "Vali uuesti kaardilt"
    ,TranslationKeys.ARCHIVE: "Arhiveeri"
    ,TranslationKeys.UNARCHIVE: "Taasta arhiivist"
    ,TranslationKeys.UNARCHIVE_EXISTING: "Taasta olemasolev"
    ,TranslationKeys.CREATE_NEW: "Loo uus"
    ,TranslationKeys.SKIP: "Jäta vahele"
    ,TranslationKeys.CREATE_LOAD_IN_GPKG: "Loo/lae GPKG-s…"
    ,TranslationKeys.SELECT_COUNTY: "Vali maakond"
    ,TranslationKeys.SELECT_MUNICIPALITY: "Vali omavalitsus"
    ,TranslationKeys.FILTER_BY_LOCATION: "Filtreeri asukoha järgi"
    ,TranslationKeys.SELECTED_PROPERTIES_COUNT: "Valitud: 0 kinnistut"
    ,TranslationKeys.SELECTED_COUNT_TEMPLATE: "Valitud: {count} kinnistut"
    ,TranslationKeys.NO_SELECTION: "Valikut pole"
    ,TranslationKeys.ATTENTION: "Tähelepanu"
    ,ToolbarTranslationKeys.OPEN_FOLDER: "Ava kaust"
    ,ToolbarTranslationKeys.OPEN_ITEM_IN_BROWSER: "Ava kirje brauseris"
    ,ToolbarTranslationKeys.SHOW_ITEMS_ON_MAP: "Näita kirjeid kaardil"
    ,ToolbarTranslationKeys.GENERATE_PROJECT_FOLDER: "Genereeri projekti kaust"
    ,TranslationKeys.PLEASE_SELECT_AT_LEAST_ONE_PROPERTY: "Palun valige vähemalt üks kinnistu."
    ,TranslationKeys.NO_PROPERTY_LAYER_SELECTED: "Kinnistute kihti pole valitud. Palun valige esmalt kinnistute kiht."
    ,TranslationKeys.DATA_LOADING_ERROR: "Andmete laadimise viga"
    ,TranslationKeys.FAILED_TO_LOAD_PROPERTY_DATA: "Andmete laadimine kihist ebaõnnestus."
    ,TranslationKeys.PROPERTIES_ADDED: "Kinnistud lisatud"
    ,TranslationKeys.SELECTED_PROPERTIES_ADDED: "Valitud kinnistud on lisatud."
    ,TranslationKeys.CONNECT_PROPERTIES: "Seosta kinnistuid"
    ,TranslationKeys.CHOSE_FROM_MAP: "Vali kaardilt"
    ,TranslationKeys.SELECT_PROPERTY_FIRST: "Palun valige esmalt kaardilt kinnisvara objekt."
    ,TranslationKeys.ERROR_SELECTING_PROPERTY: "Viga kinnisvara valimisel"
    ,TranslationKeys.SELECT_SINGLE_PROPERTY_TITLE: "Vali üks kinnisvara"
    ,TranslationKeys.SELECT_SINGLE_PROPERTY_MESSAGE: "Palun valige kaardilt ainult üks kinnisvara objekt."
    ,TranslationKeys.MAP_SELECTION_NONE: "Kaardilt ei valitud ühtegi kinnistut."
    ,TranslationKeys.MAP_SELECTION_START_FAILED: "Kinnistute kaardivalikut ei saanud alustada."
    ,TranslationKeys.LINK_PROPERTIES_SUCCESS: "Kinnistute seosed salvestatud projektile {pid}.\nKokku seotud: {count}. {preview}{extra}"
    ,TranslationKeys.LINK_PROPERTIES_MISSING_NOTE: "Puuduvad/ei leitud: {missing}"
    ,TranslationKeys.LINK_PROPERTIES_ERROR: "Kinnistute seostamine projektile {pid} ebaõnnestus.\nOotel valik ({count}): {preview}\n\nDetailid: {err}"
    ,TranslationKeys.MORE_COUNT_SUFFIX: " … (+{count} veel)"
    ,TranslationKeys.LINK_REVIEW_CONNECTIONS_TITLE: "Seosed"
    ,TranslationKeys.LINK_REVIEW_ALREADY_LINKED: "Juba seotud"
    ,TranslationKeys.LINK_REVIEW_NEW_SELECTIONS: "Uued valikud"
    ,TranslationKeys.LINK_REVIEW_RESELECT: "Vali uuesti"
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
    ,TranslationKeys.TEST_LAB: "Test Lab"
    ,TranslationKeys.CONNECTIONS: "Otsin seoseid"
    ,DialogLabels.PROJECTS_SOURCE_FOLDER: "Projektide lähtekaust"
    ,DialogLabels.PROJECTS_TARGET_FOLDER: "Projektide sihtkaust"
    ,DialogLabels.PROJECTS_PHOTO_FOLDER: "Projektide fotode kaust"
    ,DialogLabels.PROJECTS_PREFERED_FOLDER_NAME_STRUCTURE: "Eelistatud kausta nime struktuur"
    ,DialogLabels.PROJECTS_PREFERED_FOLDER_NAME_STRUCTURE_ENABLED: "Luba eelistatud kausta nime struktuur"
    ,DialogLabels.PROJECTS_PREFERED_FOLDER_NAME_STRUCTURE_RULE: "Eelistatud kausta nime struktuuri reegel"
    ,ToolbarTranslationKeys.MORE_ACTIONS: "Rohkem toiminguid"
    ,SettingDialogPlaceholders.UNSET: "Määramata"
    ,FolderNamingTranslationKeys.TR_EMPTY: "Tühi"
    ,FolderNamingTranslationKeys.TR_PROJECT_NUMBER: "Projekti number"
    ,FolderNamingTranslationKeys.TR_PROJECT_NAME: "Projekti nimi"
    ,FolderNamingTranslationKeys.TR_SYMBOL: "sümbol"
    ,FolderNamingTranslationKeys.TR_SYMBOL_TEXT: "sümboli tekst"
    ,FolderNamingTranslationKeys.TR_PREVIEW_PREFIX: "Eelvaade: "
    ,FolderNamingTranslationKeys.TR_PREVIEW_EMPTY: "(tühi)"
    ,FolderNamingTranslationKeys.TR_SYMBOL_REQUIRED: "Sümboli tekst on kohustuslik."
    ,FolderNamingTranslationKeys.TR_SELECT_AT_LEAST_ONE: "Valige vähemalt üks koht."
    ,FolderNamingTranslationKeys.TR_INVALID_RULE: "Vigane reegel"
    ,TranslationKeys.SIGNALTEST: "Signaltest"
    ,TranslationKeys.SIGNALTEST_DESC: "Lae SHP ajamällu ja võrdle selle välju oodatud kinnisvara skeemiga."
    ,TranslationKeys.SIGNALTEST_STEP_LOAD: "Lae SHP mällu"
    ,TranslationKeys.SIGNALTEST_STEP_REVIEW: "Vaata tabelit: loogilised vs kihi väljad"
    ,TranslationKeys.SIGNALTEST_STEP_MAP: "Kui nõutud/valikulised on puudu/joondamata, ava kaardistaja ja joonda"
    ,TranslationKeys.SIGNALTEST_LOAD_BTN: "Lae SHP mällu"
    ,TranslationKeys.SIGNALTEST_MAPPER_BTN: "Ava mapper"
    ,TranslationKeys.SIGNALTEST_PANEL_SCHEMA: "Skeem vs SHP"
    ,TranslationKeys.SIGNALTEST_PANEL_MAIN: "Põhikiht vs SHP"
    ,TranslationKeys.SIGNALTEST_PANEL_ARCHIVE: "Arhiivikiht vs SHP"
    ,TranslationKeys.SIGNALTEST_LEGEND_MAPPED: "Joondatud"
    ,TranslationKeys.SIGNALTEST_LEGEND_MISSING_REQUIRED: "Puudub (nõutud)"
    ,TranslationKeys.SIGNALTEST_LEGEND_UNMAPPED_OPTIONAL: "Joondamata (valikuline)"
    ,TranslationKeys.SIGNALTEST_LEGEND_EXTRA: "Lisa väljad"
    ,TranslationKeys.SIGNALTEST_SUMMARY_TEMPLATE: "Nõutud puudu: {missing_required} | Valikulised joondamata: {missing_optional} | Lisad: {extras}"
    ,TranslationKeys.SIGNALTEST_MAIN_SUMMARY_TEMPLATE: "Puudu põhikihis vs SHP: {missing} | Väljad ainult põhikihis: {extras}"
    ,TranslationKeys.SIGNALTEST_ARCHIVE_SUMMARY_TEMPLATE: "Puudu arhiivkihis vs SHP: {missing} | Väljad ainult arhiivis: {extras}"
    ,TranslationKeys.SIGNALTEST_ARCHIVE_NOT_FOUND: "Arhiivikiht puudub"
        ,TranslationKeys.SIGNALTEST_TABLE_HEADER_LOGICAL: "Standard väljad"
        ,TranslationKeys.SIGNALTEST_TABLE_HEADER_LAYER: "Väljad failis"
        ,TranslationKeys.SIGNALTEST_TABLE_HEADER_STATUS: "Tulemus"
        ,TranslationKeys.SIGNALTEST_TABLE_HEADER_NOTE: "Märkused"
        ,TranslationKeys.SIGNALTEST_FILE_DIALOG_TITLE: "Vali SHP"
        ,TranslationKeys.SIGNALTEST_FILE_DIALOG_FILTER: "Shapefailid (*.shp)"
        ,TranslationKeys.SIGNALTEST_MSG_NO_LAYER_TITLE: "Kiht puudub"
        ,TranslationKeys.SIGNALTEST_MSG_NO_LAYER_BODY: "Laadi kõigepealt SHP."
        ,TranslationKeys.SIGNALTEST_MSG_LOAD_FAIL: "SHP kihti ei õnnestunud laadida."
        ,TranslationKeys.SIGNALTEST_MSG_COPY_FAIL: "SHP kopeerimine mälukihti ebaõnnestus."
        ,TranslationKeys.SIGNALTEST_MSG_COMPARISON_TITLE: "Väljade võrdlus"
        ,TranslationKeys.SIGNALTEST_MSG_COMPARISON_DONE: "Võrdlus valmis. Vaata tulemusi allpool."
        ,TranslationKeys.SIGNALTEST_MSG_MAPPING_SAVED_TITLE: "Kaardistus salvestatud"
        ,TranslationKeys.SIGNALTEST_MSG_MAPPING_SAVED_BODY: "Väljade vastendus salvestati kihile."
        ,TranslationKeys.SIGNALTEST_MSG_MAPPING_NOT_SAVED_TITLE: "Kaardistust ei salvestatud"
        ,TranslationKeys.SIGNALTEST_MSG_MAPPING_NOT_SAVED_BODY: "Muudatusi ei rakendatud."
        ,TranslationKeys.SIGNALTEST_MSG_MISSING_FIELD_TITLE: "Puuduv väli"
        ,TranslationKeys.SIGNALTEST_MSG_MISSING_FIELD_BODY: "Palun kaardista nõutud väli: {field}"
        ,TranslationKeys.SIGNALTEST_STATUS_MAPPED: "Kaardistatud"
        ,TranslationKeys.SIGNALTEST_STATUS_MISSING: "Puudub"
        ,TranslationKeys.SIGNALTEST_STATUS_UNMAPPED: "Mappimata"
        ,TranslationKeys.SIGNALTEST_STATUS_EXTRA: "Lisaväli"
        ,TranslationKeys.SIGNALTEST_NOTE_REQUIRED: "nõutav"
        ,TranslationKeys.SIGNALTEST_NOTE_OPTIONAL: "valikuline"
        ,TranslationKeys.SIGNALTEST_NOTE_EXTRA: "Ainult kihis"
        ,TranslationKeys.SIGNALTEST_NOTE_TARGET_ONLY: "Ainult sihtkihis"
        ,TranslationKeys.SIGNALTEST_LABEL_EXTRA: "<lisaväli>"
        ,TranslationKeys.SIGNALTEST_SOURCE_STORED: "salvestatud kaardistus"
        ,TranslationKeys.SIGNALTEST_SOURCE_AUTO: "automaatne"
        ,TranslationKeys.SIGNALTEST_DIALOG_TITLE: "Väljade kaardistaja"
        ,TranslationKeys.SIGNALTEST_DIALOG_HINT: "Seo plugina loogilised väljad kihis olevate väljadega. Nõutavad väljad on märgitud *.\nVali sobiv SHP väli; <None> jätab kaardistamata (lubatud vaid valikulisel)."
        ,TranslationKeys.SIGNALTEST_NONE_OPTION: "<Puudub>"
        ,TranslationKeys.SIGNALTEST_OPTION_TOOLTIP: "Seo {logical} väljaga {name}"
        ,TranslationKeys.SIGNALTEST_REQUIRED_SUFFIX: " *"
        ,TranslationKeys.SIGNALTEST_LOGICAL_TOOLTIP: "Plugina loogiline väli: {logical}"
}
