import json

import numpy as np

from pointglyph.exporters import export_manifest_json, export_particles_json
from pointglyph.geometry import Bounds


def test_export_particles_json_uses_flat_arrays(tmp_path):
    output = tmp_path / "particles.json"
    start_positions = np.array([[0.0, 1.0, 2.0], [3.0, 4.0, 5.0]])
    text_positions = np.array([[1.0, 2.0, 0.0], [3.0, 4.0, 0.0]])
    end_positions = np.array([[6.0, 7.0, 8.0], [9.0, 10.0, 11.0]])
    appear_progresses = np.array([0.0, 0.25])

    export_particles_json(
        output,
        text="HI",
        bounds=Bounds(width=10.0, height=2.0),
        start_positions=start_positions,
        text_positions=text_positions,
        end_positions=end_positions,
        appear_progresses=appear_progresses,
    )

    raw = output.read_text()
    data = json.loads(raw)

    assert "\n" not in raw
    assert data["version"] == 1
    assert data["text"] == "HI"
    assert data["particleCount"] == 2
    assert data["coordinateSystem"] == "threejs"
    assert data["units"] == "normalized"
    assert data["bounds"] == {"width": 10.0, "height": 2.0, "depth": 0.0}
    assert data["attributes"]["startPositions"] == [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
    assert data["attributes"]["textPositions"] == [1.0, 2.0, 0.0, 3.0, 4.0, 0.0]
    assert data["attributes"]["endPositions"] == [6.0, 7.0, 8.0, 9.0, 10.0, 11.0]
    assert data["attributes"]["appearProgresses"] == [0.0, 0.25]
    assert "sizes" not in data["attributes"]
    assert "colors" not in data["attributes"]


def test_export_manifest_json_omits_glb_and_includes_defaults(tmp_path):
    output = tmp_path / "manifest.json"

    export_manifest_json(
        output,
        name="hi",
        text="HI",
        font_name="Inter-Bold.ttf",
        particle_count=2,
        bounds=Bounds(width=10.0, height=2.0),
        default_particle_size=0.035,
        default_color=(1.0, 0.9, 0.8),
    )

    raw = output.read_text()
    data = json.loads(raw)

    assert "\n" in raw
    assert data["version"] == 1
    assert data["name"] == "hi"
    assert data["text"] == "HI"
    assert data["font"] == "Inter-Bold.ttf"
    assert data["particleCount"] == 2
    assert data["defaultParticleSize"] == 0.035
    assert data["defaultColor"] == [1.0, 0.9, 0.8]
    assert data["bounds"] == {"width": 10.0, "height": 2.0, "depth": 0.0}
    assert data["files"] == {
        "particles": "particles.json",
        "preview": "preview.png",
        "solidPreview": "solid_preview.png",
        "solidParticles": "solid_particles.json",
        "solidParticlePreview": "solid_particle_preview.png",
    }
    assert data["variants"] == {
        "default": {
            "particles": "particles.json",
            "preview": "preview.png",
            "particleCount": 2,
        },
        "solid": {
            "particles": "solid_particles.json",
            "preview": "solid_particle_preview.png",
            "solidPreview": "solid_preview.png",
            "particleCount": 8,
            "recommendedForActualSolidText": False,
        },
    }
    assert data["animation"]["particleReveal"]["attribute"] == "appearProgresses"
    assert data["animation"]["particleReveal"]["initialVisibleFraction"] == 0.5
    assert data["animation"]["solidText"]["texture"] == "solid_preview.png"
    assert data["animation"]["solidText"]["recommendedRenderMode"] == "TexturePlane"
    assert data["recommendedThreeJs"]["solidRenderMode"] == "TexturePlane"
    assert "text_mesh.glb" not in raw
    assert "recommendedThreeJs" in data
