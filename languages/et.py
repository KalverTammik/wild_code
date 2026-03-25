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
        TranslationKeys.SETTINGS_PROJECT_BASE_LAYERS_TITLE: "QGIS projekti baaskihid",
        TranslationKeys.SETTINGS_PROJECT_BASE_LAYERS_DESCRIPTION: "Salvesta EVEL-iga ühilduvad baaskihtide viited käesolevasse QGIS projekti. Võimalusel tuvastatakse vanad kihitused, kuid uus seadistus hoiab tuleviku jaoks kihid eraldi.",
        TranslationKeys.SETTINGS_EVEL_LAYER_SETUP_ENABLED: "Mul on EVEL kihistus juba seadistatud",
        TranslationKeys.SETTINGS_PROJECT_BASE_LAYERS_DISABLED: "EVEL automaattuvastus on väljas. Saad kihid käsitsi määrata.",
        TranslationKeys.SETTINGS_PROJECT_BASE_LAYERS_EMPTY: "EVEL baaskihte pole veel seadistatud.",
        TranslationKeys.SETTINGS_BASE_LAYER_WATERPIPES: "Veetorud",
        TranslationKeys.SETTINGS_BASE_LAYER_SEWERPIPES: "Kanalisatsioonitorud",
        TranslationKeys.SETTINGS_BASE_LAYER_PRESSURE_SEWERPIPES: "Survekanalisatsioonitorud",
        TranslationKeys.SETTINGS_BASE_LAYER_RAINWATERPIPES: "Sademeveetorud",
        TranslationKeys.SETTINGS_BASE_LAYER_SEWAGE_PUMPING: "Reoveepumpla",
        TranslationKeys.SETTINGS_BASE_LAYER_SEWAGE_DUMP: "Purgimissõlm",
        TranslationKeys.SETTINGS_BASE_LAYER_SEWAGE_PLANT: "Reoveepuhasti",
        TranslationKeys.SETTINGS_BASE_LAYER_WATER_STATION: "Veejaam",
        TranslationKeys.SETTINGS_BASE_LAYER_RAIN_PUMP: "Sademeveepumpla",
        TranslationKeys.SETTINGS_SHARED_SEWER_MAPPING: "Kasuta üht kanalisatsioonikihti tüüpide ID-kaardistusega",
        TranslationKeys.SETTINGS_SHARED_SEWER_MAPPING_DESCRIPTION: "Kasuta Kanalisatsioonitorud kihti ühise aluskihina ja määra, millised ID-d tähistavad tava-, surve- ja sademeveekanalisatsiooni. Lülita see välja, kui igal tüübil on eraldi kiht.",
        TranslationKeys.SETTINGS_SHARED_SEWER_FIELD: "Tüübi väli",
        TranslationKeys.SETTINGS_SHARED_SEWER_IDS_HINT: "Sisesta üks või mitu ID-d komadega eraldatult.",
        TranslationKeys.SETTINGS_SHARED_SEWER_ADD_ROW: "Lisa kaardistus",
        TranslationKeys.SETTINGS_SHARED_SEWER_OTHER_VALUES: "Kõik muud väärtused",
        TranslationKeys.SETTINGS_SHARED_SEWER_KIND_SEWER: "Kanalisatsioon",
        TranslationKeys.SETTINGS_SHARED_SEWER_KIND_SEWER_PRESSURE: "Kanalisatsioon, surve",
        TranslationKeys.SETTINGS_SHARED_SEWER_KIND_COMBINED: "Ühisvoolne",
        TranslationKeys.SETTINGS_SHARED_SEWER_KIND_COMBINED_PRESSURE: "Ühisvoolne, surve",
        TranslationKeys.SETTINGS_SHARED_SEWER_KIND_RAINWATER: "Sadevesi",
        TranslationKeys.SETTINGS_SHARED_SEWER_KIND_RAINWATER_PRESSURE: "Sadevesi, surve",
        TranslationKeys.SETTINGS_SHARED_SEWER_KIND_DRAINAGE: "Drenaaz",
        TranslationKeys.SETTINGS_SHARED_SEWER_KIND_OTHER: "Muud",
        TranslationKeys.SETTINGS_UTILS_DASH: "—",
        TranslationKeys.ADD_UPDATE_PROPERTY_DIALOG_CANCELLING: "Katkestamine...",
        TranslationKeys.HEADER_WIDGET_ABI: "Abi",
        TranslationKeys.OVERDUE_DUE_SOON_PILLS_ELLIPSIS: "…",
        TranslationKeys.PROGRESS_DIALOG_MODERN_PERCENT: "0%",
        TranslationKeys.SEARCH_RESULTS_WIDGET_CLOSE_TOOLTIP: "Sulge otsingutulemused",
        TranslationKeys.ATTENTION: "Tähelepanu",
        TranslationKeys.SHOW_ONLY_ATTENTION: "Näita ainult tähelepanu vajavaid",
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
        TranslationKeys.DATA_DISPLAY_WIDGETS_EASEMENT_OVERVIEW_TITLE: "Servituudi tegevuste ülevaade",
        TranslationKeys.DATA_DISPLAY_WIDGETS_WORKS_OVERVIEW_TITLE: "Tööde tegevuste ülevaade",
        TranslationKeys.DATA_DISPLAY_WIDGETS_ASBUILT_OVERVIEW_TITLE: "Teostusjooniste tegevuste ülevaade",
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
        TranslationKeys.DATA_DISPLAY_WIDGETS_EASEMENT_DETAIL_CONTENT: """
        <h3>Servituudi Detailne Ülevaade</h3>
        <p>Servituudi elutsükli, seotud kinnistute ja dokumentide seisu ülevaade.</p>
        """,
        TranslationKeys.DATA_DISPLAY_WIDGETS_WORKS_DETAIL_CONTENT: """
        <h3>Tööde Detailne Ülevaade</h3>
        <p>Ülesannete täitmise ja välitööde ülevaade.</p>
        """,
        TranslationKeys.DATA_DISPLAY_WIDGETS_ASBUILT_DETAIL_CONTENT: """
        <h3>Teostusjooniste Detailne Ülevaade</h3>
        <p>Teostusandmete dokumenteerimise ja valideerimise ülevaade.</p>
        """,
        TranslationKeys.HEADER_HELP_BUTTON_TOOLTIP: "Abi",
        TranslationKeys.NO_PROJECTS_FOUND: "Projekte ei leitud",
        TranslationKeys.NO_CONTRACTS_FOUND: "Lepinguid ei leitud",
        TranslationKeys.NO_COORDINATIONS_FOUND: "Kooskõlastusi ei leitud",
        TranslationKeys.NO_EASEMENTS_FOUND: "Servituute ei leitud",
        TranslationKeys.NO_WORKS_FOUND: "Töid ei leitud",
        TranslationKeys.NO_ASBUILT_FOUND: "Teostusjooniseid ei leitud",
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
    TranslationKeys.PROPERTY_BACKEND_ACTION_PROMPT_TITLE: "Vali tegevus",
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
    TranslationKeys.PROPERTY_COPY_FAILED_TITLE: "Kopeerimine ebaõnnestus",
    TranslationKeys.RUN_ATTENTION_CHECKS: "Käivita kontroll",
    TranslationKeys.YES_TO_ALL: "Jah kõigile",
    TranslationKeys.ADD_WITHOUT_CHECKS: "Lisa ilma kontrollita",
    TranslationKeys.OPEN_SETTINGS: "Ava Seaded",
    TranslationKeys.MAIN_PROPERTY_LAYER: "Kinnistute põhikiht",
    TranslationKeys.ARCHIVE_LAYER: "Arhiivikiht",
    TranslationKeys.SELECT_LAYER: "Vali kiht",
    TranslationKeys.PROPERTY_LAYER_OVERVIEW: "See on kinnistute põhikiht.\nVali kiht, mis kajastab ettevõtte peamist kinnistute kaardikihti.",
    TranslationKeys.MODULE_MAIN_LAYER: "Mooduli kiht",
    TranslationKeys.MODULE_LAYER_OVERVIEW: "See on mooduli enda töökiht kaardiga seotud töövoogude jaoks. Seotud kinnistute 'Näita kaardil' tegevus kasutab Kinnistute mooduli põhikihi seadistust.",
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
    TranslationKeys.PROPERTY_NOT_FOUND: "Kinnistu ei leitud",
    TranslationKeys.PROPERTY_MISSING_ON_LAYER: "Kinnistu puudub kihil",
    TranslationKeys.PROPERTY_NOT_FOUND_ON_LAYER: "Kinnistut ei leitud kaardikihilt",
    TranslationKeys.PROPERTY_NOT_SELECTED: "Kinnistu pole valitud",
    TranslationKeys.PROPERTY_CONNECTIONS_LOAD_ERROR: "Viga: {error}",
    TranslationKeys.PROPERTY_CONNECTIONS_LOAD_FAILED_REASON: "Ühenduste laadimisel tekkis viga",
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
    ,TranslationKeys.SELECT_PROPERTIES_MAP_INSTRUCTION: "Vali kaardilt üks või mitu kinnistut peamisest kinnistute kihist.\n\nSeejärel vali tegevus (Arhiveeri/Taasta arhiivist/Kustuta)."
    ,TranslationKeys.NO_SELECTION: "Valikut pole"
    ,TranslationKeys.MISSING_TUNNUS_TITLE: "Tunnus puudub"
    ,TranslationKeys.MISSING_TUNNUS_MESSAGE: "Valitud objektidel puudub katastritunnus."
    ,TranslationKeys.SELECTION_FAILED_TITLE: "Valiku alustamine ebaõnnestus"
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
    ,TranslationKeys.ATTENTION_CAUSE_BACKEND_LOOKUP_FAILED: "taustasüsteemi päring ebaõnnestus"
    ,TranslationKeys.ATTENTION_CAUSE_MISSING_BACKEND: "puudub taustasüsteemis"
    ,TranslationKeys.ATTENTION_CAUSE_ARCHIVED_ONLY: "ainult arhiveeritud kirje"
    ,TranslationKeys.ATTENTION_CAUSE_IMPORT_NEWER: "import on uuem"
    ,TranslationKeys.ATTENTION_CAUSE_MISSING_MAIN_LAYER: "puudub põhikihis"
    ,TranslationKeys.ATTENTION_CAUSE_MAIN_LAYER_OLDER: "põhikiht on vanem"
    ,TranslationKeys.ARCHIVE_MISSING_PROGRESS_START: "Arhiveerin puuduvaid ({count}) enne lisamist..."
    ,TranslationKeys.ARCHIVE_MISSING_PROGRESS_RESULT: "Puuduvad arhiveeritud: taustasüsteem {archived}/{total}, kaardile liigutatud {moved}{errors_suffix}"
    ,TranslationKeys.ARCHIVE_MISSING_PROGRESS_ERROR: "Puuduvate arhiveerimisel ({count}) tekkis viga"
        ,TranslationKeys.ARCHIVE_MISSING_PROGRESS_ERRORS_SUFFIX: " (vigadega)"
    ,TranslationKeys.SELECT_PROPERTY_FIRST: "Palun valige esmalt kaardilt kinnisvara objekt."
    ,TranslationKeys.ERROR_SELECTING_PROPERTY: "Viga kinnisvara valimisel"
    ,TranslationKeys.SELECT_SINGLE_PROPERTY_TITLE: "Vali üks kinnisvara"
    ,TranslationKeys.SELECT_SINGLE_PROPERTY_MESSAGE: "Palun valige kaardilt ainult üks kinnisvara objekt."
    ,TranslationKeys.MAP_SELECTION_NONE: "Kaardilt ei valitud ühtegi kinnistut."
    ,TranslationKeys.MAP_SELECTION_START_FAILED: "Kinnistute kaardivalikut ei saanud alustada."
    ,TranslationKeys.LINK_PROPERTIES_SUCCESS: "Kinnistute seosed salvestatud projektile {pid}.\nKokku seotud: {count}. {preview}{extra}"
    ,TranslationKeys.LINK_PROPERTIES_MISSING_NOTE: "Puuduvad/ei leitud: {missing}"
    ,TranslationKeys.LINK_PROPERTIES_ERROR: "Kinnistute seostamine projektile {pid} ebaõnnestus.\nOotel valik ({count}): {preview}\n\nDetailid: {err}"
        ,TranslationKeys.ASBUILT_UPDATE_NOTES_ACTION: "Lisa/uuenda märkmeid"
        ,TranslationKeys.ASBUILT_UPDATE_NOTES_TITLE: "Lisa/uuenda märkmeid"
        ,TranslationKeys.ASBUILT_UPDATE_NOTES_LABEL: "Märkmed kirjele {name}:"
        ,TranslationKeys.ASBUILT_UPDATE_NOTES_SUCCESS: "Kirje {name} märkmed uuendati."
        ,TranslationKeys.ASBUILT_UPDATE_NOTES_FAILED: "Kirje {name} märkmete uuendamine ebaõnnestus."
        ,TranslationKeys.ASBUILT_NOTES_ADD_NOTE: "Lisa märkus"
        ,TranslationKeys.ASBUILT_NOTES_COLUMN_NOTE: "Märkus"
        ,TranslationKeys.ASBUILT_NOTES_COLUMN_RESOLVED: "Lahendatud"
        ,TranslationKeys.ASBUILT_NOTES_COLUMN_RESOLVED_DATE: "Lahendamise kuupäev"
        ,TranslationKeys.ASBUILT_NOTES_NO_DATE: "Kuupäev puudub"
        ,TranslationKeys.ASBUILT_NOTES_DELETE_ROW: "Kustuta märkus"
        ,TranslationKeys.ASBUILT_NOTES_PLACEHOLDER: "Sisesta märkuse sisu"
        ,TranslationKeys.WORKS_CREATE_ON_MAP_BUTTON: "Lisa UUS töö"
        ,TranslationKeys.WORKS_CREATE_DIALOG_TITLE: "Loo töö"
        ,TranslationKeys.WORKS_CREATE_DIALOG_INTRO: "Vali kaardilt asukoht ja loo sellele punktile uus töö. Kui klikitud asukohast leitakse kinnistu, proovitakse see võimalusel automaatselt siduda."
        ,TranslationKeys.WORKS_CREATE_PROPERTY_LABEL: "Kinnistu"
        ,TranslationKeys.WORKS_CREATE_PROPERTY_NONE: "Selles asukohas kinnistut ei leitud"
        ,TranslationKeys.WORKS_CREATE_COORDINATES_LABEL: "Koordinaadid"
        ,TranslationKeys.WORKS_CREATE_TYPE_LABEL: "Töö liik"
        ,TranslationKeys.WORKS_CREATE_TITLE_LABEL: "Pealkiri"
        ,TranslationKeys.WORKS_CREATE_TITLE_PLACEHOLDER: "Sisesta töö pealkiri"
        ,TranslationKeys.WORKS_CREATE_RESPONSIBLE_LABEL: "Vastutaja"
        ,TranslationKeys.WORKS_CREATE_DESCRIPTION_LABEL: "Lühikirjeldus"
        ,TranslationKeys.WORKS_CREATE_PRIORITY_LABEL: "Prioriteet"
        ,TranslationKeys.WORKS_CREATE_NO_TYPES: "Praegu pole ühtegi töö liiki loomiseks saadaval. Vajadusel kontrolli mooduli liikide seadeid."
        ,TranslationKeys.WORKS_CREATE_VALIDATE_TYPE: "Vali töö liik."
        ,TranslationKeys.WORKS_CREATE_VALIDATE_TITLE: "Sisesta töö pealkiri."
        ,TranslationKeys.WORKS_CREATE_START_FAILED: "Uue töö kaardivalikut ei saanud käivitada."
        ,TranslationKeys.WORKS_LAYER_MISSING: "Tööde kiht on seadistamata või puudub projektist. Palun seadista kõigepealt Seadetes Tööde põhikiht."
        ,TranslationKeys.WORKS_LAYER_INVALID_GEOMETRY: "Seadistatud Tööde kiht peab olema punktikiht, et kaardipõhiseid töid saaks luua."
        ,TranslationKeys.WORKS_LAYER_ID_FIELD_MISSING: "Seadistatud Tööde kihil puudub ülesande id väli ext_job_id."
        ,TranslationKeys.WORKS_CREATE_SUCCESS: "Töö {task_id} loodi edukalt."
        ,TranslationKeys.WORKS_CREATE_MAP_SAVE_FAILED: "Töö {task_id} loodi, kuid kaardiobjekti ei saanud Tööde kihile salvestada. Detailid: {error}"
        ,TranslationKeys.WORKS_CREATE_PROPERTY_LINK_FAILED: "Töö {task_id} loodi ja lisati kaardile, kuid kinnistu seostamine ebaõnnestus tunnusele {cadastral}."
        ,TranslationKeys.WORKS_CREATE_FAILED: "Uue töö loomine ebaõnnestus."
        ,TranslationKeys.WORKS_SHOW_ITEM_ON_MAP_ACTION: "Näita tööd kaardil"
        ,TranslationKeys.WORKS_REPOSITION_ACTION: "Muuda asukohta"
        ,TranslationKeys.EASEMENT_PREVIEW_ACTION: "Ava servituudi eelvaade"
        ,TranslationKeys.EASEMENT_PREVIEW_DIALOG_TITLE: "Servituudi eelvaade"
        ,TranslationKeys.EASEMENT_PREVIEW_INTRO: "Loo servituudi eelvaated kirjele {name} ({number})."
        ,TranslationKeys.EASEMENT_PREVIEW_INSTRUCTIONS: "Seotud kinnistud valitakse automaatselt, seadistatud baaskihtidelt leitakse ristuvad tehnovõrgu objektid ning eelvaatepuhvrid luuakse automaatselt. Eelvaated jäävad ainult mällu ja kustutatakse dialoogi sulgemisel."
        ,TranslationKeys.EASEMENT_PREVIEW_BUFFER_DISTANCE: "Puhvri kaugus"
        ,TranslationKeys.EASEMENT_PREVIEW_LAYER_NAME: "Seadistatud kiht"
        ,TranslationKeys.EASEMENT_PREVIEW_STATUS: "Automaatika"
        ,TranslationKeys.EASEMENT_PREVIEW_CREATE_ACTION: "Loo eelvaade"
        ,TranslationKeys.EASEMENT_PREVIEW_CREATE_FINAL_CUT: "Loo lõplik lõige"
        ,TranslationKeys.EASEMENT_PREVIEW_ROUNDED_CAPS: "Ümardatud nurgad"
        ,TranslationKeys.EASEMENT_PREVIEW_FINAL_AREA: "Lõpliku lõike pindala"
        ,TranslationKeys.EASEMENT_PREVIEW_PROPERTY_AREA_TOTAL: "Arvutatud kinnistupindala kokku"
        ,TranslationKeys.EASEMENT_PREVIEW_CALCULATED_CUT_AREA: "Arvutatud lõike pindala"
        ,TranslationKeys.EASEMENT_PREVIEW_CLEAR_ACTION: "Puhasta eelvaated"
        ,TranslationKeys.EASEMENT_PREVIEW_LAYER_MISSING: "Kiht on seadistamata või seda ei õnnestunud aktiivsest projektist leida."
        ,TranslationKeys.EASEMENT_PREVIEW_NO_SELECTION: "Vali kihil {name} enne vähemalt üks objekt."
        ,TranslationKeys.EASEMENT_PREVIEW_CREATED: "Eelvaatekiht {preview} loodi kihist {source}. Valitud objekte: {count}."
        ,TranslationKeys.EASEMENT_PREVIEW_CLEARED: "Puhastati {count} eelvaatekihti."
        ,TranslationKeys.EASEMENT_PREVIEW_NO_CONNECTED_PROPERTIES: "Sellel servituudil ei ole veel seotud kinnistuid. Vajadusel vali objektid kaardilt käsitsi."
        ,TranslationKeys.EASEMENT_PREVIEW_AUTO_SELECTED: "Seotud kinnistuid valiti: {count}. Automaatselt valitud tehnovõrgu objektid: {layers}."
        ,TranslationKeys.EASEMENT_PREVIEW_ROW_CREATED: "Loodi automaatselt: {count} objekti, {distance} m"
        ,TranslationKeys.EASEMENT_PREVIEW_ROW_SKIPPED: "Jäeti automaatselt vahele: ristuvaid objekte ei leitud"
        ,TranslationKeys.EASEMENT_PREVIEW_ROW_MISSING: "Jäeti automaatselt vahele: kiht on seadistamata"
        ,TranslationKeys.EASEMENT_PREVIEW_ROW_FAILED: "Automaatse eelvaate loomine ebaõnnestus"
        ,TranslationKeys.EASEMENT_PREVIEW_DEFINE_PROPERTIES: "Määra kinnistud kaardilt"
        ,TranslationKeys.EASEMENT_PREVIEW_DEFINE_PROPERTIES_HINT: "Sellel servituudil ei ole veel seotud kinnistuid. Vali kaardilt üks või mitu katastriüksust ja seo need siin."
        ,TranslationKeys.EASEMENT_PREVIEW_LINK_SUCCESS: "Kinnistud seoti servituudiga {pid}. Kokku seotud: {count}. {preview}{extra}"
        ,TranslationKeys.EASEMENT_PREVIEW_LINK_FAILED: "Servituudiga {pid} kinnistute sidumine ebaõnnestus. Valik ({count}): {preview}\n\nDetailid: {err}"
        ,TranslationKeys.EASEMENT_PREVIEW_PROPERTY_SECTION_TITLE: "Seotud kinnistute andmed"
        ,TranslationKeys.EASEMENT_PREVIEW_PROPERTY_SECTION_HINT: "Vaata servituudi-kinnistu seose väljad enne salvestamist üle. Pindala, pinnaühiku hind ja makseandmed saadetakse koos servituudi kinnistuseosega."
        ,TranslationKeys.EASEMENT_PREVIEW_PROPERTY_AREA: "Pindala"
        ,TranslationKeys.EASEMENT_PREVIEW_PROPERTY_UNIT: "Ühik"
        ,TranslationKeys.EASEMENT_PREVIEW_PROPERTY_PRICE: "Hind / ühik"
        ,TranslationKeys.EASEMENT_PREVIEW_PROPERTY_CURRENCY: "Valuuta"
        ,TranslationKeys.EASEMENT_PREVIEW_PROPERTY_TOTAL: "Kokku"
        ,TranslationKeys.EASEMENT_PREVIEW_PROPERTY_PAYABLE: "Tasuline"
        ,TranslationKeys.EASEMENT_PREVIEW_PROPERTY_NEXT_PAYMENT: "Järgmine makse"
        ,TranslationKeys.EASEMENT_PREVIEW_PROPERTY_DATE_PLACEHOLDER: "AAAA-KK-PP"
        ,TranslationKeys.EASEMENT_PREVIEW_PROPERTY_SAVE: "Salvesta servituudi kinnistuandmed"
        ,TranslationKeys.EASEMENT_PREVIEW_PROPERTY_SAVE_SUCCESS: "Servituudi kinnistuandmed salvestati kirjele {pid}. Kokku seotud: {count}. {preview}{extra}"
        ,TranslationKeys.EASEMENT_PREVIEW_PROPERTY_SAVE_FAILED: "Servituudi kinnistuandmete salvestamine kirjele {pid} ebaõnnestus. Valik ({count}): {preview}\n\nDetailid: {err}"
        ,TranslationKeys.EASEMENT_PREVIEW_PROPERTY_INVALID_DATE: "Kinnistu {property} järgmise makse kuupäev peab olema ISO-kujul AAAA-KK-PP."
        ,TranslationKeys.EASEMENT_PREVIEW_FINAL_CREATED: "Lõplik servituudiala eelvaade {preview} loodi {count} ristuva kihi põhjal."
        ,TranslationKeys.EASEMENT_PREVIEW_FINAL_SKIPPED: "Lõplikku servituudiala ei loodud, sest puhverdatud tehnovõrgu alad ei lõikunud valitud kinnistutega."
        ,TranslationKeys.EASEMENT_PREVIEW_FINAL_FAILED: "Lõpliku servituudiala eelvaate loomine ebaõnnestus."
        ,TranslationKeys.EASEMENT_LAYER_MISSING: "Servituudi kiht on seadistamata või puudub projektist. Palun seadista kõigepealt Seadetes Servituudi põhikiht."
        ,TranslationKeys.EASEMENT_LAYER_INVALID_GEOMETRY: "Seadistatud Servituudi kiht peab olema polügoonkiht, et lõpliku lõike geomeetriat salvestada."
        ,TranslationKeys.EASEMENT_LAYER_SAVE_SUCCESS: "Lõplik lõige salvestati Servituudi põhikihile {layer}."
        ,TranslationKeys.EASEMENT_LAYER_SAVE_FAILED: "Lõplikku lõiget ei õnnestunud Servituudi põhikihile salvestada. Detailid: {error}"
        ,TranslationKeys.EASEMENT_PREVIEW_SEWAGE_PUMPING: "Reoveepumpla"
        ,TranslationKeys.EASEMENT_PREVIEW_SEWAGE_DUMP: "Purgimissõlm"
        ,TranslationKeys.EASEMENT_PREVIEW_SEWAGE_PLANT: "Reoveepuhasti"
        ,TranslationKeys.EASEMENT_PREVIEW_WATER_STATION: "Veejaam"
        ,TranslationKeys.EASEMENT_PREVIEW_RAIN_PUMP: "Sademeveepumpla"
        ,TranslationKeys.WORKS_REPOSITION_START_FAILED: "Töö ümberpaigutamise kaardivalikut ei saanud käivitada."
        ,TranslationKeys.WORKS_REPOSITION_FEATURE_NOT_FOUND: "Tööd {task_id} ei leitud seadistatud Tööde kihilt."
        ,TranslationKeys.WORKS_REPOSITION_SAVE_FAILED: "Töö {task_id} uue kaardiasukoha salvestamine ebaõnnestus. Detailid: {error}"
        ,TranslationKeys.WORKS_REPOSITION_SUCCESS: "Töö {task_id} asukoht edukalt uuendatud."
        ,TranslationKeys.WORKS_PRIORITY_NONE: "Prioriteet puudub"
        ,TranslationKeys.WORKS_PRIORITY_LOW: "Madal"
        ,TranslationKeys.WORKS_PRIORITY_MEDIUM: "Keskmine"
        ,TranslationKeys.WORKS_PRIORITY_HIGH: "Kõrge"
        ,TranslationKeys.WORKS_PRIORITY_URGENT: "Kiire"
        ,TranslationKeys.TASK_FILES_ACTION: "Failid"
        ,TranslationKeys.TASK_FILES_DIALOG_TITLE: "Failid — {name}"
        ,TranslationKeys.TASK_FILES_COUNT: "Seotud failid: {count}"
        ,TranslationKeys.TASK_FILES_EMPTY: "Seotud faile veel ei ole."
        ,TranslationKeys.TASK_FILES_COLUMN_NAME: "Nimi"
        ,TranslationKeys.TASK_FILES_COLUMN_SIZE: "Suurus"
        ,TranslationKeys.TASK_FILES_COLUMN_TYPE: "Tüüp"
        ,TranslationKeys.TASK_FILES_COLUMN_UPLOADER: "Laadija"
        ,TranslationKeys.TASK_FILES_COLUMN_CREATED: "Lisatud"
        ,TranslationKeys.TASK_FILES_REFRESH: "Värskenda"
        ,TranslationKeys.TASK_FILES_PREVIEW: "Eelvaade"
        ,TranslationKeys.TASK_FILES_UPLOAD: "Laadi üles"
        ,TranslationKeys.TASK_FILES_OPEN: "Ava väliselt"
        ,TranslationKeys.TASK_FILES_DELETE: "Kustuta"
        ,TranslationKeys.TASK_FILES_NO_SELECTION: "Vali kõigepealt fail."
        ,TranslationKeys.TASK_FILES_LOAD_FAILED: "Failide laadimine kirjele {name} ebaõnnestus."
        ,TranslationKeys.TASK_FILES_PREVIEW_TITLE: "Eelvaade — {name}"
        ,TranslationKeys.TASK_FILES_PREVIEW_UNSUPPORTED: "Selle failitüübi eelvaade pole veel saadaval. Vajadusel ava fail väliselt."
        ,TranslationKeys.TASK_FILES_PREVIEW_TOO_LARGE: "See fail on plugina sees eelvaate jaoks liiga suur. Vajadusel ava fail väliselt."
        ,TranslationKeys.TASK_FILES_PREVIEW_FAILED: "Faili {name} eelvaate laadimine ebaõnnestus."
        ,TranslationKeys.TASK_FILES_PREVIEW_TRUNCATED: "Eelvaates kuvatakse ainult esimesed {count} KB."
        ,TranslationKeys.TASK_FILES_PREVIEW_PAGE_LIMIT: "Eelvaates kuvatakse ainult esimesed {count} lehekülge."
        ,TranslationKeys.TASK_FILES_OPEN_FAILED: "Faili {name} ei saanud avada."
        ,TranslationKeys.TASK_FILES_UPLOAD_DIALOG_TITLE: "Vali üleslaetavad failid"
        ,TranslationKeys.TASK_FILES_UPLOAD_DIALOG_FILTER: "Kõik failid (*.*)"
        ,TranslationKeys.TASK_FILES_UPLOAD_SUCCESS: "Üles laaditi {count} faili."
        ,TranslationKeys.TASK_FILES_UPLOAD_PARTIAL: "Üles laaditi {uploaded} faili. Ebaõnnestus: {failed}. {failed_preview}"
        ,TranslationKeys.TASK_FILES_UPLOAD_FAILED: "Valitud failide üleslaadimine ebaõnnestus."
        ,TranslationKeys.TASK_FILES_DELETE_CONFIRM_TITLE: "Kustuta fail"
        ,TranslationKeys.TASK_FILES_DELETE_CONFIRM_MESSAGE: "Kas kustutada fail {name}?"
        ,TranslationKeys.TASK_FILES_DELETE_SUCCESS: "Fail {name} kustutati."
        ,TranslationKeys.TASK_FILES_DELETE_FAILED: "Faili {name} kustutamine ebaõnnestus."
        ,TranslationKeys.WORKS_TEMP_LAYER_HELPER_TITLE: "Ajutine Tööde kihi abiline"
        ,TranslationKeys.WORKS_TEMP_LAYER_HELPER_DESCRIPTION: "Ajutine arendusabiline. Loob või laeb punktipõhise Tööde kihi kas valitud Tööde viitekihi GeoPackage'i sisse või uude eraldiseisvasse GeoPackage-faili. Loodud kiht määratakse kohe aktiivseks Tööde põhikihiks."
        ,TranslationKeys.WORKS_TEMP_LAYER_CREATE_BUTTON: "Loo/lae ajutine Tööde GPKG kiht"
        ,TranslationKeys.WORKS_TEMP_LAYER_PROMPT_TITLE: "Loo/lae ajutine Tööde kiht"
        ,TranslationKeys.WORKS_TEMP_LAYER_PROMPT_LABEL: "Tööde kihi nimi:"
        ,TranslationKeys.WORKS_TEMP_LAYER_REFERENCE_REQUIRED: "Vali kõigepealt Tööde viitekiht või seadista Kinnistute põhikiht. Abiline vajab olemasolevat kihti, et määrata uue Tööde kihi CRS."
        ,TranslationKeys.WORKS_TEMP_LAYER_GPKG_REQUIRED: "Valitud valik kasutab viitekihi GeoPackage'i, kuid viitekiht ei ole GeoPackage-põhine. Vali Tööde kihi valikust GPKG kiht või kasuta hoopis eraldiseisva GeoPackage'i loomist."
        ,TranslationKeys.WORKS_TEMP_LAYER_STORAGE_TITLE: "Kuhu Tööde kiht salvestada?"
        ,TranslationKeys.WORKS_TEMP_LAYER_STORAGE_MESSAGE: "Vali, kas Tööde kiht luua/laadida viitekihi GeoPackage'i sisse või uue eraldiseisva GeoPackage-failina."
        ,TranslationKeys.WORKS_TEMP_LAYER_STORAGE_EXISTING: "Kasuta viitekihi GeoPackage'i"
        ,TranslationKeys.WORKS_TEMP_LAYER_STORAGE_STANDALONE: "Loo eraldiseisev GeoPackage-fail"
        ,TranslationKeys.WORKS_TEMP_LAYER_SAVE_DIALOG_TITLE: "Vali eraldiseisva Tööde GeoPackage'i asukoht"
        ,TranslationKeys.WORKS_TEMP_LAYER_OVERWRITE_TITLE: "Kas kirjutada olemasolev GeoPackage üle?"
        ,TranslationKeys.WORKS_TEMP_LAYER_OVERWRITE_MESSAGE: "Fail on juba olemas:\n{path}\n\nKas kirjutada see üle ja luua uus eraldiseisev Tööde GeoPackage?"
        ,TranslationKeys.WORKS_TEMP_LAYER_NAME_REQUIRED: "Palun sisesta kihi nimi."
        ,TranslationKeys.WORKS_TEMP_LAYER_CREATE_FAILED: "Ajutise Tööde kihi '{name}' loomine/laadimine ebaõnnestus.\n\nDetailid: {error}"
        ,TranslationKeys.WORKS_TEMP_LAYER_READY: "Ajutine Tööde kiht '{name}' on valmis ja määrati Tööde põhikihiks."
        ,TranslationKeys.WORKS_METADATA_SECTION_TITLE: "Töö metaandmed"
        ,TranslationKeys.WORKS_METADATA_COLUMN_FIELD: "Kihi väli"
        ,TranslationKeys.WORKS_METADATA_COLUMN_VALUE: "Väärtus"
        ,TranslationKeys.WORKS_METADATA_LAYER_NAME: "Kihi nimi"
        ,TranslationKeys.WORKS_METADATA_PROJECT_NAME: "Projekti nimi"
        ,TranslationKeys.WORKS_METADATA_PROJECT_TITLE: "Projekti pealkiri"
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
    ,TranslationKeys.STATUS_WIDGET_CHANGE_TOOLTIP: "Klõpsa staatuse muutmiseks"
    ,TranslationKeys.STATUS_WIDGET_NO_OPTIONS: "Selle mooduli jaoks pole praegu ühtegi staatust saadaval."
    ,TranslationKeys.STATUS_WIDGET_UPDATE_FAILED: "Kirje staatuse uuendamine ebaõnnestus."
    ,TranslationKeys.TEST_LAB: "Test Lab"
    ,TranslationKeys.CONNECTIONS: "Otsin seoseid"
    ,TranslationKeys.EASEMENT_STATUS_MAPPING_TITLE: "Seo servituudi taustastaatused kihiväärtustega"
    ,TranslationKeys.EASEMENT_STATUS_MAPPING_DESCRIPTION: "Määra, kuidas servituudi taustastaatused kirjutatakse seadistatud servituudi põhikihi staatuse väljale. Kiht: {layer}; väli: {field}."
    ,TranslationKeys.EASEMENT_STATUS_MAPPING_LAYER_FIELD: "Sihtkihi staatuse väli: {field}"
    ,TranslationKeys.EASEMENT_STATUS_MAPPING_BACKEND_HEADER: "Taustastaatus"
    ,TranslationKeys.EASEMENT_STATUS_MAPPING_LAYER_HEADER: "Kihi väärtus"
    ,TranslationKeys.EASEMENT_STATUS_MAPPING_NONE_OPTION: "Ära kirjuta"
    ,TranslationKeys.EASEMENT_STATUS_MAPPING_NO_MAIN_LAYER: "Määra esmalt Servituudi põhikiht ja siis ava staatuste seostamine."
    ,TranslationKeys.EASEMENT_STATUS_MAPPING_NO_STATUS_FIELD: "Seadistatud Servituudi põhikihil puudub staatuse väli nagu 'Staatus'."
    ,TranslationKeys.EASEMENT_STATUS_MAPPING_NO_LAYER_VALUES: "Kihi väljal '{field}' ei leitud valitavaid staatuse väärtusi. Lisa esmalt väärtuskaart või näidisväärtused."
    ,TranslationKeys.EASEMENT_STATUS_MAPPING_NO_BACKEND_STATUSES: "Servituudi taustastaatusi ei õnnestunud laadida."
    ,TranslationKeys.EASEMENT_STATUS_MAPPING_SUMMARY: "{count} seotud: {preview}"
    ,TranslationKeys.EASEMENT_STATUS_MAPPING_SUMMARY_EMPTY: "Staatuste seost pole määratud"
    ,DialogLabels.PROJECTS_SOURCE_FOLDER: "Projektide lähtekaust"
    ,DialogLabels.PROJECTS_TARGET_FOLDER: "Projektide sihtkaust"
    ,DialogLabels.PROJECTS_PHOTO_FOLDER: "Projektide fotode kaust"
    ,DialogLabels.PROJECTS_PREFERED_FOLDER_NAME_STRUCTURE: "Eelistatud kausta nime struktuur"
    ,DialogLabels.PROJECTS_PREFERED_FOLDER_NAME_STRUCTURE_ENABLED: "Luba eelistatud kausta nime struktuur"
    ,DialogLabels.PROJECTS_PREFERED_FOLDER_NAME_STRUCTURE_RULE: "Eelistatud kausta nime struktuuri reegel"
    ,DialogLabels.EASEMENT_LAYER_STATUS_MAPPING: "Servituudi kihi staatuste seos"
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
}
