from .object import Object
from OpenGL.GL import *
from OpenGL.arrays.vbo import VBO
from .pygame_oo.shader import Mat4, Vec4, Vec2
from .pygame_oo.game_shaders import GSHp
from .pygame_oo.window import Window
import numpy as np


class LightBolt(Object):
    exclude_from_object_editor = True
    velocity = 6
    saveable = False

    max_trail = 8
    vao = None
    vbo = None

    @classmethod
    def init_vao(cls):
        if cls.vao is None:
            cls.vao = glGenVertexArrays(1)
            cls.vbo = VBO(np.array([0, 0], dtype='f'))
            glBindVertexArray(cls.vao)
            cls.vbo.bind()
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, self.draw_arrays)
            glEnableVertexAttribArray(0)
            glEnableVertexAttribArray(1)
            glBindVertexArray(0)

    def __init__(self, screen, x=0, y=0, init_dict=None):
        LightBolt.init_vao()
        super().__init__(screen, x, y, init_dict)
        self.trail = []
        self.radius = 8.0
        self.color = Vec4(0, 0.5, 1.0, 1.0)

    def draw(self, wnd):
        ix = int(self.x)
        iy = int(self.y + self.hitbox_h)
        if not self.hidden:
            draw_x = ix + self._offset_x
            draw_y = iy + self._offset_y
            with GSHp('GSHP_light_spot') as prog:
                model = Mat4.translation(draw_x, Window.instance.h - draw_y)
                Window.instance.setup_render(prog)

                prog.uniform('color', self.color)
                prog.uniform('radius', self.radius)
                prog.uniform('center', Vec2(draw_x, draw_y))
                prog.uniform('model', model)

                self.tex.bindtexunit(0)
                transparency.bindtexunit(1)

                glBindVertexArray(cls.vao)
                glDrawArrays(GL_POINTS, 0, 1)
                logger.log_draw()
                glBindVertexArray(0)
