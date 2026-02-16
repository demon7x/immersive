from __future__ import annotations

import argparse
from pathlib import Path

from app.calibration.display_calibrator import DisplayCalibrator, DisplayParams
from app.config.settings import DEFAULT_CONFIG_PATH, load_settings
from app.render.headless_matplotlib import HeadlessMatplotlibRenderer, HeadlessRendererConfig
from app.sim.camera_path import PathConfig, generate_lissajous_path, generate_orbit_path


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Headless Colab renderer")
    p.add_argument("--duration-s", type=float, default=6.0)
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--width", type=int, default=960)
    p.add_argument("--height", type=int, default=540)
    p.add_argument("--format", choices=("mp4", "gif"), default="mp4")
    p.add_argument("--path-type", choices=("orbit", "lissajous"), default="orbit")
    p.add_argument("--out", type=Path, default=Path("outputs/colab_render.mp4"))
    p.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    if args.duration_s <= 0.0:
        raise SystemExit("--duration-s must be > 0")
    if args.fps <= 0:
        raise SystemExit("--fps must be > 0")
    if args.width <= 0 or args.height <= 0:
        raise SystemExit("--width/--height must be > 0")

    settings = load_settings(args.config)
    calibrator = DisplayCalibrator(
        params=DisplayParams(
            width_m=settings.display.width_m,
            height_m=settings.display.height_m,
            resolution_w=args.width,
            resolution_h=args.height,
        ),
        camera_offset=settings.display.camera_offset,
    )

    path_cfg = PathConfig(duration_s=args.duration_s, fps=args.fps)
    if args.path_type == "orbit":
        poses = generate_orbit_path(path_cfg)
    else:
        poses = generate_lissajous_path(path_cfg)

    renderer = HeadlessMatplotlibRenderer(HeadlessRendererConfig(width=args.width, height=args.height))
    proj = calibrator.compute_proj_matrix(
        fov_deg=settings.render.fov_deg,
        near_m=settings.render.near_m,
        far_m=settings.render.far_m,
    )

    frames = []
    for pose in poses:
        view = calibrator.compute_view_matrix(pose)
        frame = renderer.render_frame(
            view_matrix=view,
            proj_matrix=proj,
            box_size_m=settings.render.box_size_m,
            box_depth_m=settings.render.box_depth_m,
        )
        frames.append(frame)

    saved = renderer.render_sequence(
        frames=frames,
        out_path=args.out,
        fps=args.fps,
        fmt=args.format,
    )
    print(f"Saved: {saved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
