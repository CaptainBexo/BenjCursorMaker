from PIL import Image

from image_processor import ImageDocument, crop_image, snap_rect


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
