from app.tracking.pose_filter import FilterConfig, PoseFilter
from app.types import HeadPose


def _pose(ts: int, x: float, conf: float = 1.0, valid: bool = True) -> HeadPose:
    return HeadPose(
        timestamp_ms=ts,
        position_m=(x, 0.0, 0.7),
        yaw_pitch_roll_deg=(0.0, 0.0, 0.0),
        confidence=conf,
        valid=valid,
    )


def test_ema_smooths_position() -> None:
    f = PoseFilter(FilterConfig(ema_alpha=0.5, velocity_limit_m_s=100.0))
    fallback = _pose(0, 0.0)

    out1 = f.update(_pose(100, 0.0), fallback)
    out2 = f.update(_pose(200, 1.0), fallback)

    assert out1.position_m[0] == 0.0
    assert 0.49 < out2.position_m[0] < 0.51


def test_velocity_limit_clamps_jump() -> None:
    f = PoseFilter(FilterConfig(ema_alpha=1.0, velocity_limit_m_s=1.0))
    fallback = _pose(0, 0.0)

    f.update(_pose(100, 0.0), fallback)
    out = f.update(_pose(200, 3.0), fallback)

    assert 0.09 <= out.position_m[0] <= 0.11


def test_tracking_loss_hold_then_recenter() -> None:
    f = PoseFilter(FilterConfig(loss_timeout_ms=300, recenter_seconds=1.0))
    fallback = _pose(0, 0.0)

    f.update(_pose(100, 1.0), fallback)

    hold = f.update(_pose(250, 9.0, conf=0.0, valid=False), fallback)
    assert 0.9 < hold.position_m[0] <= 1.0

    recentered = f.update(_pose(1700, 9.0, conf=0.0, valid=False), fallback)
    assert 0.0 <= recentered.position_m[0] < 0.2
