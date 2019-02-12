from .object import Object, EPType
from .spritesheet import Spritesheet
from .common import CollisionTest
from collections import OrderedDict
import pygame


class MovingPlatform(Object):
    object_name = "Moving platform (2-by-1)"
    editor_properties = OrderedDict({
        "dest_pos": (EPType.PointSelector, ),
        "t": (EPType.FloatSelector, 0, 0, 1, 0.01),
        "speed": (EPType.FloatSelector, 0.0005, 0.0001, 1, 0.0001),
        "forward": (EPType.IntSelector, 1, 0, 1, 1),
    })
    editor_frame_size = (48, 24)

    def __init__(self, screen, x=0, y=0, init_dict=None):
        self.dest_pos = (0, 0)
        self.t = 0
        self.forward = 0
        self.speed = 0.1
        super().__init__(screen, x, y, init_dict)
        self.spritesheet = Spritesheet.spritesheets_byname["ss_object_movingplatform-32-32.png"]
        self.init_x = self.x
        self.init_y = self.y
        self._offset_x = 0
        self._offset_y = -16
        self.hitbox_w = 32
        self.hitbox_h = 16
        self.hitbox_type = CollisionTest.SOLID
        self.dx = 0
        self.dy = 0
        self.objed_surf = None

    def tick(self, scr, ctrl):
        if self.forward:
            self.t += self.speed
            if self.t > 1:
                self.t = self.t - (self.t - 1)
                self.forward = 0
        else:
            self.t -= self.speed
            if self.t < 0:
                self.t = -self.t
                self.forward = 1
        nx = self.init_x + int(self.t * (self.dest_pos[0] - self.init_x))
        ny = self.init_y + int(self.t * (self.dest_pos[1] - self.init_y))
        self.dx = nx - self.x
        self.dy = ny - self.y
        self.x = nx
        self.y = ny
        scr.objects_dirty = True

    def object_editor_draw(self, wnd):
        if self.objed_surf is None:
            self.objed_surf = SurfaceWrapper(32, 32)
            tx = self.x
            ty = self.y
            self.x = 0
            self.y = 16
            self.draw(self.object_surf)
            a = pygame.surfarray.pixels_alpha(self.objed_surf)
            a[a > 0] = 128
            self.x = tx
            self.y = ty
        pygame.draw.line(wnd.display, (255, 255, 255, 128), (self.init_x, self.init_y), self.dest_pos)
        wnd.display.blit(self.objed_surf, (self.init_x + self._offset_x, self.init_y + self._offset_y))
        wnd.display.blit(self.objed_surf, (self.dest_pos[0] + self._offset_x, self.dest_pos[1] + self._offset_y))
