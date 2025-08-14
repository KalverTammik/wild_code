from PyQt5.QtCore import QObject
from PyQt5.QtGui import QColor

from .groups import AnimationGroupManager
from .pulses import create_colorize_pulse, build_glow_pulse
from .palettes import get_dev_halo_palette, get_frames_halo_palette


class AnimationController:
    """Central controller to apply animation state for a widget's dev controls.
    Keeps buttons stationary; only pulse effects indicate state.
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
    ):
        self._owner = owner
        self._glow = glow_effect
        self._dbg = dbg_effect
        self._frames = frames_effect
        self._dbg_glow_attr = dbg_glow_attr
        self._dbg_colorize_attr = dbg_colorize_attr
        self._frames_colorize_attr = frames_colorize_attr

    def apply_state(self, debug_on: bool, frames_on: bool):
        try:
            # Halo: pulse when either is ON
            if (debug_on or frames_on) and self._glow is not None:
                if debug_on:
                    start_col, mid_col, end_col = get_dev_halo_palette()
                else:
                    start_col, mid_col, end_col = get_frames_halo_palette()
                halo_grp = build_glow_pulse(self._glow, start_col, mid_col, end_col, duration=1200, parent=self._owner)
                AnimationGroupManager.ensure(self._owner, self._dbg_glow_attr, halo_grp)
            else:
                AnimationGroupManager.ensure(self._owner, self._dbg_glow_attr, None)
                # Reset to neutral halo
                try:
                    if self._glow is not None:
                        self._glow.setBlurRadius(16)
                        self._glow.setColor(QColor(255, 140, 0, 150))
                except Exception:
                    pass

            # DBG button pulse
            if debug_on and self._dbg is not None:
                dbg_grp = create_colorize_pulse(
                    self._dbg,
                    QColor(255, 102, 0),
                    QColor(255, 0, 160),
                    duration=1200,
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

            # Frames button pulse
            if frames_on and self._frames is not None:
                fr_grp = create_colorize_pulse(
                    self._frames,
                    QColor(0, 210, 255),
                    QColor(0, 255, 180),
                    duration=1200,
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

    def stop_all(self):
        try:
            AnimationGroupManager.ensure(self._owner, self._dbg_glow_attr, None)
            AnimationGroupManager.ensure(self._owner, self._dbg_colorize_attr, None)
            AnimationGroupManager.ensure(self._owner, self._frames_colorize_attr, None)
            try:
                if self._dbg is not None:
                    self._dbg.setStrength(0.0)
                if self._frames is not None:
                    self._frames.setStrength(0.0)
                if self._glow is not None:
                    self._glow.setBlurRadius(16)
                    self._glow.setColor(QColor(255, 140, 0, 150))
            except Exception:
                pass
        except Exception:
            pass
