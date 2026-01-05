# TODO

- Add loading/disable state on confirm in the map-link dialog using existing GradientSpinner (see modules/Property/property_tree_widget.py) to prevent double-submit while linking properties.
- Parse GraphQL errors from associate mutation and show concise error messages; log raw payload for debugging.
- If property resolution misses cadastral numbers, surface a "copy list" or "show on map" helper.
- Add a small success toast/banner on the module card after linking to reassure the user without reopening dialogs.


- Prevent duplicate confirms while request in flight; consider retry button for transient failures.


# DONE
- Extract resolve-and-associate logic into a reusable helper for other modules needing property links (check existing utilities or helpers for reuse before adding new files).
