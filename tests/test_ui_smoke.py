import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from ui import MainWindow, RETRO_STYLE, paint_canvas_background

import pytest


@pytest.fixture(autouse=True)
def _reset_lang():
    from i18n import set_lang

    set_lang("vi")
    yield


def test_theme_uses_reference_neon_green_palette_without_old_pink_accent():
    normalized = RETRO_STYLE.lower()
    assert "#47ff57" in normalized
    assert "#060713" in normalized
    assert "#ff4fd8" not in normalized


def test_canvas_background_is_flat_without_decorative_grid():
    from PyQt6.QtGui import QImage, QPainter

    image = QImage(42, 42, QImage.Format.Format_RGB32)
    painter = QPainter(image)
    paint_canvas_background(painter, image.rect())
    painter.end()
    colors = {image.pixelColor(x, y).name() for x in range(42) for y in range(42)}
    assert colors == {"#080b14"}


def test_main_window_starts_with_expected_tools():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    assert "CURSOR MAKER" in window.windowTitle()
    assert window.crop_canvas.minimumWidth() >= 420
    assert window.hotspot_canvas.minimumWidth() >= 300
    window.close()


def test_every_main_action_button_has_a_short_clear_tooltip():
    from PyQt6.QtWidgets import QPushButton

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    # tiếng Việt mặc định
    expected = {"MỞ ẢNH", "CẮT VÙNG", "XUẤT .CUR", "XUẤT .ANI", "GÓI CURSOR", "PHÁT", "VN"}
    buttons = {button.text(): button.toolTip() for button in window.findChildren(QPushButton)}
    assert expected <= buttons.keys(), buttons.keys()
    for name in expected:
        assert buttons[name].strip(), name
        assert len(buttons[name]) <= 180, name
    # tiếng Anh
    window.toggle_lang()
    expected_en = {"IMPORT", "APPLY CROP", "EXPORT .CUR", "EXPORT .ANI", "CURSORPACK", "PLAY", "EN"}
    buttons_en = {button.text(): button.toolTip() for button in window.findChildren(QPushButton)}
    assert expected_en <= buttons_en.keys(), buttons_en.keys()
    for name in expected_en:
        assert buttons_en[name].strip(), name
        assert len(buttons_en[name]) <= 180, name
    window.close()


def test_hotspot_click_applies_same_coordinates_to_every_gif_frame():
    from PIL import Image

    from image_processor import ImageDocument, ImageFrame

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.document = ImageDocument(
        None,
        [ImageFrame(Image.new("RGBA", (16, 16)), 100) for _ in range(3)],
    )
    window.hotspots = [(0, 0)] * 3
    window.frame_index = 1

    window.hotspot_changed(5, 2)

    assert window.hotspots == [(5, 2), (5, 2), (5, 2)]
    window.set_frame(2)
    assert window.hotspot_canvas.hotspot == (5, 2)
    window.close()


def test_playback_keeps_crop_selection_across_gif_frames():
    from PIL import Image

    from image_processor import ImageDocument, ImageFrame

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.document = ImageDocument(
        None,
        [ImageFrame(Image.new("RGBA", (64, 64)), 100) for _ in range(3)],
    )
    window.hotspots = [(0, 0)] * 3
    window.frame_slider.setRange(0, 2)
    window.frame_index = 0
    window.show_frame()
    window.crop_canvas.selection = (7, 9, 41, 52)

    window.next_frame()
    assert window.frame_index == 1
    assert window.crop_canvas.selection == (7, 9, 41, 52)

    window.next_frame()
    assert window.frame_index == 2
    assert window.crop_canvas.selection == (7, 9, 41, 52)
    window.close()


def test_pack_dialog_assigns_current_multi_frame_cursor_as_ani_without_export():
    from PIL import Image

    from exporter import build_ani
    from image_processor import ImageDocument, ImageFrame
    from ui import CursorPackDialog

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.document = ImageDocument(
        None,
        [ImageFrame(Image.new("RGBA", (37, 46)), 100) for _ in range(3)],
    )
    window.hotspots = [(5, 2)] * 3
    window.frame_slider.setRange(0, 2)
    window.frame_index = 0
    window.show_frame()

    pack = CursorPackDialog(window, window)
    pack.list.setCurrentRow(0)  # Normal Select -> Arrow
    pack.assign_current_cursor()

    assert pack.assignments["Arrow"].name == "Arrow.ani"
    assert pack.memory_cursors["Arrow"] == build_ani(window.cursor_frames())
    assert "Arrow.ani" in pack.list.item(0).text()
    assert "[TỪ EDITOR]" in pack.list.item(0).text()
    pack.close()
    window.close()


