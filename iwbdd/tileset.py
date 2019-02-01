from .common import eofc_read
import struct
import pygame
from io import BytesIO
import numpy as np
from PIL import Image
from .pygame_oo.texture import TextureSet2D
from .pygame_oo.shader import Mat4, Vec4
from .pygame_oo.game_shaders import GSHp
from .pygame_oo.window import Window
from .pygame_oo import logger
from OpenGL.GL import *
from OpenGL.arrays.vbo import VBO


# DATA FORMAT: (HEADER, [TILESETS])
# HEADER: (<4> Number of tilesets)
# TILESET: (HEADER, RAW DATA)
# TILESET HEADER: (<4> Tileset ID, <4> Raw data length)
# TILESET RAW DATA: raw PNG
def read_tilesets(source):
    with open(source, 'rb') as f:
        tileset_cnt = struct.unpack('<L', eofc_read(f, 4))[0]
        for i in range(tileset_cnt):
            t = Tileset(f)
            Tileset.tilesets[t.tileset_id] = t


def pack_tilesets_from_files(files, dest):
    with open(dest, 'wb') as d:
        d.write(struct.pack('<L', len(files)))
        for ts_id in files:
            d.write(struct.pack('<L', ts_id))
            with open(files[ts_id], 'rb') as f:
                data = f.read()
                d.write(struct.pack('<L', len(data)))
                d.write(data)


class Tileset:
    tilesets = {}
    draw_surface = None
    draw_surface_w = 0
    draw_surface_h = 0
    TILE_W = 24
    TILE_H = 24
    identity = Mat4()

    @staticmethod
    def find(tid):
        if tid in Tileset.tilesets:
            return Tileset.tilesets[tid]
        return None

    def __init__(self, reader=None):
        self.tileset_id = 0
        self.image_surface = None
        self.tiles_w = 0
        self.tiles_h = 0
        self.stride = 0
        self.vec_buf = Vec4(1.0, 1.0, 1.0, 1.0)
        self.model = Mat4()
        self.unit_arrays = VBO(np.array([0, 0, 1, 0, 0, 1, 1, 1], dtype='f'))
        self.draw_arrays = VBO(np.array([0, 0, Tileset.TILE_W, 0, 0, Tileset.TILE_H, Tileset.TILE_W, Tileset.TILE_H], dtype='f'))
        self.uv_arrays = VBO(np.array([0, 0, 1, 0, 0, 1, 1, 1], dtype='f'))
        self.wh_arrays = VBO(np.array([0, 0, 1, 0, 0, 2, 1, 2], dtype='f'))
        if reader is not None:
            self.read_tileset_data(reader)

    def read_tileset_data(self, reader):
        self.tileset_id = struct.unpack('<L', eofc_read(reader, 4))[0]
        data_len = struct.unpack('<L', eofc_read(reader, 4))[0]
        raw_png = eofc_read(reader, data_len)
        img_data = Image.open(BytesIO(raw_png)).transpose(Image.FLIP_TOP_BOTTOM)
        bands = img_data.getbands()
        self.tiles_w = round(img_data.width / Tileset.TILE_W)
        self.tiles_h = round(img_data.height / Tileset.TILE_H)

        xf = self.tiles_w
        self.stride = xf
        yf = self.tiles_h
        self.tex = TextureSet2D(Tileset.TILE_W, Tileset.TILE_H, xf * yf)
        with self.tex as t:
            idx = 0
            for y in range(yf):
                sy = img_data.height - y * Tileset.TILE_H
                for x in range(xf):
                    sx = x * Tileset.TILE_W
                    img = img_data.crop((sx, sy, sx + Tileset.TILE_W, sy + Tileset.TILE_H))
                    t.set_image(idx, np.frombuffer(img.tobytes(), dtype=np.uint8), data_colors=GL_RGB if len(bands) == 3 else GL_RGBA, data_type=GL_UNSIGNED_BYTE)
                    idx += 1

    def draw_to(self, x, y, draw_x, draw_y):
        with GSHp('GSHP_render_sheet') as prog:
            Window.instance.setup_render(prog)
            render_loc = self.model * Mat4.translation(draw_x, draw_y)
            prog.uniform('colorize', self.vec_buf)
            tex_idx = float(x + self.stride * y)
            prog.uniform('tex_idx', tex_idx)
            prog.uniform('model', render_loc)
            self.tex.bindtexunit(0)
            glEnableVertexAttribArray(0)
            glEnableVertexAttribArray(1)
            self.draw_arrays.bind()
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, self.draw_arrays)
            self.uv_arrays.bind()
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, self.uv_arrays)
            glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
            logger.log_draw()
            glDisableVertexAttribArray(0)
            glDisableVertexAttribArray(1)

    def draw_full_screen(self, x, y, draw_w, draw_h, transparency_tex, tileids_tex):
        with GSHp('GSHP_render_terrain') as prog:
            Window.instance.setup_render(prog)
            prog.uniform('model', Mat4.scaling(draw_w, draw_h, 1))
            prog.uniform('tile_w', float(Tileset.TILE_W))
            prog.uniform('tile_h', float(Tileset.TILE_H))
            prog.uniform('colorize', self.vec_buf)
            self.tex.bindtexunit(0)
            transparency_tex.bindtexunit(1)
            tileids_tex.bindtexunit(2)
            glEnableVertexAttribArray(0)
            glEnableVertexAttribArray(1)
            # self.wh_arrays.set_array(np.array([0, 0, draw_w, 0, 0, draw_h, draw_w, draw_h], dtype=float))
            self.unit_arrays.bind()
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, self.unit_arrays)
            self.uv_arrays.bind()
            glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 0, self.uv_arrays)
            glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
            logger.log_draw()
            glDisableVertexAttribArray(0)
            glDisableVertexAttribArray(1)

    def blit_tileids(self, x, y, w, h, tileids_tex):
        with GSHp("GSHP_blit") as prog:
            Window.instance.setup_render(prog)
            prog.uniform('model', Mat4.scaling(w, h, 1))
            prog.uniform('colorize', Vec4(1.0, 1.0, 1.0, 1.0))
            tileids_tex.bindtexunit(1)
            glEnableVertexAttribArray(0)
            glEnableVertexAttribArray(1)
            self.draw_arrays.bind()
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, self.unit_arrays)
            self.uv_arrays.bind()
            glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 0, self.uv_arrays)
            glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
            logger.log_draw()
            glDisableVertexAttribArray(0)
            glDisableVertexAttribArray(1)

