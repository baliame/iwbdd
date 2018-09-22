from .pygame_oo.main_loop import render_sync_stamp
from pygame.locals import SRCALPHA
import pygame


def generate_rectangle_hitbox(w, h):
    return [[1 for x in range(w)] for y in range(h)]


# Object state
# Unanimated: (False, (sheet_cell_x, sheet_cell_y))
# Animated:   (True, animation_speed, [(sheet_cell_x, sheet_cell_y)...], looping [True|False|next animation state])

class Object:
    def __init__(self, screen, x=0, y=0):
        self.screen = screen
        self.x = x
        self.y = y
        self._offset_x = 0
        self._offset_y = 0
        self.hidden = False
        self.spritesheet = None
        self.states = {}
        self._state = ""
        self.animation_frame = 0
        self.time_accumulator = 0
        self.last_sync_stamp = render_sync_stamp
        self.hitbox = None

        self.hb_bg_w = 0
        self.hb_bg_h = 0
        self.hbds_dirty = True
        self.hitbox_draw_surface = None
        self.hitbox_draw_surface_color = None

    @property
    def offset_x(self):
        return self._offset_x

    @offset_x.setter
    def offset_x(self, value):
        self.hbds_dirty = True
        self._offset_x = value

    @property
    def offset_y(self):
        return self._offset_y

    @offset_y.setter
    def offset_y(self, value):
        self.hbds_dirty = True
        self._offset_y = value

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, newstate):
        self._state = newstate
        self.time_accumulator = 0
        self.animation_frame = 0

    def draw(self, wnd):
        ix = int(self.x)
        iy = int(self.y)
        if not self.hidden and self.spritesheet is not None and self._state in self.states:
            draw_x = ix + self._offset_x
            draw_y = iy + self._offset_y
            state = self.states[self._state]
            if state[0]:
                self.time_accumulator += render_sync_stamp - self.last_sync_stamp
                self.last_sync_stamp = render_sync_stamp

                while state[1] > 0 and ((state[3] is False and self.animation_frame == len(state[2]) - 1) or state[3] is not False) and self.time_accumulator > state[1]:
                    self.time_accumulator -= state[1]
                    if state[3] is True:
                        self.animation_frame = (self.animation_frame + 1) % len(state[2])
                    elif state[3] is False:
                        self.animation_frame += 1
                    else:
                        self.animation_frame += 1
                        if self.animation_frame >= len(state[2]):
                            self._state = state[3]
                            self.animation_frame = 0
                            self.draw(wnd)
                            return

                self.spritesheet.draw_cell_to(wnd.display, state[2][self.animation_frame][0], state[2][self.animation_frame][1], draw_x, draw_y)
            else:
                self.spritesheet.draw_cell_to(wnd.display, state[1][0], state[1][1], draw_x, draw_y)

    def draw_as_hitbox(self, wnd, color):
        ix = int(self.x)
        iy = int(self.y)
        if self.hitbox is None:
            return
        if self.hbds_dirty or self.hitbox_draw_surface is None or color != self.hitbox_draw_surface_color:
            h = len(self.hitbox)
            w = len(self.hitbox[0])
            self.hitbox_draw_surface = pygame.Surface((w if w > self.hb_bg_w else self.hb_bg_w, h if h > self.hb_bg_h else self.hb_bg_h), SRCALPHA)
            self.hitbox_draw_surface_color = color
            self.hbds_dirty = False
            with pygame.PixelArray(self.hitbox_draw_surface) as hdpa:
                fill = (color[0], color[1], color[2], 0) if self.hb_bg_w == 0 or self.hb_bg_h == 0 else (color[0], color[1], color[2], 64)
                hdpa[:] = fill
                for yo in range(h):
                    for xo in range(w):
                        if self.hitbox[yo][xo]:
                            if self.hb_bg_w == 0 or self.hb_bg_h == 0:
                                hdpa[xo, yo] = (color[0], color[1], color[2], 255)
                            else:
                                hdpa[xo + abs(self._offset_x), yo + abs(self._offset_y)] = (color[0], color[1], color[2], 255)
        if self.hb_bg_w == 0 or self.hb_bg_h == 0:
            dest = (ix, iy)
        else:
            dest = (ix + self._offset_x, iy + self._offset_y)
        wnd.display.blit(self.hitbox_draw_surface, dest)
