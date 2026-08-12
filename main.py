"""Benj Cursor Maker application entry point."""
from __future__ import annotations

import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from tooltip_style import InstantTooltipStyle
from ui import MainWindow, RETRO_STYLE


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Benj Cursor Maker")
    app.setEffectEnabled(Qt.UIEffect.UI_AnimateTooltip, False)
    app.setEffectEnabled(Qt.UIEffect.UI_FadeTooltip, False)
    app.setStyle(InstantTooltipStyle(app.style()))
    app.setStyleSheet(RETRO_STYLE)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
