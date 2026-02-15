from app.config.settings import DEFAULT_CONFIG_PATH, load_settings
from app.tracking.keyboard_tracker import KeyboardTracker, KeyboardTrackerConfig
from app.tracking.pose_filter import FilterConfig, PoseFilter
from app.types import HeadPose


def test_settings_and_filter_contract() -> None:
    settings = load_settings(DEFAULT_CONFIG_PATH)
    f = PoseFilter(
        FilterConfig(
            ema_alpha=settings.tracking.ema_alpha,
            velocity_limit_m_s=settings.tracking.velocity_limit_m_s,
            min_confidence=settings.tracking.min_confidence,
            loss_timeout_ms=settings.tracking.loss_timeout_ms,
            recenter_seconds=settings.tracking.recenter_seconds,
        )
    )

    fallback = HeadPose(
        timestamp_ms=0,
        position_m=(0.0, 0.0, 0.7),
        yaw_pitch_roll_deg=(0.0, 0.0, 0.0),
        confidence=1.0,
        valid=True,
    )
    raw = HeadPose(
        timestamp_ms=20,
        position_m=(0.1, 0.0, 0.7),
        yaw_pitch_roll_deg=(0.0, 0.0, 0.0),
        confidence=1.0,
        valid=True,
    )

    out = f.update(raw, fallback)
    assert out.valid
    assert out.confidence > 0


def test_keyboard_tracker_smoke() -> None:
    tracker = KeyboardTracker(KeyboardTrackerConfig())
    tracker.start()
    pose = tracker.get_latest_pose()
    tracker.stop()

    assert pose.valid
    assert pose.confidence == 1.0
