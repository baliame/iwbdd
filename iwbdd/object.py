from .pygame_oo.main_loop import MainLoop
from pygame.locals import SRCALPHA
import pygame
from .common import mousebox, CollisionTest, eofc_read, COLLISIONTEST_PREVENTS_MOVEMENT, SCREEN_SIZE_W, SCREEN_SIZE_H
from enum import Enum
import numpy as np
import struct
from .spritesheet import Spritesheet


def generate_rectangle_hitbox(w, h):
    return np.ones((w, h))
    # return np.array([[1 for y in range(h)] for x in range(w)])


def generate_circle_hitbox(rad):
    wh = 2 * rad + 1
    hb = np.zeros((wh, wh))
    xx, yy = np.mgrid[:wh, :wh]
    dist2 = (xx - rad) ** 2 + (yy - rad) ** 2 <= rad ** 2
    hb[dist2] = 1
    return hb


def generate_semicircle_hitbox(rad):
    return generate_circle_hitbox(rad)[:, :rad + 1]


class EPType(Enum):
    IntSelector = 1    # Arguments: default, min, max, step
    PointSelector = 2  # Arguments: -
    FloatSelector = 3    # Arguments: default, min, max, step
    HiddenSelector = 4  # Arguments: -


class SurfaceWrapper:
    def __init__(self, w, h):
        self.display = pygame.Surface((w, h), SRCALPHA)
        self.display.fill((0, 0, 0, 0))


class ExistingSurfaceWrapper:
    def __init__(self, surf):
        self.display = surf


# Object state
# Unanimated: (False, (sheet_cell_x, sheet_cell_y))
# Animated:   (True, animation_speed, [(sheet_cell_x, sheet_cell_y)...], looping [True|False|next animation state])

