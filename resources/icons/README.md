# Icon Usage Guidelines

This document defines how icons are sourced, named, themed, and referenced across the plugin.

## Source and licensing
- All new icons must be downloaded from Icons8 “Fluency Systems Regular” set:
  - https://icons8.com/icons/set/user-interface--style-fluency-systems-regular
- Ensure you follow Icons8 licensing terms. Typically this requires attribution. Add a credit link (e.g., “Icons by Icons8”) in the project README/About dialog and keep a copy of the license or a link alongside the icons.
- Keep a note of each icon’s URL for future updates.

## Theme compatibility
- Prefer PNG assets with transparent background (no white/solid fills) for consistent rendering in Light and Dark themes.
- If needed, provide both Light and Dark variants and the app will switch them based on the active theme.
- SVGs are acceptable as an alternative when transparency and scale are guaranteed.

## File format and naming
- Use PNG (transparent) by default; SVG is also supported.
- Use lowercase, kebab-case file names to avoid case-sensitivity issues across OSes. Examples:
  - settings.png (and/or settings.svg)
  - folder.png
  - briefcase.png
- Keep sizes visually consistent (typically 24×24 or 32×32 logical size).

## Directory layout
- Place base icons in:
  - `resources/icons/`
- Theme-specific variants (optional):
  - `resources/icons/Light/<name>.png|.svg`
  - `resources/icons/Dark/<name>.png|.svg`
- Legacy PNGs (module-specific older assets) live in:
  - `resources/`

## Theme-specific icon variants
- If Light/Dark variants exist, the app automatically picks the correct one based on the current theme.
- Fallback: if a themed file is missing, the non-themed `resources/icons/<name>.png|.svg` will be used.
- Example file set:
  - `resources/icons/settings.png` (base)
  - `resources/icons/Light/settings.png` (optional)
  - `resources/icons/Dark/settings.png` (optional)

## Referencing icons in code
- Centralize module icon paths in `constants/module_icons.py` via `ModuleIconPaths.MODULE_ICONS`.
- `ModuleIconPaths.get_module_icon(module_name)` resolves Light/Dark and PNG/SVG variants automatically.
- For non-module icons, use `ThemeManager.resolve_icon_path("<name>.png|.svg")` to get a themed path.
- Avoid hardcoding absolute paths in UI code.
- Example mapping (pseudo):
  - Settings → `resources/icons/settings.png`
  - Projects → `resources/icons/folder.png`
  - Contract → `resources/icons/briefcase.png`

## Adding a new icon (checklist)
1) Download from Icons8 (Fluency Systems Regular).
2) Use transparent PNG (or SVG) and save to `resources/icons/` with lowercase, kebab-case name.
3) (Optional) Provide theme variants in `resources/icons/Light/` and `resources/icons/Dark/`.
4) Map module icons in `constants/module_icons.py`.
5) Verify rendering in both Light and Dark themes.
6) Remove obsolete files if replaced.

## Theming notes
- Avoid baked-in white or dark backgrounds; keep transparency.
- If a color is needed, ensure contrast in both themes or supply separate Light/Dark variants.

## Migration note
- Standardize on Icons8 Fluency Systems Regular. Replace older mismatched assets gradually.

## Attribution
- Include an attribution line where appropriate (README/About):
  - “Icons by Icons8 (Fluency Systems Regular): https://icons8.com/icons”
- Respect any additional requirements listed on the download page.
