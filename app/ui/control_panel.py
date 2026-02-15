from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


class ControlPanel(QWidget):
    def __init__(
        self,
        on_start_stop,
        on_recalibrate,
        on_save_calibration,
        on_fov_change,
        on_depth_change,
        initial_fov: float,
        initial_depth: float,
    ) -> None:
        super().__init__()

        self._on_start_stop = on_start_stop
        self._running = True

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)

        btn_row = QHBoxLayout()
        self._start_stop_btn = QPushButton("Stop")
        self._start_stop_btn.clicked.connect(self._toggle_run)
        recal_btn = QPushButton("Recalibrate")
        recal_btn.clicked.connect(on_recalibrate)
        save_btn = QPushButton("Save Calibration")
        save_btn.clicked.connect(on_save_calibration)
        btn_row.addWidget(self._start_stop_btn)
        btn_row.addWidget(recal_btn)
        btn_row.addWidget(save_btn)

        form = QFormLayout()
        fov_value = int(round(initial_fov))
        depth_value = int(round(initial_depth * 100))

        self._fov_label = QLabel(str(fov_value))
        fov = QSlider(Qt.Orientation.Horizontal)
        fov.setRange(40, 100)
        fov.setValue(max(40, min(100, fov_value)))
        fov.valueChanged.connect(lambda v: (self._fov_label.setText(str(v)), on_fov_change(float(v))))

        self._depth_label = QLabel(f"{depth_value/100.0:.2f}")
        depth = QSlider(Qt.Orientation.Horizontal)
        depth.setRange(50, 250)
        depth.setValue(max(50, min(250, depth_value)))
        depth.valueChanged.connect(lambda v: (self._depth_label.setText(f"{v/100.0:.2f}"), on_depth_change(v / 100.0)))

        form.addRow("FOV", fov)
        form.addRow("FOV value", self._fov_label)
        form.addRow("Depth", depth)
        form.addRow("Depth value", self._depth_label)

        root.addLayout(btn_row)
        root.addLayout(form)

    def _toggle_run(self) -> None:
        self._running = not self._running
        self._start_stop_btn.setText("Stop" if self._running else "Start")
        self._on_start_stop(self._running)
