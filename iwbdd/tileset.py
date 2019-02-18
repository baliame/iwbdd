from .common import eofc_read
import struct
from io import BytesIO
import numpy as np
from PIL import Image
from .pygame_oo.texture import TextureSet2D, Texture2D
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
    collision_tileset = 3
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
        self.uv_arrays = VBO(np.array([0, 0, 1, 0, 0, 1, 1, 1], dtype='f'))
        self.wh_arrays = VBO(np.array([0, 0, 1, 0, 0, 2, 1, 2], dtype='f'))
        self.vao = glGenVertexArrays(1)
        self.editor_display = (-1, -1, -1, -1)
        self.editor_display_tileids = None
        glBindVertexArray(self.vao)
        self.unit_arrays.bind()
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, self.unit_arrays)
        self.uv_arrays.bind()
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 0, self.uv_arrays)
        glEnableVertexAttribArray(0)
        glEnableVertexAttribArray(1)
        glBindVertexArray(0)
        if reader is not None:
            self.read_tileset_data(reader)
        if self.tileset_id == Tileset.collision_tileset:
            Tileset.collision_tileset = self

    def set_editor_display(self, x, y, w, h):
        if self.editor_display != (x, y, w, h):
            self.editor_display = (x, y, w, h)
            self.editor_display_tileids = Texture2D(w, h, np.zeros((h, w), dtype=np.uint32), arr_type=GL_UNSIGNED_INT, arr_colors=GL_RED_INTEGER, dest_colors=GL_R32UI, magf=GL_NEAREST, minf=GL_NEAREST)
            tile_idx = np.zeros((h, w), dtype=np.uint32)
            for cy in range(y, y + h):
                for cx in range(x, x + w):
                    if cx >= self.tiles_w or cy >= self.tiles_h or cx < 0 or cy < 0:
                        tile_idx[h - (cy - y + 1)][cx - x] = -1
                    else:
                        tile_idx[h - (cy - y + 1)][cx - x] = cx + cy * self.stride
            self.editor_display_tileids.set_image(tile_idx, GL_UNSIGNED_INT, GL_RED_INTEGER, dest_colors=GL_R32UI, debug=True)
        return self.editor_display_tileids

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
                sy = img_data.height - (y + 1) * Tileset.TILE_H
                for x in range(xf):
                    sx = x * Tileset.TILE_W
                    img = img_data.crop((sx, sy, sx + Tileset.TILE_W, sy + Tileset.TILE_H))
                    t.set_image(idx, np.frombuffer(img.tobytes(), dtype=np.uint8), data_colors=GL_RGB if len(bands) == 3 else GL_RGBA, data_type=GL_UNSIGNED_BYTE)
                    idx += 1

    def draw_to(self, x, y, draw_x, draw_y, w=None, h=None):
        with GSHp('GSHP_render_sheet') as prog:
            Window.instance.setup_render(prog)
            render_loc = self.model * Mat4.scaling(Tileset.TILE_W if w is None else w, Tileset.TILE_H if h is None else h).translate(draw_x, draw_y)
            prog.uniform('colorize', self.vec_buf)
            tex_idx = float(x + self.stride * y)
            prog.uniform('tex_idx', tex_idx)
            prog.uniform('model', render_loc)
            self.tex.bindtexunit(0)
            glBindVertexArray(self.vao)
            glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
            logger.log_draw()
            glBindVertexArray(0)

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
            glBindVertexArray(self.vao)
            glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
            logger.log_draw()
            glBindVertexArray(0)

    def draw_as_collision(self, x, y, draw_w, draw_h, transparency_tex, tileids_tex):
        with GSHp('GSHP_render_terrain_no_blend') as prog:
            Window.instance.setup_render(prog)
            prog.uniform('model', Mat4.scaling(draw_w, draw_h, 1))
            prog.uniform('tile_w', float(Tileset.TILE_W))
            prog.uniform('tile_h', float(Tileset.TILE_H))
            self.tex.bindtexunit(0)
            transparency_tex.bindtexunit(1)
            tileids_tex.bindtexunit(2)
            glBindVertexArray(self.vao)
            glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
            logger.log_draw()
            glBindVertexArray(0)
