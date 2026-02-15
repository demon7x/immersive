from __future__ import annotations

import math
from dataclasses import dataclass

from app.types import HeadPose


@dataclass(slots=True)
class FilterConfig:
    ema_alpha: float = 0.35
    velocity_limit_m_s: float = 1.5
    min_confidence: float = 0.4
    loss_timeout_ms: int = 300
    recenter_seconds: float = 0.6


class PoseFilter:
    def __init__(self, config: FilterConfig) -> None:
        self._cfg = config
        self._last_stable_pose: HeadPose | None = None
        self._last_output_pose: HeadPose | None = None
        self._loss_started_ms: int | None = None

    def update(self, raw_pose: HeadPose, fallback_pose: HeadPose) -> HeadPose:
        if raw_pose.valid and raw_pose.confidence >= self._cfg.min_confidence:
            self._loss_started_ms = None
            filtered = self._apply_filter(raw_pose)
            self._last_stable_pose = filtered
            self._last_output_pose = filtered
            return filtered

        now_ms = raw_pose.timestamp_ms
        if self._loss_started_ms is None:
            self._loss_started_ms = now_ms

        elapsed_ms = now_ms - self._loss_started_ms
        stable = self._last_stable_pose or fallback_pose
        if elapsed_ms <= self._cfg.loss_timeout_ms:
            hold_pose = HeadPose(
                timestamp_ms=now_ms,
                position_m=stable.position_m,
                yaw_pitch_roll_deg=stable.yaw_pitch_roll_deg,
                confidence=stable.confidence,
                valid=True,
            )
            self._last_output_pose = hold_pose
            return hold_pose

        recentered = self._recenter_pose(now_ms, stable, fallback_pose)
        self._last_output_pose = recentered
        return recentered

    def _apply_filter(self, pose: HeadPose) -> HeadPose:
        prev = self._last_output_pose
        if prev is None:
            return pose

        dt_s = max(1e-3, (pose.timestamp_ms - prev.timestamp_ms) / 1000.0)
        max_step = self._cfg.velocity_limit_m_s * dt_s

        prev_pos = prev.position_m
        target_pos = pose.position_m
        delta = tuple(target_pos[i] - prev_pos[i] for i in range(3))
        dist = math.sqrt(sum(d * d for d in delta))
        if dist > max_step:
            scale = max_step / dist
            target_pos = tuple(prev_pos[i] + delta[i] * scale for i in range(3))

        a = self._cfg.ema_alpha
        smooth_pos = tuple(prev_pos[i] * (1.0 - a) + target_pos[i] * a for i in range(3))
        smooth_rot = tuple(
            prev.yaw_pitch_roll_deg[i] * (1.0 - a) + pose.yaw_pitch_roll_deg[i] * a
            for i in range(3)
        )

        return HeadPose(
            timestamp_ms=pose.timestamp_ms,
            position_m=smooth_pos,
            yaw_pitch_roll_deg=smooth_rot,
            confidence=pose.confidence,
            valid=True,
        )

    def _recenter_pose(
        self,
        now_ms: int,
        stable_pose: HeadPose,
        fallback_pose: HeadPose,
    ) -> HeadPose:
        duration_ms = int(self._cfg.recenter_seconds * 1000)
        if duration_ms <= 0:
            return fallback_pose

        assert self._loss_started_ms is not None
        t = min(1.0, max(0.0, (now_ms - self._loss_started_ms - self._cfg.loss_timeout_ms) / duration_ms))

        p0 = stable_pose.position_m
        r0 = stable_pose.yaw_pitch_roll_deg
        p1 = fallback_pose.position_m
        r1 = fallback_pose.yaw_pitch_roll_deg

        p = tuple(p0[i] * (1.0 - t) + p1[i] * t for i in range(3))
        r = tuple(r0[i] * (1.0 - t) + r1[i] * t for i in range(3))

        return HeadPose(
            timestamp_ms=now_ms,
            position_m=p,
            yaw_pitch_roll_deg=r,
            confidence=1.0 - t,
            valid=True,
        )
