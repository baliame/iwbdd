import pygame
from OpenGL.GL import *
import glfw
from .framebuf import Framebuffer
from .shader import Mat4


class Window:
    instance = None
    enable_log = True

    def __init__(self, w, h, title="pygame window", viewport_w=None, viewport_h=None):
        if Window.instance is not None:
            raise RuntimeError("Window must be a singleton.")
        Window.instance = self
        self.x = 0
        self.y = 0
        self.w = w
        self.h = h
        viewport_w = w if viewport_w is None else viewport_w
        viewport_h = h if viewport_h is None else viewport_h
        self.viewport_w = viewport_w
        self.viewport_h = viewport_h

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

        self.glw = glfw.create_window(w, h, title, None, None)
        glfw.make_context_current(self.glw)
        #self.display = pygame.display.set_mode((w, h), pygame.DOUBLEBUF | pygame.OPENGL)
        #pygame.display.set_caption(title)
        self.fbo = Framebuffer(w, h, self, name='Window alpha buffer')
        self.view = Mat4.scaling(2.0 / viewport_w, 2.0 / viewport_h, 1).translate(-1, -1)
        self.full_view = Mat4.scaling(2.0 / w, 2.0 / h, 1).translate(-1, -1)
        glDisable(GL_DEPTH_TEST)
        print("OpenGL: " + str(glGetString(GL_VERSION)))

    def update(self):
        pygame.display.update()

    def get_parent(self):
        return None

    def new_render(self):
        pass

    def use_game_viewport(self):
        glViewport(0, 0, self.viewport_w, self.viewport_h)

    def use_full_viewport(self):
        glViewport(0, 0, self.w, self.h)

    def setup_render(self, prog):
        if prog is None:
            raise RuntimeError('setup_render called with none prog')
        self.fbo.new_render_pass()
        self.fbo.bindtexunit(1)
        prog.uniform('view', self.view)


class WindowSection(Window):
    def __init__(self, window, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.window = window
        self.view = self.window.view
        self.fbo = self.window.fbo
        self.vao = self.window.vao

    def update(self):
        pass

    def scale_event(self, ev):
        return ev

    def get_parent(self):
        return self.window

    def setup_render(self, prog):
        self.window.setup_render()