def test_pack_dialog_assigns_current_single_frame_cursor_as_cur():
    from PIL import Image

    from exporter import build_cur
    from image_processor import ImageDocument, ImageFrame
    from ui import CursorPackDialog

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.document = ImageDocument(
        None,
        [ImageFrame(Image.new("RGBA", (16, 16)), 100)],
    )
    window.hotspots = [(2, 2)]
    window.frame_slider.setRange(0, 0)
    window.frame_index = 0
    window.show_frame()

    pack = CursorPackDialog(window, window)
    pack.list.setCurrentRow(3)  # Busy -> Wait
    pack.assign_current_cursor()

    assert pack.assignments["Wait"].name == "Wait.cur"
    assert pack.memory_cursors["Wait"] == build_cur(window.cursor_frames()[0])
    pack.close()
    window.close()


def test_pack_dialog_clear_removes_memory_cursor():
    from PIL import Image

    from image_processor import ImageDocument, ImageFrame
    from ui import CursorPackDialog

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.document = ImageDocument(
        None,
        [ImageFrame(Image.new("RGBA", (16, 16)), 100)],
    )
    window.hotspots = [(1, 1)]
    window.frame_slider.setRange(0, 0)
    window.frame_index = 0
    window.show_frame()

    pack = CursorPackDialog(window, window)
    pack.list.setCurrentRow(3)
    pack.assign_current_cursor()
    assert "Wait" in pack.assignments and "Wait" in pack.memory_cursors

    pack.clear_file()
    assert "Wait" not in pack.assignments
    assert "Wait" not in pack.memory_cursors
    pack.close()
    window.close()


def test_pack_dialog_memory_cursor_lands_in_exported_pack(tmp_path):
    from PIL import Image

    from exporter import export_cursorpack_folder
    from image_processor import ImageDocument, ImageFrame
    from ui import CursorPackDialog

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.document = ImageDocument(
        None,
        [ImageFrame(Image.new("RGBA", (16, 16)), 100) for _ in range(2)],
    )
    window.hotspots = [(3, 3)] * 2
    window.frame_slider.setRange(0, 1)
    window.frame_index = 0
    window.show_frame()

    pack = CursorPackDialog(window, window)
    pack.list.setCurrentRow(1)  # Help Select -> Help
    pack.assign_current_cursor()

    target = export_cursorpack_folder(
        tmp_path, "Direct Pack", pack.assignments, pack.build_files()
    )
    assert target == tmp_path / "Direct Pack"
    assert (target / "Help.ani").read_bytes() == pack.memory_cursors["Help"]
    assert (target / "install.bat").exists()
    pack.close()
    window.close()


def test_hotspot_canvas_emits_hover_tip_following_mouse():
    from PIL import Image

    from PyQt6.QtCore import QEvent, QPointF, Qt
    from PyQt6.QtGui import QMouseEvent

    from ui import HotspotCanvas

    app = QApplication.instance() or QApplication([])
    canvas = HotspotCanvas()
    canvas.resize(400, 400)
    canvas.show()
    app.processEvents()
    canvas.set_image(Image.new("RGBA", (32, 32)))
    canvas._layout_image()
    assert canvas.hasMouseTracking()

    tips, lefts = [], []
    canvas.hoverTip.connect(lambda text, pos: tips.append((text, pos)))
    canvas.hoverLeft.connect(lambda: lefts.append(True))

    target = canvas._target
    local = QPointF(
        target.x() + 8 * canvas._scale + canvas._scale // 2,
        target.y() + 5 * canvas._scale + canvas._scale // 2,
    )
    ev = QMouseEvent(
        QEvent.Type.MouseMove,
        local,
        canvas.mapToGlobal(local.toPoint()).toPointF(),
        Qt.MouseButton.NoButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )
    canvas.mouseMoveEvent(ev)
    assert tips, "hoverTip not emitted on mouse move"
    text, pos = tips[-1]
    assert "X: 8" in text and "Y: 5" in text
    assert pos == canvas.mapToGlobal(local.toPoint())

    outside = QMouseEvent(
        QEvent.Type.MouseMove,
        QPointF(1, 1),
        canvas.mapToGlobal(QPointF(1, 1).toPoint()).toPointF(),
        Qt.MouseButton.NoButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )
    canvas.mouseMoveEvent(outside)
    assert lefts, "hoverLeft not emitted when mouse leaves the image"
    canvas.close()


