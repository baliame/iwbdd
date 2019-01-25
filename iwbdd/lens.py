from .object import Object, EPType, generate_circle_hitbox, generate_semicircle_hitbox
from .common import CollisionTest, SCREEN_SIZE_W, SCREEN_SIZE_H, COLLISIONTEST_PREVENTS_MOVEMENT
import numpy as np
import pygame


class LensParent(Object):
    exclude_from_object_editor = True
    saveable = False

    def __init__(self, screen, x=0, y=0, init_dict=None):
        super().__init__(screen, x, y, init_dict)
        self.hitbox_type = CollisionTest.LENS


class ActivatableLens(LensParent):
    exclude_from_object_editor = False
    saveable = True
    object_name = "Triggerable lens"
    editor_properties = {
        "start_active": (EPType.IntSelector, 0, 0, 1, 1),
        "radius": (EPType.IntSelector, 20, 20, 255, 1),
        "trigger_group": (EPType.IntSelector, 0, 0, 255, 1),
    }

    def __init__(self, screen, x=0, y=0, init_dict=None):
        self.start_active = 0
        self.radius = 20
        self.active = self.start_active
        self.trigger_group = 0
        super().__init__(screen, x, y, init_dict)
        self.active_hitbox = generate_circle_hitbox(self.radius)
        self.passive_hitbox = np.array([])
        self.hitbox_type = CollisionTest.LENS
        self.hitbox = self.passive_hitbox if not self.start_active else self.active_hitbox
        self.active_surface = pygame.Surface((self.radius * 2 + 5, self.radius * 2 + 5), pygame.SRCALPHA)
        self.passive_surface = pygame.Surface((self.radius * 2 + 5, self.radius * 2 + 5), pygame.SRCALPHA)
        self.active_surface.fill((0, 0, 0, 0))
        self.passive_surface.fill((0, 0, 0, 0))
        pygame.draw.circle(self.active_surface, (0, 0, 0, 255), (self.radius + 3, self.radius + 3), self.radius + 3, 3)
        pygame.draw.circle(self.passive_surface, (0, 0, 0, 255), (self.radius + 3, self.radius + 3), self.radius + 3, 3)
        self.generate_distortion()
        self.offset_x = -2
        self.offset_y = -2

    def generate_distortion(self):
        return
        bg = self.screen.background
        basex = self.x + self.radius
        basey = self.y + self.radius
        with pygame.PixelArray(self.active_surface) as pa:
            r2 = self.radius * self.radius
            for x in range(self.radius * 2 + 5):
                for y in range(self.radius * 2 + 5):
                    relx = x - self.radius - 2
                    rely = y - self.radius - 2
                    d2 = relx * relx + rely * rely
                    if d2 <= r2:
                        col = bg.sample(basex, basey, SCREEN_SIZE_W, SCREEN_SIZE_H)
                        pa[x, y] = (col[0], col[1], col[2], 255)

    def tick(self, scr, ctrl):
        if (self.start_active and ctrl.trigger_group[self.trigger_group]) or (not self.start_active and not ctrl.trigger_group[self.trigger_group]):
            if self.active:
                self.active = 0
                self.hitbox = self.passive_hitbox
                scr.objects_dirty = True
                self.hbds_dirty = True
                if scr == ctrl.player.screen:
                    coll = scr.test_screen_collision(ctrl.player.x, ctrl.player.y, ctrl.player.hitbox)
                    if coll[4][0] & COLLISIONTEST_PREVENTS_MOVEMENT:
                        ctrl.player.die()
        else:
            if not self.active:
                self.active = 1
                self.hitbox = self.active_hitbox
                scr.objects_dirty = True
                self.hbds_dirty = True

    def draw(self, wnd):
        ix = int(self.x)
        iy = int(self.y)
        if not self.hidden:
            draw_x = ix + self._offset_x
            draw_y = iy + self._offset_y
            if self.active:
                wnd.display.blit(self.active_surface, (draw_x, draw_y))
            else:
                wnd.display.blit(self.passive_surface, (draw_x, draw_y))

    def object_editor_draw(self, wnd):
        val = self.active
        self.active = self.start_active
        self.draw(wnd)
        self.active = val

    def reload_from_editor(self):
        super().reload_from_editor()
        self.active_hitbox = generate_circle_hitbox(self.radius)
        self.passive_hitbox = np.array([])
        self.hitbox = self.passive_hitbox if not self.start_active else self.active_hitbox
        self.active_surface = pygame.Surface((self.radius * 2 + 5, self.radius * 2 + 5), pygame.SRCALPHA)
        self.passive_surface = pygame.Surface((self.radius * 2 + 5, self.radius * 2 + 5), pygame.SRCALPHA)
        self.active_surface.fill((0, 0, 0, 0))
        self.passive_surface.fill((0, 0, 0, 0))
        pygame.draw.circle(self.active_surface, (0, 0, 0, 255), (self.radius + 3, self.radius + 3), self.radius + 3, 5)
        pygame.draw.circle(self.passive_surface, (0, 0, 0, 255), (self.radius + 3, self.radius + 3), self.radius + 3, 5)
        self.generate_distortion()
        ActivatableLens.editor_frame_size = (2 * self.radius + 5, 2 * self.radius + 5)

    def on_editor_select(self):
        ActivatableLens.editor_frame_size = (2 * self.radius + 5, 2 * self.radius + 5)


