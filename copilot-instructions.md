# Copilot Instructions for Wild Code QGIS Plugin

## General AI Assistant Guidelines

### Code Generation
- Always follow the coding guidelines in `copilot-prompt.md`
- Use the established patterns and architecture
- Maintain consistency with existing codebase
- Prefer existing utilities and helper classes over new implementations

### File Operations
- Always use absolute paths when referencing files
- Check file existence before operations
- Preserve existing code structure and indentation
- Make minimal, targeted changes

### Error Handling
- Test code changes for syntax errors
- Verify imports and dependencies
- Check for runtime compatibility

### Communication
- Be concise but informative
- Explain changes and reasoning
- Ask for clarification when requirements are unclear
- Provide actionable next steps

## Project-Specific Rules

### Architecture Compliance
- Follow modular architecture with BaseModule inheritance
- Use ModuleManager for lazy loading
- Implement proper activate/deactivate lifecycle
- Separate UI and logic classes
- When adding tag support to a module, reuse the base pattern: wire `TagsFilterWidget` into the toolbar, let `ModuleBaseUI` manage preference syncing, build the `hasTags` payload via `_build_has_tags_condition()`, and pass it to `FeedLogic.set_extra_arguments(hasTags=payload)` instead of hand-crafting GraphQL arguments.

### UI/UX Standards
- Use ThemeManager for all styling
- Apply QSS through established patterns
- Implement retheme() methods for theme switching
- Follow established layout patterns
- Use ModernMessageDialog for all user notifications:
  - `ModernMessageDialog.Info_messages_modern(title, message)` - Information messages with ℹ️ icon
  - `ModernMessageDialog.Warning_messages_modern(title, message)` - Warning messages with ⚠️ icon
  - `ModernMessageDialog.Error_messages_modern(title, message)` - Error messages with ❌ icon
  - `ModernMessageDialog.Message_messages_modern(title, message)` - General messages with 💬 icon

### Code Quality
- Use type hints where appropriate
- Follow PEP8 conventions
- Add docstrings to public methods
- Use relative imports within the plugin

### Testing & Validation
- Test UI components for proper theming
- Verify module loading and switching
- Check translation key usage
- Validate QGIS integration
- Test ModernMessageDialog methods for proper icon display and theming

## Development Workflow

1. Understand the request and identify affected components
2. Check existing patterns and utilities
3. Implement changes following established guidelines
4. Test for syntax and logical errors
5. Verify integration with existing codebase
6. Document changes if needed

## Emergency Contacts
- For QGIS-specific issues: Check QGIS Python API documentation
- For PyQt5 issues: Refer to Qt documentation
- For plugin architecture: See `copilot-prompt.md` guidelines

## Settings & Tag Filters
- Tag selections are stored via `SettingsService.module_preferred_tags`; rely on `TagsFilterWidget`’s built-in load/save logic rather than duplicating storage code.
- `ModuleBaseUI` now exposes `_build_has_tags_condition()` to translate selected IDs into the documented Kavitro `QueryProjectsHasTagsWhereHasConditions` input (supports `ANY`/`ALL`). Use it whenever you need to filter GraphQL feeds by tags.
- `FeedLogic` accepts arbitrary GraphQL arguments through `set_extra_arguments(**kwargs)`; modules should call this (e.g., `set_extra_arguments(hasTags=payload)`) so pagination stays consistent without monkey-patching the API client.