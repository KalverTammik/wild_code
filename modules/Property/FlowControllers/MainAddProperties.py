import os
from typing import Optional

from PyQt5.QtCore import QCoreApplication

from ....python.api_client import APIClient
from ....languages.translation_keys import TranslationKeys
from ....constants.layer_constants import IMPORT_PROPERTY_TAG
from ....constants.settings_keys import SettingsService
from ....constants.cadastral_fields import Katastriyksus
from ....utils.mapandproperties.PropertyTableManager import PropertyTableManager
from ....utils.mapandproperties.PropertyDataLoader import PropertyDataLoader
from ....languages.language_manager import LanguageManager 
from ....utils.MapTools.MapHelpers import MapHelpers, FeatureActions
from ....utils.url_manager import Module, ModuleSupports
from ....python.GraphQLQueryLoader import GraphQLQueryLoader
from .UpdatePropertyData import UpdatePropertyData
from ....widgets.DateHelpers import DateHelpers
from ....utils.TagsEngines import TagsHelpers, TagsEngines
from ....utils.moduleSwitchHelper import ModuleSwitchHelper
from ....Logs.python_fail_logger import PythonFailLogger
from ....utils.mapandproperties.ArchiveLayerHandler import ArchiveLayerHandler
from ....utils.messagesHelper import ModernMessageDialog