def test_main_window_buttons_use_floating_tip_following_mouse():
    from PyQt6.QtCore import QEvent, QPointF, Qt
    from PyQt6.QtGui import QHoverEvent

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    app.processEvents()
    button = window._tip_widgets[0]
    assert button.toolTip()

    window._tip.hide_tip()
    enter = QHoverEvent(
        QEvent.Type.HoverEnter, QPointF(10, 10), QPointF(120, 140), QPointF(0, 0),
        Qt.KeyboardModifier.NoModifier,
    )
    window.eventFilter(button, enter)
    assert window._tip.isVisible()
    assert window._tip.text() == button.toolTip()

    move = QHoverEvent(
        QEvent.Type.HoverMove, QPointF(20, 20), QPointF(200, 220), QPointF(10, 10),
        Qt.KeyboardModifier.NoModifier,
    )
    window.eventFilter(button, move)
    assert window._tip.mapToGlobal(window._tip.rect().topLeft()).x() == 200 + 14
    assert window._tip.mapToGlobal(window._tip.rect().topLeft()).y() == 220 + 18

    leave = QHoverEvent(
        QEvent.Type.HoverLeave, QPointF(20, 20), QPointF(200, 220), QPointF(20, 20),
        Qt.KeyboardModifier.NoModifier,
    )
    window.eventFilter(button, leave)
    assert not window._tip.isVisible()
    window.close()


def test_action_buttons_swallow_native_tooltip_events():
    from PyQt6.QtCore import QEvent

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    button = window._tip_widgets[0]
    assert window.eventFilter(button, QEvent(QEvent.Type.ToolTip)) is True
    window.close()


def test_main_window_connects_canvas_hover_to_floating_tip():
    from PIL import Image

    from PyQt6.QtCore import QEvent, QPointF, Qt
    from PyQt6.QtGui import QMouseEvent

    from image_processor import ImageDocument, ImageFrame

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    app.processEvents()
    window.document = ImageDocument(None, [ImageFrame(Image.new("RGBA", (16, 16)), 100)])
    window.hotspots = [(2, 2)]
    window.frame_slider.setRange(0, 0)
    window.frame_index = 0
    window.show_frame()
    canvas = window.hotspot_canvas
    canvas._layout_image()
    target = canvas._target
    local = QPointF(
        target.x() + 3 * canvas._scale + canvas._scale // 2,
        target.y() + 4 * canvas._scale + canvas._scale // 2,
    )
    ev = QMouseEvent(
        QEvent.Type.MouseMove,
        local,
        canvas.mapToGlobal(local.toPoint()).toPointF(),
        Qt.MouseButton.NoButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )
    canvas.mouseMoveEvent(ev)
    assert window._tip.isVisible()
    assert "X: 3" in window._tip.text() and "Y: 4" in window._tip.text()
    window.close()


def test_hotspot_canvas_has_no_static_tooltip_conflict():
    from ui import HotspotCanvas

    app = QApplication.instance() or QApplication([])
    canvas = HotspotCanvas()
    assert canvas.toolTip() == ""
    canvas.close()

    window = MainWindow()
    assert window.hotspot_canvas.toolTip() == ""
    window.close()


def test_hotspot_canvas_shows_hint_tooltip_without_image():
    from PyQt6.QtCore import QEvent, QPointF, Qt
    from PyQt6.QtGui import QMouseEvent

    from ui import HotspotCanvas

    app = QApplication.instance() or QApplication([])
    canvas = HotspotCanvas()
    canvas.resize(400, 400)
    canvas.show()
    app.processEvents()
    tips = []
    canvas.hoverTip.connect(lambda text, pos: tips.append(text))
    ev = QMouseEvent(
        QEvent.Type.MouseMove,
        QPointF(100, 100),
        canvas.mapToGlobal(QPointF(100, 100).toPoint()).toPointF(),
        Qt.MouseButton.NoButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )
    canvas.mouseMoveEvent(ev)
    assert tips, "no hint tooltip emitted without image"
    assert "IMPORT" in tips[-1].upper(), tips[-1]
    canvas.close()


def test_transparency_pattern_matches_image_pixels():
    from ui import transparency_pattern

    app = QApplication.instance() or QApplication([])
    pattern = transparency_pattern(8).toImage()
    assert pattern.width() == 16 and pattern.height() == 16
    c00 = pattern.pixelColor(0, 0)
    assert c00 == pattern.pixelColor(7, 7), "ô bàn cờ phải đúng kích thước 1 pixel ảnh"
    assert c00 != pattern.pixelColor(8, 0), "2 pixel cạnh nhau phải khác màu"
    assert c00 != pattern.pixelColor(0, 8)
    assert pattern.pixelColor(8, 8) == pattern.pixelColor(15, 15)


