from pygame import mixer
import glfw
from .window import WindowSection
import time
from OpenGL.GL import *


class poevent:
    @classmethod
    def keydown(cls, key, scancode, mods):
        ret = cls()
        ret.key = key
        ret.scancode = scancode
        return ret

    @classmethod
    def motion(cls, x, y, buttons):
        ret = cls()
        ret.pos = [x, y]
        ret.buttons = buttons[:]
        return ret

    @classmethod
    def button(cls, x, y, button, action, mods):
        ret = cls()
        ret.pos = [x, y]
        if button == glfw.MOUSE_BUTTON_LEFT:
            ret.button = 1
        elif button == glfw.MOUSE_BUTTON_MIDDLE:
            ret.button = 2
        elif button == glfw.MOUSE_BUTTON_RIGHT:
            ret.button = 3
        elif button == glfw.MOUSE_BUTTON_4:
            ret.button = 4
        elif button == glfw.MOUSE_BUTTON_5:
            ret.button = 5
        elif button == glfw.MOUSE_BUTTON_6:
            ret.button = 6
        elif button == glfw.MOUSE_BUTTON_7:
            ret.button = 7
        elif button == glfw.MOUSE_BUTTON_8:
            ret.button = 8
        return ret


class MainLoop:
    instance = None
    render_sync_stamp = 0

    def __init__(self):
        if MainLoop.instance is not None:
            raise RuntimeError("MainLoop must be a singleton.")
        MainLoop.instance = self
        self.was_init = False
        self.window = None
        self.top_window = None
        self.suspend_ticking = False
        self.tickers = []
        self.updatables = []
        self.renderers = []
        self.prerenderers = []
        self.atexit = []
        self.keydown_handlers = {}
        self.blanket_keydown_handler = None
        self.mouse_button_handler = None
        self.mouse_button_up_handler = None
        self.mouse_motion_handler = None
        self.prepare_exit = False
        self.measured_fps = 0
        MainLoop.render_sync_stamp = 0
        self.mouse_buttons = [0, 0, 0, 0, 0, 0, 0, 0]

    def init(self):
        if self.was_init:
            raise RuntimeError("Duplicate initialization.")

        if not glfw.init():
            raise RuntimeError("GLFW initialization failed.")

        mixer.init(44100, -16, 2, 512)

        MainLoop.render_sync_stamp = glfw.get_time()

        self.was_init = True

    def fps(self):
        return self.measured_fps

    def break_main_loop(self):
        self.prepare_exit = True

    def quit(self):
        if not self.was_init:
            raise RuntimeError("Quit before initialization.")
        mixer.quit()

    def set_window(self, w):
        if self.window is not None:
            raise RuntimeError("Set multiple windows.")
        self.window = w
        self.updatables.append(w)
        v = w
        w = w.get_parent()
        while w is not None:
            v = w
            self.updatables.append(w)
            w = w.get_parent()
        self.top_window = v
        glfw.set_key_callback(v.glw, self.handle_key)
        glfw.set_cursor_pos_callback(v.glw, self.handle_motion)
        glfw.set_mouse_button_callback(v.glw, self.handle_button)

    def segment_window(self, x, y, w, h):
        if self.window is None:
            raise RuntimeError("No window set.")
        ret = WindowSection(self.window, x, y, w, h)
        self.updatables.insert(0, ret)
        return ret

    def add_render_callback(self, cb):
        self.renderers.append(cb)

    def add_pre_render_callback(self, cb):
        self.prerenderers.append(cb)

    def add_ticker(self, cb):
        self.tickers.append(cb)

    def set_keydown_handler(self, key, cb):
        self.keydown_handlers[key] = cb

    def set_blanket_keydown_handler(self, cb):
        self.blanket_keydown_handler = cb

    def handle_key(self, wnd, key, scancode, action, mods):
        if action == glfw.PRESS:
            event = poevent.keydown(key, scancode, mods)
            if self.blanket_keydown_handler is not None:
                self.blanket_keydown_handler(event, self)
            if event.key in self.keydown_handlers:
                self.keydown_handlers[event.key](event, self)

    def set_mouse_button_handler(self, cb):
        self.mouse_button_handler = cb

    def set_mouse_button_up_handler(self, cb):
        self.mouse_button_up_handler = cb

    def handle_button(self, wnd, button, action, mods):
        if action == glfw.PRESS:
            val = 1
            cb = self.mouse_button_handler
        elif action == glfw.RELEASE:
            val = 0
            cb = self.mouse_button_up_handler
        else:
            return

        if button == glfw.MOUSE_BUTTON_LEFT:
            self.mouse_buttons[0] = val
        elif button == glfw.MOUSE_BUTTON_MIDDLE:
            self.mouse_buttons[1] = val
        elif button == glfw.MOUSE_BUTTON_RIGHT:
            self.mouse_buttons[2] = val

        x, y = glfw.get_cursor_pos(wnd)
        event = poevent.button(x, y, button, action, mods)

        if cb is not None:
            cb(event, self)

    def set_mouse_motion_handler(self, cb):
        self.mouse_motion_handler = cb

    def handle_motion(self, wnd, x, y):
        if self.mouse_motion_handler is not None:
            event = poevent.motion(x, y, self.mouse_buttons)
            self.mouse_motion_handler(event, self)

    def add_atexit_callback(self, cb):
        self.atexit.append(cb)

    def get_key(self, key_const):
        return glfw.get_key(self.top_window.glw, key_const)

    def start(self):
        spf = 1.0 / 60.0
        last_time = glfw.get_time()
        last_int = int(last_time)
        temp_fps = 0
        self.measured_fps = 0
        while not glfw.window_should_close(self.top_window.glw) and not self.prepare_exit:
            glfw.poll_events()
            MainLoop.render_sync_stamp = glfw.get_time()
            if not self.suspend_ticking:
                for ticker in self.tickers:
                    ticker(self)
            for prerenderer in self.prerenderers:
                prerenderer(self.window)
            for renderer in self.renderers:
                renderer(self.window)
            # for updatable in self.updatables:
            #     updatable.update()
            temp_fps += 1
            while glfw.get_time() < last_time + spf:
                time.sleep(0.001)
            last_time += spf
            curr_time = glfw.get_time()
            if int(curr_time) > last_int:
                last_int = int(curr_time)
                self.measured_fps = temp_fps
                temp_fps = 0
        for cb in self.atexit:
            cb(self)
