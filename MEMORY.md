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
