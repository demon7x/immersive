from __future__ import annotations

import argparse
import signal
import sys
import time

import numpy as np
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QFocusEvent, QKeyEvent
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QWidget

from app.calibration.display_calibrator import DisplayCalibrator, DisplayParams
from app.config.settings import RUNTIME_CONFIG_PATH, load_settings, save_settings
from app.render.gl_widget import AnamorphicWidget
from app.tracking.base import Tracker
from app.tracking.keyboard_tracker import KeyboardTracker, KeyboardTrackerConfig
from app.tracking.pose_filter import FilterConfig, PoseFilter
from app.tracking.zed_tracker import ZedTracker, ZedTrackerConfig
from app.types import HeadPose, RenderState
from app.ui.control_panel import ControlPanel


class MainWindow(QMainWindow):
    def __init__(self, tracker: Tracker, input_mode: str) -> None:
        super().__init__()
        self.setWindowTitle("ZED2 Anamorphic Box MVP")

        self._settings = load_settings()
        self._tracker = tracker
        self._input_mode = input_mode
        self._filter = PoseFilter(
            FilterConfig(
                ema_alpha=self._settings.tracking.ema_alpha,
                velocity_limit_m_s=self._settings.tracking.velocity_limit_m_s,
                min_confidence=self._settings.tracking.min_confidence,
                loss_timeout_ms=self._settings.tracking.loss_timeout_ms,
                recenter_seconds=self._settings.tracking.recenter_seconds,
            )
        )
        self._calibrator = DisplayCalibrator(
            params=DisplayParams(
                width_m=self._settings.display.width_m,
                height_m=self._settings.display.height_m,
                resolution_w=self._settings.display.resolution_w,
                resolution_h=self._settings.display.resolution_h,
            ),
            camera_offset=self._settings.display.camera_offset,
        )

        self._running = True
        self._fov = self._settings.render.fov_deg
        self._depth = self._settings.render.box_depth_m

        self._render = AnamorphicWidget(target_fps=self._settings.render.target_fps)
        self._controls = ControlPanel(
            on_start_stop=self._on_start_stop,
            on_recalibrate=self._on_recalibrate,
            on_save_calibration=self._on_save_calibration,
            on_fov_change=self._on_fov_change,
            on_depth_change=self._on_depth_change,
            initial_fov=self._fov,
            initial_depth=self._depth,
        )

        root = QWidget(self)
        layout = QHBoxLayout(root)
        layout.addWidget(self._render, stretch=5)
        layout.addWidget(self._controls, stretch=2)
        self.setCentralWidget(root)

        self._fallback_pose = HeadPose(
            timestamp_ms=int(time.time() * 1000),
            position_m=(0.0, 0.0, 0.7),
            yaw_pitch_roll_deg=(0.0, 0.0, 0.0),
            confidence=1.0,
            valid=True,
        )

        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._tick)
        self._poll_timer.start(10)

        self._frame_counter = 0
        self._fps_window_started = time.perf_counter()
        self._last_fps = 0.0
        self._latency_ema_ms = 0.0
        self.statusBar().showMessage(self._status_text())

    def start(self) -> None:
        self._tracker.start()

    def closeEvent(self, event) -> None:  # noqa: N802
        self._tracker.stop()
        super().closeEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if isinstance(self._tracker, KeyboardTracker) and not event.isAutoRepeat():
            self._tracker.set_key_state(event.key(), True)
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if isinstance(self._tracker, KeyboardTracker) and not event.isAutoRepeat():
            self._tracker.set_key_state(event.key(), False)
        super().keyReleaseEvent(event)

    def focusOutEvent(self, event: QFocusEvent) -> None:  # noqa: N802
        if isinstance(self._tracker, KeyboardTracker):
            self._tracker.clear_keys()
        super().focusOutEvent(event)

    def _tick(self) -> None:
        if not self._running:
            return

        raw_pose = self._tracker.get_latest_pose()
        filtered = self._filter.update(raw_pose, self._fallback_pose)

        view = self._calibrator.compute_view_matrix(filtered)
        proj = self._calibrator.compute_proj_matrix(
            fov_deg=self._fov,
            near_m=self._settings.render.near_m,
            far_m=self._settings.render.far_m,
        )

        state = RenderState(
            view_matrix=np.array(view, dtype=np.float32).reshape(-1).tolist(),
            proj_matrix=np.array(proj, dtype=np.float32).reshape(-1).tolist(),
            box_depth_m=self._depth,
            box_size_m=self._settings.render.box_size_m,
        )
        self._render.set_render_state(state)
        self._update_metrics(raw_pose.timestamp_ms)

    def _on_start_stop(self, running: bool) -> None:
        self._running = running

    def _on_recalibrate(self) -> None:
        self._fallback_pose = HeadPose(
            timestamp_ms=int(time.time() * 1000),
            position_m=(0.0, 0.0, 0.7),
            yaw_pitch_roll_deg=(0.0, 0.0, 0.0),
            confidence=1.0,
            valid=True,
        )
        if isinstance(self._tracker, KeyboardTracker):
            self._tracker.recenter()

    def _on_fov_change(self, value: float) -> None:
        self._fov = value
        self._settings.render.fov_deg = value

    def _on_depth_change(self, value: float) -> None:
        self._depth = value
        self._settings.render.box_depth_m = value

    def _on_save_calibration(self) -> None:
        try:
            save_settings(self._settings)
        except Exception:
            # Keep runtime stable if save fails; status text still updates via metrics.
            pass

    def _update_metrics(self, pose_timestamp_ms: int) -> None:
        self._frame_counter += 1
        now_perf = time.perf_counter()
        elapsed = now_perf - self._fps_window_started
        if elapsed >= 1.0:
            self._last_fps = self._frame_counter / elapsed
            self._frame_counter = 0
            self._fps_window_started = now_perf

        now_ms = int(time.time() * 1000)
        sample = max(0.0, float(now_ms - pose_timestamp_ms))
        alpha = 0.2
        self._latency_ema_ms = self._latency_ema_ms * (1.0 - alpha) + sample * alpha
        self.statusBar().showMessage(self._status_text())

    def _status_text(self) -> str:
        cfg = RUNTIME_CONFIG_PATH.name if RUNTIME_CONFIG_PATH.exists() else "defaults.yaml"
        return f"Mode: {self._input_mode} | FPS: {self._last_fps:.1f} | Latency: {self._latency_ema_ms:.1f}ms | Config: {cfg}"


