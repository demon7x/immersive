from app.sim.camera_path import PathConfig, generate_lissajous_path, generate_orbit_path


def test_orbit_path_length_and_bounds() -> None:
    cfg = PathConfig(duration_s=2.0, fps=20)
    path = generate_orbit_path(cfg)

    assert len(path) == 40
    for p in path:
        assert -cfg.clamp_xy_m <= p.position_m[0] <= cfg.clamp_xy_m
        assert -cfg.clamp_xy_m <= p.position_m[1] <= cfg.clamp_xy_m
        assert cfg.clamp_z_min_m <= p.position_m[2] <= cfg.clamp_z_max_m


def test_lissajous_timestamps_monotonic() -> None:
    cfg = PathConfig(duration_s=1.0, fps=10)
    path = generate_lissajous_path(cfg)
    stamps = [p.timestamp_ms for p in path]

    assert len(path) == 10
    assert stamps == sorted(stamps)
