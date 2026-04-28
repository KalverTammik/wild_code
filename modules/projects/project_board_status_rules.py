from __future__ import annotations

import json
from typing import Any

from ...constants.settings_keys import SettingsService
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ..Settings.setting_keys import SettingDialogPlaceholders


class ProjectBoardStatusRules:
    @staticmethod
    def parse_not_started_status_rows(value) -> list[dict[str, str]]:
        payload = value
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return []
            try:
                payload = json.loads(text)
            except Exception:
                return []

        if not isinstance(payload, list):
            return []

        rows: list[dict[str, str]] = []
        for row in payload:
            if not isinstance(row, dict):
                continue
            status_id = str(row.get("statusId") or row.get("id") or "").strip()
            status_name = str(row.get("statusName") or row.get("name") or "").strip()
            if not status_id or not status_name:
                continue
            rows.append({"statusId": status_id, "statusName": status_name})
        return rows

    @classmethod
    def load_not_started_status_ids(cls, module_key: str) -> set[str]:
        stored = SettingsService().module_label_value(
            module_key,
            SettingDialogPlaceholders.PROJECT_BOARD_NOT_STARTED_STATUSES,
        ) or ""
        return {
            str(row.get("statusId") or "").strip()
            for row in cls.parse_not_started_status_rows(stored)
            if str(row.get("statusId") or "").strip()
        }

    @staticmethod
    def serialize_not_started_status_rows(status_ids, status_names) -> str:
        ids = [str(value).strip() for value in (status_ids or []) if str(value).strip()]
        names = [str(value).strip() for value in (status_names or [])]
        rows: list[dict[str, str]] = []
        for index, status_id in enumerate(ids):
            status_name = names[index] if index < len(names) else status_id
            rows.append({"statusId": status_id, "statusName": status_name or status_id})
        return json.dumps(rows, ensure_ascii=False)

    @classmethod
    def format_not_started_status_summary(cls, stored_value) -> str:
        rows = cls.parse_not_started_status_rows(stored_value)
        if not rows:
            return LanguageManager().translate(TranslationKeys.PROJECT_BOARD_NOT_STARTED_SUMMARY_EMPTY)

        preview = ", ".join(str(row.get("statusName") or "?").strip() for row in rows[:2])
        if len(rows) > 2:
            preview = f"{preview}, +{len(rows) - 2}" if preview else f"+{len(rows) - 2}"

        return LanguageManager().translate(TranslationKeys.PROJECT_BOARD_NOT_STARTED_SUMMARY).format(
            count=len(rows),
            preview=preview or "-",
        )

    @classmethod
    def is_not_started_item(cls, module_key: str, item: dict[str, Any]) -> bool:
        configured_ids = cls.load_not_started_status_ids(module_key)
        if not configured_ids:
            return False
        status_id = str((item or {}).get("status_id") or "").strip()
        return bool(status_id and status_id in configured_ids)