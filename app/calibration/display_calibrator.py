from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from app.types import HeadPose


@dataclass(slots=True)
class DisplayParams:
    width_m: float
    height_m: float
    resolution_w: int
    resolution_h: int


class DisplayCalibrator:
    def __init__(self, params: DisplayParams, camera_offset: tuple[float, float, float, float, float, float]) -> None:
        self._params = params
        self._camera_offset = camera_offset

    def set_display_params(self, width_m: float, height_m: float, resolution_w: int, resolution_h: int) -> None:
        self._params = DisplayParams(
            width_m=width_m,
            height_m=height_m,
            resolution_w=resolution_w,
            resolution_h=resolution_h,
        )

    def set_camera_offset(self, tx_m: float, ty_m: float, tz_m: float, yaw_deg: float, pitch_deg: float, roll_deg: float) -> None:
        self._camera_offset = (tx_m, ty_m, tz_m, yaw_deg, pitch_deg, roll_deg)

    def compute_view_matrix(self, head_pose: HeadPose) -> np.ndarray:
        ox, oy, oz, oyaw, opitch, oroll = self._camera_offset
        x = head_pose.position_m[0] + ox
        y = head_pose.position_m[1] + oy
        z = head_pose.position_m[2] + oz
        yaw = math.radians(head_pose.yaw_pitch_roll_deg[0] + oyaw)
        pitch = math.radians(head_pose.yaw_pitch_roll_deg[1] + opitch)
        roll = math.radians(head_pose.yaw_pitch_roll_deg[2] + oroll)

        t = np.eye(4, dtype=np.float32)
        t[0, 3] = -x
        t[1, 3] = -y
        t[2, 3] = -z

        cy, sy = math.cos(yaw), math.sin(yaw)
        cp, sp = math.cos(pitch), math.sin(pitch)
        cr, sr = math.cos(roll), math.sin(roll)

        ry = np.array([[cy, 0.0, sy, 0.0], [0.0, 1.0, 0.0, 0.0], [-sy, 0.0, cy, 0.0], [0.0, 0.0, 0.0, 1.0]], dtype=np.float32)
        rx = np.array([[1.0, 0.0, 0.0, 0.0], [0.0, cp, -sp, 0.0], [0.0, sp, cp, 0.0], [0.0, 0.0, 0.0, 1.0]], dtype=np.float32)
        rz = np.array([[cr, -sr, 0.0, 0.0], [sr, cr, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]], dtype=np.float32)

        return rz @ rx @ ry @ t

    def compute_proj_matrix(self, fov_deg: float, near_m: float, far_m: float) -> np.ndarray:
        aspect = self._params.resolution_w / float(self._params.resolution_h)
        f = 1.0 / math.tan(math.radians(fov_deg) / 2.0)

        m = np.zeros((4, 4), dtype=np.float32)
        m[0, 0] = f / aspect
        m[1, 1] = f
        m[2, 2] = (far_m + near_m) / (near_m - far_m)
        m[2, 3] = (2.0 * far_m * near_m) / (near_m - far_m)
        m[3, 2] = -1.0
        return m
