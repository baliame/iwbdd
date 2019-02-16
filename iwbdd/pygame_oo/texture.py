from OpenGL.GL import *
import numpy as np
from .game_shaders import GSHp
from .shader import Mat4, Vec4
from OpenGL.arrays.vbo import VBO
from . import logger


def TexUnitEnum(unit):
    if unit >= GL_TEXTURE0 and unit < GL_TEXTURE0 + GL_MAX_TEXTURE_UNITS:
        return unit
    if unit >= GL_MAX_TEXTURE_UNITS:
        raise RuntimeError("You cannot use this many texture units!")
    return GL_TEXTURE0 + unit


class Texture2D:
    draw_arrays = None
    uv_arrays = None
    vao = None

    def __init__(self, w, h, arr=None, arr_type=GL_UNSIGNED_BYTE, arr_colors=GL_RGBA, magf=GL_LINEAR, minf=GL_LINEAR, dest_colors=None, no_init=False, wrap_x=GL_CLAMP_TO_EDGE, wrap_y=GL_CLAMP_TO_EDGE):
        if dest_colors is None:
            dest_colors = arr_colors
        self.texid = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texid)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, wrap_x)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, wrap_y)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, magf)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, minf)
        if no_init:
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_FLOAT, None)
        else:
            if arr is not None:
                glTexImage2D(GL_TEXTURE_2D, 0, dest_colors, w, h, 0, arr_colors, arr_type, arr)
            else:
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_FLOAT, np.ones([h, w, 4], dtype=np.float))
        self.w = w
        self.h = h
        self.last_unit = None
        if Texture2D.draw_arrays is None:
            Texture2D.draw_arrays = VBO(np.array([0, 0, 1, 0, 0, 1, 1, 1], dtype='f'))
            Texture2D.uv_arrays = VBO(np.array([0, 0, 1, 0, 0, 1, 1, 1], dtype='f'))
            Texture2D.vao = glGenVertexArrays(1)
            glBindVertexArray(Texture2D.vao)
            Texture2D.draw_arrays.bind()
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, Texture2D.draw_arrays)
            Texture2D.uv_arrays.bind()
            glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 0, Texture2D.uv_arrays)
            Texture2D.draw_arrays.unbind()
            Texture2D.uv_arrays.unbind()
            glEnableVertexAttribArray(0)
            glEnableVertexAttribArray(1)
            glBindVertexArray(0)

    def bind(self):
        self.bindtexunit()

    def set_image(self, data, data_type=GL_UNSIGNED_INT, data_colors=GL_RGBA, dest_colors=None, debug=False, noresize=False):
        if dest_colors is None:
            dest_colors = data_colors
        glBindTexture(GL_TEXTURE_2D, self.texid)
        if noresize:
            glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, self.w, self.h, data_colors, data_type, data)
        else:
            glTexImage2D(GL_TEXTURE_2D, 0, dest_colors, self.w, self.h, 0, data_colors, data_type, data)
        glBindTexture(GL_TEXTURE_2D, 0)

    def bindtexunit(self, unit=None):
        if unit is not None:
            unit = TexUnitEnum(unit)
            glActiveTexture(unit)
        self.last_unit = unit
        glBindTexture(GL_TEXTURE_2D, self.texid)

    def unbind(self):
        if self.last_unit is not None:
            glActiveTexture(self.last_unit)
        glBindTexture(GL_TEXTURE_2D, 0)

    def clear(self):
        glBindTexture(GL_TEXTURE_2D, self.texid)
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, self.w, self.h, GL_RGBA, GL_FLOAT, np.zeros(self.w * self.h * 4, dtype=np.float))
        glBindTexture(GL_TEXTURE_2D, 0)

    def screen_render(self, wnd, x, y, w, h, transparency, colorize=(1.0, 1.0, 1.0, 1.0)):
        with GSHp('GSHP_render') as prog:
            wnd.setup_render(prog)
            prog.uniform('model', Mat4.scaling(w, h).translate(x, y))
            prog.uniform('colorize', Vec4(colorize[0], colorize[1], colorize[2], colorize[3]))
            self.bindtexunit(0)
            transparency.bindtexunit(1)
            glBindVertexArray(Texture2D.vao)
            glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
            logger.log_draw()
            glBindVertexArray(0)


class TextureSet2D:
    def __init__(self, w, h, frames, arr=None, arr_type=GL_UNSIGNED_BYTE, arr_colors=GL_RGBA, no_init=False):
        self.texid = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D_ARRAY, self.texid)
        glTexParameterf(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameterf(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameterf(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        if no_init:
            glTexImage3D(GL_TEXTURE_2D_ARRAY, 0, GL_RGBA, w, h, frames, 0, GL_RGBA, GL_FLOAT, None)
        else:
            if arr is not None:
                glTexImage3D(GL_TEXTURE_2D_ARRAY, 0, GL_RGBA, w, h, frames, 0, arr_colors, arr_type, arr)
            else:
                glTexImage3D(GL_TEXTURE_2D_ARRAY, 0, GL_RGBA, w, h, frames, 0, GL_RGBA, GL_FLOAT, np.ones([frames, h, w, 4], dtype=np.float))
        self.w = w
        self.h = h
        self.last_unit = None
        self.is_context = False

    def bind(self):
        self.bindtexunit()

    def bindtexunit(self, unit=None):
        if unit is not None:
            unit = TexUnitEnum(unit)
            glActiveTexture(unit)
        self.last_unit = unit
        glBindTexture(GL_TEXTURE_2D_ARRAY, self.texid)

    def unbind(self):
        if self.last_unit is not None:
            glActiveTexture(self.last_unit)
        glBindTexture(GL_TEXTURE_2D_ARRAY, 0)

    def clear(self, color=0xFFFFFFFF):
        glBindTexture(GL_TEXTURE_2D_ARRAY, self.texid)
        glTexImage3D(GL_TEXTURE_2D_ARRAY, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_INT, np.full(width * height, color, dtype='u'))

    def __enter__(self):
        self.bindtexunit()
        self.is_context = True
        return self

    def set_image(self, idx, data, data_type=GL_UNSIGNED_INT, data_colors=GL_RGBA):
        if not self.is_context:
            raise RuntimeError("set_image must be used with 'with' syntax.")
        glTexSubImage3D(GL_TEXTURE_2D_ARRAY, 0, 0, 0, idx, self.w, self.h, 1, data_colors, data_type, data)

    def __exit__(self, type, value, traceback):
        self.unbind()
        self.is_context = False
