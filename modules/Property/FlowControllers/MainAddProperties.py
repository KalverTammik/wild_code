import re
import requests
from requests.exceptions import Timeout

from PyQt5.QtWidgets import QMessageBox
from qgis.core import QgsFeature

from ....python.api_client import APIClient
from ....languages.translation_keys import TranslationKeys
from ....constants.layer_constants import IMPORT_PROPERTY_TAG
from ....constants.settings_keys import SettingsService
from ....constants.cadastral_fields import Katastriyksus
from ....utils.mapandproperties.PropertyTableManager import PropertyTableManager
from ....utils.mapandproperties.PropertyDataLoader import PropertyDataLoader
from ....languages.language_manager import LanguageManager 
from ....utils.MapTools.MapHelpers import MapHelpers, FeatureActions
from ....utils.url_manager import Module
from ....python.GraphQLQueryLoader import GraphQLQueryLoader
from .UpdatePropertyData import UpdatePropertyData
from ....widgets.DateHelpers import DateHelpers
from ....utils.TagsEngines import TagsHelpers, TagsEngines


class MainAddPropertiesFlow:
    """
    Handles user interaction events and coordinates between data loading and UI updates.
    Separated for better maintainability.
    """
    

    @staticmethod
    def start_adding_properties(table=None):
        """
        Goals:
        1) Add selected properties from the import layer to:
                - the main property layer;
                - the backend database via GraphQL API (when needed).

        2) Avoid duplicates by cadastral number (per property):
                We always check BOTH:
                - backend existence (GraphQL) by cadastral number
                - main-layer existence (map) by cadastral number

                Decision rules (per cadastral number):
                - Not in backend AND not in main layer:
                    - create in backend; copy feature import -> main layer.
                - In backend AND in main layer:
                    - default: skip;
                    - if import has newer version: offer ARCHIVE/REPLACE flow.
                - In backend BUT missing in main layer:
                    - ask user what to do (recommended):
                        - copy feature import -> main layer (no backend create), OR skip.
                - In main layer BUT missing in backend:
                    - ask user what to do (recommended):
                        - create backend record from main/import data, OR skip.

        3) Archive/replace when import is newer:
                “Newer version” definition:
                - compare timestamps: import feature `Katastriyksus.muudet`
                    against backend `lastUpdated` (and optionally main-layer `muudet`).
                - treat import as newer if:
                    import_muudet > max(backend_lastUpdated, main_layer_muudet).


                - transfer existing feature from main layer -> archive layer
                    - Archive layer is identified by user in Settings;
                    - if not set, show error and advise user to configure it by prompting the layer 
                    configurer in the pop-up.
                    - if user skips archiving abort session and warn user that no properties were added. 
                    and full loop was aborted as archiving properties is essential to avoid duplicates and 
                    data loss.
                - update backend database to mark existing property as "archived"
                    "archived" meaning: 
                        - setting a tag in backend "Arhiveeritud".
                            - if no tags exist, create new tag;
                        - Updating Addres field to append " (archived on YYYY-MM-DD)".
                - create new property in backend from import data
                - delete existing feature from main layer
                - copy feature from import layer -> main layer



        Returns: bool - success status

        """
        table_manager = PropertyTableManager()
        selected_features = table_manager.get_selected_features(table)

        if not selected_features:
            return False

        layers = MainAddPropertiesFlow._prepare_layers()
        if layers:
            import_layer, target_layer, archive_layer = layers
            if not import_layer or not target_layer or not archive_layer:
                print ("One or more required layers are missing (import, target, or archive). Aborting.")
                return False
            
            tag_name = TagsEngines.ARHIVEERITUD_TAG_NAME
            module = Module.PROPERTY.name
            tag_id = TagsHelpers.check_if_tag_exists(tag_name=tag_name, module=module)

            if not target_layer.isEditable():
                target_layer.startEditing()

            if archive_layer and not archive_layer.isEditable():
                archive_layer.startEditing()
            try:
                for feature in selected_features:
                    data, tunnus, siht_data, last_updated_str = PropertyDataLoader().prepare_data_for_import_stage1(feature)
                    # last updated str is iso format string
                    #check if property with tunnus already exists in Kavtro
                    backend_info = BackendPropertyVerifier.verify_properties_by_cadastral_number(tunnus)
                    exists_backend = backend_info.get("exists")
                    archived_only_backend = bool(backend_info.get("archived_only"))
                    active_count = backend_info.get("active_count")
                    archived_count = backend_info.get("archived_count")
                    backend_last_updated = backend_info.get("LastUpdated") #is iso format string

                    if isinstance(active_count, int) and isinstance(archived_count, int):
                        if active_count + archived_count > 1:
                            print(
                                f"Multiple backend matches for {tunnus}: active={active_count}, archived={archived_count}. Using first active if present."
                            )

                    exists_map = MapHelpers.if_feature_exists_in_layer(target_layer, Katastriyksus.tunnus, tunnus)
                    existing_map_feature = None
                    main_layer_muudet = None
                    if exists_map:
                        print(f"Property with cadastral ID {tunnus} already exists in the main layer.")
                        matches = MapHelpers.find_features_by_fields_and_values(target_layer, Katastriyksus.tunnus, [tunnus])
                        if matches:
                            existing_map_feature = matches[0]
                            try:
                                main_layer_muudet = existing_map_feature.attribute(Katastriyksus.muudet)
                            except Exception:
                                main_layer_muudet = None

                    if exists_backend is None:
                        # Backend lookup failed; don't accidentally create duplicates.
                        err = backend_info.get("error")
                        print(f"Skipping cadastral ID {tunnus} due to backend lookup failure. {err or ''}")
                        continue

                    is_import_newer = MainAddPropertiesFlow._is_import_newer(
                        last_updated_str,
                        backend_last_updated,
                        main_layer_muudet,
                    )

                    # Step 2: decision matrix 
                    # A) Backend missing => create backend; copy import -> main if missing on map
                    if exists_backend is False:
                        archived_backend_id = None
                        try:
                            archived_backend_id = ((backend_info.get("property") or {}).get("id"))
                        except Exception:
                            archived_backend_id = None

                        if archived_only_backend and archived_backend_id:
                            msg = QMessageBox()
                            msg.setIcon(QMessageBox.Question)
                            msg.setWindowTitle("Archived backend match")
                            msg.setText(
                                f"Backend has an archived property for cadastral number {tunnus}.\n\n"
                                f"What do you want to do?"
                            )
                            btn_unarchive = msg.addButton("Unarchive existing", QMessageBox.AcceptRole)
                            btn_create_new = msg.addButton("Create new", QMessageBox.ActionRole)
                            btn_skip = msg.addButton("Skip", QMessageBox.RejectRole)
                            msg.setDefaultButton(btn_unarchive)
                            msg.exec_()
                            clicked = msg.clickedButton()

                            if clicked == btn_skip:
                                print(f"Skipped {tunnus} (archived-only backend match).")
                                continue

                            if clicked == btn_unarchive:
                                if not UpdatePropertyData._unarchive_property_data(item_id=archived_backend_id):
                                    QMessageBox.warning(
                                        None,
                                        "Unarchive failed",
                                        f"Failed to unarchive backend property {archived_backend_id} for {tunnus}.",
                                    )
                                    continue

                                ok = UpdatePropertyData.update_single_property_item(
                                    archived_backend_id,
                                    data,
                                    siht_data,
                                )
                                if not ok:
                                    QMessageBox.warning(
                                        None,
                                        "Backend update failed",
                                        f"Unarchived backend property but failed to update data for {tunnus}.",
                                    )

                                # Now treat it as backend-existing for map decisions.
                                if not exists_map:
                                    title = "Property exists"
                                    text = (
                                        f"Property {tunnus} is now active in backend but is missing from main layer.\n\n"
                                        f"Copy feature from import layer to main layer?"
                                    )
                                    reply = QMessageBox.question(
                                        None,
                                        title,
                                        text,
                                        QMessageBox.Yes | QMessageBox.No,
                                        QMessageBox.Yes,
                                    )
                                    if reply == QMessageBox.Yes:
                                        ok2, msg2 = FeatureActions.copy_feature_to_layer(feature, target_layer)
                                        if not ok2:
                                            QMessageBox.warning(None, "Copy failed", msg2)
                                    else:
                                        print(f"Skipped copying {tunnus} into main layer (backend re-activated).")

                                # If main already has feature, nothing to do on map here.
                                continue

                            # If user chose Create new, fall through to existing creation logic.

                        if exists_map:
                            title = "Backend missing"
                            if archived_only_backend:
                                text = (
                                    f"Property {tunnus} exists in main layer. Backend has only an archived record for this cadastral number.\n\n"
                                    f"Create a new ACTIVE backend record from import data?"
                                )
                            else:
                                text = (
                                    f"Property {tunnus} exists in main layer but is missing from backend.\n\n"
                                    f"Create backend record from import data?"
                                )
                            reply = QMessageBox.question(
                                None,
                                title,
                                text,
                                QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.Yes,
                            )
                            if reply != QMessageBox.Yes:
                                print(f"Skipped backend creation for {tunnus} (main layer already has feature).")
                                continue

                        property_id = MainAddPropertiesFlow.add_single_property_item(data, siht_data)
                        print(f"Added property with ID: {property_id}")

                        if not exists_map:
                            ok, msg = FeatureActions.copy_feature_to_layer(feature, target_layer)
                            if not ok:
                                print(f"Failed to copy import feature to main layer for {tunnus}: {msg}")
                        continue

                    # B) Backend exists
                    if exists_backend is True and not exists_map:
                        if is_import_newer:
                            backend_prop = backend_info.get("property") or {}
                            backend_id = backend_prop.get("id")
                            if backend_id:
                                ok = UpdatePropertyData.update_single_property_item(backend_id, data, siht_data)
                                if ok:
                                    print(f"Updated backend property {backend_id} from import for {tunnus}.")
                                else:
                                    print(f"Backend update failed for {tunnus} (id={backend_id}).")
                            else:
                                print(f"Backend id missing for {tunnus}; cannot update.")

                        # Step 3: ask user what to do when backend exists but map is missing
                        title = "Property exists"
                        text = (
                            f"Property {tunnus} exists in backend but is missing from main layer.\n\n"
                            f"Copy feature from import layer to main layer?"
                        )
                        reply = QMessageBox.question(
                            None,
                            title,
                            text,
                            QMessageBox.Yes | QMessageBox.No,
                            QMessageBox.Yes,
                        )
                        if reply == QMessageBox.Yes:
                            ok, msg = FeatureActions.copy_feature_to_layer(feature, target_layer)
                            if not ok:
                                QMessageBox.warning(None, "Copy failed", msg)
                        else:
                            print(f"Skipped copying {tunnus} into main layer (backend already exists).")
                        continue

                    # C) Backend exists and map exists => skip, unless import is newer (archive/replace)
                    if exists_backend is True and exists_map:
                        if not is_import_newer:
                            print(
                                f"Property with cadastral ID {tunnus} already exists in backend and main layer. Skipping."
                            )
                            continue

                        title = "Newer import detected"
                        text = (
                            f"Property {tunnus} exists in backend and main layer, but import appears newer.\n\n"
                            f"Archive/replace existing property?\n"
                            f"- Moves existing main-layer feature to archive layer\n"
                            f"- Marks backend property as archived\n"
                            f"- Replaces main-layer feature with import feature"
                        )
                        reply = QMessageBox.question(
                            None,
                            title,
                            text,
                            QMessageBox.Yes | QMessageBox.No,
                            QMessageBox.No,
                        )
                        if reply != QMessageBox.Yes:
                            print(f"Skipped archive/replace for {tunnus}.")
                            continue

                        if not existing_map_feature:
                            QMessageBox.warning(
                                None,
                                "Replace failed",
                                f"Could not locate existing main-layer feature for {tunnus} to archive/replace.",
                            )
                            raise RuntimeError(f"Missing existing map feature for {tunnus}")

                        if not archive_layer or not archive_layer.isValid():
                            QMessageBox.warning(
                                None,
                                "Archive layer missing",
                                "Archive layer is not configured or missing; cannot archive/replace.",
                            )
                            raise RuntimeError("Archive layer missing")

                        if not archive_layer.isEditable():
                            archive_layer.startEditing()

                        ok, msg = FeatureActions.copy_feature_to_layer(existing_map_feature, archive_layer)
                        if not ok:
                            QMessageBox.warning(None, "Archive copy failed", msg)
                            raise RuntimeError(f"Archive copy failed for {tunnus}: {msg}")

                        try:
                            deleted = target_layer.deleteFeature(existing_map_feature.id())
                        except Exception:
                            deleted = False
                        if not deleted:
                            QMessageBox.warning(
                                None,
                                "Replace failed",
                                f"Failed to delete existing main-layer feature for {tunnus}.",
                            )
                            raise RuntimeError(f"Delete existing feature failed for {tunnus}")

                        ok, msg = FeatureActions.copy_feature_to_layer(feature, target_layer)
                        if not ok:
                            QMessageBox.warning(None, "Replace failed", msg)
                            raise RuntimeError(f"Copy import->main failed for {tunnus}: {msg}")

                        backend_prop = backend_info.get("property") or {}
                        backend_id = backend_prop.get("id")
                        if backend_id:
                            if not UpdatePropertyData._archive_a_propertie(backend_id, archive_tag=tag_id):
                                QMessageBox.warning(
                                    None,
                                    "Backend archive failed",
                                    f"Failed to mark backend property as archived for {tunnus}.",
                                )
                                raise RuntimeError(f"Backend archive failed for {tunnus}")

                            # Prefer docstring behavior: create a new backend record from import.
                            # If backend rejects duplicates, fall back to updating the existing record.
                            new_id = MainAddPropertiesFlow.add_single_property_item(data, siht_data)
                            if not new_id:
                                # Creating a new backend record can fail if the backend enforces uniqueness.
                                # In that case, reactivate (unarchive) and update the existing record.
                                UpdatePropertyData._unarchive_property_data(item_id=backend_id)
                                ok = UpdatePropertyData.update_single_property_item(backend_id, data, siht_data)
                                if ok:
                                    print(f"Updated backend property {backend_id} from import for {tunnus}.")
                                else:
                                    raise RuntimeError(f"Backend create+fallback update failed for {tunnus}")
                            else:
                                print(f"Created new backend property {new_id} from import for {tunnus}.")
                        else:
                            print(f"Backend id missing for {tunnus}; cannot archive/replace backend record.")
                            raise RuntimeError(f"Backend id missing for {tunnus}")

                        continue

                if archive_layer and archive_layer.isEditable():
                    if not archive_layer.commitChanges():
                        msg = "; ".join(archive_layer.commitErrors() or [])
                        archive_layer.rollBack()
                        if target_layer.isEditable():
                            target_layer.rollBack()
                        print(f"Failed to commit changes to archive layer: {msg}")
                        return False

                if not target_layer.commitChanges():
                    msg = "; ".join(target_layer.commitErrors() or [])
                    target_layer.rollBack()
                    if archive_layer and archive_layer.isEditable():
                        archive_layer.rollBack()
                    print(f"Failed to commit changes to main layer: {msg}")
                    return False
                
                return True
            except Exception as e:
                if target_layer.isEditable():
                    target_layer.rollBack()
                if archive_layer and archive_layer.isEditable():
                    archive_layer.rollBack()
                print(f"Failed to add property: {e}")              

        return False

    @staticmethod
    def _prepare_layers() -> None:
        # 1) Import layer filtering (optional but explicit)
        import_layer = MapHelpers._get_layer_by_tag(IMPORT_PROPERTY_TAG)
        #set import layer and active layer 
        if import_layer:
            # Choose ONE behavior:
            # A) filter by explicit ids (recommended, deterministic)
            MapHelpers.set_layer_filter_to_selected_features(import_layer)

        # 2) Activate main target layer
        target_layer_name = SettingsService().module_main_layer_name(Module.PROPERTY.value)
        active_layer = MapHelpers.find_layer_by_name(target_layer_name)

        # 3) Take care of Archive layer presence
        archive_layer_name = SettingsService().module_archive_layer_name(Module.PROPERTY.value)
        archive_layer = MapHelpers.find_layer_by_name(archive_layer_name)
        
        #4) Ensure archive layers are visible
        if active_layer:
            MapHelpers.ensure_layer_visible(active_layer, make_active=True)
        if archive_layer:
            MapHelpers.ensure_layer_visible(archive_layer, make_active=False)

        return import_layer, active_layer, archive_layer
    

    @staticmethod
    def add_single_property_item(item, siht_data):

        module = Module.PROPERTY.name

        file_name =  'Add_property.graphql'
        query = GraphQLQueryLoader().load_query_by_module(module, file_name)
        print(f"Loaded query: {query}")

        variables = {
            "input": item
        }
        print(f"variables for adding property: {variables}")
        try:
            client = APIClient()
            data = client.send_query(query, variables=variables)

            created = data.get("createProperty") 
            property_id = created.get("id")
            if not property_id:
                print(f"CreateProperty did not return an id. Response: {data}")
                return None
            if property_id:
                UpdatePropertyData.add_additional_property_data(property_id, siht_data)

            return property_id
        
        except Exception as e:
            print(f"GraphQL request failed for cadastralUnitNumber={item}: {e}")
            return None



    @staticmethod
    def _is_import_newer(import_date_str: str, backend_date_str: str, main_layer_muudet=None) -> bool:
        """Return True if import is newer than max(backend, main-layer).

        Accepts ISO-like strings, QDate/QDateTime, or other values for `main_layer_muudet`.
        Non-parseable dates return False.
        """
        print(
            f"Comparing import date '{import_date_str}' with backend date '{backend_date_str}' and main-layer date '{main_layer_muudet}'"
        )

        import_dt = DateHelpers.parse_iso(str(import_date_str) if import_date_str is not None else "")
        backend_dt = DateHelpers.parse_iso(str(backend_date_str) if backend_date_str is not None else "")

        main_s = None
        if main_layer_muudet is not None:
            if isinstance(main_layer_muudet, str):
                main_s = DateHelpers().date_to_iso_string(main_layer_muudet)
            else:
                main_s = DateHelpers().date_to_iso_string(main_layer_muudet)
        main_dt = DateHelpers.parse_iso(str(main_s) if main_s else "")

        if not import_dt:
            return False

        candidates = [dt for dt in [backend_dt, main_dt] if dt]
        if not candidates:
            return False

        return import_dt > max(candidates)


