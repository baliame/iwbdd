from .object import Object, EPType
from .common import CollisionTest, Controls, MOVEMENT_SPEED, SCREEN_SIZE_W, SCREEN_SIZE_H, COLLISIONTEST_PREVENTS_MOVEMENT
from OpenGL.GL import *
from OpenGL.arrays.vbo import VBO
from .pygame_oo.shader import Mat4, Vec4, Vec2
from .pygame_oo.game_shaders import GSHp
from .pygame_oo.window import Window
from .pygame_oo import logger
import numpy as np
from math import sqrt
from .spritesheet import Spritesheet
from .audio_data import Audio


class LightBolt(Object):
    exclude_from_object_editor = True
    velocity = 6
    saveable = False

    max_trail = 8
    expiry = 360
    vao = None
    vbo = None

    @classmethod
    def init_vao(cls):
        if cls.vao is None:
            cls.vao = glGenVertexArrays(1)
            cls.vbo = VBO(np.array([0, 0, 1, 0, 0, 1, 1, 1], dtype='f'))
            glBindVertexArray(cls.vao)
            cls.vbo.bind()
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, cls.vbo)
            glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 0, cls.vbo)
            glEnableVertexAttribArray(0)
            glEnableVertexAttribArray(1)
            glBindVertexArray(0)

    def __init__(self, screen, x=0, y=0, init_dict=None):
        LightBolt.init_vao()
        super().__init__(screen, x, y, init_dict)
        self.trail = []
        self.radius = 12.0
        self.color = Vec4(0, 0.8, 1.0, 1.0)
        self.mult = 8
        self.hitbox_w = 7
        self.hitbox_h = 7
        self.check_offset_x = 2
        self.check_offset_y = 2
        self.abort = False
        self.track = 0.04
        self.counter = LightBolt.expiry
        self.tvao = glGenVertexArrays(1)
        glBindVertexArray(self.tvao)
        glEnableVertexAttribArray(0)
        glEnableVertexAttribArray(1)
        glEnableVertexAttribArray(2)
        glBindVertexArray(0)

    def draw(self, wnd):
        ix = int(self.x)
        iy = int(self.y + self.hitbox_h)
        if not self.hidden:
            draw_x = ix + self._offset_x
            draw_y = iy + self._offset_y
            if len(self.trail) > 0:
                w = 4
                cx = self.x
                cy = wnd.height() - (self.y + 5)
                cnx = -self.vy
                cny = -self.vx
                v1c = [cx - cnx * w, cy - cny * w, cx + cnx * w, cy + cny * w]
                v2c = [-1.0, 1.0]
                v3c = [0.0, 0.0, 0.0, 0.0]
                for i in range(len(self.trail)):
                    p = self.trail[i]
                    cx = p[0]
                    cy = wnd.height() - (p[1] + 5)
                    cnx = p[2]
                    cny = -p[3]
                    if i < len(self.trail) - 1:
                        v1c.extend([cx - cnx * w, cy - cny * w, cx + cnx * w, cy + cny * w])
                    else:
                        v1c.extend([cx - cnx, cy - cny, cx + cnx, cy + cny])
                    v2c.extend([-1.0, 1.0])
                    v3c.extend([0.0, 0.0, 0.0, 0.0])
                vbo1 = VBO(np.array(v1c, dtype='f'))
                vbo2 = VBO(np.array(v2c, dtype='f'))
                vbo3 = VBO(np.array(v3c, dtype='f'))
                with GSHp('GSHP_light_trail') as prog:
                    wnd.setup_render(prog)

                    prog.uniform('color', self.color)
                    prog.uniform('model', Mat4())

                    wnd.fbo.bindtexunit(1)

                    glBindVertexArray(self.tvao)
                    vbo1.bind()
                    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, vbo1)
                    vbo2.bind()
                    glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, 0, vbo2)
                    vbo3.bind()
                    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 0, vbo3)
                    glDrawArrays(GL_TRIANGLE_STRIP, 0, len(self.trail) * 2 + 2)
                    glBindVertexArray(0)

            with GSHp('GSHP_light_spot') as prog:
                model = Mat4.scaling(25, 25) * Mat4.translation(draw_x - 12, Window.instance.h - (draw_y + 11))
                Window.instance.setup_render(prog)

                prog.uniform('color', self.color)
                prog.uniform('r', self.radius)
                prog.uniform('center', Vec2(draw_x, Window.instance.h - (draw_y)))
                prog.uniform('model', model)

                wnd.fbo.bindtexunit(1)

                glBindVertexArray(LightBolt.vao)
                glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
                logger.log_draw()
                glBindVertexArray(0)


    def cleanup_self(self):
        try:
            self.screen.objects.remove(self)
        except:
            pass
        self.abort = True

    def interact_player(self, ctrl):
        ctrl.player.die()

    def tick(self, scr, ctrl):
        if ctrl.current_screen != self.screen:
            self.cleanup_self()
            return
        self.trail.insert(0, (self.x, self.y, -self.vy, self.vx))
        if len(self.trail) > LightBolt.max_trail:
            del self.trail[LightBolt.max_trail:]
        dx = ctrl.player.x - self.x
        dy = ctrl.player.y - self.y
        dist = sqrt(dx * dx + dy * dy)
        if dist > 0:
            dx1 = dx / dist * self.track
            dy1 = dy / dist * self.track
            self.vx += dx1
            self.vy += dy1
            sdist = sqrt(self.vx * self.vx + self.vy * self.vy)
            self.vx /= sdist
            self.vy /= sdist
        for i in range(self.mult):
            self.x += self.vx
            self.y += self.vy
            if self.x < 0 or self.x > SCREEN_SIZE_W - 5 or self.y < 0 or self.y > SCREEN_SIZE_H - 5:
                self.cleanup_self()
                return
            ix = int(self.x)
            iy = int(self.y)
            self.screen.test_player_collision(ctrl, ix - 5, iy - 5, (11, 11), self)
            if self.abort:
                return
        self.counter -= 1
        if self.counter <= 0:
            self.cleanup_self()
            return

    def draw_as_hitbox(self, wnd, color):
        pass


