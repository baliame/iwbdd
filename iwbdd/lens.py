from .object import Object, EPType, generate_circle_hitbox, generate_semicircle_hitbox
from .common import CollisionTest, SCREEN_SIZE_W, SCREEN_SIZE_H, COLLISIONTEST_PREVENTS_MOVEMENT
import numpy as np
from .pygame_oo.game_shaders import GSHp, GSH_vaos
from .pygame_oo.shader import Mat4
from .pygame_oo.window import Window
from OpenGL.GL import *


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
        self.model = Mat4.scaling(self.radius * 2, self.radius * 2).translate(int(self.x) + self._offset_x, Window.instance.h - int(self.y) + self._offset_y)
        self.draw_x_m = -7
        self.draw_y_m = -7

    def tick(self, scr, ctrl):
        if (self.start_active and ctrl.trigger_group[self.trigger_group]) or (not self.start_active and not ctrl.trigger_group[self.trigger_group]):
            if self.active:
                self.active = 0
                scr.objects_dirty = True
                if scr == ctrl.player.screen:
                    coll = scr.test_screen_collision(ctrl.player.x, ctrl.player.y, (ctrl.player.hitbox_w, ctrl.player.hitbox_h))
                    if coll[4][0] & COLLISIONTEST_PREVENTS_MOVEMENT:
                        ctrl.player.die()
        else:
            if not self.active:
                self.active = 1
                scr.objects_dirty = True

    def draw(self, wnd):
        ix = int(self.x)
        iy = int(self.y)
        if not self.hidden:
            draw_x = ix + self._offset_x
            draw_y = iy + self._offset_y
            if draw_x != self.draw_x_m or draw_y != self.draw_y_m:
                self.model = Mat4.scaling(self.radius * 2, self.radius * 2).translate(draw_x, wnd.h - draw_y)
                self.draw_x_m = draw_x
                self.draw_y_m = draw_y
            prog_name = "GSHP_lens_off"
            if self.active:
                prog_name = "GSHP_lens"
            with GSHp(prog_name) as prog:
                wnd.setup_render(prog)
                prog.uniform('model', self.model)

                wnd.fbo.bindtexunit(1)
                self.screen.background.tex.bindtexunit(2)

                glBindVertexArray(GSH_vaos['unit'])
                glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
                glBindVertexArray(0)

    def draw_as_hitbox(self, wnd, color):
        if self.hidden or not self.active:
            return
        ix = int(self.x)
        iy = int(self.y)
        draw_x = ix + self._offset_x
        draw_y = iy + self._offset_y
        if draw_x != self.draw_x_m or draw_y != self.draw_y_m:
            self.model = Mat4.scaling(self.radius * 2, self.radius * 2).translate(draw_x, wnd.h - draw_y)
            self.draw_x_m = draw_x
            self.draw_y_m = draw_y
        with GSHp("GSHP_lens_coll") as prog:
            wnd.setup_render(prog)
            prog.uniform('model', self.model)

            wnd.fbo.bindtexunit(1)
            self.screen.background.tex.bindtexunit(2)

            glBindVertexArray(GSH_vaos['unit'])
            glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
            glBindVertexArray(0)

    def object_editor_draw(self, wnd):
        val = self.active
        self.active = self.start_active
        self.draw(wnd)
        self.active = val

    def reload_from_editor(self):
        super().reload_from_editor()
        self.model = Mat4.scaling(self.radius * 2, self.radius * 2).translate(draw_x, Window.instance.h - draw_y)
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
        self.model = Mat4.scaling(self.radius * 2, self.radius * 2).translate(int(self.x) + self._offset_x, Window.instance.h - int(self.y) + self._offset_y)
        self.editor_drawing = False

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
            coll = scr.test_screen_collision(ctrl.player.x, ctrl.player.y, (ctrl.player.hitbox_w, ctrl.player.hitbox_h))
            if coll[4][0] & COLLISIONTEST_PREVENTS_MOVEMENT:
                ctrl.player.die()

    def draw(self, wnd):
        ix = int(self.x)
        iy = int(self.y)
        if not self.hidden:
            draw_x = ix + self._offset_x
            draw_y = iy + self._offset_y
            self.model = Mat4.scaling(self.radius * 2, self.radius * 2).translate(draw_x, wnd.h - draw_y)
            with GSHp("GSHP_lens_semi") as prog:
                wnd.setup_render(prog)
                prog.uniform('model', self.model)

                wnd.fbo.bindtexunit(1)
                self.screen.background.tex.bindtexunit(2)

                glBindVertexArray(GSH_vaos['unit'])
                glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
                glBindVertexArray(0)

    def draw_as_hitbox(self, wnd, color):
        if self.hidden:
            return
        ix = int(self.x)
        iy = int(self.y)
        draw_x = ix + self._offset_x
        draw_y = iy + self._offset_y
        self.model = Mat4.scaling(self.radius * 2, self.radius * 2).translate(draw_x, wnd.h - draw_y)
        with GSHp("GSHP_lens_semi_coll") as prog:
            wnd.setup_render(prog)
            prog.uniform('model', self.model)
            wnd.fbo.bindtexunit(1)
            self.screen.background.tex.bindtexunit(2)
            glBindVertexArray(GSH_vaos['unit'])
            glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
            glBindVertexArray(0)

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
        wnd.graphics.line(self.source[0] + self.radius + 3, self.source[1] + self.radius + 3, self.destination[0] + self.radius + 3, self.destination[1] + self.radius + 3, (0, 255, 0, 255))
        self.x = cx
        self.y = cy

    def reload_from_editor(self):
        super().reload_from_editor()
        self.x = self.source[0] + int(self.t * (self.destination[0] - self.source[0]))
        self.y = self.source[1] + int(self.t * (self.destination[1] - self.source[1]))
        self.model = Mat4.scaling(self.radius * 2, self.radius * 2).translate(draw_x, wnd.h - draw_y)
        ActivatableLens.editor_frame_size = (2 * self.radius + 5, self.radius + 4)

    def on_editor_select(self):
        ActivatableLens.editor_frame_size = (2 * self.radius + 5, self.radius + 4)