class Object:
    editor_properties = {}
    editing_values = {}
    exclude_from_object_editor = False
    saveable = True
    object_editor_items = None
    no_properties_text = None
    object_name = ""
    point_selection_var = None
    editor_frame_size = (0, 0)

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

        self.SH_model_matrix = np.identity(4)
        self.SH_colorize = (1.0, 1.0, 1.0, 1.0)

        self.last_sync_stamp = MainLoop.render_sync_stamp
        self.hitbox = None
        self.managed_hbds = False
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
        if value != self._offset_x:
            self.hbds_dirty = True
            self._offset_x = value

    @property
    def offset_y(self):
        return self._offset_y

    @offset_y.setter
    def offset_y(self, value):
        if value != self._offset_y:
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

                self.spritesheet.draw_cell_to(state[2][self.animation_frame][0], state[2][self.animation_frame][1], draw_x, draw_y, wnd.fbo)
            else:
                self.spritesheet.draw_cell_to(state[1][0], state[1][1], draw_x, draw_y, wnd.fbo)

    def object_editor_draw(self, wnd):
        self.draw(wnd)

    def _regen_hitbox(self, color):
        w = len(self.hitbox)
        if w <= 0:
            self.hitbox_draw_surface = None
            return
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

    def draw_as_hitbox(self, wnd, color):
        if self.hitbox is None or self.hidden:
                return
        ix = int(self.x)
        iy = int(self.y)
        if not self.managed_hbds:
            if self.hbds_dirty or self.hitbox_draw_surface is None or color != self.hitbox_draw_surface_color:
                self._regen_hitbox(color)
        if self.hb_bg_w == 0 or self.hb_bg_h == 0:
            dest = (ix, iy)
        else:
            dest = (ix + self._offset_x, iy + self._offset_y)
        if self.hitbox_draw_surface is not None:
            wnd.display.blit(self.hitbox_draw_surface, dest)

    def tick(self, scr, ctrl):
        pass

    def on_editor_select(self):
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
            if spec[0] != EPType.HiddenSelector:
                dv_render = "obj-dv-{0}".format(dest_var)
                if dv_render not in render_cache:
                    render_cache[dv_render] = font.render(dest_var, True, (255, 255, 255))
                surf.blit(render_cache[dv_render], (x, cy))
                if spec[0] == EPType.IntSelector:
                    if dest_var not in cls.editing_values:
                        cls.editing_values[dest_var] = spec[1]
                    value_text = font.render("{0}".format(cls.editing_values[dest_var]), True, (255, 255, 255), 0)
                    surf.blit(value_text, (x + 200, cy))
                    surf.blit(render_cache["dec"], (x + 300, cy))
                    surf.blit(render_cache["inc"], (x + 320, cy))
                elif spec[0] == EPType.PointSelector:
                    if dest_var not in cls.editing_values:
                        cls.editing_values[dest_var] = (0, 0)
                    value_text = font.render("({0}, {1})".format(cls.editing_values[dest_var][0], cls.editing_values[dest_var][1]), True, (255, 255, 255), 0)
                    surf.blit(value_text, (x + 200, cy))
                    surf.blit(render_cache["selectpt"], (x + 300, cy))
                    surf.blit(render_cache["decx"], (x + 360, cy))
                    surf.blit(render_cache["incx"], (x + 390, cy))
                    surf.blit(render_cache["decy"], (x + 420, cy))
                    surf.blit(render_cache["incy"], (x + 450, cy))
                elif spec[0] == EPType.FloatSelector:
                    if dest_var not in cls.editing_values:
                        cls.editing_values[dest_var] = spec[1]
                    value_text = font.render("{0:.4f}".format(cls.editing_values[dest_var]), True, (255, 255, 255), 0)
                    surf.blit(value_text, (x + 200, cy))
                    surf.blit(render_cache["dec"], (x + 300, cy))
                    surf.blit(render_cache["inc"], (x + 320, cy))
            cy += 20

    @classmethod
    def check_object_editor_click(cls, ed, x, y, base_x, base_y):
        count = len(cls.editor_properties.items())
        if count > 0:
            if not mousebox(x, y, base_x + 300, base_y, 200, count * 20):
                return False
            cy = base_y + 20
            for dest_var, spec in cls.editor_properties.items():
                if y < cy:
                    if spec[0] == EPType.IntSelector or spec[0] == EPType.FloatSelector:
                        if x < base_x + 320:
                            cls.editing_values[dest_var] -= spec[4]
                        else:
                            cls.editing_values[dest_var] += spec[4]
                        if cls.editing_values[dest_var] < spec[2]:
                            cls.editing_values[dest_var] = spec[2]
                        elif cls.editing_values[dest_var] > spec[3]:
                            cls.editing_values[dest_var] = spec[3]
                    elif spec[0] == EPType.PointSelector:
                        if x < base_x + 360:
                            cls.point_selection_var = dest_var
                            ed.point_selection_callback = cls.editor_point_selector
                        else:
                            pt = cls.editing_values[dest_var]
                            if x < base_x + 390:
                                pt = (pt[0] - 1, pt[1])
                            elif x < base_x + 420:
                                pt = (pt[0] + 1, pt[1])
                            elif x < base_x + 450:
                                pt = (pt[0], pt[1] - 1)
                            else:
                                pt = (pt[0], pt[1] + 1)
                            cls.editing_values[dest_var] = pt
                    elif spec[0] == EPType.HiddenSelector:
                        return False
                    return True
                cy += 20
            return False

    def load_object_to_editor(self):
        for dest_var, spec in self.__class__.editor_properties.items():
            self.__class__.editing_values[dest_var] = getattr(self, dest_var)
        self.on_editor_select()

    def reload_from_editor(self):
        for dest_var, spec in self.__class__.editor_properties.items():
            if spec[0] != EPType.HiddenSelector:
                setattr(self, dest_var, self.__class__.editing_values[dest_var])

    @classmethod
    def editor_point_selector(cls, x, y):
        if cls.point_selection_var is None:
            return
        cls.editing_values[cls.point_selection_var] = (x, y)
        cls.point_selection_var = None

    def interact(self, ctrl):
        pass

    @classmethod
    def create_from_reader(cls, reader, screen):
        x = struct.unpack("<H", eofc_read(reader, 2))[0]
        y = struct.unpack("<H", eofc_read(reader, 2))[0]
        idict = {}
        for dest_var, spec in cls.editor_properties.items():
            if spec[0] == EPType.IntSelector:
                idict[dest_var] = struct.unpack("<l", eofc_read(reader, 4))[0]
            elif spec[0] == EPType.FloatSelector:
                idict[dest_var] = struct.unpack("<d", eofc_read(reader, 8))[0]
            elif spec[0] == EPType.PointSelector:
                idict[dest_var] = (struct.unpack("<H", eofc_read(reader, 2))[0], struct.unpack("<H", eofc_read(reader, 2))[0])
        obj = cls(screen, x, y, idict)
        return obj

    def write_to_writer(self, writer):
        name = self.__class__.__name__
        name_len = len(name)
        writer.write(struct.pack("<H", name_len))
        writer.write(name.encode('ascii'))
        writer.write(struct.pack("<H", self.x))
        writer.write(struct.pack("<H", self.y))
        for dest_var, spec in self.__class__.editor_properties.items():
            val = getattr(self, dest_var)
            if spec[0] == EPType.IntSelector:
                writer.write(struct.pack("<l", val))
            elif spec[0] == EPType.FloatSelector:
                writer.write(struct.pack("<d", val))
            elif spec[0] == EPType.PointSelector:
                writer.write(struct.pack("<H", val[0]))
                writer.write(struct.pack("<H", val[1]))


