from .object import Object, Bullet
from .spritesheet import Spritesheet
from .pygame_oo.main_loop import MainLoop
from .audio_data import Audio
from .common import eofc_read, CollisionTest
import struct
# import pygame
# import numpy as np


class Player(Object):
    exclude_from_object_editor = True
    saveable = False
    max_bullets = 4

    def __init__(self, ctrl):
        super().__init__(None)
        # self.hitbox = generate_rectangle_hitbox(12, self.bottom_pixel + 1)
        # self.offset_x = -6
        # self.offset_y = -9
        self.spritesheet = Spritesheet.spritesheets[1]
        self.movement_velocity = [0, 0]
        self.gravity_velocity = [0, 0]
        self.doublejump_available = 1
        self.doublejump_blocked = False
        self.prevent_shooting = 0
        self.jump_held = False
        self.jumping = False
        self.cached_collision = None
        self.dead = False
        self.states = {
            "stop_left": (False, (0, 1), "stop_left"),
            "stop_right": (False, (0, 0), "stop_right"),
            "moving_left": (True, 0.1, [(0, 1), (1, 1), (2, 1), (3, 1)], True, "stop_left"),
            "moving_right": (True, 0.1, [(0, 0), (1, 0), (2, 0), (3, 0)], True, "stop_right"),
        }
        dja = Object(None, 0, 0)
        dja.spritesheet = Spritesheet.spritesheets[2]
        dja.hidden = True
        dja.offset_x = -4
        dja.offset_y = -16
        dja.states = {
            "2": (False, (0, 0)),
            "3": (False, (1, 0)),
            "4": (False, (2, 0)),
            "5+": (False, (3, 0)),
        }
        dja._state = "2"
        self.attachments = {
            "extra_doublejumps": dja
        }
        self._state = "stop_right"
        self.hitbox_w = 16
        self.hitbox_h = 8
        self.bottom_pixel = self.hitbox_h - 1
        self.hitbox_type = CollisionTest.PASSABLE
        self.offset_x = -4
        self.offset_y = 0
        self.bullets = []
        self.controller = ctrl
        self.save_state = None

    def create_save_state(self):
        self.save_state = Player(None)
        self.save_state.movement_velocity = self.movement_velocity.copy()
        self.save_state.gravity_velocity = [0, 0]
        self.save_state.doublejump_available = 1 if self.doublejump_available <= 1 else self.doublejump_available
        self.save_state._state = self._state
        self.save_state.x = self.x
        self.save_state.y = self.y

    def write_save_to_file(self, f):
        f.write(struct.pack('<d', self.save_state.movement_velocity[0]))
        f.write(struct.pack('<d', self.save_state.movement_velocity[1]))
        f.write(struct.pack('<d', self.save_state.gravity_velocity[0]))
        f.write(struct.pack('<d', self.save_state.gravity_velocity[1]))
        f.write(struct.pack('<H', self.save_state.doublejump_available))
        f.write(struct.pack('<H', len(self.save_state._state)))
        f.write(self.save_state._state.encode('ascii'))
        f.write(struct.pack('<d', self.save_state.x))
        f.write(struct.pack('<d', self.save_state.y))

    def restore_from_saved_file(self, f):
        self.save_state = Player(None)
        self.save_state.movement_velocity = [struct.unpack('<d', eofc_read(f, 8))[0], struct.unpack('<d', eofc_read(f, 8))[0]]
        self.save_state.gravity_velocity = [struct.unpack('<d', eofc_read(f, 8))[0], struct.unpack('<d', eofc_read(f, 8))[0]]
        self.save_state.doublejump_available = struct.unpack('<H', eofc_read(f, 2))[0]
        sl = struct.unpack('<H', eofc_read(f, 2))[0]
        self.save_state._state = eofc_read(f, sl).decode('ascii')
        self.save_state.x = struct.unpack('<d', eofc_read(f, 8))[0]
        self.save_state.y = struct.unpack('<d', eofc_read(f, 8))[0]

    def reset_to_saved_state(self):
        ss = self.save_state
        self.reset()
        if ss is not None:
            self.movement_velocity = ss.movement_velocity.copy()
            self.gravity_velocity = ss.gravity_velocity.copy()
            self.doublejump_available = ss.doublejump_available
            self.state = ss.state
            self.x = ss.x
            self.y = ss.y
            self.save_state = ss

    def reset(self):
        self.movement_velocity = [0, 0]
        self.gravity_velocity = [0, 0]
        self.doublejump_available = 1
        self.cached_collision = None
        self.spritesheet.variant_color = None
        self.dead = False
        self.jump_held = False
        self.jumping = False
        self.state = "stop_right"
        self.doublejump_blocked = False
        self.prevent_shooting = 0
        self.destroy_bullets()
        self.save_state = None

    def fire(self):
        if len(self.bullets) >= Player.max_bullets:
            return
        facing = 1
        if self._state in ("stop_left", "moving_left"):
            facing = -1
        b = Bullet(self.screen, self.x if facing < 0 else self.x + 12, self.y + 2, {"facing": facing, "player": self})
        self.bullets.append(b)
        self.screen.objects.append(b)
        Audio.play_by_name("quack2.ogg")

    def destroy_bullets(self):
        for b in self.bullets.copy():
            b.cleanup_self()

    @Object.state.setter
    def state(self, newstate):
        self._state = newstate
        self.time_accumulator = 0
        self.animation_frame = 0
        self.last_sync_stamp = MainLoop.render_sync_stamp
        self.hitbox_w = 16
        self.hitbox_h = 8
        self.offset_x = -4
        self.offset_y = 0

    def die(self):
        self.spritesheet.variant_color = 0xFF0000
        self.dead = True

    def update_attachments(self):
        dja = self.attachments["extra_doublejumps"]
        if self.doublejump_available < 2:
            dja.hidden = True
        else:
            dja.hidden = False
            if self.doublejump_available < 3:
                dja._state = "2"
            elif self.doublejump_available < 4:
                dja._state = "3"
            elif self.doublejump_available < 5:
                dja._state = "4"
            else:
                dja._state = "5+"

    def draw(self, wnd):
        super().draw(wnd)
        self.update_attachments()
        for k, elem in self.attachments.items():
            elem.x = self.x
            elem.y = self.y
            elem.draw(wnd)
