from collections import OrderedDict
from .background import Background
from .tileset import Tileset
from .screen import Screen, Collision, Layer, LayerNames
from .world import World
from .game import Controller
from .object import Object
from .pygame_oo.font import Font
from .pygame_oo.graphics import Graphics
from .common import mousebox, CollisionTest, SCREEN_SIZE_W, SCREEN_SIZE_H, COLLISIONTEST_COLORS
from .audio_data import Audio
from .bossfight import Boss
from enum import IntEnum
import glfw
from OpenGL.GL import *


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
    OBJECT_LIST = 4
    BOSS = 5
    MODE_SWITCH_ROLLOVER = 6
    SIMULATION = 6
    FRAMEBYFRAME = 7


EditingModeLock = (EditingMode.SIMULATION, EditingMode.FRAMEBYFRAME)
SimulationModes = (EditingMode.SIMULATION, EditingMode.FRAMEBYFRAME)

LayerLabels = OrderedDict({
    Layer.FOREGROUND: "FG ",
    Layer.BACKGROUND_1: "BG1",
    Layer.BACKGROUND_2: "BG2",
})


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
        "reset_simulation": glfw.KEY_Q,
        "reset_simulation_to_save": glfw.KEY_R,
        "frame_advance": glfw.KEY_F,
        "mode": glfw.KEY_M,
        "switch_to_simulation": glfw.KEY_S,
        "switch_to_frame_advance": glfw.KEY_F,
        "exit_simulation": glfw.KEY_X,
        "toggle_collision_render": glfw.KEY_M,
        "new_screen": glfw.KEY_N,
        "toolbox_left": glfw.KEY_LEFT,
        "toolbox_right": glfw.KEY_RIGHT,
        "toolbox_up": glfw.KEY_UP,
        "toolbox_down": glfw.KEY_DOWN,
        "next_screen": glfw.KEY_PAGE_DOWN,
        "previous_screen": glfw.KEY_PAGE_UP,
        "delete_screen": glfw.KEY_DELETE,
        "confirm_prompt": glfw.KEY_ENTER,
        "cancel_prompt": glfw.KEY_BACKSPACE,
        "sm_cut": glfw.KEY_X,
        "sm_copy": glfw.KEY_C,
        "sm_paste": glfw.KEY_V,
        "sm_fill_terrain": glfw.KEY_I,
        "sm_fill_collision": glfw.KEY_O,
    }
    mode_count = 2

    def __init__(self, world_file, main_loop):
        if Editor.instance is not None:
            raise RuntimeError("Editor must be a singleton.")
        Editor.instance = self
        self.graphics = Graphics(main_loop.window)
        self.font = Font(main_loop.window, "cour.ttf")
        Editor.calc()

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
        main_loop.set_keydown_handler(Editor.key_mapping["reset_simulation_to_save"], Editor.keydown_callback)
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
        self.terrain_layer = 0
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
        self.hide_objects_in_terrain_modes = False
        self.only_render_current_layer = False

        self.sm_selection_1 = None
        self.sm_selection_2 = None
        self.sm_holding = False
        self.sm_base_point = None
        self.sm_render_collisions = False
        self.sm_clipboard = None
        self.render_cache = {}
        self.build_render_cache()

        self.objed_selection = None if Object.object_editor_items is None else Object.object_editor_items[0]
        self.objlist_selection_idx = None

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

        if self.edited_world.background_music is None:
            self.edited_world.background_music = Audio.audio_by_name[list(Audio.audio_by_name)[0]]

        self.controller = Controller(main_loop, editor_control=True)
        self.controller.suspended = True
        self.controller.add_loaded_world(self.edited_world)
        self.controller.create_player()

    def initialize_bossfight(self):
        self.edited_world.bossfight_spec = (list(Boss.available_bosses)[0], list(self.edited_world.screens)[0], 0, 0)

    def prev_boss_class(self):
        bc = self.edited_world.bossfight_spec[0]
        blist = list(Boss.available_bosses)
        bidx = blist.index(bc)
        bidx -= 1
        if bidx < 0:
            bidx = len(blist) - 1
        bl = list(self.edited_world.bossfight_spec)
        bl[0] = blist[bidx]
        self.edited_world.bossfight_spec = tuple(bl)

    def next_boss_class(self):
        bc = self.edited_world.bossfight_spec[0]
        blist = list(Boss.available_bosses)
        bidx = blist.index(bc)
        bidx += 1
        if bidx >= len(blist):
            bidx = 0
        bl = list(self.edited_world.bossfight_spec)
        bl[0] = blist[bidx]
        self.edited_world.bossfight_spec = tuple(bl)

    def set_bossfight_coords(self, x, y):
        bl = list(self.edited_world.bossfight_spec)
        bl[2] = x
        bl[3] = y
        self.edited_world.bossfight_spec = tuple(bl)

    def prev_music(self):
        audio_name = self.edited_world.background_music.audio_name
        alist = list(Audio.audio_by_name)
        aidx = alist.index(audio_name)
        aidx -= 1
        if aidx < 0:
            aidx = len(alist) - 1
        self.edited_world.background_music = Audio.audio_by_name[alist[aidx]]

    def next_music(self):
        audio_name = self.edited_world.background_music.audio_name
        alist = list(Audio.audio_by_name)
        aidx = alist.index(audio_name)
        aidx += 1
        if aidx >= len(alist):
            aidx = 0
        self.edited_world.background_music = Audio.audio_by_name[alist[aidx]]

    def prev_tileset(self):
        ts = self.edited_world.tileset.tileset_id
        tlist = list(Tileset.tilesets)
        tidx = tlist.index(ts)
        tidx -= 1
        if tidx < 0:
            tidx = len(tlist) - 1
        self.ts_id_id = tidx
        self.ts_select_x = 0
        self.ts_select_y = 0
        self.edited_world.change_tileset(tlist[tidx])
        self.tileset = self.edited_world.tileset

    def next_tileset(self):
        ts = self.edited_world.tileset.tileset_id
        tlist = list(Tileset.tilesets)
        tidx = tlist.index(ts)
        tidx += 1
        if tidx >= len(tlist):
            tidx = 0
        self.ts_id_id = tidx
        self.ts_select_x = 0
        self.ts_select_y = 0
        self.edited_world.change_tileset(tlist[tidx])
        self.tileset = self.edited_world.tileset

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
        return

    @staticmethod
    def render_elements_callback(wnd):
        self = Editor.instance
        self.render_elements(wnd)

    def render_elements(self, wnd):
        #self.graphics.box("editor__TOOLBAR", 1008, 0, 592, 768, color=(0, 0, 0, 255), fill=(0, 0, 0, 255))

        self.font.clear()
        self.graphics.clear()
        passive_color = (128, 128, 128, 255)
        active_color = (255, 255, 255, 255)
        self.font.draw("editor__MODE", "Mode:", 1440, 320, color=active_color)
        self.font.draw("editor__MODE__TERRAIN", "Terrain", 1500, 320, color=active_color if self.editing_mode == EditingMode.TERRAIN else passive_color)
        self.font.draw("editor__MODE__COLLISION", "Collision", 1500, 340, color=active_color if self.editing_mode == EditingMode.COLLISION else passive_color)
        self.font.draw("editor__MODE__SELECTION", "Selection", 1500, 360, color=active_color if self.editing_mode == EditingMode.SELECTION else passive_color)
        self.font.draw("editor__MODE__OBJECTS", "Objects", 1500, 380, color=active_color if self.editing_mode == EditingMode.OBJECTS else passive_color)
        self.font.draw("editor__MODE__OBJECT_LIST", "Object List", 1500, 400, color=active_color if self.editing_mode == EditingMode.OBJECT_LIST else passive_color)
        self.font.draw("editor__MODE__BOSS", "Boss", 1500, 420, color=active_color if self.editing_mode == EditingMode.BOSS else passive_color)
        self.graphics.line("editor__MODE__SEPARATOR", 1500, 436, 1580, 436, color=passive_color)
        self.font.draw("editor__MODE__SIMULATION", "Simulation", 1500, 440, color=active_color if self.editing_mode == EditingMode.SIMULATION else passive_color)
        self.font.draw("editor__MODE__FRAMEBYFRAME", "Frame-by-frame", 1500, 460, color=active_color if self.editing_mode == EditingMode.FRAMEBYFRAME else passive_color)
        self.font.draw("editor__SAVE", "[Save now]", 1500, 728, color=active_color)

        fps = self.main_loop.fps()
        self.font.draw("editor__FPS", "{0} fps".format(fps), 1500, 748, color=active_color)

        if self.editing_mode not in EditingModeLock:
            with wnd:
                wnd.use_game_viewport()
                if self.editing_mode != EditingMode.TERRAIN or not self.only_render_current_layer:
                    self.edited_screen.render_to_window(wnd)
                else:
                    self.edited_screen.render_to_window(wnd, layer=self.terrain_layer)
                if (self.editing_mode in (EditingMode.TERRAIN, EditingMode.COLLISION) and not self.hide_objects_in_terrain_modes) or self.editing_mode in (EditingMode.OBJECTS, EditingMode.OBJECT_LIST):
                    self.edited_screen.render_editor_objects(wnd)
                if (self.editing_mode in (EditingMode.SELECTION, ) and self.sm_render_collisions) or (self.editing_mode in (EditingMode.COLLISION, )):
                    self.edited_screen.render_collisions_to_window(wnd, wnd.fbo)
                if self.edited_world.starting_screen_id == self.edited_screen.screen_id:
                    self.controller.player.x = self.edited_world.start_x
                    self.controller.player.y = self.edited_world.start_y
                    if self.editing_mode in (EditingMode.TERRAIN, EditingMode.SELECTION, EditingMode.OBJECTS, EditingMode.OBJECT_LIST):
                        self.controller.player.draw(wnd)
                    elif self.editing_mode == EditingMode.COLLISION:
                        self.controller.player.draw_as_hitbox(wnd, (0, 255, 0))
                wnd.use_full_viewport()
                self.background.draw(1080, 8, 160, 120)

                if self.editing_mode == EditingMode.TERRAIN:
                    self.tileset.draw_section(Editor.ts_display_x, 768 - Editor.ts_display_y - Editor.ts_view_h * Tileset.TILE_H, Editor.ts_view_w * Tileset.TILE_W, Editor.ts_view_h * Tileset.TILE_H, self.ts_view_x, self.ts_view_y, Editor.ts_view_w, Editor.ts_view_h)
                    #tileids = self.tileset.set_editor_display(self.ts_view_x, self.ts_view_y, Editor.ts_view_w, Editor.ts_view_h)
                    #self.tileset.draw_full_screen(Editor.ts_display_x, Editor.ts_display_y, Editor.ts_view_w * Tileset.TILE_W, Editor.ts_view_h * Tileset.TILE_H, wnd.fbo, tileids)

                    self.graphics.box("editor__TERRAIN__TILESETBOX", Editor.ts_display_x - 1, Editor.ts_display_y - 1, Editor.ts_view_w * Tileset.TILE_W + 2, Editor.ts_view_h * Tileset.TILE_H + 2, color=active_color)
                    if self.ts_select_x >= self.ts_view_x and self.ts_select_y >= self.ts_view_y and self.ts_select_x < self.ts_view_x + Editor.ts_view_w and self.ts_select_y < self.ts_view_y + Editor.ts_view_h:
                        tile_id_x = self.ts_select_x - self.ts_view_x
                        tile_id_y = self.ts_select_y - self.ts_view_y
                        self.graphics.box("editor__TERRAIN__DEST", Editor.ts_display_x + tile_id_x * Tileset.TILE_W, Editor.ts_display_y + tile_id_y * Tileset.TILE_H, Tileset.TILE_W, Tileset.TILE_H, color=(255, 0, 0, 255))
                    b_y = self.ts_display_y + Editor.ts_view_h * Tileset.TILE_H + 8
                    c_x = self.ts_display_x
                    for layer, label in LayerLabels.items():
                        self.font.draw("editor__LAYER__LABEL__{0}".format(label), label, c_x, b_y, color=active_color if self.terrain_layer == layer else passive_color)
                        c_x += 50
                    self.font.draw("editor__LAYER__HIDE", "[Hide other layers]", c_x, b_y, color=active_color if self.only_render_current_layer else passive_color)
                elif self.editing_mode == EditingMode.COLLISION:
                    Tileset.collision_tileset.draw_to(self.collision_editor, 0, Editor.tslx, Editor.tsby, w=70, h=70)

                    self.font.draw("editor__COLL__NONE", "NONE", Editor.ts_display_x, Editor.ts_display_y, (255, 255, 255, 255))
                    self.font.draw("editor__COLL__SOLID", "SOLID", Editor.ts_display_x, Editor.ts_display_y + 16, (0, 0, 255, 255))
                    self.font.draw("editor__COLL__DEADLY", "DEADLY", Editor.ts_display_x, Editor.ts_display_y + 32, (255, 0, 0, 255))
                    self.font.draw("editor__COLL__CONVEYOR", "CONVEY", Editor.ts_display_x, Editor.ts_display_y + 48, (0, 128, 0, 255))
                    self.font.draw("editor__COLL__TRIGGER", "BTRIG", Editor.ts_display_x, Editor.ts_display_y + 64, (128, 128, 0, 255))
                    self.graphics.polygon("editor__COLL__POLY1", [(Editor.ts_display_x + 48, Editor.ts_display_y + 84), (Editor.ts_display_x + 64, Editor.ts_display_y + 76), (Editor.ts_display_x + 64, Editor.ts_display_y + 92)], color=(255, 255, 255, 255))
                    self.graphics.polygon("editor__COLL__POLY2", [(Editor.ts_display_x + 120, Editor.ts_display_y + 84), (Editor.ts_display_x + 104, Editor.ts_display_y + 76), (Editor.ts_display_x + 104, Editor.ts_display_y + 92)], color=(255, 255, 255, 255))
                    self.graphics.box("editor__COLL__BOX", Editor.ts_display_x + 48, Editor.ts_display_y, 72, 72, (255, 255, 255, 255))
                elif self.editing_mode == EditingMode.SELECTION:
                    if self.sm_selection_1 is not None and self.sm_selection_2 is not None:
                        self.font.draw("editor__SELECT__TL", "TL: ({0}, {1})".format(self.sm_selection_1[0], self.sm_selection_1[1]), Editor.ts_display_x + 300, Editor.ts_display_y, color=active_color)
                        self.font.draw("editor__SELECT__BR", "BR: ({0}, {1})".format(self.sm_selection_2[0], self.sm_selection_2[1]), Editor.ts_display_x + 300, Editor.ts_display_y + 20, color=active_color)
                        w = (self.sm_selection_2[0] - self.sm_selection_1[0] + 1) * Tileset.TILE_W
                        h = (self.sm_selection_2[1] - self.sm_selection_1[1] + 1) * Tileset.TILE_H
                        self.graphics.box("editor__SELECT__SELECTION", self.sm_selection_1[0] * Tileset.TILE_W, self.sm_selection_1[1] * Tileset.TILE_H, w, h, color=(255, 0, 0, 255))

                    has_selection = self.sm_selection_1 is not None and self.sm_selection_2 is not None

                    self.font.draw("editor__SELECT__RAC", "[Render as collisions]", Editor.ts_display_x, Editor.ts_display_y, color=active_color if self.sm_render_collisions else passive_color)
                    self.font.draw("editor__SELECT__CUT", "[Cut] (X)", Editor.ts_display_x, Editor.ts_display_y + 20, color=active_color if has_selection else passive_color)
                    self.font.draw("editor__SELECT__COPY", "[Copy] (C)", Editor.ts_display_x, Editor.ts_display_y + 40, color=active_color if has_selection else passive_color)
                    self.font.draw("editor__SELECT__FILLT", "[Fill with Terrain] (I)", Editor.ts_display_x, Editor.ts_display_y + 60, color=active_color if has_selection else passive_color)
                    self.font.draw("editor__SELECT__FILLC", "[Fill with Collision] (O)", Editor.ts_display_x, Editor.ts_display_y + 80, color=active_color if has_selection else passive_color)
                    self.font.draw("editor__SELECT__RESETT", "[Reset Terrain]", Editor.ts_display_x, Editor.ts_display_y + 100, color=active_color if has_selection else passive_color)
                    self.font.draw("editor__SELECT__RESETC", "[Reset Collision]", Editor.ts_display_x, Editor.ts_display_y + 120, color=active_color if has_selection else passive_color)
                    self.font.draw("editor__SELECT__PASTE", "[Paste] (V)", Editor.ts_display_x, Editor.ts_display_y + 140, color=active_color if has_selection and self.sm_clipboard is not None else passive_color)
                elif self.editing_mode == EditingMode.OBJECTS:
                    self.edited_screen.render_editor_objects(wnd)
                    if self.objed_selection is None:
                        self.font.draw("editor__OBJECTS__404", "No placable objects exist.", Editor.ts_display_x, Editor.ts_display_y, color=(255, 0, 0, 255))
                    else:
                        self.graphics.polygon("editor__OBJECTS__LARROW", [(Editor.ts_display_x - 24, Editor.ts_display_y + 8), (Editor.ts_display_x - 8, Editor.ts_display_y), (Editor.ts_display_x - 8, Editor.ts_display_y + 16)], color=(255, 255, 255, 255), fill=(255, 255, 255, 255))
                        self.graphics.polygon("editor__OBJECTS__RARROW", [(Editor.ts_display_x + 500, Editor.ts_display_y + 8), (Editor.ts_display_x + 484, Editor.ts_display_y), (Editor.ts_display_x + 484, Editor.ts_display_y + 16)], color=(255, 255, 255, 255), fill=(255, 255, 255, 255))
                        self.font.draw("edtior__OBJECT__CREATENEW", "Creating new: {0}".format(self.objed_selection.object_name), Editor.ts_display_x, Editor.ts_display_y, color=(255, 255, 255, 255))
                        self.objed_selection.render_editor_properties(wnd, self.font, Editor.ts_display_x, Editor.ts_display_y + 40)
                elif self.editing_mode == EditingMode.OBJECT_LIST:
                    self.edited_screen.render_editor_objects(wnd)
                    if self.objlist_selection_idx is None:
                        self.font.draw("editor__OBJLIST__404", "No objects have been placed.", Editor.ts_display_x, Editor.ts_display_y, color=(255, 0, 0, 255))
                    else:
                        try:
                            ed_obj = self.edited_screen.bound_objects[self.objlist_selection_idx]
                            self.graphics.polygon("editor__OBJECTS__LARROW", [(Editor.ts_display_x - 24, Editor.ts_display_y + 8), (Editor.ts_display_x - 8, Editor.ts_display_y), (Editor.ts_display_x - 8, Editor.ts_display_y + 16)], color=(255, 255, 255, 255), fill=(255, 255, 255, 255))
                            self.graphics.polygon("editor__OBJECTS__RARROW", [(Editor.ts_display_x + 500, Editor.ts_display_y + 8), (Editor.ts_display_x + 484, Editor.ts_display_y), (Editor.ts_display_x + 484, Editor.ts_display_y + 16)], color=(255, 255, 255, 255), fill=(255, 255, 255, 255))
                            self.font.draw("editor__OBJLIST__SEL", "Editing: {0} at ({1}, {2})".format(ed_obj.__class__.object_name, ed_obj.x, ed_obj.y), Editor.ts_display_x, Editor.ts_display_y, color=(255, 255, 255, 255))
                            size = ed_obj.__class__.editor_frame_size
                            if size[0] > 0 and size[1] > 0:
                                self.graphics.box("editor__OBJLIST__BBOX", ed_obj.x - 1, ed_obj.y - 1, size[0], size[1], color=(0, 0, 255, 255))
                            self.font.draw("editor__OBJLIST__MOVE", "[Move]", Editor.ts_display_x, Editor.ts_display_y + 20, color=active_color)
                            self.font.draw("editor__OBJLIST__DELETE", "[Delete]", Editor.ts_display_x + 150, Editor.ts_display_y + 20, color=active_color)
                            if len(ed_obj.__class__.editor_properties):
                                self.font.draw("editor__OBJLIST__APPLY", "[Apply]", Editor.ts_display_x + 300, Editor.ts_display_y + 20, color=active_color)
                                ed_obj.__class__.render_editor_properties(wnd, self.font, Editor.ts_display_x, Editor.ts_display_y + 40)
                            else:
                                self.font.draw("editor__OBJECTS__404P", "No editable properties for this object", Editor.ts_display_x, Editor.ts_display_y + 40, color=(255, 0, 0, 255))
                        except IndexError:
                            print("Objlist_selection_idx {0} is out of range.", self.objlist_selection_idx)
                            if len(self.edited_screen.bound_objects):
                                self.objlist_selection_idx = len(self.edited_screen.bound_objects) - 1
                                ed_obj = self.edited_screen.bound_objects[self.objlist_selection_idx]
                                ed_obj.load_object_to_editor()
                            else:
                                self.objlist_selection_idx = None
                elif self.editing_mode == EditingMode.BOSS:
                    if self.edited_world.bossfight_spec is None:
                        self.initialize_bossfight()
                    self.font.draw("editor__BOSS__CLS", "Boss class: {0}".format(self.edited_world.bossfight_spec[0]), Editor.ts_display_x, Editor.ts_display_y, color=active_color)
                    self.font.draw("editor__BOSS__CLS__DEC", "[-]", Editor.ts_display_x + 300, Editor.ts_display_y, color=(255, 255, 255, 255))
                    self.font.draw("editor__BOSS__CLS__INC", "[+]", Editor.ts_display_x + 320, Editor.ts_display_y, color=(255, 255, 255, 255))
                    self.font.draw("editor__BOSS__SCRID", "Boss screen ID: {0}".format(self.edited_world.bossfight_spec[1]), Editor.ts_display_x, Editor.ts_display_y + 20, color=active_color)
                    self.font.draw("editor__BOSS__SCRID__UC", "[Use current]", Editor.ts_display_x + 300, Editor.ts_display_y + 20, color=(255, 255, 255, 255))
                    if self.edited_screen.screen_id == self.edited_world.bossfight_spec[1]:
                        self.font.draw("editor__BOSS__COORD", "Boss coordinates: ({0}, {1})".format(self.edited_world.bossfight_spec[2], self.edited_world.bossfight_spec[3]), Editor.ts_display_x, Editor.ts_display_y + 40, color=active_color)
                        self.font.draw("editor__BOSS__COORD_DECX", "[X-]", Editor.ts_display_x, Editor.ts_display_y + 60, color=active_color)
                        self.font.draw("editor__BOSS__COORD_INCX", "[X+]", Editor.ts_display_x + 30, Editor.ts_display_y + 60, color=active_color)
                        self.font.draw("editor__BOSS__COORD_DECY", "[Y-]", Editor.ts_display_x + 60, Editor.ts_display_y + 60, color=active_color)
                        self.font.draw("editor__BOSS__COORD_INCY", "[Y+]", Editor.ts_display_x + 90, Editor.ts_display_y + 60, color=active_color)
                        self.font.draw("editor__BOSS__COORD_SEL", "[Select]", Editor.ts_display_x + 120, Editor.ts_display_y + 60, color=active_color)
                        self.graphics.box("editor__BOSS__OUTINE", self.edited_world.bossfight_spec[2], self.edited_world.bossfight_spec[3], 72, 72, color=(255, 255, 0, 255))

                self.font.draw("editor__COMMON__SCRID", "Screen id: {0}".format(self.edited_screen.screen_id), 1080, 320, active_color)
                e_tr = self.edited_screen.transitions[0]
                self.font.draw("editor__COMMON__ETR", "East transition: {0}".format("solid" if e_tr == 0 else e_tr), 1080, 340, active_color)
                self.font.draw("editor__COMMON__ETR-", "[-]", 1270, 340, active_color)
                self.font.draw("editor__COMMON__ETR+", "[+]", 1290, 340, active_color)
                n_tr = self.edited_screen.transitions[1]
                self.font.draw("editor__COMMON__NTR", "North transition: {0}".format("solid" if n_tr == 0 else n_tr), 1080, 360, active_color)
                self.font.draw("editor__COMMON__NTR-", "[-]", 1270, 360, active_color)
                self.font.draw("editor__COMMON__NTR+", "[+]", 1290, 360, active_color)
                w_tr = self.edited_screen.transitions[2]
                self.font.draw("editor__COMMON__WTR", "West transition: {0}".format("solid" if w_tr == 0 else w_tr), 1080, 380, active_color)
                self.font.draw("editor__COMMON__WTR-", "[-]", 1270, 380, active_color)
                self.font.draw("editor__COMMON__WTR+", "[+]", 1290, 380, active_color)
                s_tr = self.edited_screen.transitions[3]
                self.font.draw("editor__COMMON__STR", "South transition: {0}".format("solid" if s_tr == 0 else s_tr), 1080, 400, active_color)
                self.font.draw("editor__COMMON__STR-", "[-]", 1270, 400, active_color)
                self.font.draw("editor__COMMON__STR+", "[+]", 1290, 400, active_color)

                self.font.draw("editor__COMMON__GRAVX", "Gravity X: {0:.2f}".format(self.edited_screen.gravity[0]), 1080, 420, active_color)
                self.font.draw("editor__COMMON__GRAVX-", "[-]", 1270, 420, active_color)
                self.font.draw("editor__COMMON__GRAVX+", "[+]", 1290, 420, active_color)
                self.font.draw("editor__COMMON__GRAVY", "Gravity Y: {0:.2f}".format(self.edited_screen.gravity[1]), 1080, 440, active_color)
                self.font.draw("editor__COMMON__GRAVY-", "[-]", 1270, 440, active_color)
                self.font.draw("editor__COMMON__GRAVY+", "[+]", 1290, 440, active_color)
                self.font.draw("editor__COMMON__JFRAM", "Jump strength: {0:.2f}".format(self.edited_screen.jump_frames), 1080, 460, active_color)
                self.font.draw("editor__COMMON__JFRAM-", "[-]", 1270, 460, active_color)
                self.font.draw("editor__COMMON__JFRAM+", "[+]", 1290, 460, active_color)
                self.font.draw("editor__COMMON__WSCRID", "World starting screen: {0}".format(self.edited_world.starting_screen_id), 1080, 500, active_color)
                self.font.draw("editor__COMMON__WSCRUSE", "[Use current]", 1080, 520, active_color)

                if self.prompt_message is not None:
                    self.font.draw("editor__PROMPT__MESSAGE", self.prompt_message, 1300, 500, (0, 255, 0, 255))
                if self.prompt_callback is not None:
                    self.font.draw("editor__PROMPT__CB", "RETURN to confirm, BACKSPACE to cancel", 1300, 520, active_color)

                if self.edited_world.starting_screen_id == self.edited_screen.screen_id:
                    self.font.draw("editor__COMMON__WSCRSTART", "[Select start location]", 1080, 540, active_color)

                if self.point_selection_callback is not None:
                    self.font.draw("editor__COMMON__PSEL", "Select point on map (right click to cancel)...", 1080, 8, (0, 255, 0, 255))

                self.font.draw("editor__COMMON__MUSIC", "World music: {0}".format(self.edited_world.background_music.audio_name), 1080, 560, active_color)
                self.font.draw("editor__COMMON__MUSIC-", "[-]", 1400, 560, active_color)
                self.font.draw("editor__COMMON__MUSIC+", "[+]", 1420, 560, active_color)

                self.font.draw("editor__COMMON__WTSID", "World tileset ID: {0}".format(self.edited_world.tileset.tileset_id), 1080, 580, active_color)
                self.font.draw("editor__COMMON__WTSID-", "[-]", 1400, 580, active_color)
                self.font.draw("editor__COMMON__WTSID+", "[+]", 1420, 580, active_color)

                self.font.draw("editor__COMMON__HIDEOBJ", "[Hide objects in terrain modes]", 1080, 600, active_color if self.hide_objects_in_terrain_modes else passive_color)
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
                self.sm_clipboard[cy][cx] = tile

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
                    self.edited_screen.tiles[wy][wx] = src_tile
                except IndexError:
                    pass
        self.edited_screen.dirty = True
        self.edited_screen.dirty_collisions = True

    def sm_terrain_fill(self):
        for x in range(self.sm_selection_1[0], self.sm_selection_2[0] + 1):
            for y in range(self.sm_selection_1[1], self.sm_selection_2[1] + 1):
                self.edited_screen.change_tile_graphic(x, y, self.terrain_layer, self.ts_select_x, self.ts_select_y)
        self.edited_screen.dirty = True

    def sm_collision_fill(self):
        for x in range(self.sm_selection_1[0], self.sm_selection_2[0] + 1):
            for y in range(self.sm_selection_1[1], self.sm_selection_2[1] + 1):
                self.edited_screen.change_tile_collision(x, y, self.collision_editor)
        self.edited_screen.dirty_collisions = True

    def sm_terrain_reset(self):
        for x in range(self.sm_selection_1[0], self.sm_selection_2[0] + 1):
            for y in range(self.sm_selection_1[1], self.sm_selection_2[1] + 1):
                self.edited_screen.change_tile_graphic(x, y, self.terrain_layer, 0, 0)
        self.edited_screen.dirty = True

    def sm_collision_reset(self):
        for x in range(self.sm_selection_1[0], self.sm_selection_2[0] + 1):
            for y in range(self.sm_selection_1[1], self.sm_selection_2[1] + 1):
                self.edited_screen.change_tile_collision(x, y, 0)
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
                elif event.pos[1] < 400:
                    self.exit_simulation_if_needed()
                    self.change_mode(EditingMode.OBJECTS)
                    return
                elif event.pos[1] < 420:
                    self.exit_simulation_if_needed()
                    self.change_mode(EditingMode.OBJECT_LIST)
                    return
                elif event.pos[1] < 436:
                    self.exit_simulation_if_needed()
                    self.change_mode(EditingMode.BOSS)
                    return
                elif event.pos[1] < 460:
                    if self.editing_mode not in SimulationModes:
                        self.exit_simulation_if_needed()
                        self.change_mode(EditingMode.SIMULATION)
                        self.start_simulation()
                    else:
                        self.change_mode(EditingMode.SIMULATION)
                        self.main_loop.suspend_ticking = False
                    return
                elif event.pos[1] < 480:
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
            if event.pos[0] >= SCREEN_SIZE_W and event.button == 1:
                if self.point_selection_callback is not None:
                    return
                if self.editing_mode == EditingMode.TERRAIN:
                    b_y = self.ts_display_y + Editor.ts_view_h * Tileset.TILE_H + 8
                    c_x = self.ts_display_x
                    if mousebox(event.pos[0], event.pos[1], Editor.ts_display_x, Editor.ts_display_y, Editor.ts_view_w * Tileset.TILE_W, Editor.ts_view_h * Tileset.TILE_H):
                        tx = int((event.pos[0] - Editor.ts_display_x) / Tileset.TILE_W) + self.ts_view_x
                        ty = int((event.pos[1] - Editor.ts_display_y) / Tileset.TILE_H) + self.ts_view_y
                        if tx < self.tileset.tiles_w and ty < self.tileset.tiles_h:
                            self.ts_select_x = tx
                            self.ts_select_y = ty
                    elif mousebox(event.pos[0], event.pos[1], c_x, b_y, (len(LayerLabels) + 4) * 50, 20):
                        for layer, label in LayerLabels.items():
                            if event.pos[0] < c_x + 50:
                                self.terrain_layer = int(layer)
                                return
                            else:
                                c_x += 50
                        if not self.locked[1]:
                            self.locked[1] = True
                            self.only_render_current_layer = not self.only_render_current_layer
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
                    if self.objed_selection is not None:
                        if mousebox(event.pos[0], event.pos[1], Editor.ts_display_x - 24, Editor.ts_display_y, 16, 16):
                            idx = Object.object_editor_items.index(self.objed_selection) - 1
                            if idx < 0:
                                idx = len(Object.object_editor_items) - 1
                            self.objed_selection = Object.object_editor_items[idx]
                            self.locked[1] = True
                        elif mousebox(event.pos[0], event.pos[1], Editor.ts_display_x + 484, Editor.ts_display_y, 16, 16):
                            idx = Object.object_editor_items.index(self.objed_selection) + 1
                            if idx > len(Object.object_editor_items) - 1:
                                idx = 0
                            self.objed_selection = Object.object_editor_items[idx]
                            self.locked[1] = True
                        elif mousebox(event.pos[0], event.pos[1], Editor.ts_display_x, Editor.ts_display_y + 40, 500, 200):
                            if self.objed_selection.check_object_editor_click(self, event.pos[0], event.pos[1], Editor.ts_display_x, Editor.ts_display_y + 40):
                                self.locked[1] = True
                elif self.editing_mode == EditingMode.OBJECT_LIST and not self.locked[1]:
                    if self.objlist_selection_idx is not None:
                        ed_obj = self.edited_screen.bound_objects[self.objlist_selection_idx]
                        if mousebox(event.pos[0], event.pos[1], Editor.ts_display_x - 24, Editor.ts_display_y, 16, 16):
                            self.objlist_selection_idx -= 1
                            if self.objlist_selection_idx < 0:
                                self.objlist_selection_idx = len(self.edited_screen.bound_objects) - 1
                            self.edited_screen.bound_objects[self.objlist_selection_idx].load_object_to_editor()
                            self.locked[1] = True
                        elif mousebox(event.pos[0], event.pos[1], Editor.ts_display_x + 484, Editor.ts_display_y, 16, 16):
                            self.objlist_selection_idx += 1
                            if self.objlist_selection_idx > len(self.edited_screen.bound_objects) - 1:
                                self.objlist_selection_idx = 0
                            self.edited_screen.bound_objects[self.objlist_selection_idx].load_object_to_editor()
                            self.locked[1] = True
                        elif mousebox(event.pos[0], event.pos[1], Editor.ts_display_x, Editor.ts_display_y + 20, 100, 20):
                            self.point_selection_callback = self.move_selected_object
                            self.locked[1] = True
                        elif mousebox(event.pos[0], event.pos[1], Editor.ts_display_x + 150, Editor.ts_display_y + 20, 100, 20):
                            del self.edited_screen.bound_objects[self.objlist_selection_idx]
                            if len(self.edited_screen.bound_objects) == 0:
                                self.objlist_selection_idx = None
                            elif self.objlist_selection_idx > len(self.edited_screen.bound_objects) - 1:
                                self.objlist_selection_idx -= 1
                            self.locked[1] = True
                            self.edited_screen.reset_to_initial_state()
                        elif len(ed_obj.__class__.editor_properties):
                            if mousebox(event.pos[0], event.pos[1], Editor.ts_display_x + 300, Editor.ts_display_y + 20, 100, 20):
                                ed_obj.reload_from_editor()
                            elif mousebox(event.pos[0], event.pos[1], Editor.ts_display_x, Editor.ts_display_y + 40, 500, 200):
                                if ed_obj.__class__.check_object_editor_click(self, event.pos[0], event.pos[1], Editor.ts_display_x, Editor.ts_display_y + 40):
                                    self.locked[1] = True
                elif self.editing_mode == EditingMode.BOSS and not self.locked[1]:
                    dx = Editor.ts_display_x
                    dy = Editor.ts_display_y
                    if mousebox(event.pos[0], event.pos[1], dx, dy, 400, 80):
                        if event.pos[1] < dy + 20:
                            if event.pos[0] >= dx + 300:
                                if event.pos[0] < dx + 320:
                                    self.locked[1] = True
                                    self.prev_boss_class()
                                else:
                                    self.locked[1] = True
                                    self.next_boss_class()
                        elif event.pos[1] < dy + 40:
                            if event.pos[0] >= dx + 300:
                                self.locked[1] = True
                                ed = list(self.edited_world.bossfight_spec)
                                ed[1] = self.edited_screen.screen_id
                                self.edited_world.bossfight_spec = tuple(ed)
                        elif event.pos[1] >= dy + 60 and self.edited_screen.screen_id == self.edited_world.bossfight_spec[1]:
                            if event.pos[1] < dy + 80:
                                if event.pos[0] < dx + 30:
                                    self.locked[1] = True
                                    ed = list(self.edited_world.bossfight_spec)
                                    ed[2] -= 1
                                    self.edited_world.bossfight_spec = tuple(ed)
                                elif event.pos[0] < dx + 60:
                                    self.locked[1] = True
                                    ed = list(self.edited_world.bossfight_spec)
                                    ed[2] += 1
                                    self.edited_world.bossfight_spec = tuple(ed)
                                elif event.pos[0] < dx + 90:
                                    self.locked[1] = True
                                    ed = list(self.edited_world.bossfight_spec)
                                    ed[3] -= 1
                                    self.edited_world.bossfight_spec = tuple(ed)
                                elif event.pos[0] < dx + 120:
                                    self.locked[1] = True
                                    ed = list(self.edited_world.bossfight_spec)
                                    ed[3] += 1
                                    self.edited_world.bossfight_spec = tuple(ed)
                                elif event.pos[0] < dx + 220:
                                    self.locked[1] = True
                                    self.point_selection_callback = self.set_bossfight_coords
                if not self.locked[1]:
                    if mousebox(event.pos[0], event.pos[1], 1500, 728, 100, 20):
                        self.locked[1] = True
                        self.atexit(self.main_loop)
                    elif mousebox(event.pos[0], event.pos[1], 1080, 520, 100, 20):
                        self.locked[1] = True
                        self.edited_world.starting_screen_id = self.edited_screen.screen_id
                    elif mousebox(event.pos[0], event.pos[1], 1080, 600, 100, 20):
                        self.locked[1] = True
                        self.hide_objects_in_terrain_modes = not self.hide_objects_in_terrain_modes
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
                    elif mousebox(event.pos[0], event.pos[1], 1400, 560, 20, 20):
                        self.locked[1] = True
                        self.prev_music()
                    elif mousebox(event.pos[0], event.pos[1], 1420, 560, 20, 20):
                        self.locked[1] = True
                        self.next_music()
                    elif mousebox(event.pos[0], event.pos[1], 1400, 580, 20, 20):
                        self.locked[1] = True
                        self.prev_tileset()
                    elif mousebox(event.pos[0], event.pos[1], 1420, 580, 20, 20):
                        self.locked[1] = True
                        self.next_tileset()
            elif event.pos[0] < SCREEN_SIZE_W:
                if self.point_selection_callback is not None and event.button == 1:
                    self.point_selection_callback(event.pos[0], event.pos[1])
                    self.point_selection_callback = None
                    self.locked[1] = True
                    return
                sctx = int(event.pos[0] / Tileset.TILE_W)
                scty = int(event.pos[1] / Tileset.TILE_H)
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
                elif self.editing_mode == EditingMode.TERRAIN:
                    if event.button == 1:
                        self.edited_screen.change_tile_graphic(sctx, scty, self.terrain_layer, self.ts_select_x, self.ts_select_y)
                    elif event.button == 3:
                        self.edited_screen.change_tile_graphic(sctx, scty, self.terrain_layer, 0, 0)
                    self.edited_screen.dirty = True
                elif self.editing_mode == EditingMode.COLLISION:
                    if event.button == 1:
                        self.edited_screen.change_tile_collision(sctx, scty, self.collision_editor)
                    elif event.button == 3:
                        self.edited_screen.change_tile_collision(sctx, scty, 0)
                    self.edited_screen.dirty_collisions = True
                elif self.editing_mode == EditingMode.OBJECTS:
                    if not self.locked[1]:
                        self.edited_screen.bound_objects.append(self.objed_selection(self.edited_screen, event.pos[0], event.pos[1], self.objed_selection.editing_values))
                        self.edited_screen.reset_to_initial_state()
        else:
            if self.editing_mode == EditingMode.SIMULATION or self.editing_mode == EditingMode.FRAMEBYFRAME and not self.locked[0]:
                if mousebox(event.pos[0], event.pos[1], Editor.ts_display_x, Editor.ts_display_y, 100, 20):
                    self.controller.render_collisions = not self.controller.render_collisions
                    self.locked[1] = True

    def set_start_coordinates(self, x, y):
        self.edited_world.start_x = x
        self.edited_world.start_y = y
        self.controller.reset_from_editor(self)

    def move_selected_object(self, x, y):
        ed_obj = self.edited_screen.bound_objects[self.objlist_selection_idx]
        ed_obj.x = x
        ed_obj.y = y
        self.edited_screen.reset_to_initial_state()

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
            if event.pos[0] < SCREEN_SIZE_W and self.editing_mode == EditingMode.SELECTION and not self.sm_holding:
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
            elif event.key == Editor.key_mapping["reset_simulation_to_save"]:
                self.controller.reset_to_save()
            elif self.editing_mode == EditingMode.FRAMEBYFRAME and event.key == Editor.key_mapping["frame_advance"]:
                self.controller(self.main_loop)
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
        if which == EditingMode.OBJECT_LIST:
            if self.objlist_selection_idx is None:
                if len(self.edited_screen.bound_objects):
                    self.objlist_selection_idx = 0
            if self.objlist_selection_idx is not None:
                if self.objlist_selection_idx < len(self.edited_screen.bound_objects):
                    self.edited_screen.bound_objects[self.objlist_selection_idx].load_object_to_editor()
                elif len(self.edited_screen.bound_objects):
                    self.objlist_selection_idx = 0
                    self.edited_screen.bound_objects[self.objlist_selection_idx].load_object_to_editor()
                else:
                    self.objlist_selection_idx = None
        self.editing_mode = which
