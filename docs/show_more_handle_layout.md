# Show More Handle Layout

This note documents the current implementation of the shared `show more` handle used by `ExtraInfoFrame`.

## Primary ownership

Implementation map:
- `widgets/DataDisplayWidgets/ExtraInfoWidget.py :: ExtraInfoFrame.__init__`
- `widgets/DataDisplayWidgets/ExtraInfoWidget.py :: ExtraInfoWidget.__init__`

The handle is created by `ExtraInfoFrame` in `widgets/DataDisplayWidgets/ExtraInfoWidget.py`.

Relevant objects:
- `ExtraInfoFrame`: outer controller for the handle and inline detail container
- `ExtraInfoWidget`: content/config host that decides whether detail exists
- `ExtraInfoHandleButton`: the actual `QToolButton` used as the visible handle
- `ExtraInfoInlineDetail`: inline expanding detail container for modules that use inline detail

The handle is not part of the normal layout tree as a layout-managed child of `ExtraInfoFrame`. It is created as a floating child of `handle_host`.

Small structure sketch:

```text
card (handle_host)
├─ MainStatusWidget
├─ CardContent
│  ├─ content_columns
│  │  ├─ left_column
│  │  └─ right_column
│  └─ ExtraInfoFrame
│     ├─ ExtraInfoWidget
│     └─ ExtraInfoInlineDetail   [inline modules only]
└─ ExtraInfoHandleButton         [floating child of card]

horizontal anchor:
ExtraInfoFrame width center
	|
	v
   [ handle ]
	|
	+-- mapped into card coordinates

vertical anchor:
card bottom - handle height - 1 px
```

## Where the handle is attached

Implementation map:
- `ui/module_card_factory.py :: ModuleCardFactory.create_item_card`
- `widgets/DataDisplayWidgets/ExtraInfoWidget.py :: ExtraInfoFrame.__init__`

`ModuleCardFactory.create_item_card()` passes `handle_host=card` when it creates `ExtraInfoFrame`.

That means:
- the detail controller widget lives inside the card content column
- the visible handle button is parented directly to the full card widget
- positioning is computed manually so the handle sits on the bottom edge of the card, not inside the content flow

Current mount point in card assembly:
- `ExtraInfoFrame` is added to `cl`, the main vertical layout of `CardContent`
- this happens after the main content columns and after contacts
- because the handle itself is parented to `card`, its visual position is independent from `cl` layout geometry except for the `ExtraInfoFrame` width and mapped origin

## Card layout inputs that affect final handle position

Implementation map:
- `ui/module_card_factory.py :: ModuleCardFactory.create_item_card`
- `styles/Light/ModuleCard.qss :: QFrame#ModuleInfoCard`
- `styles/Dark/ModuleCard.qss :: QFrame#ModuleInfoCard`

The card-level geometry comes from `ui/module_card_factory.py`.

Important layout values:
- `main = QHBoxLayout(card)`
- `main.setContentsMargins(0, 10, 10, 10)`
- `main.setSpacing(8)`
- `cl = QVBoxLayout(content)`
- `cl.setContentsMargins(0, 0, 0, 0)`
- `cl.setSpacing(6)`
- `content_columns.setSpacing(6)`

Practical effect:
- the handle is visually anchored against the outer `card`, not the inner `content`
- the bottom `10` px card margin in `main` contributes to the amount of empty space above the card border
- the `ExtraInfoFrame` width depends on the content column width, so the handle is horizontally centered relative to the extra-info row width, then mapped into card coordinates

## Handle construction

Implementation map:
- `widgets/DataDisplayWidgets/ExtraInfoWidget.py :: ExtraInfoFrame.__init__`
- `widgets/DataDisplayWidgets/ExtraInfoWidget.py :: ExtraInfoWidget.should_show_detail_handle`
- `widgets/DataDisplayWidgets/ExtraInfoWidget.py :: ExtraInfoWidget._detail_button_tooltip`

`ExtraInfoFrame.__init__()` creates the handle only if `ExtraInfoWidget.should_show_detail_handle()` returns `True`.

The button is configured as:
- object name: `ExtraInfoHandleButton`
- widget type: `QToolButton`
- parent: `handle_host` (normally the full card)
- auto raise: `True`
- fixed size: `42 x 12`
- text: empty
- tooltip: resolved from `_detail_button_tooltip()`
- cursor: `Qt.PointingHandCursor`

