from .common import eofc_read, lerp
import struct
import pygame
from io import BytesIO
from OpenGL.GL import *
from PIL import Image
from .pygame_oo.texture import Texture2D
from .pygame_oo.game_shaders import GSHp
from .pygame_oo.shader import Mat4, Vec4
from .pygame_oo.window import Window
from .pygame_oo import logger
import numpy as np
from OpenGL.arrays.vbo import VBO

# DATA FORMAT: (HEADER, [BACKGROUND])
# HEADER: (<4> Number of backgrounds)
# BACKGROUND: (HEADER, RAW DATA)
# BACKGROUND HEADER: (<4> Background ID, <4> Raw data length)
# BACKGROUND RAW DATA: raw PNG
def read_backgrounds(source):
    with open(source, 'rb') as f:
        background_cnt = struct.unpack('<L', eofc_read(f, 4))[0]
        for i in range(background_cnt):
            b = Background(f)
            Background.backgrounds[b.background_id] = b


def pack_backgrounds_from_files(files, dest):
    with open(dest, 'wb') as d:
        d.write(struct.pack('<L', len(files)))
        for ts_id in files:
            d.write(struct.pack('<L', ts_id))
            with open(files[ts_id], 'rb') as f:
                data = f.read()
                d.write(struct.pack('<L', len(data)))
                d.write(data)


class Background:
    backgrounds = {}
    draw_surface = None
    draw_surface_w = 0
    draw_surface_h = 0
    err = (255, 255, 255)
    identity = None
    draw_arrays = None
    uv_arrays = None

    @staticmethod
    def find(bid):
        if bid in Background.backgrounds:
            return Background.backgrounds[bid]
        return None

    def __init__(self, reader=None):
        if Background.identity is None:
            Background.identity = Mat4()
            Background.draw_arrays = VBO(np.array([0, 0, 1, 0, 0, 1, 1, 1], dtype='f'))
            Background.uv_arrays = VBO(np.array([0, 0, 1, 0, 0, 1, 1, 1], dtype='f'))
        self.background_id = 0
        self.image_surface = None
        if reader is not None:
            self.read_background_data(reader)

    def read_background_data(self, reader):
        self.background_id = struct.unpack('<L', eofc_read(reader, 4))[0]
        data_len = struct.unpack('<L', eofc_read(reader, 4))[0]
        raw_png = eofc_read(reader, data_len)
        img_data = Image.open(BytesIO(raw_png)).transpose(Image.FLIP_TOP_BOTTOM)
        bands = img_data.getbands()
        self.tex = Texture2D(img_data.width, img_data.height, arr=np.frombuffer(img_data.tobytes(), dtype=np.uint8), arr_type=GL_UNSIGNED_BYTE, arr_colors=GL_RGB if len(bands) == 3 else GL_RGBA, dest_colors=GL_RGBA)

    def draw(self, x, y, w, h):
        with GSHp("GSHP_blit") as prog:
            Window.instance.setup_render(prog)
            prog.uniform('model', Mat4.scaling(w, h, 1))
            prog.uniform('colorize', Vec4(1.0, 1.0, 1.0, 1.0))
            self.tex.bindtexunit(1)
            glEnableVertexAttribArray(0)
            glEnableVertexAttribArray(1)
            self.draw_arrays.bind()
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, self.draw_arrays)
            self.uv_arrays.bind()
            glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 0, self.uv_arrays)
            glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
            logger.log_draw()
            glDisableVertexAttribArray(0)
            glDisableVertexAttribArray(1)
