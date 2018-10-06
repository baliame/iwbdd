from .object import Object, generate_rectangle_hitbox
from .spritesheet import Spritesheet
from .screen import CollisionTest


class DoublejumpPellet(Object):
    object_name = "Doublejump Refill"

    def __init__(self, screen, x=0, y=0, init_dict=None):
        super().__init__(screen, x, y, init_dict)
        self.spritesheet = Spritesheet.spritesheets_byname["ss_object_small_pickups-8-8.png"]
        self.hitbox = generate_rectangle_hitbox(6, 8)
        self.hitbox_type = CollisionTest.INTERACTABLE
        self.states = {
            "available": (True, 0.05, [(0, 0), (1, 0), (2, 0), (3, 0)], True),
            "despawning": (True, 0.1, [(0, 1), (1, 1), (2, 1), (3, 1)], "not_available"),
            "not_available": (False, (2, 0)),
        }
        self.offset_x = -1
        self.unavailable = 0
        self.state = "available"

    def tick(self):
        if self.unavailable > 0:
            self.unavailable -= 1
            if self.unavailable == 0:
                self.state = "available"

    def interact(self, ctrl):
        if self.unavailable > 0:
            return
        if ctrl.player.doublejump_available < 1:
            ctrl.player.doublejump_available = 1
        self.unavailable = 180
        self.state = "despawning"
