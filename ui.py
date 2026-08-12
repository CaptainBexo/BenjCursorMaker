"""PyQt6 user interface for Benj Cursor Maker."""
from __future__ import annotations

import io
import struct
from pathlib import Path

from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt6.QtCore import QEvent, QPoint, QRect, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QMouseEvent, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from exporter import (
    CursorFrame,
    build_ani,
    build_cur,
    export_ani,
    export_cur,
    export_cursorpack_folder,
    parse_ani,
    safe_pack_name,
)
from i18n import get_lang, set_lang, tr
from image_processor import ImageDocument, crop_image, fit_cursor, snap_rect


RETRO_STYLE = """
* {
    font-family: Consolas, "Courier New";
    font-size: 12px;
    color: #F2F3F5;
    selection-background-color: #47FF57;
    selection-color: #06100A;
}
QMainWindow, QDialog, QWidget { background-color: #060713; }
QGroupBox {
    background-color: #080B14;
    border: 1px solid #347A40;
    border-radius: 0px;
    margin-top: 12px;
    padding-top: 14px;
    font-weight: bold;
    color: #47FF57;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 9px;
    padding: 0 5px;
    background-color: #080B14;
    color: #47FF57;
}
QPushButton {
    background-color: #080B14;
    color: #F2F3F5;
    border: 1px solid #347A40;
    border-radius: 0px;
    padding: 8px 13px;
    font-weight: bold;
}
QPushButton:hover, QPushButton:focus {
    background-color: #0B1712;
    border-color: #47FF57;
    color: #47FF57;
}
QPushButton:pressed {
    background-color: #25C83A;
    border-color: #25C83A;
    color: #06100A;
}
QPushButton:disabled {
    background-color: #080B14;
    color: #69767C;
    border-color: #23362B;
}
QLineEdit, QSpinBox, QComboBox, QListWidget {
    background-color: #080C13;
    color: #F2F3F5;
    border: 1px solid #285E34;
    border-radius: 0px;
    padding: 6px;
}
QLineEdit:hover, QSpinBox:hover, QComboBox:hover, QListWidget:hover { border-color: #3E9A49; }
QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QListWidget:focus { border-color: #47FF57; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView {
    background-color: #080B14;
    color: #F2F3F5;
    border: 1px solid #47FF57;
    selection-background-color: #173F24;
    selection-color: #68FF73;
}
QListWidget::item { padding: 6px; border-bottom: 1px solid #111A21; }
QListWidget::item:selected { background-color: #173F24; color: #68FF73; }
QSlider::groove:horizontal {
    height: 6px;
    background-color: #101820;
    border: 1px solid #1E432B;
}
QSlider::sub-page:horizontal { background-color: #47FF57; }
QSlider::handle:horizontal {
    width: 12px;
    margin: -5px 0;
    background-color: #47FF57;
    border: 1px solid #B7FFBC;
}
QSlider::handle:horizontal:hover { background-color: #68FF73; }
QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #347A40;
    background-color: #080C13;
}
QCheckBox::indicator:checked { background-color: #47FF57; border-color: #78FF83; }
QSplitter::handle { background-color: #1E432B; width: 1px; }
QStatusBar {
    background-color: #080B14;
    border-top: 1px solid #347A40;
    color: #47FF57;
}
QToolTip {
    background-color: #080B14;
    color: #F2F3F5;
    border: 1px solid #47FF57;
}
"""


def pil_pixmap(image) -> QPixmap:
    return QPixmap.fromImage(ImageQt(image.convert("RGBA")))


def _cur_hotspot(data: bytes) -> tuple[int, int]:
    """Read hotspot from the ICONDIRENTRY of a .cur file (type 2) — independent of PIL."""
    if len(data) >= 22 and data[2:4] == b"\x02\x00":
        return (
            struct.unpack_from("<H", data, 10)[0],
            struct.unpack_from("<H", data, 12)[0],
        )
    return (0, 0)


def paint_canvas_background(painter: QPainter, rect: QRect) -> None:
    painter.fillRect(rect, QColor("#080B14"))


_PATTERN_CACHE: dict[int, QPixmap] = {}


def transparency_pattern(scale: int) -> QPixmap:
    """Checkerboard background for transparent areas — each tile is exactly 1 image pixel (2x2 repeated)."""
    pattern = _PATTERN_CACHE.get(scale)
    if pattern is None:
        s = max(scale, 1)
        pattern = QPixmap(s * 2, s * 2)
        pattern.fill(QColor("#232E4A"))
        painter = QPainter(pattern)
        painter.fillRect(0, 0, s, s, QColor("#12162A"))
        painter.fillRect(s, s, s, s, QColor("#12162A"))
        painter.end()
        _PATTERN_CACHE[scale] = pattern
    return pattern


