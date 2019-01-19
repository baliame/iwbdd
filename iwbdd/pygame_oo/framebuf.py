from OpenGL.GL import *
from OpenGL.arrays.vbo import VBO
import numpy as np
from .game_shaders import GSH
from .shader import Mat4
from .texture import Texture2D


class Framebuffer:
    def __init__(self, w, h):
        self.fbid = glGenFramebuffers(1)
        self.target = Texture2D(w, h, None)
        self.transparency = Texture2D(w, h, None)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbid)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.target.texid, 0)
        glBindFramebuffer(GL_FRAMEBUFFER, None)
        self.draw_arrays = VBO(np.array([0, 0, 1, 0, 0, 1, 1, 1], dtype='f'))
        self.uv_arrays = VBO(np.array([0, 0, 1, 0, 0, 1, 1, 1], dtype='f'))
        self.identity = Mat4()

    def bind(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbid)

    def read_copy(self):
        glCopyImageSubData(self.transparency.texid, GL_TEXTURE_2D, 0, 0, 0, 0, self.target.texid, GL_TEXTURE_2D, 0, 0, 0, self.target.w, self.target.h, 1)

    def unbind(self):
        glBindFramebuffer(GL_FRAMEBUFFER, None)

    def new_render_pass(self, clear=False):
        if clear:
            self.transparency.clear(255)
        else:
            self.read_copy()

        return self

    def __enter__(self):
        self.bind()
        return self

    def __exit__(self, type, value, traceback):
        self.unbind()

    def blit_to_window(self):
        glBindFramebuffer(GL_FRAMEBUFFER, None)
        with GSH("GSHP_blit") as prog:
            prog.uniform("view", self.identity)
            prog.uniform("model", self.identity)
            glEnableVertexAttribArray(0)
            glEnableVertexAttribArray(1)
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, self.draw_arrays)
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, self.uv_arrays)
            glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
            glDisableVertexAttribArray(0)
            glDisableVertexAttribArray(1)