class ExplosionEffect(Object):
    exclude_from_object_editor = True
    saveable = False

    def __init__(self, screen, x=0, y=0, init_dict=None):
        self.hitbox = None
        super().__init__(screen, x, y, init_dict)
        self.spritesheet = Spritesheet.spritesheets_byname["ss_explosion-48-48.png"]
        self.states = {
            "hidden": (False, (0, 1)),
            "exploding": (True, 0.125, [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0), (7, 0)], "done"),
            "done": (False, (0, 1)),
        }
        self.state = "hidden"

    def start(self, ctrl):
        self.screen.objects.append(self)
        ctrl.ambience("explosion.ogg")
        self.state = "exploding"

    def tick(self, scr, ctrl):
        if self.state == 'done':
            try:
                self.screen.objects.remove(self)
            except:
                pass


class Bullet(Object):
    exclude_from_object_editor = True
    velocity = 6
    hitbox = None
    saveable = False

    def __init__(self, screen, x=0, y=0, init_dict=None):
        super().__init__(screen, x, y, init_dict)
        if init_dict is None:
            init_dict = {}
        if "facing" not in init_dict:
            init_dict["facing"] = 1
        self.xv = Bullet.velocity * init_dict["facing"]
        self.step = init_dict["facing"]
        self.player = init_dict["player"]
        if Bullet.hitbox is None:
            Bullet.hitbox = generate_rectangle_hitbox(4, 4)
        self.spritesheet = Spritesheet.spritesheets_byname["ss_object_bullets-8-8.png"]
        self.states = {
            "default": (False, (0, 0)),
        }
        self.state = "default"
        self._offset_x = -2
        self._offset_y = -2
        self.hitbox = Bullet.hitbox
        self.hitbox_type = CollisionTest.PASSABLE
        self.abort = False

    def tick(self, scr, ctrl):
        if self.player.dead:
            self.cleanup_self()
            return
        self.player.controller.source_bullet = self
        for i in range(0, self.xv, self.step):
            self.x += self.step
            if self.x < 0 or self.x > SCREEN_SIZE_W - 4:
                self.cleanup_self()
                return
            coll = self.screen.test_screen_collision(self.x, self.y, Bullet.hitbox, {0x000080: CollisionTest.SAVE_TILE})
            # print("{0}, {1}: {2}".format(self.x, self.y, coll))
            idx = 0 if self.xv > 0 else 2
            if coll[4][0] & COLLISIONTEST_PREVENTS_MOVEMENT or coll[idx][0] & COLLISIONTEST_PREVENTS_MOVEMENT:
                self.cleanup_self()
                return
            elif coll[4][0] & CollisionTest.SAVE_TILE:
                self.cleanup_self()
                self.player.controller.save_state()
                return
            self.screen.test_interactable_collision(self.player.controller, self.x, self.y, self.hitbox, CollisionTest.BULLET_INTERACTABLE)
            if self.abort:
                return

    def cleanup_self(self):
        try:
            self.player.bullets.remove(self)
        except:
            pass
        try:
            self.screen.objects.remove(self)
        except:
            pass
        self.abort = True


