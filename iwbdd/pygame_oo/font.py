from PIL import Image, ImageFont, ImageDraw
from .texture import Texture2D
from collections import OrderedDict
from .game_shaders import GSHp
from .window import Window
import numpy as np
from OpenGL.GL import *
from OpenGL.arrays.vbo import VBO
from .shader import Mat4, Vec4
from . import logger


class Font:
    def __init__(self, wnd, file, size=12):
        if file is None:
            self.font = ImageFont.load_default()
        else:
            self.font = ImageFont.truetype(file, size)

        self.draw_directives = OrderedDict({})
        self.text_layer = None
        self.dirty = True
        self.wnd = wnd
        self.tex = Texture2D(wnd.w, wnd.h)

        self.unit_vbo = VBO(np.array([0, 0, 1, 0, 0, 1, 1, 1], dtype='f'))
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        self.unit_vbo.bind()
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, self.unit_vbo)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 0, self.unit_vbo)
        glEnableVertexAttribArray(0)
        glEnableVertexAttribArray(1)
        self.unit_vbo.unbind()
        glBindVertexArray(0)

    def draw(self, draw_id, text, x, y, color=(0, 0, 0, 255)):
        if draw_id in self.draw_directives:
            if self.draw_directives[draw_id] == (x, y, color, text):
                return
        self.dirty = True
        self.draw_directives[draw_id] = (x, y, color, text)

    def render(self, transparency):
        if self.dirty:
            self.text_layer = Image.new('RGBA', (self.wnd.w, self.wnd.h), (255, 255, 255, 0))
            Draw = ImageDraw.Draw(self.text_layer, 'RGBA')
            for draw_id, directive in self.draw_directives.items():
                Draw.text((directive[0], directive[1]), directive[3], directive[2], self.font)
            bands = self.text_layer.getbands()
            self.tex.set_image(np.frombuffer(self.text_layer.transpose(Image.FLIP_TOP_BOTTOM).tobytes(), dtype=np.uint8), data_type=GL_UNSIGNED_BYTE, data_colors=GL_RGB if len(bands) == 3 else GL_RGBA, dest_colors=GL_RGBA, noresize=True)
            self.dirty = False
        with GSHp('GSHP_render') as prog:
            Window.instance.setup_render(prog)
            prog.uniform('model', Mat4.scaling(self.wnd.w, self.wnd.h, 1))
            prog.uniform('colorize', Vec4(1.0, 1.0, 1.0, 1.0))
            self.tex.bindtexunit(0)
            transparency.bindtexunit(1)
            glBindVertexArray(self.vao)
            glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
            logger.log_draw()
            glBindVertexArray(0)
