# Property Tree Layout

## High-Level Structure

```
PropertyTreeWidget (QFrame, VBox)
├─ Title label (“Kinnistuga seotud andmed” via lang manager)
└─ QScrollArea (no frame)
     └─ cards_container (QWidget, VBox)
            ├─ PropertyConnectionCard (QFrame) per cadastral entry
            │  └─ ModuleConnectionSection (collapsible per module)
            │     ├─ Header bar (HLayout)
            │     │  ├─ Module icon (fixed 24x24)
            │     │  ├─ Title label “{Module} ({count})”
            │     │  └─ Toggle arrow (QToolButton)
            │     └─ Body (VBox)
            │        ├─ ModuleConnectionRow repeated for each linked record
            │        └─ Empty state label when no items
            └─ MessageCard (loading / defaults)
```

## ModuleConnectionRow Grid

- Base layout: `QGridLayout` with 3 columns
    - Column 0: fixed width label for cadastral number / id.
    - Column 1: stretchable column for title and metadata.
    - Column 2: fixed/compact column for status, members, actions.
- `grid.setColumnStretch(1, 1)` so the middle column absorbs available width, keeping column 0 compact and column 2 right-aligned.
- Vertical spacing is 6px; horizontal spacing 10px.

### Column Breakdown

| Column | Row | Widget              | Notes |
| ---    | --- | ---                 | --- |
| 0      | 0   | `InfocardHeaderFrame` | Reused header (spans columns 0–1 internally) so the left side mirrors module cards. |
| 1      | 1   | `MembersView`       | Only added when member edges exist; top/right aligned to sit between header and the right rail. |
| 2      | 0   | `StatusWidget`      | Right-aligned; provides status pill + DatesWidget stack. |
| 2      | 1   | Action buttons container | Horizontal layout hosting folder/web/map buttons; includes `addStretch(1)` before the buttons so the group hugs the right edge (falls back to row 0 when nothing else is on the right rail). |

### Stretch + Alignment Rules

1. Column 1 stretch is set to `1` so the shared header spans comfortably while columns 0 and 2 maintain natural size.
2. `InfocardHeaderFrame` internally manages its own stretches (number badge stays compact, title flexes) to mirror module cards.
3. Column 2 widgets are each added with `Qt.AlignRight | Qt.AlignTop` to maintain a neat right rail. Missing elements (e.g., no members) simply collapse that row.
4. The action button container adds a stretch on the left before the buttons, ensuring the icons stay flush to the right even if more width becomes available.
5. `cards_container` uses `addStretch(1)` after the last card so content hugs the top until data fills the viewport.

## Empty/Message States

- `MessageCard` handles default (“Vali kinnistu…”), loading, and no data scenarios using themed drop shadows.
- Module sections without rows render a gray “Kirjeid ei ole” label within the body.

Use this breakdown when repositioning widgets so spacing, alignment, and stretch behaviors remain predictable across translations and varying content density.
