# Project Memory

## Decisions

### 2026-05-27 - PointGlyph MVP Scope
- Decided: V1 is a small Python package with a CLI that generates Three.js-ready particle text assets.
- Why: The first open-source user is a frontend developer building a hero effect, so the core value is direct `BufferGeometry`-friendly output.
- Rejected: A one-off script, a full viewer/website, and a library-plus-frontend-helper release.

### 2026-05-27 - Defer GLB Export
- Decided: `text_mesh.glb` is not part of v1.
- Why: The brief says particle JSON is the main product, and GLB adds geometry/dependency risk before the core pipeline is proven.
- Rejected: Implementing GLB now or exposing a `--mesh` flag that only errors.

### 2026-05-27 - Docs Snippet Only
- Decided: Include a minimal Three.js `BufferGeometry` snippet in docs, but no frontend code.
- Why: Frontend developers need proof that the output is usable, while the project must remain an asset generator.
- Rejected: A bundled website, viewer, or JavaScript helper in v1.

### 2026-05-27 - Implementation Goal
- Decided: The plan approval goal is an end-to-end v1 CLI: word plus font in, `manifest.json`, `particles.json`, and `preview.png` out.
- Why: This gives implementation agents a concrete finish line tied to the approved MVP scope.
- Rejected: Treating package scaffolding or partial module work as sufficient without generated assets and docs.

### 2026-05-27 - Solid Preview Overlay
- Decided: Exports include `solid_preview.png` as a transparent solid text render, separate from particle `preview.png`.
- Why: Frontends can fade a solid glyph overlay in when particles cluster, then fade it out as particles disperse.
- Rejected: Adding mesh or GLB export for this; solid preview is a 2D overlay asset only.

### 2026-05-28 - Dense Solid Particle Variant
- Decided: Each export also writes `solid_particles.json` and `solid_particle_preview.png` at 4x the requested particle count.
- Why: This gives consumers a particle-only solid-looking state while preserving the crisp `solid_preview.png` texture-plane option.
- Rejected: Replacing `particles.json`, adding a CLI flag, or adding mesh/GLB output.

### 2026-05-28 - Bold Means Real Font File
- Decided: Bold support should mean passing a real bold `.ttf` or `.otf` via the existing `--font` option.
- Why: PointGlyph's model is exact font file in, rendered particle assets out; real bold fonts preserve glyph design better than synthetic thickening.
- Rejected: A synthetic `--bold` flag, font-family/weight resolution, and manifest-only font weight metadata for this pass.

### 2026-05-28 - Delayed Reveal and Solid Texture Plane
- Decided: Particle JSON includes seeded `appearProgresses`, with floor-half of particles visible immediately and the rest revealed during text formation; manifest guidance then fades particles to zero opacity.
- Why: The hero animation should reanimate over time, converge into the wordmark, and finish with only solid text visible.
- Rejected: Adding a bundled frontend runtime or CLI flags for this default behavior.

### 2026-05-28 - Actual Solid Text Uses `solid_preview.png`
- Decided: `solid_preview.png` is the recommended actual solid-text phase, rendered as black text on a Three.js texture plane sized to the exported bounds.
- Why: Dense particles can look solid but are still visibly particle-based; a texture generated from the same font mask gives a crisp wordmark.
- Rejected: Treating `solid_particles.json` as the authoritative solid phase or adding GLB/mesh output in this pass.

### 2026-05-29 - Canonical Cropped Wordmark Source
- Decided: Particles and `solid_preview.png` are generated from the same cropped font alpha mask, and manifest alignment metadata records texture size, content box, zero inset, and world-to-texture mapping.
- Why: A solid texture with different crop, padding, or aspect ratio cannot align perfectly with particle `textPositions`.
- Rejected: Independent solid texture sizing, CSS text overlays, and adding SVG/outline parsing in this pass.

### 2026-05-30 - Lingering Particle Variant
- Decided: Exports include `lingering_particles.json` and `lingering_particle_preview.png` as an extra variant, while the actual solid word remains `solid_preview.png`.
- Why: Some hero states need a solid readable wordmark with a subtle unconnected particle halo so not every particle appears to have converged.
- Rejected: Replacing the default fadeout behavior, adding a CLI flag, or hardcoding a blue particle color.
