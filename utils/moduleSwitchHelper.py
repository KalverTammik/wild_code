from __future__ import annotations

from typing import Any, Callable, Protocol, TYPE_CHECKING, Optional
from qgis.PyQt.QtCore import Qt
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
    property_selected_from_map: Any
    property_selection_completed: Any


class _ModuleManagerProtocol(Protocol):
    def getActiveModuleName(self) -> Optional[str]: ...
    def activateModule(self, module_name: str) -> None: ...
    def getActiveModuleInstance(self, module_name: str) -> _ModuleInstanceProtocol | None: ...


_dialog_resolver: Callable[[], ModuleSwitchDialogProtocol] | None = None
_confirm_unsaved_handler: Callable[[str, ModuleSwitchDialogProtocol], bool] | None = None
_settings_focus_handler: Callable[[Any, str | None, ModuleSwitchDialogProtocol], None] | None = None


def set_dialog_resolver(resolver: Callable[[], ModuleSwitchDialogProtocol] | None) -> None:
    """Register a resolver that returns the active dialog instance (UI-owned)."""
    global _dialog_resolver
    _dialog_resolver = resolver


def set_settings_confirm_handler(handler: Callable[[str, ModuleSwitchDialogProtocol], bool] | None) -> None:
    """Register UI handler to confirm leaving Settings with unsaved changes."""
    global _confirm_unsaved_handler
    _confirm_unsaved_handler = handler


def set_settings_focus_handler(handler: Callable[[Any, str | None, ModuleSwitchDialogProtocol], None] | None) -> None:
    """Register UI handler to focus a Settings section after switch."""
    global _settings_focus_handler
    _settings_focus_handler = handler


class ModuleSwitchHelper:
    _is_switching = False

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
        set_dialog_resolver(resolver)

    @staticmethod
    def set_settings_confirm_handler(handler: Callable[[str, ModuleSwitchDialogProtocol], bool] | None) -> None:
        """Register UI handler to confirm leaving Settings with unsaved changes."""
        set_settings_confirm_handler(handler)

    @staticmethod
    def set_settings_focus_handler(handler: Callable[[Any, str | None, ModuleSwitchDialogProtocol], None] | None) -> None:
        """Register UI handler to focus a Settings section after switch."""
        set_settings_focus_handler(handler)

    @staticmethod
    def switch_module(
        module_name: str,
        *,
        dialog: ModuleSwitchDialogProtocol | None = None,
        focus_module: str | None = None,
    ) -> None:
        """Switch the active module using an explicit module name and dialog."""
        import sys

        if ModuleSwitchHelper._is_switching:
            return

        def _widget_label(widget: Any | None) -> str:
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

        target_key = ModuleSwitchHelper._canonical_key(module_name)

        dlg = dialog

        if dlg is None and _dialog_resolver is not None:
            try:
                dlg = _dialog_resolver()
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

        module_manager: _ModuleManagerProtocol = ModuleManager()
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
        normalized_name = target_key
        prev_key = ModuleSwitchHelper._canonical_key(previous_module_name) if previous_module_name else ""

        if _confirm_unsaved_handler and not _confirm_unsaved_handler(previous_module_name or "", dlg):
            return

        ModuleSwitchHelper._is_switching = True
        try:
            module_manager.activateModule(target_key)
            instance = module_manager.getActiveModuleInstance(target_key)
            if instance is None:
                module_manager.activateModule(Module.HOME.value)
                raise ValueError(f"Failed to get instance of module '{target_key}' after activation.")

            try:
                dlg.header_widget.set_active_token(getattr(instance, "_active_token", None))
            except Exception as exc:
                SwitchLogger.log(
                    "switch_header_set_token_failed",
                    module=normalized_name,
                    extra={"error": str(exc)},
                )

            if previous_module_name and ModuleSwitchHelper._canonical_key(previous_module_name) == Module.PROPERTY.value:
                try:
                    if previous_instance is not None:
                        try:
                            previous_instance.property_selected_from_map.disconnect(dlg.window_manager._minimize_window)
                        except TypeError:
                            pass
                        except Exception as exc:
                            SwitchLogger.log(
                                "switch_property_disconnect_minimize_failed",
                                module=normalized_name,
                                extra={"error": str(exc)},
                            )
                        try:
                            previous_instance.property_selection_completed.disconnect(dlg.window_manager._restore_window)
                        except TypeError:
                            pass
                        except Exception as exc:
                            SwitchLogger.log(
                                "switch_property_disconnect_restore_failed",
                                module=normalized_name,
                                extra={"error": str(exc)},
                            )
                except Exception as exc:
                    SwitchLogger.log(
                        "switch_property_disconnect_failed",
                        module=normalized_name,
                        extra={"error": str(exc)},
                    )

            if normalized_name == Module.PROPERTY.value:
                try:
                    try:
                        instance.property_selected_from_map.disconnect(dlg.window_manager._minimize_window)
                    except TypeError:
                        pass
                    except Exception as exc:
                        SwitchLogger.log(
                            "switch_property_disconnect_minimize_failed",
                            module=normalized_name,
                            extra={"error": str(exc)},
                        )
                    instance.property_selected_from_map.connect(
                        dlg.window_manager._minimize_window,
                        type=Qt.UniqueConnection,
                    )
                except Exception as exc:
                    SwitchLogger.log(
                        "switch_property_connect_minimize_failed",
                        module=normalized_name,
                        extra={"error": str(exc)},
                    )
                try:
                    try:
                        instance.property_selection_completed.disconnect(dlg.window_manager._restore_window)
                    except TypeError:
                        pass
                    except Exception as exc:
                        SwitchLogger.log(
                            "switch_property_disconnect_restore_failed",
                            module=normalized_name,
                            extra={"error": str(exc)},
                        )
                    instance.property_selection_completed.connect(
                        dlg.window_manager._restore_window,
                        type=Qt.UniqueConnection,
                    )
                except Exception as exc:
                    SwitchLogger.log(
                        "switch_property_connect_restore_failed",
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
            # NOTE: repaint() is intentionally disabled; update() is enough in normal cases.
            # If visual glitches appear on module switch, re-enable the next line.
            # dlg.moduleStack.repaint()
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
                if focus_module and _settings_focus_handler:
                    _settings_focus_handler(instance, focus_module, dlg)


        except Exception:
            if previous_module_name:
                # Always prefer prev_key (canonical) if available; only fall back if prev_key is empty
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
            SwitchLogger.log(
                "switch_failed",
                module=normalized_name,
                extra={
                    "from": prev_key,
                    "active_module": active_after_fail,
                    "prev_widget": _widget_label(prev_widget),
                    "current_widget": _widget_label(current_widget),
                },
            )
            import traceback
            SwitchLogger.log(
                "switch_failed_exception",
                module=normalized_name,
                extra={"error": traceback.format_exc()},
            )
            traceback.print_exc(file=sys.stderr)
        finally:
            ModuleSwitchHelper._is_switching = False