class BackendPropertyVerifier:
    @staticmethod
    def verify_properties_by_cadastral_number(item):

        item = ("" if item is None else str(item)).strip()
        if not item:
            return {"exists": False, "property": None, "tags": [], "error": None}

        module = Module.PROPERTY.name

        file =  "id_number.graphql"
        query = GraphQLQueryLoader().load_query_by_module(module, file)


        end_cursor = None

        # NOTE:
        # - This query is `properties(...)` (see python/queries/graphql/properties/id_number.graphql)
        # - For operator `IN`, backend typically expects an array.
        # - For a single cadastral number, `EQ` is the safest.
        variables = {
            # IMPORTANT: backend can contain both archived and active records for the same cadastral number.
            # Fetch enough rows (and paginate if needed) so we can correctly classify.
            "first": 50,
            "after": end_cursor,
            "search": None,
            "where": {
                "AND": [
                    {
                        "column": "CADASTRAL_UNIT_NUMBER",
                        "operator": "EQ",
                        "value": item,
                    }
                ]
            },
        }

        try:
            client = APIClient()

            nodes = []
            safety_cap = 200
            while True:
                variables["after"] = end_cursor
                data = client.send_query(query, variables=variables)
                print(f"ExistingPropertyVerifier response data: {data}")

                props = data.get("properties") or {}
                page_info = props.get("pageInfo") or {}
                edges = props.get("edges") or []
                if edges:
                    for e in edges:
                        n = (e or {}).get("node")
                        if isinstance(n, dict) and n:
                            nodes.append(n)

                # stop conditions
                try:
                    total = int(page_info.get("total"))
                except Exception:
                    total = None

                has_next = bool(page_info.get("hasNextPage"))
                end_cursor = page_info.get("endCursor")
                if not has_next:
                    break
                if not end_cursor:
                    break
                if total is not None and len(nodes) >= total:
                    break
                if len(nodes) >= safety_cap:
                    break

            if not nodes:
                return {
                    "exists": False,
                    "archived_only": False,
                    "active_count": 0,
                    "archived_count": 0,
                    "property": None,
                    "tags": [],
                    "error": None,
                }

            def _is_archived_property(node_dict: dict) -> bool:
                if not isinstance(node_dict, dict):
                    return False
                tags_edges_local = ((node_dict.get("tags") or {}).get("edges") or [])
                for te in tags_edges_local:
                    tag_node = (te or {}).get("node")
                    if not isinstance(tag_node, dict):
                        continue
                    name = (tag_node.get("name") or "").strip().lower()
                    if name == TagsEngines.ARHIVEERITUD_TAG_NAME.strip().lower():
                        return True

                display = (node_dict.get("displayAddress") or "").strip().lower()
                prefix = (TagsEngines.ARHIVEERITUD_NAME_ADDITION or "").strip().lower()
                if prefix and display.startswith(prefix):
                    return True
                return False

            archived_nodes = [n for n in nodes if _is_archived_property(n)]
            active_nodes = [n for n in nodes if n not in archived_nodes]

            active_props = []
            for n in active_nodes:
                if isinstance(n, dict):
                    active_props.append(
                        {
                            "id": n.get("id"),
                            "cadastralUnitNumber": n.get("cadastralUnitNumber"),
                            "displayAddress": n.get("displayAddress"),
                        }
                    )

            archived_props = []
            for n in archived_nodes:
                if isinstance(n, dict):
                    archived_props.append(
                        {
                            "id": n.get("id"),
                            "cadastralUnitNumber": n.get("cadastralUnitNumber"),
                            "displayAddress": n.get("displayAddress"),
                        }
                    )

            chosen = (active_nodes[0] if active_nodes else (archived_nodes[0] if archived_nodes else {}))

            tags_edges = ((chosen.get("tags") or {}).get("edges") or [])
            tags = []
            for edge in tags_edges:
                tag_node = (edge or {}).get("node")
                if isinstance(tag_node, dict) and tag_node:
                    tags.append(tag_node)

            active_count = len(active_nodes)
            archived_count = len(archived_nodes)
            archived_only = (active_count == 0 and archived_count > 0)

            # Backwards-compatible `exists`: True only if an ACTIVE backend property exists.
            return {
                "exists": active_count > 0,
                "archived_only": archived_only,
                "active_count": active_count,
                "archived_count": archived_count,
                "active_ids": [p.get("id") for p in active_props if p.get("id")],
                "archived_ids": [p.get("id") for p in archived_props if p.get("id")],
                "active_properties": active_props,
                "archived_properties": archived_props,
                "property": {
                    "id": chosen.get("id"),
                    "cadastralUnitNumber": chosen.get("cadastralUnitNumber"),
                    "displayAddress": chosen.get("displayAddress"),
                },
                "FirstRegistration": chosen.get("cadastralUnitFirstRegistration"),
                "LastUpdated": chosen.get("cadastralUnitLastUpdated"),
                "tags": tags,
                "error": None,
            }
        
        
        except Exception as e:
            print(f"GraphQL request failed for cadastralUnitNumber={item}: {e}")
            return {"exists": None, "property": None, "FirstRegistration": None, "LastUpdated": None, "tags": [], "error": str(e)}
        