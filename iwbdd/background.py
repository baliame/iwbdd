from .common import eofc_read, lerp
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
    err = (255, 255, 255)

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

    def ensureds(self, w, h):
        if Background.draw_surface is None or Background.draw_surface_w != w or Background.draw_surface_h != h:
            Background.draw_surface_w = w
            Background.draw_surface_h = h
            Background.draw_surface = pygame.Surface((w, h))
            Background.draw_surface.fill(0)
            pygame.transform.smoothscale(self.image_surface, (w, h), Background.draw_surface)

    def draw_to(self, w, h, dest_surf, dest_area):
        self.ensureds(w, h)
        dest_surf.blit(Background.draw_surface, dest_area)

    def sample(self, x, y, w, h):
        x = int(x)
        y = int(y)
        self.ensureds(w, h)
        sa = pygame.surfarray.pixels3d(Background.draw_surface)
        try:
            return (sa[x, y, 0], sa[x, y, 1], sa[x, y, 2])
        except IndexError:
            return Background.err

    def bilerp(self, x, y, w, h):
        ix = int(x)
        iy = int(y)
        xt = x - ix
        yt = y - iy
        if ix < 0 or iy < 0 or xt < 0 or yt < 0:
            return (0, 0, 0)
        self.ensureds(w, h)
        sa = pygame.surfarray.pixels3d(Background.draw_surface)
        try:
            xy = (sa[ix, iy, 0], sa[ix, iy, 1], sa[ix, iy, 2])
        except IndexError as e:
            xy = Background.err
        try:
            x1y = (sa[ix + 1, iy, 0], sa[ix + 1, iy, 1], sa[ix + 1, iy, 2])
        except IndexError as e:
            x1y = Background.err
        try:
            xy1 = (sa[ix, iy + 1, 0], sa[ix, iy + 1, 1], sa[ix, iy + 1, 2])
        except IndexError as e:
            xy1 = Background.err
        try:
            x1y1 = (sa[ix + 1, iy + 1, 0], sa[ix + 1, iy + 1, 1], sa[ix + 1, iy + 1, 2])
        except IndexError as e:
            x1y1 = Background.err
        return (lerp(lerp(xy[0], x1y[0], xt), lerp(xy1[0], x1y1[0], xt), yt), lerp(lerp(xy[1], x1y[1], xt), lerp(xy1[1], x1y1[1], xt), yt), lerp(lerp(xy[2], x1y[2], xt), lerp(xy1[2], x1y1[2], xt), yt))