def test_canvas_zoom_keeps_pixel_under_cursor():
    from PIL import Image

    from PyQt6.QtCore import QEvent, QPoint, QPointF, Qt
    from PyQt6.QtGui import QWheelEvent

    from ui import HotspotCanvas

    app = QApplication.instance() or QApplication([])
    canvas = HotspotCanvas()
    canvas.resize(400, 400)
    canvas.show()
    app.processEvents()
    canvas.set_image(Image.new("RGBA", (32, 32)))
    canvas._layout_image()
    assert canvas._scale == 11  # (400 - 24) // 32
    canvas.set_zoom(2.0)
    canvas._layout_image()
    assert canvas._scale == 22, canvas._scale

    canvas.set_zoom(1.0)
    canvas._layout_image()
    pos = QPointF(200, 200)
    u_before = (pos.x() - canvas._target.x()) / canvas._scale
    v_before = (pos.y() - canvas._target.y()) / canvas._scale
    wheel = QWheelEvent(
        pos,
        canvas.mapToGlobal(pos.toPoint()).toPointF(),
        QPoint(0, 0),
        QPoint(0, 120),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.ScrollUpdate,
        False,
    )
    canvas.wheelEvent(wheel)
    u_after = (pos.x() - canvas._target.x()) / canvas._scale
    v_after = (pos.y() - canvas._target.y()) / canvas._scale
    assert abs(u_after - u_before) < 0.5, (u_before, u_after)
    assert abs(v_after - v_before) < 0.5, (v_before, v_after)
    assert canvas._scale > 11
    canvas.close()


def test_hotspot_canvas_middle_drag_pans():
    from PIL import Image

    from PyQt6.QtCore import QEvent, QPointF, Qt
    from PyQt6.QtGui import QMouseEvent

    from ui import HotspotCanvas

    app = QApplication.instance() or QApplication([])
    canvas = HotspotCanvas()
    canvas.resize(400, 400)
    canvas.show()
    app.processEvents()
    canvas.set_image(Image.new("RGBA", (32, 32)))
    canvas.set_zoom(4.0)
    canvas._layout_image()
    start = canvas._target

    def ev_at(px, py, button, buttons, etype):
        return QMouseEvent(
            etype,
            QPointF(px, py),
            canvas.mapToGlobal(QPointF(px, py).toPoint()).toPointF(),
            button,
            buttons,
            Qt.KeyboardModifier.NoModifier,
        )

    canvas.mousePressEvent(ev_at(150, 150, Qt.MouseButton.MiddleButton, Qt.MouseButton.MiddleButton, QEvent.Type.MouseButtonPress))
    canvas.mouseMoveEvent(ev_at(170, 160, Qt.MouseButton.NoButton, Qt.MouseButton.MiddleButton, QEvent.Type.MouseMove))
    assert canvas._target.x() == start.x() + 20, (start.x(), canvas._target.x())
    assert canvas._target.y() == start.y() + 10
    canvas.mouseReleaseEvent(ev_at(170, 160, Qt.MouseButton.MiddleButton, Qt.MouseButton.NoButton, QEvent.Type.MouseButtonRelease))
    assert canvas._pan_drag is None
    canvas.close()


def test_crop_canvas_zoom_control_updates_both_canvases():
    from PIL import Image

    from image_processor import ImageDocument, ImageFrame

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    app.processEvents()
    window.document = ImageDocument(None, [ImageFrame(Image.new("RGBA", (16, 16)), 100)])
    window.hotspots = [(1, 1)]
    window.frame_slider.setRange(0, 0)
    window.frame_index = 0
    window.show_frame()
    control = window.crop_canvas.zoom_control
    assert control.label.text() == "100%"
    # thứ tự: [+] 100% [-]
    assert control.layout().itemAt(0).widget() is control.in_button
    assert control.layout().itemAt(1).widget() is control.label
    assert control.layout().itemAt(2).widget() is control.out_button
    # nằm ở góc dưới bên trái canvas crop
    assert control.parent() is window.crop_canvas
    assert control.x() == 8
    assert control.y() == window.crop_canvas.height() - control.height() - 8

    control.in_button.click()
    assert window._zoom == 1.5
    assert control.label.text() == "150%"
    assert window.crop_canvas._zoom == window.hotspot_canvas._zoom == 1.5

    control.out_button.click()
    control.out_button.click()
    assert window._zoom == 1.0
    assert control.label.text() == "100%"
    window.close()


