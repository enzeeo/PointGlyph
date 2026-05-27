# PointGlyph MVP Design

Date: 2026-05-27
Status: APPROVED
Mode: Open source
Primary user: Frontend developer building a Three.js hero effect
Reference: `/Users/enzeeo/Downloads/text-point-model-converter-codex-brief.md`

## Goal

Build a small Python package with a CLI that converts a single word and font file
into animation-ready particle text assets for Three.js.

The first release is an asset generator, not a viewer. It should produce compact
data that a frontend developer can load directly into `BufferGeometry`.

## Non-Goals

- No website, landing page, or Three.js viewer.
- No scroll animation runtime.
- No CMS or upload system.
- No per-particle mesh objects.
- No `text_mesh.glb` in v1.
- No frontend helper package in v1.

## User Workflow

1. Clone the repo.
2. Install in editable mode with `pip install -e .`.
3. Run the CLI with a word, font path, point count, and output directory.
4. Inspect `preview.png`.
5. Load `particles.json` in a Three.js project.

Example target command:

```bash
pointglyph "CONVERG3D" \
  --font ./fonts/Inter-Bold.ttf \
  --points 6000 \
  --output ./exports/converg3d \
  --seed 42
```

## Package Shape

```text
src/pointglyph/
  __init__.py
  cli.py
  text_mask.py
  sampling.py
  geometry.py
  exporters.py
  preview.py

tests/
  test_cli.py
  test_geometry.py
  test_sampling.py
  test_exporters.py
```

## Components

### `cli.py`

Parses command-line arguments, validates inputs, creates the output directory,
and runs the conversion pipeline.

Required arguments:

- `text`: single word only.
- `--font`: path to `.ttf` or `.otf`.
- `--output`: output directory.

Options:

- `--points`: default `6000`.
- `--seed`: optional integer for reproducible output.
- `--width-units`: default `10.0`.
- `--cloud-radius`: optional override, otherwise derived from text bounds.
- `--z-jitter`: default `0.02`.
- `--color`: default `1,1,1`.
- `--preview`: default enabled.

No `--mesh` flag in v1. GLB export is documented as deferred.

### `text_mask.py`

Renders the input word into a high-resolution grayscale mask using Pillow.

Responsibilities:

- Load the supplied font.
- Render text with enough padding to avoid clipping.
- Preserve holes inside letters like `O`, `P`, `A`, `D`, and `R`.
- Return the mask plus useful pixel bounds.

### `sampling.py`

Samples target text positions from filled pixels in the mask.

V1 uses uniform sampling from nonzero mask pixels. Edge-weighted sampling is a
future improvement, not part of the first release.

Responsibilities:

- Use the seed for deterministic sampling.
- Support sampling with replacement if the mask has fewer filled pixels than
  requested particles.
- Return a NumPy array of image-space points.

### `geometry.py`

Converts image-space points into centered Three.js coordinates.

Responsibilities:

- Normalize word width to `width_units`.
- Scale height proportionally.
- Center the word around `(0, 0, 0)`.
- Flip image-space `y` so text is upright in Three.js.
- Generate deterministic start and end cloud positions around the text bounds.
- Keep text `z` at `0`; apply small random `z` jitter only to cloud states.

### `exporters.py`

Writes compact JSON files.

Required output:

```text
manifest.json
particles.json
```

`particles.json` must use flat arrays:

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

The real arrays contain `particleCount * 3` values for positions.
V1 stores shared particle size and color in `manifest.json`, not per-particle
arrays, to keep the animation payload compact.

`manifest.json` includes:

- version
- name
- text
- font basename
- particle count
- default particle size
- default color
- bounds
- file references
- recommended Three.js rendering notes

The manifest must not reference `text_mesh.glb` in v1.

### `preview.py`

Writes `preview.png` for quick visual inspection.

The preview should show the readable text state as dots on a plain background.
It does not need to animate.

## Data Flow

1. Parse and validate CLI arguments.
2. Render the word into a high-resolution text mask.
3. Sample filled mask pixels into text points.
4. Normalize text points into centered Three.js coordinates.
5. Generate start and end cloud positions with the same particle count.
6. Export `particles.json`.
7. Export `manifest.json`.
8. Export `preview.png`.

## Error Handling

- Missing font path: fail with a clear message.
- Empty or whitespace text: fail with a clear message.
- Text containing spaces: fail because v1 supports a single word.
- Point count less than `1`: fail with a clear message.
- Output path cannot be created or written: surface the filesystem error.
- Invalid color format: fail with expected `r,g,b` format.

No broad recovery logic is needed. The CLI should fail early and clearly.

## Testing

Use the smallest tests that verify the output contract.

Required coverage:

- CLI creates `manifest.json`, `particles.json`, and `preview.png`.
- Same seed creates identical position arrays.
- Different seeds create different cloud arrays.
- Position arrays have length `particleCount * 3`.
- Manifest contains the configured shared particle size and color.
- Text coordinates are centered around zero.
- Image-space `y` is flipped for Three.js coordinates.
- Manifest references only files that v1 writes.
- Single-word validation rejects text with spaces.

Tests should use a real font available in the test environment or a checked-in
small fixture font if licensing allows it.

## Documentation

README should include:

- What PointGlyph does.
- Install from clone: `pip install -e .`.
- CLI example.
- Output file list.
- `particles.json` schema.
- Minimal Three.js `BufferGeometry` loading snippet.
- GLB export listed as future work.

The Three.js snippet should stay documentation-only. Do not add a website,
viewer, bundler, or example app in v1.

## Success Criteria

- A frontend developer can generate particle text assets from a word and font.
- The output text state is clearly readable in `preview.png`.
- `particles.json` can be uploaded to Three.js buffer attributes without
  per-particle object conversion.
- Re-running with the same seed is deterministic.
- The repo structure is clear enough for open-source contributors to extend.

## Future Work

- Edge-weighted sampling for sharper letter boundaries.
- Optional per-particle delays or motion factors.
- Optional `text_mesh.glb` export.
- Published package or `pipx` install path.
- Optional JavaScript helper after the data format stabilizes.
