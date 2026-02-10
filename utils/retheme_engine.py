from __future__ import annotations

from typing import Any

from ..widgets.theme_manager import ThemeManager
from ..Logs.python_fail_logger import PythonFailLogger


class RethemeEngine:
    """Centralized retheming helper that knows how to refresh the shell and modules."""

    def __init__(self, module_manager):
        self.module_manager = module_manager

    def retheme_all(self, dialog: Any) -> None:
        self.retheme_shell(dialog)
        self.retheme_modules()

    def retheme_shell(self, dialog: Any) -> None:
        targets = (
            ("header_widget", "retheme_header"),
            ("sidebar", "retheme_sidebar"),
            ("footer_widget", "retheme_footer"),
        )
        for attr, method_name in targets:
            self._call_child_retheme(dialog, attr, method_name)

    def retheme_modules(self) -> None:
        for module_name, module_data in self.module_manager.modules.items():
            instance = module_data.get("instance")
            if not instance:
                continue

            module_qss = module_data.get("init_params", {}).get("qss_files")
            bundle = ThemeManager.module_bundle(module_qss) if module_qss else ThemeManager.module_bundle()

            widget = self._get_widget(instance)
            if widget:
                ThemeManager.apply_module_style(widget, bundle)

            candidates = (
                "retheme",
                f"retheme_{module_name}",
                f"retheme_{module_name}s",
            )
            for method_name in candidates:
                method = getattr(instance, method_name, None)
                if callable(method):
                    method()
                    break

    @staticmethod
    def _get_widget(instance: Any):
        getter = getattr(instance, "get_widget", None)
        if callable(getter):
            try:
                return getter()
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="ui",
                    event="retheme_get_widget_failed",
                )
                return instance
        return instance

    @staticmethod
    def _call_child_retheme(obj: Any, attr_name: str, method_name: str) -> None:
        try:
            child = getattr(obj, attr_name, None)
            if child:
                method = getattr(child, method_name, None)
                if callable(method):
                    method()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="ui",
                event="retheme_child_failed",
                extra={"attr": attr_name, "method": method_name},
            )
