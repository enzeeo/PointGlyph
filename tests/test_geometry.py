import numpy as np
import pytest

from pointglyph.geometry import Bounds, generate_cloud_positions, normalize_points_for_threejs


def test_normalize_points_centers_and_flips_y():
    image_points = np.array([[0.0, 0.0], [100.0, 50.0]])

    points, bounds = normalize_points_for_threejs(image_points, width_units=10.0)

    assert points.shape == (2, 3)
    np.testing.assert_allclose(points[:, 0], [-5.0, 5.0])
    np.testing.assert_allclose(points[:, 1], [2.5, -2.5])
    np.testing.assert_allclose(points[:, 2], [0.0, 0.0])
    assert bounds == Bounds(width=10.0, height=5.0, depth=0.0)


def test_normalize_points_can_use_source_bounds():
    image_points = np.array([[25.0, 20.0], [75.0, 40.0]])

    points, bounds = normalize_points_for_threejs(
        image_points,
        width_units=10.0,
        source_bounds=(0.0, 0.0, 100.0, 50.0),
    )

    np.testing.assert_allclose(points[:, 0], [-2.5, 2.5])
    np.testing.assert_allclose(points[:, 1], [0.5, -1.5])
    assert bounds == Bounds(width=10.0, height=5.0, depth=0.0)


def test_generate_cloud_positions_is_seeded_and_jitters_z():
    bounds = Bounds(width=10.0, height=2.0, depth=0.0)

    first = generate_cloud_positions(5, bounds, cloud_radius=6.0, z_jitter=0.1, seed=7)
    second = generate_cloud_positions(5, bounds, cloud_radius=6.0, z_jitter=0.1, seed=7)

    np.testing.assert_array_equal(first, second)
    assert first.shape == (5, 3)
    assert np.max(np.abs(first[:, 2])) <= 0.1


def test_generate_cloud_positions_derives_radius_from_bounds():
    bounds = Bounds(width=10.0, height=2.0, depth=0.0)
    particle_count = 5
    z_jitter = 0.1
    seed = 7

    actual = generate_cloud_positions(
        particle_count,
        bounds,
        cloud_radius=None,
        z_jitter=z_jitter,
        seed=seed,
    )
    rng = np.random.default_rng(seed)
    radius_x = bounds.width * 0.75
    radius_y = max(bounds.height, bounds.width * 0.25)
    expected = np.column_stack(
        (
            rng.normal(0.0, radius_x / 2.0, particle_count),
            rng.normal(0.0, radius_y / 2.0, particle_count),
            rng.uniform(-z_jitter, z_jitter, particle_count),
        )
    )

    np.testing.assert_allclose(actual, expected)
    assert actual.shape == (particle_count, 3)


def test_normalize_points_rejects_invalid_width():
    image_points = np.array([[0.0, 0.0], [100.0, 50.0]])

    with pytest.raises(ValueError, match="width_units"):
        normalize_points_for_threejs(image_points, width_units=0.0)


def test_normalize_points_rejects_zero_width_span():
    image_points = np.array([[10.0, 0.0], [10.0, 50.0]])

    with pytest.raises(ValueError, match="zero width"):
        normalize_points_for_threejs(image_points, width_units=10.0)


def test_generate_cloud_positions_rejects_invalid_arguments():
    bounds = Bounds(width=10.0, height=2.0, depth=0.0)

    with pytest.raises(ValueError, match="particle_count"):
        generate_cloud_positions(0, bounds, cloud_radius=6.0, z_jitter=0.1, seed=7)

    with pytest.raises(ValueError, match="z_jitter"):
        generate_cloud_positions(5, bounds, cloud_radius=6.0, z_jitter=-0.1, seed=7)
