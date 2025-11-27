# Property Tree Layout

```
PropertyTreeWidget
└── Title: "Kinnistuga seotud andmed"
└── ScrollArea
    └── cards_container (VBox)
        ├── PropertyConnectionCard (one per cadastral number)
        │   └── ModuleConnectionSection (one per module)
        │       ├── Header bar
        │       │   ├── Module icon
        │       │   ├── "{Module name} ({count})"
        │       │   └── Collapse arrow
        │       └── Body
        │           ├── ModuleConnectionRow (repeat for each linked record)
        │           │   ├── Column 0: number label
        │           │   ├── Column 1: title + meta row
        │           │   │   ├── Status pill
        │           │   │   ├── Type label
        │           │   │   └── "Uuendatud {date}"
        │           │   ├── Column 2: action buttons (folder / web / show on map)
        │           │   ├── Row 1 extras: DatesWidget (right) if available
        │           │   └── Row 2 extras: MembersView spanning columns 0–2
        │           └── "Kirjeid ei ole" message when no rows
        └── MessageCard (used when loading / empty state)
```
