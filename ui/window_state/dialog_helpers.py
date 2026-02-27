from __future__ import annotations


class DialogHelpers:
    @staticmethod
    def open_folder_rule_dialog(lang_manager, dialog, dialog_class, accepted_value, current_value: str):
        dlg = dialog_class(lang_manager, dialog, initial_rule=current_value)
        result = dlg.exec_()
        if result == accepted_value:
            return dlg.get_rule()
        return current_value

    @staticmethod
    def confirm_settings_navigation(previous_module_name: str, dialog) -> bool:
        from ...Logs.switch_logger import SwitchLogger
        from ...utils.url_manager import Module

        if previous_module_name != Module.SETTINGS.name:
            return True
        try:
            instance = dialog.moduleManager.getActiveModuleInstance(Module.SETTINGS.name)
            if instance is None:
                raise ValueError("Settings module instance not found.")
            return bool(instance.confirm_navigation_away())
        except Exception as exc:
            SwitchLogger.log(
                "settings_confirm_navigation_failed",
                module=Module.SETTINGS.value,
                extra={"error": str(exc)},
            )
            raise

    @staticmethod
    def focus_settings_section(instance, focus_module: str | None, dialog) -> None:
        if not focus_module or instance is None:
            return
        try:
            from PyQt5.QtCore import QTimer
            from ...modules.Settings.scroll_helper import SettingsScrollHelper
            from ...Logs.switch_logger import SwitchLogger
            from ...utils.url_manager import Module

            QTimer.singleShot(
                0,
                lambda sm=instance, fm=focus_module: SettingsScrollHelper.scroll_to_module(
                    sm,
                    fm,
                ),
            )
        except Exception as exc:
            SwitchLogger.log(
                "settings_focus_failed",
                module=Module.SETTINGS.value,
                extra={"error": str(exc), "focus": focus_module},
            )

    @staticmethod
    def prompt_backend_action(parent, rows, *, title: str = "Choose action") -> str | None:
        from ...modules.signaltest.BackendActionPromptDialog import BackendActionPromptDialog
        from ...utils.mapandproperties.PropertyTableManager import PropertyTableManager, PropertyTableWidget
        from ...Logs.python_fail_logger import PythonFailLogger

        frame, table = PropertyTableWidget._create_properties_table()
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


