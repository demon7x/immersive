import time

from PyQt6.QtCore import Qt

from app.tracking.keyboard_tracker import KeyboardTracker, KeyboardTrackerConfig


def test_moves_right_when_key_held() -> None:
    t = KeyboardTracker(KeyboardTrackerConfig(speed_m_s=1.0, z_fixed_m=0.7, bound_xy_m=1.0))
    t.start()
    p0 = t.get_latest_pose()
    t.set_key_state(Qt.Key.Key_Right, True)
    time.sleep(0.05)
    p1 = t.get_latest_pose()
    t.set_key_state(Qt.Key.Key_Right, False)
    t.stop()

    assert p1.position_m[0] > p0.position_m[0]


def test_opposite_keys_cancel_out() -> None:
    t = KeyboardTracker(KeyboardTrackerConfig(speed_m_s=1.0, z_fixed_m=0.7, bound_xy_m=1.0))
    t.start()
    t.set_key_state(Qt.Key.Key_Left, True)
    t.set_key_state(Qt.Key.Key_Right, True)
    time.sleep(0.05)
    p = t.get_latest_pose()
    t.stop()

    assert abs(p.position_m[0]) < 1e-3


def test_recenter_resets_position() -> None:
    t = KeyboardTracker(KeyboardTrackerConfig(speed_m_s=1.0, z_fixed_m=0.7, bound_xy_m=1.0))
    t.start()
    t.set_key_state(Qt.Key.Key_Up, True)
    time.sleep(0.05)
    _ = t.get_latest_pose()
    t.recenter()
    p = t.get_latest_pose()
    t.stop()

    assert p.position_m[0] == 0.0
    assert p.position_m[1] == 0.0
