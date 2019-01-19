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
from OpenGL.GL import *


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
        self.draw_arrays = np.array([0, 0, Tileset.TILE_W, 0, 0, Tileset.TILE_H, Tileset.TILE_W, Tileset.TILE_H], dtype='f')
        self.uv_arrays = np.array([0, 0, 1, 0, 0, 1, 1, 1], dtype='f')
        if reader is not None:
            self.read_tileset_data(reader)

    def read_tileset_data(self, reader):
        self.tileset_id = struct.unpack('<L', eofc_read(reader, 4))[0]
        data_len = struct.unpack('<L', eofc_read(reader, 4))[0]
        raw_png = eofc_read(reader, data_len)
        img_data = Image.open(BytesIO(raw_png)).transpose(Image.FLIP_TOP_BOTTOM)
        self.tiles_w = round(img_data.width / Tileset.TILE_W)
        self.tiles_h = round(img_data.height / Tileset.TILE_H)

        # self.image_surface = pygame.image.load(BytesIO(raw_png)).convert_alpha()
        xf = self.tiles_w
        self.stride = xf
        yf = self.tiles_h
        self.tex = TextureSet2D(Tileset.TILE_W, self.cell_h, xf * yf)
        with self.tex as t:
            idx = 0
            for y in range(yf):
                sy = img_data.height - y * self.cell_h
                for x in range(xf):
                    sx = x * self.cell_w
                    img = img_data.crop((sx, sy - Tileset.TILE_H, sx + Tileset.TILE_H, sy))
                    t.set_image(idx, np.frombuffer(img.tobytes(), dtype=np.uint32))
                    idx += 1

    # def draw_to(self, tiles_x, tiles_y, tiles_w, tiles_h, dest_surf, dest_area):
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
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, self.draw_arrays)
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, self.uv_arrays)
            glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
            glDisableVertexAttribArray(0)
            glDisableVertexAttribArray(1)
#        if Tileset.draw_surface is None or Tileset.draw_surface_w != tiles_w or Tileset.draw_surface_h != tiles_h:
#            Tileset.draw_surface_w = tiles_w
#            Tileset.draw_surface_h = tiles_h
#            Tileset.draw_surface = pygame.Surface((tiles_w * Tileset.TILE_W, tiles_h * Tileset.TILE_H))
#        Tileset.draw_surface.fill(0)
#        if tiles_x + tiles_w > self.tiles_w:
#            tiles_w = self.tiles_w - tiles_x
#        if tiles_y + tiles_h > self.tiles_h:
#            tiles_h = self.tiles_h - tiles_y
#        Tileset.draw_surface.blit(self.image_surface, (0, 0), pygame.Rect(tiles_x * Tileset.TILE_W, tiles_y * Tileset.TILE_H, (tiles_x + tiles_w) * Tileset.TILE_W, (tiles_y + tiles_h) * Tileset.TILE_H))
#        dest_surf.blit(Tileset.draw_surface, dest_area)
