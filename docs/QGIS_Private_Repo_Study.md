# QGIS Private Plugin Repository Study (DO Spaces + Laravel)

Date: 2025-08-14
Owner: Kalver

## Goal
Keep the plugin codebase private while enabling easy installation and semi-automatic upgrades via QGIS Plugin Manager.

## Approach Overview
- Storage: DigitalOcean Spaces private bucket for plugins.xml and plugin ZIPs.
- Backend: Laravel API endpoint(s) to authenticate users and serve content.
- Access pattern:
  - plugins.xml: served via Laravel with persistent auth (Basic Auth or token) → stable URL for QGIS polling.
  - ZIP files: served via Laravel endpoint that generates a presigned URL and redirects.
- CI: Build ZIP and plugins.xml from private Git repo and upload to DO Spaces.

## Repository URL in QGIS
- In QGIS, add repository URL under Plugins → Manage and Install Plugins → Settings → Plugin Repositories.
- Example: `https://yourdomain.com/api/qgis/plugins` (returns plugins.xml).
- QGIS Authentication Manager stores credentials for repeat access.

## plugins.xml Notes
- Must be reachable by QGIS; doesn’t need to be public.
- Prefer persistent auth over presigned (presigned expires, breaks polling).
- Example minimal entry:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<plugins>
  <pyqgis_plugin name="YourPluginName" version="1.0.0">
    <description>Your plugin description</description>
    <homepage>https://your-saas.com</homepage>
    <file_name>yourplugin.zip</file_name>
    <author_name>Your Company</author_name>
    <download_url>https://yourdomain.com/api/qgis/download/yourplugin-1.0.0.zip</download_url>
    <uploaded_by>yourname</uploaded_by>
    <create_date>2025-08-14</create_date>
    <update_date>2025-08-14</update_date>
    <experimental>False</experimental>
    <deprecated>False</deprecated>
    <tracker>https://your-saas.com/support</tracker>
    <repository>https://yourdomain.com</repository>
    <tags>your,tags</tags>
    <downloads>0</downloads>
    <average_vote>0</average_vote>
    <rating_votes>0</rating_votes>
    <external_dependencies></external_dependencies>
    <server>True</server>
  </pyqgis_plugin>
</plugins>
```

## Laravel Endpoints (sketch)

- GET `/api/qgis/plugins` → returns plugins.xml
  - Auth: Basic or Bearer token; use QGIS Authentication Manager
  - Implementation: fetch `plugins.xml` from Spaces and return as `application/xml`.
- GET `/api/qgis/download/:filename` → redirects to presigned URL for ZIP in Spaces
  - Auth: same as above
  - Implementation: generate presigned URL (e.g., +1h) and `302` redirect.

## CI/CD Sketch (GitHub Actions)
- Build ZIP from private repo
- Generate/patch `plugins.xml` version + dates
- Upload both to DO Spaces via S3-compatible API

## Pros / Cons
- Pros: Private code, easy install/upgrade, full control over access.
- Cons: Server/backend setup; GPL considerations; .py visible to end-users after install.

## Legal / Licensing Note
- PyQGIS-based plugins are generally considered GPL-derivative. Private distribution may conflict with GPL if not released under compatible terms. Consider moving sensitive logic to SaaS backend APIs and consult legal if needed.

## Testing Checklist
- [ ] QGIS can fetch plugins.xml via repo URL with auth
- [ ] Install plugin via Plugin Manager from repo
- [ ] Update check detects newer version
- [ ] ZIP download via Laravel redirect works
- [ ] Expired link handling (ZIP presigned) is robust

## Next Steps
- Wire Laravel middleware for auth; implement endpoints
- Create CI job to publish ZIP + plugins.xml to Spaces
- Pilot with an internal user; refine credentials UX
