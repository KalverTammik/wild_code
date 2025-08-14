from PyQt5.QtCore import QObject

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
                except Exception:
                    pass
            if new_group is not None:
                try:
                    new_group.setLoopCount(-1)
                except Exception:
                    pass
                new_group.start()
            setattr(owner, attr_name, new_group)
        except Exception:
            try:
                setattr(owner, attr_name, None)
            except Exception:
                pass
