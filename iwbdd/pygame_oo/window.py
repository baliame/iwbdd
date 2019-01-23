import pygame
from OpenGL.GL import *
import glfw
from .framebuf import Framebuffer
from .shader import Mat4


class Window:
    instance = None

    def __init__(self, w, h, title="pygame window"):
        if Window.instance is not None:
            raise RuntimeError("Window must be a singleton.")
        self.x = 0
        self.y = 0
        self.w = w
        self.h = h
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, 3)
        self.glw = glfw.create_window(w, h, title, None, None)
        #self.display = pygame.display.set_mode((w, h), pygame.DOUBLEBUF | pygame.OPENGL)
        #pygame.display.set_caption(title)
        self.vao = glGenVertexArray(1)
        glBindVertexArray(self.vao)
        self.fbo = Framebuffer(w, h)
        self.view = Mat4.scaling(1.0 / w, 1.0 / h, 1)

    def update(self):
        pygame.display.update()

    def create_scaler(self, dest_w, dest_h):
        return WindowScaler(self, dest_w, dest_h)

    def scale_event(self, ev):
        return ev

    def get_parent(self):
        return None

    def setup_render(self, prog):
        self.fbo.new_render_pass()
        self.fbo.bindtexunit(1)
        prog.uniform('view', self.view)
        prog.uniform('wscale', self.w)
        prog.uniform('hscale', self.h)

class WindowScaler:
    def __init__(self, window, dest_w, dest_h):
        self.display = pygame.Surface((dest_w, dest_h))
        self.w = dest_w
        self.h = dest_h
        self.window = window
        self.mult_x = dest_w / window.w
        self.mult_y = dest_h / window.h

    def update(self):
        pygame.transform.smoothscale(self.display, (self.window.w, self.window.h), self.window.display)

    def scale_event(self, ev):
        ev.pos = [int(ev.pos[0] * self.mult_x), int(ev.pos[1] * self.mult_y)]
        return ev

    def get_parent(self):
        return self.window


class WindowSection(Window):
    def __init__(self, window, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.window = window
        self.display = pygame.Surface((w, h))

    def update(self):
        self.window.display.blit(self.display, (self.x, self.y))

    def scale_event(self, ev):
        return ev

    def get_parent(self):
        return self.window
