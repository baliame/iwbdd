import pygame
import glfw
from pygame.locals import *
from .window import WindowSection


class MainLoop:
    instance = None
    render_sync_stamp = 0

    def __init__(self):
        if MainLoop.instance is not None:
            raise RuntimeError("MainLoop must be a singleton.")
        MainLoop.instance = self
        self.was_init = False
        self.window = None
        self.suspend_ticking = False
        self.tickers = []
        self.updatables = []
        self.renderers = []
        self.atexit = []
        self.keydown_handlers = {}
        self.blanket_keydown_handler = None
        self.mouse_button_handler = None
        self.mouse_button_up_handler = None
        self.mouse_motion_handler = None
        self.prepare_exit = False
        MainLoop.render_sync_stamp = 0
        self.clock = pygame.time.Clock()

    def init(self):
        if self.was_init:
            raise RuntimeError("Duplicate initialization.")

        if not glfw.init():
            raise RuntimeError("GLFW initialization failed.")

        pygame.mixer.pre_init(44100, -16, 2, 512)
        init = [0, 0]

        if init[1] > 0:
            raise RuntimeError("{0} pygame modules failed to initialize.".format(init[1]))

        init_font = pygame.font.init()
        if init_font is not None:
            raise RuntimeError("Pygame font failed to initialize: {0}".format(init_font))

        MainLoop.render_sync_stamp = pygame.time.get_ticks() / 1000

        self.was_init = True

    def fps(self):
        return int(self.clock.get_fps())

    def break_main_loop(self):
        self.prepare_exit = True

    def quit(self):
        if not self.was_init:
            raise RuntimeError("Quit before initialization.")
        pygame.quit()

    def set_window(self, w):
        if self.window is not None:
            raise RuntimeError("Set multiple windows.")
        self.window = w
        self.updatables.append(w)
        w = w.get_parent()
        while w is not None:
            self.updatables.append(w)
            w = w.get_parent()

    def segment_window(self, x, y, w, h):
        if self.window is None:
            raise RuntimeError("No window set.")
        ret = WindowSection(self.window, x, y, w, h)
        self.updatables.insert(0, ret)
        return ret

    def add_render_callback(self, cb):
        self.renderers.append(cb)

    def add_ticker(self, cb):
        self.tickers.append(cb)

    def set_keydown_handler(self, key, cb):
        self.keydown_handlers[key] = cb

    def set_blanket_keydown_handler(self, cb):
        self.blanket_keydown_handler = cb

    def set_mouse_button_handler(self, cb):
        self.mouse_button_handler = cb

    def set_mouse_button_up_handler(self, cb):
        self.mouse_button_up_handler = cb

    def set_mouse_motion_handler(self, cb):
        self.mouse_motion_handler = cb

    def add_atexit_callback(self, cb):
        self.atexit.append(cb)

    def start(self):
        while True:
            self.clock.tick(60)
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.break_main_loop()
                elif event.type == KEYDOWN:
                    if self.blanket_keydown_handler is not None:
                        self.blanket_keydown_handler(event, self)
                    if event.key in self.keydown_handlers:
                        self.keydown_handlers[event.key](event, self)
                elif event.type == MOUSEBUTTONDOWN and self.mouse_button_handler is not None:
                    self.mouse_button_handler(self.window.scale_event(event), self)
                elif event.type == MOUSEBUTTONUP and self.mouse_button_up_handler is not None:
                    self.mouse_button_up_handler(self.window.scale_event(event), self)
                elif event.type == MOUSEMOTION and self.mouse_motion_handler is not None:
                    self.mouse_motion_handler(self.window.scale_event(event), self)
            if self.prepare_exit:
                for cb in self.atexit:
                    cb(self)
                break
            self.window.display.fill(0)
            MainLoop.render_sync_stamp = pygame.time.get_ticks() / 1000
            if not self.suspend_ticking:
                for ticker in self.tickers:
                    ticker(self)
            for renderer in self.renderers:
                renderer(self.window)
            for updatable in self.updatables:
                updatable.update()
