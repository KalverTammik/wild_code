import os
from typing import Optional

from PyQt5.QtCore import QCoreApplication

from ....python.api_client import APIClient
from ....python.api_rate_limit import ApiRateLimitError, RequestCancelled
from ....languages.translation_keys import TranslationKeys
from ....constants.layer_constants import IMPORT_PROPERTY_TAG
from ....constants.settings_keys import SettingsService
from ....constants.cadastral_fields import Katastriyksus
from ....languages.language_manager import LanguageManager 
from ....utils.MapTools.MapHelpers import MapHelpers, FeatureActions
from ....utils.url_manager import Module
from ....python.GraphQLQueryLoader import GraphQLQueryLoader
from .UpdatePropertyData import UpdatePropertyData
from ....utils.TagsEngines import TagsEngines
from ....utils.moduleSwitchHelper import ModuleSwitchHelper
from ....Logs.python_fail_logger import PythonFailLogger
from ....utils.mapandproperties.ArchiveLayerHandler import ArchiveLayerHandler
from ....utils.mapandproperties.PropertyDataLoader import PropertyDataLoader
from ....utils.messagesHelper import ModernMessageDialog


class MainAddPropertiesFlow:
    """
    Handles user interaction events and coordinates between data loading and UI updates.
    Separated for better maintainability.
    """

    @staticmethod
    def preflight_archive_layer_before_dialog() -> bool:
        """Ensure archive layer is configured/available BEFORE opening modal dialogs.

        Returns True when archive layer is ready; False when user chose to open Settings
        or cancel (caller should abort opening the dialog).
        """

        target_layer_name = SettingsService().module_main_layer_name(Module.PROPERTY.value)
        active_layer = MapHelpers.resolve_layer(target_layer_name)
        if not active_layer or not active_layer.isValid():
            lm = LanguageManager()
            ModernMessageDialog.Warning_messages_modern(
                lm.translate(TranslationKeys.PROPERTY_MAIN_LAYER_MISSING_TITLE),
                lm.translate(TranslationKeys.PROPERTY_MAIN_LAYER_MISSING_BODY),
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
        archive_layer = MapHelpers.resolve_layer(archive_layer_name) if archive_layer_name else None

        if not active_layer:
            return None

        if not archive_layer_name or not archive_layer or not archive_layer.isValid():
            # User-driven resolution: either open Settings (layer configurer) or create/load an archive layer in the same GPKG.
            lm = LanguageManager()
            title = lm.translate(TranslationKeys.PROPERTY_ARCHIVE_LAYER_REQUIRED_TITLE)

            if not archive_layer_name:
                body = lm.translate(TranslationKeys.PROPERTY_ARCHIVE_LAYER_REQUIRED_BODY_NO_NAME)
            else:
                body = lm.translate(TranslationKeys.PROPERTY_ARCHIVE_LAYER_REQUIRED_BODY_NAME).format(
                    name=archive_layer_name
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
                        lm.translate(TranslationKeys.PROPERTY_OPEN_SETTINGS_FAILED_TITLE),
                        lm.translate(TranslationKeys.PROPERTY_OPEN_SETTINGS_FAILED_BODY).format(error=e),
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
                    lm.translate(TranslationKeys.PROPERTY_ARCHIVE_LAYER_NAME_PROMPT_TITLE),
                    lm.translate(TranslationKeys.PROPERTY_ARCHIVE_LAYER_NAME_PROMPT_LABEL),
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
                        lm.translate(TranslationKeys.PROPERTY_ARCHIVE_LAYER_CREATE_FAILED_TITLE),
                        lm.translate(TranslationKeys.PROPERTY_ARCHIVE_LAYER_CREATE_FAILED_BODY).format(
                            name=layer_name,
                            error=e,
                        ),
                    )
                    return None

                if not created_layer or not created_layer.isValid():
                    ModernMessageDialog.Error_messages_modern(
                        lm.translate(TranslationKeys.PROPERTY_ARCHIVE_LAYER_CREATE_FAILED_TITLE),
                        lm.translate(TranslationKeys.PROPERTY_ARCHIVE_LAYER_CREATE_FAILED_BODY_GENERIC).format(
                            name=layer_name
                        ),
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
                        sm.sync_module_layer_dropdown(
                            Module.PROPERTY.value,
                            layer_name,
                            kind="archive",
                            force=True,
                        )
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
    def _prepare_layers(main_layer=None) -> tuple[object, object, object]:
        # 1) Resolve the import layer without changing its provider subset. The
        # selected feature payloads are passed directly to the add flow. Leaving
        # a village-specific subset behind would make the next village load look
        # incomplete and could invalidate archive decisions.
        import_layer = MapHelpers.get_layer_by_tag(IMPORT_PROPERTY_TAG)

        # 2) Activate main target layer. A caller that already resolved and pinned a
        # specific layer instance (e.g. the archive plan) passes it as `main_layer`, so
        # a second, independent name-based lookup here can never land on a different
        # layer than the one the plan was built against when two layers share that name.
        if main_layer is not None and getattr(main_layer, "isValid", lambda: True)():
            active_layer = main_layer
        else:
            target_layer_name = SettingsService().module_main_layer_name(Module.PROPERTY.value)
            active_layer = MapHelpers.resolve_layer(target_layer_name)

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
    def archive_missing_from_import(tunnus_iterable, *, backend_allowed: Optional[set[str]] = None,
                                     main_layer=None) -> dict:
        """Archive properties that are absent from the current import.

        Moves matching MAIN-layer features to the archive layer and archives
        matching backend records. `backend_allowed` limits which tunnus values
        are eligible for backend archiving; when None, all provided tunnus are
        eligible (legacy behavior). `main_layer`, when given, is the exact layer
        instance the archive plan was computed against, and is used as-is instead
        of a fresh name-based lookup (see `_prepare_layers`).
        """

        unique_tunnus = sorted({str(t).strip() for t in (tunnus_iterable or []) if str(t).strip()})
        summary = {
            "total": len(unique_tunnus),
            "archived_backend": 0,
            "backend_failed": 0,
            "backend_skipped": 0,
            "backend_pending": [],
            "moved_map": 0,
            "errors": [],
        }

        if not unique_tunnus:
            return summary

        layers = MainAddPropertiesFlow._prepare_layers(main_layer)
        if not layers:
            summary["errors"].append("Layer preparation failed")
            return summary

        _import_layer, target_layer, archive_layer = layers
        if not target_layer or not archive_layer:
            summary["errors"].append("Missing target or archive layer")
            return summary

        # Never commit or roll back edit buffers that may belong to the user.
        if target_layer.isEditable() or archive_layer.isEditable():
            summary["errors"].append(
                "Main or archive layer is already in edit mode; archive plan was not applied"
            )
            return summary

        try:
            if not archive_layer.startEditing():
                summary["errors"].append("Archive layer could not enter edit mode")
                return summary

            source_ids = []
            moved_tunnused = set()
            try:
                matches_by_tunnus = PropertyDataLoader.read_features_by_field_values(
                    target_layer, Katastriyksus.tunnus, unique_tunnus, include_geometry=True, group=True)
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module=Module.PROPERTY.value,
                    event="archive_find_matches_failed",
                )
                matches_by_tunnus = {}

            for tunnus in unique_tunnus:
                matches = matches_by_tunnus.get(tunnus, [])

                if not matches:
                    summary["errors"].append(f"Main feature {tunnus} was not found")
                    break

                # Stage every archive copy first. No MAIN deletion starts until all
                # copies have been committed successfully.
                for feat in matches:
                    ok, msg = FeatureActions.copy_feature_to_layer(
                        feat,
                        archive_layer,
                        attribute_overrides={
                            ArchiveLayerHandler.ARCHIVE_DATE_FIELD:
                                ArchiveLayerHandler.current_archive_timestamp(),
                        },
                    )
                    if ok:
                        source_ids.append(feat.id())
                        moved_tunnused.add(tunnus)
                    else:
                        summary["errors"].append(f"Copy {tunnus} failed: {msg}")
                        break

                if summary["errors"]:
                    break

            if summary["errors"]:
                archive_layer.rollBack()
                return summary

            if not archive_layer.commitChanges():
                msg = "; ".join(archive_layer.commitErrors() or [])
                archive_layer.rollBack()
                summary["errors"].append(f"Archive layer commit failed: {msg}")
                return summary

            # Archive copies are durable. Only now begin deleting their originals.
            if not target_layer.startEditing():
                summary["errors"].append(
                    "Main layer could not enter edit mode; committed archive copies were retained"
                )
                return summary
            if not target_layer.deleteFeatures(source_ids):
                target_layer.rollBack()
                summary["errors"].append(
                    "Main layer delete failed; committed archive copies were retained"
                )
                return summary
            if not target_layer.commitChanges():
                msg = "; ".join(target_layer.commitErrors() or [])
                target_layer.rollBack()
                summary["errors"].append(
                    f"Main layer commit failed; committed archive copies were retained: {msg}"
                )
                return summary

            summary["moved_map"] = len(source_ids)

            # Apply backend actions only after the corresponding map move is durable.
            backend_tunnused = sorted(t for t in moved_tunnused
                                      if backend_allowed is None or t in backend_allowed)
            summary["backend_skipped"] = len(moved_tunnused) - len(backend_tunnused)
            for index, tunnus in enumerate(backend_tunnused):
                summary["backend_pending"] = backend_tunnused[index + 1:]

                try:
                    backend_info = BackendPropertyVerifier.verify_properties_by_cadastral_number(tunnus)
                except Exception as exc:
                    backend_info = None
                    summary["backend_failed"] += 1
                    summary["errors"].append(f"Backend lookup {tunnus} failed: {exc}")
                    break

                if not isinstance(backend_info, dict) or backend_info.get("exists") is None:
                    summary["backend_failed"] += 1
                    summary["errors"].append(f"Backend lookup {tunnus} failed")
                    break

                active_ids = [
                    str(value).strip()
                    for value in (backend_info.get("active_ids") or [])
                    if str(value).strip()
                ]
                if len(active_ids) == 0:
                    summary["backend_skipped"] += 1
                    continue
                if len(active_ids) > 1:
                    summary["backend_failed"] += 1
                    summary["errors"].append(
                        f"Backend archive {tunnus} skipped: multiple active matches"
                    )
                    break

                property_id = active_ids[0]
                try:
                    archived = bool(UpdatePropertyData._archive_a_propertie(property_id))
                except Exception as exc:
                    archived = False
                    summary["errors"].append(
                        f"Archive backend {tunnus}/{property_id} failed: {exc}"
                    )
                if archived:
                    summary["archived_backend"] += 1
                else:
                    summary["backend_failed"] += 1
                    summary["errors"].append(
                        f"Archive backend {tunnus}/{property_id} failed"
                    )
                    break
            if summary["backend_pending"]:
                summary["errors"].append(LanguageManager().translate(
                    TranslationKeys.PROPERTY_ARCHIVE_PENDING).format(
                        tunnused=", ".join(summary["backend_pending"])))
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
    def add_single_property_item(item, siht_data, *, raise_on_error=False):

        module = Module.PROPERTY.name

        file_name =  'Add_property.graphql'
        query = GraphQLQueryLoader().load_query_by_module(module, file_name)

        variables = {
            "input": item
        }
        stage = "createProperty"
        property_id = None
        try:
            client = APIClient()
            # A lost response may still mean the create succeeded; never blindly create again.
            data = client.send_query(query, variables=variables, retry_network=False)

            created = data.get("createProperty") or {}
            property_id = created.get("id")
            if not property_id:
                raise RuntimeError(LanguageManager().translate(TranslationKeys.PROPERTY_ADD_RESPONSE_INVALID))
            stage = "updatePropertyIntendedUses"
            UpdatePropertyData.add_additional_property_data(property_id, siht_data)

            return property_id
        
        except RequestCancelled as exc:
            stage_key = (TranslationKeys.PROPERTY_ADD_STAGE_CREATE if stage == "createProperty"
                         else TranslationKeys.PROPERTY_ADD_STAGE_USES)
            message = LanguageManager().translate(TranslationKeys.PROPERTY_ADD_STAGE_CANCELLED).format(
                stage=LanguageManager().translate(stage_key))
            raise RequestCancelled(message) from exc
        except Exception as e:
            PythonFailLogger.log_exception(
                e,
                module=Module.PROPERTY.value,
                event="add_property_create_failed",
                extra={"tunnus": (item.get("cadastralUnit") or {}).get("number"),
                       "stage": stage, "item_id": property_id},
            )
            if raise_on_error or isinstance(e, ApiRateLimitError):
                stage_key = (TranslationKeys.PROPERTY_ADD_STAGE_CREATE if stage == "createProperty"
                             else TranslationKeys.PROPERTY_ADD_STAGE_USES)
                raise RuntimeError(f"{LanguageManager().translate(stage_key)}: {e}") from e
            return None


class BackendPropertyVerifier:
    """Reads the backend records of one cadastral number and splits them by state.

    The backend keeps the active/archived state in the property's own ``status`` field
    (PropertyStatus: ACTIVE or ARCHIVED), so one query per cadastral number is enough.
    A record saved before that field existed falls back to the archive tag rule.
    """

    @staticmethod
    def _is_archived(node: dict) -> bool:
        status = str((node or {}).get("status") or "").strip().upper()
        if status:
            return status == "ARCHIVED"
        return BackendPropertyVerifier._is_archived_by_tag(node)

    @staticmethod
    def _is_archived_by_tag(node: dict) -> bool:
        if not isinstance(node, dict):
            return False

        tag_name = (TagsEngines.ARHIVEERITUD_TAG_NAME or "").strip().lower()
        for edge in ((node.get("tags") or {}).get("edges") or []):
            tag_node = (edge or {}).get("node")
            if not isinstance(tag_node, dict):
                continue
            if tag_name and (tag_node.get("name") or "").strip().lower() == tag_name:
                return True

        prefix = (TagsEngines.ARHIVEERITUD_NAME_ADDITION or "").strip().lower()
        display = (node.get("displayAddress") or "").strip().lower()
        return bool(prefix and display.startswith(prefix))

    @staticmethod
    def _compact(node: dict) -> dict:
        return {
            "id": node.get("id"),
            "cadastralUnitNumber": node.get("cadastralUnitNumber"),
            "displayAddress": node.get("displayAddress"),
        }

    @staticmethod
    def _summary(active_nodes: list, archived_nodes: list) -> dict:
        if not active_nodes and not archived_nodes:
            return {
                "exists": False,
                "archived_only": False,
                "active_count": 0,
                "archived_count": 0,
                "property": None,
                "tags": [],
                "error": None,
            }

        chosen = active_nodes[0] if active_nodes else archived_nodes[0]
        tags = []
        for edge in ((chosen.get("tags") or {}).get("edges") or []):
            tag_node = (edge or {}).get("node")
            if isinstance(tag_node, dict) and tag_node:
                tags.append(tag_node)

        active_props = [BackendPropertyVerifier._compact(node) for node in active_nodes]
        archived_props = [BackendPropertyVerifier._compact(node) for node in archived_nodes]

        # `exists` stays backwards compatible: True only when an ACTIVE record exists.
        return {
            "exists": bool(active_nodes),
            "archived_only": not active_nodes and bool(archived_nodes),
            "active_count": len(active_nodes),
            "archived_count": len(archived_nodes),
            "active_ids": [prop.get("id") for prop in active_props if prop.get("id")],
            "archived_ids": [prop.get("id") for prop in archived_props if prop.get("id")],
            "active_properties": active_props,
            "archived_properties": archived_props,
            "property": BackendPropertyVerifier._compact(chosen),
            "FirstRegistration": chosen.get("cadastralUnitFirstRegistration"),
            "LastUpdated": chosen.get("cadastralUnitLastUpdated"),
            "tags": tags,
            "error": None,
        }

    @staticmethod
    def verify_properties_by_cadastral_number(item):

        item = ("" if item is None else str(item)).strip()
        if not item:
            return {"exists": False, "property": None, "tags": [], "error": None}

        query = GraphQLQueryLoader().load_query_by_module(Module.PROPERTY.name, "id_number.graphql")

        # The backend can hold both an active and an archived record for one cadastral
        # number, so read every match and split them by their status field.
        variables = {
            "first": 50,
            "after": None,
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
            nodes: list[dict] = []
            while True:
                QCoreApplication.processEvents()
                payload = client.send_query(query, variables=variables)
                props = (payload or {}).get("properties") or {}
                page_info = props.get("pageInfo") or {}
                for edge in (props.get("edges") or []):
                    node = (edge or {}).get("node")
                    if isinstance(node, dict) and node:
                        nodes.append(node)

                variables["after"] = page_info.get("endCursor")
                if not page_info.get("hasNextPage") or not variables["after"] or len(nodes) >= 200:
                    break

            archived_nodes = [node for node in nodes if BackendPropertyVerifier._is_archived(node)]
            active_nodes = [node for node in nodes if node not in archived_nodes]
            return BackendPropertyVerifier._summary(active_nodes, archived_nodes)
        
        
        except (ApiRateLimitError, RequestCancelled):
            raise
        except Exception as e:
            PythonFailLogger.log_exception(
                e,
                module=Module.PROPERTY.value,
                event="backend_verify_query_failed",
                extra={"tunnus": str(item or "")},
            )
            return {"exists": None, "property": None, "FirstRegistration": None, "LastUpdated": None, "tags": [], "error": str(e)}
