import json

import numpy as np
import pytest
from PIL import Image

from pointglyph.cli import main
from pointglyph.geometry import Bounds, normalize_points_for_threejs
from pointglyph.preview import export_preview_png, export_solid_preview_png
from pointglyph.text_mask import create_wordmark_source, render_text_mask


def test_render_text_mask_has_content(font_path):
    result = render_text_mask("TEST", font_path)

    assert result.mask.mode == "L"
    assert result.mask.getbbox() is not None
    assert result.bounds.width > 0
    assert result.bounds.height > 0


def test_render_text_mask_accepts_bold_font(bold_font_path):
    result = render_text_mask("TEST", bold_font_path)

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


def test_export_solid_preview_png_creates_aligned_black_texture(tmp_path, font_path):
    text_mask = render_text_mask("TEST", font_path)
    wordmark = create_wordmark_source(text_mask)
    _points, bounds = normalize_points_for_threejs(
        np.array([[0.0, 0.0], [wordmark.bounds.width, wordmark.bounds.height]]),
        width_units=10.0,
        source_bounds=wordmark.source_bounds,
    )
    solid_output = tmp_path / "solid_preview.png"

    metadata = export_solid_preview_png(solid_output, wordmark.mask, bounds)

    solid_image = Image.open(solid_output)
    expected_height = round(bounds.height * 1200 / bounds.width)
    assert solid_image.size == (1200, expected_height)
    assert solid_image.getbbox() is not None
    alpha_box = solid_image.getchannel("A").getbbox()
    assert metadata["contentBox"] == {
        "left": alpha_box[0],
        "top": alpha_box[1],
        "right": alpha_box[2],
        "bottom": alpha_box[3],
        "width": alpha_box[2] - alpha_box[0],
        "height": alpha_box[3] - alpha_box[1],
    }
    assert metadata["solidTexture"] == {
        "width": 1200,
        "height": expected_height,
        "padding": 0,
        "inset": [0, 0, 0, 0],
    }
    visible_pixels = [pixel for pixel in solid_image.getdata() if pixel[3] > 0]
    assert visible_pixels
    assert all(pixel[:3] == (0, 0, 0) for pixel in visible_pixels)


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
    assert len(particles["attributes"]["appearProgresses"]) == points
    assert particles["attributes"]["appearProgresses"].count(0.0) == 12
    assert solid_particles["particleCount"] == points * 4
    assert len(solid_particles["attributes"]["startPositions"]) == points * 4 * 3
    assert len(solid_particles["attributes"]["textPositions"]) == points * 4 * 3
    assert len(solid_particles["attributes"]["endPositions"]) == points * 4 * 3
    assert len(solid_particles["attributes"]["appearProgresses"]) == points * 4
    assert manifest["files"]["solidPreview"] == "solid_preview.png"
    assert manifest["files"]["solidParticles"] == "solid_particles.json"
    assert manifest["files"]["solidParticlePreview"] == "solid_particle_preview.png"
    assert manifest["variants"]["solid"]["particleCount"] == points * 4
    assert manifest["animation"]["solidText"]["texture"] == "solid_preview.png"
    assert manifest["animation"]["particleReveal"]["attribute"] == "appearProgresses"
    assert manifest["animation"]["solidText"]["planeSize"] == [
        manifest["bounds"]["width"],
        manifest["bounds"]["height"],
    ]
    assert manifest["animation"]["solidText"]["planeCenter"] == [0.0, 0.0, 0.0]
    preview_image = Image.open(output_dir / "preview.png")
    solid_particle_image = Image.open(output_dir / "solid_particle_preview.png")
    solid_image = Image.open(output_dir / "solid_preview.png")
    alpha_box = solid_image.getchannel("A").getbbox()
    assert solid_particle_image.size == preview_image.size
    assert manifest["alignment"]["solidTexture"] == {
        "width": solid_image.size[0],
        "height": solid_image.size[1],
        "padding": 0,
        "inset": [0, 0, 0, 0],
    }
    assert manifest["alignment"]["contentBox"] == {
        "left": alpha_box[0],
        "top": alpha_box[1],
        "right": alpha_box[2],
        "bottom": alpha_box[3],
        "width": alpha_box[2] - alpha_box[0],
        "height": alpha_box[3] - alpha_box[1],
    }
    assert manifest["alignment"]["worldToTexture"] == {
        "world": {
            "left": -manifest["bounds"]["width"] / 2.0,
            "right": manifest["bounds"]["width"] / 2.0,
            "top": manifest["bounds"]["height"] / 2.0,
            "bottom": -manifest["bounds"]["height"] / 2.0,
        },
        "texture": {
            "left": 0,
            "right": solid_image.size[0],
            "top": 0,
            "bottom": solid_image.size[1],
        },
    }


def test_cli_accepts_bold_font_and_records_manifest_font(tmp_path, bold_font_path):
    output_dir = tmp_path / "bold"

    exit_code = main(
        [
            "TEST",
            "--font",
            str(bold_font_path),
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
    manifest = json.loads((output_dir / "manifest.json").read_text())
    assert manifest["font"] == bold_font_path.name


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
