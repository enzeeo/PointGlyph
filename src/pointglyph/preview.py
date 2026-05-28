from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from pointglyph.geometry import Bounds


def export_preview_png(
    output_path: str | Path,
    text_positions: np.ndarray,
    bounds: Bounds,
    *,
    image_width: int = 1200,
    padding: int = 80,
) -> None:
    scale = (image_width - padding * 2) / bounds.width
    image_height = max(1, int(bounds.height * scale) + padding * 2)
    image = Image.new("RGB", (image_width, image_height), "black")
    draw = ImageDraw.Draw(image)
    center_x = image_width / 2.0
    center_y = image_height / 2.0
    radius = max(1.0, image_width / 600.0)

    for x, y, _z in text_positions:
        px = center_x + x * scale
        py = center_y - y * scale
        draw.ellipse((px - radius, py - radius, px + radius, py + radius), fill="white")

    image.save(output_path)