class MovingLens(LensParent):
    exclude_from_object_editor = False
    saveable = True
    object_name = "Moving lens"
    editor_properties = {
        "radius": (EPType.IntSelector, 20, 20, 255, 1),
        "source": (EPType.PointSelector, ),
        "destination": (EPType.PointSelector, ),
        "t": (EPType.FloatSelector, 0, 0, 1, 0.01),
        "speed": (EPType.FloatSelector, 0.0005, 0.0001, 1, 0.0001),
        "forward": (EPType.IntSelector, 1, 0, 1, 1),
    }

    def __init__(self, screen, x=0, y=0, init_dict=None):
        self.radius = 20
        self.source = (0, 0)
        self.destination = (0, 0)
        self.t = 0.0
        self.speed = 0.0005
        self.forward = 1
        super().__init__(screen, x, y, init_dict)
        self.x = self.source[0] + int(self.t * (self.destination[0] - self.source[0]))
        self.y = self.source[1] + int(self.t * (self.destination[1] - self.source[1]))
        self.hitbox = generate_semicircle_hitbox(self.radius)
        self.active_surface = pygame.Surface((self.radius * 2 + 5, self.radius + 5), pygame.SRCALPHA)
        self.active_surface.fill((0, 0, 255, 0))
        pygame.draw.circle(self.active_surface, (0, 0, 255, 255), (self.radius + 3, self.radius + 3), self.radius + 3, 3)
        pygame.draw.line(self.active_surface, (0, 0, 255, 255), (0, self.radius + 4), (self.radius * 2 + 5, self.radius + 4), 3)
        self.generate_distortion()
        self.editor_surface = self.active_surface.copy()
        sa = pygame.surfarray.pixels_alpha(self.editor_surface)
        sa[sa > 0] = 128
        self.offset_x = -2
        self.offset_y = -2
        self.editor_drawing = False

    def generate_distortion(self):
        return
        bg = self.screen.background
        basex = self.x + self.radius
        basey = self.y + self.radius
        with pygame.PixelArray(self.active_surface) as pa:
            r2 = self.radius * self.radius
            for x in range(self.radius * 2 + 5):
                for y in range(self.radius + 3):
                    relx = x - self.radius - 2
                    rely = y - self.radius - 2
                    d2 = relx * relx + rely * rely
                    if d2 <= r2:
                        col = bg.sample(basex, basey, SCREEN_SIZE_W, SCREEN_SIZE_H)
                        pa[x, y] = (col[0], col[1], col[2], 255)

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
        nx = self.source[0] + int(self.t * (self.destination[0] - self.source[0]))
        ny = self.source[1] + int(self.t * (self.destination[1] - self.source[1]))
        self.dx = nx - self.x
        self.dy = ny - self.y
        self.x = nx
        self.y = ny
        scr.objects_dirty = True
        if scr == ctrl.player.screen:
            coll = scr.test_screen_collision(ctrl.player.x, ctrl.player.y, ctrl.player.hitbox)
            if coll[4][0] & COLLISIONTEST_PREVENTS_MOVEMENT:
                ctrl.player.die()

    def draw(self, wnd):
        ix = int(self.x)
        iy = int(self.y)
        if not self.hidden:
            draw_x = ix + self._offset_x
            draw_y = iy + self._offset_y
            wnd.display.blit(self.active_surface if not self.editor_drawing else self.editor_surface, (draw_x, draw_y))

    def object_editor_draw(self, wnd):
        cx = self.x
        cy = self.y
        ix = self.source[0] + int(self.t * (self.destination[0] - self.source[0]))
        iy = self.source[1] + int(self.t * (self.destination[1] - self.source[1]))
        self.x = ix
        self.y = iy
        self.draw(wnd)
        self.editor_drawing = True
        self.x = self.source[0]
        self.y = self.source[1]
        self.draw(wnd)
        self.x = self.destination[0]
        self.y = self.destination[1]
        self.draw(wnd)
        self.editor_drawing = False
        pygame.draw.line(wnd.display, (0, 255, 0), (self.source[0] + self.radius + 3, self.source[1] + self.radius + 3), (self.destination[0] + self.radius + 3, self.destination[1] + self.radius + 3))
        self.x = cx
        self.y = cy

    def reload_from_editor(self):
        super().reload_from_editor()
        self.hitbox = generate_semicircle_hitbox(self.radius)
        self.active_surface = pygame.Surface((self.radius * 2 + 5, self.radius + 4), pygame.SRCALPHA)
        self.active_surface.fill((0, 0, 255, 0))
        pygame.draw.circle(self.active_surface, (0, 0, 255, 255), (self.radius + 3, self.radius + 3), self.radius + 3, 3)
        pygame.draw.line(self.active_surface, (0, 0, 255, 255), (0, self.radius + 4), (self.radius * 2 + 5, self.radius + 4), 3)
        self.generate_distortion()
        self.editor_surface = self.active_surface.copy()
        sa = pygame.surfarray.pixels_alpha(self.editor_surface)
        sa[sa > 0] = 128
        self.x = self.source[0] + int(self.t * (self.destination[0] - self.source[0]))
        self.y = self.source[1] + int(self.t * (self.destination[1] - self.source[1]))
        ActivatableLens.editor_frame_size = (2 * self.radius + 5, self.radius + 4)

    def on_editor_select(self):
        ActivatableLens.editor_frame_size = (2 * self.radius + 5, self.radius + 4)
