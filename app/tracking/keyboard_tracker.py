from __future__ import annotations

import threading
import time
from dataclasses import dataclass

from PyQt6.QtCore import Qt

from app.tracking.base import Tracker
from app.types import HeadPose


@dataclass(slots=True)
class KeyboardTrackerConfig:
    speed_m_s: float = 0.35
    z_fixed_m: float = 0.7
    bound_xy_m: float = 0.35


class KeyboardTracker(Tracker):
    def __init__(self, config: KeyboardTrackerConfig) -> None:
        self._cfg = config
        self._lock = threading.Lock()
        self._running = False
        self._pressed: set[int] = set()
        self._x = 0.0
        self._y = 0.0
        self._last_mono = time.monotonic()

    def start(self) -> None:
        with self._lock:
            self._running = True
            self._last_mono = time.monotonic()

    def stop(self) -> None:
        with self._lock:
            self._running = False
            self._pressed.clear()

    def get_latest_pose(self) -> HeadPose:
        with self._lock:
            now_mono = time.monotonic()
            dt = max(0.0, now_mono - self._last_mono)
            self._last_mono = now_mono

            if self._running:
                dx = 0.0
                dy = 0.0
                if Qt.Key.Key_Left in self._pressed:
                    dx -= 1.0
                if Qt.Key.Key_Right in self._pressed:
                    dx += 1.0
                if Qt.Key.Key_Up in self._pressed:
                    dy += 1.0
                if Qt.Key.Key_Down in self._pressed:
                    dy -= 1.0

                step = self._cfg.speed_m_s * dt
                self._x += dx * step
                self._y += dy * step

                b = self._cfg.bound_xy_m
                self._x = max(-b, min(b, self._x))
                self._y = max(-b, min(b, self._y))

            return HeadPose(
                timestamp_ms=int(time.time() * 1000),
                position_m=(self._x, self._y, self._cfg.z_fixed_m),
                yaw_pitch_roll_deg=(0.0, 0.0, 0.0),
                confidence=1.0,
                valid=True,
            )

    def set_key_state(self, key: int, pressed: bool) -> None:
        if key not in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down):
            return
        with self._lock:
            if pressed:
                self._pressed.add(key)
            else:
                self._pressed.discard(key)

    def clear_keys(self) -> None:
        with self._lock:
            self._pressed.clear()

    def recenter(self) -> None:
        with self._lock:
            self._x = 0.0
            self._y = 0.0
            self._pressed.clear()
