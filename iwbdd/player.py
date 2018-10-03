from .object import Object, generate_rectangle_hitbox
from .spritesheet import Spritesheet


class Player(Object):
    exclude_from_object_editor = True

    def __init__(self):
        super().__init__(None)
        self.bottom_pixel = 14
        self.hitbox = generate_rectangle_hitbox(12, self.bottom_pixel + 1)
        self.offset_x = -6
        self.offset_y = -9
        # self.hb_bg_w = 16
        # self.hb_bg_h = 16
        self.spritesheet = Spritesheet.spritesheets[1]
        self.movement_velocity = [0, 0]
        self.gravity_velocity = [0, 0]
        self.doublejump_available = 1
        self.jump_held = False
        self.jumping = False
        self.cached_collision = None
        self.dead = False
        self.states = {
            "stop_left": (False, (0, 1)),
            "stop_right": (False, (0, 0)),
            "moving_left": (True, 0.1, [(0, 1), (1, 1)], True),
            "moving_right": (True, 0.1, [(0, 0), (1, 0)], True),
        }
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