def test_pack_dialog_preview_shows_assigned_cursor_on_hover():
    """Hover vào trạng thái đã gán: ẩn con trỏ hệ thống, hiện preview cursor đã gán, chặn tooltip."""
    from PIL import Image

    from PyQt6.QtCore import QEvent, QPointF, Qt
    from PyQt6.QtGui import QHoverEvent

    from image_processor import ImageDocument, ImageFrame
    from ui import CursorPackDialog

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.document = ImageDocument(None, [ImageFrame(Image.new("RGBA", (16, 16), (0, 0, 0, 255)), 100)])
    window.hotspots = [(3, 4)]
    window.frame_index = 0
    window.cropped_frames = None
    window.show_frame()
    dialog = CursorPackDialog(window, window)
    dialog.show()
    app.processEvents()
    dialog.list.setCurrentRow(1)  # Help
    dialog.assign_current_cursor()

    viewport = dialog.list.viewport()
    item_rect = dialog.list.visualItemRect(dialog.list.item(1))
    center = item_rect.center()
    enter = QHoverEvent(
        QEvent.Type.HoverEnter, QPointF(center), QPointF(300, 300), QPointF(0, 0),
        Qt.KeyboardModifier.NoModifier,
    )
    # trả True = chặn tooltip, preview hiển thị
    assert dialog.eventFilter(viewport, enter) is True
    assert dialog._preview.isVisible()
    assert not dialog._preview.pixmap().isNull()
    assert viewport.cursor().shape() == Qt.CursorShape.BlankCursor

    # di chuyển chuột -> preview bám theo
    move = QHoverEvent(
        QEvent.Type.HoverMove, QPointF(center.x() + 4, center.y() + 2), QPointF(320, 310), QPointF(center.x(), center.y()),
        Qt.KeyboardModifier.NoModifier,
    )
    assert dialog.eventFilter(viewport, move) is True
    assert dialog._preview.isVisible()
    dialog.close()
    window.close()


def test_pack_dialog_preview_hidden_for_unassigned_role():
    from PyQt6.QtCore import QEvent, QPointF, Qt
    from PyQt6.QtGui import QHoverEvent

    from ui import CursorPackDialog

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    dialog = CursorPackDialog(window, window)
    dialog.show()
    app.processEvents()

    viewport = dialog.list.viewport()
    item_rect = dialog.list.visualItemRect(dialog.list.item(0))  # chưa gán
    enter = QHoverEvent(
        QEvent.Type.HoverEnter, QPointF(item_rect.center()), QPointF(300, 300), QPointF(0, 0),
        Qt.KeyboardModifier.NoModifier,
    )
    # không preview -> False, tooltip vẫn chảy
    assert dialog.eventFilter(viewport, enter) is False
    assert not dialog._preview.isVisible()
    assert viewport.cursor().shape() != Qt.CursorShape.BlankCursor
    dialog.close()
    window.close()


def test_pack_dialog_preview_hides_on_leave():
    from PIL import Image

    from PyQt6.QtCore import QEvent, QPointF, Qt
    from PyQt6.QtGui import QHoverEvent

    from image_processor import ImageDocument, ImageFrame
    from ui import CursorPackDialog

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.document = ImageDocument(None, [ImageFrame(Image.new("RGBA", (16, 16), (0, 0, 0, 255)), 100)])
    window.hotspots = [(3, 4)]
    window.frame_index = 0
    window.cropped_frames = None
    window.show_frame()
    dialog = CursorPackDialog(window, window)
    dialog.show()
    app.processEvents()
    dialog.list.setCurrentRow(1)
    dialog.assign_current_cursor()

    viewport = dialog.list.viewport()
    item_rect = dialog.list.visualItemRect(dialog.list.item(1))
    enter = QHoverEvent(
        QEvent.Type.HoverEnter, QPointF(item_rect.center()), QPointF(300, 300), QPointF(0, 0),
        Qt.KeyboardModifier.NoModifier,
    )
    assert dialog.eventFilter(viewport, enter) is True
    assert dialog._preview.isVisible()

    leave = QHoverEvent(
        QEvent.Type.HoverLeave, QPointF(item_rect.center()), QPointF(300, 300), QPointF(item_rect.center()),
        Qt.KeyboardModifier.NoModifier,
    )
    dialog.eventFilter(viewport, leave)
    assert not dialog._preview.isVisible()
    assert viewport.cursor().shape() != Qt.CursorShape.BlankCursor
    dialog.close()
    window.close()


