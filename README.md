# PointGlyph

PointGlyph converts a single word into lightweight Three.js-ready particle text
assets for hero effects.

It generates:

- `manifest.json`
- `particles.json`
- `preview.png`
- `solid_preview.png`
- `solid_particles.json`
- `solid_particle_preview.png`

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

## Font Files

PointGlyph uses the exact `.ttf` or `.otf` file passed to `--font`. To generate
bold assets, pass a real bold font file:

```bash
pointglyph "CONVERG3D" --font ./fonts/Inter-Regular.ttf --output ./exports/normal
pointglyph "CONVERG3D" --font ./fonts/Inter-Bold.ttf --output ./exports/bold
```

The CLI intentionally does not include a synthetic `--bold` flag, font-family
lookup, or font-weight inference. The generated `manifest.json` records the
supplied font file basename.

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
    "endPositions": [0.0, 0.0, 0.0],
    "appearProgresses": [0.0, 0.24, 0.0]
  }
}
```

The arrays above are abbreviated. In real output, each position array contains
`particleCount * 3` numbers: `x, y, z` for every particle.
`appearProgresses` contains one number per particle. At most half of those
values are `0.0`; the rest are seeded values between `0.08` and `0.75` so a
runtime can reveal particles after the animation starts.

## Manifest Data

`manifest.json` describes the generated asset set and rendering defaults:

```json
{
  "version": 1,
  "name": "converg3d",
  "text": "CONVERG3D",
  "font": "Inter-Bold.ttf",
  "particleCount": 6000,
  "defaultParticleSize": 0.035,
  "defaultColor": [1.0, 1.0, 1.0],
  "bounds": {
    "width": 10.0,
    "height": 2.4,
    "depth": 0.0
  },
  "files": {
    "particles": "particles.json",
    "preview": "preview.png",
    "solidPreview": "solid_preview.png",
    "solidParticles": "solid_particles.json",
    "solidParticlePreview": "solid_particle_preview.png"
  },
  "variants": {
    "default": {
      "particles": "particles.json",
      "preview": "preview.png",
      "particleCount": 6000
    },
    "solid": {
      "particles": "solid_particles.json",
      "preview": "solid_particle_preview.png",
      "solidPreview": "solid_preview.png",
      "particleCount": 24000,
      "recommendedForActualSolidText": false
    }
  },
  "animation": {
    "particleReveal": {
      "attribute": "appearProgresses",
      "initialVisibleFraction": 0.5,
      "delayedProgressRange": [0.08, 0.75],
      "meaning": "Hide or fade each particle until global progress reaches its appearProgress."
    },
    "solidText": {
      "texture": "solid_preview.png",
      "recommendedRenderMode": "TexturePlane",
      "fadeInAfterParticleReveal": true
    }
  },
  "recommendedThreeJs": {
    "renderMode": "BufferGeometryPoints",
    "material": "ShaderMaterial or PointsMaterial",
    "solidRenderMode": "TexturePlane",
    "transparent": true,
    "depthWrite": false
  }
}
```

V1 does not include a `textMesh` field or reference `text_mesh.glb` in the
manifest.

`preview.png` shows the sampled particle positions. `solid_preview.png` is a
transparent text render using the same font mask and canvas size, so a frontend
can fade it over the particle text for an actual solid-text phase.
`solid_particles.json` uses the same schema as `particles.json` with 4x the
requested particle count for compatibility with particle-only renderers, but it
is not the recommended solid text output.

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
geometry.setAttribute(
  "appearProgress",
  new THREE.Float32BufferAttribute(data.attributes.appearProgresses, 1)
);

const manifest = await fetch("/exports/converg3d/manifest.json").then((res) => res.json());
const solidTexture = await new THREE.TextureLoader().loadAsync(
  `/exports/converg3d/${manifest.animation.solidText.texture}`
);
const solidMaterial = new THREE.MeshBasicMaterial({
  map: solidTexture,
  transparent: true,
  opacity: 0
});
const solidText = new THREE.Mesh(
  new THREE.PlaneGeometry(data.bounds.width, data.bounds.height),
  solidMaterial
);
```

Interpolate between `startPositions`, `textPositions`, and `endPositions` in a
shader or animation loop with a single progress value. Gate each particle's
alpha against its `appearProgress` attribute, then fade `solidText.material`
from `0` to `1` once the particle wordmark has formed.

## Future Work

- Edge-weighted sampling for sharper letter boundaries.
- Optional `text_mesh.glb` export.
- Published package or `pipx` install path.
- Optional JavaScript helper after the data format stabilizes.
