from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any

from app.config.settings import CameraSettings
from app.tracking.base import Tracker
from app.types import HeadPose

try:
    import pyzed.sl as sl
except Exception:  # pragma: no cover - runtime dependency
    sl = None


@dataclass(slots=True)
class ZedTrackerConfig:
    camera: CameraSettings


class ZedTracker(Tracker):
    def __init__(self, config: ZedTrackerConfig) -> None:
        self._cfg = config
        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None
        self._latest_pose = HeadPose(
            timestamp_ms=int(time.time() * 1000),
            position_m=(0.0, 0.0, 0.7),
            yaw_pitch_roll_deg=(0.0, 0.0, 0.0),
            confidence=0.0,
            valid=False,
        )

        self._camera: Any = None
        self._bodies: Any = None

    def start(self) -> None:
        if self._running:
            return
        if sl is None:
            raise RuntimeError("pyzed.sl not available. Install ZED SDK Python bindings.")

        self._camera = sl.Camera()
        init = sl.InitParameters()
        init.camera_fps = self._cfg.camera.grab_fps
        init.depth_mode = getattr(sl.DEPTH_MODE, self._cfg.camera.depth_mode, sl.DEPTH_MODE.PERFORMANCE)

        err = self._camera.open(init)
        if err != sl.ERROR_CODE.SUCCESS:
            raise RuntimeError(f"Failed to open ZED camera: {err}")

        body_params = sl.BodyTrackingParameters()
        body_params.enable_tracking = True
        body_model = getattr(sl.BODY_TRACKING_MODEL, self._cfg.camera.body_model, sl.BODY_TRACKING_MODEL.HUMAN_BODY_MEDIUM)
        body_params.body_format = sl.BODY_FORMAT.BODY_38
        body_params.detection_model = body_model

        err = self._camera.enable_body_tracking(body_params)
        if err != sl.ERROR_CODE.SUCCESS:
            self._camera.close()
            raise RuntimeError(f"Failed to enable body tracking: {err}")

        self._bodies = sl.Bodies()
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, name="zed-capture", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

        if self._camera is not None:
            try:
                self._camera.disable_body_tracking()
            except Exception:
                pass
            self._camera.close()
            self._camera = None

    def get_latest_pose(self) -> HeadPose:
        with self._lock:
            return self._latest_pose

    def _capture_loop(self) -> None:
        runtime = sl.RuntimeParameters()
        body_runtime = sl.BodyTrackingRuntimeParameters()

        while self._running:
            if self._camera.grab(runtime) != sl.ERROR_CODE.SUCCESS:
                time.sleep(0.002)
                continue

            self._camera.retrieve_bodies(self._bodies, body_runtime)
            pose = self._extract_pose(self._bodies)
            with self._lock:
                self._latest_pose = pose

    def _extract_pose(self, bodies: Any) -> HeadPose:
        now_ms = int(time.time() * 1000)
        if not bodies.is_new:
            return HeadPose(
                timestamp_ms=now_ms,
                position_m=self._latest_pose.position_m,
                yaw_pitch_roll_deg=self._latest_pose.yaw_pitch_roll_deg,
                confidence=0.0,
                valid=False,
            )

        if len(bodies.body_list) == 0:
            return HeadPose(
                timestamp_ms=now_ms,
                position_m=self._latest_pose.position_m,
                yaw_pitch_roll_deg=self._latest_pose.yaw_pitch_roll_deg,
                confidence=0.0,
                valid=False,
            )

        body = max(bodies.body_list, key=lambda b: b.confidence)
        # BODY_38 index for nose/head center can vary by SDK version.
        # We pick the first reliable upper-face keypoint available.
        kp3d = body.keypoint
        idx_candidates = (27, 26, 30, 0)
        point = None
        for idx in idx_candidates:
            if idx < len(kp3d):
                p = kp3d[idx]
                if all(abs(v) < 1000 for v in p):
                    point = p
                    break

        if point is None:
            return HeadPose(
                timestamp_ms=now_ms,
                position_m=self._latest_pose.position_m,
                yaw_pitch_roll_deg=self._latest_pose.yaw_pitch_roll_deg,
                confidence=0.0,
                valid=False,
            )

        position = (float(point[0]), float(point[1]), float(point[2]))
        return HeadPose(
            timestamp_ms=now_ms,
            position_m=position,
            yaw_pitch_roll_deg=(0.0, 0.0, 0.0),
            confidence=float(body.confidence) / 100.0,
            valid=True,
        )