def test_pack_dialog_preview_turns_off_when_moving_to_unassigned():
    """Chuyển từ mục đã gán sang mục chưa gán -> preview tắt ngay."""
    from PIL import Image

    from PyQt6.QtCore import QEvent, QPointF, Qt
    from PyQt6.QtGui import QHoverEvent

    from image_processor import ImageDocument, ImageFrame
    from ui import CursorPackDialog

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.document = ImageDocument(None, [ImageFrame(Image.new("RGBA", (16, 16), (0, 0, 0, 255)), 100)])
    window.hotspots = [(3, 4)]
    window.frame_index = 0
    window.cropped_frames = None
    window.show_frame()
    dialog = CursorPackDialog(window, window)
    dialog.show()
    app.processEvents()
    dialog.list.setCurrentRow(1)
    dialog.assign_current_cursor()

    viewport = dialog.list.viewport()
    rect_help = dialog.list.visualItemRect(dialog.list.item(1))
    rect_other = dialog.list.visualItemRect(dialog.list.item(2))
    enter = QHoverEvent(
        QEvent.Type.HoverEnter, QPointF(rect_help.center()), QPointF(300, 300), QPointF(0, 0),
        Qt.KeyboardModifier.NoModifier,
    )
    assert dialog.eventFilter(viewport, enter) is True
    assert dialog._preview.isVisible()

    move = QHoverEvent(
        QEvent.Type.HoverMove, QPointF(rect_other.center()), QPointF(320, 320), QPointF(rect_help.center()),
        Qt.KeyboardModifier.NoModifier,
    )
    assert dialog.eventFilter(viewport, move) is False
    assert not dialog._preview.isVisible()
    assert viewport.cursor().shape() != Qt.CursorShape.BlankCursor
    dialog.close()
    window.close()


def test_language_toggle_button_top_right():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    app.processEvents()
    btn = window.lang_button
    # mặc định tiếng Việt -> nút hiện VN, nằm nửa bên phải cửa sổ
    assert btn.text() == "VN", btn.text()
    assert btn.x() > window.width() // 2, btn.x()
    assert btn.toolTip().strip()
    window.close()


def test_language_toggle_switches_all_texts():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    app.processEvents()

    # mặc định VI
    assert window.import_button.text() == "MỞ ẢNH"
    assert window.source_box.title() == "NGUỒN / CÁC FRAME GIF"
    assert window.play_button.text() == "PHÁT"
    assert "Mở PNG" in window.import_button.toolTip()

    window.toggle_lang()  # -> EN
    assert window.lang_button.text() == "EN"
    assert window.import_button.text() == "IMPORT"
    assert window.source_box.title() == "SOURCE / GIF FRAMES"
    assert window.hotspot_box.title() == "HOTSPOT // CLICK ONE PIXEL"
    assert "Open PNG" in window.import_button.toolTip()
    assert "Play or pause" in window.play_button.toolTip()
    assert window.crop_canvas.zoom_control.in_button.toolTip().startswith("Zoom in")

    window.toggle_lang()  # -> VI
    assert window.lang_button.text() == "VN"
    assert window.import_button.text() == "MỞ ẢNH"
    assert window.source_box.title() == "NGUỒN / CÁC FRAME GIF"
    window.close()


def test_dialog_follows_current_language():
    from PyQt6.QtWidgets import QPushButton

    from ui import CursorPackDialog

    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    # chuyển sang EN trước
    window.toggle_lang()
    dialog = CursorPackDialog(window, window)
    assert "— not assigned —" in dialog.list.item(0).text()
    assert any(b.text() == "ASSIGN CURRENT CURSOR" for b in dialog.findChildren(QPushButton))
    assert any(b.text() == "Apply" for b in dialog.findChildren(QPushButton))
    assert dialog.windowTitle() == "CURSORPACK BUILDER"
    dialog.close()

    # quay lại VI
    window.toggle_lang()
    dialog2 = CursorPackDialog(window, window)
    assert "— chưa gán —" in dialog2.list.item(0).text()
    assert any(b.text() == "GÁN CURSOR HIỆN TẠI" for b in dialog2.findChildren(QPushButton))
    assert any(b.text() == "ÁP DỤNG" for b in dialog2.findChildren(QPushButton))
    dialog2.close()
    window.close()


def test_pack_dialog_button_order_apply_save_cancel():
    from ui import CursorPackDialog

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.toggle_lang()  # sang EN để nút là Apply/Save/Cancel
    dialog = CursorPackDialog(window, window)
    buttons_row = dialog.layout().itemAt(4).layout()
    texts = [
        buttons_row.itemAt(i).widget().text()
        for i in range(buttons_row.count())
        if buttons_row.itemAt(i).widget() is not None
    ]
    assert texts == ["Apply", "Save", "Cancel"], texts
    dialog.close()
    window.close()


