from OpenGL.GL import *
import pygame


class Texture2D:
    def __init__(self, w, h, pgsurf=None, no_init=False):
        self.texid = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texid)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        if no_init:
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_FLOAT, None)
        else:
            if pgsurf is not None:
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, pygame.surfarray.pixels2d(pgsurf))
            else:
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_INT, np.full(width * height, 255, dtype='u'))
        self.w = w
        self.h = h
        self.last_unit = None

    def bind(self):
        self.bindtexunit()

    def bindtexunit(self, unit=None):
        if unit is not None:
            glActiveTexture(unit)
        self.last_unit = unit
        glBindTexture(GL_TEXTURE_2D, self.texid)

    def unbind(self):
        if self.last_unit is not None:
            glActiveTexture(unit)
        glBindTexture(GL_TEXTURE_2D, None)

    def clear(self, color=0xFFFFFFFF):
        glBindTexture(GL_TEXTURE_2D, self.texid)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_INT, np.full(width * height, color, dtype='u'))


class TextureSet2D:
    def __init__(self, w, h, frames, pgsurf=None, no_init=False):
        self.texid = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D_ARRAY, self.texid)
        glTexParameterf(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameterf(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameterf(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        if no_init:
            glTexImage3D(GL_TEXTURE_2D_ARRAY, 0, GL_RGBA, w, h, frames, 0, GL_RGBA, GL_FLOAT, None)
        else:
            if pgsurf is not None:
                glTexImage3D(GL_TEXTURE_2D_ARRAY, 0, GL_RGBA, w, h, frames, 0, GL_RGBA, GL_UNSIGNED_BYTE, pygame.surfarray.pixels2d(pgsurf))
            else:
                glTexImage3D(GL_TEXTURE_2D_ARRAY, 0, GL_RGBA, w, h, frames, 0, GL_RGBA, GL_UNSIGNED_INT, np.full(width * height, 255, dtype='u'))
        self.w = w
        self.h = h
        self.last_unit = None
        self.is_context = False

    def bind(self):
        self.bindtexunit()

    def bindtexunit(self, unit=None):
        if unit is not None:
            glActiveTexture(unit)
        self.last_unit = unit
        glBindTexture(GL_TEXTURE_2D_ARRAY, self.texid)

    def unbind(self):
        if self.last_unit is not None:
            glActiveTexture(unit)
        glBindTexture(GL_TEXTURE_2D_ARRAY, None)

    def clear(self, color=0xFFFFFFFF):
        glBindTexture(GL_TEXTURE_2D_ARRAY, self.texid)
        glTexImage3D(GL_TEXTURE_2D_ARRAY, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_INT, np.full(width * height, color, dtype='u'))

    def __enter__(self):
        self.bindtexunit()
        self.is_context = True
        return self

    def set_image(self, idx, data):
        if not self.is_context:
            raise RuntimeError("set_image must be used with 'with' syntax.")
        glTexSubImage3D(GL_TEXTURE_2D_ARRAY, 0, 0, 0, idx, self.w, self.h, 1, GL_RGBA, GL_UNSIGNED_INT, data)

    def __exit__(self, type, value, traceback):
        self.unbind()
        self.is_context = False
