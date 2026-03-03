# Main Plugin DEV/LIVE Release Setup (QGIS + GitHub)

This document captures the exact setup pattern validated in this test plugin so you can apply the same approach to your main plugin.

## Goal

- Keep **DEV plugin** and **LIVE plugin** separate in QGIS.
- Publish LIVE updates through GitHub Releases.
- Let users use one stable URL:
  - `https://github.com/<OWNER>/<REPO>/releases/latest/download/plugins.xml`

---

## 1) Repository Structure

Your plugin repository should contain at least:

- plugin root files (`__init__.py`, main plugin `.py`, dialog files, `metadata.txt`, `resources*`, icon)
- `.github/workflows/release.yaml`
- `config/config.json` (LIVE config)
- `config/config_dev.json` (DEV config)

Example:

```text
plugin-root/
  .github/workflows/release.yaml
  metadata.txt
  __init__.py
  <plugin_main>.py
  <dialog>.py
  <dialog>.ui
  resources.py
  resources.qrc
  icon.png
  config/
    __init__.py
    config.json
    config_dev.json
```

---

## 2) DEV vs LIVE Identity

### DEV plugin (local)

In `metadata.txt`:

- `name=Your Plugin [DEV]`
- `experimental=True`

In your plugin UI/menu labels:

- show `[DEV]` in menu/action text

This makes it obvious when you are running local dev build.

### LIVE plugin (release package)

In the CI workflow, create a release package directory (e.g. `yourplugin_live`) and patch values there:

- plugin name: remove `[DEV]`
- `experimental=False`

This makes the published plugin visible by default in QGIS Plugin Manager.

---

## 3) Config File Routing Strategy

Use this runtime behavior:

- If plugin metadata name contains `[DEV]` and `config/config_dev.json` exists -> use `config_dev.json`
- Otherwise use `config.json`

Also display active config in the dialog for fast verification:

- `Config: config_dev.json` (DEV)
- `Config: config.json` (LIVE)

---

## 4) Release Workflow (Template)

Create `.github/workflows/release.yaml` and adapt filenames to your plugin.