class SaveTile(Object):
    hitbox = None
    object_name = "Save tile (24x24)"
    editor_frame_size = (26, 26)

    def __init__(self, screen, x=0, y=0, init_dict=None):
        super().__init__(screen, x, y, init_dict)
        if SaveTile.hitbox is None:
            SaveTile.hitbox = generate_rectangle_hitbox(24, 24)
        self.hitbox = SaveTile.hitbox
        self.hitbox_type = CollisionTest.SAVE_TILE
        self.screen.objects_dirty = True
        self.spritesheet = Spritesheet.spritesheets_byname["ss_object_shootables-24-24.png"]
        self.states = {
            "default": (False, (0, 0)),
        }
        self.state = "default"


frames_per_timer = 20

class Button(Object):
    hitbox = None
    object_name = "Button (shootable, toggle)"
    editor_frame_size = (18, 18)
    editor_properties = {
        "trigger_group": (EPType.IntSelector, 0, 0, 255, 1),
    }

    def __init__(self, screen, x=0, y=0, init_dict=None):
        self.trigger_group = 0
        super().__init__(screen, x, y, init_dict)
        if Button.hitbox is None:
            Button.hitbox = generate_rectangle_hitbox(16, 16)
        self.hitbox = Button.hitbox
        self.hitbox_type = CollisionTest.BULLET_INTERACTABLE
        self.screen.objects_dirty = True
        self.spritesheet = Spritesheet.spritesheets_byname["ss_object_shootables-24-24.png"]
        self.states = {
            "default": (False, (1, 0)),
            "active": (False, (2, 0)),
        }
        self.state = "default"
        self._offset_x = -4
        self._offset_y = -4

    def tick(self, scr, ctrl):
        if ctrl.trigger_group[self.trigger_group] and self._state == "default":
            self.state = "active"
        elif not ctrl.trigger_group[self.trigger_group] and self._state == "active":
            self.state = "default"

    def interact(self, ctrl):
        ctrl.source_bullet.cleanup_self()
        if ctrl.trigger_group[self.trigger_group]:
            ctrl.trigger_group[self.trigger_group] = 0
            self.state = "default"
        else:
            ctrl.trigger_group[self.trigger_group] = 1
            self.state = "active"


class TimedButton(Object):
    hitbox = None
    object_name = "Button (shootable, timer)"
    editor_frame_size = (18, 18)
    editor_properties = {
        "trigger_group": (EPType.IntSelector, 0, 0, 255, 1),
        "timer": (EPType.IntSelector, 5, 1, 300, 1),
        "current_timer": (EPType.HiddenSelector, )
    }

    def __init__(self, screen, x=0, y=0, init_dict=None):
        self.trigger_group = 0
        self.timer = 5
        self.current_timer = 0
        super().__init__(screen, x, y, init_dict)
        if TimedButton.hitbox is None:
            TimedButton.hitbox = generate_rectangle_hitbox(16, 16)
        self.hitbox = TimedButton.hitbox
        self.hitbox_type = CollisionTest.BULLET_INTERACTABLE
        self.screen.objects_dirty = True
        self.spritesheet = Spritesheet.spritesheets_byname["ss_object_shootables-24-24.png"]
        self.states = {
            "default": (False, (0, 1)),
            "active9": (False, (1, 1)),
            "active8": (False, (2, 1)),
            "active7": (False, (3, 1)),
            "active6": (False, (4, 1)),
            "active5": (False, (5, 1)),
            "active4": (False, (6, 1)),
            "active3": (False, (7, 1)),
            "active2": (False, (8, 1)),
            "active1": (False, (9, 1)),
        }
        t9 = self.timer * frames_per_timer / 9
        self.breakpoints = tuple(t9 * i for i in range(8, 0, -1))
        self.state = "default"
        self._offset_x = -4
        self._offset_y = -4

    def update_state(self):
        if self.current_timer == 0:
            self.state = "default"
            return
        a = 9
        for bp in self.breakpoints:
            if self.current_timer > bp:
                self.state = "active{0}".format(a)
                return
            else:
                a -= 1
        self.state = "active1"

    def tick(self, scr, ctrl):
        if self.current_timer > 0:
            self.current_timer -= 1
            if self.current_timer == 0:
                if not ctrl.trigger_cache[self.trigger_group]:
                    ctrl.trigger_group[self.trigger_group] = 0
                self.state = "default"
            else:
                ctrl.trigger_group[self.trigger_group] = 1
                ctrl.trigger_cache[self.trigger_group] = 1
                self.update_state()

    def interact(self, ctrl):
        t9 = self.timer * frames_per_timer / 9
        self.breakpoints = tuple(t9 * i for i in range(8, 0, -1))
        ctrl.source_bullet.cleanup_self()
        ctrl.trigger_group[self.trigger_group] = 1
        self.current_timer = self.timer * frames_per_timer
        self.state = "active9"


