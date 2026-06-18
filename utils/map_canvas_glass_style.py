from __future__ import annotations

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QGraphicsDropShadowEffect, QWidget


class MapCanvasGlassStyle:
    """Shared visual tokens for fixed map-canvas glass overlays."""

    FRAME_BACKGROUND = "rgba(248, 252, 255, 164)"
    FRAME_BORDER = "rgba(30, 126, 180, 120)"
    CONTROL_BACKGROUND = "rgba(255, 255, 255, 118)"
    CONTROL_BACKGROUND_HOVER = "rgba(255, 255, 255, 190)"
    CONTROL_BACKGROUND_FOCUS = "rgba(255, 255, 255, 210)"
    CONTROL_BACKGROUND_PRESSED = "rgba(203, 235, 247, 210)"
    CONTROL_BORDER = "rgba(22, 111, 151, 90)"
    CONTROL_BORDER_FOCUS = "rgba(22, 111, 151, 180)"
    CONTROL_BORDER_HOVER = "rgba(22, 111, 151, 170)"
    CONTROL_TEXT = "#12394a"
    FRAME_RADIUS = 8
    CONTROL_RADIUS = 6
    SHADOW_COLOR = QColor(0, 60, 80, 78)
    SHADOW_BLUR_RADIUS = 22
    SHADOW_OFFSET = (0, 8)

    @classmethod
    def apply_shadow(cls, widget: QWidget) -> None:
        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(cls.SHADOW_BLUR_RADIUS)
        shadow.setOffset(*cls.SHADOW_OFFSET)
        shadow.setColor(cls.SHADOW_COLOR)
        widget.setGraphicsEffect(shadow)

    @classmethod
    def action_bar_stylesheet(cls) -> str:
        return f"""
            QFrame#MapCanvasGlassActionBarFrame {{
                background: {cls.FRAME_BACKGROUND};
                border: 1px solid {cls.FRAME_BORDER};
                border-radius: {cls.FRAME_RADIUS}px;
            }}
            QPushButton#MapCanvasGlassActionButton {{
                min-width: 98px;
                height: 26px;
                padding: 0 10px;
                border-radius: {cls.CONTROL_RADIUS}px;
                border: 1px solid {cls.CONTROL_BORDER};
                background: {cls.CONTROL_BACKGROUND};
                color: {cls.CONTROL_TEXT};
                font-weight: 600;
            }}
            QPushButton#MapCanvasGlassActionButton:hover {{
                background: {cls.CONTROL_BACKGROUND_HOVER};
                border-color: {cls.CONTROL_BORDER_HOVER};
            }}
            QPushButton#MapCanvasGlassActionButton:pressed {{
                background: {cls.CONTROL_BACKGROUND_PRESSED};
            }}
            """

    @classmethod
    def search_bar_stylesheet(cls) -> str:
        return f"""
            QFrame#MapCanvasSearchBarFrame {{
                background: {cls.FRAME_BACKGROUND};
                border: 1px solid {cls.FRAME_BORDER};
                border-radius: {cls.FRAME_RADIUS}px;
            }}
            QLineEdit#MapCanvasSearchEdit {{
                height: 28px;
                padding: 0 9px;
                border-radius: {cls.CONTROL_RADIUS}px;
                border: 1px solid rgba(22, 111, 151, 95);
                background: rgba(255, 255, 255, 136);
                color: {cls.CONTROL_TEXT};
                selection-background-color: {cls.CONTROL_BORDER};
            }}
            QLineEdit#MapCanvasSearchEdit:focus {{
                background: {cls.CONTROL_BACKGROUND_FOCUS};
                border-color: {cls.CONTROL_BORDER_FOCUS};
            }}
            QPushButton#MapCanvasSearchButton {{
                border-radius: {cls.CONTROL_RADIUS}px;
                border: 1px solid {cls.CONTROL_BORDER};
                background: {cls.CONTROL_BACKGROUND};
            }}
            QPushButton#MapCanvasSearchButton:hover {{
                background: {cls.CONTROL_BACKGROUND_HOVER};
                border-color: {cls.CONTROL_BORDER_HOVER};
            }}
            """
