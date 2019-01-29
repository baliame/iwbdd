from OpenGL.GL import *
import numpy as np


def TexUnitEnum(unit):
    if unit >= GL_TEXTURE0 and unit < GL_TEXTURE0 + GL_MAX_TEXTURE_UNITS:
        return unit
    if unit >= GL_MAX_TEXTURE_UNITS:
        raise RuntimeError("You cannot use this many texture units!")
    return GL_TEXTURE0 + unit


class Texture2D:
    def __init__(self, w, h, arr=None, arr_type=GL_UNSIGNED_BYTE, arr_colors=GL_RGBA, magf=GL_LINEAR, minf=GL_LINEAR, dest_colors=None, no_init=False):
        if dest_colors is None:
            dest_colors = arr_colors
        self.texid = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texid)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
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

    def bind(self):
        self.bindtexunit()

    def set_image(self, data, data_type=GL_UNSIGNED_INT, data_colors=GL_RGBA):
        glBindTexture(GL_TEXTURE_2D, self.texid)
        glTexImage2D(GL_TEXTURE_2D, 0, data_colors, self.w, self.h, 0, data_colors, data_type, data)
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
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.w, self.h, 0, GL_RGBA, GL_FLOAT, np.ones(self.w * self.h * 4, dtype=np.float))
        glBindTexture(GL_TEXTURE_2D, 0)


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
