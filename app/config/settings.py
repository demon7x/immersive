from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class CameraSettings:
    grab_fps: int
    depth_mode: str
    body_model: str


@dataclass(slots=True)
class TrackingSettings:
    ema_alpha: float
    velocity_limit_m_s: float
    min_confidence: float
    loss_timeout_ms: int
    recenter_seconds: float


@dataclass(slots=True)
class RenderSettings:
    target_fps: int
    box_depth_m: float
    box_size_m: float
    fov_deg: float
    near_m: float
    far_m: float


@dataclass(slots=True)
class DisplaySettings:
    width_m: float
    height_m: float
    resolution_w: int
    resolution_h: int
    camera_offset: tuple[float, float, float, float, float, float]


@dataclass(slots=True)
class AppSettings:
    camera: CameraSettings
    tracking: TrackingSettings
    render: RenderSettings
    display: DisplaySettings


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "defaults.yaml"
RUNTIME_CONFIG_PATH = Path(__file__).resolve().parent / "runtime.yaml"


def load_settings(path: Path | None = None) -> AppSettings:
    cfg_path = path or (RUNTIME_CONFIG_PATH if RUNTIME_CONFIG_PATH.exists() else DEFAULT_CONFIG_PATH)
    raw = _load_yaml(cfg_path)

    camera = CameraSettings(**raw["camera"])
    tracking = TrackingSettings(**raw["tracking"])
    render = RenderSettings(**raw["render"])
    display_raw = raw["display"]
    display = DisplaySettings(
        width_m=float(display_raw["width_m"]),
        height_m=float(display_raw["height_m"]),
        resolution_w=int(display_raw["resolution_w"]),
        resolution_h=int(display_raw["resolution_h"]),
        camera_offset=tuple(display_raw["camera_offset"]),
    )

    return AppSettings(camera=camera, tracking=tracking, render=render, display=display)


def save_settings(settings: AppSettings, path: Path | None = None) -> Path:
    out_path = path or RUNTIME_CONFIG_PATH
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "camera": asdict(settings.camera),
        "tracking": asdict(settings.tracking),
        "render": asdict(settings.render),
        "display": {
            "width_m": settings.display.width_m,
            "height_m": settings.display.height_m,
            "resolution_w": settings.display.resolution_w,
            "resolution_h": settings.display.resolution_h,
            "camera_offset": list(settings.display.camera_offset),
        },
    }
    with out_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, sort_keys=False)
    return out_path


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid config format: {path}")
    return data
