from PyQt5.QtCore import QObject
from PyQt5.QtGui import QColor

from .groups import AnimationGroupManager
from .pulses import create_colorize_pulse


class AnimationController:
    """Central controller for dev controls animations.
    - Red colorize pulse for both buttons when active.
    """

    def __init__(
        self,
        owner: QObject,
        glow_effect=None,
        dbg_effect=None,
        frames_effect=None,
        dbg_glow_attr: str = "_dbg_glow_anim_group",
        dbg_colorize_attr: str = "_dbg_colorize_anim_group",
        frames_colorize_attr: str = "_frames_colorize_anim_group",
    ) -> None:
        self._owner = owner
        self._glow = glow_effect
        self._dbg = dbg_effect
        self._frames = frames_effect
        self._dbg_glow_attr = dbg_glow_attr
        self._dbg_colorize_attr = dbg_colorize_attr
        self._frames_colorize_attr = frames_colorize_attr

    def apply_state(self, debug_on: bool, frames_on: bool) -> None:
        try:
            # DBG red pulse
            if debug_on and self._dbg is not None:
                dbg_grp = create_colorize_pulse(
                    self._dbg,
                    QColor(220, 0, 0),
                    QColor(255, 40, 40),
                    duration=900,
                    strength_min=0.15,
                    strength_max=0.9,
                    parent=self._owner,
                )
                AnimationGroupManager.ensure(self._owner, self._dbg_colorize_attr, dbg_grp)
            else:
                AnimationGroupManager.ensure(self._owner, self._dbg_colorize_attr, None)
                try:
                    if self._dbg is not None:
                        self._dbg.setStrength(0.0)
                except Exception:
                    pass

            # Frames red pulse
            if frames_on and self._frames is not None:
                fr_grp = create_colorize_pulse(
                    self._frames,
                    QColor(220, 0, 0),
                    QColor(255, 40, 40),
                    duration=900,
                    strength_min=0.15,
                    strength_max=0.9,
                    parent=self._owner,
                )
                AnimationGroupManager.ensure(self._owner, self._frames_colorize_attr, fr_grp)
            else:
                AnimationGroupManager.ensure(self._owner, self._frames_colorize_attr, None)
                try:
                    if self._frames is not None:
                        self._frames.setStrength(0.0)
                except Exception:
                    pass
        except Exception:
            pass

    def stop_all(self) -> None:
        try:
            AnimationGroupManager.ensure(self._owner, self._dbg_glow_attr, None)
            AnimationGroupManager.ensure(self._owner, self._dbg_colorize_attr, None)
            AnimationGroupManager.ensure(self._owner, self._frames_colorize_attr, None)
            try:
                if self._dbg is not None:
                    self._dbg.setStrength(0.0)
                if self._frames is not None:
                    self._frames.setStrength(0.0)
            except Exception:
                pass
        except Exception:
            pass
