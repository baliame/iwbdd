from OpenGL.GL import *
import pygame


class Texture2D:
    def __init__(self, w, h, pgsurf=None, no_init=False):
        self.texid = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texid)
        if no_init:
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_FLOAT, None)
        else:
            if pgsurf is not None:
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, pygame.surfarray.pixels2d(pgsurf))
            else:
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_INT, np.full(width * height, 255, dtype='u'))
        self.w = w
        self.h = h

    def bindtexunit(self, unit):
        glActiveTexture(unit)
        glBindTexture(GL_TEXTURE_2D, self.texid)

    def clear(self, color=0xFFFFFFFF):
        glBindTexture(GL_TEXTURE_2D, self.texid)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_INT, np.full(width * height, color, dtype='u'))
