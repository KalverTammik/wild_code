Contract module refactor

- UI: ContractUi builds the QWidget and scrollable feed, reusing ModuleFeedBuilder card rendering and ThemeManager QSS application.
- Logic: ContractLogic holds non-UI concerns; ContractsFeedLogic fetches batched contracts from GraphQL API via APIClient and GraphQLQueryLoader, mirroring Projects.
- Integration: dialog.py now instantiates ContractUi and registers it via a thin wrapper to ModuleManager. Theme toggle calls retheme_contract on the UI.
