# Item Card Layout Discussion

This file tracks the current item card structure after the recent responsive layout refactor and acts as the reference point before the next UI pass.

The earlier problem was that the whole card still behaved like the header row was the main layout owner. That is no longer true. The card now uses a left rail plus a two-column content band, and the right utility area can switch between wide and compact arrangements.

## Current Effective Layout

This is roughly how the current item card is built now:

```text
+------------------------------------------------------------------+
| rail | left content area                          | utility       |
|      | title / number / type                     | dates         |
|      | contacts / module-specific rows           | actions       |
|      |                                           | members       |
|      |----------------------------------------------------------|
|      | full-width inline extra detail / overview                |
+------------------------------------------------------------------+
```

More literally, the content side is currently:

```text
card
├─ MainStatusWidget
└─ content
	├─ content_columns
	│  ├─ left_column
	│  │  ├─ InfocardHeaderFrame
	│  │  ├─ ContactsWidget
	│  │  └─ EasementPropertiesWidget (module-specific)
	│  └─ right_column
	│     └─ ResponsiveCornerWidget
	│        ├─ DatesWidget
	│        ├─ ModuleConnectionActions
	│        └─ MembersView
	└─ ExtraInfoFrame
```

## Current Behavior

The card now behaves like this:

```text
left rail + content columns + full-width detail zone
```

Current implemented rules:

- The left status rail is shared across module cards.
- The main content sits in a left column instead of being forced into a single header row.
- The right utility area is isolated into its own column.
- The inline detail area sits below the two-column band and can span the full card width.
- The utility column can switch between wide and compact layouts during live resize.
- In compact mode, the actions block can restack into a 2x2 layout.

## Contacts Area In The Card

The contacts area belongs to the `left_column` content flow, directly under the main header block.

At card level it should be thought of like this:

```text
left_column
├─ InfocardHeaderFrame
├─ ContactsWidget
└─ module-specific content
```

Visually inside the card the left side is currently closer to this:

```text
+--------------------------------------------------+
| title / number / type                            |
| client / header meta                             |
| [contacts icon] [contact 1] [contact 2] [...]   |
| [wrapped contact row when width runs out]        |
| other left-column content                        |
+--------------------------------------------------+
```

This means contacts are not a floating overlay and not part of the right utility corner. They are part of the editorial content flow on the left side of the card.

## ContactsWidget Detailed Layout

The `ContactsWidget` itself should be understood as a small responsive row-wrapping container.

Its internal structure is currently:

```text
ContactsWidget
├─ contacts icon
└─ wrapping contacts body
	├─ contact entry 1
	├─ contact entry 2
	├─ contact entry 3
	└─ ...
```

Each contact entry is a single responsive unit.

```text
contact entry
├─ contact name
└─ project-specific note text
```

That means the layout should behave like this:

```text
[contact name]
[note text]
```

The note belongs to the same contact entry as the name. The responsive behavior should move the whole contact entry to the next row when needed, not separate the note from its contact.

## ContactsWidget Responsive Rule

The intended wrapping behavior is:

1. Keep contacts in a horizontal flow for as long as they fit.
2. When the next full contact entry no longer fits in the available width, move that whole entry to the next row.
3. If the second row fills too, continue to a third row, and so on.

In other words, the wrapping unit is:

```text
one full contact widget = contact name + that contact's note
```

Not this:

```text
chip and note wrapped independently
```

## Contacts Layout Example

Example when there is enough space:

```text
[Juli Lumi]           [Parim Notar]        [Vahva Kaevur]
[liituja]             [Notar]              [Lepinguline ehitaja]
```

Example when width gets tighter:

```text
[Juli Lumi]           [Parim Notar]
[liituja]             [Notar]

[Vahva Kaevur]        [Peeter Projekt]
[Lepinguline ehitaja] [...]
```

Example when width gets even tighter:

```text
[Juli Lumi]
[liituja]

[Parim Notar]
[Notar]

[Vahva Kaevur]
[Lepinguline ehitaja]
```

That is the key rule for future changes: contact entries may wrap into more rows, but each entry should remain internally coherent.

## Current Responsive Size Limitations

The current contacts responsiveness is working, but it still has some practical limits that matter when iterating further.

- The contacts row does not decide wrapping from an isolated width. It depends on the final settled width of the `left_column` after the right utility column has finished its own resize pass.
- Because of that, narrowing the card can briefly pass through intermediate widths while `ResponsiveCornerWidget` is changing between wide and compact arrangements.
- Module switching often looks more stable because the card gets a fresh settled layout before the user starts dragging widths.
- The exact-fit boundary also matters. A row that mathematically lands on the full sum of contact widths plus spacing now wraps on that boundary instead of waiting for an even narrower width.
- Near the utility threshold, the left column can still feel more sensitive than a plain standalone wrapping layout because the available width is being influenced by both the contacts area and the responsive utility column.

The practical result is this:

```text
contacts responsiveness is coupled to the settled card layout,
not only to the contacts widget in isolation
```

That coupling is currently acceptable for the active baseline, but it should be kept in mind before adding more responsive behavior into the same card band.

## Current Responsive Utility Layout

Wide mode is currently intended to feel like a compact utility column:

```text
dates
actions
members
```

Compact mode is currently intended to feel tighter and more stacked:

```text
members
dates
actions (2x2)
```

This means the utility area is no longer treated as a passive header decoration. It is a responsive sub-layout inside the card.

## What Changed From The Original Discussion

The earlier options were mainly about escaping the old header-row ownership model.

What actually got implemented is closest to a hybrid of `Option B` and `Option C`:

```text
B traits:
- the card is no longer header-owned
- the expandable detail sits in its own real band below the top content area

C traits:
- date / actions / members use a dedicated right utility column
- the utility widgets no longer compete directly with the title row
```

## Current Strengths

- The header/title area has more freedom than before.
- The right utility widgets are visually grouped and easier to reason about.
- Inline project detail now belongs to the card structure instead of feeling appended.
- Live resize behavior exists and is now consistent enough to continue building on.
- Compact mode gives a tighter utility presentation without changing the whole card concept.

## Current Open Questions

- How compact should the utility column become before readability starts dropping?
- Should members always remain above dates in compact mode, or should that be configurable by module?
- Should the compact utility layout stay vertically stacked, or should a future version merge dates and members more tightly?
- When the logging phase is over, which width metrics are still worth keeping for the controller and which can be simplified?

## Working Direction

The current layout direction should be treated as the active baseline:

```text
left rail
+ two-column content band
+ full-width expandable detail band
+ responsive utility column on the right
```

That means the next discussions should not assume the old header-row model anymore. They should start from the implemented responsive two-column card.

## Note About Logging

Responsive size logging is intentionally still active in code while the layout continues to evolve. The document should assume those values are temporary diagnostics, not part of the design contract.

