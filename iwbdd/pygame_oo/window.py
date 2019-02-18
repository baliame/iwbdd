from OpenGL.GL import *
import glfw
from .framebuf import Framebuffer
from .shader import Mat4
from .game_shaders import GSH_init
from .font import Font
from .graphics import Graphics


class Window:
    instance = None
    enable_log = True

    def __init__(self, w, h, title="IWBDD window", viewport_w=None, viewport_h=None):
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
        GSH_init()
        self.fbo = Framebuffer(w, h, name='Window alpha buffer')
        self.layers = []
        self.font = Font(self, 'arial.ttf')
        self.graphics = Graphics(self)
        self.view = Mat4.scaling(2.0 / viewport_w, 2.0 / viewport_h, 1).translate(-1, -1)
        self.full_view = Mat4.scaling(2.0 / w, 2.0 / h, 1).translate(-1, -1)
        self.full = False
        glDisable(GL_DEPTH_TEST)
        print("OpenGL: " + str(glGetString(GL_VERSION)))
        glViewport(0, 0, self.w, self.h)
        self.use_game_viewport()

    def update(self):
        pass

    def get_parent(self):
        return None

    def new_render(self):
        pass

    def add_layer(self, layer):
        self.layers.append(layer)

    def use_game_viewport(self):
        #glViewport(0, 0, self.viewport_w, self.viewport_h)
        self.full = False

    def use_full_viewport(self):
        #glViewport(0, 0, self.w, self.h)
        self.full = True

    def setup_render(self, prog, target_fbo=None):
        if prog is None:
            raise RuntimeError('setup_render called with none prog')
        if Framebuffer.bound is not None:
            Framebuffer.bound.new_render_pass()
            Framebuffer.bound.bindtexunit(1)
        prog.uniform('view', self.full_view if self.full else self.view)

    def pre_blit(self):
        with self.fbo as fbo:
            self.use_full_viewport()
            for layer in self.layers:
                layer.render(self, fbo)

    def __enter__(self):
        self.use_full_viewport()
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.fbo.new_render_pass(True)
        self.fbo.bind()
        return self

    def __exit__(self, *args):
        self.fbo.unbind()
        self.pre_blit()
        self.fbo.blit_to_window()
        glfw.swap_buffers(self.glw)

    def width(self):
        return self.w if self.full else self.viewport_w

    def height(self):
        return self.h if self.full else self.viewport_h


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
