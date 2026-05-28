import numpy as np
import pytest
from PIL import Image

from pointglyph.sampling import sample_text_points


def test_sample_text_points_is_seeded():
    mask = Image.new("L", (4, 4), 0)
    mask.putpixel((1, 1), 255)
    mask.putpixel((2, 2), 255)

    first = sample_text_points(mask, 8, seed=42)
    second = sample_text_points(mask, 8, seed=42)

    np.testing.assert_array_equal(first, second)


def test_sample_text_points_uses_only_filled_pixels():
    mask = Image.new("L", (3, 3), 0)
    mask.putpixel((2, 1), 255)

    points = sample_text_points(mask, 5, seed=1)

    assert points.shape == (5, 2)
    assert points.tolist() == [[2.0, 1.0]] * 5


def test_sample_text_points_rejects_invalid_particle_count():
    mask = Image.new("L", (1, 1), 255)

    with pytest.raises(ValueError, match="particle_count"):
        sample_text_points(mask, 0, seed=None)


def test_sample_text_points_rejects_empty_mask():
    mask = Image.new("L", (2, 2), 0)

    with pytest.raises(ValueError, match="empty"):
        sample_text_points(mask, 1, seed=None)
