from .background import Background
from .tileset import Tileset
from .screen import Screen, Collision
from .world import World
from .game import Controller
import pygame
from pygame.locals import K_m


class _mousetev:
    def __init__(self, pos, button):
        self.pos = pos
        self.button = button


def mousebox(x, y, x0, y0, w, h):
    return x >= x0 and y >= y0 and x < x0 + w and y < y0 + h


class Editor:
    instance = None
    ts_view_w = 30
    ts_view_h = 15
    ts_display_x = 1080
    ts_display_y = 32
    key_mapping = {
        "mode": K_m
    }
    mode_count = 2
    collision_editor_draw = {
        Collision.PASSABLE: lambda wnd: True,
        Collision.SOLID_TILE: lambda wnd: pygame.draw.rect(wnd.display, (0, 0, 255), pygame.Rect(Editor.ts_display_x + 49, Editor.ts_display_y + 1, 70, 70)),
        Collision.SOLID_HALF_DOWN: lambda wnd: pygame.draw.rect(wnd.display, (0, 0, 255), pygame.Rect(Editor.ts_display_x + 49, Editor.ts_display_y + 35, 70, 36)),
        Collision.SOLID_HALF_UP: lambda wnd: pygame.draw.rect(wnd.display, (0, 0, 255), pygame.Rect(Editor.ts_display_x + 49, Editor.ts_display_y + 1, 70, 36)),
        Collision.SOLID_SLOPE_UPLEFT: lambda wnd: pygame.draw.polygon(wnd.display, (0, 0, 255), [(Editor.ts_display_x + 49, Editor.ts_display_y + 1), (Editor.ts_display_x + 118, Editor.ts_display_y + 70), (Editor.ts_display_x + 49, Editor.ts_display_y + 70)]),
        Collision.SOLID_SLOPE_UPRIGHT: lambda wnd: pygame.draw.polygon(wnd.display, (0, 0, 255), [(Editor.ts_display_x + 118, Editor.ts_display_y + 1), (Editor.ts_display_x + 49, Editor.ts_display_y + 70), (Editor.ts_display_x + 118, Editor.ts_display_y + 70)]),
        Collision.DEADLY_TILE: lambda wnd: pygame.draw.rect(wnd.display, (255, 0, 0), pygame.Rect(Editor.ts_display_x + 49, Editor.ts_display_y + 1, 70, 70)),
        Collision.DEADLY_SPIKE_UP: lambda wnd: pygame.draw.polygon(wnd.display, (255, 0, 0), [(Editor.ts_display_x + 49, Editor.ts_display_y + 70), (Editor.ts_display_x + 84, Editor.ts_display_y + 1), (Editor.ts_display_x + 85, Editor.ts_display_y + 1), (Editor.ts_display_x + 118, Editor.ts_display_y + 70)]),
        Collision.DEADLY_SPIKE_DOWN: lambda wnd: pygame.draw.polygon(wnd.display, (255, 0, 0), [(Editor.ts_display_x + 49, Editor.ts_display_y + 1), (Editor.ts_display_x + 84, Editor.ts_display_y + 70), (Editor.ts_display_x + 85, Editor.ts_display_y + 70), (Editor.ts_display_x + 118, Editor.ts_display_y + 1)]),
        Collision.DEADLY_SPIKE_LEFT: lambda wnd: pygame.draw.polygon(wnd.display, (255, 0, 0), [(Editor.ts_display_x + 49, Editor.ts_display_y + 1), (Editor.ts_display_x + 118, Editor.ts_display_y + 35), (Editor.ts_display_x + 118, Editor.ts_display_y + 36), (Editor.ts_display_x + 49, Editor.ts_display_y + 70)]),
        Collision.DEADLY_SPIKE_RIGHT: lambda wnd: pygame.draw.polygon(wnd.display, (255, 0, 0), [(Editor.ts_display_x + 118, Editor.ts_display_y + 1), (Editor.ts_display_x + 49, Editor.ts_display_y + 35), (Editor.ts_display_x + 49, Editor.ts_display_y + 36), (Editor.ts_display_x + 118, Editor.ts_display_y + 70)]),
        Collision.SOLID_HALF_UP_DEADLY_HALF_DOWN: lambda wnd: pygame.draw.rect(wnd.display, (0, 0, 255), pygame.Rect(Editor.ts_display_x + 49, Editor.ts_display_y + 1, 70, 35)) and pygame.draw.rect(wnd.display, (255, 0, 0), pygame.Rect(Editor.ts_display_x + 49, Editor.ts_display_y + 36, 70, 35)),
        Collision.SOLID_HALF_DOWN_DEADLY_HALF_UP: lambda wnd: pygame.draw.rect(wnd.display, (255, 0, 0), pygame.Rect(Editor.ts_display_x + 49, Editor.ts_display_y + 1, 70, 35)) and pygame.draw.rect(wnd.display, (0, 0, 255), pygame.Rect(Editor.ts_display_x + 49, Editor.ts_display_y + 36, 70, 35)),
        Collision.SOLID_HALF_LEFT_DEADLY_HALF_RIGHT: lambda wnd: pygame.draw.rect(wnd.display, (0, 0, 255), pygame.Rect(Editor.ts_display_x + 49, Editor.ts_display_y + 1, 35, 70)) and pygame.draw.rect(wnd.display, (255, 0, 0), pygame.Rect(Editor.ts_display_x + 84, Editor.ts_display_y + 1, 35, 70)),
        Collision.SOLID_HALF_RIGHT_DEADLY_HALF_LEFT: lambda wnd: pygame.draw.rect(wnd.display, (255, 0, 0), pygame.Rect(Editor.ts_display_x + 49, Editor.ts_display_y + 1, 35, 70)) and pygame.draw.rect(wnd.display, (0, 0, 255), pygame.Rect(Editor.ts_display_x + 84, Editor.ts_display_y + 1, 35, 70)),
    }

    def __init__(self, world_file, main_loop):
        if Editor.instance is not None:
            raise RuntimeError("Editor must be a singleton.")
        Editor.instance = self
        self.font = pygame.font.SysFont('Courier New', 12)

        main_loop.add_render_callback(Editor.render_elements_callback)
        main_loop.add_atexit_callback(Editor.atexit_callback)
        main_loop.set_mouse_button_handler(Editor.mousedown_callback)
        main_loop.set_mouse_button_up_handler(Editor.mouseup_callback)
        main_loop.set_mouse_motion_handler(Editor.mousemotion_callback)
        main_loop.set_keydown_handler(Editor.key_mapping["mode"], Editor.keydown_callback)

        self.world_file = world_file
        self.bg_id_id = 0
        self.ts_id_id = 0
        self.ts_view_x = 0
        self.ts_view_y = 0
        self.ts_select_x = 0
        self.ts_select_y = 0
        self.last_click_x = 0
        self.last_click_y = 0
        self.editing_mode = 0
        self.point_selection_callback = None
        self.locked = {
            1: False,
            2: False,
            3: False,
        }
        self.collision_editor = 0
        self.screen_seg = main_loop.segment_window(0, 0, 1024, 768)

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
            self.apply_background()

        self.controller = Controller(main_loop)
        self.controller.add_loaded_world(self.edited_world)
        self.controller.create_player()

    def apply_tileset(self):
        print("apply tileset called")
        self.edited_world.tileset = self.tileset

    def apply_background(self):
        self.edited_screen.background = self.background

    def create_new_screen(self):
        self.edited_screen = Screen(self.edited_world)
        self.edited_screen.screen_id = self.next_screen_id
        self.next_screen_id += 1
        self.screens.append(self.edited_screen)
        self.edited_world.screens[self.edited_screen.screen_id] = self.edited_screen

    @staticmethod
    def render_elements_callback(wnd):
        self = Editor.instance
        self.render_elements(wnd)

    def render_elements(self, wnd):
        self.edited_screen.render_to_window(self.screen_seg)
        if self.editing_mode == 0:
            pygame.draw.rect(wnd.display, (255, 255, 255), pygame.Rect(Editor.ts_display_x - 1, Editor.ts_display_y - 1, Editor.ts_view_w * Tileset.TILE_W + 2, Editor.ts_view_h * Tileset.TILE_H + 2))
            self.tileset.draw_to(self.ts_view_x, self.ts_view_y, Editor.ts_view_w, Editor.ts_view_h, wnd.display, (Editor.ts_display_x, Editor.ts_display_y))
            if self.ts_select_x >= self.ts_view_x and self.ts_select_y >= self.ts_view_y and self.ts_select_x < self.ts_view_x + Editor.ts_view_w and self.ts_select_y < self.ts_view_y + Editor.ts_view_h:
                tile_id_x = self.ts_select_x - self.ts_view_x
                tile_id_y = self.ts_select_y - self.ts_view_y
                dest = pygame.Rect(Editor.ts_display_x + tile_id_x * Tileset.TILE_W, Editor.ts_display_y + tile_id_y * Tileset.TILE_H, Tileset.TILE_W, Tileset.TILE_H)
                pygame.draw.rect(wnd.display, (255, 0, 0), dest, 1)
        elif self.editing_mode == 1:
            self.edited_screen.render_collisions_to_window(self.screen_seg)
            none_active = self.font.render("NONE", True, (255, 255, 255), 0)
            solid_active = self.font.render("SOLID", True, (0, 0, 255), 0)
            deadly_active = self.font.render("DEADLY", True, (255, 0, 0), 0)
            wnd.display.blit(none_active, (Editor.ts_display_x, Editor.ts_display_y))
            wnd.display.blit(solid_active, (Editor.ts_display_x, Editor.ts_display_y + 16))
            wnd.display.blit(deadly_active, (Editor.ts_display_x, Editor.ts_display_y + 32))

            pygame.draw.polygon(wnd.display, (255, 255, 255), [(Editor.ts_display_x + 48, Editor.ts_display_y + 84), (Editor.ts_display_x + 64, Editor.ts_display_y + 76), (Editor.ts_display_x + 64, Editor.ts_display_y + 92)])
            pygame.draw.polygon(wnd.display, (255, 255, 255), [(Editor.ts_display_x + 120, Editor.ts_display_y + 84), (Editor.ts_display_x + 104, Editor.ts_display_y + 76), (Editor.ts_display_x + 104, Editor.ts_display_y + 92)])

            pygame.draw.rect(wnd.display, (255, 255, 255), pygame.Rect(Editor.ts_display_x + 48, Editor.ts_display_y, 72, 72))
            c = Collision(self.collision_editor)
            if Collision(self.collision_editor) in Editor.collision_editor_draw:
                Editor.collision_editor_draw[c](wnd)
        if self.edited_world.starting_screen_id == self.edited_screen.screen_id:
            self.controller.player.x = self.edited_world.start_x
            self.controller.player.y = self.edited_world.start_y
            if self.editing_mode == 0:
                self.controller.player.draw(self.screen_seg)
            elif self.editing_mode == 1:
                self.controller.player.draw_as_hitbox(self.screen_seg, (0, 255, 0))

        scr_id_text = self.font.render("Screen id: {0}".format(self.edited_screen.screen_id), True, (255, 255, 255), 0)
        wnd.display.blit(scr_id_text, (1080, 320))
        dec_text = self.font.render("[-]", True, (255, 255, 255), 0)
        inc_text = self.font.render("[+]", True, (255, 255, 255), 0)
        e_tr = self.edited_screen.transitions[0]
        e_tr_text = self.font.render("East transition: {0}".format("solid" if e_tr == 0 else e_tr), True, (255, 255, 255), 0)
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
        # lc_text = self.font.render("({0}, {1})".format(self.last_click_x, self.last_click_y), True, (255, 255, 255), 0)
        # wnd.display.blit(lc_text, (1080, 420))

        mode_text = self.font.render("Mode:", True, (255, 255, 255), 0)
        wnd.display.blit(mode_text, (1440, 320))
        passive_color = (128, 128, 128)
        active_color = (255, 255, 255)
        terrain_text = self.font.render("Terrain", True, active_color if self.editing_mode == 0 else passive_color, 0)
        wnd.display.blit(terrain_text, (1500, 320))
        collision_text = self.font.render("Collision", True, active_color if self.editing_mode == 1 else passive_color, 0)
        wnd.display.blit(collision_text, (1500, 340))

        wscr_id_text = self.font.render("World starting screen: {0}".format(self.edited_world.starting_screen_id), True, (255, 255, 255), 0)
        wnd.display.blit(wscr_id_text, (1080, 500))
        use_curr_text = self.font.render("[Use current]", True, (255, 255, 255), 0)
        wnd.display.blit(use_curr_text, (1080, 520))

        if self.edited_world.starting_screen_id == self.edited_screen.screen_id:
            select_start_text = self.font.render("[Select start location]", True, (255, 255, 255), 0)
            wnd.display.blit(select_start_text, (1080, 540))

        if self.point_selection_callback is not None:
            selecting_text = self.font.render("Select point on map (right click to cancel)...", True, (0, 255, 0), 0)
            wnd.display.blit(selecting_text, (1080, 8))

        self.background.draw_to(160, 120, wnd.display, (1080, 640))

    @staticmethod
    def mousedown_callback(event, ml):
        self = Editor.instance
        self.mousedown(event, ml)

    def mousedown(self, event, ml):
        if event.button != 1 and event.button != 3:
            return
        self.last_click_x = event.pos[0]
        self.last_click_y = event.pos[1]
        if self.point_selection_callback is not None and event.button == 3:
            self.point_selection_callback = None
            return
        if event.pos[0] >= 1024 and event.button == 1:
            if self.editing_mode == 0:
                if mousebox(event.pos[0], event.pos[1], Editor.ts_display_x, Editor.ts_display_y, Editor.ts_view_w * Tileset.TILE_W, Editor.ts_view_h * Tileset.TILE_H):
                    tx = int((event.pos[0] - Editor.ts_display_x) / Tileset.TILE_W) + self.ts_view_x
                    ty = int((event.pos[1] - Editor.ts_display_y) / Tileset.TILE_H) + self.ts_view_y
                    if tx < self.tileset.tiles_w and ty < self.tileset.tiles_h:
                        self.ts_select_x = tx
                        self.ts_select_y = ty
            elif self.editing_mode == 1:
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
            if event.pos[0] >= 1500:
                if event.pos[1] >= 320:
                    if event.pos[1] < 340:
                        self.change_mode(0)
                    elif event.pos[1] < 360:
                        self.change_mode(1)
            if not self.locked[1]:
                if mousebox(event.pos[0], event.pos[1], 1080, 520, 100, 20):
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
                elif self.edited_world.starting_screen_id == self.edited_screen.screen_id and mousebox(event.pos[0], event.pos[1], 1080, 540, 180, 20):
                    self.locked[1] = True
                    self.point_selection_callback = self.set_start_coordinates
        elif event.pos[0] < 1024:
            if self.point_selection_callback is not None and event.button == 1:
                self.point_selection_callback(event.pos[0], event.pos[1])
                self.point_selection_callback = None
                return
            sctx = int(event.pos[0] / Tileset.TILE_W)
            scty = int(event.pos[1] / Tileset.TILE_H)
            tile = self.edited_screen.tiles[scty][sctx]
            if self.editing_mode == 0:
                if event.button == 1:
                    self.edited_screen.tiles[scty][sctx] = (self.ts_select_x, self.ts_select_y, tile[2])
                elif event.button == 3:
                    self.edited_screen.tiles[scty][sctx] = (0, 0, tile[2])
                self.edited_screen.dirty = True
            elif self.editing_mode == 1:
                if event.button == 1:
                    self.edited_screen.tiles[scty][sctx] = (tile[0], tile[1], self.collision_editor)
                elif event.button == 3:
                    self.edited_screen.tiles[scty][sctx] = (tile[0], tile[1], 0)
                self.edited_screen.dirty_collisions = True

    def set_start_coordinates(self, x, y):
        self.edited_world.start_x = x
        self.edited_world.start_y = y

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
        self.locked[event.button] = False

    @staticmethod
    def mousemotion_callback(event, ml):
        self = Editor.instance
        self.mousemotion(event, ml)

    def mousemotion(self, event, ml):
        if event.buttons[0]:
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
        if event.key == Editor.key_mapping["mode"]:
            self.change_mode(-1)

    def change_mode(self, which):
        if which == -1:
            which = (self.editing_mode + 1) % 2
        if which == self.editing_mode:
            return
        self.editing_mode = which
