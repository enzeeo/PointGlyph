from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from pointglyph.geometry import Bounds
from pointglyph.text_mask import TextMask


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


def export_solid_preview_png(
    output_path: str | Path,
    text_mask: TextMask,
    bounds: Bounds,
    *,
    image_width: int = 1200,
    padding: int = 80,
) -> None:
    scale = (image_width - padding * 2) / bounds.width
    content_height = max(1, int(bounds.height * scale))
    image_height = content_height + padding * 2
    image = Image.new("RGBA", (image_width, image_height), (0, 0, 0, 0))

    cropped_mask = text_mask.mask.crop(
        (text_mask.bounds.left, text_mask.bounds.top, text_mask.bounds.right, text_mask.bounds.bottom)
    )
    resized_mask = cropped_mask.resize((image_width - padding * 2, content_height), Image.Resampling.LANCZOS)
    solid_text = Image.new("RGBA", resized_mask.size, (255, 255, 255, 255))
    image.paste(solid_text, (padding, padding), resized_mask)

    image.save(output_path)