```yaml
name: Release QGIS Plugin

on:
  release:
    types:
      - published
  workflow_dispatch:
    inputs:
      release_version:
        description: Version to package for manual test run (e.g. 1.2.3)
        required: true
      release_tag:
        description: Optional tag override for manual runs (e.g. v1.2.3)
        required: false

permissions:
  contents: write

jobs:
  release:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Install qgis-plugin-ci
        run: python -m pip install --upgrade pip qgis-plugin-ci

      - name: Resolve release values
        id: release_values
        shell: bash
        run: |
          if [ "${{ github.event_name }}" = "release" ]; then
            RELEASE_TAG="${{ github.event.release.tag_name }}"
            RELEASE_VERSION="${RELEASE_TAG#v}"
          else
            RELEASE_VERSION="${{ inputs.release_version }}"
            if [ -n "${{ inputs.release_tag }}" ]; then
              RELEASE_TAG="${{ inputs.release_tag }}"
            else
              RELEASE_TAG="v${RELEASE_VERSION}"
            fi
          fi

          RELEASE_VERSION="${RELEASE_VERSION#.}"

          if [[ "${RELEASE_VERSION}" =~ ^[0-9]+\.[0-9]+$ ]]; then
            RELEASE_VERSION="${RELEASE_VERSION}.0"
          elif [[ "${RELEASE_VERSION}" =~ ^[0-9]+$ ]]; then
            RELEASE_VERSION="${RELEASE_VERSION}.0.0"
          fi

          if ! [[ "${RELEASE_VERSION}" =~ ^[0-9]+\.[0-9]+\.[0-9]+([.-].*)?$ ]]; then
            echo "Invalid release version '${RELEASE_VERSION}'. Use x.y.z (or vX.Y.Z as tag)."
            exit 1
          fi

          echo "release_tag=${RELEASE_TAG}" >> "$GITHUB_OUTPUT"
          echo "release_version=${RELEASE_VERSION}" >> "$GITHUB_OUTPUT"

      - name: Prepare live plugin directory
        run: |
          rm -rf yourplugin_live
          mkdir -p yourplugin_live

          cp __init__.py yourplugin_live/
          cp icon.png yourplugin_live/
          cp metadata.txt yourplugin_live/
          cp <plugin_main>.py yourplugin_live/
          cp <dialog>.py yourplugin_live/
          cp <dialog>.ui yourplugin_live/
          cp resources.py yourplugin_live/
          cp resources.qrc yourplugin_live/

          mkdir -p yourplugin_live/config
          cp config/__init__.py yourplugin_live/config/
          cp config/config.json yourplugin_live/config/

          sed -i 's/^name=Your Plugin \[DEV\]$/name=Your Plugin/' yourplugin_live/metadata.txt
          sed -i 's/^experimental=True$/experimental=False/' yourplugin_live/metadata.txt

          cat > .qgis-plugin-ci << 'EOF'
          plugin_path: yourplugin_live
          github_organization_slug: <OWNER>
          project_slug: <REPO>
          EOF

      - name: Stage generated release files
        run: |
          git add -A yourplugin_live .qgis-plugin-ci

      - name: Ensure GitHub release exists (manual dispatch)
        if: github.event_name == 'workflow_dispatch'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          TAG="${{ steps.release_values.outputs.release_tag }}"
          gh release view "${TAG}" >/dev/null 2>&1 || gh release create "${TAG}" --target "${GITHUB_SHA}" --title "${TAG}" --notes "Manual release ${TAG}"

      - name: Deploy plugin
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          qgis-plugin-ci release "${{ steps.release_values.outputs.release_version }}" \
            --release-tag "${{ steps.release_values.outputs.release_tag }}" \
            --github-token "${GITHUB_TOKEN}" \
            --create-plugin-repo \
            --allow-uncommitted-changes

      - name: Build changelog-aware repository assets
        shell: bash
        run: |
          TAG="${{ steps.release_values.outputs.release_tag }}"
          python tools/qgis_repo_release.py \
            --plugin-dir yourplugin_live \
            --out release_repo \
            --base-url "https://github.com/${{ github.repository }}/releases/download/${TAG}/" \
            --release-tag "${TAG}"

      - name: Upload repository assets to release
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        shell: bash
        run: |
          TAG="${{ steps.release_values.outputs.release_tag }}"
          gh release upload "${TAG}" \
            release_repo/plugins.xml \
            release_repo/*.zip \
            release_repo/*.png \
            --clobber
```

---

## 5) Release Process (Operational)

1. Update plugin version in `metadata.txt` (e.g. `1.2.3`)
2. Commit + push
3. Tag + push:
   - `git tag v1.2.3`
   - `git push origin refs/tags/v1.2.3`
4. Publish release on GitHub for that tag
5. Verify release assets include:
   - `plugins.xml`
   - `yourplugin_live.<version>.zip`

---

## 6) QGIS Repository URL for Users

Use this in QGIS Plugin Manager:

`https://github.com/<OWNER>/<REPO>/releases/latest/download/plugins.xml`

QGIS path:

- Plugins -> Manage and Install Plugins -> Settings -> Add...

---

## 7) Troubleshooting (Based on Real Failures)

### Error: `qgis-plugin-ci package: ... release_version required`
- Cause: package/release command missing version argument.
- Fix: always pass resolved version.

### Error: `fatal: pathspec '<live_folder>' did not match any files`
- Cause: generated live folder not staged for git archive.
- Fix: `git add -A <live_folder> .qgis-plugin-ci` before release command.

### Plugin not visible in QGIS repo list
- Cause: published metadata has `experimental=True`.
- Fix: set `experimental=False` in LIVE package metadata.

### URL works in browser but not visible in QGIS list
- Check plugin filters in QGIS (`All`, not only `Installed`).
- Reload repositories.

---

## 8) Minimal Verification Checklist

- DEV local plugin shows `[DEV]` in menu/dialog
- DEV dialog shows `Config: config_dev.json`
- LIVE released plugin shows no `[DEV]`
- LIVE dialog shows `Config: config.json`
- `releases/latest/download/plugins.xml` resolves and includes latest version
- `plugins.xml` includes a `<changelog>` block containing GitHub release title + notes

---

## Notes

- Keep tags in stable format: `vX.Y.Z`
- Avoid odd formats like `v.1.0.5`
- Do not reuse old tags for new release logic changes; create a new tag each time
