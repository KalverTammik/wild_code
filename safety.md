# Secure Storage Policy

Plugin handles login data through QGIS-supported storage instead of custom encryption.

## Credential Storage

Sensitive data:

- password
- API key or token-like secrets

These must be stored through QGIS Authentication Manager, not plain `QSettings`.

Non-sensitive convenience data:

- username
- auth config id

These may be stored in `QSettings` because they are not secrets.

## Session Responsibilities

The session layer should:

- create or reuse a secure `QgsAuthMethodConfig`
- store only the auth id and username in plugin settings
- keep credentials in memory only for the active session
- avoid logging credentials or raw authentication payloads

## Avoid

- hardcoded credentials
- plaintext passwords in settings files
- custom encryption/decryption logic
- credentials in logs, UI errors, or debug output

## Future Option

The plugin may later support multiple saved sessions by storing multiple QGIS auth config ids with user-friendly labels.
