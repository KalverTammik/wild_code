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

The template expects `tools/resolve_release_values.py` from this repository. The resolver receives workflow inputs through environment variables, accepts only the documented version/tag format, and writes validated values to `GITHUB_OUTPUT`. Do not interpolate inputs or step outputs directly into a `run:` script.

Enable **Release immutability** in the GitHub repository settings only after this draft-first workflow is on the default branch. An immutable release locks its tag and assets when the draft is published, so assets must be built, uploaded, and verified first.

```yaml
name: Release QGIS Plugin

on:
  workflow_dispatch:
    inputs:
      release_version:
        description: Version to package from an existing draft release (e.g. 1.2.3)
        required: true
      release_tag:
        description: Optional draft release tag override (e.g. v1.2.3)
        required: false

permissions:
  contents: write

jobs:
  release:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09 # v5.1.0
        with:
          persist-credentials: false

      - name: Set up Python
        uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # v6.3.0
        with:
          python-version: '3.13'

      - name: Resolve release values
        id: release_values
        env:
          PLUGIN_INPUT_RELEASE_VERSION: ${{ inputs.release_version }}
          PLUGIN_INPUT_RELEASE_TAG: ${{ inputs.release_tag }}
        shell: bash
        run: python tools/resolve_release_values.py

      - name: Prepare live plugin directory
        env:
          PLUGIN_RELEASE_VERSION: ${{ steps.release_values.outputs.release_version }}
        shell: bash
        run: |
          rm -rf yourplugin_live
          mkdir -p yourplugin_live

          cp __init__.py yourplugin_live/
          cp icon.png yourplugin_live/
          cp metadata.release.txt yourplugin_live/metadata.txt
          cp <plugin_main>.py yourplugin_live/
          cp <dialog>.py yourplugin_live/
          cp <dialog>.ui yourplugin_live/
          cp resources.py yourplugin_live/
          cp resources.qrc yourplugin_live/

          mkdir -p yourplugin_live/config
          cp config/__init__.py yourplugin_live/config/
          cp config/config.json yourplugin_live/config/

          python - <<'PY'
          import os
          from pathlib import Path

          path = Path("yourplugin_live/metadata.txt")
          version = os.environ["PLUGIN_RELEASE_VERSION"]
          lines = [
              f"version={version}" if line.startswith("version=") else line
              for line in path.read_text(encoding="utf-8").splitlines()
          ]
          path.write_text("\n".join(lines) + "\n", encoding="utf-8")
          PY

      - name: Resolve empty draft release
        id: draft_release
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          PLUGIN_RELEASE_TAG: ${{ steps.release_values.outputs.release_tag }}
        shell: bash
        run: |
          RELEASE_JSON_FILE="${RUNNER_TEMP}/plugin-draft-release.json"
          RELEASE_TITLE_FILE="${RUNNER_TEMP}/plugin-release-title.txt"
          RELEASE_NOTES_FILE="${RUNNER_TEMP}/plugin-release-notes.md"

          gh api "repos/${GITHUB_REPOSITORY}/releases?per_page=100" \
            | jq --arg tag "${PLUGIN_RELEASE_TAG}" \
                '[.[] | select(.tag_name == $tag)] | first' \
            > "${RELEASE_JSON_FILE}"

          if [ "$(jq -r 'if . == null then "missing" else "found" end' "${RELEASE_JSON_FILE}")" != "found" ]; then
            echo "ERROR: Create and save draft release ${PLUGIN_RELEASE_TAG} before running this workflow."
            exit 1
          fi
          if [ "$(jq -r '.draft' "${RELEASE_JSON_FILE}")" != "true" ]; then
            echo "ERROR: Published releases must not be modified."
            exit 1
          fi
          if [ "$(jq -r '.assets | length' "${RELEASE_JSON_FILE}")" != "0" ]; then
            echo "ERROR: The draft must not contain pre-existing assets."
            exit 1
          fi

          TAG_REF="refs/tags/${PLUGIN_RELEASE_TAG}"
          TAG_REFS="$(git ls-remote origin "${TAG_REF}" "${TAG_REF}^{}")"
          if [ -z "${TAG_REFS}" ]; then
            CREATED_TAG_FILE="${RUNNER_TEMP}/plugin-created-tag.json"
            gh api --method POST \
              "repos/${GITHUB_REPOSITORY}/git/refs" \
              -f ref="${TAG_REF}" \
              -f sha="${GITHUB_SHA}" \
              > "${CREATED_TAG_FILE}"
            test "$(jq -r '.ref' "${CREATED_TAG_FILE}")" = "${TAG_REF}"
            test "$(jq -r '.object.sha' "${CREATED_TAG_FILE}")" = "${GITHUB_SHA}"
          else
            TAG_COMMIT="$(printf '%s\n' "${TAG_REFS}" | awk '$2 ~ /\^\{\}$/ { print $1; exit }')"
            if [ -z "${TAG_COMMIT}" ]; then
              TAG_COMMIT="$(printf '%s\n' "${TAG_REFS}" | awk 'NR == 1 { print $1 }')"
            fi
            test "${TAG_COMMIT}" = "${GITHUB_SHA}"
          fi

          RELEASE_ID="$(jq -r '.id' "${RELEASE_JSON_FILE}")"
          if ! [[ "${RELEASE_ID}" =~ ^[0-9]+$ ]]; then
            echo "ERROR: Draft release id is invalid."
            exit 1
          fi

          gh api --method PATCH \
            "repos/${GITHUB_REPOSITORY}/releases/${RELEASE_ID}" \
            -f tag_name="${PLUGIN_RELEASE_TAG}" \
            -f target_commitish="${GITHUB_SHA}" \
            > "${RELEASE_JSON_FILE}"
          test "$(jq -r '.tag_name' "${RELEASE_JSON_FILE}")" = "${PLUGIN_RELEASE_TAG}"
          jq -r 'if (.name // "") == "" then .tag_name else .name end' \
            "${RELEASE_JSON_FILE}" > "${RELEASE_TITLE_FILE}"
          jq -r '.body // ""' "${RELEASE_JSON_FILE}" > "${RELEASE_NOTES_FILE}"
          printf 'release_id=%s\n' "${RELEASE_ID}" >> "${GITHUB_OUTPUT}"

      - name: Build changelog-aware repository assets
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          PLUGIN_RELEASE_TAG: ${{ steps.release_values.outputs.release_tag }}
        shell: bash
        run: |
          RELEASE_TITLE_FILE="${RUNNER_TEMP}/plugin-release-title.txt"
          NOTES_FILE="${RUNNER_TEMP}/plugin-release-notes.md"
          PREVIOUS_XML_FILE="previous_plugins.xml"
          RELEASES_FILE="${RUNNER_TEMP}/plugin-published-releases.json"
          PLUGIN_RELEASE_TITLE="$(cat "${RELEASE_TITLE_FILE}")"

          if [ -z "${PLUGIN_RELEASE_TITLE}" ]; then
            PLUGIN_RELEASE_TITLE="${PLUGIN_RELEASE_TAG}"
          fi

          gh api "repos/${GITHUB_REPOSITORY}/releases?per_page=100" > "${RELEASES_FILE}"
          PREV_TAG="$(jq -r --arg tag "${PLUGIN_RELEASE_TAG}" \
            '[.[] | select(.draft == false and .tag_name != $tag)] | sort_by(.published_at) | reverse | .[0].tag_name // ""' \
            "${RELEASES_FILE}")"
          if [ -n "${PREV_TAG}" ]; then
            PREV_XML_URL="$(gh api "repos/${GITHUB_REPOSITORY}/releases/tags/${PREV_TAG}" --jq '.assets[] | select(.name=="plugins.xml") | .browser_download_url' 2>/dev/null || true)"
            if [ -n "${PREV_XML_URL}" ]; then
              curl -fsSL "${PREV_XML_URL}" -o "${PREVIOUS_XML_FILE}" || true
            fi
          fi

          CMD=(
            python tools/qgis_repo_release.py
            --plugin-dir yourplugin_live
            --out release_repo
            --base-url "https://github.com/${GITHUB_REPOSITORY}/releases/download/${PLUGIN_RELEASE_TAG}/"
            --release-tag "${PLUGIN_RELEASE_TAG}"
            --release-title "${PLUGIN_RELEASE_TITLE}"
          )
          if [ -s "${NOTES_FILE}" ]; then
            CMD+=(--release-notes-file "${NOTES_FILE}")
          fi
          if [ -s "${PREVIOUS_XML_FILE}" ]; then
            CMD+=(--previous-plugins-xml "${PREVIOUS_XML_FILE}")
          fi
          "${CMD[@]}"

      - name: Upload repository assets to release
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          PLUGIN_RELEASE_ID: ${{ steps.draft_release.outputs.release_id }}
        shell: bash
        run: |
          shopt -s nullglob
          ASSETS=(release_repo/plugins.xml release_repo/*.zip release_repo/*.png)
          if [ "${#ASSETS[@]}" -ne 3 ]; then
            echo "ERROR: Expected exactly plugins.xml, one plugin ZIP and one icon before upload."
            exit 1
          fi

          UPLOAD_BASE_URL="https://uploads.github.com/repos/${GITHUB_REPOSITORY}/releases/${PLUGIN_RELEASE_ID}/assets"
          UPLOAD_INDEX=0
          for ASSET_PATH in "${ASSETS[@]}"; do
            ASSET_NAME="$(basename "${ASSET_PATH}")"
            ENCODED_ASSET_NAME="$(jq -rn --arg value "${ASSET_NAME}" '$value | @uri')"
            UPLOAD_RESPONSE="${RUNNER_TEMP}/plugin-upload-${UPLOAD_INDEX}.json"

            curl --fail-with-body --silent --show-error -L \
              -X POST \
              -H 'Accept: application/vnd.github+json' \
              -H "Authorization: Bearer ${GH_TOKEN}" \
              -H 'X-GitHub-Api-Version: 2022-11-28' \
              -H 'Content-Type: application/octet-stream' \
              "${UPLOAD_BASE_URL}?name=${ENCODED_ASSET_NAME}" \
              --data-binary "@${ASSET_PATH}" \
              > "${UPLOAD_RESPONSE}"

            if ! jq -e --arg name "${ASSET_NAME}" \
              '.name == $name and .state == "uploaded"' \
              "${UPLOAD_RESPONSE}" >/dev/null; then
              echo "ERROR: GitHub did not confirm a completed upload for ${ASSET_NAME}."
              exit 1
            fi
            UPLOAD_INDEX=$((UPLOAD_INDEX + 1))
          done

      - name: Verify uploaded release asset digests
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          PLUGIN_RELEASE_ID: ${{ steps.draft_release.outputs.release_id }}
        shell: bash
        run: |
          RELEASE_JSON_FILE="${RUNNER_TEMP}/plugin-uploaded-release.json"
          gh api "repos/${GITHUB_REPOSITORY}/releases/${PLUGIN_RELEASE_ID}" > "${RELEASE_JSON_FILE}"

          shopt -s nullglob
          ASSETS=(release_repo/plugins.xml release_repo/*.zip release_repo/*.png)
          REMOTE_ASSET_COUNT="$(jq -r '.assets | length' "${RELEASE_JSON_FILE}")"
          if [ "${REMOTE_ASSET_COUNT}" -ne "${#ASSETS[@]}" ]; then
            echo "ERROR: GitHub draft contains an unexpected number of assets."
            exit 1
          fi

          for ASSET_PATH in "${ASSETS[@]}"; do
            ASSET_NAME="$(basename "${ASSET_PATH}")"
            EXPECTED_DIGEST="sha256:$(sha256sum "${ASSET_PATH}" | awk '{print $1}')"
            ACTUAL_DIGEST="$(jq -r --arg name "${ASSET_NAME}" \
              '.assets[] | select(.name == $name and .state == "uploaded") | .digest // empty' \
              "${RELEASE_JSON_FILE}")"
            test "${ACTUAL_DIGEST}" = "${EXPECTED_DIGEST}"
          done

      - name: Publish and lock release
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          PLUGIN_RELEASE_ID: ${{ steps.draft_release.outputs.release_id }}
          PLUGIN_RELEASE_TAG: ${{ steps.release_values.outputs.release_tag }}
        shell: bash
        run: |
          PUBLISHED_RELEASE_FILE="${RUNNER_TEMP}/plugin-published-release.json"
          gh api --method PATCH \
            "repos/${GITHUB_REPOSITORY}/releases/${PLUGIN_RELEASE_ID}" \
            -f tag_name="${PLUGIN_RELEASE_TAG}" \
            -f target_commitish="${GITHUB_SHA}" \
            -F draft=false \
            -F make_latest=true \
            -F prerelease=false \
            > "${PUBLISHED_RELEASE_FILE}"
          test "$(jq -r '.immutable' "${PUBLISHED_RELEASE_FILE}")" = "true"
          test "$(jq -r '.tag_name' "${PUBLISHED_RELEASE_FILE}")" = "${PLUGIN_RELEASE_TAG}"
          test "$(jq -r '.target_commitish' "${PUBLISHED_RELEASE_FILE}")" = "${GITHUB_SHA}"
          EXPECTED_DOWNLOAD_SEGMENT="/releases/download/${PLUGIN_RELEASE_TAG}/"
          jq -e --arg segment "${EXPECTED_DOWNLOAD_SEGMENT}" \
            'all(.assets[]; (.browser_download_url | contains($segment)))' \
            "${PUBLISHED_RELEASE_FILE}" >/dev/null
```

