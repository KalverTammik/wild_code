# Kavitro GraphQL – Projects Overview Filtered by Tags

You are an AI coding assistant working in VS Code. Your task is to help me implement **“project overview by tags”** using the Kavitro GraphQL API and then keep the codebase consistent with this approach.

The docs you should rely on are here: https://kavitro.dev/docs

---

## 1. Context / Goal

I want a feature where I can:

1. See a list of available **tags** that belong to the **Project** module.
2. Select one or more tags (e.g. `["Roadworks", "Urgent", "Tallinn"]`).
3. Get a **paginated overview of projects** that have these tags.
4. For each project, see some basic info plus the tags attached to that project.

Think of this as a “tag-based project dashboard”:
- Tag list panel on the side (multi-select, maybe with search).
- Main view that shows projects filtered by the selected tags.
- Ability to paginate and optionally search by project name/number.

You should implement the **data layer and basic UI wiring** for this. I’ll handle styling and UX polish later.

---

## 2. API Facts (from Kavitro docs)

### 2.1 `tags` query

- The `tags` query returns a paginated list of tags.
- Signature:
  ```graphql
  tags(
    where: QueryTagsWhereWhereConditions
    orderBy: [QueryTagsOrderByOrderByClause!]
    search: String
    first: Int! = 50
    after: String
    trashed: Trashed
  ): TagConnection!
  ```
- The `Tag` object has (at least) the following fields:
  ```graphql
  type Tag {
    id: ID!
    module: String!
    name: String
    createdAt: DateTimeTz!
    updatedAt: DateTimeTz!
    deletedAt: DateTimeTz
  }
  ```

### 2.2 `projects` query with `hasTags`

- The `projects` query returns a paginated list of projects.
  ```graphql
  projects(
    where: QueryProjectsWhereWhereConditions
    hasMembers: QueryProjectsHasMembersWhereHasConditions
    hasResponsible: QueryProjectsHasResponsibleWhereHasConditions
    hasFollowers: QueryProjectsHasFollowersWhereHasConditions
    hasCreator: QueryProjectsHasCreatorWhereHasConditions
    hasClient: QueryProjectsHasClientWhereHasConditions
    hasTags: QueryProjectsHasTagsWhereHasConditions
    relationIsAbsent: ProjectsRelations
    search: String
    orderBy: [QueryProjectsOrderByOrderByClause!]
    first: Int! = 50
    after: String
    trashed: Trashed
  ): ProjectConnection!
  ```

- The `Project` object exposes a `tags` connection:
  ```graphql
  type Project {
    id: ID!
    name: String
    number: String
    # ...
    tags(
      where: ProjectTagsWhereWhereConditions
      orderBy: [ProjectTagsOrderByOrderByClause!]
      first: Int! = 10
      after: String
    ): TagConnection!
    # ...
  }
  ```

- The exact shape of `QueryProjectsHasTagsWhereHasConditions` is documented in the **Inputs** section of the Kavitro docs. You must look it up there and use the documented fields (e.g. `column`, `operator`, `value`, `AND`, `OR`, etc.), **not guess them**.

---

## 3. High‑Level Architecture

Please implement this feature with a clear separation of concerns:

1. **GraphQL client / API layer**
   - A small module with functions:
     - `fetchProjectTags(...)`
     - `fetchProjectsByTags(...)`

2. **State / hook layer (if React)**
   - Hooks (or equivalent abstractions) to combine:
     - Selected tag IDs
     - Search text
     - Pagination cursor
     - Loading and error state

3. **UI layer**
   - A “Tag filter” component.
   - A “Project list” component.
   - A simple container/screen that wires them together.

Keep all logic for building GraphQL queries and mapping responses in the API & hook layers. The UI should only work with clean TypeScript types / DTOs.

---

## 4. GraphQL Operations to Implement

### 4.1 Fetch tags for the Project module

Implement a query like this (pseudo‑shape, use the exact input type and fields from the docs):

```graphql
query ProjectTags($search: String, $first: Int!, $after: String) {
  tags(
    where: {
      # Filter so we only get tags that belong to the "Project" module.
      # Use the documented column/operator/value fields for tag.module.
    }
    search: $search
    first: $first
    after: $after
  ) {
    pageInfo {
      hasNextPage
      endCursor
    }
    edges {
      node {
        id
        module
        name
      }
    }
  }
}
```

**Requirements:**
- Only fetch tags where `module` corresponds to the project module (check the docs for the expected value, e.g. `"projects"` or `"project"`).
- Support:
  - Optional search term (by tag name).
  - Pagination (`first`, `after`).

### 4.2 Fetch projects filtered by selected tags

Implement a query that takes a list of tag IDs and returns projects that have these tags:

