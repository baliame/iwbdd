from .object import Object, generate_rectangle_hitbox
from .spritesheet import Spritesheet


class Player(Object):
    def __init__(self):
        super.__init__(self, None)
        self.hitbox = generate_rectangle_hitbox(8, 12)
        self.offset_x = -4
        self.offset_y = 4
        self.spritesheet = Spritesheet.spritesheets[1]
        self.states = {
            "stop_left": (False, (0, 0)),
            "stop_right": (False, (0, 1)),
            "moving_left": (True, 0.5, [(0, 0), (1, 0)], True),
            "moving_right": (True, 0.5, [(0, 1), (1, 1)], True),
        }
        self.state = "stop_right"