class Perpetuator(Object):
    hitbox = None
    object_name = "Perpetual timer"
    editor_frame_size = (24, 24)
    editor_properties = {
        "trigger_group": (EPType.IntSelector, 0, 0, 255, 1),
        "timer": (EPType.IntSelector, 5, 1, 300, 1),
        "current_timer": (EPType.HiddenSelector, ),
    }

    def __init__(self, screen, x=0, y=0, init_dict=None):
        self.trigger_group = 0
        self.timer = 5
        self.current_timer = 0
        super().__init__(screen, x, y, init_dict)
        if Perpetuator.hitbox is None:
            Perpetuator.hitbox = generate_rectangle_hitbox(24, 24)
        self.current_timer = self.timer * frames_per_timer
        self.hitbox = Perpetuator.hitbox
        self.hitbox_type = CollisionTest.PASSABLE
        self.screen.objects_dirty = True
        self.spritesheet = Spritesheet.spritesheets_byname["ss_object_shootables-24-24.png"]
        self.states = {
            "passive9": (False, (0, 2)),
            "passive8": (False, (1, 2)),
            "passive7": (False, (2, 2)),
            "passive6": (False, (3, 2)),
            "passive5": (False, (4, 2)),
            "passive4": (False, (5, 2)),
            "passive3": (False, (6, 2)),
            "passive2": (False, (7, 2)),
            "passive1": (False, (8, 2)),
            "active9": (False, (0, 3)),
            "active8": (False, (1, 3)),
            "active7": (False, (2, 3)),
            "active6": (False, (3, 3)),
            "active5": (False, (4, 3)),
            "active4": (False, (5, 3)),
            "active3": (False, (6, 3)),
            "active2": (False, (7, 3)),
            "active1": (False, (8, 3)),
        }
        t9 = self.timer * frames_per_timer / 9
        self.breakpoints = tuple(t9 * i for i in range(8, 0, -1))
        self.state = "passive9"
        self._offset_x = -4
        self._offset_y = -4

    def update_state(self, ctrl):
        if self.current_timer == 0:
            self.state = "default"
            return
        a = 9
        for bp in self.breakpoints:
            if self.current_timer > bp:
                self.state = "{0}{1}".format("active" if ctrl.trigger_group[self.trigger_group] else "passive", a)
                return
            else:
                a -= 1
        self.state = "{0}1".format("active" if ctrl.trigger_group[self.trigger_group] else "passive")

    def tick(self, scr, ctrl):
        if self.current_timer > 0:
            self.current_timer -= 1
            if self.current_timer == 0:
                if ctrl.trigger_group[self.trigger_group]:
                    ctrl.trigger_group[self.trigger_group] = 0
                else:
                    ctrl.trigger_group[self.trigger_group] = 1
                self.current_timer = self.timer * frames_per_timer
            self.update_state(ctrl)