class PopupHelpers:
    EVENT_HIDE_TIMEOUT_FAILED = "popup_helper_hide_timeout_failed"
    EVENT_HOVER_EVENT_FAILED = "popup_helper_hover_event_failed"
    EVENT_SHOW_POPUP_FAILED = "popup_helper_show_popup_failed"
    EVENT_POSITION_POPUP_FAILED = "popup_helper_position_popup_failed"
    EVENT_STYLE_APPLY_FAILED = "popup_helper_style_apply_failed"

    DEFAULT_POPUP_PROFILE = {
        "delay_ms": 120,
        "close_on_deactivate": True,
        "placement": "below_left",
        "offset": (0, 0),
        "keep_on_screen": True,
        "smart_flip": True,
        "screen_padding": 8,
        "style_key": "popup",
    }

    POPUP_PROFILES = {
        "default": {},
        "dates": {
            "style_key": "dates",
        },
        "tags": {
            "placement": "top_left",
            "offset": (0, 6),
        },
        "members": {
            "offset": (0, 6),
        },
    }

    @staticmethod
    def _profile(popup_kind: str | None):
        key = (popup_kind or "default").lower()
        overrides = PopupHelpers.POPUP_PROFILES.get(key, PopupHelpers.POPUP_PROFILES["default"])
        return {**PopupHelpers.DEFAULT_POPUP_PROFILE, **overrides}

    @staticmethod
    def _with_profile(popup_kind, action):
        profile = PopupHelpers._profile(popup_kind)
        return action(profile)

    @staticmethod
    def popup_delay(popup_kind: str | None = None) -> int:
        return PopupHelpers._with_profile(
            popup_kind,
            lambda profile: int(profile.get("delay_ms", 120)),
        )

    @staticmethod
    def _log_helper_error(exc, event: str) -> None:
        try:
            from ...Logs.python_fail_logger import PythonFailLogger

            PythonFailLogger.log_exception(
                exc,
                module="ui",
                event=event,
            )
        except Exception:
            pass

    @staticmethod
    def is_popup_alive(widget) -> bool:
        if widget is None:
            return False

        try:
            widget.isVisible()
            return True
        except Exception:
            return False

    @staticmethod
    def stop_hide_timer(timer) -> None:
        if timer is not None:
            timer.stop()

    @staticmethod
    def schedule_hide_timer(timer, delay_ms: int = 120) -> None:
        if timer is not None:
            timer.start(delay_ms)

    @staticmethod
    def is_cursor_over_widget(widget) -> bool:
        if not PopupHelpers.is_popup_alive(widget) or not widget.isVisible():
            return False
        from PyQt5.QtGui import QCursor

        cursor_pos = widget.mapFromGlobal(QCursor.pos())
        return widget.rect().contains(cursor_pos)

    @staticmethod
    def should_keep_popup(anchor_widget, popup_widget) -> bool:
        return (
            PopupHelpers.is_cursor_over_widget(anchor_widget)
            or PopupHelpers.is_cursor_over_widget(popup_widget)
        )

    @staticmethod
    def handle_hide_timeout(timer, anchor_widget, popup_widget, hide_callback, delay_ms: int = 120) -> None:
        try:
            if PopupHelpers.should_keep_popup(anchor_widget, popup_widget):
                PopupHelpers.schedule_hide_timer(timer, delay_ms)
                return
            hide_callback()
        except Exception as exc:
            PopupHelpers._log_helper_error(exc, PopupHelpers.EVENT_HIDE_TIMEOUT_FAILED)

    @staticmethod
    def bind_hide_timeout(timer, anchor_getter, popup_getter, hide_callback, delay_ms: int = 120) -> None:
        if timer is None:
            return

        timer.timeout.connect(
            lambda: PopupHelpers.handle_hide_timeout(
                timer,
                anchor_getter() if callable(anchor_getter) else anchor_getter,
                popup_getter() if callable(popup_getter) else popup_getter,
                hide_callback,
                delay_ms=delay_ms,
            )
        )

    @staticmethod
    def bind_hide_timeout_for(popup_kind, timer, anchor_getter, popup_getter, hide_callback) -> None:
        PopupHelpers._with_profile(
            popup_kind,
            lambda profile: PopupHelpers.bind_hide_timeout(
                timer,
                anchor_getter=anchor_getter,
                popup_getter=popup_getter,
                hide_callback=hide_callback,
                delay_ms=int(profile.get("delay_ms", 120)),
            ),
        )

    @staticmethod
    def hide_popup_attr(owner, attr_name: str, timer, event_filter_owner=None):
        popup_widget = getattr(owner, attr_name, None)
        popup_widget = PopupHelpers.hide_popup(timer, popup_widget, event_filter_owner)
        setattr(owner, attr_name, popup_widget)
        return popup_widget

    @staticmethod
    def bind_hide_timeout_attr_for(
        popup_kind,
        *,
        owner,
        attr_name: str,
        timer,
        anchor_getter,
        event_filter_owner=None,
    ) -> None:
        PopupHelpers.bind_hide_timeout_for(
            popup_kind,
            timer,
            anchor_getter=anchor_getter,
            popup_getter=lambda: getattr(owner, attr_name, None),
            hide_callback=lambda: PopupHelpers.hide_popup_attr(
                owner,
                attr_name,
                timer,
                event_filter_owner,
            ),
        )

    @staticmethod
    def handle_popup_hover_event(
        obj,
        event,
        *,
        popup_widget,
        timer,
        anchor_matcher=None,
        on_anchor_enter=None,
        delay_ms: int = 120,
        close_on_deactivate: bool = False,
        on_popup_deactivate=None,
    ) -> bool:
        try:
            from PyQt5.QtCore import QEvent

            event_type = event.type()

            if obj == popup_widget:
                if event_type == QEvent.Enter:
                    PopupHelpers.stop_hide_timer(timer)
                elif event_type == QEvent.Leave:
                    PopupHelpers.schedule_hide_timer(timer, delay_ms)
                elif close_on_deactivate and event_type == QEvent.WindowDeactivate:
                    if callable(on_popup_deactivate):
                        on_popup_deactivate()
                return True

            if callable(anchor_matcher) and anchor_matcher(obj):
                if event_type == QEvent.Enter:
                    PopupHelpers.stop_hide_timer(timer)
                    if callable(on_anchor_enter):
                        on_anchor_enter(obj)
                elif event_type == QEvent.Leave:
                    PopupHelpers.schedule_hide_timer(timer, delay_ms)
                return True

            return False
        except Exception as exc:
            PopupHelpers._log_helper_error(exc, PopupHelpers.EVENT_HOVER_EVENT_FAILED)
            return False

    @staticmethod
    def handle_popup_hover_event_for(
        popup_kind,
        obj,
        event,
        *,
        popup_widget,
        timer,
        anchor_matcher=None,
        on_anchor_enter=None,
        on_popup_deactivate=None,
    ) -> bool:
        return PopupHelpers._with_profile(
            popup_kind,
            lambda profile: PopupHelpers.handle_popup_hover_event(
                obj,
                event,
                popup_widget=popup_widget,
                timer=timer,
                anchor_matcher=anchor_matcher,
                on_anchor_enter=on_anchor_enter,
                delay_ms=int(profile.get("delay_ms", 120)),
                close_on_deactivate=bool(profile.get("close_on_deactivate", True)),
                on_popup_deactivate=on_popup_deactivate,
            ),
        )

    @staticmethod
    def position_popup(
        popup_widget,
        anchor_widget,
        *,
        placement: str = "below_left",
        offset=None,
        keep_on_screen: bool = True,
        smart_flip: bool = True,
        screen_padding: int = 8,
    ) -> None:
        if not PopupHelpers.is_popup_alive(popup_widget) or anchor_widget is None:
            return

        try:
            from PyQt5.QtCore import QPoint
            from PyQt5.QtGui import QGuiApplication

            offset = offset or QPoint(0, 0)
            popup_widget.adjustSize()

            if placement == "top_left":
                pos = anchor_widget.mapToGlobal(QPoint(0, 0)) + offset
            else:
                pos = anchor_widget.mapToGlobal(QPoint(0, anchor_widget.height())) + offset

            if keep_on_screen:
                screen = QGuiApplication.screenAt(pos) or QGuiApplication.primaryScreen()
                if screen is not None:
                    available = screen.availableGeometry()

                    if placement == "below_left" and smart_flip:
                        if pos.y() + popup_widget.height() > available.bottom() - screen_padding:
                            top_pos = anchor_widget.mapToGlobal(QPoint(0, 0))
                            pos.setY(top_pos.y() - popup_widget.height() - screen_padding)

                    min_x = available.left() + screen_padding
                    max_x = available.right() - popup_widget.width() - screen_padding
                    min_y = available.top() + screen_padding
                    max_y = available.bottom() - popup_widget.height() - screen_padding

                    if max_x < min_x:
                        max_x = min_x
                    if max_y < min_y:
                        max_y = min_y

                    pos.setX(max(min_x, min(pos.x(), max_x)))
                    pos.setY(max(min_y, min(pos.y(), max_y)))

            popup_widget.move(pos)
        except Exception as exc:
            PopupHelpers._log_helper_error(exc, PopupHelpers.EVENT_POSITION_POPUP_FAILED)

    @staticmethod
    def show_popup(
        *,
        timer,
        current_popup,
        anchor_widget,
        popup_factory,
        event_filter_owner=None,
        placement: str = "below_left",
        offset=None,
        keep_on_screen: bool = True,
        smart_flip: bool = True,
        screen_padding: int = 8,
    ):
        try:
            PopupHelpers.hide_popup(timer, current_popup, event_filter_owner)

            popup = popup_factory()
            if not PopupHelpers.is_popup_alive(popup):
                return None

            if event_filter_owner is not None:
                popup.installEventFilter(event_filter_owner)

            PopupHelpers.position_popup(
                popup,
                anchor_widget,
                placement=placement,
                offset=offset,
                keep_on_screen=keep_on_screen,
                smart_flip=smart_flip,
                screen_padding=screen_padding,
            )
            popup.show()
            popup.raise_()
            return popup
        except Exception as exc:
            PopupHelpers._log_helper_error(exc, PopupHelpers.EVENT_SHOW_POPUP_FAILED)
            return None

    @staticmethod
    def show_popup_for(
        popup_kind,
        *,
        timer,
        current_popup,
        anchor_widget,
        popup_factory,
        event_filter_owner=None,
    ):
        from PyQt5.QtCore import QPoint

        return PopupHelpers._with_profile(
            popup_kind,
            lambda profile: PopupHelpers.show_popup(
                timer=timer,
                current_popup=current_popup,
                anchor_widget=anchor_widget,
                popup_factory=popup_factory,
                event_filter_owner=event_filter_owner,
                placement=profile.get("placement", "below_left"),
                offset=QPoint(*profile.get("offset", (0, 0))),
                keep_on_screen=bool(profile.get("keep_on_screen", True)),
                smart_flip=bool(profile.get("smart_flip", True)),
                screen_padding=int(profile.get("screen_padding", 8)),
            ),
        )

    @staticmethod
    def apply_popup_style(widget, popup_kind: str | None = None) -> None:
        if not PopupHelpers.is_popup_alive(widget):
            return
        try:
            from ...widgets.theme_manager import ThemeManager
            from ...constants.file_paths import QssPaths

            style_key = PopupHelpers._with_profile(
                popup_kind,
                lambda profile: profile.get("style_key", "popup"),
            )
            style_paths = [QssPaths.POPUP] if style_key == "popup" else [QssPaths.DATES]
            ThemeManager.apply_module_style(widget, style_paths)
        except Exception as exc:
            PopupHelpers._log_helper_error(exc, PopupHelpers.EVENT_STYLE_APPLY_FAILED)

    @staticmethod
    def close_popup_widget(popup_widget, event_filter_owner=None):
        if not PopupHelpers.is_popup_alive(popup_widget):
            return None

        if event_filter_owner is not None:
            try:
                popup_widget.removeEventFilter(event_filter_owner)
            except Exception:
                pass

        try:
            popup_widget.close()
            popup_widget.deleteLater()
        except Exception:
            pass

        return None

    @staticmethod
    def hide_popup(timer, popup_widget, event_filter_owner=None):
        PopupHelpers.stop_hide_timer(timer)
        return PopupHelpers.close_popup_widget(popup_widget, event_filter_owner)