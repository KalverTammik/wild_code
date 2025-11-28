# Search Result Deep-Link Workplan

## Goal
Make the header search act as a deep link into module feeds: when a user selects a search result, load the specific record (contract, project, property) straight into the feed area regardless of the users current filters. Unsupported modules should show a friendly "coming soon" style message.

## Current Inputs
- `HeaderWidget` emits `searchResultClicked(module, item_id, title)` but nobody consumes it.
- Search results include several modules; we will initially focus on **contracts, projects, properties**.
- Feed rendering already exists in `FeedLogic`/`feed_load_engine` and per-module widgets.

## GraphQL Capability Audit
| Module     | Existing list query | ID-based query present? | Notes |
|------------|--------------------|--------------------------|-------|
| Contracts  | `contracts/ListFilteredContracts.graphql` | ✅ `contracts/W_contract_id.graphql` | Returns contract + linked properties; may need extra fragments later. |
| Projects   | `projects/ListFilteredProjects.graphql`   | ✅ `projects/W_project_id.graphql`   | Similar structure to contract query (properties connection). |
| Properties | `properties/ListAllProperties.graphql`    | ❌ none found | Only search-by-id-number template; no single-property detail query yet. |

### Action Items
1. **Contracts & Projects**: build new files for each moduel to get same data as provided by ListFilter files. use same name logic as for  `W_*_id.graphql` files using `w_{module_name}_module_data_by_item_id.graphql` Extend them with the same fragments used by the feed cards if data fields are missing.
2. **Properties**: reuse connected-data queries that returns the complete property payload required by the property module cards.
3. **Other modules**: show a temporary message (e.g., `"Opening search results for Tasks is not supported yet"`) until bespoke queries are available.

## Client-Side Plan
1. **Signal Wiring**
   - In the parent controller dialog.py use same idea as in 'swich_module', connect `HeaderWidget.searchResultClicked` to a handler `_on_search_jump(module, item_id, title)`.
2. **Routing Layer**
   - Create a dispatcher that maps `module` strings to loader functions (`contracts`, `projects`, `properties`).
   - Unknown modules fall back to `showUnsupportedSearchModule(module)` (toast/dialog/banner).
3. **Data Fetching**
   - Add helper as a new `SearchDeepLinkService` that:
     - Picks the right GraphQL file.
     - Calls `APIClient.send_query` with `{ "id": item_id }`.
     - Normalizes the result into the same structure the feed renderer expects (ideally reusing existing serializer utilities).
4. **Feed Injection**
   - Provide a method on each module feed widget to accept a single record payload (e.g., `ModuleFeedBuilder.render_single(record, highlight=True)`).
   - When a deep link loads, temporarily override current filters, display the record, and optionally show a dismissible banner like `"Showing search result for …"` with a button to restore filters.
5. **Error Handling**
   - Network/404 errors should show a toast and re-focus the search bar.
   - Unsupported module selection triggers the planned message.

## Backend Research Needs
- Confirm with [Kavitro API docs](https://kavitro.dev/docs) how single-item endpoints expose all fields needed by the feed (members, statuses, tags, etc.).

## Deliverables Checklist
- [ ] Property-by-ID GraphQL query added.
- [ ] Client dispatcher + loaders implemented.
- [ ] Feed widgets can display injected single records.
- [ ] Unsupported-module message path implemented.
- [ ] Manual test plan: select contract/project/property search result, validate card display irrespective of filters.
