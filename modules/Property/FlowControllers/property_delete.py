from ....python.api_client import APIClient
from ....constants.module_names import Module
from ....python.GraphQLQueryLoader import GraphQLQueryLoader
from ....languages.language_manager import LanguageManager
from ....languages.translation_keys import TranslationKeys
from ....utils.api_error_handling import user_message


class deleteProperty:
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
