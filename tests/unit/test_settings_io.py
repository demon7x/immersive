from app.config.settings import DEFAULT_CONFIG_PATH, load_settings, save_settings


def test_save_and_load_roundtrip(tmp_path) -> None:
    settings = load_settings(DEFAULT_CONFIG_PATH)
    settings.render.fov_deg = 72.0
    settings.render.box_depth_m = 1.44

    out_path = tmp_path / "runtime.yaml"
    save_settings(settings, out_path)

    loaded = load_settings(out_path)
    assert loaded.render.fov_deg == 72.0
    assert loaded.render.box_depth_m == 1.44
