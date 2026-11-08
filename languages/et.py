from .translation_keys import (
    TranslationKeys,
    ToolbarTranslationKeys,
    DialogLabels,
    FolderNamingTranslationKeys,
    SettingDialogPlaceholders,
)

TRANSLATIONS = {
        TranslationKeys.LIST_SORT: "Sordi",
        TranslationKeys.LIST_GROUP: "Grupeeri",
        TranslationKeys.LIST_SORT_DEFAULT: "Vaikimisi järjekord",
        TranslationKeys.LIST_GROUP_NONE: "Grupeerimata",
        TranslationKeys.LIST_SORT_GLOBAL: "Kogu filtreeritud tulemus",
        TranslationKeys.LIST_SORT_LOCAL: "Laaditud kannetes",
        TranslationKeys.LIST_SORT_TITLE: "Pealkiri",
        TranslationKeys.LIST_SORT_DUE: "Tähtaeg",
        TranslationKeys.LIST_SORT_START: "Algusaeg",
        TranslationKeys.LIST_SORT_CREATED: "Loomise aeg",
        TranslationKeys.LIST_SORT_UPDATED: "Muutmise aeg",
        TranslationKeys.LIST_SORT_STATUS: "Staatus",
        TranslationKeys.LIST_SORT_TYPE: "Liik",
        TranslationKeys.LIST_SORT_PRIORITY: "Prioriteet",
        TranslationKeys.LIST_SORT_RESPONSIBLE: "Vastutaja",
        TranslationKeys.LIST_SORT_ASC_TEXT: "A–Z",
        TranslationKeys.LIST_SORT_DESC_TEXT: "Z–A",
        TranslationKeys.LIST_SORT_ASC_DATE: "Varasem ees",
        TranslationKeys.LIST_SORT_DESC_DATE: "Hilisem ees",
        TranslationKeys.LIST_SORT_ASC_PRIORITY: "Kõrgem ees",
        TranslationKeys.LIST_SORT_DESC_PRIORITY: "Madalam ees",
        TranslationKeys.LIST_GROUP_DEADLINE: "Tähtaja seis",
        TranslationKeys.LIST_GROUP_SCOPE: "Grupid põhinevad laaditud kannetel. Arvud täienevad laadimisel.",
        TranslationKeys.LIST_GROUP_COUNT: "{name} · {count} laaditud",
        TranslationKeys.LIST_VALUE_MISSING: "Määramata",
        TranslationKeys.LIST_DEADLINE_OVERDUE: "Üle tähtaja",
        TranslationKeys.LIST_DEADLINE_TODAY: "Täna",
        TranslationKeys.LIST_DEADLINE_TOMORROW: "Homme",
        TranslationKeys.LIST_DEADLINE_WEEK: "Sel nädalal",
        TranslationKeys.LIST_DEADLINE_NEXT_WEEK: "Järgmisel nädalal",
        TranslationKeys.LIST_DEADLINE_LATER: "Hiljem",
        TranslationKeys.LIST_DEADLINE_CLOSED: "Lõpetatud",
        TranslationKeys.LIST_DEADLINE_NONE: "Tähtajata",
        TranslationKeys.LIST_GROUP_EXPAND_ALL: "Ava kõik grupid",
        TranslationKeys.LIST_GROUP_COLLAPSE_ALL: "Sulge kõik grupid",
        TranslationKeys.LIST_LOCAL_NOTICE: "Sortimine: laaditud kannetes",
        TranslationKeys.LIST_GROUP_NOTICE: "Grupid: laaditud kanded",
        TranslationKeys.LIST_UNIQUE_COUNT: "{count} unikaalset kannet laaditud",
        TranslationKeys.CARD_LOAD_RETRY: "Proovi uuesti",
        TranslationKeys.CARD_DETAIL_LOAD_FAILED: "Detailide laadimine ebaõnnestus.",
        TranslationKeys.CARD_DETAIL_OPEN: "Ava detailid",
        TranslationKeys.CARD_DETAIL_CLOSE: "Sule detailid",
        TranslationKeys.CARD_RESPONSIBLE_UNASSIGNED: "Vastutaja määramata",
        TranslationKeys.CARD_MEMBERS_OPEN: "Vaata liikmeid",
        TranslationKeys.CARD_MEMBERS_EMPTY: "Liikmeid pole lisatud.",
        TranslationKeys.CARD_FILES_VIEW_ALL: "Vaata kõiki faile ({count})",
        TranslationKeys.MAP_IDENTIFY_BUTTON: "Mis see on",
        TranslationKeys.MAP_IDENTIFY_UNSUPPORTED_MODULE: "Aktiivne moodul {module} ei toeta praegu kaardilt tuvastamist.",
        TranslationKeys.MAP_IDENTIFY_LAYER_MISSING: "Mooduli {module} pĆµhikiht on seadistamata vĆµi puudub projektist.",
        TranslationKeys.MAP_IDENTIFY_ID_FIELD_MISSING: "Valitud kihilt {layer} ei leitud vĆ¤lja, mille jĆ¤rgi Kavitro elementi avada.",
        TranslationKeys.MAP_IDENTIFY_FEATURE_MISSING: "Selles kohas ei leitud aktiivse mooduli objekti.",
        TranslationKeys.MAP_IDENTIFY_OPEN_FAILED: "Objekti avamine Kavitro moodulis ebaĆµnnestus.",
        # Added from translation audit (UI literals)
        TranslationKeys.FOLDER_NAMING_RULE_DIALOG_TITLE: "Kausta nimetamise reegel",
        TranslationKeys.SETTINGS_BASE_CARD_TEXT: "Seaded",
        TranslationKeys.SETTINGS_PROJECT_BASE_LAYERS_TITLE: "QGIS projekti baaskihid",
        TranslationKeys.SETTINGS_PROJECT_BASE_LAYERS_DESCRIPTION: "Salvesta EVEL-iga ühilduvad baaskihtide viited käesolevasse QGIS projekti. Võimalusel tuvastatakse vanad kihitused, kuid uus seadistus hoiab tuleviku jaoks kihid eraldi.",
        TranslationKeys.SETTINGS_EVEL_LAYER_SETUP_ENABLED: "Mul on EVEL kihistus juba seadistatud",
        TranslationKeys.SETTINGS_PROJECT_BASE_LAYERS_EMPTY: "EVEL baaskihte pole veel seadistatud.",
        TranslationKeys.SETTINGS_GEOSPATIAL_MODE_VALUE: "Seadistusrežiim: {mode}",
        TranslationKeys.SETTINGS_GEOSPATIAL_MODE_MANUAL: "Käsitsi seadistus",
        TranslationKeys.SETTINGS_GEOSPATIAL_MODE_ACTIVE: "Geospatiali abiga seadistus",
        TranslationKeys.SETTINGS_GEOSPATIAL_STATUS_MANUAL: "Projekti baaskihtide käsitsi seadistus on aktiivne.",
        TranslationKeys.SETTINGS_GEOSPATIAL_STATUS_ACTIVE: "Geospatiali abiga seadistus on aktiivne. Projekti baaskihtide käsitsi väljad on peidetud kuni naased käsitsi seadistusse.",
        TranslationKeys.SETTINGS_GEOSPATIAL_CONNECT_BUTTON: "Ühenda Geospatiali kaudu",
        TranslationKeys.SETTINGS_GEOSPATIAL_MANAGE_BUTTON: "Vaata Geospatiali seadistust",
        TranslationKeys.SETTINGS_GEOSPATIAL_DIALOG_TITLE: "Geospatiali abiga seadistus",
        TranslationKeys.SETTINGS_GEOSPATIAL_DIALOG_BODY: "See voog hakkab hiljem seadistama projekti baaskihid ja seotud vaikimisi väärtused automaatselt nende klientide jaoks, kes kasutavad Geospatiali teenuseid. Praegu peidab selle režiimi sisselülitamine käsitsi projekti baaskihtide väljad ja reserveerib selle ala juhitud integratsioonivoo jaoks.",
        TranslationKeys.SETTINGS_GEOSPATIAL_DIALOG_SCOPE: "Praegune vahe-etapp ei kirjuta veel automaatseid kihiseadistusi. Käsitsi seadistusse saab igal ajal tagasi minna.",
        TranslationKeys.SETTINGS_GEOSPATIAL_DISABLE_TITLE: "Kas lülitada Geospatiali abiga seadistus välja?",
        TranslationKeys.SETTINGS_GEOSPATIAL_DISABLE_BODY: "Kui lülitad Geospatiali abiga seadistuse välja, eemaldatakse kõik salvestatud Geospatiali seadistused. Pärast seda saad eelistatud väljad käsitsi seadistada või need ise Seadetes lähtestada.",
        TranslationKeys.SETTINGS_MAP_OVERLAY_TITLE: "Tööriistad",
        TranslationKeys.SETTINGS_MAP_OVERLAY_DESCRIPTION: "Näita kiireid otse juurdepääse",
        TranslationKeys.SETTINGS_MAP_OVERLAY_GLASS_BAR: "Sisestuspaan",
        TranslationKeys.SETTINGS_MAP_OVERLAY_SEARCH_BAR: "Otsingupaan",
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
        TranslationKeys.SHOW_ONLY_ATTENTION: "Näita ainult tähelepanu vajavaid",
        TranslationKeys.SIDEBAR_LEFT_ARROW: "«",
        TranslationKeys.SIDEBAR_RIGHT_ARROW: "»",
        TranslationKeys.DATA_DISPLAY_WIDGETS_INFOCARDHEADER_TOOLTIP: "Privaatne",
        TranslationKeys.DATA_DISPLAY_WIDGETS_DATES_EMPTY: "Kuupäevad puuduvad",
        TranslationKeys.DATA_DISPLAY_WIDGETS_COLUMN_DONE: "Tehtud",
        TranslationKeys.DATA_DISPLAY_WIDGETS_COLUMN_IN_PROGRESS: "Töös",
        TranslationKeys.PROJECT_BOARD_DETAILS_LOAD_HINT: "Ava silmaikoon, et laadida projektiga seotud moodulite edenemise detailid.",
        TranslationKeys.PROJECT_BOARD_DETAILS_EMPTY_DONE: "Ühtegi seotud mooduli kirjet ei paista veel lõpetatuna.",
        TranslationKeys.PROJECT_BOARD_DETAILS_EMPTY_IN_PROGRESS: "Ühtegi seotud mooduli kirjet ei liigitatud praegu töös olevaks.",
        TranslationKeys.PROJECT_BOARD_DETAILS_EMPTY_TODO: "Ühtegi seotud mooduli kirjet ei liigitatud praegu alustamata olekusse.",
        TranslationKeys.PROJECT_BOARD_COLUMN_NOT_STARTED: "Alustamata",
        TranslationKeys.DATA_DISPLAY_WIDGETS_TERMS_HEADING: "Tingimused",
        TranslationKeys.HEADER_HELP_BUTTON_TOOLTIP: "Abi",
        TranslationKeys.NO_PROJECTS_FOUND: "Projekte ei leitud",
        TranslationKeys.NO_CONTRACTS_FOUND: "Lepinguid ei leitud",
        TranslationKeys.NO_COORDINATIONS_FOUND: "Kooskõlastusi ei leitud",
        TranslationKeys.NO_EASEMENTS_FOUND: "Servituute ei leitud",
        TranslationKeys.NO_WORKS_FOUND: "Töid ei leitud",
        TranslationKeys.NO_ASBUILT_FOUND: "Teostusjooniseid ei leitud",
        TranslationKeys.NO_VALUES_FOUND: "Väärtusi ei leitud!",
        TranslationKeys.LOADING: "Laadimine…",
        TranslationKeys.LOCATION_LOADING_CHOICES: "Laen maakonna omavalitsuste ja külade valikuid…",
        TranslationKeys.LOCATION_LOADING_PROPERTIES: "Laen kinnistuid ja kaardivaadet…",
        TranslationKeys.LOCATION_LOADING_MAP: "Uuendan kaardivaadet…",
        TranslationKeys.LOCATION_PROPERTIES_READY: "Laaditud {count} kinnistut.",
        TranslationKeys.LOCATION_NO_CHOICES: "Impordikihis puuduvad asukohavalikud.",
        TranslationKeys.LOCATION_LOAD_FAILED: "Asukohaandmete laadimine ebaõnnestus. Proovi uuesti.",
        TranslationKeys.LOCATION_MAP_FAILED: "Kaardivaate uuendamine ebaõnnestus. Proovi uuesti.",
        TranslationKeys.LOCATION_REFRESH: "Värskenda tabelit ja kaardivaadet praeguste asukohavalikute järgi",
        TranslationKeys.PROPERTY_ADD_RESULT: "Töödeldud {done}/{total}. Õnnestus: {succeeded}. Ebaõnnestus: {failed}.",
        TranslationKeys.PROPERTY_IMPORT_CHANGED: "Andmed on pärast ülevaatust muutunud. Vaata värsked andmed üle ja otsusta uuesti.",
        TranslationKeys.PROPERTY_IMPORT_REVIEW: "Vaata otsust ootavaid kinnistuid ({count})",
        TranslationKeys.PROPERTY_IMPORT_REVIEW_TITLE: "Otsust ootavad kinnistud",
        TranslationKeys.PROPERTY_IMPORT_REVIEW_INTRO: "Siin on otsust ootama jäänud kinnistud. Vali iga kinnistu tegevus; „Jäta hilisemaks” säilitab selle nimekirjas kuni selle haldusakna sulgemiseni.",
        TranslationKeys.PROPERTY_IMPORT_LATER: "Jäta hilisemaks",
        TranslationKeys.PROPERTY_IMPORT_KEEP: "Säilita olemasolev",
        TranslationKeys.PROPERTY_IMPORT_APPLY: "Rakenda impordi andmed",
        TranslationKeys.PROPERTY_IMPORT_CONFIRM: "Rakenda valitud otsused",
        TranslationKeys.PROPERTY_IMPORT_ACTION: "Tegevus",
        TranslationKeys.PROPERTY_IMPORT_REASON: "Põhjus",
        TranslationKeys.PROPERTY_IMPORT_DETAILS: "Katastritunnus: {tunnus}\n\nImpordi aadress: {import_address}\nImpordi muutmise aeg: {import_date}\n\nTaustasüsteemi aadress: {backend_address}\nTaustasüsteemi katastriandmete muutmise aeg: {backend_date}\n\nPõhikihi aadress: {main_address}\nPõhikihi muutmise aeg: {main_date}",
        TranslationKeys.PROPERTY_IMPORT_WRITE_SCOPE: "„Rakenda impordi andmed” uuendab taustasüsteemis kinnistu numbrit, katastriandmeid, aadressi, pindala ja sihtotstarbeid. Olemasolev põhikihi objekt säilib; puuduv objekt kopeeritakse importkihist. „Säilita olemasolev” jätab selle kinnistu nii taustasüsteemis kui ka kaardil muutmata. Arhiveeritud ja mitme vastega kirjed vajavad eraldi ülevaatamist.",
        TranslationKeys.PROPERTY_IMPORT_UNKNOWN: "Puudub või teadmata",
        TranslationKeys.PROPERTY_IMPORT_SUMMARY: "Otsust ootab: {deferred}. Säilitati olemasolev: {kept}.",
        TranslationKeys.PROPERTY_IMPORT_MATCHES: "Taustasüsteemi vasted: {matches}",
        TranslationKeys.PROPERTY_ADD_BACKEND_DIFFERS: "Taustasüsteemi aadress erineb ja impordi uuemust ei saa kinnitada. Vajab otsust; andmeid ei kirjutata automaatselt üle.",
        TranslationKeys.PROPERTY_ADD_UNFINISHED: "Kinnistu töötlemine jäi pooleli. Enne uuesti lisamist kontrolli taustasüsteemi seisu.",
        TranslationKeys.PROPERTY_ADD_STAGE_CANCELLED: "{stage} jäi pooleli. Varasem etapp võis juba salvestuda; enne jätkamist kontrolli kinnistut uuesti.",
        TranslationKeys.API_RATE_LIMIT_WAIT: "Serveri päringupiirang (HTTP 429). Enne jätkamist tuleb oodata.",
        TranslationKeys.API_REQUEST_TITLE: "Kavitro päring",
        TranslationKeys.PROPERTY_BACKEND_PENDING: "Taustasüsteemis töötlemata kinnistud: {tunnused}",
        TranslationKeys.PROPERTY_DELETE_STOPPED: "Kustutamine peatus kinnistul {tunnus}: {error}\nJärgmised kinnistud jäid töötlemata: {pending}\nKaardikihti ei kustutatud. Varasemad taustasüsteemi kustutamised võivad olla lõpetatud; kontrolli enne jätkamist tulemusi.",
        TranslationKeys.PROPERTY_DELETE_FAILED: "Kustutamine ebaõnnestus",
        TranslationKeys.PROPERTY_DELETED_TITLE: "Kustutatud",
        TranslationKeys.PROPERTY_DELETED_MESSAGE: "Kinnistu on kustutatud.",
        TranslationKeys.PROPERTY_MAIN_LAYER_MISSING: "Kinnistute põhikiht on seadistamata või projektist puudu.",
        TranslationKeys.GEOMETRY_FORM_CANCEL: "Katkesta",
        TranslationKeys.ERROR_DETAILS: "Viga: {error}",
        TranslationKeys.SEARCH_FAILED: "Otsing ebaõnnestus",
        TranslationKeys.SEARCH_STATUS_SEARCHING: "Otsin „{term}“…",
        TranslationKeys.SEARCH_OPEN_NOT_AVAILABLE_TITLE: "Pole saadaval",
        TranslationKeys.SEARCH_OPEN_NOT_AVAILABLE_MESSAGE: "Seda moodulit ei saa veel otsingust avada.",
        TranslationKeys.SEARCH_SHOW_MORE: "  -- Näita veel {count} --",
        TranslationKeys.FEED_COUNTER_LOADED: "Laaditud {loaded}",
        TranslationKeys.FEED_COUNTER_LOADED_OF: "Laaditud {loaded} / {total}",
        TranslationKeys.TASK_FILE_LOCAL_FILE: "Kohalik fail",
        TranslationKeys.LAYER_IMPORT_PROGRESS: "Objektide töötlemine: {done}/{total} ({percent}%)",
        TranslationKeys.LAYER_IMPORT_COPIED: "Kopeeritud objekte: {count}",
        TranslationKeys.LAYER_IMPORT_IMPORTED: "Imporditud objekte: {count}",
        TranslationKeys.EASEMENT_MAIN_LAYER_AMBIGUOUS: "Servituutide põhikiht ei ole üheselt määratud. Vali seadetes servituutide põhikiht uuesti.",
        TranslationKeys.FOLDER_COPY_SUCCESS: "Kausta '{source}'\n(k.a kaustas sisalduvad alamkaustad ja failid) dubleerimine õnnestus.\n\nSihtkohta on genereeritud kaust nimetusega \n'{folder}'.",
        TranslationKeys.PROPERTY_SUMMARY_TITLE: "Kinnistu andmed",
        TranslationKeys.PROPERTY_SUMMARY_CADASTRAL: "Katastritunnus:",
        TranslationKeys.PROPERTY_SUMMARY_REGISTRY: "(reg.nr:)",
        TranslationKeys.PROPERTY_SUMMARY_ADDRESS: "Aadress:",
        TranslationKeys.PROPERTY_SUMMARY_AREA: "Pindala (m²):",
        TranslationKeys.PROPERTY_SUMMARY_PURPOSE: "Siht {index}:",
        TranslationKeys.PROPERTY_SUMMARY_REGISTERED: "Moodustatud:",
        TranslationKeys.PROPERTY_SUMMARY_UPDATED: "Viimati muudetud:",
        TranslationKeys.PROPERTY_ACTION_UNKNOWN_TITLE: "Tundmatu toiming",
        TranslationKeys.PROPERTY_ACTION_MISSING_MESSAGE: "Toimingut ei antud.",
        TranslationKeys.PROPERTY_ACTION_UNSUPPORTED_MESSAGE: "Toimingut '{action}' ei toetata.",
        TranslationKeys.PROPERTY_ACTION_MISSING_TUNNUS_TITLE: "Katastritunnus puudub",
        TranslationKeys.PROPERTY_ACTION_MISSING_TUNNUS_MESSAGE: "Valitud objektidel puudub katastritunnus.",
        TranslationKeys.PROPERTY_ACTION_ARCHIVE_TITLE: "Arhiveerimine taustasüsteemis",
        TranslationKeys.PROPERTY_ACTION_ARCHIVE_PARTIAL_TITLE: "Arhiveerimine taustasüsteemis (osaliselt)",
        TranslationKeys.PROPERTY_ACTION_ARCHIVE_SUMMARY: "Taustasüsteemis arhiveeritud: {succeeded}; vahele jäetud: {skipped}; ebaõnnestus: {failed}",
        TranslationKeys.PROPERTY_ACTION_UNARCHIVE_TITLE: "Arhiivist taastamine taustasüsteemis",
        TranslationKeys.PROPERTY_ACTION_UNARCHIVE_PARTIAL_TITLE: "Arhiivist taastamine taustasüsteemis (osaliselt)",
        TranslationKeys.PROPERTY_ACTION_UNARCHIVE_SUMMARY: "Taustasüsteemis arhiivist taastatud: {succeeded}; vahele jäetud: {skipped}; ebaõnnestus: {failed}",
        TranslationKeys.PROPERTY_ACTION_DELETE_TITLE: "Kustutamine",
        TranslationKeys.PROPERTY_ACTION_DELETE_PARTIAL_TITLE: "Kustutamine (osaliselt)",
        TranslationKeys.PROPERTY_ACTION_DELETE_ATTEMPTED: "Taustasüsteemis kustutamiseks saadetud: {count}",
        TranslationKeys.PROPERTY_ACTION_DELETE_MATCHED: "Põhikihil leitud: {count}",
        TranslationKeys.PROPERTY_ACTION_DELETE_DELETED: "Põhikihilt kustutatud: {count}",
        TranslationKeys.PROPERTY_ACTION_FAILED_TITLE: "Taustasüsteemi toiming ebaõnnestus",
        TranslationKeys.EASEMENT_FORM_TITLE: "Servituudi ala andmed",
        TranslationKeys.EASEMENT_FORM_INTRO: "Täida servituudi ala kihiandmed enne ala salvestamist. Muudetud staatus salvestatakse ka Kavitrosse. Automaatika täidab seose, pindala ja logiväljad, kui need on arvutatavad.",
        TranslationKeys.EASEMENT_FORM_TAB_DATA: "Andmed",
        TranslationKeys.EASEMENT_FORM_TAB_LOCATION: "Asukoht",
        TranslationKeys.EASEMENT_FORM_STATUS_TOOLTIP: "Muudetud staatus salvestatakse Kavitrosse ja kaardikihile.",
        TranslationKeys.EASEMENT_FORM_DATE_TOOLTIP: "Kuupäev salvestatakse, kui staatusele vastab kihil väärtus {status}.",
        TranslationKeys.EASEMENT_FORM_STATUS_MAP_UNCHANGED: "{label} (kaardil ei muutu)",
        TranslationKeys.EASEMENT_FORM_STATUS_MAP_VALUE: "{label} (kaardil: {value})",
        TranslationKeys.EASEMENT_FORM_STATUS_REJECTED_TITLE: "Staatust ei muudetud",
        TranslationKeys.EASEMENT_FORM_STATUS_REJECTED_MESSAGE: "Kavitro ei võtnud uut staatust vastu, seega kaardile ei salvestatud midagi. Proovi uuesti või vali tagasi algne staatus.",
        TranslationKeys.EASEMENT_FIELD_KIND: "Liik",
        TranslationKeys.EASEMENT_FIELD_STATUS: "Staatus",
        TranslationKeys.EASEMENT_FIELD_NOTARY_NUMBER: "Notari reg nr",
        TranslationKeys.EASEMENT_FIELD_LAND_OWNER: "Maa omanik",
        TranslationKeys.EASEMENT_FIELD_CADASTRAL: "Katastritunnus",
        TranslationKeys.EASEMENT_FIELD_PHONE: "Telefon",
        TranslationKeys.EASEMENT_FIELD_EMAIL: "E-kiri",
        TranslationKeys.EASEMENT_FIELD_NOTE: "Märkus",
        TranslationKeys.EASEMENT_FIELD_ESTABLISHED_DATE: "Kehtestamise kuupäev",
        TranslationKeys.EASEMENT_FIELD_SOURCE: "Allikas",
        TranslationKeys.EASEMENT_FIELD_NETWORK: "Võrk",
        TranslationKeys.EASEMENT_FIELD_PROTECTION_WIDTH: "Kaitsevööndi laius",
        TranslationKeys.EASEMENT_FIELD_COMPENSATION: "Talumistasu",
        TranslationKeys.EASEMENT_FIELD_MUNICIPALITY: "Vald",
        TranslationKeys.EASEMENT_FIELD_REGION: "Piirkond",
        TranslationKeys.EASEMENT_FIELD_ADDRESS: "Aadress",
        TranslationKeys.EASEMENT_FIELD_HOUSE_NUMBER: "Maja nr",
        TranslationKeys.ASBUILT_FORM_TITLE: "Teostusjoonise andmed",
        TranslationKeys.ASBUILT_FORM_INTRO: "Täida kaardile joonistatud teostusjoonise ala põhiandmed. Need väärtused salvestatakse QGIS kihile enne backend geomeetria uuendamist.",
        TranslationKeys.ASBUILT_FIELD_WORK_NUMBER: "Töö nr",
        TranslationKeys.ASBUILT_FIELD_OBJECT: "Objekt",
        TranslationKeys.ASBUILT_FIELD_SURVEY_DATE: "Mõõdistamise kpv",
        TranslationKeys.ASBUILT_FIELD_SURVEYOR: "Mõõdistaja",
        TranslationKeys.ASBUILT_FIELD_CONTACT: "Kontakt",
        TranslationKeys.ASBUILT_FIELD_DRAWING: "Joonis",
        TranslationKeys.ASBUILT_FIELD_SCALE: "Mõõtkava",
        TranslationKeys.ASBUILT_FIELD_COORDINATE_SYSTEM: "Koordinaatsüsteem",
        TranslationKeys.ASBUILT_FIELD_HEIGHT_SYSTEM: "Kõrgussüsteem",
        TranslationKeys.ASBUILT_FIELD_NETWORK: "Võrk",
        TranslationKeys.ASBUILT_FIELD_NOTES: "Märkused",
        TranslationKeys.ASBUILT_FORM_NOTES_PLACEHOLDER: "Mõõdistaja märkused",
        TranslationKeys.ASBUILT_DRAWING_ASBUILT: "Teostusjoonis",
        TranslationKeys.ASBUILT_DRAWING_BASE: "Geoalus",
        TranslationKeys.ASBUILT_COORDINATES_TARTU: "Tartu kohalik",
        TranslationKeys.ASBUILT_NETWORK_WATER: "Vesi",
        TranslationKeys.ASBUILT_NETWORK_SEWER: "Kanal",
        TranslationKeys.ASBUILT_NETWORK_STORMWATER: "Sadevesi",
        TranslationKeys.ASBUILT_NETWORK_ELECTRICITY: "Elekter ja tänavavalgustus",
        TranslationKeys.ASBUILT_NETWORK_GAS: "Gaas",
        TranslationKeys.ASBUILT_NETWORK_TELECOM: "Side",
        TranslationKeys.PROPERTY_ARCHIVE_PENDING: "Taustasüsteemi arhiveerimine peatus. Kaardi arhiivikoopiad on säilinud. Järgmiste kinnistute taustasüsteemi toiming jäi tegemata: {tunnused}",
        TranslationKeys.TASK_FILES_UPLOAD_STOPPED: "Failide lisamine peatus. Lisatud: {uploaded}. Faili „{failed}” salvestamist ei kinnitatud; kontrolli failide loendit enne korduskatset. Saatmata: {pending}.\n{pending_names}",
        TranslationKeys.WORKS_GEOMETRY_SYNC_STOPPED: "Geomeetriate salvestamine Kavitrosse peatus kaardiobjekti {feature_id} juures. Järgmisi objekte jäi töötlemata: {pending}. Kaardimuudatused on alles, kuid nende jõudmine Kavitrosse vajab kontrollimist.",
        TranslationKeys.API_REQUEST_RUNNING: "Suhtlen Kavitroga…",
        TranslationKeys.API_REQUEST_RATE_WAIT: "Serveri päringupiirang. Jätkan automaatselt {seconds} s pärast sama päringuga.",
        TranslationKeys.API_REQUEST_PACING_WAIT: "Ootan päringute vahel {seconds} s, et vältida serveri piirangut. Jätkan automaatselt.",
        TranslationKeys.API_REQUEST_CANCELLED: "Päring katkestati enne saatmist. Varasemad toimingud võivad olla salvestatud; enne jätkamist kontrolli tulemust.",
        TranslationKeys.API_REQUEST_CANCELLING: "Katkestan ootamise. Juba saadetud päringu puhul ootan vastuse ära…",
        TranslationKeys.API_RATE_LIMIT_REQUEST_TOO_LARGE: "Päring ületab muutmistoimingute piiri (HTTP 429). Päring tuleb jagada väiksemateks osadeks; ootamine seda viga ei lahenda.",
        TranslationKeys.PROPERTY_ADD_RATE_WAIT: "Kinnistu {tunnus}: serveri päringupiirang. Jätkan automaatselt {seconds} s pärast sama salvestusega.",
        TranslationKeys.PROPERTY_ADD_PACING_WAIT: "Kinnistu {tunnus}: salvestamine jätkub {seconds} s pärast.",
        TranslationKeys.PROPERTY_CHECK_CANCELLED: "Kontroll katkestati. Kontrollitud {done}/{total} kinnistut. Valitud kinnistute lisamiseks käivita kontroll uuesti.",
        TranslationKeys.PROPERTY_ARCHIVE_LOOKUP_PROGRESS: "Kontrollin impordist puuduvate kinnistute seisu taustasüsteemis: {done}/{total}. Arhiveerimiskava avaneb pärast kontrolli.",
        TranslationKeys.PROPERTY_ARCHIVE_LOOKUP_CANCELLED: "Arhiveerimiskava koostamine katkestati. Kinnistuid ei arhiveeritud ega lisatud.",
        TranslationKeys.PROPERTY_IMPORT_BULK_LABEL: "Määra kõigile:",
        TranslationKeys.PROPERTY_IMPORT_BULK_SET: "Määra",
        TranslationKeys.PROPERTY_IMPORT_BULK_SKIPPED: "{count} kinnistut ei võimalda seda tegevust ja jäid endise valikuga.",
        TranslationKeys.PROPERTY_TOOLTIP_PENDING: "Kontrolli tulemus puudub. Vajuta „Käivita kontroll”.",
        TranslationKeys.PROPERTY_TOOLTIP_BACKEND_OK: "Kavitros on kirje olemas ja selle andmed kattuvad impordiga.",
        TranslationKeys.PROPERTY_TOOLTIP_BACKEND_ISSUES: "Kavitro: {causes}",
        TranslationKeys.PROPERTY_TOOLTIP_MAIN_OK: "Kinnistu on kaardi põhikihil olemas ja selle kuupäev ei ole impordist vanem.",
        TranslationKeys.PROPERTY_TOOLTIP_MAIN_ISSUES: "Kaardil: {causes}",
        TranslationKeys.PROPERTY_TOOLTIP_ARCHIVE_NONE: "Arhiveerimine puudutab ainult kinnistuid, mida impordis enam ei ole. Selle rea kohta kava ei ole.",
        TranslationKeys.PROPERTY_TOOLTIP_ARCHIVE_BACKEND_PLANNED: "Lisamisel arhiveeritakse Kavitro kirje.",
        TranslationKeys.PROPERTY_TOOLTIP_ARCHIVE_BACKEND_SKIP: "Kavitro kirjet ei leitud, seega seda ei arhiveerita.",
        TranslationKeys.PROPERTY_TOOLTIP_ARCHIVE_MAP_PLANNED: "Lisamisel viiakse põhikihi objekt arhiivikihti.",
        TranslationKeys.PROPERTY_IMPORT_ADDRESS_MISSING: "Impordis aadress puudub, taustasüsteemis on aadress olemas. Vajab otsust; taustasüsteemi aadressi ei kirjutata automaatselt üle.",
        TranslationKeys.PROPERTY_ADD_STOPPED_RESULT: "Töö peatus vea tõttu. Töödeldud {done}/{total}. Õnnestus: {succeeded}. Ebaõnnestus: {failed}. Töötlemata: {pending}.",
        TranslationKeys.PROPERTY_ADD_RESPONSE_INVALID: "Serveri vastus ei kinnitanud kinnistu salvestamist.",
        TranslationKeys.PROPERTY_ADD_STAGE_CREATE: "Kinnistu loomine",
        TranslationKeys.PROPERTY_ADD_STAGE_UPDATE: "Kinnistu andmete uuendamine",
        TranslationKeys.PROPERTY_ADD_STAGE_USES: "Sihtotstarvete salvestamine",
        TranslationKeys.PROPERTY_ADD_CANCELLED_RESULT: "Katkestatud. Töödeldud {done}/{total}. Õnnestus: {succeeded}. Ebaõnnestus: {failed}. Töötlemata: {pending}.",
        TranslationKeys.PROPERTY_ADD_LOOKUP_FAILED: "Taustasüsteemi olemasolukontroll ebaõnnestus. Kirjet ei loodud.",
        TranslationKeys.PROPERTY_ADD_WRITE_FAILED: "Taustasüsteemi salvestamine ei õnnestunud täielikult. Enne korduskatset kontrolli kirjet uuesti.",
        TranslationKeys.PROPERTY_ADD_AMBIGUOUS: "Leiti arhiveeritud kirje või mitu aktiivset vastet. Vajab eraldi ülevaatamist; automaatseid muudatusi ei tehtud.",
        TranslationKeys.PROPERTY_ADD_MAP_FAILED: "Taustasüsteemi toiming lõpetati, kuid põhikihile lisamine ebaõnnestus või kiht on redigeerimisel.",
        TranslationKeys.PROPERTY_ADD_LAYER_CHANGED: "Impordi- või põhikiht on muutunud või pole kättesaadav. Kontrolli kinnistut uuesti.",
        TranslationKeys.CLEAR_VALUE: "Tühjenda väärtus",
        TranslationKeys.PROPERTY_ID_PLACEHOLDER: "Kinnistu ID",
        TranslationKeys.MISSING_PROPERTY_ID_TITLE: "ID puudub",
        TranslationKeys.MISSING_PROPERTY_ID_BODY: "Palun sisesta kinnistu ID.",
        TranslationKeys.PROPERTY_LAYER_FIELD_NOT_FOUND: "Väli '{field_name}' puudub kinnistute kihil.",
        TranslationKeys.PROPERTY_GENERATE_SEARCH_FIELD: "Loo/paranda otsinguväli",
        TranslationKeys.PROPERTY_SEARCH_FIELD_MISSING_BODY: "Valitud kinnistute põhikihil puudub search_field väli. Kinnistu otsing ja automaatne kaardile zoomimine ei pruugi ilma selleta toimida.\n\nAva Kinnistute haldus ja käivita 'Loo/paranda otsinguväli'.",
        TranslationKeys.PROPERTY_SEARCH_FIELD_MISSING_TOOLTIP: "search_field puudub. Loo see väli kinnistu otsingu ja zoomi jaoks.",
        TranslationKeys.PROPERTY_SEARCH_FIELD_EXISTS_TOOLTIP: "search_field on olemas. Vajadusel saab väärtused uuesti arvutada.",
        TranslationKeys.PROPERTY_SEARCH_FIELD_PROGRESS_TITLE: "Kinnistute otsinguväli",
        TranslationKeys.PROPERTY_SEARCH_FIELD_PROGRESS_LABEL: "Koostan kinnistute otsinguvälja...",
        TranslationKeys.PROPERTY_SEARCH_FIELD_LAYER_INVALID: "Kinnistukiht puudub või ei ole korrektne.",
        TranslationKeys.PROPERTY_SEARCH_FIELD_NO_SOURCE_FIELDS: "Kihilt ei leitud välju, mille põhjal otsinguvälja koostada.",
        TranslationKeys.PROPERTY_SEARCH_FIELD_EDIT_FAILED: "Kihi muutmisrežiimi ei saanud käivitada.",
        TranslationKeys.PROPERTY_SEARCH_FIELD_ADD_FAILED: "Otsinguvälja search_field lisamine ebaõnnestus.",
        TranslationKeys.PROPERTY_SEARCH_FIELD_MISSING: "Otsinguvälja search_field ei leitud pärast lisamist kihilt.",
        TranslationKeys.PROPERTY_SEARCH_FIELD_SAVE_FAILED: "Otsinguvälja muudatuste salvestamine ebaõnnestus.",
        TranslationKeys.PROPERTY_SEARCH_FIELD_CREATED_BODY: "Kinnistute otsinguväli on valmis. Uuendatud kirjeid: {count}.",
        TranslationKeys.PROPERTY_SEARCH_FIELD_FAILED_BODY: "Kinnistute otsinguvälja loomine ebaõnnestus.\n\nDetailid: {error}",
        TranslationKeys.ADD_UPDATE_PROGRESS_PREFIX: "Kinnistute lisamine",
        TranslationKeys.ADD_UPDATE_PROGRESS_PREFIX_NO_CHECKS: "Lisamine (ilma kontrollideta)",
        TranslationKeys.ADD_UPDATE_PROGRESS_FINISHED: "Lõpetatud",
        TranslationKeys.ADD_UPDATE_PROGRESS_FINISHED_NO_CHECKS: "Lõpetatud (ilma kontrollideta)",
        TranslationKeys.ADD_UPDATE_PROGRESS_TEMPLATE: "{prefix} {done}/{total}",
        TranslationKeys.ADD_UPDATE_PROGRESS_COUNTS: "Töödeldud {done}/{total} kinnistut · Jäänud {remaining}",
        TranslationKeys.ADD_UPDATE_PROGRESS_ELAPSED: "Kulunud {duration}",
        TranslationKeys.ADD_UPDATE_PROGRESS_ESTIMATING: "Järelejäänud aeg arvutamisel…",
        TranslationKeys.ADD_UPDATE_PROGRESS_ESTIMATE: "Jäänud ligikaudu {duration}",
        TranslationKeys.ADD_UPDATE_PROGRESS_CURRENT: "Kinnistu {tunnus}: salvestamine pooleli.",
        TranslationKeys.ADD_UPDATE_PROGRESS_CANCELLED_TEMPLATE: "{prefix} - katkestati {done}/{total} juures",
    TranslationKeys.SERVER_REQUEST_FAILED: "Serveri päring ebaõnnestus (HTTP {status_code}).",
    TranslationKeys.SERVER_REQUEST_REFUSED: "Server keeldus päringust ({reason}). Sisselogimine jääb kehtima, proovi hiljem uuesti.",
    TranslationKeys.NETWORK_ERROR: "Võrgu viga: {error}",
    TranslationKeys.LANGUAGE_LABEL: "Keel:",
    TranslationKeys.USERNAME_LABEL: "Kasutajanimi:",
    TranslationKeys.PASSWORD_LABEL: "Parool:",
    TranslationKeys.LOGIN_BUTTON: "Logi sisse",
    TranslationKeys.CANCEL_BUTTON: "Tühista",
    TranslationKeys.LOGIN_USERNAME_REQUIRED: "Palun sisesta kasutajanimi.",
    TranslationKeys.LOGIN_PASSWORD_REQUIRED: "Palun sisesta parool.",
    TranslationKeys.LOGIN_USERNAME_INVALID: "Kontrolli kasutajanime.",
    TranslationKeys.LOGIN_PASSWORD_INVALID: "Kontrolli parooli.",
    TranslationKeys.LOGIN_CREDENTIALS_INVALID: "Kasutajanimi või parool ei klapi.",
    TranslationKeys.LOGIN_SERVER_UNAVAILABLE: "Sisselogimine ebaõnnestus. Palun proovi uuesti.",
    TranslationKeys.LOGIN_TOO_MANY_ATTEMPTS: "Liiga palju sisselogimiskatseid. Oota minut ja proovi uuesti.",
    TranslationKeys.MFA_CODE_PROMPT: "Sisesta autentimisrakenduse 6-kohaline kood või üks oma taastekoodidest.",
    TranslationKeys.MFA_CODE_REQUIRED: "Sisesta kood.",
    TranslationKeys.MFA_CODE_FORMAT: "Kood koosneb 6 numbrist. Taastekood koosneb 8 tähest ja numbrist.",
    TranslationKeys.MFA_CODE_INVALID: "Kood on vale või aegunud. Proovi uuesti.",
    TranslationKeys.MFA_VERIFY_BUTTON: "Kinnita",
    TranslationKeys.MFA_BACK_BUTTON: "Tagasi",
    TranslationKeys.MFA_SETUP_REQUIRED: "Sinu organisatsioon nõuab kahetasandilist autentimist. Lülita see Kavitro veebirakenduses sisse ja proovi siis uuesti.",
    TranslationKeys.MFA_OPEN_WEB_APP: "Ava Kavitro veebirakendus",
    TranslationKeys.SESSION_STORAGE_WARNING_TITLE: "Sessiooni ei salvestatud täielikult",
    TranslationKeys.SESSION_STORAGE_MEMORY_ONLY: "QGIS-i turvalist sessioonihoidlat ei õnnestunud avada. Saad selles QGIS-i käivituses tööd jätkata, kuid pärast QGIS-i sulgemist tuleb uuesti sisse logida. Kavitro parooli ega juurdepääsutõendit ei salvestatud avatekstina.",
    TranslationKeys.SESSION_STORAGE_MIGRATION_PENDING: "Sessioon taastati, kuid vana autentimiskirje puhastamine ei õnnestunud täielikult. Tööd saab jätkata ja puhastamist proovitakse järgmisel sobival käivitamisel või sisselogimisel uuesti.",
    TranslationKeys.SESSION_STORAGE_CLEANUP_FAILED: "Vana avatekstis juurdepääsutõendi eemaldamist QGIS-i seadetest ei saanud kinnitada. Lõpeta töö turvaliselt ja pöördu toe poole; ära jaga QGIS-i profiili ega selle varukoopiat.",
    TranslationKeys.KAVITRO_PLUGIN_TITLE: "Kavitro",
    TranslationKeys.UNKNOWN_MODULE: "Tundmatu moodul: {module}",
    TranslationKeys.USER: "Kasutaja",
    TranslationKeys.ROLES: "Rollid",
    TranslationKeys.CONFIRM: "Kinnita",
    TranslationKeys.NAME: "Nimi",
    TranslationKeys.EMAIL: "E-post",
    TranslationKeys.PREFERRED_MODULE: "Eelistatud moodul",
    TranslationKeys.COUNTY: "Maakond",
    TranslationKeys.MUNICIPALITY: "Omavalitsus",
    TranslationKeys.DUE: "Tähtaeg",
    TranslationKeys.TOGGLE_PASSWORD: "Näita parooli",
    TranslationKeys.NO_PROJECT_LOADED_TITLE: "Ühtegi projekti pole avatud",
    TranslationKeys.NO_PROJECT_LOADED_MESSAGE: "Kavitro plugnin nõuab QGIS projektifaili, et töötada. Palun ava või loo uus projekt.",
    TranslationKeys.PROJECT_FOLDER_CREATE_CONFIRM: "Ettevalmistatud struktuuriga projektikausta loomine on mõeldud eelkõige uutele projektidele. Kontrolli, et samasisulist kausta pole juba loodud.\n\nMallkausta sisu kopeeritakse järgmisse asukohta.\n\nLähtekaust:\n{source}\n\nSihtkaust:\n{destination}\n\nKontrolli sihttee üle. Kas jätkata?",
    TranslationKeys.PROJECT_FOLDER_SOURCE_INVALID: "Seadistatud lähtekaust puudub või ei ole kaust:\n{path}",
    TranslationKeys.PROJECT_FOLDER_TARGET_INVALID: "Seadistatud sihtkaust puudub või ei ole kaust:\n{path}",
    TranslationKeys.PROJECT_FOLDER_TARGET_INSIDE_SOURCE: "Sihtkaust ei tohi olla mallkaust ega paikneda mallkausta sees.\n\nLähtekaust:\n{source}\n\nSihtkaust:\n{target}",
    TranslationKeys.PROJECT_FOLDER_DESTINATION_INVALID: "Projekti nimest ei õnnestunud moodustada turvalist sihtkausta.",
    TranslationKeys.PROJECT_FOLDER_NUMBER_MISSING: "Valitud kaustanime reegel sisaldab projekti numbrit, kuid projekti kirjel number puudub. Kausta ei loodud.",
    TranslationKeys.PROJECT_FOLDER_ALREADY_EXISTS: "Kaust on sihtkohas juba olemas:\n{path}",
    TranslationKeys.PROJECT_FOLDER_COPY_FAILED: "Projektikausta loomine ebaõnnestus:\n{error}",
    TranslationKeys.PROJECT_FOLDER_LINK_CONFIRM: "Kas soovid lisada genereeritud kausta tee Kavitro projektile?\n\nKaust:\n{path}",
    TranslationKeys.PROJECT_FOLDER_LINK_UPDATE_FAILED: "Kaust on failisüsteemis olemas, kuid kaustatee salvestamine Kavitro projektile ebaõnnestus.\n\nKaust:\n{path}\n\nViga:\n{error}",
    TranslationKeys.PROJECT_FOLDER_LINK_ACTION: "Lisa või uuenda",
    TranslationKeys.PROJECT_FOLDER_EXISTING_LINK_CONFIRM: "Kaust on sihtkohas juba olemas. Kavitro ei kopeeri ega muuda selle sisu.\n\nOlemasolev kaust:\n{path}\n\nKas soovid lisada või uuendada selle kausta teekonna Kavitro projektis?",
    TranslationKeys.PROJECT_FOLDER_EXISTING_LINK_SUCCESS: "Olemasoleva kausta teekond lisati või uuendati Kavitro projektis.\n\nKaust:\n{path}\n\nSelle projektikaardi Ava kaust nupp on kasutamiseks valmis.",
    TranslationKeys.SETTINGS_SETUP_MISSING_TITLE: "Mooduli seadistus puudub",
    TranslationKeys.SETTINGS_SETUP_MISSING_MESSAGE: "Mooduli {module} seadistused ei ole veel täielikult määratud. Järgmisena suunatakse sind selle mooduli seadete juurde.",
    TranslationKeys.SETTINGS_SETUP_MISSING_NOTE: "Nota bene:\nVaata palun üle ka teiste moodulite seadistused, et töövood oleksid terviklikult valmis.",
    TranslationKeys.MODULE_SWITCH_FAILED_TITLE: "Moodulit ei saanud avada",
    TranslationKeys.MODULE_SWITCH_FAILED_MESSAGE: "Mooduli {module} avamine ebaõnnestus. Proovi uuesti. Kui viga kordub, taaskäivita QGIS.\n\nVea üksikasjad on pluginakausta logis Logs/SwitchLogs.",
    TranslationKeys.HOME_KPI_TOTAL_LABEL: "Filtreeritud kokku",
    TranslationKeys.HOME_KPI_OTHER_LABEL: "Muu",
    TranslationKeys.HOME_KPI_OTHER_TOOLTIP: "Filtreeritud kirjed, mis ei ole hilinenud ega peagi tähtajaga",
    TranslationKeys.HOME_KPI_OVERDUE_LABEL: "Hilis",
    TranslationKeys.HOME_KPI_DUE_SOON_LABEL: "Varsti",
    TranslationKeys.HOME_KPI_OVERDUE_TOOLTIP: "Filtreeritud hilinenud kirjed",
    TranslationKeys.HOME_KPI_DUE_SOON_TOOLTIP: "Filtreeritud peagi tähtajani jõudvad kirjed",
    TranslationKeys.HOW_SELECT_PROPERTIES: "Kuidas soovid kinnistuid valida?",
    TranslationKeys.PROPERTY_BACKEND_ACTION_PROMPT_TITLE: "Vali tegevus",
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
    TranslationKeys.PROPERTY_BOOTSTRAP_REQUIRED_TITLE: "Kinnistute põhikiht puudub",
    TranslationKeys.PROPERTY_BOOTSTRAP_REQUIRED_BODY: "Projektis ei ole seadistatud kinnistute põhikihti. Kas soovid luua valitud SHP struktuuri põhjal uue GeoPackage'i koos tühja põhi- ja arhiivikihiga?",
    TranslationKeys.PROPERTY_BOOTSTRAP_CREATE: "Loo GeoPackage'i kihid",
    TranslationKeys.PROPERTY_BOOTSTRAP_CONTINUE_SHP: "Jätka ainult SHP-kihiga",
    TranslationKeys.PROPERTY_BOOTSTRAP_EXISTING_GPKG_TITLE: "GeoPackage on juba olemas",
    TranslationKeys.PROPERTY_BOOTSTRAP_EXISTING_GPKG_BODY: "Fail on juba olemas:\n{path}\n\nKas lisada kinnistute põhi- ja arhiivikiht sellesse faili? Olemasolevaid kihte ei kirjutata üle.",
    TranslationKeys.PROPERTY_BOOTSTRAP_ADD_TO_GPKG: "Lisa kihid",
    TranslationKeys.PROPERTY_BOOTSTRAP_SAVE_DIALOG_TITLE: "Vali kinnistute GeoPackage'i asukoht",
    TranslationKeys.PROPERTY_BOOTSTRAP_FAILED_TITLE: "Kinnistukihtide loomine ebaõnnestus",
    TranslationKeys.PROPERTY_BOOTSTRAP_MISSING_FIELDS_BODY: "SHP struktuurist puuduvad kinnistukihi kohustuslikud väljad:\n{fields}\n\nGeoPackage'i kihte ei loodud.",
    TranslationKeys.PROPERTY_BOOTSTRAP_INVALID_GEOMETRY_BODY: "Kinnistute põhikihi loomiseks peab SHP olema polügoonikiht. GeoPackage'i kihte ei loodud.",
    TranslationKeys.PROPERTY_BOOTSTRAP_INVALID_CRS_BODY: "SHP kihil puudub kehtiv koordinaatsüsteem. GeoPackage'i kihte ei loodud.",
    TranslationKeys.PROPERTY_BOOTSTRAP_LAYER_EXISTS_BODY: "Kiht nimega '{name}' on projektis või valitud GeoPackage'is juba olemas. Kihte ei kirjutatud üle; vali teine GeoPackage.",
    TranslationKeys.PROPERTY_BOOTSTRAP_INVALID_SOURCE_BODY: "Valitud SHP kiht ei ole kehtiv ja selle põhjal ei saa kinnistukihte luua.",
    TranslationKeys.PROPERTY_BOOTSTRAP_CREATE_FAILED_BODY: "Kinnistute põhi- ja arhiivikihi loomine ebaõnnestus etapis: {stage}. Täpsem info salvestati logisse.",
    TranslationKeys.PROPERTY_BOOTSTRAP_STAGE_CREATE_MAIN: "põhikihi loomine",
    TranslationKeys.PROPERTY_BOOTSTRAP_STAGE_LOAD_MAIN: "põhikihi laadimine",
    TranslationKeys.PROPERTY_BOOTSTRAP_STAGE_CREATE_ARCHIVE: "arhiivikihi loomine",
    TranslationKeys.PROPERTY_BOOTSTRAP_STAGE_SAVE_SETTINGS: "kihiseadistuste salvestamine",
    TranslationKeys.PROPERTY_BOOTSTRAP_READY_BODY: "Loodi ja seadistati põhikiht '{main}' ning arhiivikiht '{archive}' failis:\n{path}",
    TranslationKeys.RUN_ATTENTION_CHECKS: "Käivita kontroll",
    TranslationKeys.ADD_WITHOUT_CHECKS: "Lisa ilma kontrollita",
    TranslationKeys.OPEN_SETTINGS: "Ava Seaded",
    TranslationKeys.MAIN_PROPERTY_LAYER: "Kinnistute põhikiht",
    TranslationKeys.ARCHIVE_LAYER: "Arhiivikiht",
    TranslationKeys.SELECT_LAYER: "Vali kiht",
    TranslationKeys.PROPERTY_LAYER_OVERVIEW: "See on kinnistute põhikiht.\nVali kiht, mis kajastab ettevõtte peamist kinnistute kaardikihti.",
    TranslationKeys.MODULE_MAIN_LAYER: "Mooduli kiht",
    TranslationKeys.MODULE_LAYER_OVERVIEW: "See on mooduli enda töökiht kaardiga seotud töövoogude jaoks. Seotud kinnistute 'Näita kaardil' tegevus kasutab Kinnistute mooduli põhikihi seadistust.",
    TranslationKeys.ARCHIVE_LAYER_DESCRIPTION: "Kasuta valikulist arhiivikihti ajalooliste või varuandmete salvestamiseks.",
    TranslationKeys.LOGOUT_BUTTON_TOOLTIP: "Logi välja",
    TranslationKeys.SEARCH_TOOLTIP: "Funktsioon veel ei tööta",
    TranslationKeys.SEARCH_PLACEHOLDER: "Otsi...",
    TranslationKeys.SEARCH_NO_RESULTS: "Tulemusi ei leitud: '{term}'",
    TranslationKeys.SIDEBAR_COLLAPSE_TOOLTIP: "Ahenda külgriba",
    TranslationKeys.SIDEBAR_EXPAND_TOOLTIP: "Laienda külgriba",
    TranslationKeys.THEME_SWITCH_TOOLTIP: "Tume/Hele režiim",
    TranslationKeys.SESSION_EXPIRED: "Teie seanss on aegunud. Palun logige uuesti sisse.",
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
    TranslationKeys.SETTINGS_RESET_FAILED: "Lähtestamine ebaõnnestus",
    TranslationKeys.MODULE_ACCESS: "Mooduli juurdepääs",
    TranslationKeys.OPEN_MAA_AMET_PAGE: "Ava Maa-ameti leht",
    TranslationKeys.PROPERTY_MANAGEMENT: "Kinnistute haldus",
    TranslationKeys.ADD_SHP_FILE: "Lisa SHP fail",
    TranslationKeys.ADD_PROPERTY: "Lisa kinnistuid",
    TranslationKeys.REMOVE_PROPERTY: "Eemalda kinnistu",
    TranslationKeys.SELECT_SHAPEFILE: "Vali Shapefile fail",
    TranslationKeys.PROPERTY_TREE_HEADER: "Kinnistuga seotud andmed",
    TranslationKeys.PROPERTY_TREE_DEFAULT_MESSAGE: "Vali kinnistu kaardilt",
    TranslationKeys.PROPERTY_TREE_NO_CONNECTIONS: "Seoseid ei leitud",
    TranslationKeys.PROPERTY_TREE_MODULE_EMPTY: "Kirjeid ei ole",
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
    ,TranslationKeys.IMPORTING_SHAPEFILE: "Shapefile importimine"
    ,TranslationKeys.INITIALIZING: "Initsialiseerimine..."
    ,TranslationKeys.PROGRESS_WORKING: "Töötlemine..."
    ,TranslationKeys.LAYER_IMPORT_FINAL_TOUCHES: "Viimistlemine..."
    ,TranslationKeys.LAYER_IMPORT_COMPLETE: "Import on lõpetatud!"
    ,TranslationKeys.RESIDENTIAL: "Elamu"
    ,TranslationKeys.OTHER: "Muu"
    ,TranslationKeys.CADASTRAL_ID: "Katastritunnus"
    ,TranslationKeys.ADDRESS: "Aadress"
    ,TranslationKeys.AREA: "Pindala (m²)"
    ,TranslationKeys.SETTLEMENT: "Linn/Asustusüksus"
    ,TranslationKeys.PROPERTY_COLUMN_BACKEND: "Kavitro"
    ,TranslationKeys.PROPERTY_COLUMN_MAIN_LAYER: "Kaardil"
    ,TranslationKeys.PROPERTY_COLUMN_ARCHIVE_BACKEND: "Arhiiv"
    ,TranslationKeys.PROPERTY_COLUMN_ARCHIVE_MAP: "Arhiiv: kaart"
    ,TranslationKeys.SAVE: "Salvesta"
    ,TranslationKeys.DELETE: "Kustuta"
    ,TranslationKeys.SELECT: "Vali"
    ,TranslationKeys.WARNING: "Hoiatus"
    ,TranslationKeys.INFO: "Info"
    ,TranslationKeys.INVALID_VALUE: "Vigane väärtus"
    ,TranslationKeys.YES: "Jah"
    ,TranslationKeys.NO: "Ei"
    ,TranslationKeys.OK: "OK"
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
    ,TranslationKeys.TYPE_FILTER_ALL_GROUPS: "Kõik grupid"
    ,TranslationKeys.STATUS_GROUP_OPEN: "AVATUD"
    ,TranslationKeys.STATUS_GROUP_CLOSED: "SULETUD"
    ,TranslationKeys.STATUS_GROUP_OTHER: "MUUD"
    ,TranslationKeys.ADD_SELECTED: "Lisa valitud"
    ,TranslationKeys.DELETE_BY_ID: "Kustuta ID järgi"
    ,TranslationKeys.SELECT_FROM_MAP: "Vali kaardilt"
    ,TranslationKeys.SELECT_BY_LOCATION_LIST: "Vali asukoha järgi (loend)"
    ,TranslationKeys.RESELECT_FROM_MAP: "Vali uuesti kaardilt"
    ,TranslationKeys.ARCHIVE: "Arhiveeri"
    ,TranslationKeys.UNARCHIVE: "Taasta arhiivist"
    ,TranslationKeys.CREATE_LOAD_IN_GPKG: "Loo/lae GPKG-s…"
    ,TranslationKeys.SELECT_COUNTY: "Vali maakond"
    ,TranslationKeys.SELECT_MUNICIPALITY: "Vali omavalitsus"
    ,TranslationKeys.PROPERTY_MANAGEMENT_BY_LOCATION_TITLE: "Kinnistute haldus – asukoha järgi filtreerimine"
    ,TranslationKeys.SELECTED_PROPERTIES_COUNT: "Valitud: 0 kinnistut"
    ,TranslationKeys.SELECTED_COUNT_TEMPLATE: "Valitud: {count} kinnistut"
    ,TranslationKeys.PROPERTY_TABLE_COUNT_TEMPLATE: "Tabelis: {count} kinnistut"
    ,TranslationKeys.SELECT_PROPERTIES_MAP_INSTRUCTION: "Vali kaardilt üks või mitu kinnistut peamisest kinnistute kihist.\n\nSeejärel vali tegevus (Arhiveeri/Taasta arhiivist/Kustuta)."
    ,TranslationKeys.NO_SELECTION: "Valikut pole"
    ,TranslationKeys.MISSING_TUNNUS_TITLE: "Tunnus puudub"
    ,TranslationKeys.MISSING_TUNNUS_MESSAGE: "Valitud objektidel puudub katastritunnus."
    ,TranslationKeys.SELECTION_FAILED_TITLE: "Valiku alustamine ebaõnnestus"
    ,ToolbarTranslationKeys.OPEN_FOLDER: "Ava kaust"
    ,ToolbarTranslationKeys.OPEN_ITEM_IN_BROWSER: "Ava kirje brauseris"
    ,ToolbarTranslationKeys.SHOW_CONNECTED_PROPERTIES_ON_MAP: "Näita seotud kinnistuid kaardil"
    ,ToolbarTranslationKeys.CONNECT_MISSING_PROPERTIES: "Kinnistuseos puudub – seosta kinnistuid"
    ,ToolbarTranslationKeys.GENERATE_PROJECT_FOLDER: "Genereeri projekti kaust"
    ,TranslationKeys.NO_PROPERTY_LAYER_SELECTED: "Kinnistute kihti pole valitud. Palun valige esmalt kinnistute kiht."
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
    ,TranslationKeys.PROPERTY_ARCHIVE_PLAN_TITLE: "Arhiveerimisplaani ülevaade"
    ,TranslationKeys.PROPERTY_ARCHIVE_PLAN_SCOPE: "Piirkond: {county} / {municipality} / {settlements}"
    ,TranslationKeys.PROPERTY_ARCHIVE_PLAN_INTRO: "Valitud asustusüksuste täielikust impordist puudub {count} kinnistut. Kontrolli enne jätkamist kaardi- ja taustasüsteemi toiminguid."
    ,TranslationKeys.PROPERTY_ARCHIVE_PLAN_COLUMN_TUNNUS: "Katastritunnus"
    ,TranslationKeys.PROPERTY_ARCHIVE_PLAN_COLUMN_SETTLEMENT: "Asustusüksus"
    ,TranslationKeys.PROPERTY_ARCHIVE_PLAN_COLUMN_MAP: "Kaart"
    ,TranslationKeys.PROPERTY_ARCHIVE_PLAN_COLUMN_BACKEND: "Taustasüsteem"
    ,TranslationKeys.PROPERTY_ARCHIVE_PLAN_COLUMN_NOTE: "Märkus"
    ,TranslationKeys.PROPERTY_ARCHIVE_PLAN_MAP_MOVE: "Liiguta arhiivi"
    ,TranslationKeys.PROPERTY_ARCHIVE_PLAN_BACKEND_ARCHIVE: "Arhiveeri"
    ,TranslationKeys.PROPERTY_ARCHIVE_PLAN_BACKEND_MISSING: "Aktiivne kirje puudub — jäta vahele"
    ,TranslationKeys.PROPERTY_ARCHIVE_PLAN_BACKEND_FAILED: "Kontroll ebaõnnestus — jäta vahele"
    ,TranslationKeys.PROPERTY_ARCHIVE_PLAN_BACKEND_MULTIPLE: "Mitu aktiivset kirjet — jäta vahele"
    ,TranslationKeys.PROPERTY_ARCHIVE_PLAN_CONFIRM: "Kinnita ja jätka"
    ,TranslationKeys.PROPERTY_ARCHIVE_PLAN_CANCEL: "Loobu"
    ,TranslationKeys.PROPERTY_ARCHIVE_PLAN_COMPLETENESS_CONFIRM: "Kinnitan, et import sisaldab valitud asustusüksuste täielikke kehtivaid andmeid."
    ,TranslationKeys.PROPERTY_ARCHIVE_PLAN_STALE_TITLE: "Arhiveerimisplaan ei ole enam kehtiv"
    ,TranslationKeys.PROPERTY_ARCHIVE_PLAN_STALE_BODY: "Valitud piirkond või impordikiht muutus pärast kontrolli. Enne muudatuste rakendamist käivita kontroll uuesti."
    ,TranslationKeys.PROPERTY_ARCHIVE_PLAN_PARTIAL_TITLE: "Arhiveerimine lõpetati puudustega"
    ,TranslationKeys.PROPERTY_ARCHIVE_PLAN_PARTIAL_BODY: "Kaardil arhiveeritud: {moved}. Taustasüsteemis arhiveeritud: {archived}. Ebaõnnestunud või vahele jäetud toiminguid: {failed}."
    ,TranslationKeys.PROPERTY_ARCHIVE_SCOPE_SKIPPED: "Puuduvate kinnistute arhiveerimine on sellel korral välja lülitatud. Vali vähemalt üks asustusüksus ja laadi selle täielikud, mittetühjad impordiandmed."
    ,TranslationKeys.PROPERTY_ARCHIVE_MOVED_EXCLUDED: "{count} puuduvat katastritunnust leiti impordist teise asustusüksuse alt ja jäeti automaatsest arhiveerimisest välja."
    ,TranslationKeys.MAP_SELECTION_NONE: "Kaardilt ei valitud ühtegi kinnistut."
    ,TranslationKeys.MAP_SELECTION_START_FAILED: "Kinnistute kaardivalikut ei saanud alustada."
    ,TranslationKeys.LINK_PROPERTIES_SUCCESS: "Kinnistute seosed salvestatud projektile {pid}.\nKokku seotud: {count}. {preview}{extra}"
    ,TranslationKeys.LINK_PROPERTIES_MISSING_NOTE: "Puuduvad/ei leitud: {missing}"
    ,TranslationKeys.LINK_PROPERTIES_ERROR: "Kinnistute seostamine projektile {pid} ebaõnnestus.\nOotel valik ({count}): {preview}\n\nDetailid: {err}"
        ,TranslationKeys.ASBUILT_UPDATE_NOTES_ACTION: "Lisa/uuenda märkmeid"
        ,TranslationKeys.ASBUILT_UPDATE_NOTES_TITLE: "Teostusjoonise märkused"
        ,TranslationKeys.ASBUILT_UPDATE_NOTES_SUCCESS: "Kirje {name} märkmed uuendati."
        ,TranslationKeys.ASBUILT_UPDATE_NOTES_FAILED: "Kirje {name} märkmete uuendamine ebaõnnestus."
        ,TranslationKeys.ASBUILT_NOTES_ADD_NOTE: "Lisa märkus"
        ,TranslationKeys.ASBUILT_NOTES_COLUMN_NOTE: "Märkus"
        ,TranslationKeys.ASBUILT_NOTES_COLUMN_RESOLVED: "Lahendatud"
        ,TranslationKeys.ASBUILT_NOTES_NO_DATE: "Kuupäev puudub"
        ,TranslationKeys.ASBUILT_NOTES_DELETE_ROW: "Kustuta märkus"
        ,TranslationKeys.ASBUILT_NOTES_PLACEHOLDER: "Sisesta märkuse sisu"
        ,TranslationKeys.ASBUILT_NOTES_OPEN_COUNT: "Lahendamata: {count}"
        ,TranslationKeys.ASBUILT_NOTES_ALL_RESOLVED: "Kõik lahendatud"
        ,TranslationKeys.ASBUILT_NOTES_LOAD_FAILED: "Kirje {name} kirjeldust ei õnnestunud laadida, seega märkmeid ei avatud. Proovi uuesti."
        ,TranslationKeys.PROJECT_DRAW_NEW_ACTION: "Joonista uus seotud ala kaardile"
        ,TranslationKeys.PROJECT_DRAW_NEW_START_FAILED: "Uue projekti ala joonistamist kaardil ei saanud käivitada."
        ,TranslationKeys.PROJECT_DRAW_NEW_SAVE_FAILED: "Uus kaardiala loodi, kuid selle sidumine backendi projektiga {item_id} ebaõnnestus. Detailid: {error}"
        ,TranslationKeys.PROJECT_DRAW_NEW_SUCCESS: "Uus kaardiala loodi ja seoti backendi projektiga {item_id}."
        ,TranslationKeys.PROJECT_PREVIEW_ACTION: "Ava projekti ala eelvaade"
        ,TranslationKeys.PROJECT_PREVIEW_DIALOG_TITLE: "Projekti ala eelvaade"
        ,TranslationKeys.PROJECT_PREVIEW_INTRO: "Loo projektiala eelvaade kirjele {name} ({number}) seotud kinnistute põhjal."
        ,TranslationKeys.PROJECT_PREVIEW_INSTRUCTIONS: "Seotud kinnistud valitakse kaardilt, neist luuakse ajutine koondala eelvaade ning seejärel saab tulemuse salvestada Projektide põhikihile. Enne salvestamist saab kinnistute seoseid kaardilt muuta."
        ,TranslationKeys.PROJECT_PREVIEW_LAYER_NAME: "Sihtkiht"
        ,TranslationKeys.PROJECT_PREVIEW_CONNECTED_PROPERTIES: "Seotud kinnistud"
        ,TranslationKeys.PROJECT_PREVIEW_CONNECTED_PROPERTIES_VALUE: "{count} seotud: {preview}"
        ,TranslationKeys.PROJECT_PREVIEW_PROPERTY_CARD_TITLE: "Seotud kinnistu näidis"
        ,TranslationKeys.PROJECT_PREVIEW_BUFFER_DISTANCE: "Puhvri kaugus"
        ,TranslationKeys.PROJECT_PREVIEW_ROUNDED_CORNERS: "Ümardatud nurgad"
        ,TranslationKeys.PROJECT_PREVIEW_CORNER_RADIUS: "Nurga raadius"
        ,TranslationKeys.PROJECT_PREVIEW_CREATE_ACTION: "Värskenda eelvaadet"
        ,TranslationKeys.PROJECT_PREVIEW_CLEAR_ACTION: "Puhasta eelvaade"
        ,TranslationKeys.PROJECT_PREVIEW_SAVE_ACTION: "Salvesta ala kihile"
        ,TranslationKeys.PROJECT_PREVIEW_NO_CONNECTED_PROPERTIES: "Sellel projektil ei ole veel seotud kinnistuid. Ala eelvaate loomiseks seo kõigepealt üks või mitu kinnistut."
        ,TranslationKeys.PROJECT_PREVIEW_LAYER_SELECTION_FAILED: "Seotud kinnistuid ei õnnestunud aktiivselt kinnistukihilt leida."
        ,TranslationKeys.PROJECT_PREVIEW_CREATE_FAILED: "Praegu seotud kinnistutest ei õnnestunud projekti ala eelvaadet luua."
        ,TranslationKeys.PROJECT_PREVIEW_CREATED: "Eelvaatekiht {preview} loodi {count} seotud kinnistu põhjal. Puhver: {distance} m. Nurga raadius: {radius} m."
        ,TranslationKeys.PROJECT_PREVIEW_CLEARED: "Puhastati {count} projekti eelvaate kiht(i)."
        ,TranslationKeys.PROJECT_PREVIEW_SAVE_NO_PREVIEW: "Enne Projektide kihile salvestamist loo kõigepealt projekti ala eelvaade."
        ,TranslationKeys.PROJECT_PREVIEW_SAVE_SUCCESS: "Projekti {item_id} ala salvestati kihile {layer}."
        ,TranslationKeys.PROJECT_PREVIEW_SAVE_FAILED: "Projekti {item_id} ala salvestamine ebaõnnestus. Detailid: {error}"
        ,TranslationKeys.PROJECT_LAYER_MISSING: "Projektide kiht ei ole seadistatud või puudub projektist. Seadista kõigepealt Seadetes Projektide põhikiht."
        ,TranslationKeys.PROJECT_LAYER_INVALID_GEOMETRY: "Projektide kiht peab ala joonistamiseks olema polügoongeomeetriaga."
        ,TranslationKeys.ASBUILT_DRAW_NEW_ACTION: "Joonista uus seotud objekt kaardile"
        ,TranslationKeys.ASBUILT_DRAW_NEW_START_FAILED: "Uue teostusjoonise objekti joonistamist kaardil ei saanud käivitada."
        ,TranslationKeys.ASBUILT_DRAW_NEW_SAVE_FAILED: "Uus kaardiobjekt loodi, kuid selle sidumine backendi teostusjoonise kirjega {item_id} ebaõnnestus. Detailid: {error}"
        ,TranslationKeys.ASBUILT_DRAW_NEW_SUCCESS: "Uus kaardiobjekt loodi ja seoti backendi teostusjoonise kirjega {item_id}."
        ,TranslationKeys.ASBUILT_LAYER_MISSING: "Teostusjooniste kiht on seadistamata või puudub projektist. Palun seadista kõigepealt Seadetes Teostusjooniste põhikiht."
        ,TranslationKeys.WORKS_CREATE_ON_MAP_BUTTON: "Lisa uus töö"
        ,TranslationKeys.WORKS_CREATE_DIALOG_TITLE: "Lisa uus töö"
        ,TranslationKeys.WORKS_CREATE_PROPERTY_LINK_HINT: "Selles asukohas leitud kinnistu seotakse tööga võimalusel automaatselt."
        ,TranslationKeys.WORKS_CREATE_PROPERTY_LABEL: "Kinnistu"
        ,TranslationKeys.WORKS_CREATE_PROPERTY_NONE: "Selles asukohas kinnistut ei leitud"
        ,TranslationKeys.WORKS_CREATE_COORDINATES_LABEL: "Koordinaadid"
        ,TranslationKeys.WORKS_CREATE_TYPE_LABEL: "Töö liik"
        ,TranslationKeys.WORKS_CREATE_TITLE_LABEL: "Pealkiri"
        ,TranslationKeys.WORKS_CREATE_TITLE_PLACEHOLDER: "Sisesta töö pealkiri"
        ,TranslationKeys.WORKS_CREATE_RESPONSIBLE_LABEL: "Vastutaja"
        ,TranslationKeys.WORKS_CREATE_STATUS_LABEL: "Staatus"
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
        ,TranslationKeys.WORKS_ADD_EXISTING_ON_MAP_ACTION: "Lisa punkt kaardile"
        ,TranslationKeys.WORKS_ADD_EXISTING_ON_MAP_START_FAILED: "Olemasoleva töö kaardivalikut ei saanud käivitada."
        ,TranslationKeys.WORKS_ADD_EXISTING_ON_MAP_TASK_LOAD_FAILED: "Tööd {task_id} ei õnnestunud enne kaardiobjekti loomist laadida."
        ,TranslationKeys.WORKS_ADD_EXISTING_ON_MAP_ALREADY_LINKED: "Tööl {task_id} on juba seotud kaardiobjekt olemas."
        ,TranslationKeys.WORKS_ADD_EXISTING_ON_MAP_SAVE_FAILED: "Töö {task_id} on Kavitros olemas, kuid selle kaardiobjekti ei saanud Tööde kihile salvestada. Detailid: {error}"
        ,TranslationKeys.WORKS_ADD_EXISTING_ON_MAP_PROPERTY_LINK_FAILED: "Töö {task_id} lisati kaardile, kuid kinnistu seostamine ebaõnnestus tunnusele {cadastral}."
        ,TranslationKeys.WORKS_ADD_EXISTING_ON_MAP_SUCCESS: "Töö {task_id} lisati Tööde kihile."
        ,TranslationKeys.WORKS_PENDING_GIS_ACTION: "Kontrolli sidumata GIS töid"
        ,TranslationKeys.WORKS_PENDING_GIS_START_FAILED: "Sidumata GIS tööde kontrolli ei saanud käivitada."
        ,TranslationKeys.WORKS_PENDING_GIS_CHECKING: "Kontrollin kaardiandmeid..."
        ,TranslationKeys.WORKS_PENDING_GIS_DIALOG_TITLE: "Sidumata GIS tööd"
        ,TranslationKeys.WORKS_PENDING_GIS_DIALOG_INTRO: "Need Tööde kihi punktid ei ole veel Kavitro tööga seotud. Tee real topeltklikk, et punkt kaardil avada ja eeltäidetud töö loomise vorm läbi vaadata."
        ,TranslationKeys.WORKS_PENDING_GIS_NONE: "Tööde kihilt ei leitud Kavitroga sidumata uusi GIS töid."
        ,TranslationKeys.WORKS_PENDING_GIS_OPEN_SELECTED: "Ava valitud"
        ,TranslationKeys.WORKS_PENDING_GIS_COL_ID: "FID"
        ,TranslationKeys.WORKS_PENDING_GIS_COL_TITLE: "Pealkiri"
        ,TranslationKeys.WORKS_PENDING_GIS_COL_TYPE: "Liik"
        ,TranslationKeys.WORKS_PENDING_GIS_COL_STATUS: "Staatus"
        ,TranslationKeys.WORKS_PENDING_GIS_COL_UPDATED: "Muudetud"
        ,TranslationKeys.WORKS_PENDING_GIS_FEATURE_MISSING: "Valitud GIS tööd ei leitud enam kihilt või see on juba Kavitroga seotud."
        ,TranslationKeys.WORKS_REPOSITION_ACTION: "Muuda asukohta"
        ,TranslationKeys.EASEMENT_PREVIEW_ACTION: "Ava servituudi eelvaade"
        ,TranslationKeys.EASEMENT_DRAW_NEW_ACTION: "Joonista uus seotud objekt kaardile"
        ,TranslationKeys.EASEMENT_ATTACH_EXISTING_ACTION: "Seo olemasolev joonis kaardilt"
        ,TranslationKeys.EASEMENT_EDIT_GEOMETRY_ACTION: "Muuda joonise geomeetriat kaardil"
        ,TranslationKeys.EASEMENT_PREVIEW_DIALOG_TITLE: "Servituudi eelvaade"
        ,TranslationKeys.EASEMENT_PREVIEW_INTRO: "Loo servituudi eelvaated kirjele {name} ({number})."
        ,TranslationKeys.EASEMENT_PREVIEW_INSTRUCTIONS: "Seotud kinnistud valitakse automaatselt, seadistatud baaskihtidelt leitakse ristuvad tehnovõrgu objektid ning eelvaatepuhvrid luuakse automaatselt. Eelvaated jäävad ainult mällu ja kustutatakse dialoogi sulgemisel."
        ,TranslationKeys.EASEMENT_PREVIEW_BUFFER_DISTANCE: "Puhvri kaugus"
        ,TranslationKeys.EASEMENT_PREVIEW_LAYER_NAME: "Seadistatud kiht"
        ,TranslationKeys.EASEMENT_PREVIEW_STATUS: "Automaatika"
        ,TranslationKeys.EASEMENT_PREVIEW_CREATE_FINAL_CUT: "Loo lõplik lõige"
        ,TranslationKeys.EASEMENT_PREVIEW_ROUNDED_CAPS: "Ümardatud nurgad"
        ,TranslationKeys.EASEMENT_PREVIEW_CLEAR_ACTION: "Puhasta eelvaated"
        ,TranslationKeys.EASEMENT_PREVIEW_LAYER_MISSING: "Kiht on seadistamata või seda ei õnnestunud aktiivsest projektist leida."
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
        ,TranslationKeys.EASEMENT_PREVIEW_LINK_FAILED: "Servituudiga {pid} kinnistute sidumine ebaõnnestus. Valik ({count}): {preview}\n\nDetailid: {err}"
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
        ,TranslationKeys.EASEMENT_PREVIEW_DRAWING_PREVIEW: "Eelvaata PDF skeemi"
        ,TranslationKeys.EASEMENT_PREVIEW_DRAWING_PUBLISH: "Avalda PDF skeem"
        ,TranslationKeys.EASEMENT_PREVIEW_DRAWING_EXPORT_FAILED: "Servituudi PDF skeemi loomine ebaõnnestus. Detailid: {error}"
        ,TranslationKeys.EASEMENT_PREVIEW_DRAWING_PREVIEW_FAILED: "Genereeritud PDF skeemi eelvaadet ei saanud avada."
        ,TranslationKeys.EASEMENT_PREVIEW_DRAWING_PUBLISH_SUCCESS: "Servituudi PDF skeem laaditi edukalt üles."
        ,TranslationKeys.EASEMENT_PREVIEW_DRAWING_PUBLISH_FAILED: "Servituudi PDF skeemi ei õnnestunud üles laadida."
        ,TranslationKeys.EASEMENT_LAYER_MISSING: "Servituudi kiht on seadistamata või puudub projektist. Palun seadista kõigepealt Seadetes Servituudi põhikiht."
        ,TranslationKeys.EASEMENT_LAYER_INVALID_GEOMETRY: "Seadistatud Servituudi kiht peab olema polügoonkiht, et lõpliku lõike geomeetriat salvestada."
        ,TranslationKeys.EASEMENT_LAYER_SAVE_SUCCESS: "Lõplik lõige salvestati Servituudi põhikihile {layer}."
        ,TranslationKeys.EASEMENT_LAYER_SAVE_FAILED: "Lõplikku lõiget ei õnnestunud Servituudi põhikihile salvestada. Detailid: {error}"
        ,TranslationKeys.WORKS_REPOSITION_START_FAILED: "Töö ümberpaigutamise kaardivalikut ei saanud käivitada."
        ,TranslationKeys.WORKS_REPOSITION_FEATURE_NOT_FOUND: "Tööd {task_id} ei leitud seadistatud Tööde kihilt."
        ,TranslationKeys.WORKS_REPOSITION_SAVE_FAILED: "Töö {task_id} uue kaardiasukoha salvestamine ebaõnnestus. Detailid: {error}"
        ,TranslationKeys.WORKS_REPOSITION_SUCCESS: "Töö {task_id} asukoht edukalt uuendatud."
        ,TranslationKeys.EASEMENT_ATTACH_EXISTING_START_FAILED: "Olemasoleva servituudijoonise sidumise kaardivalikut ei saanud käivitada."
        ,TranslationKeys.EASEMENT_ATTACH_EXISTING_FEATURE_NOT_FOUND: "Klikitud asukohast ei leitud servituudi objekti. Palun kliki otse servituudi polügoonile."
        ,TranslationKeys.EASEMENT_ATTACH_EXISTING_SAVE_FAILED: "Backendi servituudi {item_id} sidumine valitud kaardiobjektiga ebaõnnestus. Detailid: {error}"
        ,TranslationKeys.EASEMENT_ATTACH_EXISTING_SUCCESS: "Backendi servituut {item_id} seoti valitud kaardiobjektiga edukalt."
        ,TranslationKeys.EASEMENT_ATTACH_EXISTING_CONFLICT_MESSAGE: "Klikitud servituudi objekt on juba seotud backendi servituudiga {current_id}.\n\nSidumine servituudiga {new_id} on blokeeritud. Palun vali enne, mida olemasoleva objektiga teha."
        ,TranslationKeys.EASEMENT_ATTACH_EXISTING_DELETE_OPTION: "Kustuta objekt"
        ,TranslationKeys.EASEMENT_ATTACH_EXISTING_ARCHIVE_OPTION: "Arhiveeri objekt"
        ,TranslationKeys.EASEMENT_ATTACH_EXISTING_CANCEL_OPTION: "Loobu"
        ,TranslationKeys.EASEMENT_ATTACH_EXISTING_DELETE_SUCCESS: "Olemasolev backendi servituudiga {item_id} seotud objekt kustutati."
        ,TranslationKeys.EASEMENT_ATTACH_EXISTING_DELETE_FAILED: "Olemasoleva backendi servituudiga {item_id} seotud objekti kustutamine ebaõnnestus. Detailid: {error}"
        ,TranslationKeys.EASEMENT_ATTACH_EXISTING_ARCHIVE_SUCCESS: "Olemasolev backendi servituudiga {item_id} seotud objekt arhiveeriti, määrates staatuseks (puudub)."
        ,TranslationKeys.EASEMENT_ATTACH_EXISTING_ARCHIVE_FAILED: "Olemasoleva backendi servituudiga {item_id} seotud objekti arhiveerimine ebaõnnestus. Detailid: {error}"
        ,TranslationKeys.EASEMENT_DRAW_NEW_START_FAILED: "Uue servituudi objekti joonistamist kaardil ei saanud käivitada."
        ,TranslationKeys.EASEMENT_DRAW_NEW_SAVE_FAILED: "Uus kaardiobjekt loodi, kuid selle sidumine backendi servituudiga {item_id} ebaõnnestus. Detailid: {error}"
        ,TranslationKeys.EASEMENT_DRAW_NEW_SUCCESS: "Uus kaardiobjekt loodi ja seoti backendi servituudiga {item_id}."
        ,TranslationKeys.EASEMENT_EDIT_GEOMETRY_NOT_FOUND: "Backendi servituudi {item_id} jaoks ei leitud seotud kaardiobjekti."
        ,TranslationKeys.EASEMENT_EDIT_GEOMETRY_START_FAILED: "Seotud servituudi objekti geomeetria muutmist ei saanud käivitada."
        ,TranslationKeys.EASEMENT_EDIT_GEOMETRY_READY: "Seotud servituudi objekt {item_id} on nüüd muutmiseks valitud. Kasuta QGIS-i liigutamise ja tippude tööriistu ning salvesta kihi muudatused pärast lõpetamist."
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
        ,TranslationKeys.TASK_FILES_PDF_RUNTIME_UNSUPPORTED: "Sisseehitatud PDF eelvaade ei ole selles QGIS-i käitusajas saadaval. Praegune käitusaeg: Qt {qt_version}, PyQt {pyqt_version}.\n\nAinult eraldi PyQt6 paigaldamisest tavaliselt QGIS pluginate jaoks ei piisa. QGIS peab ise töötama uuema Qt/PyQt käitusajaga, kus on PDF-e toetav WebEngine.\n\nSoovitus: uuenda QGIS-i uuemale versioonile, mis sisaldab Qt6/PyQt6 ja Qt WebEngine PDF tuge."
        ,TranslationKeys.TASK_FILES_OPEN_FAILED: "Faili {name} ei saanud avada."
        ,TranslationKeys.TASK_FILES_EXTERNAL_OPEN_CONFIRM: "Fail avatakse arvuti vaikimisi rakenduses.\n\nFail: {name}\nTüüp: .{extension}\n\nAva ainult siis, kui usaldad faili ja selle üleslaadijat. Kas jätkata?"
        ,TranslationKeys.TASK_FILES_EXTERNAL_OPEN_BLOCKED: "Faili {name} ei saa turvakaalutlustel välise rakendusega avada."
        ,TranslationKeys.DESCRIPTION_LINK_WEB_CONFIRM: "Veebiaadress avatakse arvuti vaikebrauseris.\n\nAadress: {url}{http_warning}\n\nKas jätkata?"
        ,TranslationKeys.DESCRIPTION_LINK_HTTP_WARNING: "\n\nHoiatus: aadress kasutab krüpteerimata HTTP-ühendust."
        ,TranslationKeys.DESCRIPTION_LINK_FOLDER_CONFIRM: "Kaust avatakse arvuti failihalduris.\n\nKaust: {path}\n\nKas jätkata?"
        ,TranslationKeys.DESCRIPTION_LINK_NETWORK_CONFIRM: "See sihtkoht asub võrgus. Jätkamisel loob Windows ühenduse näidatud serveri või võrgukettaga.\n\nServer või võrguketas: {host}\nTee: {path}\n\nJätka ainult siis, kui tunned ja usaldad seda sihtkohta. Kas jätkata?"
        ,TranslationKeys.DESCRIPTION_LINK_FILE_CONFIRM: "Fail avatakse arvuti vaikimisi rakenduses.\n\nFail: {path}\nTüüp: .{extension}\n\nAva ainult siis, kui usaldad faili. Kas jätkata?"
        ,TranslationKeys.DESCRIPTION_LINK_BLOCKED: "Linki ei saa turvakaalutlustel avada. Lubatud on HTTP- ja HTTPS-aadressid ning absoluutsed kohaliku või kinnitatud võrgutee failid ja kaustad.\n\nSihtkoht: {target}"
        ,TranslationKeys.DESCRIPTION_LINK_NOT_FOUND: "Lingi sihtkohta ei leitud või sellele puudub juurdepääs.\n\nSihtkoht: {target}"
        ,TranslationKeys.DESCRIPTION_LINK_OPEN_FAILED: "Lingi sihtkohta ei saanud avada.\n\nSihtkoht: {target}"
        ,TranslationKeys.TASK_FILES_UPLOAD_DIALOG_TITLE: "Vali üleslaetavad failid"
        ,TranslationKeys.TASK_FILES_UPLOAD_DIALOG_FILTER: "Kõik failid (*.*)"
        ,TranslationKeys.TASK_FILES_UPLOAD_SUCCESS: "Üles laaditi {count} faili."
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
        ,TranslationKeys.GEOSPATIAL_LAYER_MAPPER_HELPER_TITLE: "Geospatiali kihi mapper"
        ,TranslationKeys.GEOSPATIAL_LAYER_MAPPER_HELPER_DESCRIPTION: "Nähtav ainult Geospatiali režiimis. Avab migratsioonidialoogi, millega saab vanemast kihist andmed valitud Geospatiali põhikihile kaardistada, koos geomeetria ülekandega ja puuduolevate väljade vaikeväärtustega."
        ,TranslationKeys.GEOSPATIAL_LAYER_MAPPER_OPEN_BUTTON: "Ava mapper"
        ,TranslationKeys.GEOSPATIAL_LAYER_MAPPER_DIALOG_TITLE: "Kaardista vana kiht Geospatiali kihile"
        ,TranslationKeys.GEOSPATIAL_LAYER_MAPPER_DIALOG_DESCRIPTION: "Sihtmoodul: {module}. Valitud Geospatiali kiht: {target}. Vali olemasolev lähtekiht, kontrolli väljade kaardistust ja kanna seejärel atribuudid ning geomeetria Geospatiali kihile üle."
        ,TranslationKeys.GEOSPATIAL_LAYER_MAPPER_SOURCE_LAYER: "Lähtekiht"
        ,TranslationKeys.GEOSPATIAL_LAYER_MAPPER_TARGET_FIELD: "Geospatiali väli"
        ,TranslationKeys.GEOSPATIAL_LAYER_MAPPER_SOURCE_FIELD: "Lähteväli"
        ,TranslationKeys.GEOSPATIAL_LAYER_MAPPER_DEFAULT_VALUE: "Vaikeväärtus"
        ,TranslationKeys.GEOSPATIAL_LAYER_MAPPER_NONE_OPTION: "Ära kaardista"
        ,TranslationKeys.GEOSPATIAL_LAYER_MAPPER_NO_DEFAULT: "Vaikeväärtus puudub"
        ,TranslationKeys.GEOSPATIAL_LAYER_MAPPER_USE_DEFAULT: "Kasuta vaikeväärtust"
        ,TranslationKeys.GEOSPATIAL_LAYER_MAPPER_OPTIONAL_DEFAULT: "Valikuline vaikeväärtus"
        ,TranslationKeys.GEOSPATIAL_LAYER_MAPPER_RUN_BUTTON: "Kanna andmed üle"
        ,TranslationKeys.GEOSPATIAL_LAYER_MAPPER_TARGET_REQUIRED: "Vali sellele moodulile esmalt Geospatiali põhikiht."
        ,TranslationKeys.GEOSPATIAL_LAYER_MAPPER_SOURCE_REQUIRED: "Vali olemasolev lähtekiht, millest andmed üle kanda."
        ,TranslationKeys.GEOSPATIAL_LAYER_MAPPER_NO_TARGET_FIELDS: "Valitud Geospatiali kihil ei ole kaardistatavaid välju."
        ,TranslationKeys.GEOSPATIAL_LAYER_MAPPER_CONFIRM_TITLE: "Kas kanda andmed Geospatiali kihile üle?"
        ,TranslationKeys.GEOSPATIAL_LAYER_MAPPER_CONFIRM_BODY: "Lähtekiht: {source}\nSihtkiht: {target}\nTöödeldavaid objekte: {count}\n\nMapper kopeerib geomeetria ja kaardistatud väärtused Geospatiali kihile. Kui võimalik, uuendatakse sama välise id-ga olemasolevad sihtobjektid."
        ,TranslationKeys.GEOSPATIAL_LAYER_MAPPER_EDIT_START_FAILED: "Geospatiali sihtkihi muutmisrežiimi ei saanud käivitada."
        ,TranslationKeys.GEOSPATIAL_LAYER_MAPPER_ADD_FEATURE_FAILED: "Migreeritud objekti lisamine Geospatiali sihtkihile ebaõnnestus."
        ,TranslationKeys.GEOSPATIAL_LAYER_MAPPER_COMMIT_FAILED: "Migreeritud objektide salvestamine Geospatiali sihtkihile ebaõnnestus."
        ,TranslationKeys.GEOSPATIAL_LAYER_MAPPER_RESULT_SUCCESS: "Migratsioon lõpetati. Lisatud: {inserted}, uuendatud: {updated}, muutmata: {skipped}."
        ,TranslationKeys.GEOSPATIAL_LAYER_MAPPER_RESULT_WITH_ERRORS: "Migratsioon lõpetati vigadega. Lisatud: {inserted}, uuendatud: {updated}, muutmata: {skipped}.\n\nVead:\n{errors}"
        ,TranslationKeys.PROJECTS_TEMP_LAYER_HELPER_TITLE: "Ajutine Projektide kihi abiline"
        ,TranslationKeys.PROJECTS_TEMP_LAYER_HELPER_DESCRIPTION: "Ajutine arendusabiline. Loob või laeb polügoonpõhise Projektide kihi kas valitud viitekihi GeoPackage'i sisse või uude eraldiseisvasse GeoPackage-faili. Loodud kiht määratakse kohe aktiivseks Projektide põhikihiks."
        ,TranslationKeys.PROJECTS_TEMP_LAYER_CREATE_BUTTON: "Loo/lae ajutine Projektide GPKG kiht"
        ,TranslationKeys.PROJECTS_TEMP_LAYER_PROMPT_TITLE: "Loo/lae ajutine Projektide kiht"
        ,TranslationKeys.PROJECTS_TEMP_LAYER_PROMPT_LABEL: "Projektide kihi nimi:"
        ,TranslationKeys.PROJECTS_TEMP_LAYER_REFERENCE_REQUIRED: "Vali kõigepealt Projektide viitekiht või seadista Kinnistute põhikiht. Abiline vajab olemasolevat kihti, et määrata uue Projektide kihi CRS."
        ,TranslationKeys.PROJECTS_TEMP_LAYER_GPKG_REQUIRED: "Valitud valik kasutab viitekihi GeoPackage'i, kuid viitekiht ei ole GeoPackage-põhine. Vali Projektide kihi valikust GPKG kiht või kasuta hoopis eraldiseisva GeoPackage'i loomist."
        ,TranslationKeys.PROJECTS_TEMP_LAYER_STORAGE_TITLE: "Kuhu Projektide kiht salvestada?"
        ,TranslationKeys.PROJECTS_TEMP_LAYER_STORAGE_MESSAGE: "Vali, kas Projektide kiht luua/laadida viitekihi GeoPackage'i sisse või uue eraldiseisva GeoPackage-failina."
        ,TranslationKeys.PROJECTS_TEMP_LAYER_STORAGE_EXISTING: "Kasuta viitekihi GeoPackage'i"
        ,TranslationKeys.PROJECTS_TEMP_LAYER_STORAGE_STANDALONE: "Loo eraldiseisev GeoPackage-fail"
        ,TranslationKeys.PROJECTS_TEMP_LAYER_SAVE_DIALOG_TITLE: "Vali eraldiseisva Projektide GeoPackage'i asukoht"
        ,TranslationKeys.PROJECTS_TEMP_LAYER_OVERWRITE_TITLE: "Kas kirjutada olemasolev GeoPackage üle?"
        ,TranslationKeys.PROJECTS_TEMP_LAYER_OVERWRITE_MESSAGE: "Fail on juba olemas:\n{path}\n\nKas kirjutada see üle ja luua uus eraldiseisev Projektide GeoPackage?"
        ,TranslationKeys.PROJECTS_TEMP_LAYER_NAME_REQUIRED: "Palun sisesta kihi nimi."
        ,TranslationKeys.PROJECTS_TEMP_LAYER_CREATE_FAILED: "Ajutise Projektide kihi '{name}' loomine/laadimine ebaõnnestus.\n\nDetailid: {error}"
        ,TranslationKeys.PROJECTS_TEMP_LAYER_READY: "Ajutine Projektide kiht '{name}' on valmis ja määrati Projektide põhikihiks."
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
    ,TranslationKeys.START: "Algus"
    ,TranslationKeys.CREATED: "Loodud"
    ,TranslationKeys.UPDATED: "Muudetud"
    ,TranslationKeys.STATUS_WIDGET_CHANGE_TOOLTIP: "Klõpsa staatuse muutmiseks"
    ,TranslationKeys.STATUS_WIDGET_NO_OPTIONS: "Selle mooduli jaoks pole praegu ühtegi staatust saadaval."
    ,TranslationKeys.STATUS_WIDGET_UPDATE_FAILED: "Kirje staatuse uuendamine ebaõnnestus."
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
    ,TranslationKeys.PROJECT_BOARD_NOT_STARTED_STATUS_TITLE: "Vali alustamata staatused"
    ,TranslationKeys.PROJECT_BOARD_NOT_STARTED_STATUS_DESCRIPTION: "Vali taustastaatused, mille korral kuvatakse selle mooduli kirjed projekti ülevaate tahvlil veerus Alustamata."
    ,DialogLabels.PROJECTS_SOURCE_FOLDER: "Projektide lähtekaust"
    ,DialogLabels.PROJECTS_TARGET_FOLDER: "Projektide sihtkaust"
    ,DialogLabels.PROJECTS_PHOTO_FOLDER: "Projektide fotode kaust"
    ,DialogLabels.PROJECTS_PREFERED_FOLDER_NAME_STRUCTURE: "Eelistatud kausta nime struktuur"
    ,DialogLabels.PROJECTS_PREFERED_FOLDER_NAME_STRUCTURE_ENABLED: "Luba eelistatud kausta nime struktuur"
    ,DialogLabels.PROJECTS_PREFERED_FOLDER_NAME_STRUCTURE_RULE: "Eelistatud kausta nime struktuuri reegel"
    ,DialogLabels.EASEMENT_LAYER_STATUS_MAPPING: "Servituudi kihi staatuste seos"
    ,DialogLabels.PROJECT_BOARD_NOT_STARTED_STATUSES: "Projekti tahvli alustamata staatused"
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