def _parse_args(argv: list[str]) -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(description="ZED2 / keyboard anamorphic renderer")
    parser.add_argument("--input-mode", choices=("zed", "keyboard"), default="zed")
    parser.add_argument("--kb-speed-mps", type=float, default=0.35)
    parser.add_argument("--kb-z-fixed", type=float, default=0.70)
    parser.add_argument("--kb-bound", type=float, default=0.35)
    return parser.parse_known_args(argv)


def _build_tracker(args: argparse.Namespace) -> Tracker:
    if args.input_mode == "keyboard":
        return KeyboardTracker(
            KeyboardTrackerConfig(
                speed_m_s=args.kb_speed_mps,
                z_fixed_m=args.kb_z_fixed,
                bound_xy_m=args.kb_bound,
            )
        )

    settings = load_settings()
    return ZedTracker(ZedTrackerConfig(camera=settings.camera))


def main() -> int:
    args, qt_args = _parse_args(sys.argv[1:])
    app = QApplication([sys.argv[0], *qt_args])
    window = MainWindow(tracker=_build_tracker(args), input_mode=args.input_mode)
    window.resize(1400, 850)
    window.show()

    def _shutdown(*_) -> None:
        window.close()
        app.quit()

    signal.signal(signal.SIGINT, _shutdown)

    try:
        window.start()
    except Exception as exc:
        print(f"Startup error: {exc}", file=sys.stderr)
        return 1

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