class FloatingTip(QLabel):
    """Custom tooltip: floating label that follows the mouse, no system tooltip."""

    def __init__(self, parent=None) -> None:
        super().__init__(
            parent,
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setStyleSheet(
            "QLabel { background: #0B0F20; color: #47FF57; border: 1px solid #2E7D3A;"
            " padding: 4px 8px; font-family: 'Courier New'; font-size: 11px; }"
        )
        self.hide()

    def show_text(self, text: str, global_pos: QPoint) -> None:
        if self.text() != text:
            self.setText(text)
            self.adjustSize()
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(
            min(global_pos.x() + 14, screen.right() - self.width()),
            min(global_pos.y() + 18, screen.bottom() - self.height()),
        )
        if not self.isVisible():
            self.show()
            self.raise_()

    def hide_tip(self) -> None:
        self.hide()


class ZoomControl(QWidget):
    """Compact zoom control in the canvas corner: [+] 100% [-]."""

    def __init__(self, on_zoom_in=None, on_zoom_out=None, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)
        self.in_button = QPushButton("+")
        self.label = QLabel("100%")
        self.out_button = QPushButton("-")
        self.in_button.setFixedSize(24, 20)
        self.out_button.setFixedSize(24, 20)
        self.in_button.setToolTip(tr("tip.zoom_in"))
        self.out_button.setToolTip(tr("tip.zoom_out"))
        if on_zoom_in:
            self.in_button.clicked.connect(on_zoom_in)
        if on_zoom_out:
            self.out_button.clicked.connect(on_zoom_out)
        layout.addWidget(self.in_button)
        layout.addWidget(self.label)
        layout.addWidget(self.out_button)
        self.setStyleSheet(
            "ZoomControl { background: #0A0E1A; border: 1px solid #2E7D3A; }"
            "ZoomControl QPushButton { background: transparent; color: #47FF57; border: none;"
            " padding: 0px; min-width: 0px; min-height: 0px;"
            " font-family: 'Courier New'; font-size: 14px; font-weight: bold; }"
            "ZoomControl QPushButton:hover { color: #B7FFBC; }"
            "ZoomControl QLabel { color: #7DE3FF; font-family: 'Courier New'; font-size: 11px; }"
        )

    def set_percent(self, percent: int) -> None:
        self.label.setText(f"{percent}%")

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        parent = self.parent()
        if parent is not None and hasattr(parent, "_place_zoom_control"):
            parent._place_zoom_control()


class FloatingTipOwner:
    """Mixin: smooth mouse-following floating tip shared by the Editor and dialogs."""

    def _init_floating_tip(self) -> None:
        self._tip = FloatingTip(self)
        self._tip_widgets: list[QWidget] = []

    def _register_tip_widget(self, widget: QWidget) -> None:
        widget.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        widget.installEventFilter(self)
        self._tip_widgets.append(widget)

    def eventFilter(self, obj, event) -> bool:
        etype = event.type()
        if obj in self._tip_widgets:
            if etype == QEvent.Type.ToolTip:
                return True  # swallow native tooltip, use the floating tip instead
            if etype in (QEvent.Type.HoverEnter, QEvent.Type.HoverMove):
                self._tip.show_text(obj.toolTip(), event.globalPosition().toPoint())
            elif etype in (QEvent.Type.HoverLeave, QEvent.Type.MouseButtonPress):
                self._tip.hide_tip()
            return False
        if obj is self and etype in (QEvent.Type.WindowDeactivate, QEvent.Type.WindowMove):
            self._tip.hide_tip()
        return super().eventFilter(obj, event)


class CropCanvas(QWidget):
    selectionChanged = pyqtSignal(tuple)
    zoomChanged = pyqtSignal(float)
    panChanged = pyqtSignal(QPoint)
    zoomInRequested = pyqtSignal()
    zoomOutRequested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(420, 420)
        self.setMouseTracking(True)
        self.image = None
        self.selection: tuple[int, int, int, int] | None = None
        self.grid = 1
        self._drag_start: tuple[int, int] | None = None
        self._pan_drag: tuple[QPoint, QPoint] | None = None
        self._target = QRect()
        self._scale = 1
        self._zoom = 1.0
        self._pan = QPoint()
        self.zoom_control = ZoomControl(
            on_zoom_in=lambda: self.zoomInRequested.emit(),
            on_zoom_out=lambda: self.zoomOutRequested.emit(),
            parent=self,
        )
        self.zoom_control.move(8, 8)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._place_zoom_control()

    def _place_zoom_control(self) -> None:
        margin = 8
        self.zoom_control.move(margin, self.height() - self.zoom_control.height() - margin)

    def sizeHint(self) -> QSize:
        return QSize(600, 540)

    def set_image(self, image, reset_selection: bool = False) -> None:
        self.image = image
        if image is None:
            self.selection = None
        elif reset_selection or self.selection is None:
            self.selection = (0, 0, image.width, image.height)
        else:
            x1, y1, x2, y2 = self.selection
            self.selection = (
                min(max(x1, 0), image.width),
                min(max(y1, 0), image.height),
                min(max(x2, 0), image.width),
                min(max(y2, 0), image.height),
            )
        self.update()

    def set_grid(self, grid: int) -> None:
        self.grid = grid
        if self.selection and self.image:
            self.selection = snap_rect(self.selection, grid, self.image.size)
            self.selectionChanged.emit(self.selection)
        self.update()

    def _layout_image(self) -> None:
        if not self.image:
            self._target = QRect()
            return
        margin = 18
        fit = max(1, min((self.width() - margin * 2) // self.image.width, (self.height() - margin * 2) // self.image.height))
        self._scale = max(1, int(fit * self._zoom))
        draw_w, draw_h = self.image.width * self._scale, self.image.height * self._scale
        cx = (self.width() - draw_w) // 2
        cy = (self.height() - draw_h) // 2
        min_x, max_x = 8 - draw_w, self.width() - 8
        min_y, max_y = 8 - draw_h, self.height() - 8
        px = max(min_x, min(max_x, cx + self._pan.x()))
        py = max(min_y, min(max_y, cy + self._pan.y()))
        self._pan.setX(px - cx)
        self._pan.setY(py - cy)
        self._target = QRect(px, py, draw_w, draw_h)

    def set_zoom(self, zoom: float) -> None:
        if self._zoom != zoom:
            self._zoom = zoom
            self.update()

    def set_pan(self, pan: QPoint) -> None:
        if self._pan != pan:
            self._pan = QPoint(pan)
            self._layout_image()
            self.update()

    def wheelEvent(self, event) -> None:
        if not self.image:
            return
        factor = 1.25 if event.angleDelta().y() > 0 else 0.8
        new_zoom = max(1.0, min(self._zoom * factor, 32.0))
        if new_zoom == self._zoom:
            return
        self._layout_image()
        pos = event.position().toPoint()
        u = (pos.x() - self._target.x()) / self._scale
        v = (pos.y() - self._target.y()) / self._scale
        self._zoom = new_zoom
        self._layout_image()
        self._pan.setX(self._pan.x() + int(pos.x() - u * self._scale) - self._target.x())
        self._pan.setY(self._pan.y() + int(pos.y() - v * self._scale) - self._target.y())
        self._layout_image()
        self.zoomChanged.emit(self._zoom)
        self.update()

    def _to_image(self, point: QPoint) -> tuple[int, int]:
        x = min(max((point.x() - self._target.x()) // self._scale, 0), self.image.width)
        y = min(max((point.y() - self._target.y()) // self._scale, 0), self.image.height)
        return int(x), int(y)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        paint_canvas_background(painter, self.rect())
        if not self.image:
            painter.setPen(QColor("#347A40"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, tr("canvas.empty_crop"))
            return
        self._layout_image()
        painter.drawTiledPixmap(self._target, transparency_pattern(self._scale))
        pixmap = pil_pixmap(self.image)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        painter.drawPixmap(self._target, pixmap)
        if self._scale >= 8:
            painter.setPen(QPen(QColor(24, 55, 34, 125), 1))
            for x in range(self.image.width + 1):
                sx = self._target.x() + x * self._scale
                painter.drawLine(sx, self._target.y(), sx, self._target.bottom())
            for y in range(self.image.height + 1):
                sy = self._target.y() + y * self._scale
                painter.drawLine(self._target.x(), sy, self._target.right(), sy)
        if self.selection:
            x1, y1, x2, y2 = self.selection
            rect = QRect(self._target.x() + x1 * self._scale, self._target.y() + y1 * self._scale, (x2 - x1) * self._scale, (y2 - y1) * self._scale)
            painter.setPen(QPen(QColor("#47FF57"), 2, Qt.PenStyle.DashLine))
            painter.drawRect(rect)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self._layout_image()
        if event.button() == Qt.MouseButton.MiddleButton:
            self._pan_drag = (event.globalPosition().toPoint(), QPoint(self._pan))
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return
        if self.image and event.button() == Qt.MouseButton.LeftButton and self._target.contains(event.position().toPoint()):
            self._drag_start = self._to_image(event.position().toPoint())
            self.selection = (*self._drag_start, *self._drag_start)
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._pan_drag:
            start_global, start_pan = self._pan_drag
            delta = event.globalPosition().toPoint() - start_global
            self._pan = start_pan + delta
            self._layout_image()
            self.update()
            self.panChanged.emit(QPoint(self._pan))
            return
        if self.image and self._drag_start:
            current = self._to_image(event.position().toPoint())
            self.selection = snap_rect((*self._drag_start, *current), self.grid, self.image.size)
            self.selectionChanged.emit(self.selection)
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.MiddleButton and self._pan_drag:
            self._pan_drag = None
            self.unsetCursor()
            return
        if self._drag_start:
            self.mouseMoveEvent(event)
            self._drag_start = None


class HotspotCanvas(QWidget):
    hotspotChanged = pyqtSignal(int, int)
    hoverTip = pyqtSignal(str, QPoint)
    hoverLeft = pyqtSignal()
    zoomChanged = pyqtSignal(float)
    panChanged = pyqtSignal(QPoint)

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(300, 300)
        self.setMouseTracking(True)
        self.image = None
        self.hotspot = (0, 0)
        self._target = QRect()
        self._scale = 1
        self._zoom = 1.0
        self._pan = QPoint()
        self._pan_drag: tuple[QPoint, QPoint] | None = None

    def set_image(self, image, hotspot=(0, 0)) -> None:
        self.image = image
        self.hotspot = hotspot
        self.update()

    def _layout_image(self) -> None:
        if not self.image:
            return
        fit = max(1, min((self.width() - 24) // self.image.width, (self.height() - 24) // self.image.height))
        self._scale = max(1, int(fit * self._zoom))
        draw_w, draw_h = self.image.width * self._scale, self.image.height * self._scale
        cx = (self.width() - draw_w) // 2
        cy = (self.height() - draw_h) // 2
        min_x, max_x = 8 - draw_w, self.width() - 8
        min_y, max_y = 8 - draw_h, self.height() - 8
        px = max(min_x, min(max_x, cx + self._pan.x()))
        py = max(min_y, min(max_y, cy + self._pan.y()))
        self._pan.setX(px - cx)
        self._pan.setY(py - cy)
        self._target = QRect(px, py, draw_w, draw_h)

    def set_zoom(self, zoom: float) -> None:
        if self._zoom != zoom:
            self._zoom = zoom
            self.update()

    def set_pan(self, pan: QPoint) -> None:
        if self._pan != pan:
            self._pan = QPoint(pan)
            self._layout_image()
            self.update()

    def wheelEvent(self, event) -> None:
        if not self.image:
            return
        factor = 1.25 if event.angleDelta().y() > 0 else 0.8
        new_zoom = max(1.0, min(self._zoom * factor, 32.0))
        if new_zoom == self._zoom:
            return
        self._layout_image()
        pos = event.position().toPoint()
        u = (pos.x() - self._target.x()) / self._scale
        v = (pos.y() - self._target.y()) / self._scale
        self._zoom = new_zoom
        self._layout_image()
        self._pan.setX(self._pan.x() + int(pos.x() - u * self._scale) - self._target.x())
        self._pan.setY(self._pan.y() + int(pos.y() - v * self._scale) - self._target.y())
        self._layout_image()
        self.zoomChanged.emit(self._zoom)
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        paint_canvas_background(painter, self.rect())
        if not self.image:
            painter.setPen(QColor("#347A40"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, tr("canvas.empty_hotspot"))
            return
        self._layout_image()
        painter.drawTiledPixmap(self._target, transparency_pattern(self._scale))
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        painter.drawPixmap(self._target, pil_pixmap(self.image))
        if self._scale >= 6:
            painter.setPen(QPen(QColor(24, 55, 34, 135), 1))
            for x in range(self.image.width + 1):
                sx = self._target.x() + x * self._scale
                painter.drawLine(sx, self._target.y(), sx, self._target.bottom())
            for y in range(self.image.height + 1):
                sy = self._target.y() + y * self._scale
                painter.drawLine(self._target.x(), sy, self._target.right(), sy)
        x, y = self.hotspot
        cx = self._target.x() + x * self._scale + self._scale // 2
        cy = self._target.y() + y * self._scale + self._scale // 2
        painter.setPen(QPen(QColor("#B7FFBC"), 2))
        painter.drawLine(cx, self._target.top(), cx, self._target.bottom())
        painter.drawLine(self._target.left(), cy, self._target.right(), cy)
        painter.setPen(QPen(QColor("#47FF57"), 2))
        painter.drawRect(self._target.x() + x * self._scale, self._target.y() + y * self._scale, self._scale, self._scale)

    def _pixel_at(self, point: QPoint) -> tuple[int, int] | None:
        if not self.image or not self._target.contains(point):
            return None
        x = min(max((point.x() - self._target.x()) // self._scale, 0), self.image.width - 1)
        y = min(max((point.y() - self._target.y()) // self._scale, 0), self.image.height - 1)
        return int(x), int(y)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self._layout_image()
        if event.button() == Qt.MouseButton.MiddleButton:
            self._pan_drag = (event.globalPosition().toPoint(), QPoint(self._pan))
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return
        pixel = self._pixel_at(event.position().toPoint())
        if pixel is not None:
            self.hotspot = pixel
            self.hotspotChanged.emit(*self.hotspot)
            self.update()
        self.hoverLeft.emit()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._pan_drag:
            start_global, start_pan = self._pan_drag
            delta = event.globalPosition().toPoint() - start_global
            self._pan = start_pan + delta
            self._layout_image()
            self.update()
            self.panChanged.emit(QPoint(self._pan))
            return
        self._layout_image()
        if not self.image:
            self.hoverTip.emit(tr("hint.no_image"), event.globalPosition().toPoint())
            return
        pixel = self._pixel_at(event.position().toPoint())
        if pixel is None:
            self.hoverLeft.emit()
            return
        x, y = pixel
        self.hoverTip.emit(
            tr("hotspot.hover", x=x, y=y),
            event.globalPosition().toPoint(),
        )

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.MiddleButton and self._pan_drag:
            self._pan_drag = None
            self.unsetCursor()

    def leaveEvent(self, event) -> None:
        self.hoverLeft.emit()
        super().leaveEvent(event)


CURSOR_ROLES = {
    "Normal Select": "Arrow", "Help Select": "Help", "Working in Background": "AppStarting",
    "Busy": "Wait", "Precision Select": "Crosshair", "Text Select": "IBeam", "Handwriting": "NWPen",
    "Unavailable": "No", "Vertical Resize": "SizeNS", "Horizontal Resize": "SizeWE",
    "Diagonal Resize 1": "SizeNWSE", "Diagonal Resize 2": "SizeNESW", "Move": "SizeAll",
    "Alternate Select": "UpArrow", "Link Select": "Hand",
}


class CursorPackDialog(FloatingTipOwner, QDialog):
    def __init__(self, parent=None, main_window=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("pack.title"))
        self.resize(780, 590)
        self.main_window = main_window
        self.assignments: dict[str, Path] = {}
        self.memory_cursors: dict[str, bytes] = {}
        self._init_floating_tip()
        self._preview = QLabel(self)
        self._preview.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._preview.setStyleSheet("background: transparent; border: none;")
        self._preview.hide()
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._advance_preview)
        self._preview_role: str | None = None
        self._preview_frame = 0
        self._preview_hotspot = (0, 0)
        self._preview_rates: list[int] = []
        self._preview_pos = QPoint(0, 0)
        self._preview_cache: dict[str, tuple[list[QPixmap], tuple[int, int], list[int]]] = {}
        if main_window is not None:
            self.assignments = dict(main_window.pack_assignments)
            self.memory_cursors = dict(main_window.pack_cursors)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name_edit = QLineEdit("Neon Pixel Pack")
        self.name_edit.setToolTip(tr("pack.tip.scheme"))
        if main_window is not None and main_window.pack_name:
            self.name_edit.setText(main_window.pack_name)
        form.addRow(tr("pack.scheme_label"), self.name_edit)
        layout.addLayout(form)
        self._register_tip_widget(self.name_edit)
        self.list = QListWidget()
        self.list.setToolTip(tr("pack.tip.list"))
        for label, role in CURSOR_ROLES.items():
            self.list.addItem(f"{label:<24} [{role}]   {tr('pack.unassigned')}")
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        layout.addWidget(self.list)
        self._register_tip_widget(self.list)
        self.list.viewport().setToolTip(tr("pack.tip.list"))
        self._register_tip_widget(self.list.viewport())
        for row in range(len(CURSOR_ROLES)):
            self._refresh_row(row)
        row = QHBoxLayout()
        assign = QPushButton(tr("pack.assign_file"))
        clear = QPushButton(tr("pack.clear"))
        assign.setToolTip(tr("pack.tip.assign_file"))
        clear.setToolTip(tr("pack.tip.clear"))
        assign.clicked.connect(self.assign_file)
        clear.clicked.connect(self.clear_file)
        row.addWidget(assign)
        row.addWidget(clear)
        layout.addLayout(row)
        self._register_tip_widget(assign)
        self._register_tip_widget(clear)
        row2 = QHBoxLayout()
        assign_current = QPushButton(tr("pack.assign_current"))
        assign_all = QPushButton(tr("pack.assign_all"))
        assign_current.setToolTip(tr("pack.tip.assign_current"))
        assign_all.setToolTip(tr("pack.tip.assign_all"))
        assign_current.clicked.connect(self.assign_current_cursor)
        assign_all.clicked.connect(self.assign_to_all)
        row2.addWidget(assign_current)
        row2.addWidget(assign_all)
        layout.addLayout(row2)
        self._register_tip_widget(assign_current)
        self._register_tip_widget(assign_all)
        buttons = QHBoxLayout()
        apply_button = QPushButton(tr("pack.apply"))
        save_button = QPushButton(tr("pack.save"))
        cancel_button = QPushButton(tr("pack.cancel"))
        apply_button.setToolTip(tr("pack.tip.apply"))
        save_button.setToolTip(tr("pack.tip.save"))
        cancel_button.setToolTip(tr("pack.tip.cancel"))
        apply_button.clicked.connect(self.apply_pack)
        save_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        buttons.addStretch(1)
        buttons.addWidget(apply_button)
        buttons.addWidget(save_button)
        buttons.addWidget(cancel_button)
        layout.addLayout(buttons)
        self._register_tip_widget(apply_button)
        self._register_tip_widget(save_button)
        self._register_tip_widget(cancel_button)

    def _role_at(self, row: int) -> str:
        return list(CURSOR_ROLES.values())[row]

    def _refresh_row(self, row: int) -> None:
        label = list(CURSOR_ROLES.keys())[row]
        role = self._role_at(row)
        value = self.assignments.get(role)
        marker = tr("pack.from_editor") if role in self.memory_cursors else ""
        self.list.item(row).setText(f"{label:<24} [{role}]   {value.name if value else tr('pack.unassigned')}{marker}")

    # --- Preview con trỏ khi hover ---
    def eventFilter(self, obj, event) -> bool:
        etype = event.type()
        if obj is self.list or obj is self.list.viewport():
            if etype in (QEvent.Type.HoverEnter, QEvent.Type.HoverMove):
                item = self.list.itemAt(event.position().toPoint())
                if item is not None:
                    role = self._role_at(self.list.row(item))
                    if self._preview_role == role and self._preview.isVisible():
                        self._preview_pos = event.globalPosition().toPoint()
                        self._place_preview()
                        return True
                    if self._show_preview(role, event):
                        return True  # suppress tooltip while previewing
                    self._hide_preview()  # unassigned item -> turn the old preview off
                else:
                    self._hide_preview()
            elif etype in (QEvent.Type.HoverLeave, QEvent.Type.MouseButtonPress):
                self._hide_preview()
        if obj is self and etype == QEvent.Type.WindowDeactivate:
            self._hide_preview()
        return super().eventFilter(obj, event)

    def _load_preview(self, role: str) -> tuple[list[QPixmap], tuple[int, int], list[int]] | None:
        """(pixmaps, hotspot, rates_ms) for an assigned state, or None if unassigned/unreadable."""
        cached = self._preview_cache.get(role)
        if cached is not None:
            return cached
        data: bytes | None = None
        if role in self.memory_cursors:
            data = self.memory_cursors[role]
        else:
            path = self.assignments.get(role)
            if path is None:
                return None
            try:
                data = Path(path).read_bytes()
            except OSError:
                return None
        try:
            if data[:4] == b"RIFF":  # .ani
                pil_frames, hotspot, rates = parse_ani(data)
                frames = [pil_pixmap(frame) for frame in pil_frames]
                rates_ms = [max(16, round(rate * 1000 / 60)) for rate in rates]
            else:  # .cur
                image = Image.open(io.BytesIO(data)).convert("RGBA")
                hotspot = _cur_hotspot(data)
                frames = [pil_pixmap(image)]
                rates_ms = [0]
            result = (frames, hotspot, rates_ms)
            self._preview_cache[role] = result
            return result
        except Exception:
            return None

    def _show_preview(self, role: str, event) -> bool:
        preview = self._load_preview(role)
        if preview is None:
            return False
        frames, hotspot, rates_ms = preview
        self._preview_role = role
        self._preview_frame = 0
        self._preview_hotspot = hotspot
        self._preview_rates = rates_ms
        self._preview_pos = event.globalPosition().toPoint()
        self._preview.setPixmap(frames[0])
        self._preview.resize(frames[0].width(), frames[0].height())
        self._place_preview()
        self._preview.show()
        self._preview.raise_()
        self.list.viewport().setCursor(Qt.CursorShape.BlankCursor)
        if len(frames) > 1:
            self._anim_timer.start(max(16, rates_ms[1]))
        return True

    def _place_preview(self) -> None:
        hx, hy = self._preview_hotspot
        self._preview.move(self.mapFromGlobal(self._preview_pos) - QPoint(hx, hy))

    def _advance_preview(self) -> None:
        if self._preview_role is None:
            return
        frames, _hot, rates_ms = self._preview_cache[self._preview_role]
        self._preview_frame = (self._preview_frame + 1) % len(frames)
        self._preview.setPixmap(frames[self._preview_frame])
        self._preview.resize(frames[self._preview_frame].width(), frames[self._preview_frame].height())
        nxt = rates_ms[(self._preview_frame + 1) % len(frames)]
        self._anim_timer.start(max(16, nxt))

    def _hide_preview(self) -> None:
        self._anim_timer.stop()
        self._preview.hide()
        self._preview_role = None
        self.list.viewport().unsetCursor()

    def _store_memory_cursor(self, role: str) -> None:
        frames = self.main_window.cursor_frames()
        if len(frames) > 1:
            name = f"{role}.ani"
            data = build_ani(frames)
        else:
            name = f"{role}.cur"
            data = build_cur(frames[0])
        self.assignments[role] = Path(name)
        self.memory_cursors[role] = data
        self._preview_cache.pop(role, None)

    def assign_current_cursor(self) -> None:
        if self.main_window is None or self.main_window.document is None:
            QMessageBox.warning(self, tr("pack.warn.no_image"), tr("pack.warn.no_image_body"))
            return
        row = self.list.currentRow()
        if row < 0:
            QMessageBox.information(self, tr("pack.warn.no_selection"), tr("pack.warn.no_selection_body"))
            return
        role = self._role_at(row)
        self._store_memory_cursor(role)
        self._refresh_row(row)

    def assign_to_all(self) -> None:
        if self.main_window is None or self.main_window.document is None:
            QMessageBox.warning(self, tr("pack.warn.no_image"), tr("pack.warn.no_image_body"))
            return
        for role in CURSOR_ROLES.values():
            self._store_memory_cursor(role)
        for row in range(len(CURSOR_ROLES)):
            self._refresh_row(row)

    def build_files(self) -> dict[Path, bytes]:
        return {
            self.assignments[role]: data
            for role, data in self.memory_cursors.items()
            if role in self.assignments
        }

    def assign_file(self) -> None:
        row = self.list.currentRow()
        if row < 0:
            return
        filename, _ = QFileDialog.getOpenFileName(self, tr("pack.choose_cursor"), "", "Windows Cursor (*.cur *.ani)")
        if filename:
            role = self._role_at(row)
            self.assignments[role] = Path(filename)
            self.memory_cursors.pop(role, None)
            self._preview_cache.pop(role, None)
            self._refresh_row(row)

    def clear_file(self) -> None:
        row = self.list.currentRow()
        if row >= 0:
            role = self._role_at(row)
            self.assignments.pop(role, None)
            self.memory_cursors.pop(role, None)
            self._preview_cache.pop(role, None)
            self._refresh_row(row)

    def _persist(self) -> None:
        if self.main_window is not None:
            self.main_window.pack_assignments = dict(self.assignments)
            self.main_window.pack_cursors = dict(self.memory_cursors)
            self.main_window.pack_name = self.name_edit.text().strip()

    def _assign_selected_role_if_possible(self) -> bool:
        """Directly assign the current editor cursor to the selected state when an image is open. True if assigned."""
        if self.main_window is None or self.main_window.document is None:
            return False
        row = self.list.currentRow()
        if row < 0:
            return False
        role = self._role_at(row)
        self._store_memory_cursor(role)
        self._refresh_row(row)
        return True

    def apply_pack(self) -> None:
        """Directly assign the current editor cursor (image + state selected), save temporarily and close to keep editing."""
        assigned = self._assign_selected_role_if_possible()
        if not self.assignments:
            if self.main_window is None or self.main_window.document is None:
                QMessageBox.warning(self, tr("pack.warn.no_image"), tr("pack.warn.no_image_body"))
            else:
                QMessageBox.information(
                    self, tr("pack.warn.no_role"), tr("pack.warn.no_role_body"),
                )
            return
        self._persist()
        if self.main_window is not None:
            detail = f" → {self._role_at(self.list.currentRow())}" if assigned else ""
            self.main_window.statusBar().showMessage(tr("status.applied", detail=detail, n=len(self.assignments)))
        self.done(2)  # close without triggering export (only Accepted exports)

    def accept(self) -> None:
        self._assign_selected_role_if_possible()
        if not self.name_edit.text().strip() or not self.assignments:
            QMessageBox.warning(self, tr("pack.warn.missing"), tr("pack.warn.missing_body"))
            return
        self._persist()
        super().accept()


class MainWindow(FloatingTipOwner, QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("BENJ CURSOR MAKER // NEON PIXEL EDITION")
        self.resize(1240, 780)
        self.document: ImageDocument | None = None
        self.frame_index = 0
        self.hotspots: list[tuple[int, int]] = []
        self.cropped_frames: list | None = None
        self.pack_assignments: dict[str, Path] = {}
        self.pack_cursors: dict[str, bytes] = {}
        self.pack_name = ""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_frame)
        self._init_floating_tip()
        self._zoom = 1.0
        self._retranslate_actions: list = []
        self._build_ui()
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage(tr("status.ready"))

    def _on_retranslate(self, action) -> None:
        self._retranslate_actions.append(action)

    def toggle_lang(self) -> None:
        set_lang("en" if get_lang() == "vi" else "vi")
        self.retranslate()

    def retranslate(self) -> None:
        for action in self._retranslate_actions:
            action()
        self.lang_button.setText(tr("btn.lang"))
        self.lang_button.setToolTip(tr("tip.lang"))
        self.statusBar().showMessage(tr("status.ready"))
        self.crop_canvas.update()  # repaint canvas text in the new language
        self.hotspot_canvas.update()
        self._tip.hide_tip()

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        toolbar = QHBoxLayout()
        actions = (
            ("btn.import", self.import_file, "tip.import"),
            ("btn.apply_crop", self.apply_crop, "tip.apply_crop"),
            ("btn.export_cur", self.export_cur_file, "tip.export_cur"),
            ("btn.export_ani", self.export_ani_file, "tip.export_ani"),
            ("btn.cursorpack", self.make_pack, "tip.cursorpack"),
        )
        for text_key, slot, tip_key in actions:
            button = QPushButton(tr(text_key))
            button.clicked.connect(slot)
            button.setToolTip(tr(tip_key))
            self._register_tip_widget(button)
            toolbar.addWidget(button)
            self._on_retranslate(lambda b=button, tk=text_key: b.setText(tr(tk)))
            self._on_retranslate(lambda b=button, tk=tip_key: b.setToolTip(tr(tk)))
            setattr(self, text_key.removeprefix("btn.") + "_button", button)
        toolbar.addStretch(1)
        self.lang_button = QPushButton(tr("btn.lang"))
        self.lang_button.setToolTip(tr("tip.lang"))
        self.lang_button.setFixedWidth(44)
        self.lang_button.clicked.connect(self.toggle_lang)
        self._register_tip_widget(self.lang_button)
        toolbar.addWidget(self.lang_button)
        outer.addLayout(toolbar)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.crop_canvas = CropCanvas()
        self.crop_canvas.selectionChanged.connect(self.selection_changed)
        self.crop_canvas.zoomChanged.connect(self._set_zoom)
        self.crop_canvas.panChanged.connect(self._set_pan)
        self.crop_canvas.zoomInRequested.connect(self.zoom_in)
        self.crop_canvas.zoomOutRequested.connect(self.zoom_out)
        self._register_tip_widget(self.crop_canvas.zoom_control.in_button)
        self._register_tip_widget(self.crop_canvas.zoom_control.out_button)
        self._on_retranslate(
            lambda: self.crop_canvas.zoom_control.in_button.setToolTip(tr("tip.zoom_in"))
        )
        self._on_retranslate(
            lambda: self.crop_canvas.zoom_control.out_button.setToolTip(tr("tip.zoom_out"))
        )
        splitter.addWidget(self.crop_canvas)

        side = QWidget()
        side_layout = QVBoxLayout(side)
        self.source_box = QGroupBox(tr("title.source"))
        self._on_retranslate(lambda: self.source_box.setTitle(tr("title.source")))
        source_layout = QGridLayout(self.source_box)
        self.play_button = QPushButton(tr("btn.play"))
        self.play_button.setToolTip(tr("tip.play"))
        self.play_button.clicked.connect(self.toggle_play)
        self._register_tip_widget(self.play_button)
        self._on_retranslate(lambda: self.play_button.setText(tr("btn.play")))
        self._on_retranslate(lambda: self.play_button.setToolTip(tr("tip.play")))
        self.frame_slider = QSlider(Qt.Orientation.Horizontal)
        self.frame_slider.setToolTip(tr("tip.frame_slider"))
        self.frame_slider.valueChanged.connect(self.set_frame)
        self._register_tip_widget(self.frame_slider)
        self._on_retranslate(lambda: self.frame_slider.setToolTip(tr("tip.frame_slider")))
        self.frame_label = QLabel("FRAME 0 / 0")
        source_layout.addWidget(self.play_button, 0, 0)
        source_layout.addWidget(self.frame_slider, 0, 1)
        source_layout.addWidget(self.frame_label, 1, 0, 1, 2)
        side_layout.addWidget(self.source_box)

        self.crop_box = QGroupBox(tr("title.grid_snap"))
        self._on_retranslate(lambda: self.crop_box.setTitle(tr("title.grid_snap")))
        crop_layout = QFormLayout(self.crop_box)
        self.grid_combo = QComboBox()
        self.grid_combo.setToolTip(tr("tip.grid_combo"))
        self.grid_combo.addItems(["OFF", "16 × 16", "32 × 32", "48 × 48"])
        self.grid_combo.currentIndexChanged.connect(lambda i: self.crop_canvas.set_grid([1, 16, 32, 48][i]))
        self._register_tip_widget(self.grid_combo)
        self._on_retranslate(lambda: self.grid_combo.setToolTip(tr("tip.grid_combo")))
        self.selection_label = QLabel("0, 0 → 0, 0")
        crop_layout.addRow("Snap:", self.grid_combo)
        crop_layout.addRow("Rect:", self.selection_label)
        side_layout.addWidget(self.crop_box)

        self.hotspot_box = QGroupBox(tr("title.hotspot"))
        self._on_retranslate(lambda: self.hotspot_box.setTitle(tr("title.hotspot")))
        hotspot_layout = QVBoxLayout(self.hotspot_box)
        self.hotspot_canvas = HotspotCanvas()
        self.hotspot_canvas.hotspotChanged.connect(self.hotspot_changed)
        self.hotspot_canvas.hoverTip.connect(self._tip.show_text)
        self.hotspot_canvas.hoverLeft.connect(self._tip.hide_tip)
        self.hotspot_canvas.zoomChanged.connect(self._set_zoom)
        self.hotspot_canvas.panChanged.connect(self._set_pan)
        self.hotspot_label = QLabel("HOTSPOT X:0  Y:0")
        hotspot_layout.addWidget(self.hotspot_canvas, 1)
        hotspot_layout.addWidget(self.hotspot_label)
        side_layout.addWidget(self.hotspot_box, 1)
        splitter.addWidget(side)
        splitter.setSizes([730, 460])
        outer.addWidget(splitter, 1)

    def zoom_in(self) -> None:
        self._set_zoom(min(self._zoom * 1.5, 32.0))

    def zoom_out(self) -> None:
        self._set_zoom(max(self._zoom / 1.5, 1.0))

    def _set_zoom(self, zoom: float) -> None:
        self._zoom = zoom
        self.crop_canvas.set_zoom(zoom)
        self.hotspot_canvas.set_zoom(zoom)
        self.crop_canvas.zoom_control.set_percent(int(round(zoom * 100)))

    def _set_pan(self, pan: QPoint) -> None:
        self.crop_canvas.set_pan(pan)
        self.hotspot_canvas.set_pan(pan)

    def _error(self, title: str, error: Exception | str) -> None:
        QMessageBox.critical(self, title, str(error))

    def import_file(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, tr("dialog.open_image"), "", "Images (*.png *.gif *.jpg *.jpeg *.bmp)")
        if not filename:
            return
        try:
            self.document = ImageDocument.load(filename)
            self.frame_index = 0
            self.hotspots = [(0, 0)] * len(self.document.frames)
            self.cropped_frames = None
            self.crop_canvas.selection = None
            self.frame_slider.setRange(0, len(self.document.frames) - 1)
            self.frame_slider.setValue(0)
            self.show_frame()
            self.statusBar().showMessage(tr("status.loaded", name=Path(filename).name, n=len(self.document.frames)))
        except Exception as error:
            self._error(tr("error.open"), error)

    def show_frame(self) -> None:
        if not self.document:
            return
        source = self.document.frames[self.frame_index].image
        self.crop_canvas.set_image(source)
        self.frame_label.setText(f"FRAME {self.frame_index + 1} / {len(self.document.frames)}   •   {self.document.frames[self.frame_index].duration_ms} ms")
        preview = self.cropped_frames[self.frame_index] if self.cropped_frames else source
        hot = self.hotspots[self.frame_index]
        hot = (min(hot[0], preview.width - 1), min(hot[1], preview.height - 1))
        self.hotspots[self.frame_index] = hot
        self.hotspot_canvas.set_image(preview, hot)
        self.hotspot_label.setText(f"HOTSPOT X:{hot[0]}  Y:{hot[1]}")

    def set_frame(self, index: int) -> None:
        if self.document:
            self.frame_index = index
            self.show_frame()

    def next_frame(self) -> None:
        if not self.document:
            return
        index = (self.frame_index + 1) % len(self.document.frames)
        self.frame_slider.setValue(index)
        self.timer.start(self.document.frames[index].duration_ms)

    def toggle_play(self) -> None:
        if not self.document or len(self.document.frames) < 2:
            return
        if self.timer.isActive():
            self.timer.stop()
            self.play_button.setText(tr("btn.play"))
        else:
            self.timer.start(self.document.frames[self.frame_index].duration_ms)
            self.play_button.setText(tr("btn.pause"))

    def selection_changed(self, rect: tuple) -> None:
        self.selection_label.setText(f"{rect[0]}, {rect[1]} → {rect[2]}, {rect[3]}   ({rect[2]-rect[0]} × {rect[3]-rect[1]})")

    def apply_crop(self) -> None:
        if not self.document or not self.crop_canvas.selection:
            return
        try:
            rect = self.crop_canvas.selection
            self.cropped_frames = [crop_image(frame.image, rect) for frame in self.document.frames]
            self.hotspots = [(0, 0)] * len(self.document.frames)
            self.show_frame()
            self.statusBar().showMessage(
                tr("status.cropped", w=self.cropped_frames[0].width, h=self.cropped_frames[0].height)
            )
        except Exception as error:
            self._error(tr("error.crop"), error)

    def hotspot_changed(self, x: int, y: int) -> None:
        if self.document:
            self.hotspots = [(x, y)] * len(self.document.frames)
            self.hotspot_label.setText(f"HOTSPOT X:{x}  Y:{y}  // ALL FRAMES")
            self.statusBar().showMessage(tr("status.hotspot", x=x, y=y, n=len(self.document.frames)))

    def cursor_frames(self) -> list[CursorFrame]:
        if not self.document:
            raise ValueError(tr("error.no_image"))
        images = self.cropped_frames or [frame.image for frame in self.document.frames]
        result = []
        for index, image in enumerate(images):
            fitted = fit_cursor(image)
            hx = round(self.hotspots[index][0] * fitted.width / image.width)
            hy = round(self.hotspots[index][1] * fitted.height / image.height)
            result.append(CursorFrame(fitted, (hx, hy), self.document.frames[index].duration_ms))
        return result

    def export_cur_file(self) -> None:
        try:
            frame = self.cursor_frames()[self.frame_index]
            filename, _ = QFileDialog.getSaveFileName(self, "Export CUR", "cursor.cur", "Windows Cursor (*.cur)")
            if filename:
                export_cur(filename, frame)
                self.statusBar().showMessage(tr("status.exported", path=filename))
        except Exception as error:
            self._error(tr("error.export_cur"), error)

    def export_ani_file(self) -> None:
        try:
            frames = self.cursor_frames()
            filename, _ = QFileDialog.getSaveFileName(self, "Export ANI", "animated.ani", "Animated Cursor (*.ani)")
            if filename:
                export_ani(filename, frames)
                self.statusBar().showMessage(tr("status.exported", path=filename))
        except Exception as error:
            self._error(tr("error.export_ani"), error)

    def make_pack(self) -> None:
        dialog = CursorPackDialog(self, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        parent_dir = QFileDialog.getExistingDirectory(self, tr("dialog.pick_pack_dir"))
        if not parent_dir:
            return
        try:
            folder = export_cursorpack_folder(
                parent_dir,
                dialog.name_edit.text().strip(),
                dialog.assignments,
                dialog.build_files(),
            )
            QMessageBox.information(
                self,
                tr("dialog.pack_done"),
                tr("dialog.pack_done_body", folder=folder),
            )
            self.statusBar().showMessage(tr("status.packed", path=folder))
        except Exception as error:
            self._error(tr("error.pack"), error)
