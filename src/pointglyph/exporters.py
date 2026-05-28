import json
from pathlib import Path

import numpy as np

from pointglyph.geometry import Bounds


def _flat(values: np.ndarray) -> list[float]:
    return [float(value) for value in values.reshape(-1)]


def export_particles_json(
    output_path: str | Path,
    *,
    text: str,
    bounds: Bounds,
    start_positions: np.ndarray,
    text_positions: np.ndarray,
    end_positions: np.ndarray,
    appear_progresses: np.ndarray,
) -> None:
    data = {
        "version": 1,
        "text": text,
        "particleCount": len(text_positions),
        "coordinateSystem": "threejs",
        "units": "normalized",
        "bounds": bounds.to_dict(),
        "attributes": {
            "startPositions": _flat(start_positions),
            "textPositions": _flat(text_positions),
            "endPositions": _flat(end_positions),
            "appearProgresses": _flat(appear_progresses),
        },
    }
    Path(output_path).write_text(json.dumps(data, separators=(",", ":")))


def export_manifest_json(
    output_path: str | Path,
    *,
    name: str,
    text: str,
    font_name: str,
    particle_count: int,
    bounds: Bounds,
    default_particle_size: float,
    default_color: tuple[float, float, float],
) -> None:
    data = {
        "version": 1,
        "name": name,
        "text": text,
        "font": font_name,
        "particleCount": particle_count,
        "defaultParticleSize": default_particle_size,
        "defaultColor": [float(channel) for channel in default_color],
        "bounds": bounds.to_dict(),
        "files": {
            "particles": "particles.json",
            "preview": "preview.png",
            "solidPreview": "solid_preview.png",
            "solidParticles": "solid_particles.json",
            "solidParticlePreview": "solid_particle_preview.png",
        },
        "variants": {
            "default": {
                "particles": "particles.json",
                "preview": "preview.png",
                "particleCount": particle_count,
            },
            "solid": {
                "particles": "solid_particles.json",
                "preview": "solid_particle_preview.png",
                "solidPreview": "solid_preview.png",
                "particleCount": particle_count * 4,
                "recommendedForActualSolidText": False,
            },
        },
        "animation": {
            "particleReveal": {
                "attribute": "appearProgresses",
                "initialVisibleFraction": 0.5,
                "delayedProgressRange": [0.08, 0.75],
                "meaning": "Hide or fade each particle until global progress reaches its appearProgress.",
            },
            "solidText": {
                "texture": "solid_preview.png",
                "recommendedRenderMode": "TexturePlane",
                "fadeInAfterParticleReveal": True,
            },
        },
        "recommendedThreeJs": {
            "renderMode": "BufferGeometryPoints",
            "material": "ShaderMaterial or PointsMaterial",
            "solidRenderMode": "TexturePlane",
            "transparent": True,
            "depthWrite": False,
        },
    }
    Path(output_path).write_text(json.dumps(data, indent=2))
