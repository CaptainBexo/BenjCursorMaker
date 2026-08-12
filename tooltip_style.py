"""Fast, stable Qt tooltip behavior without fade or wake-up lag."""
from __future__ import annotations

from PyQt6.QtWidgets import QProxyStyle, QStyle


class InstantTooltipStyle(QProxyStyle):
    """Preserve the active Qt style while making tooltips appear immediately."""

    def styleHint(self, hint, option=None, widget=None, returnData=None):
        if hint in (
            QStyle.StyleHint.SH_ToolTip_WakeUpDelay,
            QStyle.StyleHint.SH_ToolTip_FallAsleepDelay,
        ):
            return 0
        if hint == QStyle.StyleHint.SH_ToolTipLabel_Opacity:
            return 255
        return super().styleHint(hint, option, widget, returnData)
