from .object import Object, generate_rectangle_hitbox
from .spritesheet import Spritesheet


class Player(Object):
    def __init__(self):
        super().__init__(None)
        self.hitbox = generate_rectangle_hitbox(8, 12)
        self.offset_x = -4
        self.offset_y = -4
        self.hb_bg_w = 16
        self.hb_bg_h = 16
        self.spritesheet = Spritesheet.spritesheets[1]
        self.movement_velocity = (0, 0)
        self.gravity_velocity = (0, 0)
        self.doublejump_available = 1
        self.cached_collision = None
        self.states = {
            "stop_left": (False, (0, 1)),
            "stop_right": (False, (0, 0)),
            "moving_left": (True, 0.5, [(0, 1), (1, 1)], True),
            "moving_right": (True, 0.5, [(0, 0), (1, 0)], True),
        }
        self._state = "stop_right"

    def reset(self):
        self.movement_velocity = (0, 0)
        self.gravity_velocity = (0, 0)
        self.doublejump_available = 1
        self.cached_collision = None
        self.state = "stop_right"
