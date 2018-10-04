from .pygame_oo.main_loop import MainLoop
from pygame.locals import SRCALPHA
import pygame
from .screen import CollisionTest
from enum import Enum
import numpy as np


def generate_rectangle_hitbox(w, h):
    return np.array([[1 for y in range(h)] for x in range(w)])


class EPType(Enum):
    IntSelector = 1    # Arguments: default, min, max, step
    PointSelector = 2  # Arguments: -
    FloatSelector = 3    # Arguments: default, min, max, step


class SurfaceWrapper:
    def __init__(self, w, h):
        self.display = pygame.Surface((w, h), SRCALPHA)
        self.display.fill((0, 0, 0, 0))


# Object state
# Unanimated: (False, (sheet_cell_x, sheet_cell_y))
# Animated:   (True, animation_speed, [(sheet_cell_x, sheet_cell_y)...], looping [True|False|next animation state])

class Object:
    editor_properties = {}
    editing_values = {}
    exclude_from_object_editor = False
    object_editor_items = None
    no_properties_text = None
    object_name = ""

    @staticmethod
    def enumerate_objects(base_class):
        if Object.object_editor_items is None:
            Object.object_editor_items = []
        for item in base_class.__subclasses__():
            if not item.exclude_from_object_editor:
                Object.object_editor_items.append(item)
                Object.enumerate_objects(item)

    def __init__(self, screen, x=0, y=0, init_dict=None):
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
        self.last_sync_stamp = MainLoop.render_sync_stamp
        self.hitbox = None
        self.hitbox_type = CollisionTest.PASSABLE

        self.hb_bg_w = 0
        self.hb_bg_h = 0
        self.hbds_dirty = True
        self.hitbox_draw_surface = None
        self.hitbox_draw_surface_color = None

        if init_dict is not None:
            for dest_var, init_val in init_dict.items():
                setattr(self, dest_var, init_val)

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
        self.last_sync_stamp = MainLoop.render_sync_stamp

    def draw(self, wnd):
        ix = int(self.x)
        iy = int(self.y)
        if not self.hidden and self.spritesheet is not None and self._state in self.states:
            draw_x = ix + self._offset_x
            draw_y = iy + self._offset_y
            state = self.states[self._state]
            if state[0]:
                self.time_accumulator += MainLoop.render_sync_stamp - self.last_sync_stamp
                self.last_sync_stamp = MainLoop.render_sync_stamp

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

    def object_editor_draw(self, wnd):
        self.draw(self, wnd)

    def draw_as_hitbox(self, wnd, color):
        ix = int(self.x)
        iy = int(self.y)
        if self.hitbox is None:
            return
        if self.hbds_dirty or self.hitbox_draw_surface is None or color != self.hitbox_draw_surface_color:
            w = len(self.hitbox)
            h = len(self.hitbox[0])
            self.hitbox_draw_surface = pygame.Surface((w if w > self.hb_bg_w else self.hb_bg_w, h if h > self.hb_bg_h else self.hb_bg_h), SRCALPHA)
            self.hitbox_draw_surface_color = color
            self.hbds_dirty = False
            with pygame.PixelArray(self.hitbox_draw_surface) as hdpa:
                fill = (color[0], color[1], color[2], 0) if self.hb_bg_w == 0 or self.hb_bg_h == 0 else (color[0], color[1], color[2], 64)
                hdpa[:] = fill
                for yo in range(h):
                    for xo in range(w):
                        if self.hitbox[xo, yo]:
                            if self.hb_bg_w == 0 or self.hb_bg_h == 0:
                                hdpa[xo, yo] = (color[0], color[1], color[2], 255)
                            else:
                                hdpa[xo + abs(self._offset_x), yo + abs(self._offset_y)] = (color[0], color[1], color[2], 255)
        if self.hb_bg_w == 0 or self.hb_bg_h == 0:
            dest = (ix, iy)
        else:
            dest = (ix + self._offset_x, iy + self._offset_y)
        wnd.display.blit(self.hitbox_draw_surface, dest)

    def tick(self):
        pass

    @classmethod
    def render_editor_properties(cls, surf, font, x, y, render_cache):
        if cls.exclude_from_object_editor:
            raise TypeError('{0} is a hidden object, should not be available in editor.'.format(cls))
        if len(cls.editor_properties) == 0:
            if Object.no_properties_text is None:
                Object.no_properties_text = font.render("This object has no configurable attributes.", True, (255, 255, 255), 0)
            surf.blit(Object.no_properties_text, (x, y))
            return
        cy = y
        for dest_var, spec in cls.editor_properties.items():
            dv_render = "obj-dv-{0}".format(dest_var)
            if dv_render not in render_cache:
                render_cache[dv_render] = font.render(dest_var, True, (255, 255, 255))
            surf.blit(render_cache[dv_render], (x, cy))
            if spec[0] == EPType.IntSelector:
                if dest_var not in cls.editing_values:
                    cls.editing_values[dest_var] = spec[1]
                value_text = font.render("{0}".format(cls.editing_values[dest_var]), True, (255, 255, 255), 0)
                surf.blit(value_text, (x + 200, cy))
                surf.blit(render_cache["inc"], (x + 300, cy))
                surf.blit(render_cache["dec"], (x + 320, cy))
            elif spec[0] == EPType.PointSelector:
                if dest_var not in cls.editing_values:
                    cls.editing_values[dest_var] = (0, 0)
                value_text = font.render("({0}, {1})".format(cls.editing_values[dest_var][0], cls.editing_values[dest_var][1]), True, (255, 255, 255), 0)
                surf.blit(value_text, (x + 200, cy))
                surf.blit(render_cache["selectpt"], (x + 300, cy))
            elif spec[0] == EPType.FloatSelector:
                if dest_var not in cls.editing_values:
                    cls.editing_values[dest_var] = spec[1]
                value_text = font.render("{0:.4f}".format(cls.editing_values[dest_var]), True, (255, 255, 255), 0)
                surf.blit(value_text, (x + 200, cy))
                surf.blit(render_cache["inc"], (x + 300, cy))
                surf.blit(render_cache["dec"], (x + 320, cy))
            cy += 20

    @classmethod
    def check_object_editor_click(cls):
        pass
