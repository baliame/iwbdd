from .common import eofc_read
import struct
import pygame
from io import BytesIO
import os.path as path
from pygame.locals import BLEND_RGB_MULT


# DATA FORMAT: (HEADER, [SPRITESHEETS])
# HEADER: (<4> Number of spritesheets)
# SPRITESHEET: (HEADER, RAW DATA)
# SPRITESHEET HEADER: (<4> Spritesheet ID, <4> Sprite cell width, <4> Sprite cell height, <4> Raw data length)
# SPRITESHEET RAW DATA: raw PNG
def read_spritesheets(source):
    with open(source, 'rb') as f:
        tileset_cnt = struct.unpack('<L', eofc_read(f, 4))[0]
        for i in range(tileset_cnt):
            t = Spritesheet(f)
            Spritesheet.spritesheets[t.spritesheet_id] = t


def pack_spritesheets_from_files(files, dest):
    with open(dest, 'wb') as d:
        d.write(struct.pack('<L', len(files)))
        for ss_id in files:
            fn = path.basename(files[ss_id])
            meta = fn.split('.')[0].split('-')
            try:
                w = int(meta[1])
                h = int(meta[2])
            except Exception:
                print("Filename must be SHEETNAME-WIDTH-HEIGHT.{0}".format('.'.join(fn.split('.')[1:])))
                raise
            d.write(struct.pack('<L', ss_id))
            d.write(struct.pack('<L', w))
            d.write(struct.pack('<L', h))
            with open(files[ss_id], 'rb') as f:
                data = f.read()
                d.write(struct.pack('<L', len(data)))
                d.write(data)


class Spritesheet:
    spritesheets = {}

    @staticmethod
    def find(tid):
        if tid in Spritesheet.spritesheets:
            return Spritesheet.spritesheets[tid]
        return None

    def __init__(self, reader=None):
        self.spritesheet_id = 0
        self.image_surface = None
        self.image_surface_colored = None
        self.cell_w = 0
        self.cell_h = 0
        self.applied_color = None
        self._applied_color = None
        if reader is not None:
            self.read_spritesheet_data(reader)

    def read_spritesheet_data(self, reader):
        self.spritesheet_id = struct.unpack('<L', eofc_read(reader, 4))[0]
        self.cell_w = struct.unpack('<L', eofc_read(reader, 4))[0]
        self.cell_h = struct.unpack('<L', eofc_read(reader, 4))[0]
        data_len = struct.unpack('<L', eofc_read(reader, 4))[0]
        raw_png = eofc_read(reader, data_len)
        self.image_surface = pygame.image.load(BytesIO(raw_png)).convert_alpha()

    def check_applied_color(self):
        if self.image_surface_colored is None or self.applied_color != self._applied_color:
            self.image_surface_colored = self.image_surface.copy()
            if self.applied_color is not None:
                temp = pygame.Surface(self.image_surface_colored.get_size())
                temp.fill(self.applied_color)
                self.image_surface_colored.blit(temp, (0, 0), None, BLEND_RGB_MULT)
            self._applied_color = self.applied_color

    def draw_cell_to(self, target, x, y, draw_x, draw_y):
        self.check_applied_color()
        target.blit(self.image_surface_colored, (draw_x, draw_y), pygame.Rect(x * self.cell_w, y * self.cell_h, self.cell_w, self.cell_h))
