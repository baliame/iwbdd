from .common import eofc_read
import struct
import pygame
from io import BytesIO


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
        if reader is not None:
            self.read_tileset_data(reader)

    def read_tileset_data(self, reader):
        self.tileset_id = struct.unpack('<L', eofc_read(reader, 4))[0]
        data_len = struct.unpack('<L', eofc_read(reader, 4))[0]
        raw_png = eofc_read(reader, data_len)
        self.image_surface = pygame.image.load(BytesIO(raw_png)).convert_alpha()
        self.tiles_w = self.image_surface.get_width() / Tileset.TILE_W
        self.tiles_h = self.image_surface.get_height() / Tileset.TILE_H

    def draw_to(self, tiles_x, tiles_y, tiles_w, tiles_h, dest_surf, dest_area):
        if Tileset.draw_surface is None or Tileset.draw_surface_w != tiles_w or Tileset.draw_surface_h != tiles_h:
            Tileset.draw_surface_w = tiles_w
            Tileset.draw_surface_h = tiles_h
            Tileset.draw_surface = pygame.Surface((tiles_w * Tileset.TILE_W, tiles_h * Tileset.TILE_H))
        Tileset.draw_surface.fill(0)
        if tiles_x + tiles_w > self.tiles_w:
            tiles_w = self.tiles_w - tiles_x
        if tiles_y + tiles_h > self.tiles_h:
            tiles_h = self.tiles_h - tiles_y
        Tileset.draw_surface.blit(self.image_surface, (0, 0), pygame.Rect(tiles_x * Tileset.TILE_W, tiles_y * Tileset.TILE_H, (tiles_x + tiles_w) * Tileset.TILE_W, (tiles_y + tiles_h) * Tileset.TILE_H))
        dest_surf.blit(Tileset.draw_surface, dest_area)