There is no icon or label text. The visual appearance is entirely stylesheet-driven.

## Positioning logic

Implementation map:
- `widgets/DataDisplayWidgets/ExtraInfoWidget.py :: ExtraInfoFrame._position_handle`
- `widgets/DataDisplayWidgets/ExtraInfoWidget.py :: ExtraInfoFrame._schedule_position_handle`

Positioning is handled by `ExtraInfoFrame._position_handle()`.

### Horizontal placement

Implementation map:
- `widgets/DataDisplayWidgets/ExtraInfoWidget.py :: ExtraInfoFrame._position_handle`

The handle is centered using the width of `ExtraInfoFrame`, not the width of the full card.

Formula:

```text
handle_x = max(0, (self.width() - handle.width()) // 2)
```

If `handle_host is self`:
- `target_x = handle_x`

If `handle_host is not self`:
- `host_pos = self.mapTo(host, QPoint(0, 0))`
- `target_x = max(0, host_pos.x() + handle_x)`

Because `handle_host` is usually the full `card`, the second path is used in normal module cards.

Practical effect:
- the handle tracks the horizontal center of the `ExtraInfoFrame` row
- the handle does not center across the whole card unless `ExtraInfoFrame` itself spans the full usable card width

### Vertical placement

Implementation map:
- `widgets/DataDisplayWidgets/ExtraInfoWidget.py :: ExtraInfoFrame._position_handle`

Formula:

```text
target_y = max(0, host.height() - handle.height() - 1)
```

With the current fixed handle height of `12`, the handle sits exactly `1` px above the bottom edge of the host.

Practical effect:
- the handle visually overlaps the lower card edge area
- it behaves like a floating tab attached to the bottom of the card

## When positioning is recalculated

Implementation map:
- `widgets/DataDisplayWidgets/ExtraInfoWidget.py :: ExtraInfoFrame.showEvent`
- `widgets/DataDisplayWidgets/ExtraInfoWidget.py :: ExtraInfoFrame.moveEvent`
- `widgets/DataDisplayWidgets/ExtraInfoWidget.py :: ExtraInfoFrame.resizeEvent`
- `widgets/DataDisplayWidgets/ExtraInfoWidget.py :: ExtraInfoFrame._schedule_position_handle`

The handle is not continuously laid out. Repositioning is event-driven.

Triggers:
- `showEvent()`
- `moveEvent()`
- `resizeEvent()`

These do not reposition immediately. They call `_schedule_position_handle()`, which starts a single-shot `QTimer` with `0` delay.

Reason for the timer:
- lets Qt finish current layout/geometry updates first
- avoids positioning against stale dimensions during layout churn

## Inline detail container and how it affects the handle

Implementation map:
- `widgets/DataDisplayWidgets/ExtraInfoWidget.py :: ExtraInfoFrame._init_project_detail_container`
- `widgets/DataDisplayWidgets/ExtraInfoWidget.py :: ExtraInfoFrame._toggle_project_detail`
- `widgets/DataDisplayWidgets/ExtraInfoWidget.py :: ExtraInfoFrame._run_detail_animation`
- `widgets/DataDisplayWidgets/ExtraInfoWidget.py :: ExtraInfoFrame._on_detail_animation_finished`

Inline detail is used for these modules right now:
- `project`
- `contract`
- `coordination`
- `easement`
- `task`
- `works`
- `asbuilt`

For inline-detail modules, `ExtraInfoFrame` creates `ExtraInfoInlineDetail`.

Container properties:
- widget type: `QFrame`
- size policy: `Expanding x Fixed`
- `maximumHeight = 0`
- `minimumHeight = 0`
- initially hidden
- inner layout margins: `0, 8, 0, 8`
- inner layout spacing: `0`

Expansion is animated via `QPropertyAnimation` on `maximumHeight`:
- duration: `260 ms`
- easing: `QEasingCurve.OutCubic`

This affects handle placement indirectly:
- expanding detail changes `ExtraInfoFrame` height
- `resizeEvent()` runs during/after size changes
- `_position_handle()` is scheduled again
- the handle stays pinned to the bottom of the host card while the detail area grows above it

## One-open-card rule

