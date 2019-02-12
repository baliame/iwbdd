from enum import IntEnum, auto
import struct
from .background import Background
from .tileset import Tileset
from .common import eofc_read, is_reader_stream, CollisionTest, COLLISIONTEST_PREVENTS_MOVEMENT, SCREEN_SIZE_W, SCREEN_SIZE_H, COLLISIONTEST_COLORS
from .object_importer import read_object
from .pygame_oo.window import Window
from .pygame_oo.texture import Texture2D
from .pygame_oo.framebuf import Framebuffer
import copy
from OpenGL.GL import *
import numpy as np


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
    CONVEYOR_EAST_SINGLE_SPEED = 15
    CONVEYOR_NORTH_SINGLE_SPEED = 16
    CONVEYOR_WEST_SINGLE_SPEED = 17
    CONVEYOR_SOUTH_SINGLE_SPEED = 18
    SOLID_HALF_LEFT = 19
    SOLID_HALF_RIGHT = 20
    BOSSFIGHT_INIT_TRIGGER = 21
    SOLID_BEAM_UPRIGHT_PART_1 = 22
    SOLID_BEAM_UPRIGHT_PART_2 = 23
    SOLID_BEAM_UPLEFT_PART_1 = 24
    SOLID_BEAM_UPLEFT_PART_2 = 25
    COLLISION_TYPE_COUNT = auto()


class Layer(IntEnum):
    FOREGROUND = 0
    BACKGROUND_1 = 1
    BACKGROUND_2 = 2
    LAYER_COUNT = auto()


LayerNames = {
    Layer.FOREGROUND: "foreground",
    Layer.BACKGROUND_1: "background 1",
    Layer.BACKGROUND_2: "background 2",
}

LayerDrawOrder = [Layer.BACKGROUND_2, Layer.BACKGROUND_1, Layer.FOREGROUND]

COLLISIONTEST_ALL_FLAGS = CollisionTest.SOLID | CollisionTest.DEADLY | CollisionTest.TRANSITION_EAST | CollisionTest.TRANSITION_NORTH | CollisionTest.TRANSITION_WEST | CollisionTest.TRANSITION_SOUTH | CollisionTest.BOSSFIGHT_INIT_TRIGGER
COLLISIONTEST_PREVENTS_SIDE_GRAVITY = CollisionTest.CONVEYOR_SOUTH_SINGLE_SPEED | CollisionTest.CONVEYOR_NORTH_SINGLE_SPEED
COLLISIONTEST_TRANSITIONS = CollisionTest.TRANSITION_EAST | CollisionTest.TRANSITION_NORTH | CollisionTest.TRANSITION_SOUTH | CollisionTest.TRANSITION_WEST


