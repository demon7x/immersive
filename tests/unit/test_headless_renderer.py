import numpy as np

from app.render.headless_matplotlib import HeadlessMatplotlibRenderer, HeadlessRendererConfig


def test_render_frame_shape_and_dtype() -> None:
    r = HeadlessMatplotlibRenderer(HeadlessRendererConfig(width=320, height=180))
    view = np.eye(4, dtype=np.float32)
    proj = np.eye(4, dtype=np.float32)

    frame = r.render_frame(view_matrix=view, proj_matrix=proj, box_size_m=0.8, box_depth_m=1.2)

    assert frame.shape == (180, 320, 3)
    assert frame.dtype == np.uint8


def test_invalid_resolution_raises() -> None:
    try:
        HeadlessMatplotlibRenderer(HeadlessRendererConfig(width=0, height=180))
        assert False, "Expected ValueError"
    except ValueError:
        assert True
