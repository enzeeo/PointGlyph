# Particle-to-solid wordmark approach

## Recommendation

Use one visual coordinate system for the hero wordmark.

The current implementation combines:

- particle geometry from `/public/converg3d/particles.json`
- browser-rendered DOM text from `h1.three-wordmark`

That can be tuned, but it is fragile. Browser text metrics, font fallback, antialiasing, point size, and responsive CSS can make the DOM text drift from the particle layer.

The better long-term approach is to make the visible wordmark come from the particle asset pipeline, not from live DOM text.

## Preferred options

### Option A: Particle-only wordmark

Use particles for the entire visible wordmark.

Animation flow:

1. Intro: `startPositions -> textPositions`
2. Resting state: particles stay at `textPositions`
3. Scroll: `textPositions -> endPositions`

To make the resting state read more like solid text:

- increase particle density during asset generation
- use darker particle colors
- increase alpha while resting
- reduce point softness
- optionally use a slightly larger point size only while resting

Keep a hidden or screen-reader-only `h1` for accessibility and SEO.

### Option B: Particle layer plus generated solid image

Use particles for animation and a generated image for the crisp solid wordmark.

Asset pipeline:

1. Render the wordmark to a canvas using the exact intended font.
2. Sample that same canvas to create `textPositions`.
3. Export a `solid_preview.png` from the same canvas.
4. Render `solid_preview.png` as a Three.js plane using the same camera and bounds as the particles.
5. Fade the plane out immediately when scroll dispersion starts.

This avoids browser DOM font drift while preserving a crisp solid wordmark.

## JSON structure

Keep the JSON as the source of truth:

```json
{
  "text": "CONVERG3D",
  "font": "Arial.ttf",
  "particleCount": 6000,
  "bounds": {
    "width": 10,
    "height": 1.1845816358508303,
    "depth": 0
  },
  "attributes": {
    "startPositions": [],
    "textPositions": [],
    "endPositions": []
  },
  "files": {
    "solidPreview": "solid_preview.png"
  }
}
```

Useful metadata to add later:

- source canvas width and height
- font family, font file, font size, weight, and tracking
- sampling threshold
- particle radius or intended point size
- normalized bounds used by Three.js
- asset generation script version

## Implementation direction

1. Keep `textPositions` as the canonical wordmark geometry.
2. Remove visible DOM text from the hero.
3. Keep accessible text separately:

```html
<h1 class="screen-reader-only">CONVERG3D</h1>
```

4. For Option A, make the particle resting state visually dense enough to read as the wordmark.
5. For Option B, add a `THREE.PlaneGeometry` sized to `bounds.width` and `bounds.height`, apply `solid_preview.png` as a texture, and fade that material out on scroll.

## When to choose each option

Choose Option A if the brand should feel animated and particle-native.

Choose Option B if the initial wordmark must look sharp and typographic before it breaks into particles.

Avoid continuing with live DOM text for the visible wordmark unless quick iteration matters more than long-term alignment.
