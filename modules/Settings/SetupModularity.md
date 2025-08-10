# Settings Setup Modularity

Purpose: Extract and formalize the functionality for configuring target layers and related preferences from legacy dialogs into modular, reusable logic and UI for the current Settings module.

Scope
- Read QGIS Project layer tree (vector layers, metadata needed for selection and previews)
- Persist selected targets and preferences to QGIS settings
- Optionally apply a selected QGIS style (.qml) to a chosen layer
- Provide a clean API the Settings module can call, independent of any specific UI

Design Principles
- UI/Logic separation: UI renders and delegates, logic interacts with QGIS and settings
- Single source of truth: QGIS settings for persistence
- Non-blocking UI: no long operations on the main thread
- Theming & i18n: respect ThemeManager and LanguageManager
- Testable: logic functions avoid UI dependencies

Modules and Responsibilities
- SettingsDomain (logic-only)
  - LayersService
    - list_vector_layers(): [(id, name, path, is_visible, geometry_type, group)]
    - get_layer_by_name(name) -> QgsVectorLayer | None
    - apply_qml_style(layer: QgsVectorLayer, qml_path: str) -> bool
  - SettingsRepository
    - read(key: str, default: Any=None)
    - write(key: str, value: Any)
    - keys for this feature:
      - settings/target_cadastral_layer_name
      - settings/target_cadastral_style_path (optional)
  - UseCases
    - get_available_cadastral_targets()
    - save_cadastral_target(layer_name: str)
    - apply_layer_style_if_selected(layer_name: str, qml_path: Optional[str])

- SettingsUi (existing SettingsUI)
  - Uses the UseCases above
  - Renders combobox/list for layers, buttons for save/apply
  - Calls ThemeManager.apply_module_style for styling
  - Translates labels via LanguageManager

Public API (callable from SettingsUI)
- list_vector_layers() -> list[dict]
- save_target_cadastral(layer_name: str)
- apply_selected_style(layer_name: str, qml_path: str) -> bool

Interaction Flow
1) UI opens Settings → Cadastral configuration page
2) UI calls list_vector_layers() and populates combobox
3) On Save, UI calls save_target_cadastral(selected_name)
4) If style chosen, UI calls apply_selected_style(selected_name, qml)
5) UI shows a success/failure message

Theme & QSS
- Always use ThemeManager.apply_module_style(widget, [QssPaths.MAIN])
- No direct QSS file reads
- Provide retheme method to re-apply QSS to dynamic content

Translations
- All strings via LanguageManager; add keys to modules/Settings/lang/*

Error Handling
- Wrap QGIS operations with try/except; surface translated messages
- Validate layer existence before style application

Pseudocode
- LayersService.list_vector_layers
  - Iterate QgsProject.instance().layerTreeRoot() → collect QgsVectorLayer items
- SettingsRepository
  - use QgsSettings() under a plugin namespace: wild_code/settings/...

Roadmap
- [ ] Implement SettingsDomain services
- [ ] Add Cadastral page to SettingsUI using services
- [ ] Wire translations and theming
- [ ] Add unit-style tests for service behavior where feasible