class Channeler(Object):
    exclude_from_object_editor = False
    saveable = True
    fire_frames = 60
    object_name = "Channeler"
    editor_frame_size = (16, 27)

    def __init__(self, screen, x=0, y=0, init_dict=None):
        super().__init__(screen, x, y, init_dict)
        self._offset_x = -5
        self._offset_y = 0

        self.states = {
            "left": (False, (0, 0), "left"),
            "right": (False, (1, 0), "right"),
        }
        self.spritesheet = Spritesheet.spritesheets_byname["ss_object_channeler-24-48.png"]
        self.attachment1 = Spritesheet.spritesheets_byname["ss_object_trident-24-24.png"]
        self.state = "left"
        self.dv = [-1, 0]
        self.hitbox_w = 16
        self.hitbox_h = 27
        self.hitbox_type = CollisionTest.DEADLY
        self.counter = Channeler.fire_frames

    def tick(self, scr, ctrl):
        if ctrl.current_screen != self.screen:
            self.counter = Channeler.fire_frames
            return
        hmovement = 0
        vmovement = 0
        dx = ctrl.player.x - self.x
        dy = ctrl.player.y - self.y - 6
        dist = sqrt(sqrt(dx * dx + dy * dy))

        if ctrl.ckeys[ctrl.keybindings[Controls.LEFT]]:
            hmovement += -MOVEMENT_SPEED * dist
        if ctrl.ckeys[ctrl.keybindings[Controls.RIGHT]]:
            hmovement += MOVEMENT_SPEED * dist
        hmovement += ctrl.player.gravity_velocity[0] * dist
        vmovement += ctrl.player.gravity_velocity[1] * sqrt(dist)

        dx += hmovement
        dy += vmovement
        dist2 = sqrt(dx * dx + dy * dy)
        if dist2 > 0:
            self.dv[0], self.dv[1] = (dx / dist2, dy / dist2)
        else:
            self.dv[0], self.dv[1] = (1, 0)

        if self.dv[0] < 0:
            self.state = "left"
        else:
            self.state = "right"

        self.counter -= 1
        if self.counter <= 0:
            self.screen.objects.append(LightBolt(self.screen, self.x, self.y, {"vx": self.dv[0], "vy": self.dv[1]}))
            Audio.play_by_name("lightbolt.ogg")
            self.counter = Channeler.fire_frames

    def object_editor_draw(self, wnd):
        super().draw(wnd)

    def draw(self, wnd):
        super().draw(wnd)
        ix = int(self.x)
        iy = int(self.y + self.hitbox_h)
        if not self.hidden and self.spritesheet is not None and self._state in self.states:
            draw_x = ix + self._offset_x
            draw_y = iy + self._offset_y
            sa = self.dv[1] if self.dv[0] >= 0 else -self.dv[1]
            ca = self.dv[0] if self.dv[0] >= 0 else -self.dv[0]
            state = self.states[self._state]
            mt = Mat4.translation(-0.5, -0.5) * Mat4.rotation_sincos(sa, ca)
            self.attachment1.draw_cell_to(state[1][0], state[1][1], draw_x + 12, draw_y - 12, wnd.fbo, model_transform=mt)


