from PyQt6.QtWidgets import QStyle

from tooltip_style import InstantTooltipStyle


def test_instant_tooltip_style_removes_wakeup_and_fall_asleep_delays():
    style = InstantTooltipStyle()
    assert style.styleHint(QStyle.StyleHint.SH_ToolTip_WakeUpDelay) == 0
    assert style.styleHint(QStyle.StyleHint.SH_ToolTip_FallAsleepDelay) == 0