class MainAddPropertiesFlow:
    """
    Handles user interaction events and coordinates between data loading and UI updates.
    Separated for better maintainability.
    """

    # Cooperative cancel flag for in-flight add operations (set by AddBatchRunner.cancel()).
    _cancel_requested: bool = False
    # Persist "yes to all" choice across batch invocations.
    _yes_to_all_copy_missing_map: bool = False

    @staticmethod
    def request_cancel() -> None:
        MainAddPropertiesFlow._cancel_requested = True

    @staticmethod
    def reset_cancel() -> None:
        MainAddPropertiesFlow._cancel_requested = False

    @staticmethod
    def reset_yes_to_all_flags() -> None:
        MainAddPropertiesFlow._yes_to_all_copy_missing_map = False
    

    @staticmethod
    def start_adding_properties(table=None, *, selected_features=None):
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
        if selected_features is None:
            table_manager = PropertyTableManager()
            selected_features = table_manager.get_selected_features(table)

        if not selected_features:
            return False

        layers = MainAddPropertiesFlow._prepare_layers()
        if layers:
            import_layer, target_layer, archive_layer = layers
            if not import_layer or not target_layer or not archive_layer:
                return False

            # Reset cooperative cancel at the start of each call.
            MainAddPropertiesFlow.reset_cancel()
            # Do not reset yes-to-all here; batch runner handles it so choice persists across invocations within a run.

            # Preload backend status ids once for this run to avoid repeating GraphQL calls per property.
            BackendPropertyVerifier.warm_status_cache()
            
            tag_name = TagsEngines.ARHIVEERITUD_TAG_NAME
            module = Module.PROPERTY.name
            tag_id = TagsHelpers.check_if_tag_exists(tag_name=tag_name, module=module)

            lm = LanguageManager()

            if not target_layer.isEditable():
                target_layer.startEditing()

            if archive_layer and not archive_layer.isEditable():
                archive_layer.startEditing()

            try:
                for feature in selected_features:
                    if MainAddPropertiesFlow._cancel_requested:
                        print("Add canceled before processing next feature; rolling back pending edits.")
                        if target_layer.isEditable():
                            target_layer.rollBack()
                        if archive_layer and archive_layer.isEditable():
                            archive_layer.rollBack()
                        return False

                    QCoreApplication.processEvents()
                    data, tunnus, siht_data, last_updated_str = PropertyDataLoader().prepare_data_for_import_stage1(feature)
                    # last updated str is iso format string
                    #check if property with tunnus already exists in Kavtro
                    backend_info = BackendPropertyVerifier.verify_properties_by_cadastral_number(tunnus)
                    exists_backend = backend_info.get("exists")
                    backend_prop = backend_info.get("property") or {}
                    backend_id = backend_prop.get("id")
                    backend_cadastral = backend_prop.get("cadastralUnitNumber")
                    backend_name = (backend_prop.get("displayAddress") or "").strip()
                    import_name = (data.get("address") or {}).get("street")
                    identifiers_unchanged = bool(
                        exists_backend
                        and backend_id
                        and str(tunnus) == str(backend_cadastral)
                        and (import_name or "").strip() == backend_name
                    )
                    archived_only_backend = bool(backend_info.get("archived_only"))
                    active_count = backend_info.get("active_count")
                    archived_count = backend_info.get("archived_count")
                    backend_last_updated = backend_info.get("LastUpdated") #is iso format string

                    if MainAddPropertiesFlow._cancel_requested:
                        print("Add canceled; stopping before comparing dates.")
                        if target_layer.isEditable():
                            target_layer.rollBack()
                        if archive_layer and archive_layer.isEditable():
                            archive_layer.rollBack()
                        return False

                    if isinstance(active_count, int) and isinstance(archived_count, int):
                        if active_count + archived_count > 1:
                            print(
                                f"Multiple backend matches for {tunnus}: active={active_count}, archived={archived_count}. Using first active if present."
                            )

                    matches = MapHelpers.find_features_by_fields_and_values(target_layer, Katastriyksus.tunnus, [tunnus])
                    exists_map = bool(matches)
                    existing_map_feature = matches[0] if matches else None
                    main_layer_muudet = None
                    if existing_map_feature:
                        print(f"Property with cadastral ID {tunnus} already exists in the main layer.")
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

                    # If identifiers are unchanged, prefer in-place backend update and skip archive/replace.
                    updated_in_place = False
                    if identifiers_unchanged:
                        if backend_id:
                            ok = UpdatePropertyData.update_single_property_item(backend_id, data, siht_data)
                            if ok:
                                print(f"Updated backend property {backend_id} in place for {tunnus} (identifiers unchanged).")
                                updated_in_place = True
                            else:
                                print(f"Failed to update backend property {backend_id} for {tunnus} (identifiers unchanged path).")
                        # When only backend is updated, still allow map handling below.

                    # Step 2: decision matrix 
                    # A) Backend missing => create backend; copy import -> main if missing on map
                    if exists_backend is False:
                        archived_backend_id = None
                        try:
                            archived_backend_id = ((backend_info.get("property") or {}).get("id"))
                        except Exception:
                            archived_backend_id = None

                        if archived_only_backend and archived_backend_id:
                            btn_unarchive = lm.translate(TranslationKeys.UNARCHIVE_EXISTING) or "Unarchive existing"
                            btn_create_new = lm.translate(TranslationKeys.CREATE_NEW) or "Create new"
                            btn_skip = lm.translate(TranslationKeys.SKIP) or "Skip"

                            choice = ModernMessageDialog.ask_choice_modern(
                                "Archived backend match",
                                f"Backend has an archived property for cadastral number {tunnus}.\n\n"
                                f"What do you want to do?",
                                buttons=[btn_unarchive, btn_create_new, btn_skip],
                                default=btn_unarchive,
                                cancel=btn_skip,
                            )

                            if choice == btn_skip or choice is None:
                                print(f"Skipped {tunnus} (archived-only backend match).")
                                continue

                            if choice == btn_unarchive:
                                if not UpdatePropertyData._unarchive_property_data(item_id=archived_backend_id):
                                    ModernMessageDialog.Error_messages_modern(
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
                                    ModernMessageDialog.Warning_messages_modern(
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
                                    reply = ModernMessageDialog.ask_choice_modern(
                                        title,
                                        text,
                                        buttons=[lm.translate(TranslationKeys.YES), lm.translate(TranslationKeys.NO)],
                                        default=lm.translate(TranslationKeys.YES),
                                        cancel=lm.translate(TranslationKeys.NO),
                                    )
                                    if reply == lm.translate(TranslationKeys.YES):
                                        ok2, msg2 = FeatureActions.copy_feature_to_layer(feature, target_layer)
                                        if not ok2:
                                            ModernMessageDialog.Error_messages_modern("Copy failed", msg2)
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
                            reply = ModernMessageDialog.ask_choice_modern(
                                title,
                                text,
                                buttons=[lm.translate(TranslationKeys.YES), lm.translate(TranslationKeys.NO)],
                                default=lm.translate(TranslationKeys.YES),
                                cancel=lm.translate(TranslationKeys.NO),
                            )
                            if reply != (lm.translate(TranslationKeys.YES)):
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
                        if is_import_newer and not updated_in_place:
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
                        reply = None
                        if MainAddPropertiesFlow._yes_to_all_copy_missing_map:
                            reply = lm.translate(TranslationKeys.YES) or "Yes"
                        else:
                            btn_yes = lm.translate(TranslationKeys.YES) or "Yes"
                            btn_no = lm.translate(TranslationKeys.NO) or "No"
                            btn_yes_all = lm.translate(TranslationKeys.YES_TO_ALL) or "Yes to all"

                            reply = ModernMessageDialog.ask_choice_modern(
                                title,
                                text,
                                buttons=[btn_yes, btn_no, btn_yes_all],
                                default=btn_yes,
                                cancel=btn_no,
                            )

                            if reply == btn_yes_all:
                                MainAddPropertiesFlow._yes_to_all_copy_missing_map = True
                                reply = btn_yes
                        if reply == (lm.translate(TranslationKeys.YES) or "Yes"):
                            ok, msg = FeatureActions.copy_feature_to_layer(feature, target_layer)
                            if not ok:
                                ModernMessageDialog.Error_messages_modern("Copy failed", msg)
                        else:
                            print(f"Skipped copying {tunnus} into main layer (backend already exists).")
                        continue

                    # C) Backend exists and map exists
                    if exists_backend is True and exists_map:
                        # Identifiers unchanged: only update when newer; no archiving here.
                        if identifiers_unchanged:
                            if is_import_newer and not updated_in_place and backend_id:
                                ok = UpdatePropertyData.update_single_property_item(backend_id, data, siht_data)
                                if ok:
                                    print(f"Updated backend property {backend_id} in place for {tunnus} (map present).")
                                else:
                                    print(f"Backend update failed for {tunnus} (id={backend_id}).")
                            else:
                                print(f"Property {tunnus} unchanged (identifiers match); skipping archive/replace.")
                            continue

                        # Identifiers differ: update backend if import is newer; do not archive in this flow.
                        if is_import_newer and backend_id:
                            ok = UpdatePropertyData.update_single_property_item(backend_id, data, siht_data)
                            if ok:
                                print(f"Updated backend property {backend_id} (identifiers differ) for {tunnus}.")
                            else:
                                print(f"Backend update failed for {tunnus} (id={backend_id}).")
                        else:
                            print(f"Property {tunnus} not newer or missing backend id; skipping archive/replace.")
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
    def preflight_archive_layer_before_dialog() -> bool:
        """Ensure archive layer is configured/available BEFORE opening modal dialogs.

        Returns True when archive layer is ready; False when user chose to open Settings
        or cancel (caller should abort opening the dialog).
        """

        target_layer_name = SettingsService().module_main_layer_name(Module.PROPERTY.value)
        active_layer = MapHelpers.find_layer_by_name(target_layer_name)
        if not active_layer or not active_layer.isValid():
            ModernMessageDialog.Warning_messages_modern(
                "Main layer missing",
                "Main property layer is not found/invalid. Please configure it in Settings.",
            )
            return False

        archive_layer = MainAddPropertiesFlow._ensure_archive_layer_ready(active_layer)
        if not archive_layer:
            return False

        # Keep both visible so user immediately sees what will be used.
        MapHelpers.ensure_layer_visible(active_layer, make_active=True)
        MapHelpers.ensure_layer_visible(archive_layer, make_active=False)
        return True

    @staticmethod
    def _ensure_archive_layer_ready(active_layer):
        """Return a valid archive layer, or None if user cancels."""

        settings = SettingsService()
        archive_layer_name = (settings.module_archive_layer_name(Module.PROPERTY.value) or "").strip()
        archive_layer = MapHelpers.find_layer_by_name(archive_layer_name) if archive_layer_name else None

        if not active_layer:
            return None

        if not archive_layer_name or not archive_layer or not archive_layer.isValid():
            # User-driven resolution: either open Settings (layer configurer) or create/load an archive layer in the same GPKG.
            title = "Archive layer required"
            lm = LanguageManager()

            if not archive_layer_name:
                body = (
                    "Archive layer is not configured for Properties.\n\n"
                    "Choose what to do:\n"
                    "- Open Settings to pick an archive layer\n"
                    "- Create/load an archive layer inside the same GPKG as MAIN"
                )
            else:
                body = (
                    f"Archive layer '{archive_layer_name}' is not found/invalid in the project.\n\n"
                    "Choose what to do:\n"
                    "- Open Settings to pick an archive layer\n"
                    "- Create/load an archive layer inside the same GPKG as MAIN"
                )

            choice = ModernMessageDialog.ask_choice_modern(
                title,
                body,
                buttons=[
                    lm.translate(TranslationKeys.OPEN_SETTINGS),
                    lm.translate(TranslationKeys.CREATE_LOAD_IN_GPKG),
                    lm.translate(TranslationKeys.CANCEL_BUTTON),
                ],
                default=lm.translate(TranslationKeys.OPEN_SETTINGS),
                cancel=lm.translate(TranslationKeys.CANCEL_BUTTON),
            )

            if choice == (lm.translate(TranslationKeys.OPEN_SETTINGS)):
                try:
                    ModuleSwitchHelper.switch_module(
                        Module.SETTINGS.name,
                        focus_module=Module.PROPERTY.name,
                    )
                except Exception as e:
                    ModernMessageDialog.Warning_messages_modern(
                        "Open Settings failed",
                        f"Could not open Settings module automatically.\n\nError: {e}",
                    )
                return None

            if choice in (None, (lm.translate(TranslationKeys.CANCEL_BUTTON))):
                return None

            if choice == (lm.translate(TranslationKeys.CREATE_LOAD_IN_GPKG)):
                # Only supported when MAIN layer is sourced from a GeoPackage.
                try:
                    uri = active_layer.dataProvider().dataSourceUri() or ""
                except Exception:
                    uri = ""
                gpkg_path = (uri.split("|")[0] if uri else "").strip()
                if not gpkg_path or os.path.splitext(gpkg_path)[1].lower() != ".gpkg":
                    ModernMessageDialog.Warning_messages_modern(
                        lm.translate(TranslationKeys.PROPERTY_CANNOT_CREATE_ARCHIVE_TITLE),
                        lm.translate(TranslationKeys.PROPERTY_CANNOT_CREATE_ARCHIVE_BODY),
                    )
                    return None

                default_name = archive_layer_name
                layer_name, ok = ModernMessageDialog.get_text_modern(
                    "Create/Load archive layer",
                    "Archive layer name:",
                    text=default_name,
                )
                if not ok:
                    return None

                layer_name = (layer_name or "").strip()
                if not layer_name:
                    ModernMessageDialog.Warning_messages_modern(lm.translate(TranslationKeys.PROPERTY_INVALID_ARCHIVE_NAME_TITLE), lm.translate(TranslationKeys.PROPERTY_INVALID_ARCHIVE_NAME_BODY))
                    return None

                created_layer = None
                try:
                    created_layer = ArchiveLayerHandler.resolve_or_create_archive_layer(active_layer, layer_name)
                except Exception as e:
                    ModernMessageDialog.Error_messages_modern(
                        "Archive layer creation failed",
                        f"Failed to create/load archive layer '{layer_name}'.\n\nError: {e}",
                    )
                    return None

                if not created_layer or not created_layer.isValid():
                    ModernMessageDialog.Error_messages_modern(
                        "Archive layer creation failed",
                        f"Failed to create/load archive layer '{layer_name}'.",
                    )
                    return None

                # Persist to settings so next run doesn't need prompts.
                try:
                    settings.module_archive_layer_name(Module.PROPERTY.value, value=layer_name)
                except Exception as exc:
                    PythonFailLogger.log_exception(
                        exc,
                        module=Module.PROPERTY.value,
                        event="archive_layer_name_save_failed",
                        extra={"layer": layer_name},
                    )

                # If Settings UI is open, immediately sync the archive dropdown.
                try:
                    from ....dialog import PluginDialog

                    dlg = PluginDialog.get_instance() if PluginDialog else None
                    sm = getattr(dlg, "settingsModule", None) if dlg else None
                    if sm is not None:
                        sm.sync_module_archive_layer_dropdown(Module.PROPERTY.value, layer_name, force=True)
                except Exception as exc:
                    PythonFailLogger.log_exception(
                        exc,
                        module=Module.PROPERTY.value,
                        event="archive_layer_sync_failed",
                        extra={"layer": layer_name},
                    )

                return created_layer

        return archive_layer

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

        # 3) Ensure archive layer exists/valid (may prompt user)
        archive_layer = MainAddPropertiesFlow._ensure_archive_layer_ready(active_layer) if active_layer else None
        if active_layer and not archive_layer:
            return import_layer, active_layer, None
        
        #4) Ensure archive layers are visible
        if active_layer:
            MapHelpers.ensure_layer_visible(active_layer, make_active=True)
        if archive_layer:
            MapHelpers.ensure_layer_visible(archive_layer, make_active=False)

        return import_layer, active_layer, archive_layer


    @staticmethod
    def archive_missing_from_import(tunnus_iterable, *, backend_allowed: Optional[set[str]] = None) -> dict:
        """Archive properties that are absent from the current import.

        Moves matching MAIN-layer features to the archive layer and archives
        matching backend records. `backend_allowed` limits which tunnus values
        are eligible for backend archiving; when None, all provided tunnus are
        eligible (legacy behavior).
        """

        unique_tunnus = [t for t in {str(t).strip() for t in (tunnus_iterable or [])} if t]
        summary = {
            "total": len(unique_tunnus),
            "archived_backend": 0,
            "moved_map": 0,
            "errors": [],
        }

        if not unique_tunnus:
            return summary

        layers = MainAddPropertiesFlow._prepare_layers()
        if not layers:
            summary["errors"].append("Layer preparation failed")
            return summary

        _import_layer, target_layer, archive_layer = layers
        if not target_layer or not archive_layer:
            summary["errors"].append("Missing target or archive layer")
            return summary

        if not target_layer.isEditable():
            target_layer.startEditing()
        if not archive_layer.isEditable():
            archive_layer.startEditing()

        try:
            for tunnus in unique_tunnus:
                try:
                    matches = MapHelpers.find_features_by_fields_and_values(target_layer, Katastriyksus.tunnus, [tunnus])
                except Exception as exc:
                    PythonFailLogger.log_exception(
                        exc,
                        module=Module.PROPERTY.value,
                        event="archive_find_matches_failed",
                        extra={"tunnus": tunnus},
                    )
                    matches = []

                if not matches:
                    continue

                # Move map features into archive layer and remove from main layer.
                moved_ids = []
                for feat in matches:
                    ok, msg = FeatureActions.copy_feature_to_layer(feat, archive_layer)
                    if ok:
                        summary["moved_map"] += 1
                        moved_ids.append(feat.id())
                    else:
                        summary["errors"].append(f"Copy {tunnus} failed: {msg}")

                if moved_ids:
                    try:
                        target_layer.deleteFeatures(moved_ids)
                    except Exception as e:
                        summary["errors"].append(f"Delete {tunnus} failed: {e}")

                # Archive backend property best-effort.
                # Backend archive is optional per tunnus when backend_allowed is provided.
                backend_ok = (backend_allowed is None) or (tunnus in backend_allowed)
                if backend_ok:
                    try:
                        backend_info = BackendPropertyVerifier.verify_properties_by_cadastral_number(tunnus)
                    except Exception as e:
                        backend_info = None
                        summary["errors"].append(f"Backend lookup {tunnus} failed: {e}")

                    ids = []
                    if isinstance(backend_info, dict):
                        ids = backend_info.get("active_ids") or []
                        # If already archived, skip; only archive active ones.
                    for pid in ids:
                        ok = False
                        try:
                            ok = UpdatePropertyData._archive_a_propertie(pid)
                        except Exception as e:
                            summary["errors"].append(f"Archive backend {tunnus}/{pid} failed: {e}")
                        if ok:
                            summary["archived_backend"] += 1

            if archive_layer.isEditable():
                if not archive_layer.commitChanges():
                    msg = "; ".join(archive_layer.commitErrors() or [])
                    archive_layer.rollBack()
                    summary["errors"].append(f"Archive layer commit failed: {msg}")
            if target_layer.isEditable():
                if not target_layer.commitChanges():
                    msg = "; ".join(target_layer.commitErrors() or [])
                    target_layer.rollBack()
                    summary["errors"].append(f"Main layer commit failed: {msg}")
        except Exception as e:
            try:
                if target_layer.isEditable():
                    target_layer.rollBack()
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module=Module.PROPERTY.value,
                    event="archive_target_rollback_failed",
                )
            try:
                if archive_layer.isEditable():
                    archive_layer.rollBack()
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module=Module.PROPERTY.value,
                    event="archive_layer_rollback_failed",
                )
            summary["errors"].append(str(e))

        return summary
    

    @staticmethod
    def add_single_property_item(item, siht_data):

        module = Module.PROPERTY.name

        file_name =  'Add_property.graphql'
        query = GraphQLQueryLoader().load_query_by_module(module, file_name)
        #print(f"Loaded query: {query}")

        variables = {
            "input": item
        }
        #print(f"variables for adding property: {variables}")
        try:
            client = APIClient()
            data = client.send_query(query, variables=variables)

            created = data.get("createProperty") 
            property_id = created.get("id")
            if not property_id:
                #print(f"CreateProperty did not return an id. Response: {data}")
                return None
            if property_id:
                UpdatePropertyData.add_additional_property_data(property_id, siht_data)

            return property_id
        
        except Exception as e:
            #print(f"GraphQL request failed for cadastralUnitNumber={item}: {e}")
            return None



    @staticmethod
    def _is_import_newer(import_date_str: str, backend_date_str: str, main_layer_muudet=None) -> bool:
        """Return True if import is newer than max(backend, main-layer).

        Accepts ISO-like strings, QDate/QDateTime, or other values for `main_layer_muudet`.
        Non-parseable dates return False.
        """
        if MainAddPropertiesFlow._cancel_requested:
            return False

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
    # Cache status ids for the process; statuses do not change at runtime for this plugin.
    _status_cache: dict[str, Optional[str]] = {}

    @classmethod
    def warm_status_cache(cls) -> dict[str, Optional[str]]:
        """Resolve ACTIVE/ARCHIVED status ids once and cache them."""
        try:
            client = APIClient()
            # Populate cache only if missing; keep existing values to avoid extra calls.
            if "ACTIVE" not in cls._status_cache:
                cls._status_cache["ACTIVE"] = cls._resolve_property_status_id_by_name("ACTIVE", client)
            if "ARCHIVED" not in cls._status_cache:
                cls._status_cache["ARCHIVED"] = cls._resolve_property_status_id_by_name("ARCHIVED", client)
        except Exception as exc:
            # Best-effort; fall back to per-call resolution if warm-up fails.
            PythonFailLogger.log_exception(
                exc,
                module=Module.PROPERTY.value,
                event="property_status_cache_warm_failed",
            )
        return cls._status_cache

    @classmethod
    def _unwrap_data(cls, payload: dict) -> dict:
        if isinstance(payload, dict) and "data" in payload and isinstance(payload.get("data"), dict):
            return payload.get("data")
        return payload if isinstance(payload, dict) else {}

    @classmethod
    def _resolve_property_status_id_by_name(cls, status_name: str, client: APIClient) -> Optional[str]:
        name = ("" if status_name is None else str(status_name)).strip()
        if not name:
            return None

        # Serve from cache when present (even if None was cached from a previous failed lookup).
        if name.upper() in cls._status_cache:
            return cls._status_cache.get(name.upper())

        try:
            statuses_query = GraphQLQueryLoader().load_query_by_module(
                ModuleSupports.STATUSES.value,
                "ListModuleStatuses.graphql",
            )
        except Exception:
            return None

        variables_local = {
            "first": 50,
            "after": None,
            "where": {
                "AND": [
                    {"column": "MODULE", "operator": "EQ", "value": "PROPERTIES"},
                    {"column": "NAME", "operator": "EQ", "value": name},
                ]
            },
        }

        try:
            raw = client.send_query(statuses_query, variables=variables_local, return_raw=True) or {}
            data_local = cls._unwrap_data(raw)
            edges_local = ((data_local.get("statuses") or {}).get("edges") or [])
            for edge in edges_local:
                node = (edge or {}).get("node") or {}
                if (node.get("name") or "").strip().lower() == name.lower():
                    sid = node.get("id")
                    cls._status_cache[name.upper()] = str(sid) if sid else None
                    return cls._status_cache[name.upper()]
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.PROPERTY.value,
                event="property_status_lookup_failed",
                extra={"status": name},
            )

        cls._status_cache[name.upper()] = None
        return None

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

            def _fetch_nodes_for_where(where_obj: dict) -> list[dict]:
                nodes_local: list[dict] = []
                end_cursor_local = None
                safety_cap_local = 200
                vars_local = {
                    "first": 50,
                    "after": None,
                    "search": None,
                    "where": where_obj,
                }

                while True:
                    QCoreApplication.processEvents()
                    vars_local["after"] = end_cursor_local
                    payload = client.send_query(query, variables=vars_local)
                    props = (payload or {}).get("properties") or {}
                    page_info = props.get("pageInfo") or {}
                    edges = props.get("edges") or []
                    for e in edges:
                        n = (e or {}).get("node")
                        if isinstance(n, dict) and n:
                            nodes_local.append(n)

                    has_next = bool(page_info.get("hasNextPage"))
                    end_cursor_local = page_info.get("endCursor")
                    if not has_next or not end_cursor_local:
                        break
                    if len(nodes_local) >= safety_cap_local:
                        break

                return nodes_local

            # Preferred (new backend): classify by STATUS
            active_status_id = BackendPropertyVerifier._resolve_property_status_id_by_name("ACTIVE", client)
            archived_status_id = BackendPropertyVerifier._resolve_property_status_id_by_name("ARCHIVED", client)

            if active_status_id and archived_status_id:
                base_conditions = [
                    {"column": "CADASTRAL_UNIT_NUMBER", "operator": "EQ", "value": item},
                ]
                active_where = {"AND": base_conditions + [{"column": "STATUS", "operator": "IN", "value": [active_status_id]}]}
                archived_where = {"AND": base_conditions + [{"column": "STATUS", "operator": "IN", "value": [archived_status_id]}]}

                active_nodes = _fetch_nodes_for_where(active_where)
                archived_nodes = _fetch_nodes_for_where(archived_where)

                active_count = len(active_nodes)
                archived_count = len(archived_nodes)
                archived_only = (active_count == 0 and archived_count > 0)

                if active_count == 0 and archived_count == 0:
                    return {
                        "exists": False,
                        "archived_only": False,
                        "active_count": 0,
                        "archived_count": 0,
                        "property": None,
                        "tags": [],
                        "error": None,
                    }

                chosen = (active_nodes[0] if active_nodes else (archived_nodes[0] if archived_nodes else {}))
                tags_edges = ((chosen.get("tags") or {}).get("edges") or [])
                tags = []
                for edge in tags_edges:
                    tag_node = (edge or {}).get("node")
                    if isinstance(tag_node, dict) and tag_node:
                        tags.append(tag_node)

                def _compact(n: dict) -> dict:
                    return {
                        "id": n.get("id"),
                        "cadastralUnitNumber": n.get("cadastralUnitNumber"),
                        "displayAddress": n.get("displayAddress"),
                    }

                active_props = [_compact(n) for n in active_nodes if isinstance(n, dict)]
                archived_props = [_compact(n) for n in archived_nodes if isinstance(n, dict)]

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

            # Legacy fallback: fetch everything and classify by archived tag/prefix
            nodes = []
            safety_cap = 200
            while True:
                QCoreApplication.processEvents()
                variables["after"] = end_cursor
                data = client.send_query(query, variables=variables)

                props = data.get("properties") or {}
                page_info = props.get("pageInfo") or {}
                edges = props.get("edges") or []
                if edges:
                    for e in edges:
                        n = (e or {}).get("node")
                        if isinstance(n, dict) and n:
                            nodes.append(n)

                has_next = bool(page_info.get("hasNextPage"))
                end_cursor = page_info.get("endCursor")
                if not has_next:
                    break
                if not end_cursor:
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
                tag_name = (TagsEngines.ARHIVEERITUD_TAG_NAME or "").strip().lower()

                tags_edges_local = ((node_dict.get("tags") or {}).get("edges") or [])
                for te in tags_edges_local:
                    tag_node = (te or {}).get("node")
                    if not isinstance(tag_node, dict):
                        continue
                    name = (tag_node.get("name") or "").strip().lower()
                    if name == tag_name and tag_name:
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
        