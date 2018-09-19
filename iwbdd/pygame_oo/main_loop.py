import pygame
from pygame.locals import *
from .window import WindowSection
import time


render_sync_stamp = 0


class MainLoop:
    instance = None

    def __init__(self):
        if MainLoop.instance is not None:
            raise RuntimeError("MainLoop must be a singleton.")
        MainLoop.instance = self
        self.was_init = False
        self.window = None
        self.updatables = []
        self.renderers = []
        self.atexit = []
        self.keydown_handlers = {}
        self.mouse_button_handler = None
        self.mouse_button_up_handler = None
        self.mouse_motion_handler = None
        self.prepare_exit = False
        self.render_sync_stamp = time.time()

    def init(self):
        if self.was_init:
            raise RuntimeError("Duplicate initialization.")

        init = pygame.init()
        if init[1] > 0:
            raise RuntimeError("{0} pygame modules failed to initialize.".format(init[1]))

        init_font = pygame.font.init()
        if init_font is not None:
            raise RuntimeError("Pygame font failed to initialize: {0}".format(init_font))

        self.was_init = True

    def break_main_loop(self):
        self.prepare_exit = True

    def quit(self):
        if not self.was_init:
            raise RuntimeError("Quit before initialization.")
        pygame.quit()
        quit()

    def set_window(self, w):
        if self.window is not None:
            raise RuntimeError("Set multiple windows.")
        self.window = w
        self.updatables.append(w)

    def segment_window(self, x, y, w, h):
        if self.window is None:
            raise RuntimeError("No window set.")
        ret = WindowSection(self.window, x, y, w, h)
        self.updatables.insert(0, ret)
        return ret

    def add_render_callback(self, cb):
        self.renderers.append(cb)

    def set_keydown_handler(self, key, cb):
        self.keydown_handlers[key] = cb

    def set_mouse_button_handler(self, cb):
        self.mouse_button_handler = cb

    def set_mouse_button_up_handler(self, cb):
        self.mouse_button_up_handler = cb

    def set_mouse_motion_handler(self, cb):
        self.mouse_motion_handler = cb

    def add_atexit_callback(self, cb):
        self.atexit.append(cb)

    def start(self):
        global render_sync_stamp
        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.break_main_loop()
                elif event.type == KEYDOWN:
                    if event.key in self.keydown_handlers:
                        self.keydown_handlers[event.key](event, self)
                elif event.type == MOUSEBUTTONDOWN and self.mouse_button_handler is not None:
                    self.mouse_button_handler(event, self)
                elif event.type == MOUSEBUTTONUP and self.mouse_button_up_handler is not None:
                    self.mouse_button_up_handler(event, self)
                elif event.type == MOUSEMOTION and self.mouse_motion_handler is not None:
                    self.mouse_motion_handler(event, self)
            if self.prepare_exit:
                for cb in self.atexit:
                    cb(self)
                break
            self.window.display.fill(0)
            render_sync_stamp = time.time()
            for renderer in self.renderers:
                renderer(self.window)
            for updatable in self.updatables:
                updatable.update()