def test_pack_dialog_buttons_use_floating_tip_like_editor():
    from PyQt6.QtCore import QEvent, QPointF, Qt
    from PyQt6.QtGui import QHoverEvent

    from ui import CursorPackDialog

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.toggle_lang()  # sang EN để nút là Apply/Save/Cancel
    dialog = CursorPackDialog(window, window)
    dialog.show()
    app.processEvents()
    button = dialog._tip_widgets[0]
    tip = dialog._tip
    assert button.toolTip()

    # native tooltip bị nuốt
    assert dialog.eventFilter(button, QEvent(QEvent.Type.ToolTip)) is True

    tip.hide_tip()
    enter = QHoverEvent(
        QEvent.Type.HoverEnter, QPointF(5, 5), QPointF(300, 400), QPointF(0, 0),
        Qt.KeyboardModifier.NoModifier,
    )
    dialog.eventFilter(button, enter)
    assert tip.isVisible()
    assert tip.text() == button.toolTip()

    move = QHoverEvent(
        QEvent.Type.HoverMove, QPointF(10, 10), QPointF(320, 430), QPointF(5, 5),
        Qt.KeyboardModifier.NoModifier,
    )
    dialog.eventFilter(button, move)  # tooltip dài bị clamp màn hình — không kiểm tra vị trí tuyệt đối ở đây

    leave = QHoverEvent(
        QEvent.Type.HoverLeave, QPointF(10, 10), QPointF(320, 430), QPointF(10, 10),
        Qt.KeyboardModifier.NoModifier,
    )
    dialog.eventFilter(button, leave)
    assert not tip.isVisible()

    # tooltip ngắn (nút Cancel) thì vị trí không bị clamp, bám đúng chuột
    from PyQt6.QtWidgets import QPushButton

    cancel = [w for w in dialog._tip_widgets if isinstance(w, QPushButton) and w.text() == "Cancel"][0]
    tip.hide_tip()
    dialog.eventFilter(cancel, enter)
    assert tip.isVisible()
    dialog.eventFilter(cancel, move)
    assert tip.mapToGlobal(tip.rect().topLeft()).x() == 320 + 14
    dialog.close()
    window.close()


