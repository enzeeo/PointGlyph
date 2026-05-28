from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Bounds:
    width: float
    height: float
    depth: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return {"width": self.width, "height": self.height, "depth": self.depth}


def normalize_points_for_threejs(points: np.ndarray, width_units: float) -> tuple[np.ndarray, Bounds]:
    if width_units <= 0:
        raise ValueError("width_units must be greater than 0")

    numeric_points = np.asarray(points, dtype=float)
    min_xy = numeric_points.min(axis=0)
    max_xy = numeric_points.max(axis=0)
    span = max_xy - min_xy
    if span[0] == 0:
        raise ValueError("Cannot normalize points with zero width span")

    scale = width_units / span[0]
    center = (min_xy + max_xy) / 2.0
    centered = (numeric_points - center) * scale
    xyz = np.column_stack((centered[:, 0], -centered[:, 1], np.zeros(len(centered))))
    bounds = Bounds(width=float(width_units), height=float(span[1] * scale), depth=0.0)
    return xyz.astype(float), bounds


def generate_cloud_positions(
    particle_count: int,
    bounds: Bounds,
    cloud_radius: float,
    z_jitter: float,
    seed: int | None,
) -> np.ndarray:
    if particle_count < 1:
        raise ValueError("particle_count must be at least 1")
    if z_jitter < 0:
        raise ValueError("z_jitter must be greater than or equal to 0")

    rng = np.random.default_rng(seed)
    x = rng.normal(0.0, cloud_radius / 2.0, particle_count)
    y = rng.normal(0.0, cloud_radius / 2.0, particle_count)
    z = rng.uniform(-z_jitter, z_jitter, particle_count)
    return np.column_stack((x, y, z)).astype(float)
