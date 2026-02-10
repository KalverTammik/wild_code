from PyQt5.QtCore import QObject
from ...Logs.python_fail_logger import PythonFailLogger

class AnimationGroupManager:
    """Utility to manage starting/stopping and swapping animation groups on an owner object."""
    @staticmethod
    def ensure(owner: QObject, attr_name: str, new_group):
        try:
            grp = getattr(owner, attr_name, None)
            if grp is not None:
                try:
                    grp.stop()
                    grp.deleteLater()
                except Exception as exc:
                    PythonFailLogger.log_exception(
                        exc,
                        module="ui",
                        event="animation_group_stop_failed",
                    )
            if new_group is not None:
                try:
                    new_group.setLoopCount(-1)
                except Exception as exc:
                    PythonFailLogger.log_exception(
                        exc,
                        module="ui",
                        event="animation_group_loop_count_failed",
                    )
                new_group.start()
            setattr(owner, attr_name, new_group)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="ui",
                event="animation_group_ensure_failed",
            )
            try:
                setattr(owner, attr_name, None)
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="ui",
                    event="animation_group_reset_failed",
                )
