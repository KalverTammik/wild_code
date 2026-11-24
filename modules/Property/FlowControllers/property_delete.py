from ....python.api_client import APIClient
from ....constants.module_names import Module
from ....python.GraphQLQueryLoader import GraphQLQueryLoader
from ....languages.language_manager import LanguageManager
from ....languages.translation_keys import TranslationKeys
from ....utils.api_error_handling import user_message


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
        for edge in (((listing.get("properties") or {}).get("edges")) or []):
            node = (edge or {}).get("node") or {}
            if str(node.get("id") or "") == item:
                address = str(node.get("displayAddress") or "").strip()
                break
        return deleteProperty.PREVIEW_OK, {"id": item, "number": number, "address": address}

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
