from .background import Background
from .tileset import Tileset
from .screen import Screen, Collision, COLLISIONTEST_COLORS, CollisionTest
from .world import World
from .game import Controller
from .object import Object
from .common import mousebox
from enum import IntEnum
import pygame
from pygame.locals import K_f, K_m, K_r, K_s, K_x, K_n, K_LEFT, K_RIGHT, K_UP, K_DOWN, K_PAGEUP, K_PAGEDOWN, K_DELETE, K_RETURN, K_BACKSPACE, K_c, K_v, K_o, K_i


class _mousetev:
    def __init__(self, pos, button):
        self.pos = pos
        self.button = button


class EditingMode(IntEnum):
    MODE_SWITCH_ROLLOVER_DESTINATION = 0
    TERRAIN = 0
    COLLISION = 1
    SELECTION = 2
    OBJECTS = 3
    MODE_SWITCH_ROLLOVER = 4
    SIMULATION = 4
    FRAMEBYFRAME = 5


EditingModeLock = (EditingMode.SIMULATION, EditingMode.FRAMEBYFRAME)
SimulationModes = (EditingMode.SIMULATION, EditingMode.FRAMEBYFRAME)


class Editor:
    instance = None
    ts_view_w = 20
    ts_view_h = 10

    ts_display_x = 1080
    ts_display_y = 32
    tslx = 0
    tsty = 0
    tshx1 = 0
    tshx2 = 0
    tshy1 = 0
    tshy2 = 0
    tsrx = 0
    tsby = 0

    @staticmethod
    def calc():
        Editor.tslx = Editor.ts_display_x + 49
        Editor.tsty = Editor.ts_display_y + 1
        Editor.tshx1 = Editor.ts_display_x + 84
        Editor.tshx2 = Editor.ts_display_x + 85
        Editor.tshy1 = Editor.ts_display_y + 35
        Editor.tshy2 = Editor.ts_display_y + 36
        Editor.tsrx = Editor.ts_display_x + 118
        Editor.tsby = Editor.ts_display_y + 70

    key_mapping = {
        "reset_simulation": K_r,
        "frame_advance": K_f,
        "mode": K_m,
        "switch_to_simulation": K_s,
        "switch_to_frame_advance": K_f,
        "exit_simulation": K_x,
        "toggle_collision_render": K_m,
        "new_screen": K_n,
        "toolbox_left": K_LEFT,
        "toolbox_right": K_RIGHT,
        "toolbox_up": K_UP,
        "toolbox_down": K_DOWN,
        "next_screen": K_PAGEDOWN,
        "previous_screen": K_PAGEUP,
        "delete_screen": K_DELETE,
        "confirm_prompt": K_RETURN,
        "cancel_prompt": K_BACKSPACE,
        "sm_cut": K_x,
        "sm_copy": K_c,
        "sm_paste": K_v,
        "sm_fill_terrain": K_i,
        "sm_fill_collision": K_o,
    }
    mode_count = 2
    collision_editor_draw = {
        Collision.PASSABLE: lambda wnd: True,
        Collision.SOLID_TILE: lambda wnd: pygame.draw.rect(wnd.display, (0, 0, 255), pygame.Rect(Editor.tslx, Editor.tsty, 70, 70)),
        Collision.SOLID_HALF_DOWN: lambda wnd: pygame.draw.rect(wnd.display, (0, 0, 255), pygame.Rect(Editor.tslx, Editor.tshy1, 70, 36)),
        Collision.SOLID_HALF_UP: lambda wnd: pygame.draw.rect(wnd.display, (0, 0, 255), pygame.Rect(Editor.tslx, Editor.tsty, 70, 36)),
        Collision.SOLID_SLOPE_UPLEFT: lambda wnd: pygame.draw.polygon(wnd.display, (0, 0, 255), [(Editor.tslx, Editor.tsty), (Editor.tsrx, Editor.tsby), (Editor.tslx, Editor.tsby)]),
        Collision.SOLID_SLOPE_UPRIGHT: lambda wnd: pygame.draw.polygon(wnd.display, (0, 0, 255), [(Editor.tsrx, Editor.tsty), (Editor.tslx, Editor.tsby), (Editor.tsrx, Editor.tsby)]),
        Collision.DEADLY_TILE: lambda wnd: pygame.draw.rect(wnd.display, (255, 0, 0), pygame.Rect(Editor.tslx, Editor.tsty, 70, 70)),
        Collision.DEADLY_SPIKE_UP: lambda wnd: pygame.draw.polygon(wnd.display, (255, 0, 0), [(Editor.tslx, Editor.tsby), (Editor.tshx1, Editor.tsty), (Editor.tshx2, Editor.tsty), (Editor.tsrx, Editor.tsby)]),
        Collision.DEADLY_SPIKE_DOWN: lambda wnd: pygame.draw.polygon(wnd.display, (255, 0, 0), [(Editor.tslx, Editor.tsty), (Editor.tshx1, Editor.tsby), (Editor.tshx2, Editor.tsby), (Editor.tsrx, Editor.tsty)]),
        Collision.DEADLY_SPIKE_LEFT: lambda wnd: pygame.draw.polygon(wnd.display, (255, 0, 0), [(Editor.tslx, Editor.tsty), (Editor.tsrx, Editor.tshy1), (Editor.tsrx, Editor.tshy2), (Editor.tslx, Editor.tsby)]),
        Collision.DEADLY_SPIKE_RIGHT: lambda wnd: pygame.draw.polygon(wnd.display, (255, 0, 0), [(Editor.tsrx, Editor.tsty), (Editor.tslx, Editor.tshy1), (Editor.tslx, Editor.tshy2), (Editor.tsrx, Editor.tsby)]),
        Collision.SOLID_HALF_UP_DEADLY_HALF_DOWN: lambda wnd: pygame.draw.rect(wnd.display, (0, 0, 255), pygame.Rect(Editor.tslx, Editor.tsty, 70, 35)) and pygame.draw.rect(wnd.display, (255, 0, 0), pygame.Rect(Editor.tslx, Editor.tshy2, 70, 35)),
        Collision.SOLID_HALF_DOWN_DEADLY_HALF_UP: lambda wnd: pygame.draw.rect(wnd.display, (255, 0, 0), pygame.Rect(Editor.tslx, Editor.tsty, 70, 35)) and pygame.draw.rect(wnd.display, (0, 0, 255), pygame.Rect(Editor.tslx, Editor.tshy2, 70, 35)),
        Collision.SOLID_HALF_LEFT_DEADLY_HALF_RIGHT: lambda wnd: pygame.draw.rect(wnd.display, (0, 0, 255), pygame.Rect(Editor.tslx, Editor.tsty, 35, 70)) and pygame.draw.rect(wnd.display, (255, 0, 0), pygame.Rect(Editor.ts_display_x + 84, Editor.tsty, 35, 70)),
        Collision.SOLID_HALF_RIGHT_DEADLY_HALF_LEFT: lambda wnd: pygame.draw.rect(wnd.display, (255, 0, 0), pygame.Rect(Editor.tslx, Editor.tsty, 35, 70)) and pygame.draw.rect(wnd.display, (0, 0, 255), pygame.Rect(Editor.ts_display_x + 84, Editor.tsty, 35, 70)),
        Collision.CONVEYOR_EAST_SINGLE_SPEED: lambda wnd: pygame.draw.rect(wnd.display, COLLISIONTEST_COLORS[CollisionTest.CONVEYOR_EAST_SINGLE_SPEED], pygame.Rect(Editor.tslx, Editor.tsty, 70, 70)) and pygame.draw.polygon(wnd.display, COLLISIONTEST_COLORS[CollisionTest.SOLID], [(Editor.tslx + 4, Editor.tsty + 4), (Editor.tsrx - 4, Editor.tshy1), (Editor.tsrx - 4, Editor.tshy2), (Editor.tslx + 4, Editor.tsby - 4)]),
        Collision.CONVEYOR_NORTH_SINGLE_SPEED: lambda wnd: pygame.draw.rect(wnd.display, COLLISIONTEST_COLORS[CollisionTest.CONVEYOR_NORTH_SINGLE_SPEED], pygame.Rect(Editor.tslx, Editor.tsty, 70, 70)) and pygame.draw.polygon(wnd.display, COLLISIONTEST_COLORS[CollisionTest.SOLID], [(Editor.tslx + 4, Editor.tsby - 4), (Editor.tshx1, Editor.tsty + 4), (Editor.tshx2, Editor.tsty + 4), (Editor.tsrx - 4, Editor.tsby - 4)]),
        Collision.CONVEYOR_WEST_SINGLE_SPEED: lambda wnd: pygame.draw.rect(wnd.display, COLLISIONTEST_COLORS[CollisionTest.CONVEYOR_WEST_SINGLE_SPEED], pygame.Rect(Editor.tslx, Editor.tsty, 70, 70)) and pygame.draw.polygon(wnd.display, COLLISIONTEST_COLORS[CollisionTest.SOLID], [(Editor.tsrx - 4, Editor.tsty + 4), (Editor.tslx + 4, Editor.tshy1), (Editor.tslx + 4, Editor.tshy2), (Editor.tsrx - 4, Editor.tsby - 4)]),
        Collision.CONVEYOR_SOUTH_SINGLE_SPEED: lambda wnd: pygame.draw.rect(wnd.display, COLLISIONTEST_COLORS[CollisionTest.CONVEYOR_SOUTH_SINGLE_SPEED], pygame.Rect(Editor.tslx, Editor.tsty, 70, 70)) and pygame.draw.polygon(wnd.display, COLLISIONTEST_COLORS[CollisionTest.SOLID], [(Editor.tslx + 4, Editor.tsty + 4), (Editor.tshx1, Editor.tsby - 4), (Editor.tshx2, Editor.tsby - 4), (Editor.tsrx - 4, Editor.tsty + 4)]),
        Collision.SOLID_HALF_LEFT: lambda wnd: pygame.draw.rect(wnd.display, (0, 0, 255), pygame.Rect(Editor.tslx, Editor.tsty, 36, 70)),
        Collision.SOLID_HALF_RIGHT: lambda wnd: pygame.draw.rect(wnd.display, (0, 0, 255), pygame.Rect(Editor.tshx1, Editor.tsty, 36, 70)),
    }

    def __init__(self, world_file, main_loop):
        if Editor.instance is not None:
            raise RuntimeError("Editor must be a singleton.")
        Editor.instance = self
        Editor.calc()
        self.font = pygame.font.SysFont('Courier New', 12)

        main_loop.add_render_callback(Editor.render_elements_callback)
        main_loop.add_atexit_callback(Editor.atexit_callback)
        main_loop.set_mouse_button_handler(Editor.mousedown_callback)
        main_loop.set_mouse_button_up_handler(Editor.mouseup_callback)
        main_loop.set_mouse_motion_handler(Editor.mousemotion_callback)
        main_loop.set_keydown_handler(Editor.key_mapping["mode"], Editor.keydown_callback)
        main_loop.set_keydown_handler(Editor.key_mapping["switch_to_simulation"], Editor.keydown_callback)
        main_loop.set_keydown_handler(Editor.key_mapping["switch_to_frame_advance"], Editor.keydown_callback)
        main_loop.set_keydown_handler(Editor.key_mapping["exit_simulation"], Editor.keydown_callback)
        main_loop.set_keydown_handler(Editor.key_mapping["toggle_collision_render"], Editor.keydown_callback)
        main_loop.set_keydown_handler(Editor.key_mapping["frame_advance"], Editor.keydown_callback)
        main_loop.set_keydown_handler(Editor.key_mapping["reset_simulation"], Editor.keydown_callback)
        main_loop.set_keydown_handler(Editor.key_mapping["new_screen"], Editor.keydown_callback)
        main_loop.set_keydown_handler(Editor.key_mapping["toolbox_left"], Editor.keydown_callback)
        main_loop.set_keydown_handler(Editor.key_mapping["toolbox_right"], Editor.keydown_callback)
        main_loop.set_keydown_handler(Editor.key_mapping["toolbox_up"], Editor.keydown_callback)
        main_loop.set_keydown_handler(Editor.key_mapping["toolbox_down"], Editor.keydown_callback)
        main_loop.set_keydown_handler(Editor.key_mapping["next_screen"], Editor.keydown_callback)
        main_loop.set_keydown_handler(Editor.key_mapping["previous_screen"], Editor.keydown_callback)
        main_loop.set_keydown_handler(Editor.key_mapping["delete_screen"], Editor.keydown_callback)
        main_loop.set_keydown_handler(Editor.key_mapping["confirm_prompt"], Editor.keydown_callback)
        main_loop.set_keydown_handler(Editor.key_mapping["cancel_prompt"], Editor.keydown_callback)
        main_loop.set_keydown_handler(Editor.key_mapping["sm_cut"], Editor.keydown_callback)
        main_loop.set_keydown_handler(Editor.key_mapping["sm_copy"], Editor.keydown_callback)
        main_loop.set_keydown_handler(Editor.key_mapping["sm_paste"], Editor.keydown_callback)
        main_loop.set_keydown_handler(Editor.key_mapping["sm_fill_terrain"], Editor.keydown_callback)
        main_loop.set_keydown_handler(Editor.key_mapping["sm_fill_collision"], Editor.keydown_callback)

        self.main_loop = main_loop
        self.world_file = world_file
        self.bg_id_id = 0
        self.ts_id_id = 0
        self.ts_view_x = 0
        self.ts_view_y = 0
        self.ts_select_x = 0
        self.ts_select_y = 0
        self.last_click_x = 0
        self.last_click_y = 0
        self.editing_mode = EditingMode.TERRAIN
        self.point_selection_callback = None
        self.prompt_callback = None
        self.prompt_message = None
        self.locked = {
            1: False,
            2: False,
            3: False,
        }
        self.collision_editor = 0
        self.screen_seg = main_loop.segment_window(0, 0, Screen.SCREEN_SIZE_W, Screen.SCREEN_SIZE_H)

        self.sm_selection_1 = None
        self.sm_selection_2 = None
        self.sm_holding = False
        self.sm_base_point = None
        self.sm_render_collisions = False
        self.sm_clipboard = None
        self.render_cache = {}
        self.build_render_cache()

        self.objed_selection = None if Object.object_editor_items is None else Object.object_editor_items[0]

        try:
            fh = open(world_file, 'rb')
            fh.close()
            self.edited_world = World(world_file)
            max_sid = 1
            first_sid = -1
            self.screens = []
            for k, v in self.edited_world.screens.items():
                if first_sid == -1:
                    first_sid = v.screen_id
                if v.screen_id > max_sid:
                    max_sid = v.screen_id
                self.screens.append(v)
            self.next_screen_id = max_sid + 1
            self.tileset = self.edited_world.tileset
            TL = list(Tileset.tilesets)
            for i in range(len(TL)):
                if Tileset.tilesets[TL[i]] is self.tileset:
                    self.ts_id_id = i

            if first_sid == -1:
                self.create_new_screen()
                self.edited_world.starting_screen_id = list(self.edited_world.screens)[0]
                self.apply_background()
            else:
                self.edited_screen = self.edited_world.screens[first_sid]
                self.background = self.edited_screen.background
                BG = list(Tileset.tilesets)
                for i in range(len(BG)):
                    if Tileset.tilesets[BG[i]] is self.tileset:
                        self.bg_id_id = i
        except FileNotFoundError:
            self.edited_world = World()
            self.background = Background.backgrounds[list(Background.backgrounds)[self.bg_id_id]]
            self.tileset = Tileset.tilesets[list(Tileset.tilesets)[self.ts_id_id]]
            self.next_screen_id = 1
            self.screens = []
            self.apply_tileset()
            self.create_new_screen()
            self.edited_world.starting_screen_id = list(self.edited_world.screens)[0]
            self.apply_background()

        self.controller = Controller(main_loop)
        self.controller.suspended = True
        self.controller.add_loaded_world(self.edited_world)
        self.controller.create_player()

    def apply_tileset(self):
        self.edited_world.tileset = self.tileset

    def apply_background(self):
        self.edited_screen.background = self.background

    def create_new_screen(self):
        self.edited_screen = Screen(self.edited_world)
        self.edited_screen.screen_id = self.next_screen_id
        self.next_screen_id += 1
        self.screens.append(self.edited_screen)
        self.edited_world.screens[self.edited_screen.screen_id] = self.edited_screen

    def build_render_cache(self):
        passive_color = (128, 128, 128)
        active_color = (255, 255, 255)
        self.render_cache = {
            "mode": self.font.render("Mode:", True, (255, 255, 255), 0),
            "terrain-active": self.font.render("Terrain", True, active_color, 0),
            "terrain-passive": self.font.render("Terrain", True, passive_color, 0),
            "collision-active": self.font.render("Collision", True, active_color, 0),
            "collision-passive": self.font.render("Collision", True, passive_color, 0),
            "selection-active": self.font.render("Selection", True, active_color, 0),
            "selection-passive": self.font.render("Selection", True, passive_color, 0),
            "objects-active": self.font.render("Objects", True, active_color, 0),
            "objects-passive": self.font.render("Objects", True, passive_color, 0),
            "simulation-active": self.font.render("Simulation", True, active_color, 0),
            "simulation-passive": self.font.render("Simulation", True, passive_color, 0),
            "framebyframe-active": self.font.render("Frame-by-frame", True, active_color, 0),
            "framebyframe-passive": self.font.render("Frame-by-frame", True, passive_color, 0),
            "coll-NONE": self.font.render("NONE", True, (255, 255, 255), 0),
            "coll-SOLID": self.font.render("SOLID", True, (0, 0, 255), 0),
            "coll-DEADLY": self.font.render("DEADLY", True, (255, 0, 0), 0),
            "coll-CONVEYOR": self.font.render("CONVEYOR", True, (0, 128, 0), 0),
            "sel-cut-active": self.font.render("[Cut] (X)", True, active_color, 0),
            "sel-cut-passive": self.font.render("[Cut] (X)", True, passive_color, 0),
            "sel-copy-active": self.font.render("[Copy] (C)", True, active_color, 0),
            "sel-copy-passive": self.font.render("[Copy] (C)", True, passive_color, 0),
            "sel-fillt-active": self.font.render("[Fill with terrain] (I)", True, active_color, 0),
            "sel-fillt-passive": self.font.render("[Fill with terrain] (I)", True, passive_color, 0),
            "sel-fillc-active": self.font.render("[Fill with collision] (O)", True, active_color, 0),
            "sel-fillc-passive": self.font.render("[Fill with collision] (O)", True, passive_color, 0),
            "sel-resett-active": self.font.render("[Reset terrain]", True, active_color, 0),
            "sel-resett-passive": self.font.render("[Reset terrain]", True, passive_color, 0),
            "sel-resetc-active": self.font.render("[Reset collision]", True, active_color, 0),
            "sel-resetc-passive": self.font.render("[Reset collision]", True, passive_color, 0),
            "sel-paste-active": self.font.render("[Paste] (V)", True, active_color, 0),
            "sel-paste-passive": self.font.render("[Paste] (V)", True, passive_color, 0),
            "rac-active": self.font.render("[Render as collisions]", True, active_color, 0),
            "rac-passive": self.font.render("[Render as collisions]", True, passive_color, 0),
            "dec": self.font.render("[-]", True, (255, 255, 255), 0),
            "inc": self.font.render("[+]", True, (255, 255, 255), 0),
            "selectpt": self.font.render("[Select]", True, (255, 255, 255), 0),
        }

    @staticmethod
    def render_elements_callback(wnd):
        self = Editor.instance
        self.render_elements(wnd)

    def render_elements(self, wnd):
        wnd.display.blit(self.render_cache["mode"], (1440, 320))
        passive_color = (128, 128, 128)
        active_color = (255, 255, 255)
        wnd.display.blit(self.render_cache["terrain-active"] if self.editing_mode == EditingMode.TERRAIN else self.render_cache["terrain-passive"], (1500, 320))
        wnd.display.blit(self.render_cache["collision-active"] if self.editing_mode == EditingMode.COLLISION else self.render_cache["collision-passive"], (1500, 340))
        wnd.display.blit(self.render_cache["selection-active"] if self.editing_mode == EditingMode.SELECTION else self.render_cache["selection-passive"], (1500, 360))
        wnd.display.blit(self.render_cache["objects-active"] if self.editing_mode == EditingMode.OBJECTS else self.render_cache["objects-passive"], (1500, 380))
        pygame.draw.line(wnd.display, passive_color, (1500, 396), (1580, 396))
        wnd.display.blit(self.render_cache["simulation-active"] if self.editing_mode == EditingMode.SIMULATION else self.render_cache["simulation-passive"], (1500, 400))
        wnd.display.blit(self.render_cache["framebyframe-active"] if self.editing_mode == EditingMode.FRAMEBYFRAME else self.render_cache["framebyframe-passive"], (1500, 420))

        save_now_text = self.font.render("[Save now]", True, active_color, 0)
        wnd.display.blit(save_now_text, (1500, 728))

        fps = self.main_loop.fps()
        fpst = "{0}-fps".format(fps)
        if fpst in self.render_cache:
            fps_text = self.render_cache[fpst]
        else:
            fps_text = self.font.render("{0} FPS".format(self.main_loop.fps()), True, active_color, 0)
            self.render_cache[fpst] = fps_text
        wnd.display.blit(fps_text, (1540, 748))

        if self.editing_mode not in EditingModeLock:
            self.edited_screen.render_to_window(self.screen_seg)
            if self.editing_mode == EditingMode.TERRAIN:
                pygame.draw.rect(wnd.display, (255, 255, 255), pygame.Rect(Editor.ts_display_x - 1, Editor.ts_display_y - 1, Editor.ts_view_w * Tileset.TILE_W + 2, Editor.ts_view_h * Tileset.TILE_H + 2))
                self.tileset.draw_to(self.ts_view_x, self.ts_view_y, Editor.ts_view_w, Editor.ts_view_h, wnd.display, (Editor.ts_display_x, Editor.ts_display_y))
                if self.ts_select_x >= self.ts_view_x and self.ts_select_y >= self.ts_view_y and self.ts_select_x < self.ts_view_x + Editor.ts_view_w and self.ts_select_y < self.ts_view_y + Editor.ts_view_h:
                    tile_id_x = self.ts_select_x - self.ts_view_x
                    tile_id_y = self.ts_select_y - self.ts_view_y
                    dest = pygame.Rect(Editor.ts_display_x + tile_id_x * Tileset.TILE_W, Editor.ts_display_y + tile_id_y * Tileset.TILE_H, Tileset.TILE_W, Tileset.TILE_H)
                    pygame.draw.rect(wnd.display, (255, 0, 0), dest, 1)
            elif self.editing_mode == EditingMode.COLLISION:
                self.edited_screen.render_collisions_to_window(self.screen_seg)
                wnd.display.blit(self.render_cache["coll-NONE"], (Editor.ts_display_x, Editor.ts_display_y))
                wnd.display.blit(self.render_cache["coll-SOLID"], (Editor.ts_display_x, Editor.ts_display_y + 16))
                wnd.display.blit(self.render_cache["coll-DEADLY"], (Editor.ts_display_x, Editor.ts_display_y + 32))
                wnd.display.blit(self.render_cache["coll-CONVEYOR"], (Editor.ts_display_x, Editor.ts_display_y + 48))

                pygame.draw.polygon(wnd.display, (255, 255, 255), [(Editor.ts_display_x + 48, Editor.ts_display_y + 84), (Editor.ts_display_x + 64, Editor.ts_display_y + 76), (Editor.ts_display_x + 64, Editor.ts_display_y + 92)])
                pygame.draw.polygon(wnd.display, (255, 255, 255), [(Editor.ts_display_x + 120, Editor.ts_display_y + 84), (Editor.ts_display_x + 104, Editor.ts_display_y + 76), (Editor.ts_display_x + 104, Editor.ts_display_y + 92)])

                pygame.draw.rect(wnd.display, (255, 255, 255), pygame.Rect(Editor.ts_display_x + 48, Editor.ts_display_y, 72, 72))
                c = Collision(self.collision_editor)
                if Collision(self.collision_editor) in Editor.collision_editor_draw:
                    Editor.collision_editor_draw[c](wnd)
            elif self.editing_mode == EditingMode.SELECTION:
                if self.sm_render_collisions:
                    self.edited_screen.render_collisions_to_window(self.screen_seg)
                if self.sm_selection_1 is not None and self.sm_selection_2 is not None:
                    select_1_text = self.font.render("TL: ({0}, {1})".format(self.sm_selection_1[0], self.sm_selection_1[1]), True, (255, 255, 255), 0)
                    select_2_text = self.font.render("BR: ({0}, {1})".format(self.sm_selection_2[0], self.sm_selection_2[1]), True, (255, 255, 255), 0)
                    wnd.display.blit(select_1_text, (Editor.ts_display_x + 300, Editor.ts_display_y))
                    wnd.display.blit(select_2_text, (Editor.ts_display_x + 300, Editor.ts_display_y + 20))
                    w = (self.sm_selection_2[0] - self.sm_selection_1[0] + 1) * Tileset.TILE_W
                    h = (self.sm_selection_2[1] - self.sm_selection_1[1] + 1) * Tileset.TILE_H
                    pygame.draw.rect(self.screen_seg.display, (255, 0, 0), pygame.Rect(self.sm_selection_1[0] * Tileset.TILE_W, self.sm_selection_1[1] * Tileset.TILE_H, w, h), 1)
                wnd.display.blit(self.render_cache["rac-active"] if self.sm_render_collisions else self.render_cache["rac-passive"], (Editor.ts_display_x, Editor.ts_display_y))
                has_selection = self.sm_selection_1 is not None and self.sm_selection_2 is not None
                wnd.display.blit(self.render_cache["sel-cut-active"] if has_selection else self.render_cache["sel-cut-passive"], (Editor.ts_display_x, Editor.ts_display_y + 20))
                wnd.display.blit(self.render_cache["sel-copy-active"] if has_selection else self.render_cache["sel-copy-passive"], (Editor.ts_display_x, Editor.ts_display_y + 40))
                wnd.display.blit(self.render_cache["sel-fillt-active"] if has_selection else self.render_cache["sel-fillt-passive"], (Editor.ts_display_x, Editor.ts_display_y + 60))
                wnd.display.blit(self.tileset.image_surface, (Editor.ts_display_x - 20, Editor.ts_display_y + 58), pygame.Rect(self.ts_select_x * Tileset.TILE_W, self.ts_select_y * Tileset.TILE_H, Tileset.TILE_W, Tileset.TILE_H))
                wnd.display.blit(self.render_cache["sel-fillc-active"] if has_selection else self.render_cache["sel-fillc-passive"], (Editor.ts_display_x, Editor.ts_display_y + 80))
                Screen.collision_overlays[self.collision_editor](wnd.display, Editor.ts_display_x - 20, Editor.ts_display_y + 78)
                wnd.display.blit(self.render_cache["sel-resett-active"] if has_selection else self.render_cache["sel-resett-passive"], (Editor.ts_display_x, Editor.ts_display_y + 100))
                wnd.display.blit(self.render_cache["sel-resetc-active"] if has_selection else self.render_cache["sel-resetc-passive"], (Editor.ts_display_x, Editor.ts_display_y + 120))
                wnd.display.blit(self.render_cache["sel-paste-active"] if self.sm_clipboard is not None else self.render_cache["sel-paste-passive"], (Editor.ts_display_x, Editor.ts_display_y + 140))
            elif self.editing_mode == EditingMode.OBJECTS:
                if self.objed_selection is None:
                    no_way_text = self.font.render("No placable objects exist.", True, (255, 0, 0), 0)
                    wnd.display.blit(no_way_text, (Editor.ts_display_x, Editor.ts_display_y))
                else:
                    object_name_text = self.font.render("Creating new: {0}".format(self.objed_selection.object_name), True, (255, 255, 255), 0)
                    wnd.display.blit(object_name_text, (Editor.ts_display_x, Editor.ts_display_y))
                    self.objed_selection.render_editor_properties(wnd.display, self.font, Editor.ts_display_x, Editor.ts_display_y + 40, self.render_cache)
            if self.edited_world.starting_screen_id == self.edited_screen.screen_id:
                self.controller.player.x = self.edited_world.start_x
                self.controller.player.y = self.edited_world.start_y
                if self.editing_mode == EditingMode.TERRAIN:
                    self.controller.player.draw(self.screen_seg)
                elif self.editing_mode == EditingMode.COLLISION:
                    self.controller.player.draw_as_hitbox(self.screen_seg, (0, 255, 0))

            scr_id_text = self.font.render("Screen id: {0}".format(self.edited_screen.screen_id), True, (255, 255, 255), 0)
            wnd.display.blit(scr_id_text, (1080, 320))
            e_tr = self.edited_screen.transitions[0]
            e_tr_text = self.font.render("East transition: {0}".format("solid" if e_tr == 0 else e_tr), True, (255, 255, 255), 0)
            dec_text = self.render_cache["dec"]
            inc_text = self.render_cache["inc"]
            wnd.display.blit(e_tr_text, (1080, 340))
            wnd.display.blit(dec_text, (1270, 340))
            wnd.display.blit(inc_text, (1290, 340))
            n_tr = self.edited_screen.transitions[1]
            n_tr_text = self.font.render("North transition: {0}".format("solid" if n_tr == 0 else n_tr), True, (255, 255, 255), 0)
            wnd.display.blit(n_tr_text, (1080, 360))
            wnd.display.blit(dec_text, (1270, 360))
            wnd.display.blit(inc_text, (1290, 360))
            w_tr = self.edited_screen.transitions[2]
            w_tr_text = self.font.render("West transition: {0}".format("solid" if w_tr == 0 else w_tr), True, (255, 255, 255), 0)
            wnd.display.blit(w_tr_text, (1080, 380))
            wnd.display.blit(dec_text, (1270, 380))
            wnd.display.blit(inc_text, (1290, 380))
            s_tr = self.edited_screen.transitions[3]
            s_tr_text = self.font.render("South transition: {0}".format("solid" if s_tr == 0 else s_tr), True, (255, 255, 255), 0)
            wnd.display.blit(s_tr_text, (1080, 400))
            wnd.display.blit(dec_text, (1270, 400))
            wnd.display.blit(inc_text, (1290, 400))
            grav_x_text = self.font.render("Gravity X: {0:.2f}".format(self.edited_screen.gravity[0]), True, (255, 255, 255), 0)
            wnd.display.blit(grav_x_text, (1080, 420))
            wnd.display.blit(dec_text, (1270, 420))
            wnd.display.blit(inc_text, (1290, 420))
            grav_y_text = self.font.render("Gravity Y: {0:.2f}".format(self.edited_screen.gravity[1]), True, (255, 255, 255), 0)
            wnd.display.blit(grav_y_text, (1080, 440))
            wnd.display.blit(dec_text, (1270, 440))
            wnd.display.blit(inc_text, (1290, 440))
            jump_frames = self.font.render("Jump strength: {0}".format(self.edited_screen.jump_frames), True, (255, 255, 255), 0)
            wnd.display.blit(jump_frames, (1080, 460))
            wnd.display.blit(dec_text, (1270, 460))
            wnd.display.blit(inc_text, (1290, 460))
            # lc_text = self.font.render("({0}, {1})".format(self.last_click_x, self.last_click_y), True, (255, 255, 255), 0)
            # wnd.display.blit(lc_text, (1080, 420))

            wscr_id_text = self.font.render("World starting screen: {0}".format(self.edited_world.starting_screen_id), True, (255, 255, 255), 0)
            wnd.display.blit(wscr_id_text, (1080, 500))
            use_curr_text = self.font.render("[Use current]", True, (255, 255, 255), 0)
            wnd.display.blit(use_curr_text, (1080, 520))

            if self.prompt_message is not None:
                prompt_1_text = self.font.render(self.prompt_message, True, (0, 255, 0), 0)
                wnd.display.blit(prompt_1_text, (1300, 500))
            if self.prompt_callback is not None:
                prompt_2_text = self.font.render("RETURN to confirm, BACKSPACE to cancel", True, (255, 255, 255), 0)
                wnd.display.blit(prompt_2_text, (1300, 520))

            if self.edited_world.starting_screen_id == self.edited_screen.screen_id:
                select_start_text = self.font.render("[Select start location]", True, (255, 255, 255), 0)
                wnd.display.blit(select_start_text, (1080, 540))

            if self.point_selection_callback is not None:
                selecting_text = self.font.render("Select point on map (right click to cancel)...", True, (0, 255, 0), 0)
                wnd.display.blit(selecting_text, (1080, 8))

            self.background.draw_to(160, 120, wnd.display, (1080, 640))
        else:
            if self.editing_mode == EditingMode.SIMULATION or self.editing_mode == EditingMode.FRAMEBYFRAME:
                self.controller.render_elements(self.screen_seg)
                wnd.display.blit(self.render_cache["rac-active"] if self.controller.render_collisions else self.render_cache["rac-passive"], (Editor.ts_display_x, Editor.ts_display_y))

    def sm_to_clipboard(self):
        self.sm_clipboard = [[(0, 0, 0) for x in range(self.sm_selection_1[0], self.sm_selection_2[0] + 1)] for y in range(self.sm_selection_1[1], self.sm_selection_2[1] + 1)]
        for x in range(self.sm_selection_1[0], self.sm_selection_2[0] + 1):
            for y in range(self.sm_selection_1[1], self.sm_selection_2[1] + 1):
                cx = x - self.sm_selection_1[0]
                cy = y - self.sm_selection_1[1]
                tile = self.edited_screen.tiles[y][x]
                self.sm_clipboard[cy][cx] = (tile[0], tile[1], tile[2])

    def sm_cut(self):
        self.sm_to_clipboard()
        self.sm_terrain_reset()
        self.sm_collision_reset()

    def sm_paste(self):
        if self.sm_selection_1[0] == self.sm_selection_2[0] and self.sm_selection_1[1] == self.sm_selection_2[1]:
            xti = len(self.sm_clipboard[0])
            yti = len(self.sm_clipboard)
        else:
            xti = min(self.sm_selection_2[0] - self.sm_selection_1[0] + 1, len(self.sm_clipboard[0]))
            yti = min(self.sm_selection_2[1] - self.sm_selection_1[1] + 1, len(self.sm_clipboard))
        for yo in range(yti):
            for xo in range(xti):
                try:
                    wx = self.sm_selection_1[0] + xo
                    wy = self.sm_selection_1[1] + yo
                    src_tile = self.sm_clipboard[yo][xo]
                    self.edited_screen.tiles[wy][wx] = (src_tile[0], src_tile[1], src_tile[2])
                except IndexError:
                    pass
        self.edited_screen.dirty = True
        self.edited_screen.dirty_collisions = True

    def sm_terrain_fill(self):
        for x in range(self.sm_selection_1[0], self.sm_selection_2[0] + 1):
            for y in range(self.sm_selection_1[1], self.sm_selection_2[1] + 1):
                tile = self.edited_screen.tiles[y][x]
                self.edited_screen.tiles[y][x] = (self.ts_select_x, self.ts_select_y, tile[2])
        self.edited_screen.dirty = True

    def sm_collision_fill(self):
        for x in range(self.sm_selection_1[0], self.sm_selection_2[0] + 1):
            for y in range(self.sm_selection_1[1], self.sm_selection_2[1] + 1):
                tile = self.edited_screen.tiles[y][x]
                self.edited_screen.tiles[y][x] = (tile[0], tile[1], self.collision_editor)
        self.edited_screen.dirty_collisions = True

    def sm_terrain_reset(self):
        for x in range(self.sm_selection_1[0], self.sm_selection_2[0] + 1):
            for y in range(self.sm_selection_1[1], self.sm_selection_2[1] + 1):
                tile = self.edited_screen.tiles[y][x]
                self.edited_screen.tiles[y][x] = (0, 0, tile[2])
        self.edited_screen.dirty = True

    def sm_collision_reset(self):
        for x in range(self.sm_selection_1[0], self.sm_selection_2[0] + 1):
            for y in range(self.sm_selection_1[1], self.sm_selection_2[1] + 1):
                tile = self.edited_screen.tiles[y][x]
                self.edited_screen.tiles[y][x] = (tile[0], tile[1], 0)
        self.edited_screen.dirty_collisions = True

    @staticmethod
    def mousedown_callback(event, ml):
        self = Editor.instance
        self.mousedown(event, ml)

    def exit_simulation_if_needed(self):
        if self.editing_mode == EditingMode.SIMULATION or self.editing_mode == EditingMode.FRAMEBYFRAME:
            self.controller.reset_from_editor(self)
            if self.editing_mode == EditingMode.FRAMEBYFRAME:
                self.main_loop.suspend_ticking = False

    def start_simulation(self):
        if self.editing_mode == EditingMode.SIMULATION or self.editing_mode == EditingMode.FRAMEBYFRAME:
            self.controller.start_from_editor(self)
            if self.editing_mode == EditingMode.FRAMEBYFRAME:
                self.main_loop.suspend_ticking = True

    def mousedown(self, event, ml):
        if event.button != 1 and event.button != 3:
            return
        self.last_click_x = event.pos[0]
        self.last_click_y = event.pos[1]
        if self.prompt_callback is not None:
            return
        if event.pos[0] >= 1500:
            if event.pos[1] >= 320:
                if event.pos[1] < 340:
                    self.exit_simulation_if_needed()
                    self.change_mode(EditingMode.TERRAIN)
                    return
                elif event.pos[1] < 360:
                    self.exit_simulation_if_needed()
                    self.change_mode(EditingMode.COLLISION)
                    return
                elif event.pos[1] < 380:
                    self.exit_simulation_if_needed()
                    self.change_mode(EditingMode.SELECTION)
                    return
                elif event.pos[1] < 397:
                    self.exit_simulation_if_needed()
                    self.change_mode(EditingMode.OBJECTS)
                    return
                elif event.pos[1] < 420:
                    if self.editing_mode not in SimulationModes:
                        self.exit_simulation_if_needed()
                        self.change_mode(EditingMode.SIMULATION)
                        self.start_simulation()
                    else:
                        self.change_mode(EditingMode.SIMULATION)
                        self.main_loop.suspend_ticking = False
                    return
                elif event.pos[1] < 440:
                    if self.editing_mode not in SimulationModes:
                        self.exit_simulation_if_needed()
                        self.change_mode(EditingMode.FRAMEBYFRAME)
                        self.start_simulation()
                    else:
                        self.change_mode(EditingMode.FRAMEBYFRAME)
                        self.main_loop.suspend_ticking = True
                    return
        if self.editing_mode not in EditingModeLock:
            if self.point_selection_callback is not None and event.button == 3:
                self.point_selection_callback = None
                return
            if event.pos[0] >= Screen.SCREEN_SIZE_W and event.button == 1:
                if self.editing_mode == EditingMode.TERRAIN:
                    if mousebox(event.pos[0], event.pos[1], Editor.ts_display_x, Editor.ts_display_y, Editor.ts_view_w * Tileset.TILE_W, Editor.ts_view_h * Tileset.TILE_H):
                        tx = int((event.pos[0] - Editor.ts_display_x) / Tileset.TILE_W) + self.ts_view_x
                        ty = int((event.pos[1] - Editor.ts_display_y) / Tileset.TILE_H) + self.ts_view_y
                        if tx < self.tileset.tiles_w and ty < self.tileset.tiles_h:
                            self.ts_select_x = tx
                            self.ts_select_y = ty
                elif self.editing_mode == EditingMode.COLLISION:
                    if not self.locked[1]:
                        if mousebox(event.pos[0], event.pos[1], Editor.ts_display_x + 48, Editor.ts_display_y + 76, 16, 16):
                            self.collision_editor -= 1
                            if self.collision_editor < 0:
                                self.collision_editor = Collision.COLLISION_TYPE_COUNT - 1
                            self.locked[1] = True
                        elif mousebox(event.pos[0], event.pos[1], Editor.ts_display_x + 104, Editor.ts_display_y + 76, 16, 16):
                            self.collision_editor += 1
                            if self.collision_editor >= Collision.COLLISION_TYPE_COUNT:
                                self.collision_editor = 0
                            self.locked[1] = True
                elif self.editing_mode == EditingMode.SELECTION and not self.locked[1]:
                    if mousebox(event.pos[0], event.pos[1], Editor.ts_display_x, Editor.ts_display_y, 200, 160):
                        self.locked[1] = True
                        has_selection = self.sm_selection_1 is not None and self.sm_selection_2 is not None
                        if event.pos[1] < Editor.ts_display_y + 20:
                            self.sm_render_collisions = not self.sm_render_collisions
                        elif event.pos[1] < Editor.ts_display_y + 40:
                            if has_selection:
                                self.sm_cut()
                        elif event.pos[1] < Editor.ts_display_y + 60:
                            if has_selection:
                                self.sm_to_clipboard()
                        elif event.pos[1] < Editor.ts_display_y + 80:
                            if has_selection:
                                self.sm_terrain_fill()
                        elif event.pos[1] < Editor.ts_display_y + 100:
                            if has_selection:
                                self.sm_collision_fill()
                        elif event.pos[1] < Editor.ts_display_y + 120:
                            if has_selection:
                                self.sm_terrain_reset()
                        elif event.pos[1] < Editor.ts_display_y + 140:
                            if has_selection:
                                self.sm_collision_reset()
                        elif event.pos[1] < Editor.ts_display_y + 160:
                            if self.sm_clipboard is not None:
                                self.sm_paste()
                elif self.editing_mode == EditingMode.OBJECTS and not self.locked[1]:
                    if self.objed_selection is not None and mousebox(event.pos[0], event.pos[1], Editor.ts_display_x, Editor.ts_display_y, 400, 240):
                        if self.objed_selection.check_object_editor_click(self, event.pos[0], event.pos[1], Editor.ts_display_x, Editor.ts_display_y + 40):
                            self.locked[1] = True
                if not self.locked[1]:
                    if mousebox(event.pos[0], event.pos[1], 1500, 728, 100, 20):
                        self.locked[1] = True
                        self.atexit(self.main_loop)
                    elif mousebox(event.pos[0], event.pos[1], 1080, 520, 100, 20):
                        self.locked[1] = True
                        self.edited_world.starting_screen_id = self.edited_screen.screen_id
                    elif mousebox(event.pos[0], event.pos[1], 1270, 340, 40, 80):
                        self.locked[1] = True
                        if event.pos[1] < 380:
                            if event.pos[0] < 1290:
                                if event.pos[1] < 360:
                                    self.dec_transition(0)
                                else:
                                    self.dec_transition(1)
                            else:
                                if event.pos[1] < 360:
                                    self.inc_transition(0)
                                else:
                                    self.inc_transition(1)
                        else:
                            if event.pos[0] < 1290:
                                if event.pos[1] >= 400:
                                    self.dec_transition(3)
                                else:
                                    self.dec_transition(2)
                            else:
                                if event.pos[1] >= 400:
                                    self.inc_transition(3)
                                else:
                                    self.inc_transition(2)
                    elif mousebox(event.pos[0], event.pos[1], 1270, 420, 40, 40):
                        self.locked[1] = True
                        if event.pos[0] < 1290:
                            if event.pos[1] < 440:
                                grav_x = self.edited_screen.gravity[0]
                                grav_y = self.edited_screen.gravity[1]
                                self.edited_screen.gravity = (grav_x - 0.01, grav_y)
                            else:
                                grav_x = self.edited_screen.gravity[0]
                                grav_y = self.edited_screen.gravity[1]
                                self.edited_screen.gravity = (grav_x, grav_y - 0.01)
                        else:
                            if event.pos[1] < 440:
                                grav_x = self.edited_screen.gravity[0]
                                grav_y = self.edited_screen.gravity[1]
                                self.edited_screen.gravity = (grav_x + 0.01, grav_y)
                            else:
                                grav_x = self.edited_screen.gravity[0]
                                grav_y = self.edited_screen.gravity[1]
                                self.edited_screen.gravity = (grav_x, grav_y + 0.01)
                    elif mousebox(event.pos[0], event.pos[1], 1270, 460, 40, 20):
                        self.locked[1] = True
                        if event.pos[0] < 1290:
                            if self.edited_screen.jump_frames > 0:
                                self.edited_screen.jump_frames -= 1
                        else:
                            self.edited_screen.jump_frames += 1
                    elif self.edited_world.starting_screen_id == self.edited_screen.screen_id and mousebox(event.pos[0], event.pos[1], 1080, 540, 180, 20):
                        self.locked[1] = True
                        self.point_selection_callback = self.set_start_coordinates
            elif event.pos[0] < Screen.SCREEN_SIZE_W:
                if self.point_selection_callback is not None and event.button == 1:
                    self.point_selection_callback(event.pos[0], event.pos[1])
                    self.point_selection_callback = None
                    return
                sctx = int(event.pos[0] / Tileset.TILE_W)
                scty = int(event.pos[1] / Tileset.TILE_H)
                tile = self.edited_screen.tiles[scty][sctx]
                if self.editing_mode == EditingMode.SELECTION:
                    if event.button == 3:
                        self.sm_selection_1 = None
                        self.sm_selection_2 = None
                        self.sm_base_point = None
                        self.sm_holding = False
                    elif event.button == 1:
                        if not self.sm_holding:
                            self.sm_holding = True
                            self.sm_base_point = (sctx, scty)
                            self.sm_selection_1 = (sctx, scty)
                            self.sm_selection_2 = (sctx, scty)
                        else:
                            xmin = min(sctx, self.sm_base_point[0])
                            xmax = max(sctx, self.sm_base_point[0])
                            ymin = min(scty, self.sm_base_point[1])
                            ymax = max(scty, self.sm_base_point[1])
                            self.sm_selection_1 = (xmin, ymin)
                            self.sm_selection_2 = (xmax, ymax)
                if self.editing_mode == EditingMode.TERRAIN:
                    if event.button == 1:
                        self.edited_screen.tiles[scty][sctx] = (self.ts_select_x, self.ts_select_y, tile[2])
                    elif event.button == 3:
                        self.edited_screen.tiles[scty][sctx] = (0, 0, tile[2])
                    self.edited_screen.dirty = True
                elif self.editing_mode == EditingMode.COLLISION:
                    if event.button == 1:
                        self.edited_screen.tiles[scty][sctx] = (tile[0], tile[1], self.collision_editor)
                    elif event.button == 3:
                        self.edited_screen.tiles[scty][sctx] = (tile[0], tile[1], 0)
                    self.edited_screen.dirty_collisions = True
        else:
            if self.editing_mode == EditingMode.SIMULATION or self.editing_mode == EditingMode.FRAMEBYFRAME and not self.locked[0]:
                if mousebox(event.pos[0], event.pos[1], Editor.ts_display_x, Editor.ts_display_y, 100, 20):
                    self.controller.render_collisions = not self.controller.render_collisions
                    self.locked[0] = True

    def set_start_coordinates(self, x, y):
        self.edited_world.start_x = x
        self.edited_world.start_y = y
        self.controller.reset_from_editor(self)

    def dec_transition(self, idx):
        tup = list(self.edited_screen.transitions)
        t_id = tup[idx]
        keys = list(self.edited_world.screens)
        if t_id == 0:
            t_id = keys[len(keys) - 1]
        elif t_id == keys[0]:
            t_id = 0
        else:
            for i in range(len(keys)):
                if keys[i] == t_id:
                    t_id = keys[i - 1]
                    break
        tup[idx] = t_id
        self.edited_screen.transitions = tuple(tup)

    def inc_transition(self, idx):
        tup = list(self.edited_screen.transitions)
        t_id = tup[idx]
        keys = list(self.edited_world.screens)
        if t_id == keys[len(keys) - 1]:
            t_id = 0
        elif t_id == 0:
            t_id = keys[0]
        else:
            for i in range(len(keys)):
                if keys[i] == t_id:
                    t_id = keys[i + 1]
                    break
        tup[idx] = t_id
        self.edited_screen.transitions = tuple(tup)

    @staticmethod
    def mouseup_callback(event, ml):
        self = Editor.instance
        self.mouseup(event, ml)

    def mouseup(self, event, ml):
        if self.sm_holding:
            self.sm_holding = False
            self.sm_base_point = None
        self.locked[event.button] = False

    @staticmethod
    def mousemotion_callback(event, ml):
        self = Editor.instance
        self.mousemotion(event, ml)

    def mousemotion(self, event, ml):
        if event.buttons[0]:
            if event.pos[0] < Screen.SCREEN_SIZE_W and self.editing_mode == EditingMode.SELECTION and not self.sm_holding:
                return
            self.mousedown(_mousetev(event.pos, 1), ml)
        if event.buttons[2]:
            self.mousedown(_mousetev(event.pos, 3), ml)

    @staticmethod
    def atexit_callback(ml):
        self = Editor.instance
        self.atexit(ml)

    def atexit(self, ml):
        self.edited_world.write_to(self.world_file)

    @staticmethod
    def keydown_callback(event, ml):
        self = Editor.instance
        self.keydown(event, ml)

    def keydown(self, event, ml):
        if self.prompt_callback is not None:
            if event.key == Editor.key_mapping["confirm_prompt"]:
                self.prompt_message = None
                self.prompt_callback()
                self.prompt_callback = None
            elif event.key == Editor.key_mapping["cancel_prompt"]:
                self.prompt_callback = None
                self.prompt_message = "Cancelled."
            return
        if self.editing_mode != EditingMode.SIMULATION and event.key == Editor.key_mapping["switch_to_simulation"]:
            if self.editing_mode == EditingMode.FRAMEBYFRAME:
                self.change_mode(EditingMode.SIMULATION)
                self.main_loop.suspend_ticking = False
            else:
                self.exit_simulation_if_needed()
                self.change_mode(EditingMode.SIMULATION)
                self.start_simulation()
        elif self.editing_mode != EditingMode.FRAMEBYFRAME and event.key == Editor.key_mapping["switch_to_frame_advance"]:
            if self.editing_mode == EditingMode.SIMULATION:
                self.change_mode(EditingMode.FRAMEBYFRAME)
                self.main_loop.suspend_ticking = True
            else:
                self.exit_simulation_if_needed()
                self.change_mode(EditingMode.FRAMEBYFRAME)
                self.start_simulation()
        elif self.editing_mode == EditingMode.SIMULATION or self.editing_mode == EditingMode.FRAMEBYFRAME:
            if event.key == Editor.key_mapping["reset_simulation"]:
                self.exit_simulation_if_needed()
                self.start_simulation()
            elif self.editing_mode == EditingMode.FRAMEBYFRAME and event.key == Editor.key_mapping["frame_advance"]:
                self.controller.simulate()
            elif event.key == Editor.key_mapping["exit_simulation"]:
                self.exit_simulation_if_needed()
                self.change_mode(EditingMode.COLLISION if self.controller.render_collisions else EditingMode.TERRAIN)
            elif event.key == Editor.key_mapping["toggle_collision_render"]:
                self.controller.render_collisions = not self.controller.render_collisions
            return
        elif event.key == Editor.key_mapping["mode"]:
            self.change_mode(-1)
        elif event.key == Editor.key_mapping["new_screen"]:
            self.create_new_screen()
            self.apply_background()
        elif event.key == Editor.key_mapping["toolbox_left"]:
            if self.editing_mode == EditingMode.TERRAIN:
                if self.ts_select_x > 0:
                    self.ts_select_x -= 1
            elif self.editing_mode == EditingMode.COLLISION:
                self.collision_editor -= 1
                if self.collision_editor < 0:
                    self.collision_editor = Collision.COLLISION_TYPE_COUNT - 1
        elif event.key == Editor.key_mapping["toolbox_right"]:
            if self.editing_mode == EditingMode.TERRAIN:
                if self.ts_select_x < self.tileset.tiles_w - 1:
                    self.ts_select_x += 1
            elif self.editing_mode == EditingMode.COLLISION:
                self.collision_editor += 1
                if self.collision_editor >= Collision.COLLISION_TYPE_COUNT:
                    self.collision_editor = 0
        elif event.key == Editor.key_mapping["toolbox_left"]:
            if self.editing_mode == EditingMode.TERRAIN:
                if self.ts_select_y > 0:
                    self.ts_select_y -= 1
        elif event.key == Editor.key_mapping["toolbox_right"]:
            if self.editing_mode == EditingMode.TERRAIN:
                if self.ts_select_y < self.tileset.tiles_h - 1:
                    self.ts_select_y += 1
        elif event.key == Editor.key_mapping["next_screen"]:
            keys = list(self.edited_world.screens)
            for i in range(len(keys)):
                if keys[i] == self.edited_screen.screen_id:
                    if i != len(keys) - 1:
                        self.edited_screen = self.edited_world.screens[keys[i + 1]]
                        break
        elif event.key == Editor.key_mapping["previous_screen"]:
            keys = list(self.edited_world.screens)
            for i in range(len(keys)):
                if keys[i] == self.edited_screen.screen_id:
                    if i != 0:
                        self.edited_screen = self.edited_world.screens[keys[i - 1]]
                        break
        elif event.key == Editor.key_mapping["delete_screen"]:
            if len(self.edited_world.screens) <= 1:
                self.prompt_message = "Cannot delete the only screen in a world."
                return
            else:
                self.prompt_callback = self.delete_current_screen
                self.prompt_message = "Delete screen ID {0}?".format(self.edited_screen.screen_id)
        elif self.editing_mode == EditingMode.SELECTION:
            has_selection = self.sm_selection_1 is not None and self.sm_selection_2 is not None
            if event.key == Editor.key_mapping["sm_cut"]:
                if has_selection:
                    self.sm_cut()
            elif event.key == Editor.key_mapping["sm_copy"]:
                if has_selection:
                    self.sm_to_clipboard()
            elif event.key == Editor.key_mapping["sm_fill_terrain"]:
                if has_selection:
                    self.sm_terrain_fill()
            elif event.key == Editor.key_mapping["sm_fill_collision"]:
                if has_selection:
                    self.sm_collision_fill()
            elif event.key == Editor.key_mapping["sm_paste"]:
                if self.sm_clipboard is not None:
                    self.sm_paste()

    def delete_current_screen(self):
        self.edited_world.screens.pop(self.edited_screen.screen_id)
        for k, scr in self.edited_world.screens.items():
            tr = list(scr.transitions)
            for i in range(len(tr)):
                if tr[i] == self.edited_screen.screen_id:
                    tr[i] = 0
            scr.transitions = tuple(tr)
        if self.edited_world.starting_screen_id == self.edited_screen.screen_id:
            self.edited_world.starting_screen_id = list(self.edited_world.screens)[0]
        self.prompt_message = "Deleted screen ID {0}".format(self.edited_screen.screen_id)
        self.edited_screen = self.edited_world.screens[self.edited_world.starting_screen_id]
        self.prompt_callback = None

    def change_mode(self, which):
        self.prompt_callback = None
        self.point_selection_callback = None
        if which == -1:
            if self.editing_mode >= EditingMode.MODE_SWITCH_ROLLOVER:
                return
            else:
                which = self.editing_mode + 1
                if which >= EditingMode.MODE_SWITCH_ROLLOVER:
                    which = EditingMode.MODE_SWITCH_ROLLOVER_DESTINATION
        if which == self.editing_mode:
            return
        if self.editing_mode == EditingMode.SELECTION:
            self.sm_base_point = None
            self.sm_holding = False
        self.editing_mode = which
