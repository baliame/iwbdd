from .pygame_oo.game_shaders import GSHp
from .pygame_oo.shader import Mat4, Vec4, IntArray, Vec4Array, Vec2Array, Vec2
from OpenGL.GL import *
import numpy as np
from .pygame_oo.window import Window
from OpenGL.arrays.vbo import VBO
from .pygame_oo import logger


class FX:
    fx_prog = None

    def __init__(self, wnd):
        self.vbo = VBO(np.array([0, 0, 1, 0, 0, 1, 1, 1], dtype='f'))
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        self.vbo.bind()
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, self.vbo)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 0, self.vbo)
        glEnableVertexAttribArray(0)
        glEnableVertexAttribArray(1)
        glBindVertexArray(0)
        wnd.use_game_viewport()
        self.model = Mat4.scaling(wnd.width(), wnd.height())
        self.renders = 0

    def setup_uniforms(self, prog):
        pass

    def apply(self):
        if self.__class__.fx_prog is not None:
            self.renders = (self.renders + 1) % 36000
            with GSHp(self.__class__.fx_prog) as prog:
                Window.instance.setup_render(prog)
                prog.uniform('model', self.model)
                self.setup_uniforms(prog)
                glBindVertexArray(self.vao)
                glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
                logger.log_draw()
                glBindVertexArray(0)


class Darkroom(FX):
    fx_prog = "GSHP_fx_darkroom"
    instance = None

    def __init__(self, wnd, intensity=100.0):
        super().__init__(wnd)
        self.light_sources = [{"enabled": False, "location": Vec2(0, 0), "color": Vec4(0, 0, 0, 0)} for i in range(10)]
        self.intensity = intensity

    def setup_uniforms(self, prog):
        prog.uniform('lightSourceOn', IntArray([1 if d["enabled"] else 0 for d in self.light_sources]))
        prog.uniform('lightSourceColors', Vec4Array([d["color"] for d in self.light_sources]))
        prog.uniform('lightSourceLocs', Vec2Array([d["location"] for d in self.light_sources]))
        prog.uniform('fullIntensityRadius', float(self.intensity))

    def reset(self):
        for i in range(10):
            self.disable_light_source(i)

    def disable_light_source(self, i):
        self.light_sources[i]["enabled"] = False

    def set_light_source(self, i, loc, color):
        self.light_sources[i]["enabled"] = True
        self.light_sources[i]["location"] = loc
        self.light_sources[i]["color"] = color


class HSV_Rotator(FX):
    instance = None
    fx_prog = "GSHP_fx_hsv_rotate"

    def setup_uniforms(self, prog):
        prog.uniform('t', self.renders)


class Vertical_Sine_Distortion(FX):
    instance = None
    fx_prog = "GSHP_fx_vertical_sine"

    def setup_uniforms(self, prog):
        prog.uniform('t', self.renders)


def init_fx():
    Darkroom.instance = Darkroom(Window.instance)
    HSV_Rotator.instance = HSV_Rotator(Window.instance)
    Vertical_Sine_Distortion.instance = Vertical_Sine_Distortion(Window.instance)


ApplicableFXes = [Darkroom, HSV_Rotator]
