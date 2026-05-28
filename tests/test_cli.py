import json

import numpy as np
import pytest
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
    points = 25
    output_dir = tmp_path / "export"

    exit_code = main(
        [
            "TEST",
            "--font",
            str(font_path),
            "--points",
            str(points),
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
    assert len(particles["attributes"]["startPositions"]) == points * 3
    assert len(particles["attributes"]["textPositions"]) == points * 3
    assert len(particles["attributes"]["endPositions"]) == points * 3


def test_cli_same_seed_creates_identical_particles(tmp_path, font_path):
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    shared_args = [
        "TEST",
        "--font",
        str(font_path),
        "--points",
        "25",
        "--seed",
        "42",
    ]

    assert main([*shared_args, "--output", str(first_dir)]) == 0
    assert main([*shared_args, "--output", str(second_dir)]) == 0

    assert (first_dir / "particles.json").read_text() == (second_dir / "particles.json").read_text()


@pytest.mark.parametrize(
    ("option", "value"),
    [
        ("--width-units", "0"),
        ("--z-jitter", "-1"),
        ("--cloud-radius", "-1"),
    ],
)
def test_cli_rejects_invalid_numeric_options(tmp_path, font_path, option, value):
    with pytest.raises(SystemExit) as exc_info:
        main(["TEST", "--font", str(font_path), "--output", str(tmp_path), option, value])

    assert exc_info.value.code == 2


def test_cli_rejects_multiple_words(tmp_path, font_path):
    with pytest.raises(SystemExit) as exc_info:
        main(["TWO WORDS", "--font", str(font_path), "--output", str(tmp_path)])

    assert exc_info.value.code == 2