class WheelingtonSpawner(Object):
    exclude_from_object_editor = False
    saveable = True
    object_name = "Wheelington Spawner"
    editor_frame_size = (20, 20)
    editor_properties = {
        "facing_right": (EPType.IntSelector, 0, 0, 1, 1),
    }

    def __init__(self, screen, x=0, y=0, init_dict=None):
        super().__init__(screen, x, y, init_dict)
        if init_dict is not None and "facing_right" in init_dict and init_dict["facing_right"] > 0:
            self.facing = 1
        else:
            self.facing = -1
        self.editor_wheel = None

    def draw(self, wnd):
        pass

    def draw_as_hitbox(self, wnd, color):
        pass

    def object_editor_draw(self, wnd):
        if self.editor_wheel is None:
            self.editor_wheel = Wheelington(None, self.x, self.y, {"facing": "right" if self.facing > 0 else "left"})
            self.editor_wheel.screen = self.screen
        self.editor_wheel.draw(wnd)

    def screen_trigger(self, ctrl):
        self.screen.objects.append(Wheelington(self.screen, self.x, self.y, {"facing": "right" if self.facing > 0 else "left"}))


class Wheelington(Object):
    exclude_from_object_editor = False
    audio_frames = 20
    saveable = True
    object_name = "Wheelington"
    editor_frame_size = (20, 20)

    def __init__(self, screen, x=0, y=0, init_dict=None):
        super().__init__(screen, x, y, init_dict)
        self._offset_x = -2
        self._offset_y = 0

        self.spritesheet = Spritesheet.spritesheets_byname["ss_skeletons-24-24.png"]
        self.states = {
            "left": (True, 0.1, [(4, 0), (5, 0), (6, 0), (7, 0)], True, "left"),
            "right": (True, 0.1, [(0, 0), (1, 0), (2, 0), (3, 0)], True, "right"),
        }
        if "facing" in init_dict:
            self.state = init_dict["facing"]
            self.vx = 3 if init_dict["facing"] == "right" else -3
        else:
            self.state = "right"
            self.vx = 3
        self.vy = 0
        self.hitbox_w = 20
        self.hitbox_h = 20
        self.hitbox_type = CollisionTest.DEADLY
        self.audio_counter = Wheelington.audio_frames
        self.abort = False

    def draw_as_hitbox(self, wnd, color):
        pass

    def cleanup_self(self):
        try:
            self.screen.objects.remove(self)
        except:
            pass
        self.abort = True

    def tick(self, scr, ctrl):
        if ctrl.current_screen != self.screen or self.abort:
            self.audio_counter = Wheelington.audio_frames
            return
        avx = -1 if self.vx < 0 else 1
        f = abs(self.vx)
        for i in range(f):
            need_check = True
            while need_check:
                coll1 = self.screen.test_screen_collision(int(self.x + 9), int(self.y + self.hitbox_h - 1), (2, 1))
                if coll1[4][0] & CollisionTest.DEADLY:
                    self.cleanup_self()
                    return
                if coll1[4][0] & COLLISIONTEST_PREVENTS_MOVEMENT:
                    self.y -= 1
                    continue
                if coll1[3][0] & COLLISIONTEST_PREVENTS_MOVEMENT:
                    self.vy = 0
                else:
                    self.vy += self.screen.gravity[1] / 9.0
                self.y += self.vy
                need_check = False
            coll2 = self.screen.test_screen_collision(int(self.x if avx < 0 else self.x + 19), int(self.y + 9), (1, 11))
            if coll2[0 if avx > 0 else 2][0] & COLLISIONTEST_PREVENTS_MOVEMENT:
                self.state = "right" if avx < 0 else "left"
                self.vx = -self.vx
                avx = -avx
            else:
                self.x += avx
            self.screen.test_player_collision_circle(ctrl, int(self.x + 10), int(self.y + 10), 10, self)
        self.audio_counter -= 1
        if self.audio_counter <= 0:
            Audio.play_by_name("wheelington.ogg")
            self.audio_counter = Wheelington.audio_frames

    def interact_player(self, ctrl):
        ctrl.player.die()
