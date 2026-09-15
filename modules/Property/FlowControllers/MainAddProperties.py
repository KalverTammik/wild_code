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
from ....utils.url_manager import Module, ModuleSupports
from ....python.GraphQLQueryLoader import GraphQLQueryLoader
from .UpdatePropertyData import UpdatePropertyData
from ....widgets.DateHelpers import DateHelpers
from ....utils.TagsEngines import TagsEngines
from ....utils.moduleSwitchHelper import ModuleSwitchHelper
from ....Logs.python_fail_logger import PythonFailLogger
from ....utils.mapandproperties.ArchiveLayerHandler import ArchiveLayerHandler
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
        active_layer = MapHelpers.find_layer_by_name(target_layer_name)
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
        archive_layer = MapHelpers.find_layer_by_name(archive_layer_name) if archive_layer_name else None

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
    def _prepare_layers() -> tuple[object, object, object]:
        # 1) Resolve the import layer without changing its provider subset. The
        # selected feature payloads are passed directly to the add flow. Leaving
        # a village-specific subset behind would make the next village load look
        # incomplete and could invalidate archive decisions.
        import_layer = MapHelpers.get_layer_by_tag(IMPORT_PROPERTY_TAG)

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

        layers = MainAddPropertiesFlow._prepare_layers()
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



    @staticmethod
    def _is_import_newer(import_date_str: str, backend_date_str: str, main_layer_muudet=None) -> bool:
        """Return True if import is newer than max(backend, main-layer).

        Accepts ISO-like strings, QDate/QDateTime, or other values for `main_layer_muudet`.
        Non-parseable dates return False.
        """
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

        # These are cadastral dates (the import payload also uses YYYY-MM-DD).
        # Backend ISO timestamps may include a timezone; compare calendar dates
        # consistently instead of mixing timezone-aware and naive datetimes.
        return import_dt.date() > max(dt.date() for dt in candidates)


class BackendPropertyVerifier:
    # Cache status ids for the process; statuses do not change at runtime for this plugin.
    _status_cache: dict[str, Optional[str]] = {}

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
        except (ApiRateLimitError, RequestCancelled):
            raise
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
