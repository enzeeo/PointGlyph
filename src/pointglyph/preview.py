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


def export_solid_preview_png(
    output_path: str | Path,
    wordmark_mask: Image.Image,
    bounds: Bounds,
    *,
    image_width: int = 1200,
    padding: int = 80,
) -> dict[str, object]:
    scale = image_width / bounds.width
    image_height = max(1, round(bounds.height * scale))
    image = Image.new("RGBA", (image_width, image_height), (0, 0, 0, 0))

    resized_mask = wordmark_mask.resize(image.size, Image.Resampling.LANCZOS)
    solid_text = Image.new("RGBA", resized_mask.size, (0, 0, 0, 255))
    image.paste(solid_text, (0, 0), resized_mask)

    image.save(output_path)
    alpha_box = image.getchannel("A").getbbox()
    if alpha_box is None:
        raise ValueError("Solid text texture is empty")

    return {
        "contentBox": {
            "left": alpha_box[0],
            "top": alpha_box[1],
            "right": alpha_box[2],
            "bottom": alpha_box[3],
            "width": alpha_box[2] - alpha_box[0],
            "height": alpha_box[3] - alpha_box[1],
        },
        "solidTexture": {
            "width": image_width,
            "height": image_height,
            "padding": 0,
            "inset": [0, 0, 0, 0],
        },
    }
