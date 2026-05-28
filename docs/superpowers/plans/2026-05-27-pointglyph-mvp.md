# PointGlyph MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a small Python CLI package that converts one word plus a font into `manifest.json`, `particles.json`, and `preview.png` for Three.js particle text.

**Architecture:** The package is a linear asset pipeline: render a Pillow text mask, sample filled pixels with NumPy, normalize points into Three.js coordinates, generate deterministic cloud states, export compact JSON, and render a static preview. Each module has one responsibility so future GLB, edge sampling, or JS helper work can be added without changing the v1 contract.

**Tech Stack:** Python 3.11+, Pillow, NumPy, pytest, setuptools via `pyproject.toml`.

---

## Source Spec

Implement the approved spec at `docs/superpowers/specs/2026-05-27-pointglyph-mvp-design.md`.

Do not implement a website, viewer, JavaScript helper, or GLB export.

## File Structure

- Create: `pyproject.toml` for package metadata, dependencies, console script, and pytest config.
- Modify: `README.md` with install, CLI, schema, and Three.js snippet.
- Create: `src/pointglyph/__init__.py` for package version export.
- Create: `src/pointglyph/cli.py` for argument parsing, validation, and pipeline orchestration.
- Create: `src/pointglyph/text_mask.py` for font loading and text mask rendering.
- Create: `src/pointglyph/sampling.py` for deterministic mask-pixel sampling.
- Create: `src/pointglyph/geometry.py` for normalization, bounds, and cloud generation.
- Create: `src/pointglyph/exporters.py` for `particles.json` and `manifest.json`.
- Create: `src/pointglyph/preview.py` for static preview generation.
- Create: `tests/conftest.py` for locating a usable system font.
- Create: `tests/test_sampling.py` for deterministic sampling.
- Create: `tests/test_geometry.py` for coordinate conversion and cloud rules.
- Create: `tests/test_exporters.py` for compact JSON schema.
- Create: `tests/test_cli.py` for end-to-end CLI output.

---

### Task 1: Package Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `src/pointglyph/__init__.py`

- [ ] **Step 1: Create packaging config**

Add `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "pointglyph"
version = "0.1.0"
description = "Convert text into Three.js-ready particle glyph assets."
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
  "numpy>=1.26",
  "Pillow>=10.0",
]

[project.scripts]
pointglyph = "pointglyph.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

- [ ] **Step 2: Create package init**

Add `src/pointglyph/__init__.py`:

```python
"""PointGlyph converts text into Three.js-ready particle glyph assets."""

__version__ = "0.1.0"
```

- [ ] **Step 3: Verify package metadata**

Run: `python3 -m pip install -e .`

Expected: editable install succeeds and exposes a `pointglyph` console command.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml src/pointglyph/__init__.py
git commit -m "chore: add Python package skeleton"
```

---

### Task 2: Text Mask Rendering

**Files:**
- Create: `src/pointglyph/text_mask.py`
- Create: `tests/conftest.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write font fixture helper**

Add `tests/conftest.py`:

```python
from pathlib import Path

import pytest


