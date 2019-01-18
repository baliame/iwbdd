import numpy as np
from .common import eofc_read
import struct
import pygame
from io import BytesIO
import os.path as path
from pygame.locals import BLEND_RGB_MULT
from PIL import Image
from .pygame_oo.texture import TextureSet2D
from .pygame_oo.game_shaders import GSH

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
            Spritesheet.spritesheets_byname[t.spritesheet_name.decode('ascii')] = t


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
            d.write(struct.pack('<L', len(fn)))
            d.write(fn.encode('ascii', 'replace'))
            d.write(struct.pack('<L', w))
            d.write(struct.pack('<L', h))
            with open(files[ss_id], 'rb') as f:
                data = f.read()
                d.write(struct.pack('<L', len(data)))
                d.write(data)


class Spritesheet:
    spritesheets = {}
    spritesheets_byname = {}

    @staticmethod
    def find(tid):
        if tid in Spritesheet.spritesheets:
            return Spritesheet.spritesheets[tid]
        return None

    def __init__(self, reader=None):
        self.spritesheet_id = 0
        self.spritesheet_name = ""
        self.image_surface = None
        self.variants = {}
        self.cell_w = 0
        self.cell_h = 0
        self.variant_color = None
        self.variant_alpha = 255
        self.variant_downscale = 1
        if reader is not None:
            self.read_spritesheet_data(reader)

    def precache_variant(self, variant_color=None, variant_alpha=255, variant_downscale=1):
        key = (variant_color, variant_alpha, variant_downscale)
        if key in self.variants:
            return
        base = self.variants[(None, 255, 1)].copy()
        if variant_color is not None:
            temp = pygame.Surface(base.get_size())
            temp.fill(variant_color)
            base.blit(temp, (0, 0), None, BLEND_RGB_MULT)
        if variant_alpha < 255:
            sa = pygame.surfarray.pixels_alpha(base)
            sa[sa > variant_alpha] = variant_alpha
        if variant_downscale != 1:
            src_size = base.get_size()
            dest_size = (int(src_size[0] / variant_downscale), int(src_size[1] / variant_downscale))
            base = pygame.transform.scale(base, dest_size)
        self.variants[key] = base

    def read_spritesheet_data(self, reader):
        self.spritesheet_id = struct.unpack('<L', eofc_read(reader, 4))[0]
        spritesheet_name_len = struct.unpack('<L', eofc_read(reader, 4))[0]
        self.spritesheet_name = eofc_read(reader, spritesheet_name_len)
        self.cell_w = struct.unpack('<L', eofc_read(reader, 4))[0]
        self.cell_h = struct.unpack('<L', eofc_read(reader, 4))[0]
        data_len = struct.unpack('<L', eofc_read(reader, 4))[0]
        raw_png = eofc_read(reader, data_len)
        # self.image_surface = pygame.image.load(BytesIO(raw_png)).convert_alpha()
        img_data = Image.open(BytesIO(raw_png)).transpose(Image.FLIP_TOP_BOTTOM)
        xf = round(img_data.width / self.cell_w)
        self.stride = xf
        yf = round(img_data.height / self.cell_h)
        self.tex = TextureSet2D(self.cell_w, self.cell_h, xf * yf)
        with self.tex as t:
            idx = 0
            for y in range(yf):
                sy = img_data.height - y * self.cell_h
                for x in range(xf):
                    sx = x * self.cell_w
                    img = np.array(img_data.crop((sx, sy - self.cell_h, sx + self.cell_w, sy)).getdata(), dtype='u')
                    t.set_image(idx, np.frombuffer(img.tobytes(), dtype=np.uint32))
                    idx += 1
        # self.variants[(None, 255, 1)] = self.image_surface

    def draw_cell_to(self, target, x, y, draw_x, draw_y):
        variant_scale = 1 / self.variant_downscale
        variant_key = (self.variant_color, self.variant_alpha, self.variant_downscale)
        if variant_key not in self.variants:
            self.precache_variant(self.variant_color, self.variant_alpha, self.variant_downscale)
        target.blit(self.variants[variant_key], (draw_x, draw_y), pygame.Rect(int(x * self.cell_w * variant_scale), int(y * self.cell_h * variant_scale), int(self.cell_w * variant_scale), int(self.cell_h * variant_scale)))

    def make_hitbox(self, cell_x, cell_y, variant_downscale=1, alpha_threshold=1):
        temp = self.variant_downscale
        self.variant_downscale = variant_downscale
        vs = 1 / variant_downscale
        surf = pygame.Surface((int(self.cell_w * vs), int(self.cell_h * vs)), flags=pygame.SRCALPHA)
        self.draw_cell_to(surf, cell_x, cell_y, 0, 0)
        sa = pygame.surfarray.array_alpha(surf)
        cond = np.nonzero(sa)
        rmin = np.min(cond[0])
        rmax = np.max(cond[0])
        cmin = np.min(cond[1])
        cmax = np.max(cond[1])
        ox = -rmin
        oy = -cmin
        hitbox = sa[rmin:rmax, cmin:cmax]
        hitbox[hitbox < alpha_threshold] = 0
        hitbox[hitbox > 0] = 1
        self.variant_scale = temp
        return (hitbox, ox, oy)
