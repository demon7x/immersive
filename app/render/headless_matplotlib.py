from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import imageio.v2 as imageio
import matplotlib
import numpy as np

matplotlib.use("Agg")
from matplotlib import pyplot as plt


@dataclass(slots=True)
class HeadlessRendererConfig:
    width: int = 960
    height: int = 540
    line_color: str = "#26d2ee"
    bg_color: str = "#090b14"


class HeadlessMatplotlibRenderer:
    def __init__(self, config: HeadlessRendererConfig) -> None:
        if config.width <= 0 or config.height <= 0:
            raise ValueError("width/height must be > 0")
        self._cfg = config

    def render_frame(
        self,
        view_matrix: np.ndarray,
        proj_matrix: np.ndarray,
        box_size_m: float,
        box_depth_m: float,
    ) -> np.ndarray:
        # We currently rely on view_matrix to derive camera location for a simple wireframe view.
        del proj_matrix

        fig = plt.figure(
            figsize=(self._cfg.width / 100.0, self._cfg.height / 100.0),
            dpi=100,
            facecolor=self._cfg.bg_color,
        )
        ax = fig.add_subplot(111, projection="3d")
        ax.set_facecolor(self._cfg.bg_color)
        ax.grid(False)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_zticks([])

        for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
            axis.line.set_color((0.0, 0.0, 0.0, 0.0))
            axis.set_pane_color((0.0, 0.0, 0.0, 0.0))

        s = box_size_m / 2.0
        z0 = 0.0
        z1 = -box_depth_m
        front = [(-s, -s, z0), (s, -s, z0), (s, s, z0), (-s, s, z0)]
        back = [(-s, -s, z1), (s, -s, z1), (s, s, z1), (-s, s, z1)]
        edges = [
            (front[0], front[1]), (front[1], front[2]), (front[2], front[3]), (front[3], front[0]),
            (back[0], back[1]), (back[1], back[2]), (back[2], back[3]), (back[3], back[0]),
            (front[0], back[0]), (front[1], back[1]), (front[2], back[2]), (front[3], back[3]),
        ]
        for a, b in edges:
            ax.plot(
                [a[0], b[0]],
                [a[1], b[1]],
                [a[2], b[2]],
                color=self._cfg.line_color,
                linewidth=2.0,
            )

        # view_matrix is world->camera; inverse translation approximates camera position.
        inv = np.linalg.inv(view_matrix)
        cam_x, cam_y, cam_z = float(inv[0, 3]), float(inv[1, 3]), float(inv[2, 3])
        azim = np.degrees(np.arctan2(cam_x, max(1e-6, cam_z)))
        elev = np.degrees(np.arctan2(cam_y, max(1e-6, cam_z)))
        ax.view_init(elev=elev, azim=180.0 - azim)

        bound = max(0.6, box_size_m)
        ax.set_xlim(-bound, bound)
        ax.set_ylim(-bound, bound)
        ax.set_zlim(-max(box_depth_m + 0.3, 1.0), 0.6)
        ax.set_box_aspect((1.0, 1.0, 1.0))
        fig.tight_layout(pad=0)

        fig.canvas.draw()
        w, h = fig.canvas.get_width_height()
        rgb = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8).reshape(h, w, 3)
        plt.close(fig)
        return rgb

    def render_sequence(
        self,
        frames: list[np.ndarray],
        out_path: Path,
        fps: int,
        fmt: str,
    ) -> Path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fmt_norm = fmt.lower()
        if fmt_norm not in ("mp4", "gif"):
            raise ValueError("format must be mp4 or gif")

        if fmt_norm == "mp4":
            try:
                imageio.mimsave(out_path, frames, fps=fps)
                return out_path
            except Exception:
                fallback = out_path.with_suffix(".gif")
                imageio.mimsave(fallback, frames, format="GIF", fps=fps)
                return fallback

        imageio.mimsave(out_path, frames, format="GIF", fps=fps)
        return out_path
