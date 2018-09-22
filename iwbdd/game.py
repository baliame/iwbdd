from .world import World
from .player import Player
from .screen import CollisionTest
import pygame
from enum import IntEnum


def bound(v, m0, m1):
    if v < m1:
        if v < m0:
            return m0
        return v
    return m1


class Controls(IntEnum):
    LEFT = 0
    RIGHT = 1
    JUMP = 2
    SHOOT = 3


class Controller:
    instance = None
    terminal_velocity = 3
    default_keybindings = {
        Controls.LEFT: pygame.K_LEFT,
        Controls.RIGHT: pygame.K_RIGHT,
        Controls.JUMP: pygame.K_SPACE,
        Controls.SHOOT: pygame.K_a,
    }

    def __init__(self, main_loop):
        if Controller.instance is not None:
            raise RuntimeError("Editor must be a singleton.")
        Controller.instance = self

        self.worlds = []
        self.current_world = None
        self.current_screen = None
        self.keybindings = default_keybindings

        self.player = None

    def add_loaded_world(self, world):
        self.worlds.append(world)
        if self.current_world is None:
            self.current_world = world
            self.current_screen = self.current_world.screens[self.current_world.starting_screen_id]

    def load_world_from_file(self, world):
        loaded_world = World(world)
        self.worlds.append(loaded_world)
        if self.current_world is None:
            self.current_world = loaded_world
            self.current_screen = self.current_world.screens[self.current_world.starting_screen_id]

    def create_player(self):
        if self.player is None:
            self.player = Player()

    def simulate(self):
        if self.player.cached_collision is None:
            self.player.cached_collision = self.current_screen.test_terrain_collision(self.player.x, self.player.y, self.player.hitbox)
        cancel_dirs = []
        gx = self.current_screen.gravity[0]
        gy = self.current_screen.gravity[1]
        gv = self.player.gravity_velocity
        tv = Controller.terminal_velocity
        gv = (bound(gv[0] + gx, -tv, tv), bound(gv[1] + gy, -tv, tv))
        if gv[0] != 0:
            if gv[0] < 0:
                cancel_dirs.append(2)
            else:
                cancel_dirs.append(0)
        if gv[1] != 0:
            if gv[1] < 0:
                cancel_dirs.append(1)
            else:
                cancel_dirs.append(3)
        for el in cancel_dirs:
            if self.player.cached_collision[el][0] & CollisionTest.SOLID:
                if el in (0, 2):
                    gv[0] = 0
                else:
                    gv[1] = 0
        self.player.gravity_velocity = gv

        mvx = 0
        mvy = 0
        change_facing = 0
        keys = pygame.key.get_pressed()
        if keys[self.keybindings[Controls.LEFT]]:
            mvx += -1
            change_facing = -1
        if keys[self.keybindings[Controls.RIGHT]]:
            mvx += 1
            if change_facing == -1:
                change_facing = 0
            else:
                change_facing = 1
        self.player.movement_velocity = (mvx, mvy)

        if change_facing:
            if change_facing < 0:
                self.player.state = "moving_left"
            else:
                self.player.state = "moving_right"
        elif self.player.state != "stop_left" and self.player.state != "stop_right":
            if self.player.state == "moving_left":
                self.player.state = "stop_left"
            else:
                self.player.state = "stop_right"

        sumv = (gv[0] + mvx, gv[1] + mvy)
        player_pass = []
        dest = (self.player.x + sumv[0], self.player.y + sumv[1])
        cx = self.player.x
        cy = self.player.y
        sgnx = -1 if sumv[0] < 0 else 1
        sgny = -1 if sumv[1] < 0 else 1
        while True:
            nx = int(cx) + sgnx
            ny = int(cy) + sgny
            if sumv[0]:
                nxt = (nx - cx) / sumv[0]
            else:
                nxt = 2
            if sumv[1]:
                nyt = (ny - cy) / sumv[0]
            else:
                nyt = 2
            if nxt > 1 and nyt > 1:
                break
            elif nxt < nyt:
                pt = (nx, cy)
                cx = nx
            else:
                pt = (cx, ny)
                cy = ny
            coll = self.current_screen.test_terrain_collision(pt[0], pt[1], self.player.hitbox)

        player_pass.append(dest)

    @staticmethod
    def render_elements_callback(wnd):
        self = Controller.instance
        self.render_elements(wnd)

    def render_elements(self, wnd):
        if self.current_screen is not None:
            self.current_screen.render_to_window(wnd)
