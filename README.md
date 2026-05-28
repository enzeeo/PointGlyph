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
