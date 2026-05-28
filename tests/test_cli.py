import json

import numpy as np
from PIL import Image

from pointglyph.cli import main
from pointglyph.geometry import Bounds
from pointglyph.preview import export_preview_png
from pointglyph.text_mask import render_text_mask


def test_render_text_mask_has_content(font_path):
    result = render_text_mask("TEST", font_path)

    assert result.mask.mode == "L"
    assert result.mask.getbbox() is not None
    assert result.bounds.width > 0
    assert result.bounds.height > 0


def test_export_preview_png_creates_image(tmp_path):
    output = tmp_path / "preview.png"
    points = np.array([[-1.0, -1.0, 0.0], [1.0, 1.0, 0.0], [0.0, 0.0, 0.0]])

    export_preview_png(output, points, Bounds(width=2.0, height=2.0))

    image = Image.open(output)
    assert image.size[0] > 0
    assert image.size[1] > 0


def test_cli_creates_required_files(tmp_path, font_path):
    output_dir = tmp_path / "export"

    exit_code = main(
        [
            "TEST",
            "--font",
            str(font_path),
            "--points",
            "25",
            "--output",
            str(output_dir),
            "--seed",
            "42",
        ]
    )

    assert exit_code == 0
    assert (output_dir / "manifest.json").exists()
    assert (output_dir / "particles.json").exists()
    assert (output_dir / "preview.png").exists()
    particles = json.loads((output_dir / "particles.json").read_text())
    assert len(particles["attributes"]["textPositions"]) == 25 * 3


def test_cli_rejects_multiple_words(tmp_path, font_path):
    exit_code = main(["TWO WORDS", "--font", str(font_path), "--output", str(tmp_path)])

    assert exit_code == 2
