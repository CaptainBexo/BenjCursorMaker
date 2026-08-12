from PIL import Image

from image_processor import ImageDocument, crop_image, fit_cursor, snap_rect


def test_fit_cursor_pads_to_square():
    """Windows scales any cursor into a square box (squishing non-square ones),
    so fit_cursor must pad the canvas to a square with transparency."""
    img = Image.new("RGBA", (116, 252), (0, 0, 0, 0))
    img.putpixel((0, 0), (255, 0, 0, 255))
    out = fit_cursor(img)
    assert out.size == (252, 252), out.size
    # content pixel keeps its relative position (padding offset 68 on X)
    assert out.getpixel((68, 0)) == (255, 0, 0, 255)
    assert out.getpixel((0, 0)) == (0, 0, 0, 0)  # padding transparent


def test_fit_cursor_square_unchanged():
    img = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
    out = fit_cursor(img)
    assert out.size == (100, 100)
    assert out.getpixel((50, 50)) == (255, 0, 0, 255)


def test_fit_cursor_downscales_then_pads():
    img = Image.new("RGBA", (232, 504), (0, 0, 0, 0))
    img.putpixel((0, 0), (255, 0, 0, 255))
    out = fit_cursor(img)
    assert out.size == (256, 256), out.size
    # after 256/504 scale: content 118x256, pad offset (256-118)//2 = 69
    assert out.getpixel((69, 0)) == (255, 0, 0, 255)


def test_snap_rect_uses_nearest_grid_boundaries():
    assert snap_rect((7, 10, 41, 50), 16, (80, 80)) == (0, 16, 48, 48)


def test_crop_image_preserves_exact_pixel_colors():
    image = Image.new("RGBA", (4, 4))
    image.putpixel((2, 1), (12, 34, 56, 255))
    result = crop_image(image, (2, 1, 3, 2))
    assert result.size == (1, 1)
    assert result.getpixel((0, 0)) == (12, 34, 56, 255)


def test_png_document_has_one_rgba_frame(tmp_path):
    path = tmp_path / "pixel.png"
    Image.new("RGB", (3, 2), "red").save(path)
    document = ImageDocument.load(path)
    assert len(document.frames) == 1
    assert document.frames[0].image.mode == "RGBA"
    assert document.frames[0].duration_ms == 100
