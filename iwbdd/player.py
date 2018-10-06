from .object import Object, generate_rectangle_hitbox
from .spritesheet import Spritesheet
from .pygame_oo.main_loop import MainLoop
# import pygame
# import numpy as np


class Player(Object):
    exclude_from_object_editor = True

    def __init__(self):
        super().__init__(None)
        self.bottom_pixel = 0
        # self.hitbox = generate_rectangle_hitbox(12, self.bottom_pixel + 1)
        # self.offset_x = -6
        # self.offset_y = -9
        # self.hb_bg_w = 16
        # self.hb_bg_h = 16
        self.spritesheet = Spritesheet.spritesheets[1]
        self.movement_velocity = [0, 0]
        self.gravity_velocity = [0, 0]
        self.doublejump_available = 1
        self.doublejump_blocked = False
        self.hitboxes_cache = {}
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
        self.generate_hitboxes()
        dja = Object(None, 0, 0)
        dja.spritesheet = Spritesheet.spritesheets[2]
        dja.hidden = True
        dja.offset_x = self.offset_x
        dja.offset_y = self.offset_y
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
        self.hitbox = self.hitboxes_cache[self.states[self._state][-1]][0]
        self.offset_x = self.hitboxes_cache[self.states[self._state][-1]][1]
        self.offset_y = self.hitboxes_cache[self.states[self._state][-1]][2]

    def generate_hitboxes(self):
        hitbox_names = set()
        for statename, definition in self.states.items():
            if definition[-1] not in hitbox_names:
                hitbox_names.add(definition[-1])
        for hbname in hitbox_names:
            hb = generate_rectangle_hitbox(16, 12)
            self.hitboxes_cache[hbname] = (hb, -4, -12)
            self.bottom_pixel = 11
            # if self.states[hbname][0]:
            #     tile_coord = self.states[hbname][2][0]
            # else:
            #     tile_coord = self.states[hbname][1]
            # surf = pygame.Surface((self.spritesheet.cell_w, self.spritesheet.cell_h), flags=pygame.SRCALPHA)
            # self.spritesheet.draw_cell_to(surf, tile_coord[0], tile_coord[1], 0, 0)
            # sa = pygame.surfarray.array_alpha(surf)
            # cond = np.nonzero(sa)
            # rmin = np.min(cond[0])
            # rmax = np.max(cond[0])
            # cmin = np.min(cond[1])
            # cmax = np.max(cond[1])
            # ox = -rmin
            # oy = -cmin
            # hitbox = sa[rmin:rmax, cmin:cmax]
            # hitbox[hitbox > 0] = 1
            # self.hitboxes_cache[hbname] = (hitbox, ox, oy)
            # h = len(hitbox[0])
            # if h - 1 > self.bottom_pixel:
            #     self.bottom_pixel = h - 1

    def reset(self):
        self.movement_velocity = (0, 0)
        self.gravity_velocity = (0, 0)
        self.doublejump_available = 1
        self.cached_collision = None
        self.spritesheet.applied_color = None
        self.dead = False
        self.jump_held = False
        self.jumping = False
        self.state = "stop_right"
        self.doublejump_blocked = False

    @Object.state.setter
    def state(self, newstate):
        self._state = newstate
        self.time_accumulator = 0
        self.animation_frame = 0
        self.last_sync_stamp = MainLoop.render_sync_stamp
        self.hitbox = self.hitboxes_cache[self.states[self._state][-1]][0]
        self.offset_x = self.hitboxes_cache[self.states[self._state][-1]][1]
        self.offset_y = self.hitboxes_cache[self.states[self._state][-1]][2]

    def die(self):
        self.spritesheet.applied_color = (255, 0, 0)
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