Implementation map:
- `widgets/DataDisplayWidgets/ExtraInfoWidget.py :: ExtraInfoFrame._expanded_project_frame`
- `widgets/DataDisplayWidgets/ExtraInfoWidget.py :: ExtraInfoFrame._set_expanded_project_frame`
- `widgets/DataDisplayWidgets/ExtraInfoWidget.py :: ExtraInfoFrame._toggle_project_detail`

`ExtraInfoFrame` keeps a class-level weak reference to the currently expanded inline frame.

Behavior:
- opening one card collapses any other expanded inline detail first
- this does not change the handle position formula
- it does affect perceived movement because one card may shrink while another expands

## Style application path

Implementation map:
- `widgets/DataDisplayWidgets/ExtraInfoWidget.py :: ExtraInfoWidget._build_ui`
- `ui/module_card_factory.py :: ModuleCardFactory.create_item_card`
- `widgets/theme_manager.py :: ThemeManager.apply_module_style`
- `widgets/theme_manager.py :: ThemeManager.module_bundle`
- `constants/file_paths.py :: QssPaths`

The handle style comes from `ModuleInfo.qss`.

Relevant theme files:
- `styles/Light/ModuleInfo.qss`
- `styles/Dark/ModuleInfo.qss`

Important implementation detail:
- `ExtraInfoWidget` applies `ThemeManager.apply_module_style(self, [QssPaths.MODULE_INFO])`
- `ModuleCardFactory` applies `ThemeManager.apply_module_style(card, [QssPaths.MODULE_CARD])`
- `ThemeManager.apply_module_style()` always uses `ThemeManager.module_bundle(...)`
- `module_bundle` already includes `QssPaths.MODULE_INFO`

Practical effect:
- even though the handle is parented to `card`, it still receives `ExtraInfoHandleButton` rules because the card stylesheet bundle includes `ModuleInfo.qss`

## Handle stylesheet selectors

Implementation map:
- `styles/Light/ModuleInfo.qss :: QToolButton#ExtraInfoHandleButton`
- `styles/Light/ModuleInfo.qss :: QToolButton#ExtraInfoHandleButton:hover`
- `styles/Dark/ModuleInfo.qss :: QToolButton#ExtraInfoHandleButton`
- `styles/Dark/ModuleInfo.qss :: QToolButton#ExtraInfoHandleButton:hover`

Selector used in both themes:

```qss
QToolButton#ExtraInfoHandleButton
QToolButton#ExtraInfoHandleButton:hover
```

### Light theme

Implementation map:
- `styles/Light/ModuleInfo.qss :: QToolButton#ExtraInfoHandleButton`
- `styles/Light/ModuleInfo.qss :: QToolButton#ExtraInfoHandleButton:hover`

`styles/Light/ModuleInfo.qss`

Base style:
- vertical light gradient background
- text color `#24292e`
- border `1px solid rgba(0,0,0,0.24)`
- `border-bottom: none`
- radius `3px` on all corners
- `padding: 0`
- `font-size: 1px`
- `font-weight: 700`

Hover style:
- border color changes to `rgba(9,144,143,0.65)`
- `border-bottom: none` remains

### Dark theme

Implementation map:
- `styles/Dark/ModuleInfo.qss :: QToolButton#ExtraInfoHandleButton`
- `styles/Dark/ModuleInfo.qss :: QToolButton#ExtraInfoHandleButton:hover`

`styles/Dark/ModuleInfo.qss`

Base style:
- dark vertical gradient background
- text color `#e0e0e6`
- border `1px solid rgba(255,255,255,0.24)`
- `border-bottom: none`
- radius `3px` on all corners
- `padding: 0`
- `font-size: 1px`
- `font-weight: 700`

Hover style:
- border color changes to `rgba(9,144,143,0.68)`
- `border-bottom: none` remains

## Visual notes about the current tab shape

Implementation map:
- `styles/Light/ModuleInfo.qss :: QToolButton#ExtraInfoHandleButton`
- `styles/Dark/ModuleInfo.qss :: QToolButton#ExtraInfoHandleButton`

The current selector sets:
- all four corner radii to `3px`
- `border-bottom: none`

That creates a small floating pill/tab rather than a strict top-tab shape. If a more attached look is wanted, the lower radius could be reduced or removed.

## What decides whether the handle exists

