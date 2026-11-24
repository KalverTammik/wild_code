from ....python.api_client import APIClient
from ....constants.module_names import Module
from ....python.GraphQLQueryLoader import GraphQLQueryLoader
from ....languages.language_manager import LanguageManager
from ....languages.translation_keys import TranslationKeys
from ....utils.api_error_handling import user_message
from ....constants.cadastral_fields import Katastriyksus
from ....utils.MapTools.MapHelpers import FeatureActions, MapHelpers
from ....utils.settings_service import SettingsService
from qgis.core import QgsVectorLayer


class deleteProperty:
    PREVIEW_OK = "ok"
    PREVIEW_NOT_FOUND = "not_found"
    PREVIEW_FAILED = "failed"

    @staticmethod
    def load_preview(item: str) -> tuple[str, dict]:
        """Read the cadastral number and address of the record a delete by ID would remove.

        Returns (status, data). With PREVIEW_OK, data has "id", "number" and "address";
        with PREVIEW_FAILED, data has "error". Uses only the two read queries the plugin
        already sends: the record by ID gives its cadastral number, and the records of
        that number give the address of the one with this ID.
        """
        item = str(item or "").strip()
        module = Module.PROPERTY.name
        loader = GraphQLQueryLoader()
        client = APIClient()
        try:
            data = client.send_query(
                loader.load_query_by_module(module, "cadastralNumber_by_id.graphql"),
                variables={"id": item},
            ) or {}
            record = data.get("property") or {}
            number = str(record.get("cadastralUnitNumber") or "").strip()
            if not record or not number:
                return deleteProperty.PREVIEW_NOT_FOUND, {"id": item}

            listing = client.send_query(
                loader.load_query_by_module(module, "id_number.graphql"),
                variables={
                    "first": 50,
                    "after": None,
                    "search": None,
                    "where": {"AND": [{"column": "CADASTRAL_UNIT_NUMBER", "operator": "EQ", "value": number}]},
                },
            ) or {}
        except Exception as exc:
            return deleteProperty.PREVIEW_FAILED, {"id": item, "error": user_message(exc)}

        address = ""
        found = False
        properties = listing.get("properties") or {}
        edges = properties.get("edges") or []
        for edge in edges:
            node = (edge or {}).get("node") or {}
            if str(node.get("id") or "") == item:
                address = str(node.get("displayAddress") or "").strip()
                found = True
                break
        try:
            total = int((properties.get("pageInfo") or {}).get("total"))
        except (TypeError, ValueError):
            total = len(edges)
        # "others" decides whether the map feature may go: it belongs to this record only when no
        # other Kavitro record has the number. Unknown (record not in the listing) counts as shared.
        others = max(0, total - 1) if found else None
        return deleteProperty.PREVIEW_OK, {"id": item, "number": number, "address": address, "others": others}

    @staticmethod
    def property_map_layers() -> list:
        """The property main and archive layers that exist in the project (each once)."""
        settings = SettingsService()
        layers = []
        for name in (
            settings.module_main_layer_name(Module.PROPERTY.value) or "",
            settings.module_archive_layer_name(Module.PROPERTY.value) or "",
        ):
            layer = MapHelpers.resolve_layer(name) if str(name).strip() else None
            if isinstance(layer, QgsVectorLayer) and layer.isValid() and all(layer.id() != known.id() for known in layers):
                layers.append(layer)
        return layers

    @staticmethod
    def map_matches(number: str) -> list:
        """[(layer, feature count)] of the property layers holding this cadastral number.

        Raises LayerLookupError when a layer cannot be read: the caller must not promise
        a map change it cannot check.
        """
        matches = []
        for layer in deleteProperty.property_map_layers():
            features = MapHelpers.find_features_by_fields_and_values(layer, Katastriyksus.tunnus, [number], strict=True)
            if features:
                matches.append((layer, len(features)))
        return matches

    @staticmethod
    def remove_from_map(number: str, layers: list) -> tuple[int, list[str]]:
        """Delete this number's features from the given layers. Returns (removed, errors).

        FeatureActions refuses a layer already in edit mode, so the user's own pending
        edits are never saved along with the delete.
        """
        removed = 0
        errors: list[str] = []
        for layer in layers:
            ok, feature_ids, error = FeatureActions.delete_features_by_field_values(layer, Katastriyksus.tunnus, [number])
            if ok:
                removed += len(feature_ids or [])
            else:
                errors.append(f"{layer.name()}: {error}" if error else layer.name())
        return removed, errors

    @staticmethod
    def delete_single_item(item: str):

        module = Module.PROPERTY.name

        file =  "deleteProperty.graphql"
        query = GraphQLQueryLoader().load_query_by_module(module, file)


        variables = {
            "id": item  # ID of property i want to delete
            }

        client = APIClient()
        try:
            result = client.send_query(query, variables=variables, return_raw=True, with_success=True)
        except Exception as exc:
            return False, user_message(exc)

        deleted = (((result.get("raw") or {}).get("data") or {}).get("deleteProperty") or {})
        if result.get("success") is True and str(deleted.get("id") or "") == str(item):
            return True, ""

        err = result.get("error")
        lang = LanguageManager()
        if err:
            return False, lang.translate(TranslationKeys.PROPERTY_DELETE_FAILED_WITH_ERROR).format(id=item, error=err)
        return False, lang.translate(TranslationKeys.PROPERTY_DELETE_FAILED_DETAIL).format(id=item)
