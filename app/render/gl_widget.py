from __future__ import annotations

import ctypes
import re

import numpy as np
from OpenGL import GL
from PyQt6.QtCore import QTimer
from PyQt6.QtOpenGLWidgets import QOpenGLWidget

from app.types import RenderState


VERT_SHADER_330 = """
#version 330 core
layout(location = 0) in vec3 aPos;
uniform mat4 u_view;
uniform mat4 u_proj;
void main() {
    gl_Position = u_proj * u_view * vec4(aPos, 1.0);
}
"""

FRAG_SHADER_330 = """
#version 330 core
out vec4 FragColor;
void main() {
    FragColor = vec4(0.15, 0.75, 0.95, 1.0);
}
"""

VERT_SHADER_150 = """
#version 150
in vec3 aPos;
uniform mat4 u_view;
uniform mat4 u_proj;
void main() {
    gl_Position = u_proj * u_view * vec4(aPos, 1.0);
}
"""

FRAG_SHADER_150 = """
#version 150
out vec4 FragColor;
void main() {
    FragColor = vec4(0.15, 0.75, 0.95, 1.0);
}
"""

VERT_SHADER_120 = """
#version 120
attribute vec3 aPos;
uniform mat4 u_view;
uniform mat4 u_proj;
void main() {
    gl_Position = u_proj * u_view * vec4(aPos, 1.0);
}
"""

FRAG_SHADER_120 = """
#version 120
void main() {
    gl_FragColor = vec4(0.15, 0.75, 0.95, 1.0);
}
"""


class AnamorphicWidget(QOpenGLWidget):
    def __init__(self, target_fps: int, parent=None) -> None:
        super().__init__(parent)
        self._program = 0
        self._vao = 0
        self._vbo = 0
        self._vertex_count = 0
        self._state = RenderState(
            view_matrix=np.eye(4, dtype=np.float32).reshape(-1).tolist(),
            proj_matrix=np.eye(4, dtype=np.float32).reshape(-1).tolist(),
            box_depth_m=1.2,
            box_size_m=0.8,
        )

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update)
        self._timer.start(max(1, int(1000 / max(1, target_fps))))
        self._gl_ready = False

    def set_render_state(self, state: RenderState) -> None:
        geometry_changed = (
            state.box_depth_m != self._state.box_depth_m
            or state.box_size_m != self._state.box_size_m
        )
        self._state = state
        if self._gl_ready and geometry_changed:
            self._rebuild_geometry(state.box_size_m, state.box_depth_m)

    def initializeGL(self) -> None:
        vert_src, frag_src = self._select_shaders()
        self._program = self._create_program(vert_src, frag_src)
        self._rebuild_geometry(self._state.box_size_m, self._state.box_depth_m)
        GL.glEnable(GL.GL_DEPTH_TEST)
        self._gl_ready = True

    def paintGL(self) -> None:
        GL.glClearColor(0.03, 0.03, 0.05, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        GL.glUseProgram(self._program)
        view_loc = GL.glGetUniformLocation(self._program, "u_view")
        proj_loc = GL.glGetUniformLocation(self._program, "u_proj")
        view = np.array(self._state.view_matrix, dtype=np.float32).reshape(4, 4)
        proj = np.array(self._state.proj_matrix, dtype=np.float32).reshape(4, 4)
        GL.glUniformMatrix4fv(view_loc, 1, GL.GL_TRUE, view)
        GL.glUniformMatrix4fv(proj_loc, 1, GL.GL_TRUE, proj)

        GL.glBindVertexArray(self._vao)
        GL.glDrawArrays(GL.GL_LINES, 0, self._vertex_count)

    def resizeGL(self, w: int, h: int) -> None:
        GL.glViewport(0, 0, w, max(1, h))

    def _rebuild_geometry(self, size_m: float, depth_m: float) -> None:
        s = size_m / 2.0
        z0 = 0.0
        z1 = -depth_m

        front = [(-s, -s, z0), (s, -s, z0), (s, s, z0), (-s, s, z0)]
        back = [(-s, -s, z1), (s, -s, z1), (s, s, z1), (-s, s, z1)]

        lines = [
            front[0], front[1], front[1], front[2], front[2], front[3], front[3], front[0],
            back[0], back[1], back[1], back[2], back[2], back[3], back[3], back[0],
            front[0], back[0], front[1], back[1], front[2], back[2], front[3], back[3],
        ]

        vertices = np.array(lines, dtype=np.float32).reshape(-1)
        self._vertex_count = len(lines)

        if self._vao == 0:
            self._vao = GL.glGenVertexArrays(1)
        if self._vbo == 0:
            self._vbo = GL.glGenBuffers(1)

        GL.glBindVertexArray(self._vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._vbo)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL.GL_STATIC_DRAW)
        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, ctypes.c_void_p(0))

    def _create_program(self, vert_src: str, frag_src: str) -> int:
        vs = GL.glCreateShader(GL.GL_VERTEX_SHADER)
        GL.glShaderSource(vs, vert_src)
        GL.glCompileShader(vs)
        self._check_shader(vs)

        fs = GL.glCreateShader(GL.GL_FRAGMENT_SHADER)
        GL.glShaderSource(fs, frag_src)
        GL.glCompileShader(fs)
        self._check_shader(fs)

        program = GL.glCreateProgram()
        GL.glAttachShader(program, vs)
        GL.glAttachShader(program, fs)
        GL.glBindAttribLocation(program, 0, "aPos")
        GL.glLinkProgram(program)

        ok = GL.glGetProgramiv(program, GL.GL_LINK_STATUS)
        if not ok:
            raise RuntimeError(GL.glGetProgramInfoLog(program).decode("utf-8", errors="ignore"))

        GL.glDeleteShader(vs)
        GL.glDeleteShader(fs)
        return program

    def _check_shader(self, shader: int) -> None:
        ok = GL.glGetShaderiv(shader, GL.GL_COMPILE_STATUS)
        if not ok:
            raise RuntimeError(GL.glGetShaderInfoLog(shader).decode("utf-8", errors="ignore"))

    def _select_shaders(self) -> tuple[str, str]:
        raw = GL.glGetString(GL.GL_SHADING_LANGUAGE_VERSION)
        if not raw:
            return VERT_SHADER_120, FRAG_SHADER_120

        text = raw.decode("utf-8", errors="ignore")
        match = re.search(r"(\\d+)\\.(\\d+)", text)
        if not match:
            return VERT_SHADER_120, FRAG_SHADER_120

        major = int(match.group(1))
        minor = int(match.group(2))
        if major > 3 or (major == 3 and minor >= 30):
            return VERT_SHADER_330, FRAG_SHADER_330
        if major > 1 or (major == 1 and minor >= 50):
            return VERT_SHADER_150, FRAG_SHADER_150
        return VERT_SHADER_120, FRAG_SHADER_120
