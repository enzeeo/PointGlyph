from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


@dataclass(frozen=True)
class PixelBounds:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top


@dataclass(frozen=True)
class TextMask:
    mask: Image.Image
    bounds: PixelBounds


def render_text_mask(
    text: str,
    font_path: str | Path,
    *,
    font_size: int = 512,
    padding: int = 64,
) -> TextMask:
    font = ImageFont.truetype(str(font_path), font_size)
    probe = Image.new("L", (1, 1), 0)
    draw = ImageDraw.Draw(probe)
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    width = right - left
    height = bottom - top

    image = Image.new("L", (width + padding * 2, height + padding * 2), 0)
    draw = ImageDraw.Draw(image)
    draw.text((padding - left, padding - top), text, fill=255, font=font)

    bbox = image.getbbox()
    if bbox is None:
        raise ValueError("Rendered text mask is empty")

    return TextMask(mask=image, bounds=PixelBounds(*bbox))
