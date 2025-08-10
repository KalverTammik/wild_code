from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from typing import Optional

def apply_chip_shadow(label, theme: Optional[str] = None):
    """Visible but tasteful chip shadow; theme chooses light/dark glow."""
    eff = QGraphicsDropShadowEffect(label)
    eff.setBlurRadius(20)
    eff.setXOffset(0)
    eff.setYOffset(2)
    if (theme or "dark").lower() == "dark":
        eff.setColor(QColor(255, 255, 255, 90))
    else:
        eff.setColor(QColor(0, 0, 0, 120))
    label.setGraphicsEffect(eff)