def test_pack_dialog_buttons_right_aligned():
    from ui import CursorPackDialog

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    app.processEvents()
    dialog = CursorPackDialog(window, window)
    dialog.show()
    app.processEvents()
    buttons_row = dialog.layout().itemAt(4).layout()
    widgets = [
        buttons_row.itemAt(i).widget()
        for i in range(buttons_row.count())
        if buttons_row.itemAt(i).widget() is not None
    ]
    assert all(w.x() > dialog.width() // 2 for w in widgets), [w.x() for w in widgets]
    assert widgets[0].x() < widgets[1].x() < widgets[2].x()
    dialog.close()
    window.close()


def test_pack_dialog_apply_assigns_current_cursor_directly():
    """Bấm Apply trực tiếp (không gán trước) với ảnh + role đã chọn -> gán thẳng + lưu tạm."""
    from PIL import Image

    from PyQt6.QtWidgets import QDialog

    from image_processor import ImageDocument, ImageFrame
    from ui import CursorPackDialog

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.document = ImageDocument(None, [ImageFrame(Image.new("RGBA", (16, 16)), 100)])
    window.hotspots = [(2, 2)]
    window.frame_slider.setRange(0, 0)
    window.frame_index = 0
    window.show_frame()

    dialog = CursorPackDialog(window, window)
    dialog.name_edit.setText("My Pack")
    dialog.list.setCurrentRow(1)  # Help
    dialog.apply_pack()
    assert "Help" in window.pack_assignments, "Apply phải gán thẳng cursor hiện tại"
    assert "Help" in window.pack_cursors
    assert window.pack_assignments["Help"].name == "Help.cur"
    assert window.pack_name == "My Pack"
    assert dialog.result() != QDialog.DialogCode.Accepted
    dialog.close()
    window.close()


def test_pack_dialog_save_assigns_current_cursor_directly():
    """Bấm Save trực tiếp với ảnh + role đã chọn -> tự gán thẳng rồi mới xuất."""
    from PIL import Image

    from PyQt6.QtWidgets import QDialog

    from image_processor import ImageDocument, ImageFrame
    from ui import CursorPackDialog

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.document = ImageDocument(None, [ImageFrame(Image.new("RGBA", (16, 16)), 100)])
    window.hotspots = [(2, 2)]
    window.frame_slider.setRange(0, 0)
    window.frame_index = 0
    window.show_frame()

    dialog = CursorPackDialog(window, window)
    dialog.name_edit.setText("My Pack")
    dialog.list.setCurrentRow(0)  # Arrow
    dialog.accept()
    assert dialog.result() == QDialog.DialogCode.Accepted
    assert "Arrow" in window.pack_assignments
    assert "Arrow" in window.pack_cursors
    dialog.close()
    window.close()


def test_pack_dialog_apply_persists_without_exporting():
    from PIL import Image

    from PyQt6.QtWidgets import QDialog

    from image_processor import ImageDocument, ImageFrame
    from ui import CursorPackDialog

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.document = ImageDocument(None, [ImageFrame(Image.new("RGBA", (16, 16)), 100)])
    window.hotspots = [(3, 3)]
    window.frame_slider.setRange(0, 0)
    window.frame_index = 0
    window.show_frame()

    dialog = CursorPackDialog(window, window)
    dialog.name_edit.setText("My Pack")
    dialog.list.setCurrentRow(1)  # Help
    dialog.assign_current_cursor()
    assert "Help" in dialog.assignments

    dialog.apply_pack()
    # đã lưu vào main window, không kích hoạt xuất (result != Accepted)
    assert window.pack_assignments.get("Help") == dialog.assignments["Help"]
    assert "Help" in window.pack_cursors
    assert window.pack_name == "My Pack"
    assert dialog.result() != QDialog.DialogCode.Accepted
    dialog.close()
    window.close()


def test_pack_dialog_reopen_restores_applied_state():
    from PIL import Image

    from image_processor import ImageDocument, ImageFrame
    from ui import CursorPackDialog

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.document = ImageDocument(None, [ImageFrame(Image.new("RGBA", (16, 16)), 100)])
    window.hotspots = [(3, 3)]
    window.frame_slider.setRange(0, 0)
    window.frame_index = 0
    window.show_frame()

    first = CursorPackDialog(window, window)
    first.name_edit.setText("My Pack")
    first.list.setCurrentRow(1)  # Help
    first.assign_current_cursor()
    first.apply_pack()
    first.close()

    second = CursorPackDialog(window, window)
    assert second.assignments.get("Help") == first.assignments["Help"]
    assert "Help" in second.memory_cursors
    assert second.name_edit.text() == "My Pack"
    assert "Help.cur" in second.list.item(1).text()
    second.close()
    window.close()


def test_pan_syncs_between_canvases():
    from PIL import Image

    from PyQt6.QtCore import QEvent, QPoint, QPointF, Qt
    from PyQt6.QtGui import QMouseEvent

    from image_processor import ImageDocument, ImageFrame

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    app.processEvents()
    window.document = ImageDocument(None, [ImageFrame(Image.new("RGBA", (16, 16)), 100)])
    window.hotspots = [(1, 1)]
    window.frame_slider.setRange(0, 0)
    window.frame_index = 0
    window.show_frame()
    crop, hotspot = window.crop_canvas, window.hotspot_canvas
    crop.set_zoom(4.0)
    hotspot.set_zoom(4.0)
    crop._layout_image()
    hotspot._layout_image()

    def ev_at(canvas, px, py, button, buttons, etype):
        p = QPointF(px, py)
        return QMouseEvent(etype, p, canvas.mapToGlobal(p.toPoint()).toPointF(), button, buttons, Qt.KeyboardModifier.NoModifier)

    # pan trên crop canvas -> hotspot phải đi theo
    before = hotspot._target
    crop.mousePressEvent(ev_at(crop, 100, 100, Qt.MouseButton.MiddleButton, Qt.MouseButton.MiddleButton, QEvent.Type.MouseButtonPress))
    crop.mouseMoveEvent(ev_at(crop, 120, 130, Qt.MouseButton.NoButton, Qt.MouseButton.MiddleButton, QEvent.Type.MouseMove))
    crop.mouseReleaseEvent(ev_at(crop, 120, 130, Qt.MouseButton.MiddleButton, Qt.MouseButton.NoButton, QEvent.Type.MouseButtonRelease))
    assert crop._pan == QPoint(20, 30), crop._pan
    assert hotspot._pan == QPoint(20, 30), hotspot._pan
    assert hotspot._target.x() == before.x() + 20, (before.x(), hotspot._target.x())
    assert hotspot._target.y() == before.y() + 30

    # pan ngược lại trên hotspot -> crop phải đi theo
    crop_before = crop._target
    hotspot.mousePressEvent(ev_at(hotspot, 100, 100, Qt.MouseButton.MiddleButton, Qt.MouseButton.MiddleButton, QEvent.Type.MouseButtonPress))
    hotspot.mouseMoveEvent(ev_at(hotspot, 110, 115, Qt.MouseButton.NoButton, Qt.MouseButton.MiddleButton, QEvent.Type.MouseMove))
    hotspot.mouseReleaseEvent(ev_at(hotspot, 110, 115, Qt.MouseButton.MiddleButton, Qt.MouseButton.NoButton, QEvent.Type.MouseButtonRelease))
    assert hotspot._pan == QPoint(30, 45), hotspot._pan
    assert crop._pan == QPoint(30, 45), crop._pan
    assert crop._target.x() == crop_before.x() + 10
    assert crop._target.y() == crop_before.y() + 15
    window.close()
