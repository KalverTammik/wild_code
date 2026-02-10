from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
from PyQt5.QtGui import QColor
from ...Logs.python_fail_logger import PythonFailLogger


def create_colorize_pulse(effect, start_color: QColor, mid_color: QColor,
                           duration: int = 1200, strength_min: float = 0.15, strength_max: float = 0.9,
                           parent=None):
    """Create a looping colorize+strength pulse animation group for a given QGraphicsColorizeEffect.
    Returns the QParallelAnimationGroup or None on failure.
    """
    try:
        if effect is None:
            return None
        c_anim = QPropertyAnimation(effect, b"color", parent)
        c_anim.setDuration(int(duration))
        c_anim.setStartValue(start_color)
        c_anim.setKeyValueAt(0.5, mid_color)
        c_anim.setEndValue(start_color)
        try:
            c_anim.setEasingCurve(QEasingCurve.InOutSine)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="ui",
                event="pulse_color_easing_failed",
            )

        s_anim = QPropertyAnimation(effect, b"strength", parent)
        s_anim.setDuration(int(duration))
        s_anim.setStartValue(float(strength_min))
        s_anim.setKeyValueAt(0.5, float(strength_max))
        s_anim.setEndValue(float(strength_min))
        try:
            s_anim.setEasingCurve(QEasingCurve.InOutSine)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="ui",
                event="pulse_strength_easing_failed",
            )

        grp = QParallelAnimationGroup(parent)
        grp.addAnimation(c_anim)
        grp.addAnimation(s_anim)
        try:
            grp.setLoopCount(-1)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="ui",
                event="pulse_loop_count_failed",
            )
        return grp
    except Exception as exc:
        PythonFailLogger.log_exception(
            exc,
            module="ui",
            event="pulse_create_failed",
        )
        return None


def build_glow_pulse(
    glow_effect,
    start_color: QColor,
    mid_color: QColor,
    end_color: QColor,
    duration: int = 1200,
    parent=None,
    animate_blur: bool = False,
    blur_start: float = 16.0,
    blur_mid: float = 16.0,
    blur_end: float = 16.0,
):
    """Construct a frame glow animation group with color pulse only by default.
    Optionally animate blur if animate_blur=True. No yOffset/geometry movement is applied here.
    """
    try:
        if glow_effect is None:
            return None
        grp = QParallelAnimationGroup(parent)

        # Blur: keep constant by default to avoid layout/paint jitter
        if animate_blur:
            try:
                blur_anim = QPropertyAnimation(glow_effect, b"blurRadius", parent)
                blur_anim.setDuration(int(duration))
                blur_anim.setStartValue(float(blur_start))
                blur_anim.setKeyValueAt(0.5, float(blur_mid))
                blur_anim.setEndValue(float(blur_end))
                try:
                    blur_anim.setEasingCurve(QEasingCurve.InOutSine)
                except Exception as exc:
                    PythonFailLogger.log_exception(
                        exc,
                        module="ui",
                        event="glow_blur_easing_failed",
                    )
                grp.addAnimation(blur_anim)
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="ui",
                    event="glow_blur_anim_failed",
                )
        else:
            try:
                glow_effect.setBlurRadius(float(blur_start))
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="ui",
                    event="glow_blur_set_failed",
                )

        color_anim = QPropertyAnimation(glow_effect, b"color", parent)
        color_anim.setDuration(int(duration))
        color_anim.setStartValue(start_color)
        color_anim.setKeyValueAt(0.5, mid_color)
        color_anim.setEndValue(end_color)
        try:
            color_anim.setEasingCurve(QEasingCurve.InOutSine)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="ui",
                event="glow_color_easing_failed",
            )
        grp.addAnimation(color_anim)
        return grp
    except Exception as exc:
        PythonFailLogger.log_exception(
            exc,
            module="ui",
            event="glow_pulse_create_failed",
        )
        return None