---

## 5) Release Process (Operational)

1. Update and review `metadata.release.txt`; keep the approved LIVE icon there.
2. Commit and push the intended release state.
3. In GitHub, create and **save an empty draft release** with the intended tag, title, and release notes. Do not publish it manually and do not attach assets. The workflow creates the Git tag at the exact checked-out commit if it does not already exist.
4. Run **Release QGIS Plugin** from the Actions tab with the matching version and tag. Run it from the exact branch or commit intended for release.
5. The workflow creates or validates the real Git tag at its checked-out commit, builds the assets, compares their local SHA-256 values with GitHub's asset digests, and only then publishes the draft.
6. Verify that the completed release is marked **Immutable**, retains the requested tag name, and includes:
   - `plugins.xml`
   - `yourplugin_live.<version>.zip`
   - the repository icon PNG

If any release asset or digest check fails, the draft remains unpublished. Remove the failed draft assets before retrying; never overwrite assets of a published release.

---

## 6) QGIS Repository URL for Users

Use this in QGIS Plugin Manager:

`https://github.com/<OWNER>/<REPO>/releases/latest/download/plugins.xml`

QGIS path:

- Plugins -> Manage and Install Plugins -> Settings -> Add...

---

## 7) Troubleshooting (Based on Real Failures)

### Error: draft release does not exist or already contains assets
- Cause: the workflow was started without first saving an empty GitHub draft for the requested tag.
- Fix: create a draft with release notes but no attached files. If retrying a failed draft, remove its previous workflow assets first.

### Error: release was published but is not immutable
- Cause: GitHub repository setting **Enable release immutability** is disabled.
- Fix: enable the setting before creating the next release. Do not silently replace the already published release assets.

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
- release assets use the icon declared in `metadata.release.txt`
- GitHub marks the release as `Immutable`
- local and GitHub SHA-256 digests match before publication

---

## Notes

- Keep tags in stable format: `vX.Y.Z`
- Avoid odd formats like `v.1.0.5`
- Do not reuse old tags or replace published assets; create a new release version for every correction
