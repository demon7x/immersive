import numpy as np

from app.calibration.display_calibrator import DisplayCalibrator, DisplayParams
from app.types import HeadPose


def test_projection_matrix_has_perspective_shape() -> None:
    c = DisplayCalibrator(
        params=DisplayParams(width_m=0.6, height_m=0.34, resolution_w=1920, resolution_h=1080),
        camera_offset=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    )
    m = c.compute_proj_matrix(fov_deg=60.0, near_m=0.05, far_m=10.0)

    assert m.shape == (4, 4)
    assert np.isclose(m[3, 2], -1.0)
    assert m[2, 3] < 0.0


def test_view_matrix_translates_inverse_pose() -> None:
    c = DisplayCalibrator(
        params=DisplayParams(width_m=0.6, height_m=0.34, resolution_w=1920, resolution_h=1080),
        camera_offset=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    )
    pose = HeadPose(
        timestamp_ms=0,
        position_m=(1.0, 2.0, 3.0),
        yaw_pitch_roll_deg=(0.0, 0.0, 0.0),
        confidence=1.0,
        valid=True,
    )

    m = c.compute_view_matrix(pose)
    assert np.isclose(m[0, 3], -1.0)
    assert np.isclose(m[1, 3], -2.0)
    assert np.isclose(m[2, 3], -3.0)


def test_view_matrix_applies_camera_offset() -> None:
    c = DisplayCalibrator(
        params=DisplayParams(width_m=0.6, height_m=0.34, resolution_w=1920, resolution_h=1080),
        camera_offset=(0.1, -0.1, 0.2, 0.0, 0.0, 0.0),
    )
    pose = HeadPose(
        timestamp_ms=0,
        position_m=(1.0, 2.0, 3.0),
        yaw_pitch_roll_deg=(0.0, 0.0, 0.0),
        confidence=1.0,
        valid=True,
    )
    m = c.compute_view_matrix(pose)
    assert np.isclose(m[0, 3], -(1.1))
    assert np.isclose(m[1, 3], -(1.9))
    assert np.isclose(m[2, 3], -(3.2))