class Screen:
    SCREEN_W = 42
    SCREEN_H = 32

    collision_test_flags = {
        0xFF0000: CollisionTest.DEADLY,
        0xFE0000: CollisionTest.BOSS,
        0x0000FF: CollisionTest.SOLID,
        0x008000: CollisionTest.CONVEYOR_EAST_SINGLE_SPEED,
        0x008100: CollisionTest.CONVEYOR_NORTH_SINGLE_SPEED,
        0x008200: CollisionTest.CONVEYOR_WEST_SINGLE_SPEED,
        0x008300: CollisionTest.CONVEYOR_SOUTH_SINGLE_SPEED,
        0x000080: CollisionTest.SAVE_TILE,
        0x800000: CollisionTest.LENS,
        0x808000: CollisionTest.BOSSFIGHT_INIT_TRIGGER,
    }

    CollisionBuffer = None

    def __init__(self, world, tile_data=None):
        self.world = world
        self.version = 1
        self.screen_id = None
        self.pre_rendered_layer = None
        self.pre_rendered_unscaled = None
        self.pre_rendered = None
        self.background = None
        self.dirty = True
        self.dirty_collisions = True
        self.transitions = (0, 0, 0, 0)
        self.flags = 0
        tile_tuple = tuple([0 for i in range(Layer.LAYER_COUNT * 2 + 1)])
        self.tiles = [[tile_tuple for x in range(Screen.SCREEN_W)] for y in range(Screen.SCREEN_H)]
        self.objects = []
        self.bound_objects = []
        self.savestate_objects = []
        self.gravity = (0, 0.4)
        self.jump_frames = 22
        self.objects_dirty = True
        self.tileids = {}
        for layer in range(Layer.LAYER_COUNT):
            self.tileids[layer] = Texture2D(Screen.SCREEN_W, Screen.SCREEN_H, np.zeros((Screen.SCREEN_H, Screen.SCREEN_W), dtype=np.uint32), arr_type=GL_UNSIGNED_INT, arr_colors=GL_RED_INTEGER, dest_colors=GL_R32UI, magf=GL_NEAREST, minf=GL_NEAREST)
        if tile_data is not None:
            self.load_tile_data(tile_data)
        dim = (Screen.SCREEN_W * Tileset.TILE_W, Screen.SCREEN_H * Tileset.TILE_H)
        if Screen.CollisionBuffer is None:
            Screen.CollisionBuffer = Framebuffer(dim[0], dim[1], name='Screen collision buffer')
        self.collids = Texture2D(Screen.SCREEN_W, Screen.SCREEN_H, np.zeros((Screen.SCREEN_H, Screen.SCREEN_W), dtype=np.uint32), arr_type=GL_UNSIGNED_INT, arr_colors=GL_RED_INTEGER, dest_colors=GL_R32UI, magf=GL_NEAREST, minf=GL_NEAREST)
        self.terrain_collisions = Texture2D(dim[0], dim[1], np.zeros(dim[0] * dim[1] * 4, dtype='f'), arr_type=GL_FLOAT, arr_colors=GL_RGBA, dest_colors=GL_RGBA, magf=GL_NEAREST, minf=GL_NEAREST)
        self.all_collisions = Texture2D(dim[0], dim[1], np.zeros(dim[0] * dim[1] * 4, dtype='f'), arr_type=GL_FLOAT, arr_colors=GL_RGBA, dest_colors=GL_RGBA, magf=GL_NEAREST, minf=GL_NEAREST)
        self.terrain_collision_data = []

    def reset_to_initial_state(self):
        self.objects = []
        self.savestate_objects = []
        for obj in self.bound_objects:
            self.objects.append(copy.copy(obj))
            self.savestate_objects.append(copy.copy(obj))
        self.objects_dirty = True

    def reset_to_saved_state(self):
        self.objects = []
        for obj in self.savestate_objects:
            self.objects.append(copy.copy(obj))
        self.objects_dirty = True

    def save_state(self):
        self.savestate_objects = []
        for obj in self.objects:
            if obj.__class__.saveable:
                self.savestate_objects.append(copy.copy(obj))

    def write_save_to_file(self, f):
        pass

    def restore_from_saved_file(self, f):
        self.reset_to_initial_state()

    def _read_header_v1(self, reader):
        scrid = struct.unpack("<L", eofc_read(reader, 4))[0]
        tr_e = struct.unpack("<L", eofc_read(reader, 4))[0]
        tr_n = struct.unpack("<L", eofc_read(reader, 4))[0]
        tr_w = struct.unpack("<L", eofc_read(reader, 4))[0]
        tr_s = struct.unpack("<L", eofc_read(reader, 4))[0]
        background_id = struct.unpack("<L", eofc_read(reader, 4))[0]
        flags = struct.unpack("<L", eofc_read(reader, 4))[0]
        return (scrid, tr_e, tr_n, tr_w, tr_s, background_id, flags, 0, 0.2, 22, 0)

    def _read_header_v2(self, reader):
        scrid = struct.unpack("<L", eofc_read(reader, 4))[0]
        tr_e = struct.unpack("<L", eofc_read(reader, 4))[0]
        tr_n = struct.unpack("<L", eofc_read(reader, 4))[0]
        tr_w = struct.unpack("<L", eofc_read(reader, 4))[0]
        tr_s = struct.unpack("<L", eofc_read(reader, 4))[0]
        background_id = struct.unpack("<L", eofc_read(reader, 4))[0]
        flags = struct.unpack("<L", eofc_read(reader, 4))[0]
        grav_x = struct.unpack("<f", eofc_read(reader, 4))[0]
        grav_y = struct.unpack("<f", eofc_read(reader, 4))[0]
        return (scrid, tr_e, tr_n, tr_w, tr_s, background_id, flags, grav_x, grav_y, 22, 0)

    def _read_header_v3(self, reader):
        scrid = struct.unpack("<L", eofc_read(reader, 4))[0]
        tr_e = struct.unpack("<L", eofc_read(reader, 4))[0]
        tr_n = struct.unpack("<L", eofc_read(reader, 4))[0]
        tr_w = struct.unpack("<L", eofc_read(reader, 4))[0]
        tr_s = struct.unpack("<L", eofc_read(reader, 4))[0]
        background_id = struct.unpack("<L", eofc_read(reader, 4))[0]
        flags = struct.unpack("<L", eofc_read(reader, 4))[0]
        grav_x = struct.unpack("<f", eofc_read(reader, 4))[0]
        grav_y = struct.unpack("<f", eofc_read(reader, 4))[0]
        jump_frames = struct.unpack("<H", eofc_read(reader, 2))[0]
        return (scrid, tr_e, tr_n, tr_w, tr_s, background_id, flags, grav_x, grav_y, jump_frames, 0)

    def _read_header_v4(self, reader):
        scrid = struct.unpack("<L", eofc_read(reader, 4))[0]
        tr_e = struct.unpack("<L", eofc_read(reader, 4))[0]
        tr_n = struct.unpack("<L", eofc_read(reader, 4))[0]
        tr_w = struct.unpack("<L", eofc_read(reader, 4))[0]
        tr_s = struct.unpack("<L", eofc_read(reader, 4))[0]
        background_id = struct.unpack("<L", eofc_read(reader, 4))[0]
        flags = struct.unpack("<L", eofc_read(reader, 4))[0]
        grav_x = struct.unpack("<f", eofc_read(reader, 4))[0]
        grav_y = struct.unpack("<f", eofc_read(reader, 4))[0]
        jump_frames = struct.unpack("<H", eofc_read(reader, 2))[0]
        object_count = struct.unpack("<H", eofc_read(reader, 2))[0]
        return (scrid, tr_e, tr_n, tr_w, tr_s, background_id, flags, grav_x, grav_y, jump_frames, object_count)

    def _read_header_v5(self, reader):
        return self._read_header_v4(reader)

    def _read_header_v6(self, reader):
        return self._read_header_v5(reader)

    def _read_header(self, reader, legacy=False):
        if legacy:
            self.version = 1
            return self._read_header_v1(reader)
        else:
            ver = struct.unpack("<H", eofc_read(reader, 2))[0]
            self.version = ver
            if ver == 2:
                return self._read_header_v2(reader)
            elif ver == 3:
                return self._read_header_v3(reader)
            elif ver == 4:
                return self._read_header_v4(reader)
            elif ver == 5:
                return self._read_header_v5(reader)
            elif ver == 6:
                return self._read_header_v5(reader)
            else:
                raise RuntimeError("Unknown version number: {0}".format(ver))

    def _read_tile_v1(self, reader):
        ts_x = struct.unpack("<H", eofc_read(reader, 2))[0]
        ts_y = struct.unpack("<H", eofc_read(reader, 2))[0]
        collision = struct.unpack("<H", eofc_read(reader, 2))[0]
        return (ts_x, ts_y, 0, 0, 0, 0, collision)

    def _read_tile_v5(self, reader):
        ts_x = struct.unpack("<H", eofc_read(reader, 2))[0]
        ts_y = struct.unpack("<H", eofc_read(reader, 2))[0]
        decor_x = struct.unpack("<H", eofc_read(reader, 2))[0]
        decor_y = struct.unpack("<H", eofc_read(reader, 2))[0]
        collision = struct.unpack("<H", eofc_read(reader, 2))[0]
        return (ts_x, ts_y, decor_x, decor_y, 0, 0, collision)

    def _read_tile_v6(self, reader):
        ts_x = struct.unpack("<H", eofc_read(reader, 2))[0]
        ts_y = struct.unpack("<H", eofc_read(reader, 2))[0]
        decor_x = struct.unpack("<H", eofc_read(reader, 2))[0]
        decor_y = struct.unpack("<H", eofc_read(reader, 2))[0]
        decor_x_2 = struct.unpack("<H", eofc_read(reader, 2))[0]
        decor_y_2 = struct.unpack("<H", eofc_read(reader, 2))[0]
        collision = struct.unpack("<H", eofc_read(reader, 2))[0]
        return (ts_x, ts_y, decor_x, decor_y, decor_x_2, decor_y_2, collision)

    def _write_header(self, writer):
        writer.write(struct.pack("<H", 6))
        writer.write(struct.pack("<L", self.screen_id))
        writer.write(struct.pack("<L", self.transitions[0]))
        writer.write(struct.pack("<L", self.transitions[1]))
        writer.write(struct.pack("<L", self.transitions[2]))
        writer.write(struct.pack("<L", self.transitions[3]))
        writer.write(struct.pack("<L", self.background.background_id))
        writer.write(struct.pack("<L", self.flags))
        writer.write(struct.pack("<f", self.gravity[0]))
        writer.write(struct.pack("<f", self.gravity[1]))
        writer.write(struct.pack("<H", self.jump_frames))
        writer.write(struct.pack("<H", len(self.bound_objects)))

    def _write_tile(self, writer, tile):
        writer.write(struct.pack("<H", tile[0]))
        writer.write(struct.pack("<H", tile[1]))
        writer.write(struct.pack("<H", tile[2]))
        writer.write(struct.pack("<H", tile[3]))
        writer.write(struct.pack("<H", tile[4]))
        writer.write(struct.pack("<H", tile[5]))
        writer.write(struct.pack("<H", tile[6]))

    def change_tile_graphic(self, x, y, layer, new_x, new_y):
        tile = list(self.tiles[y][x])
        xid = int(layer) * 2
        yid = xid + 1
        tile[xid] = new_x
        tile[yid] = new_y
        self.tiles[y][x] = tuple(tile)

    def change_tile_collision(self, x, y, collision):
        tile = list(self.tiles[y][x])
        tile[-1] = collision
        self.tiles[y][x] = tuple(tile)

    # Data format:
    # (HEADER, [<24>[<32>TILE]])
    # HEADER: (<4> Screen ID, <4> E Transition ID, <4> N Transition ID, <4> W Transition ID, <4> S Transition ID, <4> Background ID, <4> Room shader flags)
    # TILE: (<2> Tileset X, <2> Tileset Y, <2> Collision type)
    def load_tile_data(self, tile_data):
        if is_reader_stream(tile_data):
            header = self._read_header(tile_data)
            if self.version >= 6:
                tile_read_func = self._read_tile_v6
            elif self.version >= 5:
                tile_read_func = self._read_tile_v5
            else:
                tile_read_func = self._read_tile_v1
            tiles = []
            for y in range(Screen.SCREEN_H):
                row = []
                for x in range(Screen.SCREEN_W):
                    row.append(tile_read_func(tile_data))
                tiles.append(row)
            self.screen_id = header[0]
            self.transitions = (header[1], header[2], header[3], header[4])
            self.background = Background.find(header[5])
            self.flags = header[6]
            self.tiles = tiles
            self.gravity = (header[7], header[8])
            self.jump_frames = header[9]
            for i in range(header[10]):
                obj = read_object(tile_data, self)
                self.bound_objects.append(obj)
                self.savestate_objects.append(copy.copy(obj))
        else:
            raise RuntimeError("Only readers are allowed for tile data reading.")
        self.reset_to_initial_state()

    def write_tile_data(self, target):
        self._write_header(target)
        for row in self.tiles:
            for tile in row:
                self._write_tile(target, tile)
        for i in range(len(self.bound_objects)):
            self.bound_objects[i].write_to_writer(target)

    def render_to_window(self, wnd, layer=None):
        if self.dirty:
            for l1 in range(Layer.LAYER_COUNT):
                if layer is not None and l1 != layer:
                    continue
                tile_idx = np.zeros((Screen.SCREEN_H, Screen.SCREEN_W), dtype=np.uint32)
                for y in range(Screen.SCREEN_H):
                    for x in range(Screen.SCREEN_W):
                        tx, ty = (self.tiles[y][x][2 * l1], self.tiles[y][x][1 + 2 * l1])
                        tile_idx[Screen.SCREEN_H - (y + 1)][x] = self.world.tileset.stride * ty + tx
                self.tileids[l1].set_image(tile_idx, GL_UNSIGNED_INT, GL_RED_INTEGER, dest_colors=GL_R32UI, debug=True, noresize=True)
                self.dirty = False
        self.background.draw(0, 0, wnd.w, wnd.h)
        for l2 in LayerDrawOrder:
            self.world.tileset.draw_full_screen(0, 0, wnd.w, wnd.h, wnd.fbo, self.tileids[int(l2)])

    def render_objects(self, wnd):
        for obj in self.objects:
            obj.draw(wnd)

    def render_editor_objects(self, wnd):
        for obj in self.bound_objects:
            obj.object_editor_draw(wnd)

    def render_objects_hitboxes(self, wnd):
        for obj in self.objects:
            if obj.hitbox_type in COLLISIONTEST_COLORS:
                obj.draw_as_hitbox(wnd, fbo, COLLISIONTEST_COLORS[obj.hitbox_type])

    def ensure_unscaled_collisions(self):
        if self.dirty_collisions:
            tile_idx = np.zeros((Screen.SCREEN_H, Screen.SCREEN_W), dtype=np.uint32)
            for y in range(Screen.SCREEN_H):
                for x in range(Screen.SCREEN_W):
                    collid = self.tiles[y][x][-1]
                    tile_idx[Screen.SCREEN_H - (y + 1)][x] = collid
            self.collids.set_image(tile_idx, GL_UNSIGNED_INT, GL_RED_INTEGER, dest_colors=GL_R32UI, debug=True, noresize=True)
            with Screen.CollisionBuffer as fbo:
                fbo.use_external_texture(self.terrain_collisions)
                fbo.new_render_pass(True)
                Tileset.collision_tileset.draw_as_collision(0, 0, fbo.w, fbo.h, fbo, self.collids)
            self.terrain_collisions.bindtexunit(0)
            self.terrain_collision_data = glGetTexImage(GL_TEXTURE_2D, 0, GL_RGB, GL_UNSIGNED_BYTE, outputType=list)
            self.dirty_collisions = False
            return True
        return False

    def generate_object_collisions(self):
        self.ensure_unscaled_collisions()
        if self.objects_dirty:
            with Screen.CollisionBuffer as fbo:
                glCopyImageSubData(self.terrain_collisions.texid, GL_TEXTURE_2D, 0, 0, 0, 0, self.all_collisions.texid, GL_TEXTURE_2D, 0, 0, 0, 0, self.terrain_collisions.w, self.terrain_collisions.h, 1)
                fbo.use_external_texture(self.all_collisions)
                for obj in self.objects:
                    if obj.hitbox_type in COLLISIONTEST_COLORS:
                        obj.draw_as_hitbox(Window.instance, COLLISIONTEST_COLORS[obj.hitbox_type])
            self.all_collisions.bindtexunit(0)
            self.all_collision_data = glGetTexImage(GL_TEXTURE_2D, 0, GL_RGB, GL_UNSIGNED_BYTE, outputType=list)
            self.objects_dirty = False

    def access_collision(self):
        self.generate_object_collisions()
        return self.all_collision_data

    # hitbox: (w, h)
    # coll: (flags, solid count, solid min yo, solid max yo) [E, N, W, S, overlap]
    def test_screen_collision(self, x, y, hitbox, extra_flags=None):
        x = int(x)
        y = int(y)
        w = hitbox[0]
        h = hitbox[1]
        coll = [(0, 0, -1, -1), (0, 0, -1, -1), (0, 0, -1, -1), (0, 0, -1, -1), (0, 0, -1, -1)]
        cap = COLLISIONTEST_ALL_FLAGS
        pixels = self.access_collision()
        for yo in range(h):
            cy = y + yo
            for xo in range(w):
                cx = x + xo
                sat = 0
                for cxo, cyo, idx in [(1, 0, 0), (0, -1, 1), (-1, 0, 2), (0, 1, 3), (0, 0, 4)]:
                    try:
                        if cx + cxo < 0 or cy + cyo < 0:
                            raise IndexError
                        pxb = pixels[cx + cxo][cy + cyo]
                        px = (pxb[0] << 16) + (pxb[1] << 8) + pxb[2]
                        if px in Screen.collision_test_flags or (extra_flags is not None and px in extra_flags):
                            flag = Screen.collision_test_flags[px]
                            coll[idx] = (coll[idx][0] | Screen.collision_test_flags[px], coll[idx][1], coll[idx][2], coll[idx][3])
                            if flag & COLLISIONTEST_PREVENTS_MOVEMENT:
                                cnt = coll[idx][1] + 1
                                min_yo = yo + cyo if coll[idx][2] == -1 or coll[idx][2] > yo + cyo else coll[idx][2]
                                max_yo = yo + cyo if coll[idx][3] == -1 or coll[idx][3] < yo + cyo else coll[idx][3]
                                coll[idx] = (coll[idx][0], cnt, min_yo, max_yo)
                    except IndexError:
                        flag = 0
                        if cx + cxo < 0:
                            if self.transitions[2]:
                                flag |= CollisionTest.TRANSITION_WEST
                            else:
                                flag |= CollisionTest.SOLID
                        elif cy + cyo < 0:
                            if self.transitions[1]:
                                flag |= CollisionTest.TRANSITION_NORTH
                            else:
                                flag |= CollisionTest.SOLID
                        elif cx + cxo >= SCREEN_SIZE_W:
                            if self.transitions[0]:
                                flag |= CollisionTest.TRANSITION_EAST
                            else:
                                flag |= CollisionTest.SOLID
                        elif cy + cyo >= SCREEN_SIZE_H:
                            if self.transitions[3]:
                                flag |= CollisionTest.TRANSITION_SOUTH
                            else:
                                flag |= CollisionTest.SOLID
                        coll[idx] = (coll[idx][0] | flag, coll[idx][1], coll[idx][2], coll[idx][3])
                        if flag & CollisionTest.SOLID:
                            cnt = coll[idx][1] + 1
                            min_yo = yo + cyo if coll[idx][2] == -1 or coll[idx][2] > yo + cyo else coll[idx][2]
                            max_yo = yo + cyo if coll[idx][3] == -1 or coll[idx][3] < yo + cyo else coll[idx][3]
                            coll[idx] = (coll[idx][0], cnt, min_yo, max_yo)

                    if coll[idx] == cap:
                        sat += 1
                if sat == len(coll):
                    break
            if sat == len(coll):
                break
        return coll

    def test_interactable_collision(self, ctrl, x, y, hitbox, interactable_type=CollisionTest.INTERACTABLE):
        x = int(x)
        y = int(y)
        bbw = hitbox[0]
        bbh = hitbox[1]
        lx = x + bbw - 1
        ly = y + bbh - 1
        for obj in self.objects:
            if obj.hitbox_type & interactable_type:
                obw = obj.hitbox_w
                obh = obj.hitbox_h
                olx = int(obj.x) + obw
                oly = int(obj.y) + obh
                if len(range(max(x, int(obj.x)), min(lx, olx))) and len(range(max(y, int(obj.y)), min(ly, oly))):
                    obj.interact(ctrl)

    def render_collisions_to_window(self, wnd, fbo):
        self.ensure_unscaled_collisions()
        self.terrain_collisions.screen_render(wnd, 0, 0, wnd.w, wnd.h, fbo, colorize=(1.0, 1.0, 1.0, 0.5))

    def render_all_collisions_to_window(self, wnd, fbo):
        self.generate_object_collisions()
        fbo.bind()
        self.all_collisions.screen_render(wnd, 0, 0, wnd.w, wnd.h, fbo, colorize=(1.0, 1.0, 1.0, 0.5))

    def tick(self, ctrl):
        for obj in self.objects.copy():
            obj.tick(self, ctrl)
