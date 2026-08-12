"""Image loading and pixel-perfect processing for Benj Cursor Maker."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageSequence


@dataclass(slots=True)
class ImageFrame:
    image: Image.Image
    duration_ms: int = 100


@dataclass(slots=True)
class ImageDocument:
    path: Path
    frames: list[ImageFrame]

    @classmethod
    def load(cls, path: str | Path) -> "ImageDocument":
        source = Path(path)
        frames: list[ImageFrame] = []
        with Image.open(source) as opened:
            for raw in ImageSequence.Iterator(opened):
                duration = max(10, int(raw.info.get("duration", opened.info.get("duration", 100)) or 100))
                frames.append(ImageFrame(raw.convert("RGBA").copy(), duration))
        if not frames:
            raise ValueError("Image file contains no valid frames.")
        return cls(source, frames)


def normalize_rect(rect: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = rect
    return min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)


def snap_rect(
    rect: tuple[int, int, int, int], grid: int, bounds: tuple[int, int]
) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = normalize_rect(rect)
    if grid <= 1:
        return max(0, x1), max(0, y1), min(bounds[0], x2), min(bounds[1], y2)

    def snap(value: int) -> int:
        return int(value / grid + 0.5) * grid

    sx1, sy1 = snap(x1), snap(y1)
    sx2, sy2 = snap(x2), snap(y2)
    if sx2 == sx1:
        sx2 += grid
    if sy2 == sy1:
        sy2 += grid
    return max(0, sx1), max(0, sy1), min(bounds[0], sx2), min(bounds[1], sy2)


def crop_image(image: Image.Image, rect: tuple[int, int, int, int]) -> Image.Image:
    x1, y1, x2, y2 = normalize_rect(rect)
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(image.width, x2), min(image.height, y2)
    if x2 <= x1 or y2 <= y1:
        raise ValueError("Crop region must have width and height greater than 0.")
    return image.crop((x1, y1, x2, y2)).convert("RGBA")


def fit_cursor(image: Image.Image, max_size: int = 256) -> Image.Image:
    """Make an image a valid Windows cursor frame.

    Scales down to max_size (uniform, Nearest-Neighbor) and PADS the canvas
    to a SQUARE with transparency: Windows scales any cursor into a square
    box (SM_CXCURSOR x SM_CYCURSOR), which squishes non-square cursors.
    """
    rgba = image.convert("RGBA")
    side = max(rgba.width, rgba.height)
    if side > max_size:
        scale = max_size / side
        size = (max(1, int(rgba.width * scale)), max(1, int(rgba.height * scale)))
        rgba = rgba.resize(size, Image.Resampling.NEAREST)
    if rgba.width != rgba.height:
        side = max(rgba.width, rgba.height)
        canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        canvas.paste(rgba, ((side - rgba.width) // 2, (side - rgba.height) // 2))
        rgba = canvas
    return rgba
