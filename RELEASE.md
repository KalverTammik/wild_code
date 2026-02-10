# Release (Custom QGIS Plugin Repository)

This plugin is distributed via a **custom QGIS plugin repository** (not the official plugins.qgis.org).

This follows the approach described here:
https://medium.com/geospatial-team/publishing-qgis-plugins-fb410b958f6

## What QGIS needs

A custom repository must expose (via direct HTTP access):

- `plugins.xml`
- a zip archive for each plugin version (zip must contain a **root folder** equal to the plugin folder name)

QGIS Plugin Manager links the installed plugin to the repository by **folder name**.

## One-time GitHub setup

1. Push this repo to GitHub.
2. Enable **GitHub Pages** for this repository.
   - Recommended: **Source = Deploy from a branch**
   - Branch: `main`
   - Folder: `/docs`
3. After Pages is enabled, your repository URL will look like:
   - `https://<user>.github.io/<repo>/`

We host the QGIS plugin repo artifacts under `docs/qgis-repo/`, so the URL you add to QGIS is:

- `https://<user>.github.io/<repo>/qgis-repo/plugins.xml`

## Release steps (every version)

1. Bump the plugin version in [metadata.txt](metadata.txt) (must match what you publish).
2. Build repo artifacts:

   - Windows PowerShell:
     - `C:/Users/Kalver/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/kavitro/.venv/Scripts/python.exe tools/qgis_repo_release.py --out docs/qgis-repo --repo-path qgis-repo`

   If you want to pin the exact URL, pass `--base-url`, for example:

   - `...python.exe tools/qgis_repo_release.py --out docs/qgis-repo --base-url https://<user>.github.io/<repo>/qgis-repo/`

3. Commit the generated files in `docs/qgis-repo/` (at minimum `plugins.xml` + the version zip).
4. Push to `main`.
5. (Optional but recommended) Create a git tag and a GitHub Release for the same version.

## Customer installation

In QGIS:

- Plugins → Manage and Install Plugins… → Settings → Plugin Repositories → **Add…**
- URL: `https://<user>.github.io/<repo>/qgis-repo/plugins.xml`

Then install/update the plugin from the **Not installed** tab.

## Notes

- Make sure the version in `metadata.txt` matches the `version` attribute in `plugins.xml` (the script keeps them in sync).
- If you rename the plugin folder, you must also publish zips using the new folder name, otherwise QGIS will treat it as a different plugin.
