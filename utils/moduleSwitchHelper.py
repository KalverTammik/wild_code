from __future__ import annotations

from typing import Any, Callable, Protocol, TYPE_CHECKING, Optional
from .url_manager import Module
from ..module_manager import ModuleManager
from ..Logs.switch_logger import SwitchLogger


class _HeaderWidgetProtocol(Protocol):
    def set_active_token(self, token: Any | None) -> None: ...
    def set_title(self, title: str) -> None: ...


class _ModuleStackProtocol(Protocol):
    def currentWidget(self) -> Any | None: ...
    def indexOf(self, widget: Any) -> int: ...
    def addWidget(self, widget: Any) -> None: ...
    def setCurrentWidget(self, widget: Any) -> None: ...
    def update(self) -> None: ...
    def repaint(self) -> None: ...


class _SidebarProtocol(Protocol):
    def setActiveModuleOnSidebarButton(self, module_name: str) -> None: ...


class _WindowManagerProtocol(Protocol):
    def _minimize_window(self) -> None: ...
    def _restore_window(self) -> None: ...


class ModuleSwitchDialogProtocol(Protocol):
    header_widget: _HeaderWidgetProtocol
    moduleStack: _ModuleStackProtocol
    sidebar: _SidebarProtocol
    window_manager: _WindowManagerProtocol
    lang_manager: Any
    settingsModule: Any


class _ModuleInstanceProtocol(Protocol):
    def get_widget(self) -> Any | None: ...


class _ModuleManagerProtocol(Protocol):
    def getActiveModuleName(self) -> Optional[str]: ...
    def activateModule(self, module_name: str) -> None: ...
    def getActiveModuleInstance(self, module_name: str) -> _ModuleInstanceProtocol | None: ...