FONT_CANDIDATES = [
    Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    Path("/Library/Fonts/Arial.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
]


@pytest.fixture(scope="session")
def font_path() -> Path:
    for candidate in FONT_CANDIDATES:
        if candidate.exists():
            return candidate
    pytest.skip("No supported test font found on this system")
```

- [ ] **Step 2: Write failing text mask test**

Add this to `tests/test_cli.py`:

```python
from pointglyph.text_mask import render_text_mask


def test_render_text_mask_has_content(font_path):
    result = render_text_mask("TEST", font_path)

    assert result.mask.mode == "L"
    assert result.mask.getbbox() is not None
    assert result.bounds.width > 0
    assert result.bounds.height > 0
```

- [ ] **Step 3: Run failing test**

Run: `python3 -m pytest tests/test_cli.py::test_render_text_mask_has_content -q`

Expected: FAIL because `pointglyph.text_mask` does not exist.

- [ ] **Step 4: Implement text mask module**

Add `src/pointglyph/text_mask.py`:

```python
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


@dataclass(frozen=True)
class PixelBounds:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top


@dataclass(frozen=True)
class TextMask:
    mask: Image.Image
    bounds: PixelBounds


def render_text_mask(
    text: str,
    font_path: str | Path,
    *,
    font_size: int = 512,
    padding: int = 64,
) -> TextMask:
    font = ImageFont.truetype(str(font_path), font_size)
    probe = Image.new("L", (1, 1), 0)
    draw = ImageDraw.Draw(probe)
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    width = right - left
    height = bottom - top
    image = Image.new("L", (width + padding * 2, height + padding * 2), 0)
    draw = ImageDraw.Draw(image)
    draw.text((padding - left, padding - top), text, fill=255, font=font)
    bbox = image.getbbox()
    if bbox is None:
        raise ValueError("Rendered text mask is empty")
    return TextMask(mask=image, bounds=PixelBounds(*bbox))
```

- [ ] **Step 5: Run test**

Run: `python3 -m pytest tests/test_cli.py::test_render_text_mask_has_content -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/pointglyph/text_mask.py tests/conftest.py tests/test_cli.py
git commit -m "feat: render text masks"
```

---

### Task 3: Sampling

**Files:**
- Create: `src/pointglyph/sampling.py`
- Create: `tests/test_sampling.py`

- [ ] **Step 1: Write failing sampling tests**

Add `tests/test_sampling.py`:

```python
import numpy as np
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
```

- [ ] **Step 2: Run failing tests**

Run: `python3 -m pytest tests/test_sampling.py -q`

Expected: FAIL because `pointglyph.sampling` does not exist.

- [ ] **Step 3: Implement sampling**

Add `src/pointglyph/sampling.py`:

```python
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
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_sampling.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/pointglyph/sampling.py tests/test_sampling.py
git commit -m "feat: sample text mask points"
```

---

### Task 4: Geometry and Clouds

**Files:**
- Create: `src/pointglyph/geometry.py`
- Create: `tests/test_geometry.py`

- [ ] **Step 1: Write failing geometry tests**

Add `tests/test_geometry.py`:

```python
import numpy as np

from pointglyph.geometry import Bounds, generate_cloud_positions, normalize_points_for_threejs


def test_normalize_points_centers_and_flips_y():
    image_points = np.array([[0.0, 0.0], [100.0, 50.0]])

    points, bounds = normalize_points_for_threejs(image_points, width_units=10.0)

    assert points.shape == (2, 3)
    np.testing.assert_allclose(points[:, 0], [-5.0, 5.0])
    np.testing.assert_allclose(points[:, 1], [2.5, -2.5])
    np.testing.assert_allclose(points[:, 2], [0.0, 0.0])
    assert bounds == Bounds(width=10.0, height=5.0, depth=0.0)


def test_generate_cloud_positions_is_seeded_and_jitters_z():
    bounds = Bounds(width=10.0, height=2.0, depth=0.0)

    first = generate_cloud_positions(5, bounds, cloud_radius=6.0, z_jitter=0.1, seed=7)
    second = generate_cloud_positions(5, bounds, cloud_radius=6.0, z_jitter=0.1, seed=7)

    np.testing.assert_array_equal(first, second)
    assert first.shape == (5, 3)
    assert np.max(np.abs(first[:, 2])) <= 0.1
```

- [ ] **Step 2: Run failing tests**

Run: `python3 -m pytest tests/test_geometry.py -q`

Expected: FAIL because `pointglyph.geometry` does not exist.

- [ ] **Step 3: Implement geometry**

Add `src/pointglyph/geometry.py`:

```python
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
    min_xy = points.min(axis=0)
    max_xy = points.max(axis=0)
    span = max_xy - min_xy
    if span[0] == 0:
        raise ValueError("Cannot normalize text points with zero width")

    scale = width_units / span[0]
    centered = (points - ((min_xy + max_xy) / 2.0)) * scale
    xyz = np.column_stack((centered[:, 0], -centered[:, 1], np.zeros(len(points))))
    bounds = Bounds(width=float(width_units), height=float(span[1] * scale), depth=0.0)
    return xyz.astype(float), bounds


def generate_cloud_positions(
    particle_count: int,
    bounds: Bounds,
    cloud_radius: float | None,
    z_jitter: float,
    seed: int | None,
) -> np.ndarray:
    if particle_count < 1:
        raise ValueError("particle_count must be at least 1")
    if z_jitter < 0:
        raise ValueError("z_jitter must be greater than or equal to 0")

    rng = np.random.default_rng(seed)
    radius_x = cloud_radius if cloud_radius is not None else bounds.width * 0.75
    radius_y = cloud_radius * 0.45 if cloud_radius is not None else max(bounds.height, bounds.width * 0.25)
    x = rng.normal(0.0, radius_x / 2.0, particle_count)
    y = rng.normal(0.0, radius_y / 2.0, particle_count)
    z = rng.uniform(-z_jitter, z_jitter, particle_count)
    return np.column_stack((x, y, z)).astype(float)
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_geometry.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/pointglyph/geometry.py tests/test_geometry.py
git commit -m "feat: normalize particle geometry"
```

---

### Task 5: JSON Exporters

**Files:**
- Create: `src/pointglyph/exporters.py`
- Create: `tests/test_exporters.py`

- [ ] **Step 1: Write failing exporter tests**

Add `tests/test_exporters.py`:

```python
import json
import numpy as np

from pointglyph.exporters import export_manifest_json, export_particles_json
from pointglyph.geometry import Bounds


def test_export_particles_json_uses_flat_arrays(tmp_path):
    output = tmp_path / "particles.json"
    positions = np.array([[1.0, 2.0, 0.0], [3.0, 4.0, 0.0]])

    export_particles_json(
        output,
        text="HI",
        bounds=Bounds(width=10.0, height=2.0),
        start_positions=positions,
        text_positions=positions,
        end_positions=positions,
    )

    data = json.loads(output.read_text())
    assert data["particleCount"] == 2
    assert data["attributes"]["textPositions"] == [1.0, 2.0, 0.0, 3.0, 4.0, 0.0]
    assert "sizes" not in data["attributes"]
    assert "colors" not in data["attributes"]


def test_export_manifest_json_omits_glb(tmp_path):
    output = tmp_path / "manifest.json"

    export_manifest_json(
        output,
        name="hi",
        text="HI",
        font_name="Inter-Bold.ttf",
        particle_count=2,
        bounds=Bounds(width=10.0, height=2.0),
        default_particle_size=0.035,
        default_color=(1.0, 1.0, 1.0),
    )

    data = json.loads(output.read_text())
    assert data["files"] == {"particles": "particles.json", "preview": "preview.png"}
    assert data["defaultColor"] == [1.0, 1.0, 1.0]
```

- [ ] **Step 2: Run failing tests**

Run: `python3 -m pytest tests/test_exporters.py -q`

Expected: FAIL because `pointglyph.exporters` does not exist.

- [ ] **Step 3: Implement exporters**

Add `src/pointglyph/exporters.py`:

```python
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
) -> None:
    particle_count = len(text_positions)
    data = {
        "version": 1,
        "text": text,
        "particleCount": particle_count,
        "coordinateSystem": "threejs",
        "units": "normalized",
        "bounds": bounds.to_dict(),
        "attributes": {
            "startPositions": _flat(start_positions),
            "textPositions": _flat(text_positions),
            "endPositions": _flat(end_positions),
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
        "files": {"particles": "particles.json", "preview": "preview.png"},
        "recommendedThreeJs": {
            "renderMode": "BufferGeometryPoints",
            "material": "ShaderMaterial or PointsMaterial",
            "transparent": True,
            "depthWrite": False,
        },
    }
    Path(output_path).write_text(json.dumps(data, indent=2))
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_exporters.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/pointglyph/exporters.py tests/test_exporters.py
git commit -m "feat: export particle JSON"
```

---

### Task 6: Preview Rendering

**Files:**
- Create: `src/pointglyph/preview.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write failing preview test**

Add this to `tests/test_cli.py`:

```python
import numpy as np
from PIL import Image

from pointglyph.geometry import Bounds
from pointglyph.preview import export_preview_png


def test_export_preview_png_creates_image(tmp_path):
    output = tmp_path / "preview.png"
    points = np.array([[-1.0, -1.0, 0.0], [1.0, 1.0, 0.0], [0.0, 0.0, 0.0]])

    export_preview_png(output, points, Bounds(width=2.0, height=2.0))

    image = Image.open(output)
    assert image.size[0] > 0
    assert image.size[1] > 0
```

- [ ] **Step 2: Run failing test**

Run: `python3 -m pytest tests/test_cli.py::test_export_preview_png_creates_image -q`

Expected: FAIL because `pointglyph.preview` does not exist.

- [ ] **Step 3: Implement preview**

Add `src/pointglyph/preview.py`:

```python
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from pointglyph.geometry import Bounds


def export_preview_png(
    output_path: str | Path,
    text_positions: np.ndarray,
    bounds: Bounds,
    *,
    image_width: int = 1200,
    padding: int = 80,
) -> None:
    scale = (image_width - padding * 2) / bounds.width
    image_height = max(1, int(bounds.height * scale) + padding * 2)
    image = Image.new("RGB", (image_width, image_height), "black")
    draw = ImageDraw.Draw(image)
    center_x = image_width / 2.0
    center_y = image_height / 2.0
    radius = max(1.0, image_width / 600.0)

    for x, y, _z in text_positions:
        px = center_x + x * scale
        py = center_y - y * scale
        draw.ellipse((px - radius, py - radius, px + radius, py + radius), fill="white")

    image.save(output_path)
```

- [ ] **Step 4: Run test**

Run: `python3 -m pytest tests/test_cli.py::test_export_preview_png_creates_image -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/pointglyph/preview.py tests/test_cli.py
git commit -m "feat: render particle previews"
```

---

### Task 7: CLI Pipeline

**Files:**
- Create: `src/pointglyph/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write failing CLI tests**

Add this to `tests/test_cli.py`:

```python
import json

from pointglyph.cli import main


def test_cli_creates_required_files(tmp_path, font_path):
    output_dir = tmp_path / "export"

    exit_code = main([
        "TEST",
        "--font",
        str(font_path),
        "--points",
        "25",
        "--output",
        str(output_dir),
        "--seed",
        "42",
    ])

    assert exit_code == 0
    assert (output_dir / "manifest.json").exists()
    assert (output_dir / "particles.json").exists()
    assert (output_dir / "preview.png").exists()
    particles = json.loads((output_dir / "particles.json").read_text())
    assert len(particles["attributes"]["textPositions"]) == 25 * 3


def test_cli_rejects_multiple_words(tmp_path, font_path):
    exit_code = main(["TWO WORDS", "--font", str(font_path), "--output", str(tmp_path)])

    assert exit_code == 2
```

- [ ] **Step 2: Run failing tests**

Run: `python3 -m pytest tests/test_cli.py -q`

Expected: FAIL because `pointglyph.cli` does not exist or lacks `main`.

- [ ] **Step 3: Implement CLI**

Add `src/pointglyph/cli.py`:

```python
import argparse
import sys
from pathlib import Path

from pointglyph.exporters import export_manifest_json, export_particles_json
from pointglyph.geometry import generate_cloud_positions, normalize_points_for_threejs
from pointglyph.preview import export_preview_png
from pointglyph.sampling import sample_text_points
from pointglyph.text_mask import render_text_mask


def _parse_color(raw: str) -> tuple[float, float, float]:
    parts = raw.split(",")
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("color must use r,g,b format")
    try:
        channels = tuple(float(part) for part in parts)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("color must use numeric r,g,b values") from exc
    if any(channel < 0.0 or channel > 1.0 for channel in channels):
        raise argparse.ArgumentTypeError("color channels must be between 0 and 1")
    return channels


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Three.js-ready particle text assets.")
    parser.add_argument("text", help="Single word to render")
    parser.add_argument("--font", required=True, type=Path, help="Path to a .ttf or .otf font")
    parser.add_argument("--points", type=int, default=6000, help="Target particle count")
    parser.add_argument("--output", required=True, type=Path, help="Output directory")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducible output")
    parser.add_argument("--width-units", type=float, default=10.0, help="Normalized text width")
    parser.add_argument("--cloud-radius", type=float, default=None, help="Scatter cloud radius")
    parser.add_argument("--z-jitter", type=float, default=0.02, help="Cloud z jitter")
    parser.add_argument("--color", type=_parse_color, default=(1.0, 1.0, 1.0), help="Default RGB color")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.text.strip() or any(char.isspace() for char in args.text):
        parser.error("text must be a single non-empty word")
    if not args.font.exists():
        parser.error(f"font file not found: {args.font}")
    if args.points < 1:
        parser.error("--points must be at least 1")

    args.output.mkdir(parents=True, exist_ok=True)
    text_mask = render_text_mask(args.text, args.font)
    image_points = sample_text_points(text_mask.mask, args.points, args.seed)
    text_positions, bounds = normalize_points_for_threejs(image_points, args.width_units)
    start_positions = generate_cloud_positions(args.points, bounds, args.cloud_radius, args.z_jitter, args.seed)
    end_seed = None if args.seed is None else args.seed + 1
    end_positions = generate_cloud_positions(args.points, bounds, args.cloud_radius, args.z_jitter, end_seed)

    export_particles_json(
        args.output / "particles.json",
        text=args.text,
        bounds=bounds,
        start_positions=start_positions,
        text_positions=text_positions,
        end_positions=end_positions,
    )
    export_manifest_json(
        args.output / "manifest.json",
        name=args.output.name,
        text=args.text,
        font_name=args.font.name,
        particle_count=args.points,
        bounds=bounds,
        default_particle_size=0.035,
        default_color=args.color,
    )
    export_preview_png(args.output / "preview.png", text_positions, bounds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

- [ ] **Step 4: Run CLI tests**

Run: `python3 -m pytest tests/test_cli.py -q`

Expected: PASS.

- [ ] **Step 5: Run all tests**

Run: `python3 -m pytest -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/pointglyph/cli.py tests/test_cli.py
git commit -m "feat: add PointGlyph CLI pipeline"
```

---

### Task 8: README Documentation

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace README content**

Set `README.md` to:

````markdown
# PointGlyph

PointGlyph converts a single word into lightweight Three.js-ready particle text
assets for hero effects.

It generates:

- `manifest.json`
- `particles.json`
- `preview.png`

PointGlyph does not build a website, viewer, or scroll animation runtime.

## Install

```bash
git clone <repo-url>
cd PointGlyph
python3 -m pip install -e .
```

## Usage

```bash
pointglyph "CONVERG3D" \
  --font ./fonts/Inter-Bold.ttf \
  --points 6000 \
  --output ./exports/converg3d \
  --seed 42
```

## Particle Data

`particles.json` uses flat arrays so a frontend can upload them directly into
Three.js buffer attributes:

```json
{
  "version": 1,
  "text": "CONVERG3D",
  "particleCount": 6000,
  "coordinateSystem": "threejs",
  "units": "normalized",
  "bounds": {
    "width": 10.0,
    "height": 2.4,
    "depth": 0.0
  },
  "attributes": {
    "startPositions": [0.0, 0.0, 0.0],
    "textPositions": [0.0, 0.0, 0.0],
    "endPositions": [0.0, 0.0, 0.0]
  }
}
```

## Three.js Loading Sketch

```js
const data = await fetch("/exports/converg3d/particles.json").then((res) => res.json());

const geometry = new THREE.BufferGeometry();
geometry.setAttribute(
  "position",
  new THREE.Float32BufferAttribute(data.attributes.startPositions, 3)
);
geometry.setAttribute(
  "textPosition",
  new THREE.Float32BufferAttribute(data.attributes.textPositions, 3)
);
geometry.setAttribute(
  "endPosition",
  new THREE.Float32BufferAttribute(data.attributes.endPositions, 3)
);
```

Interpolate between `startPositions`, `textPositions`, and `endPositions` in a
shader or animation loop with a single progress value.

## Future Work

- Edge-weighted sampling for sharper letter boundaries.
- Optional per-particle delays or motion factors.
- Optional `text_mesh.glb` export.
- Published package or `pipx` install path.
- Optional JavaScript helper after the data format stabilizes.
````

- [ ] **Step 2: Verify docs mention v1 non-goals**

Run: `rg -n "does not build|text_mesh\\.glb|Three.js Loading" README.md`

Expected: all three phrases appear.

- [ ] **Step 3: Run all tests**

Run: `python3 -m pytest -q`

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: document PointGlyph CLI usage"
```

---

### Task 9: Final Verification

**Files:**
- No new files unless fixes are required.

- [ ] **Step 1: Install editable package**

Run: `python3 -m pip install -e .`

Expected: install succeeds.

- [ ] **Step 2: Run test suite**

Run: `python3 -m pytest -q`

Expected: all tests pass.

- [ ] **Step 3: Run CLI smoke test**

Use a real font path from `tests/conftest.py`, then run:

```bash
pointglyph "TEST" --font /path/to/font.ttf --points 50 --output /tmp/pointglyph-test --seed 42
```

Expected:

```text
/tmp/pointglyph-test/manifest.json
/tmp/pointglyph-test/particles.json
/tmp/pointglyph-test/preview.png
```

- [ ] **Step 4: Inspect JSON shape**

Run:

```bash
python3 -m json.tool /tmp/pointglyph-test/manifest.json >/dev/null
python3 -m json.tool /tmp/pointglyph-test/particles.json >/dev/null
```

Expected: both commands exit successfully.

- [ ] **Step 5: Commit any verification fixes**

If verification required changes:

```bash
git add <changed-files>
git commit -m "fix: complete PointGlyph MVP verification"
```

If no changes were required, do not create an empty commit.

---

## Plan Self-Review

- Spec coverage: package shape, CLI, mask rendering, sampling, geometry, exporters, preview, tests, and docs are all mapped to tasks.
- Placeholder scan: no unresolved placeholder markers or deferred implementation steps inside v1 tasks.
- Scope check: GLB, website/viewer, JS helper, and publishing are excluded from implementation and listed only as future work.
- Type consistency: `Bounds`, `render_text_mask`, `sample_text_points`, `normalize_points_for_threejs`, `generate_cloud_positions`, exporter functions, and `export_preview_png` signatures match across tasks.
