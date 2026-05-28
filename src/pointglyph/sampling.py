import numpy as np
from PIL import Image


def sample_text_points(mask: Image.Image, particle_count: int, seed: int | None) -> np.ndarray:
    if particle_count < 1:
        raise ValueError("particle_count must be at least 1")

    pixels = np.asarray(mask)
    ys, xs = np.nonzero(pixels > 0)
    if len(xs) == 0:
        raise ValueError("Cannot sample from an empty text mask")

    rng = np.random.default_rng(seed)
    indices = rng.choice(len(xs), size=particle_count, replace=len(xs) < particle_count)
    return np.column_stack((xs[indices], ys[indices])).astype(float)