Implementation map:
- `widgets/DataDisplayWidgets/ExtraInfoWidget.py :: ExtraInfoWidget.should_show_detail_handle`
- `widgets/DataDisplayWidgets/ExtraInfoWidget.py :: ExtraInfoWidget.has_detail_content`
- `widgets/DataDisplayWidgets/ModuleConfig.py :: ModuleConfig.load_detailed_content`
- `widgets/DataDisplayWidgets/ModuleConfig.py :: ModuleConfigFactory.create_config`

The handle is created only when `ExtraInfoWidget.should_show_detail_handle()` returns `True`.

That is true when either:
- `config.show_detail_handle` is explicitly enabled
- or the config already has detail content / detail widget / a detail loader that yields content

So the handle depends on module config, not only on layout.

## Modules currently using the shared handle for inline detail

Implementation map:
- `widgets/DataDisplayWidgets/ExtraInfoWidget.py :: ExtraInfoFrame.__init__`
- `widgets/DataDisplayWidgets/ExtraInfoWidget.py :: ExtraInfoWidget._build_ui`
- `widgets/DataDisplayWidgets/ModuleConfig.py :: ModuleConfigFactory.create_config`

At the time of writing, inline detail is enabled in `ExtraInfoFrame` for:
- `project`
- `contract`
- `coordination`
- `easement`
- `task`
- `works`
- `asbuilt`

Other modules can still use the same handle in dialog mode if their config provides detail content but they are not in the inline-detail set.

## Files that affect the handle

Implementation map:
- `widgets/DataDisplayWidgets/ExtraInfoWidget.py`
- `widgets/DataDisplayWidgets/ModuleConfig.py`
- `ui/module_card_factory.py`
- `styles/Light/ModuleInfo.qss`
- `styles/Dark/ModuleInfo.qss`
- `styles/Light/ModuleCard.qss`
- `styles/Dark/ModuleCard.qss`
- `widgets/theme_manager.py`
- `constants/file_paths.py`

Primary behavior:
- `widgets/DataDisplayWidgets/ExtraInfoWidget.py`
- `widgets/DataDisplayWidgets/ModuleConfig.py`
- `ui/module_card_factory.py`

Theme and style:
- `styles/Light/ModuleInfo.qss`
- `styles/Dark/ModuleInfo.qss`
- `styles/Light/ModuleCard.qss`
- `styles/Dark/ModuleCard.qss`
- `widgets/theme_manager.py`
- `constants/file_paths.py`

## Safe places to modify behavior

Implementation map:
- styling: `styles/Light/ModuleInfo.qss`, `styles/Dark/ModuleInfo.qss`
- positioning: `widgets/DataDisplayWidgets/ExtraInfoWidget.py :: ExtraInfoFrame._position_handle`
- host anchor: `ui/module_card_factory.py :: ModuleCardFactory.create_item_card`
- visibility/config: `widgets/DataDisplayWidgets/ExtraInfoWidget.py :: ExtraInfoWidget.should_show_detail_handle`, `widgets/DataDisplayWidgets/ModuleConfig.py :: ModuleConfigFactory.create_config`

If the goal is visual styling only:
- change `QToolButton#ExtraInfoHandleButton` in `ModuleInfo.qss`

If the goal is horizontal/vertical placement:
- change `_position_handle()` in `ExtraInfoWidget.py`

If the goal is where the handle is anchored:
- change `handle_host=card` in `ModuleCardFactory.create_item_card()`

If the goal is when the handle appears:
- change `ModuleConfigFactory` rules or `should_show_detail_handle()`

## Current constraints and quirks

Implementation map:
- `widgets/DataDisplayWidgets/ExtraInfoWidget.py :: ExtraInfoFrame.__init__`
- `widgets/DataDisplayWidgets/ExtraInfoWidget.py :: ExtraInfoFrame._position_handle`
- `widgets/theme_manager.py :: ThemeManager.apply_module_style`

- The handle width is hard-coded to `42` px.
- The handle height is hard-coded to `12` px.
- The handle bottom offset is hard-coded to `1` px.
- Horizontal centering is based on `ExtraInfoFrame.width()`, not card width.
- The handle floats outside the layout flow, so unusual parent resizing can make it look detached until the next scheduled reposition.
- Because the card also gets `ModuleInfo.qss` through the module bundle, moving the handle to a different parent may require checking stylesheet scope again.
