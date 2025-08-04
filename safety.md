🔐 Secure Storage Policy for QGIS Plugin Session Data

This plugin handles user authentication securely by following QGIS best practices and leveraging the native Authentication Manager.

✅ 1. Credential Storage

Sensitive Data (password, API key):

Stored securely using QGIS Authentication Manager (QgsAuthManager).

Encrypted and protected by the QGIS authentication system.

Never stored in plain text or in QSettings.

Non-sensitive Data (username, auth ID):

Stored in QSettings for convenience.

No encryption required, as these do not contain secrets.

✅ 2. SessionManager Responsibilities

Create a secure QgsAuthMethodConfig for each login session.

Save the configuration into QGIS's encrypted authentication database.

Store only the auth_id and username in QSettings.

Provide access to credentials for the current session in-memory only.

🛑 What We Avoid

❌ No hardcoded credentials.

❌ No use of third-party encryption libraries (cryptography, AES, scrypt).

❌ No manual encryption/decryption logic.

🔁 Optional Enhancements

In the future, plugin could support multiple sessions by tagging and storing multiple auth_ids.

UI should allow credential removal and clearing session data.

📌 Summary Table

Credential Storage Matrix

Password➤ Storage: QGIS Authentication DB➤ Encrypted: ✅ Yes➤ Persisted: ✅ Yes

API Key➤ Storage: QGIS Authentication DB➤ Encrypted: ✅ Yes➤ Persisted: ✅ Yes

Username➤ Storage: QSettings➤ Encrypted: ❌ No➤ Persisted: ✅ Yes

Auth ID➤ Storage: QSettings➤ Encrypted: ❌ No➤ Persisted: ✅ Yes

📚 References

QGIS Authentication Guide

QgsAuthManager API

Important: Always respect user privacy. Never expose credentials in logs, error messages, or UI.