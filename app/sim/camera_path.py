from __future__ import annotations

import math
from dataclasses import dataclass

from app.types import HeadPose


@dataclass(slots=True)
class PathConfig:
    duration_s: float = 6.0
    fps: int = 30
    x_amp_m: float = 0.2
    y_amp_m: float = 0.12
    z_base_m: float = 0.7
    z_amp_m: float = 0.08
    clamp_xy_m: float = 0.35
    clamp_z_min_m: float = 0.4
    clamp_z_max_m: float = 1.2


def generate_orbit_path(config: PathConfig) -> list[HeadPose]:
    _validate(config)
    frames = int(round(config.duration_s * config.fps))
    out: list[HeadPose] = []
    for i in range(frames):
        t = i / max(1, frames - 1)
        angle = t * math.tau
        x = config.x_amp_m * math.cos(angle)
        y = config.y_amp_m * math.sin(angle)
        z = config.z_base_m + config.z_amp_m * math.sin(angle * 0.5)
        out.append(_pose(i, config.fps, x, y, z, config))
    return out


def generate_lissajous_path(config: PathConfig) -> list[HeadPose]:
    _validate(config)
    frames = int(round(config.duration_s * config.fps))
    out: list[HeadPose] = []
    for i in range(frames):
        t = i / max(1, frames - 1)
        phase = t * math.tau
        x = config.x_amp_m * math.sin(2.0 * phase)
        y = config.y_amp_m * math.sin(3.0 * phase + math.pi / 4.0)
        z = config.z_base_m + config.z_amp_m * math.cos(phase)
        out.append(_pose(i, config.fps, x, y, z, config))
    return out


def _pose(i: int, fps: int, x: float, y: float, z: float, cfg: PathConfig) -> HeadPose:
    x = max(-cfg.clamp_xy_m, min(cfg.clamp_xy_m, x))
    y = max(-cfg.clamp_xy_m, min(cfg.clamp_xy_m, y))
    z = max(cfg.clamp_z_min_m, min(cfg.clamp_z_max_m, z))
    return HeadPose(
        timestamp_ms=int((i / fps) * 1000.0),
        position_m=(x, y, z),
        yaw_pitch_roll_deg=(0.0, 0.0, 0.0),
        confidence=1.0,
        valid=True,
    )


def _validate(config: PathConfig) -> None:
    if config.duration_s <= 0.0:
        raise ValueError("duration_s must be > 0")
    if config.fps <= 0:
        raise ValueError("fps must be > 0")
