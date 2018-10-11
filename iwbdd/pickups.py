from .object import Object, generate_rectangle_hitbox
from .spritesheet import Spritesheet
from .common import CollisionTest


class DoublejumpPellet(Object):
    object_name = "Doublejump Refill"
    editor_frame_size = (10, 10)

    def __init__(self, screen, x=0, y=0, init_dict=None):
        super().__init__(screen, x, y, init_dict)
        self.spritesheet = Spritesheet.spritesheets_byname["ss_object_small_pickups-8-8.png"]
        self.hitbox = generate_rectangle_hitbox(6, 8)
        self.hitbox_type = CollisionTest.INTERACTABLE
        self.states = {
            "available": (True, 0.05, [(0, 0), (1, 0), (2, 0), (3, 0)], True),
            "despawning": (True, 0.1, [(0, 1), (1, 1), (2, 1), (3, 1)], "not_available"),
            "not_available": (False, (0, 2)),
        }
        self.offset_x = -1
        self.unavailable = 0
        self.state = "available"

    def tick(self, scr, ctrl):
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


class TriplejumpPellet(DoublejumpPellet):
    object_name = "Triplejump Pellet"
    editor_frame_size = (10, 10)

    def __init__(self, screen, x=0, y=0, init_dict=None):
        super().__init__(screen, x, y, init_dict)
        self.states = {
            "available": (True, 0.05, [(0, 3), (1, 3), (2, 3), (3, 3)], True),
            "despawning": (True, 0.1, [(0, 4), (1, 4), (2, 4), (3, 4)], "not_available"),
            "not_available": (False, (0, 2)),
        }

    def interact(self, ctrl):
        if self.unavailable > 0:
            return
        if ctrl.player.doublejump_available < 2:
            ctrl.player.doublejump_available = 2
        self.unavailable = 180
        self.state = "despawning"


class QuadjumpPellet(DoublejumpPellet):
    object_name = "Quadjump Pellet"
    editor_frame_size = (10, 10)

    def __init__(self, screen, x=0, y=0, init_dict=None):
        super().__init__(screen, x, y, init_dict)
        self.states = {
            "available": (True, 0.05, [(0, 5), (1, 5), (2, 5), (3, 5)], True),
            "despawning": (True, 0.1, [(0, 6), (1, 6), (2, 6), (3, 6)], "not_available"),
            "not_available": (False, (0, 2)),
        }

    def interact(self, ctrl):
        if self.unavailable > 0:
            return
        if ctrl.player.doublejump_available < 3:
            ctrl.player.doublejump_available = 3
        self.unavailable = 180
        self.state = "despawning"


class PentajumpPellet(DoublejumpPellet):
    object_name = "Pentajump Pellet"
    editor_frame_size = (10, 10)

    def __init__(self, screen, x=0, y=0, init_dict=None):
        super().__init__(screen, x, y, init_dict)
        self.states = {
            "available": (True, 0.05, [(0, 7), (1, 7), (2, 7), (3, 7)], True),
            "despawning": (True, 0.1, [(0, 8), (1, 8), (2, 8), (3, 8)], "not_available"),
            "not_available": (False, (0, 2)),
        }

    def interact(self, ctrl):
        if self.unavailable > 0:
            return
        if ctrl.player.doublejump_available < 4:
            ctrl.player.doublejump_available = 4
        self.unavailable = 180
        self.state = "despawning"
