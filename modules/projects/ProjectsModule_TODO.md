# ProjectsModule Refactor & Generalization TODO

## 1. Generalize the Card
- [ ] Rename `ProjectCard` to `ModuleInfoCard` (or similar) for multi-module support
- [ ] Refactor card creation to accept a generic "module" object and type

## 2. Tools Widget (Sidebar/Toolbar)
- [ ] Design and implement a sidebar or toolbar for module-specific actions
- [ ] Allow each module to register its own tools/actions

## 3. Bottom Area (Footer/Status/Actions)
- [ ] Define what should appear at the bottom (pagination, summary, global actions)
- [ ] Implement as a separate widget, easily extendable

## 4. Modularization
- [ ] Move each card section (header, members, extra info, status) into its own file/class for reusability
- [ ] Allow modules to plug in their own info widgets

## 5. API & Data
- [ ] Abstract API calls so other modules can provide their own data sources
- [ ] Support pagination, filtering, and searching generically

## 6. Theming & Customization
- [ ] Continue to use QSS for all styling
- [ ] Allow modules to provide their own QSS overrides if needed

---

### Visual Layout (ASCII)

```
+------------------------------------------------------+
| [Tools Widget] | [Central Feed: Module Info Cards]   |
|                | +-------------------------------+   |
|                | |  [Header]   [Members]         |   |
|                | |  [Extra Info]                 |   |
|                | |  [Status/Privacy/Dates]       |   |
|                | +-------------------------------+   |
|                | |  ... more cards ...           |   |
+------------------------------------------------------+
| [Bottom Area: Pagination / Summary / Actions]        |
+------------------------------------------------------+
```

---

**Next Steps:**
1. Decide on a new name for the card and refactor for general use
2. Design the Tools Widget and Bottom Area
3. Modularize card sections into separate files
4. Abstract data/API handling for multi-module support