```graphql
query ProjectsByTags(
  $tagIds: [ID!]!
  $first: Int!
  $after: String
  $search: String
) {
  projects(
    hasTags: {
      # Use the QueryProjectsHasTagsWhereHasConditions input from the docs.
      # Goal: filter to projects that are related to ANY or ALL of the given tag IDs,
      # depending on what the UI chooses to support.
    }
    search: $search
    first: $first
    after: $after
  ) {
    pageInfo {
      hasNextPage
      endCursor
    }
    edges {
      node {
        id
        name
        number
        status {
          id
          name
        }
        client {
          id
          name
        }
        tags(first: 20) {
          edges {
            node {
              id
              name
              module
            }
          }
        }
      }
    }
  }
}
```

**Important:**
- Look up `QueryProjectsHasTagsWhereHasConditions` in the Kavitro docs and use its real structure.
- Implement both modes if reasonably easy:
  - **“Any of these tags”** (OR)
  - **“All of these tags”** (AND)
- Expose this as an option in the API layer and in the hook (e.g. `matchMode: 'ANY' | 'ALL'`).

---

## 5. API Layer Design

Write a small API module (TypeScript) roughly like this (names can be adjusted, but keep the idea):

```ts
export type TagDTO = {
  id: string;
  module: string;
  name: string | null;
};

export type ProjectTagFilterMode = 'ANY' | 'ALL';

export type ProjectDTO = {
  id: string;
  name: string | null;
  number: string | null;
  statusName: string | null;
  clientName: string | null;
  tags: TagDTO[];
};

export interface PaginatedResult<T> {
  items: T[];
  endCursor: string | null;
  hasNextPage: boolean;
}

export async function fetchProjectTags(params: {
  search?: string;
  first?: number;
  after?: string | null;
}): Promise<PaginatedResult<TagDTO>>;

export async function fetchProjectsByTags(params: {
  tagIds: string[];
  matchMode?: ProjectTagFilterMode; // default ANY
  search?: string;
  first?: number;
  after?: string | null;
}): Promise<PaginatedResult<ProjectDTO>>;
```

**Implementation notes:**
- Map GraphQL connections/edges into flat arrays (`items`) and `pageInfo` into `endCursor`/`hasNextPage`.
- Centralize the GraphQL client (endpoint, headers, auth token). Reuse that instead of duplicating fetch logic.
- Do not expose raw GraphQL types to the rest of the app; always go through these DTOs.

---

## 6. State / Hooks

If the project uses React, implement hooks like:

```ts
function useProjectTagFilters() {
  // Holds: selected tag IDs, match mode, search term for tags,
  // and handles fetching paginated tag lists.
}

function useProjectsOverviewByTags(params: {
  selectedTagIds: string[];
  matchMode: ProjectTagFilterMode;
  search?: string;
}) {
  // Internally calls fetchProjectsByTags, manages loading & error & pagination.
}
```

Requirements:

- Debounce network calls when the tag selection or search term changes (e.g. 250–500 ms).
- Do not re‑fetch on every keystroke without debounce.
- Preserve current tag selection if the tag list page changes.
- Support “Load more” pagination in the project list.

---

## 7. UI Wiring

Implement (or extend) the following components:

1. **`ProjectTagFilterPanel`**
   - Shows a searchable list of project tags.
   - Supports multi‑select (e.g. checkboxes or pill chips).
   - Allows switching between **ANY** vs **ALL** tag filter mode.

2. **`ProjectOverviewList`**
   - Displays a list of projects (name, number, status, client, tags).
   - Shows selected tags per project (using the embedded `tags` connection).
   - Has a “Load more” button if `hasNextPage` is true.

3. **`ProjectTagsOverviewScreen`**
   - Combines the tag panel and project list.
   - Keeps shared state for:
     - Selected tag IDs
     - Tag match mode (ANY/ALL)
     - Project search term
   - Uses the hooks to fetch and render data.

Keep styling minimal and clean; focus on correct data flow and good naming.

---

## 8. Edge Cases & Behaviour

- If **no tags** are selected:
  - Show either all projects or none, depending on what is easiest to implement consistently. Expose this behaviour clearly in the code comments.
- If the selected tags return **no projects**:
  - Show a friendly empty state (“No projects match the selected tags”).
- Handle API errors:
  - Surface a simple error message and a “Retry” option.
- Keep the code ready for future extensions:
  - It should be easy to add filters like status, date ranges, or client later.

---

## 9. Code Quality Expectations

- Use TypeScript types for all externally visible functions.
- Avoid hard‑coding magic strings that come from GraphQL; centralize them if needed.
- Keep functions small and focused.
- Add comments where the GraphQL input shapes are a bit non‑obvious (especially `hasTags` conditions).

---

## 10. What NOT to Do

- Don’t invent GraphQL fields or arguments that are not in the Kavitro docs.
  - Always align with the schemas under **Objects / Queries / Inputs** in the official docs.
- Don’t mix UI and data fetching logic into the same giant component.
- Don’t break existing parts of the app that are unrelated to tags/projects.

---

## 11. Final Deliverable

- A working implementation of:
  - Tag fetching for the project module.
  - Project fetching filtered by tags using `projects(hasTags: ...)`.
  - Basic UI to combine tag selection and project list overview.
- Clean, well‑typed code that I can easily extend later.
