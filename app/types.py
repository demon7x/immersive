from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class HeadPose:
    timestamp_ms: int
    position_m: tuple[float, float, float]
    yaw_pitch_roll_deg: tuple[float, float, float]
    confidence: float
    valid: bool


@dataclass(slots=True)
class RenderState:
    view_matrix: list[float]
    proj_matrix: list[float]
    box_depth_m: float
    box_size_m: float