class ModuleSwitchHelper:
    _is_switching = False
    _dialog_resolver: Callable[[], ModuleSwitchDialogProtocol] | None = None
    _confirm_unsaved_handler: Callable[[str, ModuleSwitchDialogProtocol], bool] | None = None
    _settings_focus_handler: Callable[[Any, str | None, ModuleSwitchDialogProtocol], None] | None = None

    @staticmethod
    def _canonical_key(name: str | None) -> str:
        normalized = (name or "").strip()
        if not normalized:
            raise TypeError("ModuleSwitchHelper.switch_module requires a module_name.")
        try:
            return Module[normalized.upper()].value
        except Exception:
            return normalized.lower()

    @staticmethod
    def set_dialog_resolver(resolver: Callable[[], ModuleSwitchDialogProtocol] | None) -> None:
        """Register a resolver that returns the active dialog instance (UI-owned)."""
        ModuleSwitchHelper._dialog_resolver = resolver

    @staticmethod
    def set_settings_confirm_handler(handler: Callable[[str, ModuleSwitchDialogProtocol], bool] | None) -> None:
        """Register UI handler to confirm leaving Settings with unsaved changes."""
        ModuleSwitchHelper._confirm_unsaved_handler = handler

    @staticmethod
    def set_settings_focus_handler(handler: Callable[[Any, str | None, ModuleSwitchDialogProtocol], None] | None) -> None:
        """Register UI handler to focus a Settings section after switch."""
        ModuleSwitchHelper._settings_focus_handler = handler

    @staticmethod
    def _widget_label(widget: Any | None, *, module_name: str) -> str:
        if widget is None:
            return "<None>"
        try:
            name = widget.objectName() or ""
        except Exception as exc:
            SwitchLogger.log(
                "switch_widget_label_error",
                module=(module_name or "").lower(),
                extra={"error": str(exc)},
            )
            name = ""
        return f"{widget.__class__.__name__}:{name}" if name else widget.__class__.__name__

    @staticmethod
    def _resolve_dialog(target_key: str, dialog: ModuleSwitchDialogProtocol | None) -> ModuleSwitchDialogProtocol:
        dlg = dialog
        if dlg is None and ModuleSwitchHelper._dialog_resolver is not None:
            try:
                dlg = ModuleSwitchHelper._dialog_resolver()
            except Exception as exc:
                SwitchLogger.log(
                    "switch_dialog_resolver_failed",
                    module=target_key,
                    extra={"error": str(exc)},
                )
                dlg = None
        if dlg is None:
            raise RuntimeError(
                "ModuleSwitchHelper.switch_module requires a dialog instance (pass one or register a resolver)."
            )
        return dlg

    @staticmethod
    def _collect_switch_context(
        module_manager: _ModuleManagerProtocol,
        dlg: ModuleSwitchDialogProtocol,
        *,
        target_key: str,
    ) -> tuple[str, Any | None, Any | None, str]:
        previous_module_name = module_manager.getActiveModuleName() or ""

        previous_instance = None
        try:
            if previous_module_name:
                previous_instance = module_manager.getActiveModuleInstance(previous_module_name)
        except Exception as exc:
            SwitchLogger.log(
                "switch_prev_instance_failed",
                module=target_key,
                extra={"error": str(exc)},
            )

        prev_widget = None
        try:
            prev_widget = dlg.moduleStack.currentWidget()
        except Exception as exc:
            SwitchLogger.log(
                "switch_prev_widget_failed",
                module=target_key,
                extra={"error": str(exc)},
            )
            prev_widget = None

        prev_key = ModuleSwitchHelper._canonical_key(previous_module_name) if previous_module_name else ""
        return previous_module_name, previous_instance, prev_widget, prev_key

    @staticmethod
    def _confirm_navigation(previous_module_name: str, dlg: ModuleSwitchDialogProtocol) -> bool:
        if not ModuleSwitchHelper._confirm_unsaved_handler:
            return True
        return bool(ModuleSwitchHelper._confirm_unsaved_handler(previous_module_name or "", dlg))

    @staticmethod
    def _activate_target(
        module_manager: _ModuleManagerProtocol,
        *,
        target_key: str,
    ) -> _ModuleInstanceProtocol:
        module_manager.activateModule(target_key)
        instance = module_manager.getActiveModuleInstance(target_key)
        if instance is None:
            module_manager.activateModule(Module.HOME.value)
            raise ValueError(f"Failed to get instance of module '{target_key}' after activation.")
        return instance

    @staticmethod
    def _bind_switch_ui(
        dlg: ModuleSwitchDialogProtocol,
        module_manager: _ModuleManagerProtocol,
        *,
        target_key: str,
        instance: _ModuleInstanceProtocol,
        focus_module: str | None,
    ) -> None:
        normalized_name = target_key

        try:
            dlg.header_widget.set_active_token(getattr(instance, "_active_token", None))
        except Exception as exc:
            SwitchLogger.log(
                "switch_header_set_token_failed",
                module=normalized_name,
                extra={"error": str(exc)},
            )

        widget = instance.get_widget()
        if widget is None:
            raise ValueError(f"Module '{target_key}' returned no widget.")
        if dlg.moduleStack.indexOf(widget) == -1:
            dlg.moduleStack.addWidget(widget)
        dlg.moduleStack.setCurrentWidget(widget)
        dlg.header_widget.set_title(dlg.lang_manager.translate_module_name(normalized_name))

        dlg.sidebar.setActiveModuleOnSidebarButton(target_key)
        dlg.moduleStack.update()

        try:
            module_manager.getActiveModuleName()
        except Exception as exc:
            SwitchLogger.log(
                "switch_active_after_failed",
                module=normalized_name,
                extra={"error": str(exc)},
            )

        if normalized_name == Module.SETTINGS.value:
            dlg.settingsModule = instance
            if focus_module and ModuleSwitchHelper._settings_focus_handler:
                ModuleSwitchHelper._settings_focus_handler(instance, focus_module, dlg)

    @staticmethod
    def _rollback_switch(
        *,
        module_manager: _ModuleManagerProtocol,
        dlg: ModuleSwitchDialogProtocol,
        previous_module_name: str,
        prev_key: str,
        prev_widget: Any | None,
        normalized_name: str,
    ) -> tuple[str | None, Any | None]:
        if previous_module_name:
            key_to_use = prev_key if prev_key else previous_module_name
            try:
                module_manager.activateModule(key_to_use)
            except Exception as exc:
                SwitchLogger.log(
                    "switch_reactivate_prev_failed",
                    module=normalized_name,
                    extra={"error": str(exc)},
                )
            try:
                dlg.sidebar.setActiveModuleOnSidebarButton(key_to_use)
            except Exception as exc:
                SwitchLogger.log(
                    "switch_restore_sidebar_failed",
                    module=normalized_name,
                    extra={"error": str(exc)},
                )

        try:
            if prev_widget is not None:
                dlg.moduleStack.setCurrentWidget(prev_widget)
        except Exception as exc:
            SwitchLogger.log(
                "switch_restore_widget_failed",
                module=normalized_name,
                extra={"error": str(exc)},
            )

        try:
            active_after_fail = module_manager.getActiveModuleName()
        except Exception as exc:
            SwitchLogger.log(
                "switch_active_after_fail_failed",
                module=normalized_name,
                extra={"error": str(exc)},
            )
            active_after_fail = None

        try:
            current_widget = dlg.moduleStack.currentWidget()
        except Exception:
            current_widget = None

        return active_after_fail, current_widget

    @staticmethod
    def switch_module(
        module_name: str,
        *,
        dialog: ModuleSwitchDialogProtocol | None = None,
        focus_module: str | None = None,
    ) -> None:
        """Switch the active module using an explicit module name and dialog."""
        import sys
        import traceback

        if ModuleSwitchHelper._is_switching:
            return

        target_key = ModuleSwitchHelper._canonical_key(module_name)
        normalized_name = target_key
        dlg = ModuleSwitchHelper._resolve_dialog(target_key, dialog)

        module_manager: _ModuleManagerProtocol = ModuleManager()
        previous_module_name, _previous_instance, prev_widget, prev_key = ModuleSwitchHelper._collect_switch_context(
            module_manager,
            dlg,
            target_key=target_key,
        )

        if not ModuleSwitchHelper._confirm_navigation(previous_module_name, dlg):
            return

        ModuleSwitchHelper._is_switching = True
        try:
            instance = ModuleSwitchHelper._activate_target(module_manager, target_key=target_key)
            ModuleSwitchHelper._bind_switch_ui(
                dlg,
                module_manager,
                target_key=target_key,
                instance=instance,
                focus_module=focus_module,
            )


        except Exception:
            active_after_fail, current_widget = ModuleSwitchHelper._rollback_switch(
                module_manager=module_manager,
                dlg=dlg,
                previous_module_name=previous_module_name,
                prev_key=prev_key,
                prev_widget=prev_widget,
                normalized_name=normalized_name,
            )
            SwitchLogger.log(
                "switch_failed",
                module=normalized_name,
                extra={
                    "from": prev_key,
                    "active_module": active_after_fail,
                    "prev_widget": ModuleSwitchHelper._widget_label(prev_widget, module_name=module_name),
                    "current_widget": ModuleSwitchHelper._widget_label(current_widget, module_name=module_name),
                },
            )
            SwitchLogger.log(
                "switch_failed_exception",
                module=normalized_name,
                extra={"error": traceback.format_exc()},
            )
            traceback.print_exc(file=sys.stderr)
        finally:
            ModuleSwitchHelper._is_switching = False
