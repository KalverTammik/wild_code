from __future__ import annotations
from typing import Any

from ...Logs.python_fail_logger import PythonFailLogger
from ...modules.signaltest.BackendActionPromptDialog import BackendActionPromptDialog
from .PropertyTableManager import PropertyTableManager, PropertyTableWidget


class PropertyPromptHelpers:
    @staticmethod
    def prompt_backend_action(parent: Any, rows: list[Any], *, title: str) -> str | None:
        frame, table = PropertyTableWidget.create_properties_table()
        PropertyTableManager.reset_and_populate_properties_table(table, rows)
        try:
            table.selectAll()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="settings",
                event="settings_property_table_select_failed",
            )

        dlg = BackendActionPromptDialog(parent=parent, table_frame=frame, table=table, title=title)
        ok = dlg.exec_()
        if not ok:
            return None
        return dlg.action
