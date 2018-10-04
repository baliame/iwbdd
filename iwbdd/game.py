from .world import World
from .player import Player
from .screen import CollisionTest, COLLISIONTEST_PREVENTS_MOVEMENT, COLLISIONTEST_PREVENTS_SIDE_GRAVITY, COLLISIONTEST_TRANSITIONS, Screen
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
    RESET = 4


# 4 tiles = 96 px
# 1 jump ~ 2 tiles
# full 2 jumps ~ 4.1 tiles
# v0 = ?, vt = 0
# g = 0.2
# v0 = -0.2 * t
# s = 50
# v0 * t + g/2 * t^2 = -50
# -0.2t^2 + 0.1t^2 = -50
# -0.1t^2 = -50
# t^2 = 500
# t = 22.36f
# v0 = 0.2*22.36 = 4.47

def sgnor0(v):
    if v == 0:
        return 0
    return -1 if v < 0 else 1


class Controller:
    instance = None
    # terminal_velocity = 4.4
    # terminal_velocity = 3.3
    terminal_velocity = 7.47
    jump_velocity = -7.2
    doublejump_strength = 0.8
    default_keybindings = {
        Controls.LEFT: pygame.K_LEFT,
        Controls.RIGHT: pygame.K_RIGHT,
        Controls.JUMP: pygame.K_SPACE,
        Controls.SHOOT: pygame.K_a,
        Controls.RESET: pygame.K_r,
    }
    movement_speed = 2

    def __init__(self, main_loop):
        if Controller.instance is not None:
            raise RuntimeError("Editor must be a singleton.")
        Controller.instance = self

        self.worlds = []
        self.current_world = None
        self.current_screen = None
        self.keybindings = Controller.default_keybindings.copy()
        self.keybindings_lookup = {}
        for ctrl in list(self.keybindings):
            self.keybindings_lookup[self.keybindings[ctrl]] = ctrl
        self.suspended = False
        self.render_collisions = False

        self.player = None
        main_loop.add_ticker(self)
        self.ml = main_loop

    def add_loaded_world(self, world):
        self.worlds.append(world)
        if self.current_world is None:
            self.current_world = world
            self.current_screen = self.current_world.screens[self.current_world.starting_screen_id]
            if self.player is not None:
                self.player.x = self.current_world.start_x
                self.player.y = self.current_world.start_y
                self.current_screen.objects.append(self.player)
                self.player.screen = self.current_screen

    def load_world_from_file(self, world):
        loaded_world = World(world)
        self.worlds.append(loaded_world)
        if self.current_world is None:
            self.current_world = loaded_world
            self.current_screen = self.current_world.screens[self.current_world.starting_screen_id]
            if self.player is not None:
                self.player.x = self.current_world.start_x
                self.player.y = self.current_world.start_y
                self.current_screen.objects.append(self.player)
                self.player.screen = self.current_screen

    def create_player(self):
        if self.player is None:
            self.player = Player()
            if self.current_world is not None:
                self.player.x = self.current_world.start_x
                self.player.y = self.current_world.start_y
                self.current_screen.objects.append(self.player)
            self.player.screen = self.current_screen

    def reset_from_editor(self, editor):
        self.player.reset()
        self.current_screen.objects.remove(self.player)
        self.current_world = editor.edited_world
        self.current_screen = self.current_world.screens[self.current_world.starting_screen_id]
        self.player.screen = self.current_screen
        self.player.x = self.current_world.start_x
        self.player.y = self.current_world.start_y
        self.current_screen.objects.append(self.player)
        self.suspended = True

    def start_from_editor(self, editor):
        self.suspended = False

    # TODO: Save states
    def reset_to_save(self):
        self.player.reset()
        self.current_screen.objects.remove(self.player)
        self.current_screen = self.current_world.screens[self.current_world.starting_screen_id]
        self.player.screen = self.current_screen
        self.player.x = self.current_world.start_x
        self.player.y = self.current_world.start_y
        self.current_screen.objects.append(self.player)

    def transition(self, id):
        self.current_screen.objects.remove(self.player)
        self.current_screen = self.current_world.screens[self.current_screen.transitions[id]]
        if id == 0:
            self.player.x = 0
        elif id == 1:
            self.player.y = Screen.SCREEN_SIZE_H - len(self.player.hitbox)
        elif id == 2:
            self.player.x = Screen.SCREEN_SIZE_W - len(self.player.hitbox[0])
        elif id == 3:
            self.player.y = 0
        self.current_screen.objects.append(self.player)

    def simulate(self):
        if self.suspended:
            return
        if self.player.dead:
            return
        self.current_screen.generate_object_collisions()
        # print("==== Running simulation for frame")
        if self.player.cached_collision is None:
            self.player.cached_collision = self.current_screen.test_screen_collision(int(self.player.x), int(self.player.y), self.player.hitbox)
            # print("Checking initial collision at {0} {1} - result: {2}".format(int(self.player.x), int(self.player.y), self.player.cached_collision))
        if self.player.cached_collision[4][0] & CollisionTest.DEADLY:
            self.player.die()
            self.player.cached_collision = None
            return
        if self.player.cached_collision[4][0] & COLLISIONTEST_PREVENTS_MOVEMENT:
            self.player.y -= 1
            self.player.cached_collision = None
            # print("Frame failed: player overlapping solid object")
            return
        if self.player.cached_collision[4][0] & COLLISIONTEST_TRANSITIONS:
            if self.player.cached_collision[4][0] & CollisionTest.TRANSITION_EAST and self.current_screen.transitions[0]:
                self.transition(0)
                self.player.cached_collision = None
                return
            elif self.player.cached_collision[4][0] & CollisionTest.TRANSITION_NORTH and self.current_screen.transitions[1]:
                self.transition(1)
                self.player.cached_collision = None
                return
            elif self.player.cached_collision[4][0] & CollisionTest.TRANSITION_WEST and self.current_screen.transitions[2]:
                self.transition(2)
                self.player.cached_collision = None
                return
            elif self.player.cached_collision[4][0] & CollisionTest.TRANSITION_SOUTH and self.current_screen.transitions[3]:
                self.transition(3)
                self.player.cached_collision = None
                return
            else:
                print("BUG: Collision flag {0} but no valid transition in direction(s)".format(self.player.cached_collision[4][0]))
        cancel_dirs = []
        grav_dirs = []
        gx = self.current_screen.gravity[0]
        gy = self.current_screen.gravity[1]
        gv = self.player.gravity_velocity
        tv = Controller.terminal_velocity
        prevent_doublejump = False
        # gv = [bound(gv[0] + gx, -tv if gx < 0 else -2 * tv, tv if gx > 0 else 2 * tv), bound(gv[1] + gy, -tv if gy < 0 else -2 * tv, tv if gy > 0 else 2 * tv)]
        if gx != 0:
            if gx < 0:
                grav_dirs.append(2)
            else:
                grav_dirs.append(0)
        if gy != 0:
            if gy < 0:
                grav_dirs.append(1)
            else:
                grav_dirs.append(3)
        jump_available = False
        if self.player.cached_collision[0][0] & COLLISIONTEST_PREVENTS_SIDE_GRAVITY or self.player.cached_collision[2][0] & COLLISIONTEST_PREVENTS_SIDE_GRAVITY:
            gv = [0, 0]
            prevent_doublejump = True
            self.player.jumping = False
        else:
            gv = [bound(gv[0] + gx, -tv, tv), bound(gv[1] + gy, -tv, tv)]
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
                if self.player.cached_collision[el][0] & COLLISIONTEST_PREVENTS_MOVEMENT:
                    if el in (0, 2):
                        gv[0] = 0
                    else:
                        gv[1] = 0
        for el in grav_dirs:
            if self.player.cached_collision[el][0] & COLLISIONTEST_PREVENTS_MOVEMENT:
                jump_available = True
                if self.player.doublejump_available < 1:
                    self.player.doublejump_available = 1
                self.player.jumping = False

        # if gx:
        #    tgvrx = tv / gx
        # else:
        #     tgvrx = 0

        # if gy:
        #     tgvry = tv / gy
        # else:
        #     tgvry = 0

        mvx = 0
        mvy = 0
        change_facing = 0
        keys = pygame.key.get_pressed()
        if keys[self.keybindings[Controls.LEFT]]:
            mvx += -Controller.movement_speed
            change_facing = -1
        if keys[self.keybindings[Controls.RIGHT]]:
            mvx += Controller.movement_speed
            if change_facing == -1:
                change_facing = 0
            else:
                change_facing = 1
        if keys[self.keybindings[Controls.JUMP]]:
            if not self.player.jump_held:
                self.player.jump_held = True
                if jump_available:
                    # gv[0] += tgvrx * -gx
                    # gv[1] += tgvry * -gy
                    gv[0] += Controller.jump_velocity * sgnor0(gx)
                    gv[1] += Controller.jump_velocity * sgnor0(gy)
                    self.player.jumping = True
                elif self.player.doublejump_available > 0 and not prevent_doublejump:
                    if gx:
                        if (gv[0] < 0 and gx < 0) or (gv[0] > 0 and gx > 0):
                            gv[0] = 0
                    if gy:
                        if (gv[1] < 0 and gy < 0) or (gv[1] > 0 and gy > 0):
                            gv[1] = 0
                    # gv[0] += tgvrx * -gx * Controller.doublejump_strength
                    # gv[1] += tgvry * -gy * Controller.doublejump_strength
                    gv[0] += Controller.jump_velocity * sgnor0(gx) * Controller.doublejump_strength
                    gv[1] += Controller.jump_velocity * sgnor0(gy) * Controller.doublejump_strength
                    self.player.jumping = True
                    self.player.doublejump_available -= 1
        else:
            if self.player.jump_held:
                self.player.jump_held = False
                if self.player.jumping:
                    self.player.jumping = False
                    if gx:
                        if (gv[0] < 0 and gx > 0) or (gv[0] > 0 and gx < 0):
                            gv[0] = 0
                    if gy:
                        if (gv[1] < 0 and gy > 0) or (gv[1] > 0 and gy < 0):
                            gv[1] = 0

        self.player.gravity_velocity = gv
        self.player.movement_velocity = [mvx, mvy]

        conveyor_velocity = [0, 0]
        if self.player.cached_collision[0][0] & CollisionTest.CONVEYOR_NORTH_SINGLE_SPEED or self.player.cached_collision[2][0] & CollisionTest.CONVEYOR_NORTH_SINGLE_SPEED:
            conveyor_velocity[1] += -Controller.movement_speed * 0.75
        if self.player.cached_collision[0][0] & CollisionTest.CONVEYOR_SOUTH_SINGLE_SPEED or self.player.cached_collision[2][0] & CollisionTest.CONVEYOR_SOUTH_SINGLE_SPEED:
            conveyor_velocity[1] += Controller.movement_speed * 0.75
        if self.player.cached_collision[3][0] & CollisionTest.CONVEYOR_WEST_SINGLE_SPEED:
            conveyor_velocity[0] += -Controller.movement_speed * 0.75
        if self.player.cached_collision[3][0] & CollisionTest.CONVEYOR_EAST_SINGLE_SPEED:
            conveyor_velocity[0] += Controller.movement_speed * 0.75

        if change_facing:
            if change_facing < 0:
                if self.player.state != "moving_left":
                    self.player.state = "moving_left"
            else:
                if self.player.state != "moving_right":
                    self.player.state = "moving_right"
        elif self.player.state != "stop_left" and self.player.state != "stop_right":
            if self.player.state == "moving_left":
                self.player.state = "stop_left"
            else:
                self.player.state = "stop_right"

        sumv = (gv[0] + mvx + conveyor_velocity[0], gv[1] + mvy + conveyor_velocity[1])
        dest = [self.player.x + sumv[0], self.player.y + sumv[1]]
        cx = self.player.x
        cy = self.player.y
        sgnx = -1 if sumv[0] < 0 else 1
        sgny = -1 if sumv[1] < 0 else 1
        prevent_y = False
        if not sumv[1] or self.player.cached_collision[1 if sgny < 0 else 3][0] & COLLISIONTEST_PREVENTS_MOVEMENT:
            prevent_y = True
            dest[1] = self.player.y
        prevent_x = False
        sloping = 0
        if sumv[0]:
            xdir = 2 if sgnx < 0 else 0
            if self.player.cached_collision[xdir][0] & COLLISIONTEST_PREVENTS_MOVEMENT:
                if self.player.cached_collision[xdir][1] != 1 or self.player.cached_collision[xdir][2] not in (0, self.player.bottom_pixel) or (self.player.cached_collision[1][0] & COLLISIONTEST_PREVENTS_MOVEMENT and self.player.cached_collision[xdir][2] == self.player.bottom_pixel) or (self.player.cached_collision[3][0] & COLLISIONTEST_PREVENTS_MOVEMENT and self.player.cached_collision[xdir][2] == 0):
                    prevent_x = True
                    dest[0] = self.player.x
                elif self.player.cached_collision[xdir][2] == self.player.bottom_pixel and not self.player.cached_collision[1][0] & COLLISIONTEST_PREVENTS_MOVEMENT:
                    sloping = -1
                elif self.player.cached_collision[xdir][2] == 0 and not self.player.cached_collision[3][0] & COLLISIONTEST_PREVENTS_MOVEMENT:
                    sloping = 1
                else:
                    prevent_x = True
                    dest[0] = self.player.x
        else:
            prevent_x = True
            dest[0] = self.player.x
        acc_tx = 0
        acc_ty = 0
        while True:
            # print("=== Running iteration of discrete simulation [current location: {0} {1}]".format(cx, cy))
            nx = int(cx) + sgnx
            ny = int(cy) + sgny
            if sumv[0] and not prevent_x:
                nxt = acc_tx + (nx - cx) / sumv[0]
            else:
                nxt = 2
            if sumv[1] and not prevent_y:
                nyt = acc_ty + (ny - cy) / sumv[1]
            else:
                nyt = 2
            if (nxt > 1 or prevent_x) and (nyt > 1 or prevent_y):
                break
            elif nxt <= nyt and not prevent_x:
                if sloping:
                    cy += sloping
                    dest[1] += sloping
                pt = (nx, int(cy))
                cx = nx
                acc_tx = nxt
            elif not prevent_y:
                pt = (int(cx), ny)
                cy = ny
                acc_ty = nyt
            else:
                break
            coll = self.current_screen.test_screen_collision(pt[0], pt[1], self.player.hitbox)
            overlap = coll[4][0]
            if overlap & CollisionTest.DEADLY:
                self.player.die()
                return
            # print("Checking collision at {0} {1} - result: {2}".format(pt[0], pt[1], coll))
            # if coll[3][0] & COLLISIONTEST_PREVENTS_MOVEMENT:
            #     print("Next iteration will overlap with terrain.")
            # if overlap & COLLISIONTEST_PREVENTS_MOVEMENT:
            #     print("Detected overlap of terrain.")
            xdir = coll[2 if sgnx < 0 else 0]
            ydir = coll[1 if sgny < 0 else 3]
            if not prevent_y and ydir[0] & COLLISIONTEST_PREVENTS_MOVEMENT:
                prevent_y = True
                dest[1] = pt[1]
            if not prevent_x and xdir[0] & COLLISIONTEST_PREVENTS_MOVEMENT:
                if xdir[1] != 1 or xdir[2] not in (0, self.player.bottom_pixel) or (coll[1][0] & COLLISIONTEST_PREVENTS_MOVEMENT and xdir[2] == self.player.bottom_pixel) or (coll[3][0] & COLLISIONTEST_PREVENTS_MOVEMENT and xdir[2] == 0):
                    prevent_x = True
                    dest[0] = pt[0]
                    sloping = 0
                elif xdir[2] == self.player.bottom_pixel and not coll[1][0] & COLLISIONTEST_PREVENTS_MOVEMENT:
                    sloping = -1
                elif xdir[2] == 0 and not coll[3][0] & COLLISIONTEST_PREVENTS_MOVEMENT:
                    sloping = 1
                else:
                    prevent_x = True
                    dest[0] = pt[0]
            else:
                sloping = 0
            self.player.x = pt[0]
            self.player.y = pt[1]
        self.player.x = dest[0]
        self.player.y = dest[1]
        self.player.cached_collision = None

    @staticmethod
    def render_elements_callback(wnd):
        self = Controller.instance
        self.render_elements(wnd)

    def render_elements(self, wnd):
        if self.current_screen is not None:
            self.current_screen.render_to_window(wnd)
            if self.render_collisions:
                self.current_screen.render_collisions_to_window(wnd)
            if not self.render_collisions:
                self.current_screen.render_objects(wnd)
            else:
                self.current_screen.render_objects_hitboxes(wnd)

    def keydown_handler(self, event, ml):
        if event.key in self.keybindings_lookup:
            ctrl = self.keybindings_lookup[event.key]
            if ctrl == Controls.RESET:
                self.reset_to_save()

    def use_as_main_renderer(self):
        self.ml.add_render_callback(Controller.render_elements_callback)

    def use_as_main_keyhandler(self):
        self.ml.set_blanket_keydown_handler(self.keydown_handler)

    def __call__(self, ml):
        self.simulate()
