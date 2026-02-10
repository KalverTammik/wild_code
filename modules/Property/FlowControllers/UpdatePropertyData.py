


from ....utils.url_manager import Module, ModuleSupports
from ....python.GraphQLQueryLoader import GraphQLQueryLoader
from ....python.api_client import APIClient

from ....utils.TagsEngines import TagsEngines
from ....Logs.python_fail_logger import PythonFailLogger

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
    def _resolve_property_status_id_by_name(status_name: str) -> str | None:
        """Resolve backend STATUS id (from module statuses) by name.

        This is used for archiving/unarchiving. If the backend doesn't support
        statuses for properties, returns None.
        """

        name = ("" if status_name is None else str(status_name)).strip()
        if not name:
            return None

        try:
            query_file = "ListModuleStatuses.graphql"
            query = GraphQLQueryLoader().load_query_by_module(module=ModuleSupports.STATUSES.value, query_filename=query_file)
        except Exception:
            return None

        # Properties module uses MODULE=PROPERTIES in filter helpers.
        module_value = "PROPERTIES"

        # Try to filter by module + name in one go.
        variables = {
            "first": 50,
            "after": None,
            "where": {
                "AND": [
                    {"column": "MODULE", "operator": "EQ", "value": module_value},
                    {"column": "NAME", "operator": "EQ", "value": name},
                ]
            },
        }

        try:
            payload = APIClient().send_query(query, variables=variables, return_raw=True) or {}
            edges = (((payload.get("data") or payload).get("statuses") or {}).get("edges") or [])
            for edge in edges:
                node = (edge or {}).get("node") or {}
                if (node.get("name") or "").strip().lower() == name.lower():
                    sid = node.get("id")
                    return str(sid) if sid else None
        except Exception:
            # Fall back to module-only fetch + local match.
            pass

        variables = {
            "first": 50,
            "after": None,
            "where": {"column": "MODULE", "operator": "EQ", "value": module_value},
        }
        try:
            payload = APIClient().send_query(query, variables=variables, return_raw=True) or {}
            edges = (((payload.get("data") or payload).get("statuses") or {}).get("edges") or [])
            for edge in edges:
                node = (edge or {}).get("node") or {}
                if (node.get("name") or "").strip().lower() == name.lower():
                    sid = node.get("id")
                    return str(sid) if sid else None
        except Exception:
            return None

        return None


    @staticmethod
    def _set_backend_property_status(item_id: str, *, status_name: str) -> bool:
        """Best-effort: update backend property status.

        Backend recently introduced status=ACTIVE/ARCHIVED for properties.
        We try a few input shapes to stay compatible with schema variations.
        """

        item_id = ("" if item_id is None else str(item_id)).strip()
        status_name = ("" if status_name is None else str(status_name)).strip().upper()
        if not item_id or not status_name:
            return False

        mutation_file = "UpdateProperty.graphql"
        try:
            mutation = GraphQLQueryLoader().load_query_by_module(module=Module.PROPERTY.name, query_filename=mutation_file)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.PROPERTY.value,
                event="property_status_mutation_load_failed",
            )
            return False

        client = APIClient()

        # 1) Try enum/string status directly
        for input_payload in (
            {"id": item_id, "status": status_name},
            {"id": item_id, "status": status_name.lower()},
        ):
            try:
                client.send_query(mutation, {"input": input_payload})
                return True
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module=Module.PROPERTY.value,
                    event="property_status_update_failed",
                    extra={"input": input_payload},
                )

        # 2) Try status relation via STATUS id
        status_id = UpdatePropertyData._resolve_property_status_id_by_name(status_name)
        if not status_id:
            return False

        for input_payload in (
            {"id": item_id, "status": status_id},
            {"id": item_id, "statusId": status_id},
            {"id": item_id, "status": {"connect": status_id}},
            {"id": item_id, "status": {"connect": [status_id]}},
        ):
            try:
                client.send_query(mutation, {"input": input_payload})
                return True
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module=Module.PROPERTY.value,
                    event="property_status_update_failed",
                    extra={"input": input_payload},
                )

        return False



    @staticmethod
    def _archive_a_propertie(item_id: str, archive_tag=None, recovery_name: str = None) -> bool:


        # Best-effort: mark backend status
        try:
            UpdatePropertyData._set_backend_property_status(item_id, status_name="ARCHIVED")
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.PROPERTY.value,
                event="property_backend_archive_status_failed",
            )

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
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.PROPERTY.value,
                event="property_archive_name_fetch_failed",
            )
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
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.PROPERTY.value,
                event="property_archive_tags_fetch_failed",
            )
            # If tags cannot be fetched, fall back to prefix-only behavior.
            tag_present = False

        if not tag_present and not had_prefix:
            # Already active (not archived) -> nothing to do.
            return False

        # Best-effort: mark backend status
        try:
            UpdatePropertyData._set_backend_property_status(item_id, status_name="ACTIVE")
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.PROPERTY.value,
                event="property_backend_activate_status_failed",
            )

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



