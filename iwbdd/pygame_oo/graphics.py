from PIL import Image, ImageDraw
from .texture import Texture2D
from collections import OrderedDict
from .game_shaders import GSHp
import numpy as np
from OpenGL.GL import *
from OpenGL.arrays.vbo import VBO
from .shader import Mat4, Vec4
from . import logger


class Graphics:
    def __init__(self, wnd):
        self.draw_directives = OrderedDict({})
        self.layer = None
        self.draw = None
        self.dirty = True
        self.wnd = wnd
        wnd.add_layer(self)
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

    def box(self, draw_id, x, y, w, h, color=(0, 0, 0, 255), fill=None):
        if draw_id in self.draw_directives:
            if self.draw_directives[draw_id] == (self._box, (x, y, w, h, color, fill)):
                return
        self.dirty = True
        self.draw_directives[draw_id] = (self._box, (x, y, w, h, color, fill))

    def _box(self, args):
        self.draw.rectangle((args[0], args[1], args[0] + args[2], args[1] + args[3]), args[5], args[4])

    def polygon(self, draw_id, xy, color=(0, 0, 0, 255), fill=None):
        if draw_id in self.draw_directives:
            if self.draw_directives[draw_id] == (self._polygon, (xy, color, fill)):
                return
        self.dirty = True
        self.draw_directives[draw_id] = (self._polygon, (xy, color, fill))

    def _polygon(self, args):
        self.draw.polygon(args[0], fill=args[2], outline=args[1])

    def line(self, draw_id, x0, y0, x1, y1, color=(0, 0, 0, 255)):
        if draw_id in self.draw_directives:
            if self.draw_directives[draw_id] == (self._line, (x0, y0, x1, y1, color)):
                return
        self.dirty = True
        self.draw_directives[draw_id] = (self._line, (x0, y0, x1, y1, color))

    def _line(self, args):
        self.draw.line(args[0:4], args[4])

    def clear(self, draw_id=None):
        if draw_id is None:
            if len(self.draw_directives):
                self.dirty = True
                self.draw_directives = OrderedDict({})
        else:
            if draw_id in self.draw_directives:
                del self.draw_directives[draw_id]
                self.dirty = True

    def clear_all(self):
        self.clear()

    def render(self, wnd, transparency):
        if self.dirty or self.draw is None:
            self.layer = Image.new('RGBA', (self.wnd.w, self.wnd.h), (255, 255, 255, 0))
            self.draw = ImageDraw.Draw(self.layer, 'RGBA')
            for draw_id, directive in self.draw_directives.items():
                directive[0](directive[1])
            bands = self.layer.getbands()
            self.tex.set_image(np.frombuffer(self.layer.transpose(Image.FLIP_TOP_BOTTOM).tobytes(), dtype=np.uint8), data_type=GL_UNSIGNED_BYTE, data_colors=GL_RGB if len(bands) == 3 else GL_RGBA, dest_colors=GL_RGBA, noresize=True)
            self.dirty = False
        with GSHp('GSHP_render') as prog:
            wnd.setup_render(prog)
            prog.uniform('model', Mat4.scaling(self.wnd.w, self.wnd.h, 1))
            prog.uniform('colorize', Vec4(1.0, 1.0, 1.0, 1.0))
            self.tex.bindtexunit(0)
            transparency.bindtexunit(1)
            glBindVertexArray(self.vao)
            glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
            logger.log_draw()
            glBindVertexArray(0)
