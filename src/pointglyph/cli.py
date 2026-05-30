import argparse
import sys
from pathlib import Path

from pointglyph.exporters import export_manifest_json, export_particles_json
from pointglyph.geometry import (
    generate_appear_progresses,
    generate_cloud_positions,
    generate_lingering_text_positions,
    normalize_points_for_threejs,
)
from pointglyph.preview import export_preview_png, export_solid_preview_png
from pointglyph.sampling import sample_text_points
from pointglyph.text_mask import create_wordmark_source, render_text_mask

LINGERING_PARTICLE_FRACTION = 0.12


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
    parser.add_argument("--output", required=True, type=Path, help="Output directory")
    parser.add_argument("--points", type=int, default=6000, help="Target particle count")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducible output")
    parser.add_argument("--width-units", type=float, default=10.0, help="Normalized text width")
    parser.add_argument("--cloud-radius", type=float, default=None, help="Scatter cloud radius")
    parser.add_argument("--z-jitter", type=float, default=0.02, help="Cloud z jitter")
    parser.add_argument("--color", type=_parse_color, default=(1.0, 1.0, 1.0), help="Default RGB color")
    parser.add_argument(
        "--preview",
        action="store_const",
        const=True,
        default=argparse.SUPPRESS,
        help="Accepted for compatibility; preview generation is always enabled",
    )
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
    if args.width_units <= 0:
        parser.error("--width-units must be greater than 0")
    if args.z_jitter < 0:
        parser.error("--z-jitter must be greater than or equal to 0")
    if args.cloud_radius is not None and args.cloud_radius <= 0:
        parser.error("--cloud-radius must be greater than 0")

    args.output.mkdir(parents=True, exist_ok=True)
    text_mask = render_text_mask(args.text, args.font)
    wordmark = create_wordmark_source(text_mask)
    image_points = sample_text_points(wordmark.mask, args.points, args.seed)
    text_positions, bounds = normalize_points_for_threejs(image_points, args.width_units, wordmark.source_bounds)
    start_positions = generate_cloud_positions(args.points, bounds, args.cloud_radius, args.z_jitter, args.seed)
    end_seed = None if args.seed is None else args.seed + 1
    end_positions = generate_cloud_positions(args.points, bounds, args.cloud_radius, args.z_jitter, end_seed)
    appear_seed = None if args.seed is None else args.seed + 2
    appear_progresses = generate_appear_progresses(args.points, appear_seed)
    lingering_seed = None if args.seed is None else args.seed + 7
    lingering_text_positions = generate_lingering_text_positions(
        text_positions,
        bounds,
        residual_fraction=LINGERING_PARTICLE_FRACTION,
        seed=lingering_seed,
    )
    solid_particle_count = args.points * 4
    solid_sample_seed = None if args.seed is None else args.seed + 3
    solid_start_seed = None if args.seed is None else args.seed + 4
    solid_end_seed = None if args.seed is None else args.seed + 5
    solid_appear_seed = None if args.seed is None else args.seed + 6
    solid_image_points = sample_text_points(wordmark.mask, solid_particle_count, solid_sample_seed)
    solid_text_positions, solid_bounds = normalize_points_for_threejs(
        solid_image_points,
        args.width_units,
        wordmark.source_bounds,
    )
    solid_start_positions = generate_cloud_positions(
        solid_particle_count,
        solid_bounds,
        args.cloud_radius,
        args.z_jitter,
        solid_start_seed,
    )
    solid_end_positions = generate_cloud_positions(
        solid_particle_count,
        solid_bounds,
        args.cloud_radius,
        args.z_jitter,
        solid_end_seed,
    )
    solid_appear_progresses = generate_appear_progresses(solid_particle_count, solid_appear_seed)

    export_particles_json(
        args.output / "particles.json",
        text=args.text,
        bounds=bounds,
        start_positions=start_positions,
        text_positions=text_positions,
        end_positions=end_positions,
        appear_progresses=appear_progresses,
    )
    export_particles_json(
        args.output / "lingering_particles.json",
        text=args.text,
        bounds=bounds,
        start_positions=start_positions,
        text_positions=lingering_text_positions,
        end_positions=end_positions,
        appear_progresses=appear_progresses,
    )
    export_particles_json(
        args.output / "solid_particles.json",
        text=args.text,
        bounds=solid_bounds,
        start_positions=solid_start_positions,
        text_positions=solid_text_positions,
        end_positions=solid_end_positions,
        appear_progresses=solid_appear_progresses,
    )
    solid_metadata = export_solid_preview_png(args.output / "solid_preview.png", wordmark.mask, bounds)
    alignment = {
        **solid_metadata,
        "worldToTexture": {
            "world": {
                "left": -bounds.width / 2.0,
                "right": bounds.width / 2.0,
                "top": bounds.height / 2.0,
                "bottom": -bounds.height / 2.0,
            },
            "texture": {
                "left": 0,
                "right": solid_metadata["solidTexture"]["width"],
                "top": 0,
                "bottom": solid_metadata["solidTexture"]["height"],
            },
        },
    }
    export_manifest_json(
        args.output / "manifest.json",
        name=args.output.name,
        text=args.text,
        font_name=args.font.name,
        particle_count=args.points,
        bounds=bounds,
        default_particle_size=0.035,
        default_color=args.color,
        alignment=alignment,
        lingering_particle_fraction=LINGERING_PARTICLE_FRACTION,
    )
    export_preview_png(args.output / "preview.png", text_positions, bounds)
    export_preview_png(args.output / "lingering_particle_preview.png", lingering_text_positions, bounds)
    export_preview_png(args.output / "solid_particle_preview.png", solid_text_positions, solid_bounds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
