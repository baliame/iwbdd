from .common import eofc_read
import struct
import pygame
from io import BytesIO


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

    @staticmethod
    def find(bid):
        if bid in Background.backgrounds:
            return Background.backgrounds[bid]
        return None

    def __init__(self, reader=None):
        self.background_id = 0
        self.image_surface = None
        if reader is not None:
            self.read_background_data(reader)

    def read_background_data(self, reader):
        self.background_id = struct.unpack('<L', eofc_read(reader, 4))[0]
        data_len = struct.unpack('<L', eofc_read(reader, 4))[0]
        raw_png = eofc_read(reader, data_len)
        self.image_surface = pygame.image.load(BytesIO(raw_png)).convert_alpha()

    def draw_to(self, w, h, dest_surf, dest_area):
        if Background.draw_surface is None or Background.draw_surface_w != w or Background.draw_surface_h != h:
            Background.draw_surface_w = w
            Background.draw_surface_h = h
            Background.draw_surface = pygame.Surface((w, h))
        Background.draw_surface.fill(0)
        pygame.transform.smoothscale(self.image_surface, (w, h), Background.draw_surface)
        dest_surf.blit(Background.draw_surface, dest_area)
