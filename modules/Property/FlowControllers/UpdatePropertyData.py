


from ....utils.url_manager import Module
from ....python.GraphQLQueryLoader import GraphQLQueryLoader
from ....python.api_client import APIClient

from ....utils.TagsEngines import TagsEngines

class UpdatePropertyData:

    @staticmethod
    def _unwrap_gql_data(response):
        if isinstance(response, dict) and "data" in response and isinstance(response.get("data"), dict):
            return response.get("data")
        return response if isinstance(response, dict) else {}
        
    @staticmethod
    def _update_property_address_details(module, variables):
        

        file =  'UpdateProperty.graphql'
        query = GraphQLQueryLoader().load_query_by_module(module, file)

        client = APIClient()
        client.send_query(query, variables)

        
    @staticmethod
    def _update_property_street_name(propertie_id, new_name, module: str = None):
        
        mutation_file =  'UpdateStreetName.graphql'
        module = module or Module.PROPERTY.name
        mutation = GraphQLQueryLoader().load_query_by_module(module=module, query_filename=mutation_file)

        variables = {
            "input": {
                "id": propertie_id,
                "address": {
                    "street": new_name
                        }
            }
        }
        
        response = APIClient().send_query(mutation, variables)
        return UpdatePropertyData._unwrap_gql_data(response)
    
    @staticmethod
    def _update_property_tags(property_id: str, module: str, tag_id: str) -> bool:

        
        # Step 1: Load current tags
        query_file = 'Tags.graphql'
        query = GraphQLQueryLoader().load_query_by_module(module=module, query_filename=query_file)

        variables = {"id": property_id}

        response = APIClient().send_query(query, variables)
        data = UpdatePropertyData._unwrap_gql_data(response)
        current_tags = (((data or {}).get("property") or {}).get("tags") or {}).get("edges") or []
        current_tag_ids = [tag["node"]["id"] for tag in current_tags]
        
        if tag_id not in current_tag_ids:
            current_tag_ids.append(tag_id)

        update_guery_file = 'UpdateTags.graphql'
        update_mutation = GraphQLQueryLoader().load_query_by_module(module=module, query_filename=update_guery_file)
        variables = {
            "input": {
                "id": property_id,
                "tags": {
                    "associate": current_tag_ids
                }
            }
        }

        APIClient().send_query(update_mutation, variables)
        return True

    @staticmethod
    def _remove_property_tag(property_id: str, module: str, tag_id: str) -> bool:
        update_query_file = 'UpdateTags.graphql'
        update_mutation = GraphQLQueryLoader().load_query_by_module(module=module, query_filename=update_query_file)

        update_variables = {
            "input": {
                "id": property_id,
                "tags": {
                    "dissociate": [tag_id]
                }
            }
        }

        APIClient().send_query(update_mutation, update_variables)
        return True


    @staticmethod
    def _get_property_tags(property_id: str, module: str) -> list:
        query_file = 'Tags.graphql'
        query = GraphQLQueryLoader().load_query_by_module(module=module, query_filename=query_file)
        variables = {"id": property_id}

        response = APIClient().send_query(query, variables)
        data = UpdatePropertyData._unwrap_gql_data(response)
        edges = (((data or {}).get("property") or {}).get("tags") or {}).get("edges") or []
        tags = []
        for e in edges:
            n = (e or {}).get("node")
            if isinstance(n, dict) and n:
                tags.append(n)
        return tags


    @staticmethod
    def is_property_archived(property_id: str) -> bool:
        module = Module.PROPERTY.name
        tag_name = (TagsEngines.ARHIVEERITUD_TAG_NAME or "").strip().lower()

        try:
            tags = UpdatePropertyData._get_property_tags(property_id=property_id, module=module)
            for t in tags:
                name = (t.get("name") or "").strip().lower()
                if name == tag_name and tag_name:
                    return True
        except Exception:
            # fall back to name-prefix check
            pass

        try:
            current_name = str(UpdatePropertyData._get_properties_street_name_to_achived(property_id=property_id) or "")
        except Exception:
            current_name = ""

        prefix = (TagsEngines.ARHIVEERITUD_NAME_ADDITION or "") + " - "
        return bool(prefix and current_name.startswith(prefix))



    @staticmethod
    def _archive_a_propertie(item_id: str, archive_tag=None, recovery_name: str = None) -> bool:


        #print(f"✔️ Final item_id to use: {item_id} ({type(item_id)})")
        module= Module.PROPERTY.name
        #tag_name = "Arhiveeritud"
        tag_name = TagsEngines.ARHIVEERITUD_TAG_NAME
        tag_id = archive_tag
        if not tag_id:
            tag_id = TagsEngines.get_modules_tag_id_by_name(tag_name=tag_name, module=module)
            if tag_id is None:
                res = TagsEngines.create_tag(tag_name=tag_name, module=module)
                if res is not False:
                    tag_id = res
        tag_id = str(tag_id) if tag_id is not None else None

        if not tag_id:
            return False

        if not UpdatePropertyData._update_property_tags(property_id=item_id, module=module, tag_id=tag_id):
            return False

        #prefix = "ARHIIVEERITUD - "
        prefix = TagsEngines.ARHIVEERITUD_NAME_ADDITION + " - "

        current_name = str(UpdatePropertyData._get_properties_street_name_to_achived(property_id=item_id) or "")
        if recovery_name:
            new_name = recovery_name
        else:
            if current_name.startswith(prefix):
                new_name = current_name  # Already prefixed
            else:
                new_name = prefix + current_name
        
        UpdatePropertyData._update_property_street_name(propertie_id=item_id, new_name=new_name, module=module)
        return True

    @staticmethod
    def _unarchive_property_data(item_id: str) -> bool:

        module= Module.PROPERTY.name
        tag_name = TagsEngines.ARHIVEERITUD_TAG_NAME

        # Determine current archived state before attempting any changes.
        prefix = (TagsEngines.ARHIVEERITUD_NAME_ADDITION or "") + " - "
        try:
            current_name = str(UpdatePropertyData._get_properties_street_name_to_achived(property_id=item_id) or "")
        except Exception:
            current_name = ""
        had_prefix = bool(prefix and current_name.startswith(prefix))

        tag_present = False
        try:
            tags = UpdatePropertyData._get_property_tags(property_id=item_id, module=module)
            wanted = (tag_name or "").strip().lower()
            for t in tags:
                name = (t.get("name") or "").strip().lower()
                if wanted and name == wanted:
                    tag_present = True
                    break
        except Exception:
            # If tags cannot be fetched, fall back to prefix-only behavior.
            tag_present = False

        if not tag_present and not had_prefix:
            # Already active (not archived) -> nothing to do.
            return False

        # Remove archive tag (no need to create if missing!)
        tag_id = TagsEngines.get_modules_tag_id_by_name(tag_name=tag_name, module=module)
        if tag_id and tag_present:
            UpdatePropertyData._remove_property_tag(property_id=item_id, module=module, tag_id=tag_id)

        # Restore original name (remove prefix if it exists)
        if had_prefix:
            new_name = current_name.replace(prefix, "", 1)
            UpdatePropertyData._update_property_street_name(propertie_id=item_id, new_name=new_name, module=module)

        return True




    @staticmethod
    def _get_properties_street_name_to_achived(property_id) -> bool:
        #item_id: str, notes_text: str

        query = """
            query GetPropertyName($id: ID!) {
                property(id: $id) {
                    id
                    address {
                            street 
                        }
                    }
                }
            """
        variables = {"id": property_id}

        client = APIClient()
        response = client.send_query(query, variables)
        data = UpdatePropertyData._unwrap_gql_data(response)
        current_name = (((data or {}).get("property") or {}).get("address") or {}).get("street")

        return current_name



    @staticmethod
    def update_single_property_item(input_id, data, uses_input):
        """Update an existing backend property with import data + intended uses.

        Similar pattern to add_additional_property_data:
        - runs UpdateProperty mutation
        - then updates intended uses

        Returns: bool
        """
        module = Module.PROPERTY.name

        file = "UpdateProperty.graphql"
        query = GraphQLQueryLoader().load_query_by_module(module, file)

        payload = {}
        if isinstance(data, dict):
            payload.update(data)
        payload["id"] = input_id

        variables = {"input": payload}
        try:
            client = APIClient()
            response = client.send_query(query, variables)
            print(f"Updated property response: {response}")

            # Reuse the existing intended-uses update flow
            UpdatePropertyData.add_additional_property_data(input_id, uses_input)
            return True
        except Exception as e:
            print(f"Failed to update property {input_id}: {e}")
            return False

    @staticmethod
    def add_additional_property_data(input_id, uses_input):

        module = Module.PROPERTY.name

        file =  "Add_purpose.graphql"
        query = GraphQLQueryLoader().load_query_by_module(module, file)

    # Construct the list of PropertyIntendedUseInput
        variables = {
            "input": {
                "id": input_id,
                "uses": uses_input
            }
        }
        # Send the POST request to the GraphQL endpoint
        client = APIClient()
        response = client.send_query(query, variables)
        print(f"Added intended use data response: {response}")



