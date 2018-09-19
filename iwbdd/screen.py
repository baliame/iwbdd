from enum import IntEnum, auto
import struct
import pygame
from .background import Background
from .tileset import Tileset
from .common import eofc_read, is_reader_stream


class Collision(IntEnum):
    PASSABLE = 0
    SOLID_TILE = 1
    SOLID_HALF_DOWN = 2
    SOLID_HALF_UP = 3
    SOLID_SLOPE_UPLEFT = 4
    SOLID_SLOPE_UPRIGHT = 5
    DEADLY_TILE = 6
    DEADLY_SPIKE_UP = 7
    DEADLY_SPIKE_DOWN = 8
    DEADLY_SPIKE_LEFT = 9
    DEADLY_SPIKE_RIGHT = 10
    SOLID_HALF_UP_DEADLY_HALF_DOWN = 11
    SOLID_HALF_DOWN_DEADLY_HALF_UP = 12
    SOLID_HALF_LEFT_DEADLY_HALF_RIGHT = 13
    SOLID_HALF_RIGHT_DEADLY_HALF_LEFT = 14
    COLLISION_TYPE_COUNT = auto()


class Screen:
    SCREEN_W = 64
    SCREEN_H = 48

    collision_overlays = {
        Collision.PASSABLE: lambda tgt, x, y: True,
        Collision.SOLID_TILE: lambda tgt, x, y: pygame.draw.rect(tgt, (0, 0, 255), pygame.Rect(x, y, Tileset.TILE_W, Tileset.TILE_H)),
        Collision.SOLID_HALF_DOWN: lambda tgt, x, y: pygame.draw.rect(tgt, (0, 0, 255), pygame.Rect(x, y + Tileset.TILE_H / 2, Tileset.TILE_W, Tileset.TILE_H / 2)),
        Collision.SOLID_HALF_UP: lambda tgt, x, y: pygame.draw.rect(tgt, (0, 0, 255), pygame.Rect(x, y, Tileset.TILE_W, Tileset.TILE_H / 2)),
        Collision.SOLID_SLOPE_UPLEFT: lambda tgt, x, y: pygame.draw.polygon(tgt, (0, 0, 255), [(x, y), (x + Tileset.TILE_W - 1, y + Tileset.TILE_H - 1), (x, y + Tileset.TILE_H - 1)]),
        Collision.SOLID_SLOPE_UPRIGHT: lambda tgt, x, y: pygame.draw.polygon(tgt, (0, 0, 255), [(x + Tileset.TILE_W - 1, y), (x, y + Tileset.TILE_H - 1), (x + Tileset.TILE_W - 1, y + Tileset.TILE_H - 1)]),
        Collision.DEADLY_TILE: lambda tgt, x, y: pygame.draw.rect(tgt, (255, 0, 0), pygame.Rect(x, y, Tileset.TILE_W, Tileset.TILE_H)),
        Collision.DEADLY_SPIKE_UP: lambda tgt, x, y: pygame.draw.polygon(tgt, (255, 0, 0), [(x, y + Tileset.TILE_H - 1), (x + Tileset.TILE_W / 2 - 1, y), (x + Tileset.TILE_W / 2, y), (x + Tileset.TILE_W - 1, y + Tileset.TILE_H - 1)]),
        Collision.DEADLY_SPIKE_DOWN: lambda tgt, x, y: pygame.draw.polygon(tgt, (255, 0, 0), [(x, y), (x + Tileset.TILE_W / 2 - 1, y + Tileset.TILE_H - 1), (x + Tileset.TILE_W / 2, y + Tileset.TILE_H - 1), (x + Tileset.TILE_W - 1, y)]),
        Collision.DEADLY_SPIKE_LEFT: lambda tgt, x, y: pygame.draw.polygon(tgt, (255, 0, 0), [(x, y), (x + Tileset.TILE_W - 1, y + Tileset.TILE_H / 2 - 1), (x + Tileset.TILE_W - 1, y + Tileset.TILE_H / 2), (x, y + Tileset.TILE_H - 1)]),
        Collision.DEADLY_SPIKE_RIGHT: lambda tgt, x, y: pygame.draw.polygon(tgt, (255, 0, 0), [(x + Tileset.TILE_W - 1, y), (x, y + Tileset.TILE_H / 2 - 1), (x, y + Tileset.TILE_H / 2), (x + Tileset.TILE_W - 1, y + Tileset.TILE_H - 1)]),
        Collision.SOLID_HALF_UP_DEADLY_HALF_DOWN: lambda tgt, x, y: pygame.draw.rect(tgt, (0, 0, 255), pygame.Rect(x, y, Tileset.TILE_W, Tileset.TILE_H / 2)) and pygame.draw.rect(tgt, (255, 0, 0), pygame.Rect(x, y + Tileset.TILE_H / 2, Tileset.TILE_W, Tileset.TILE_H / 2)),
        Collision.SOLID_HALF_DOWN_DEADLY_HALF_UP: lambda tgt, x, y: pygame.draw.rect(tgt, (255, 0, 0), pygame.Rect(x, y, Tileset.TILE_W, Tileset.TILE_H / 2)) and pygame.draw.rect(tgt, (0, 0, 255), pygame.Rect(x, y + Tileset.TILE_H / 2, Tileset.TILE_W, Tileset.TILE_H / 2)),
        Collision.SOLID_HALF_LEFT_DEADLY_HALF_RIGHT: lambda tgt, x, y: pygame.draw.rect(tgt, (0, 0, 255), pygame.Rect(x, y, Tileset.TILE_W / 2, Tileset.TILE_H)) and pygame.draw.rect(tgt, (255, 0, 0), pygame.Rect(x + Tileset.TILE_W / 2 - 1, y, Tileset.TILE_W / 2, Tileset.TILE_H)),
        Collision.SOLID_HALF_RIGHT_DEADLY_HALF_LEFT: lambda tgt, x, y: pygame.draw.rect(tgt, (255, 0, 0), pygame.Rect(x, y, Tileset.TILE_W / 2, Tileset.TILE_H)) and pygame.draw.rect(tgt, (0, 0, 255), pygame.Rect(x + Tileset.TILE_W / 2 - 1, y, Tileset.TILE_W / 2, Tileset.TILE_H)),
    }

    def __init__(self, world, tile_data=None):
        self.world = world
        self.screen_id = None
        self.pre_rendered_unscaled = None
        self.pre_rendered = None
        self.background = None
        self.dirty = True
        self.dirty_collisions = True
        self.pre_rendered_unscaled_collisions = None
        self.pre_rendered_collisions = None
        self.transitions = (0, 0, 0, 0)
        self.flags = 0
        self.tiles = [[(0, 0, 0) for x in range(Screen.SCREEN_W)] for y in range(Screen.SCREEN_H)]
        self.objects = []
        if tile_data is not None:
            self.load_tile_data(tile_data)

    def _read_header(self, reader):
        scrid = struct.unpack("<L", eofc_read(reader, 4))[0]
        tr_e = struct.unpack("<L", eofc_read(reader, 4))[0]
        tr_n = struct.unpack("<L", eofc_read(reader, 4))[0]
        tr_w = struct.unpack("<L", eofc_read(reader, 4))[0]
        tr_s = struct.unpack("<L", eofc_read(reader, 4))[0]
        background_id = struct.unpack("<L", eofc_read(reader, 4))[0]
        flags = struct.unpack("<L", eofc_read(reader, 4))[0]
        return (scrid, tr_e, tr_n, tr_w, tr_s, background_id, flags)

    def _read_tile(self, reader):
        ts_x = struct.unpack("<H", eofc_read(reader, 2))[0]
        ts_y = struct.unpack("<H", eofc_read(reader, 2))[0]
        collision = struct.unpack("<H", eofc_read(reader, 2))[0]
        return (ts_x, ts_y, collision)

    def _write_header(self, writer):
        writer.write(struct.pack("<L", self.screen_id))
        writer.write(struct.pack("<L", self.transitions[0]))
        writer.write(struct.pack("<L", self.transitions[1]))
        writer.write(struct.pack("<L", self.transitions[2]))
        writer.write(struct.pack("<L", self.transitions[3]))
        writer.write(struct.pack("<L", self.background.background_id))
        writer.write(struct.pack("<L", self.flags))

    def _write_tile(self, writer, tile):
        writer.write(struct.pack("<H", tile[0]))
        writer.write(struct.pack("<H", tile[1]))
        writer.write(struct.pack("<H", tile[2]))

    # Data format:
    # (HEADER, [<24>[<32>TILE]])
    # HEADER: (<4> Screen ID, <4> E Transition ID, <4> N Transition ID, <4> W Transition ID, <4> S Transition ID, <4> Background ID, <4> Room shader flags)
    # TILE: (<2> Tileset X, <2> Tileset Y, <2> Collision type)
    def load_tile_data(self, tile_data):
        if is_reader_stream(tile_data):
            header = self._read_header(tile_data)
            tiles = []
            for y in range(Screen.SCREEN_H):
                row = []
                for x in range(Screen.SCREEN_W):
                    row.append(self._read_tile(tile_data))
                tiles.append(row)
            self.screen_id = header[0]
            self.transitions = (header[1], header[2], header[3], header[4])
            self.background = Background.find(header[5])
            self.flags = header[6]
            self.tiles = tiles
        else:
            self.screen_id = tile_data[0][0]
            self.transitions = (tile_data[0][1], tile_data[0][2], tile_data[0][3], tile_data[0][4])
            self.flags = tile_data[0][5]
            self.tiles = tile_data[1]

    def write_tile_data(self, target):
        self._write_header(target)
        for row in self.tiles:
            for tile in row:
                self._write_tile(target, tile)

    def render_to_window(self, wnd):
        win_w = wnd.display.get_width()
        win_h = wnd.display.get_height()
        resizing = False
        if self.pre_rendered is not None:
            pr_w = self.pre_rendered.get_width()
            pr_h = self.pre_rendered.get_height()
            if pr_w != win_w or pr_h != win_h:
                resizing = True
        else:
            pr_w = win_w
            pr_h = win_h
        if self.dirty or self.pre_rendered_unscaled is None:
            if self.pre_rendered_unscaled is None:
                self.pre_rendered_unscaled = pygame.Surface((1024, 768))
            self.pre_rendered_unscaled.fill(0)
            self.pre_rendered_unscaled.blit(self.background.image_surface, (0, 0))
            for y in range(Screen.SCREEN_H):
                for x in range(Screen.SCREEN_W):
                    tile = self.tiles[y][x]
                    src_x = tile[0] * Tileset.TILE_W
                    src_y = tile[1] * Tileset.TILE_H
                    dest_x = x * Tileset.TILE_W
                    dest_y = y * Tileset.TILE_H
                    self.pre_rendered_unscaled.blit(self.world.tileset.image_surface, (dest_x, dest_y), pygame.Rect(src_x, src_y, Tileset.TILE_W, Tileset.TILE_H))
            self.dirty = False
            resizing = True
        if resizing or self.pre_rendered is None:
            self.pre_rendered = pygame.Surface((win_w, win_h))
            pygame.transform.smoothscale(self.pre_rendered_unscaled, (win_w, win_h), self.pre_rendered)
        wnd.display.blit(self.pre_rendered, (0, 0))

    def render_objects(self, wnd):
        pass

    def render_collisions_to_window(self, wnd):
        win_w = wnd.display.get_width()
        win_h = wnd.display.get_height()
        resizing = False
        if self.pre_rendered_collisions is not None:
            pr_w = self.pre_rendered_collisions.get_width()
            pr_h = self.pre_rendered_collisions.get_height()
            if pr_w != win_w or pr_h != win_h:
                resizing = True
        else:
            pr_w = win_w
            pr_h = win_h
        if self.dirty_collisions or self.pre_rendered_unscaled_collisions is None:
            if self.pre_rendered_unscaled_collisions is None:
                self.pre_rendered_unscaled_collisions = pygame.Surface((1024, 768))
            self.pre_rendered_unscaled_collisions.fill((255, 255, 255))
            for y in range(Screen.SCREEN_H):
                for x in range(Screen.SCREEN_W):
                    tile = self.tiles[y][x]
                    dest_x = x * Tileset.TILE_W
                    dest_y = y * Tileset.TILE_H
                    Screen.collision_overlays[Collision(tile[2])](self.pre_rendered_unscaled_collisions, dest_x, dest_y)
            self.dirty_collisions = False
            resizing = True
        if resizing or self.pre_rendered is None:
            self.pre_rendered_collisions = pygame.Surface((win_w, win_h))
            pygame.transform.smoothscale(self.pre_rendered_unscaled_collisions, (win_w, win_h), self.pre_rendered_collisions)
            self.pre_rendered_collisions.set_alpha(128)
        wnd.display.blit(self.pre_rendered_collisions, (0, 0))
