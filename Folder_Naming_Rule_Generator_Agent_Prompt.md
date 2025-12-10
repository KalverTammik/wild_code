# Agent Prompt — Folder Naming Rule Generator (Projects)

Implement a PyQt5 folder naming rule generator for the Projects module that stores stable internal keys and updates the existing engine to parse those keys.

## Scope

- Add a reusable dialog class that builds a folder naming rule.
- Update `FolderNameGenerator.folder_structure_name_order()` in `foldersHelpers.py`.
- Integrate the dialog into Projects settings using `ModuleLabelsWidget` label definitions.

## Tokens 

Support exactly these token types:

- Project Name
- Project Number
- Symbol (Custom Text)

## Internal keys

Use these stable keys for storage and parsing:

- `PROJECT_NAME`
- `PROJECT_NUMBER`
- `SYMBOL`

The UI shows localized labels for these keys, but the stored rule uses only the keys above.

## Rule model

- The rule has three ordered slots: Slot 1, Slot 2, Slot 3.
- Each slot can be:
  - Empty
  - `PROJECT_NAME`
  - `PROJECT_NUMBER`
  - `SYMBOL` with custom text

## Validation

- At least one slot must be non-empty.
- If a slot is `SYMBOL`, its text must be non-empty.

## Serialization (single string)

- Serialize only non-empty slots in slot order 1 → 2 → 3.
- Join components with the literal delimiter ` + `.
- Encode symbol as `SYMBOL(<text>)`.
- Encode name/number as `PROJECT_NAME` / `PROJECT_NUMBER`.

Valid examples:

- `PROJECT_NUMBER + SYMBOL(-) + PROJECT_NAME`
- `PROJECT_NAME`
- `SYMBOL(_) + PROJECT_NUMBER`

## Engine update

Update `FolderNameGenerator.folder_structure_name_order()` to:

- Split the stored rule by `" + "`.
- Compare against internal keys, not localized strings.
- Extract symbol text from parentheses when component starts with `SYMBOL(` and ends with `)`.
- Resolve components:
  - `PROJECT_NUMBER` → project number value.
  - `PROJECT_NAME` → project name value.
  - `SYMBOL(text)` → literal `text`.
- Concatenate resolved parts in rule order into the final folder name.

## Dialog UI

- Three rows for Slot 1–3.
- Each row contains:
  - slot label
  - dropdown: Empty, Project Number, Project Name, Symbol
  - text input enabled only when Symbol is selected
- Live preview label that updates on any change.
- Preview uses sample values:
  - Project Number: `(24)AR-3-1`
  - Project Name: `Awesome Ltd`
  - Symbol: user-entered text
- OK/Cancel actions.

## Settings integration (Projects)

Add two settings-backed labels:

1) Enable checkbox  
   - Key: `SettingDialogPlaceholders.PROJECTS_PREFERED_FOLDER_NAME_STRUCTURE_ENABLED`  
   - Tool: `checkBox`

2) Rule editor button  
   - Key: `SettingDialogPlaceholders.PROJECTS_PREFERED_FOLDER_NAME_STRUCTURE_RULE`  
   - Tool: `button`  
   - Displays current stored rule string as value.  
   - Opens the dialog.  
   - On accept, saves the serialized rule string to the rule key and refreshes the displayed value.

## Styling

- Use the existing modular QSS passed in module registration.
- Match the project’s dark-themed UI style.

## Done when

- Rule is stored using internal keys.
- Engine generates correct folder names from stored rules.
- Changing UI language does not break parsing.
- Users can enable/disable preferred structure and edit the rule from Projects settings.
