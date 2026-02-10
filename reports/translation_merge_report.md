# Translation Merge Report

## Summary
Applied AUTO_SAFE merges and cleanup based on config/translation_merge_plan.yaml. Normalized canonical IDs, removed duplicate translation keys, updated usage sites, and eliminated raw string translation keys in EN/ET.

## Applied AUTO_SAFE merges (highlights)
- Canonicalized cancel/save/login/title usages to TranslationKeys equivalents.
- Consolidated SignalTest labels to TranslationKeys.SIGNALTEST and TranslationKeys.TEST_LAB.
- Consolidated Add New Property usage to TranslationKeys.PROPERTY_MANAGEMENT (alias kept for transition).
- Removed raw string keys from EN/ET translation dicts.

## Translation key changes
- Aliases:
  - DialogLabels.LOGIN_TITLE -> TranslationKeys.LOGIN_BUTTON
  - DialogLabels.SETTINGS_TITLE -> TranslationKeys.SETTINGS_BASE_CARD_TEXT
  - FolderNamingTranslationKeys.TR_FOLDER_NAMING_RULE -> TranslationKeys.FOLDER_NAMING_RULE_DIALOG_TITLE
  - TranslationKeys.SIGNALTEST_SAVE_BUTTON -> TranslationKeys.SAVE
  - TranslationKeys.SIGNALTEST_CANCEL_BUTTON -> TranslationKeys.CANCEL_BUTTON
  - TranslationKeys.ADD_NEW_PROPERTY -> TranslationKeys.PROPERTY_MANAGEMENT
- Added canonical constants:
  - TranslationKeys.SIGNALTEST, TranslationKeys.TEST_LAB
  - TranslationKeys.AREA_M2, TranslationKeys.ENTER_ADDITIONAL_NOTES_OR_DESCRIPTION, TranslationKeys.THIS_FIELD_IS_REQUIRED

## Translation dict cleanup
- EN/ET: removed raw string keys and duplicate dict entries.
- Removed TranslationKeys.SIGNALTEST_TITLE from EN/ET (merged into TranslationKeys.SIGNALTEST).
- Removed TranslationKeys.ADD_NEW_PROPERTY from EN/ET (merged into TranslationKeys.PROPERTY_MANAGEMENT).

## Usage site updates
- SignalTest module/dialog: use TranslationKeys.SIGNALTEST and TranslationKeys.SAVE/CANCEL_BUTTON.
- Login dialog: use TranslationKeys.LOGIN_BUTTON.
- ProgressDialogModern: use TranslationKeys.INITIALIZING and TranslationKeys.CANCEL_BUTTON.
- MessagesHelper: use TranslationKeys.CANCEL_BUTTON and TranslationKeys.OK.
- SettingsUI: use TranslationKeys.SAVE and TranslationKeys.CANCEL_BUTTON.
- AddUpdatePropertyDialog/AddFromMapPropertyDialog: use TranslationKeys.PROPERTY_MANAGEMENT.
- BackendActionPromptDialog/MainDeleteProperties: use TranslationKeys.CANCEL_BUTTON.

## Plan issues fixed
- Normalized unsafe canonical_id values in config/translation_merge_plan.yaml.
- Resolved duplicate canonical_id entries where required (e.g., test lab vs signaltest).

## NEEDS_REVIEW queue
See reports/translations_needs_review.md for the full list with usage counts and file locations.

## Notes
- translation_keys.py no longer contains duplicate constant definitions.
- EN/ET translation dicts now have zero duplicate keys.
