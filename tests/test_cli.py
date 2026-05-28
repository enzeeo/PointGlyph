import json

import numpy as np
import pytest
from PIL import Image

from pointglyph.cli import main
from pointglyph.geometry import Bounds
from pointglyph.preview import export_preview_png, export_solid_preview_png
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


def test_export_solid_preview_png_matches_particle_preview_canvas(tmp_path, font_path):
    text_mask = render_text_mask("TEST", font_path)
    bounds = Bounds(width=10.0, height=2.0)
    particle_output = tmp_path / "preview.png"
    solid_output = tmp_path / "solid_preview.png"

    export_preview_png(particle_output, np.array([[-5.0, -1.0, 0.0], [5.0, 1.0, 0.0]]), bounds)
    export_solid_preview_png(solid_output, text_mask, bounds)

    particle_image = Image.open(particle_output)
    solid_image = Image.open(solid_output)
    assert solid_image.size == particle_image.size
    assert solid_image.getbbox() is not None


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
    assert (output_dir / "solid_preview.png").exists()
    assert (output_dir / "solid_particles.json").exists()
    assert (output_dir / "solid_particle_preview.png").exists()
    particles = json.loads((output_dir / "particles.json").read_text())
    solid_particles = json.loads((output_dir / "solid_particles.json").read_text())
    manifest = json.loads((output_dir / "manifest.json").read_text())
    assert len(particles["attributes"]["startPositions"]) == points * 3
    assert len(particles["attributes"]["textPositions"]) == points * 3
    assert len(particles["attributes"]["endPositions"]) == points * 3
    assert solid_particles["particleCount"] == points * 4
    assert len(solid_particles["attributes"]["startPositions"]) == points * 4 * 3
    assert len(solid_particles["attributes"]["textPositions"]) == points * 4 * 3
    assert len(solid_particles["attributes"]["endPositions"]) == points * 4 * 3
    assert manifest["files"]["solidPreview"] == "solid_preview.png"
    assert manifest["files"]["solidParticles"] == "solid_particles.json"
    assert manifest["files"]["solidParticlePreview"] == "solid_particle_preview.png"
    assert manifest["variants"]["solid"]["particleCount"] == points * 4
    preview_image = Image.open(output_dir / "preview.png")
    solid_particle_image = Image.open(output_dir / "solid_particle_preview.png")
    solid_image = Image.open(output_dir / "solid_preview.png")
    assert solid_particle_image.size == preview_image.size
    assert solid_image.size == preview_image.size


def test_cli_accepts_preview_flag_and_creates_preview(tmp_path, font_path):
    output_dir = tmp_path / "export"

    exit_code = main(
        [
            "TEST",
            "--font",
            str(font_path),
            "--output",
            str(output_dir),
            "--points",
            "25",
            "--preview",
        ]
    )

    assert exit_code == 0
    assert (output_dir / "preview.png").exists()


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
    assert (first_dir / "solid_particles.json").read_text() == (second_dir / "solid_particles.json").read_text()


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
