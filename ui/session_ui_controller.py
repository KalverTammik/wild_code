"""The plugin window's side of a session: logging in, logging out and gating the UI."""
from __future__ import annotations

import gc
from typing import Callable, Optional, Protocol, TYPE_CHECKING

from PyQt5.QtWidgets import QApplication
from qgis.PyQt.QtCore import QTimer

from ..Logs.python_fail_logger import PythonFailLogger
from ..Logs.switch_logger import SwitchLogger
from ..constants.settings_keys import SettingsService
from ..login_dialog import LoginDialog
from ..utils.SessionManager import SessionManager
from ..utils.moduleSwitchHelper import ModuleSwitchHelper
from ..utils.url_manager import Module

if TYPE_CHECKING:

    class ModuleWidgetProtocol(Protocol):
        ...

    class ModuleInstanceProtocol(Protocol):
        def get_widget(self) -> Optional[ModuleWidgetProtocol]: ...

    class ModuleManagerProtocol(Protocol):
        modules: dict
        def getActiveModuleName(self) -> Optional[str]: ...
        def getActiveModuleInstance(self, moduleName: str) -> Optional[ModuleInstanceProtocol]: ...

    class ModuleStackProtocol(Protocol):
        def setCurrentWidget(self, widget: ModuleWidgetProtocol) -> None: ...
        def setEnabled(self, enabled: bool) -> None: ...

    class SidebarProtocol(Protocol):
        def setActiveModuleOnSidebarButton(self, moduleName: str) -> None: ...
        def setEnabled(self, enabled: bool) -> None: ...

    class LogoutButtonProtocol(Protocol):
        def setEnabled(self, enabled: bool) -> None: ...

    class HeaderProtocol(Protocol):
        logoutButton: LogoutButtonProtocol

    class FooterProtocol(Protocol):
        def setEnabled(self, enabled: bool) -> None: ...

    class SessionDialogProtocol(Protocol):
        _has_shown: bool
        _force_close: bool
        _session_listener: Optional[Callable[[], None]]
        moduleManager: ModuleManagerProtocol
        moduleStack: ModuleStackProtocol
        sidebar: SidebarProtocol
        header_widget: HeaderProtocol
        footer_widget: FooterProtocol
        def close(self) -> None: ...
        def hide(self) -> None: ...
        def _refresh_session_dependent_ui(self) -> None: ...


class SessionUIController:
    @staticmethod
    def logout(dialog: "SessionDialogProtocol") -> None:
        PythonFailLogger.log(
            "logout_requested",
            module="auth",
        )
        SessionManager.clear()
        gc.collect()
        dialog._force_close = True
        dialog.close()
        try:
            dialog.deleteLater()
        except Exception:
            pass
        PythonFailLogger.log(
            "logout_dialog_closed",
            module="auth",
        )

    @staticmethod
    def ensure_logged_in(dialog: "SessionDialogProtocol") -> bool:
        """Refuse to show an unusable window; ask for a login instead.

        ``close()`` only minimises this dialog, so returning without a prompt
        used to leave a blank window and no explanation.
        """
        if SessionManager.is_session_valid():
            return True
        dialog.hide()
        SessionManager.request_login(reason="dialog_show", user_initiated=True)
        return False

    @staticmethod
    def after_show(dialog: "SessionDialogProtocol") -> None:
        if dialog._session_listener is None:
            def _listener():
                SessionUIController.handle_session_changed(dialog)

            dialog._session_listener = _listener
            SessionManager.register_listener(_listener)
            try:
                dialog.destroyed.connect(lambda *_: SessionManager.unregister_listener(_listener))
            except Exception:
                pass

        SessionUIController.refresh_login_ui(dialog)
        if dialog._has_shown and dialog.moduleManager.getActiveModuleName():
            # Preserve the current active module on subsequent shows
            active_name = dialog.moduleManager.getActiveModuleName()
            inst = dialog.moduleManager.getActiveModuleInstance(active_name)
            if inst:
                try:
                    widget = inst.get_widget()
                    if widget:
                        dialog.moduleStack.setCurrentWidget(widget)
                        dialog.sidebar.setActiveModuleOnSidebarButton(active_name)
                except Exception as exc:
                    SwitchLogger.log(
                        "dialog_restore_widget_failed",
                        module=active_name,
                        extra={"error": str(exc)},
                    )
            return

        pref_key = SettingsService().preferred_module().lower() or ""
        if pref_key and pref_key in dialog.moduleManager.modules:
            ModuleSwitchHelper.switch_module(pref_key, dialog=dialog)
        else:
            ModuleSwitchHelper.switch_module(Module.HOME.name, dialog=dialog)
        dialog._has_shown = True

    @staticmethod
    def handle_session_changed(dialog: "SessionDialogProtocol") -> None:
        SessionUIController.refresh_login_ui(dialog)
        dialog._refresh_session_dependent_ui()

    @staticmethod
    def refresh_login_ui(dialog: "SessionDialogProtocol") -> None:
        """Gate session-scoped UI on session validity (no dialog opening here).

        Logout stays enabled on purpose: it is the only action that resets a
        session stuck behind a cancelled login prompt.
        """
        is_valid = SessionManager.is_session_valid()
        dialog.sidebar.setEnabled(is_valid)
        dialog.moduleStack.setEnabled(is_valid)
        dialog.footer_widget.setEnabled(is_valid)
        dialog.header_widget.logoutButton.setEnabled(True)

    @staticmethod
    def open_login_prompt(parent, reason: Optional[str]) -> None:
        """Registered with SessionManager at plugin start; the window opens once the caller has returned."""
        QTimer.singleShot(0, lambda: SessionUIController._run_login_prompt(parent, reason))

    @staticmethod
    def _login_parent(parent):
        try:
            if parent is not None:
                return parent
        except Exception:
            return None
        try:
            from qgis.utils import iface
            if iface:
                return iface.mainWindow()
        except Exception:
            return None
        try:
            return QApplication.activeWindow()
        except Exception:
            return None

    @staticmethod
    def _run_login_prompt(parent, reason: Optional[str]) -> None:
        cancelled = False
        try:
            dlg = LoginDialog(parent=SessionUIController._login_parent(parent))
            result = dlg.exec_()
            if SessionManager.is_session_valid():
                QTimer.singleShot(0, SessionManager.notify_session_changed)
                PythonFailLogger.log(
                    "login_dialog_success",
                    module="auth",
                    extra={"reason": str(reason or "")},
                )
            elif result == 0:
                cancelled = True
                PythonFailLogger.log(
                    "login_dialog_cancelled",
                    module="auth",
                    extra={"reason": str(reason or "")},
                )
            else:
                PythonFailLogger.log(
                    "login_dialog_no_session",
                    module="auth",
                    extra={"reason": str(reason or "")},
                )
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="auth",
                event="login_dialog_open_failed",
            )
        finally:
            SessionManager.finish_login_prompt(reason, cancelled=cancelled)
