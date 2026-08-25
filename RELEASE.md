# Release (custom QGIS plugin repository)

This plugin is distributed from **GitHub Releases** through a custom QGIS plugin repository. GitHub Pages is not used.

## Stable installation URL

Add this repository URL to QGIS Plugin Manager:

`https://github.com/KalverTammik/wild_code/releases/latest/download/plugins.xml`

In QGIS, open **Plugins -> Manage and Install Plugins... -> Settings -> Plugin Repositories -> Add...**, paste the URL, and install the plugin from **Not installed**.

The `latest` URL always resolves to the `plugins.xml` asset of the GitHub Release marked as latest. That XML points to the matching versioned ZIP asset on the same release.

## Publishing a release

1. Update the plugin version in [metadata.txt](metadata.txt).
2. Commit and push the intended release state.
3. Create and publish a GitHub Release with a matching tag, for example `v2.00.18`.
4. The **Release QGIS Plugin** workflow builds the live plugin, creates `plugins.xml`, the versioned ZIP and icon, uploads them to the release, and marks the release as latest.
5. Verify that the stable installation URL above downloads the newly generated `plugins.xml`.

The workflow also copies the GitHub Release title and notes into the `<changelog>` field shown by QGIS Plugin Manager.

## Source repository vs release package

Development and handoff material remains versioned in Git but is not included in the installed plugin. The release workflow validates this before packaging.

Excluded from the live package:

- internal operating guides (`docs/juhendid/`), all other repository documentation (`docs/`), and Markdown handoff files (`*.md`)
- tests and developer tooling (`tests/`, `tools/`)
- local environments, caches, logs, and temporary output
- development-only configuration and metadata
- local sample data and exploratory files

Runtime packages, styles, UI files, GraphQL queries, production configuration, and logging implementation remain included. `tools/qgis_repo_release.py` applies the same exclusions when run directly.

## Optional local artifact build

The release workflow is the canonical publishing path. To inspect the generated artifacts locally, provide the future tag-specific Release URL explicitly:

```powershell
python tools/qgis_repo_release.py `
  --out release_repo `
  --base-url https://github.com/KalverTammik/wild_code/releases/download/v2.00.18/ `
  --release-tag v2.00.18
```

This creates `release_repo/plugins.xml`, a versioned ZIP and an optional icon. Local output is for validation only; the GitHub workflow uploads the public release assets.
