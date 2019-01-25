from OpenGL.GL import *
from OpenGL.arrays.vbo import VBO
import numpy as np
from .game_shaders import GSH
from .shader import Mat4
from .texture import Texture2D, TexUnitEnum


class Framebuffer:
    bound = None

    def __init__(self, w, h, wnd, name='Unknown'):
        self.wnd = wnd
        self.fbo_name = name
        self.fbid = glGenFramebuffers(1)
        self.target = Texture2D(w, h, None)
        self.transparency = Texture2D(w, h, None)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbid)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.target.texid, 0)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        self.draw_arrays = VBO(np.array([0, 0, 1, 0, 0, 1, 1, 1], dtype='f'))
        self.uv_arrays = VBO(np.array([0, 0, 1, 0, 0, 1, 1, 1], dtype='f'))
        self.identity = Mat4()

    def bind(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbid)
        Framebuffer.bound = self

    def bindtexunit(self, unit):
        glActiveTexture(TexUnitEnum(unit))
        glBindTexture(GL_TEXTURE_2D, self.transparency.texid)

    def read_copy(self):
        glCopyImageSubData(self.target.texid, GL_TEXTURE_2D, 0, 0, 0, 0, self.transparency.texid, GL_TEXTURE_2D, 0, 0, 0, 0, self.target.w, self.target.h, 1)

    def unbind(self):
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        Framebuffer.bound = None

    def new_render_pass(self, clear=False):
        if clear:
            self.transparency.clear()
        else:
            self.read_copy()
            self.wnd.log_read_copy(self.fbo_name)

        return self

    def __enter__(self):
        self.bind()
        return self

    def __exit__(self, type, value, traceback):
        self.unbind()

    def blit_to_window(self):
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        Framebuffer.bound = None
        with GSH("GSHP_blit") as prog:
            prog.uniform("view", self.identity)
            prog.uniform("model", self.identity)
            glEnableVertexAttribArray(0)
            glEnableVertexAttribArray(1)
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, self.draw_arrays)
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, self.uv_arrays)
            glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
            self.wnd.log_draw()
            glDisableVertexAttribArray(0)
            glDisableVertexAttribArray(1)
