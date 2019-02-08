import os
from shutil import copyfile
from .pygame_oo.window import Window
from .pygame_oo.main_loop import MainLoop
from .pygame_oo.font import Font
from .tileset import pack_tilesets_from_files, read_tilesets
from .background import pack_backgrounds_from_files, read_backgrounds
from .spritesheet import pack_spritesheets_from_files, read_spritesheets
from .audio_data import pack_audio_from_files, read_audio
from .editor import Editor
from .object import Object
from .bossfight import Bossfight, Boss
from . import object_importer
from .game import Controller
from OpenGL.GL import *
import glfw
import time
import sys
import cProfile as profile
from .pygame_oo.game_shaders import GSH_init
import faulthandler

def ml_exit_handler(event, ml):
    ml.break_main_loop()


def opengl_tests_main():
    faulthandler.enable()
    m = MainLoop()
    m.init()
    w = Window(1008, 768, "IWBDD")
    Object.enumerate_objects(Object)
    Boss.enumerate_bosses()
    m.set_window(w)
    m.set_keydown_handler(glfw.KEY_ESCAPE, ml_exit_handler)
    GSH_init()
    read_tilesets("tilesets.tls")
    read_backgrounds("backgrounds.bgs")
    read_spritesheets("spritesheets.sss")
    read_audio("audio.dat")

    c = Controller(m)
    c.load_world_from_file(sys.argv[1])
    c.current_screen = c.current_world.screens[1]
    font = Font(w, 'arial.ttf')
    font.draw('test1', 'yup yup yup', 300, 75, (255, 0, 0, 255))
    font.draw('test2', 'maybe', 500, 300, (255, 255, 255, 255))
    font.draw('test3', 'yeah', 200, 200, (0, 0, 255, 255))
    while glfw.get_key(w.glw, glfw.KEY_ESCAPE) != glfw.PRESS:
        w.use_full_viewport()
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        w.fbo.new_render_pass(True)
        with w.fbo as fbo:
            w.use_game_viewport()
            c.current_screen.render_to_window(w)
            w.use_full_viewport()
            font.render(fbo)
        w.fbo.blit_to_window()
        glfw.swap_buffers(w.glw)
        #time.sleep(0.02)
        time.sleep(1)
    m.quit()


def main():
    m = MainLoop()
    m.init()
    Object.enumerate_objects(Object)
    Boss.enumerate_bosses()
    w = Window(1008, 768, "IWBDD")
    m.set_window(w)
    m.set_keydown_handler(glfw.KEY_ESCAPE, ml_exit_handler)

    read_tilesets("tilesets.tls")
    read_backgrounds("backgrounds.bgs")
    read_spritesheets("spritesheets.sss")
    read_audio("audio.dat")

    c = Controller(m)
    c.load_world_from_file(sys.argv[1])
    c.create_player()
    c.start_world()
    c.check_save_file()
    c.use_as_main_renderer()
    c.use_as_main_keyhandler()

    m.start()

    m.quit()


def profiled():
    pr = profile.Profile()
    pr.enable()
    pr.runcall(main)
    # pr.dump_stats('prof.out')
    pr.print_stats('cumulative')


def profiled_boss():
    pr = profile.Profile()
    pr.enable()
    pr.runcall(boss_tester)
    # pr.dump_stats('prof.out')
    pr.print_stats('cumulative')


def editor():
    m = MainLoop()
    m.init()
    if len(sys.argv) == 1:
        print("Missing argument: world file")
        sys.exit(2)

    Object.enumerate_objects(Object)
    Boss.enumerate_bosses()
    w = Window(1600, 768, "IWBDD Editor")
    m.set_window(w)

    read_tilesets("tilesets.tls")
    read_backgrounds("backgrounds.bgs")
    read_spritesheets("spritesheets.sss")
    read_audio("audio.dat")

    try:
        os.mkdir("backups")
    except FileExistsError:
        pass

    try:
        copyfile(sys.argv[1], "backups/{0}.{1}".format(sys.argv[1], time.strftime("%Y%m%d.%H%M%S")))
    except FileNotFoundError:
        pass

    ed = Editor(sys.argv[1], m)
    m.set_keydown_handler(K_ESCAPE, ml_exit_handler)
    m.start()

    m.quit()

def editor_w2():
    m = MainLoop()
    m.init()

    Object.enumerate_objects(Object)
    w = Window(1600, 768, "IWBDD Editor")
    m.set_window(w)

    read_tilesets("tilesets.tls")
    read_backgrounds("backgrounds.bgs")
    read_spritesheets("spritesheets.sss")
    read_audio("audio.dat")

    try:
        os.mkdir("backups")
    except FileExistsError:
        pass

    ed = Editor("world2.wld", m)
    m.set_keydown_handler(K_ESCAPE, ml_exit_handler)
    m.start()

    m.quit()

def editor_scaled():
    m = MainLoop()
    m.init()
    if len(sys.argv) == 1:
        print("Missing argument: world file")
        sys.exit(2)

    Object.enumerate_objects(Object)
    w = Window(1200, 576, "IWBDD Editor")
    scaler = w.create_scaler(1600, 768)
    m.set_window(scaler)

    read_tilesets("tilesets.tls")
    read_backgrounds("backgrounds.bgs")
    read_spritesheets("spritesheets.sss")
    read_audio("audio.dat")

    ed = Editor(sys.argv[1], m)
    m.set_keydown_handler(K_ESCAPE, ml_exit_handler)
    m.start()

    m.quit()


def boss_tester():
    m = MainLoop()
    m.init()
    Object.enumerate_objects(Object)
    if len(sys.argv) == 1:
        print("Missing argument: world file")
        sys.exit(2)
    cl = None
    for item in Boss.__subclasses__():
        if item.__name__ == sys.argv[1]:
            cl = item
            break
    if cl is None:
        print("Unknown class: ", sys.argv[1])
        sys.exit(2)

    w = Window(1008, 768, "IWBDD Boss Test")
    m.set_window(w)

    read_tilesets("tilesets.tls")
    read_backgrounds("backgrounds.bgs")
    read_spritesheets("spritesheets.sss")
    read_audio("audio.dat")

    c = Controller(m)
    c.load_world_from_file("boss_test_world.wld")
    c.create_player()
    c.use_as_main_renderer()
    c.use_as_main_keyhandler()
    c.start_world()
    c.bossfight = Bossfight(c.current_world, c.current_screen, c)
    c.current_world.bossfight = c.bossfight
    c.bossfight.attach_boss(cl(c.current_screen, 800, 384))
    c.bossfight.dev_mode = True
    # c.also_render_objects = True
    # c.render_collisions = True

    m.set_keydown_handler(K_ESCAPE, ml_exit_handler)
    m.start()

    m.quit()


def world_tester():
    m = MainLoop()
    m.init()
    Object.enumerate_objects(Object)

    if len(sys.argv) == 1:
        print("Missing argument: boss class")
        sys.exit(2)

    w = Window(1008, 768, "IWBDD World Test")
    m.set_window(w)

    read_tilesets("tilesets.tls")
    read_backgrounds("backgrounds.bgs")
    read_spritesheets("spritesheets.sss")
    read_audio("audio.dat")

    c = Controller(m)
    c.load_world_from_file(sys.argv[1])
    c.create_player()
    c.use_as_main_renderer()
    c.use_as_main_keyhandler()

    m.set_keydown_handler(K_ESCAPE, ml_exit_handler)
    m.start()

    m.quit()


def pack_tilesets():
    m = MainLoop()
    m.init()
    if len(sys.argv) == 1:
        print("Missing arguments: destination, source files")
        sys.exit(2)
    if len(sys.argv) == 2:
        print("Missing arguments: source files")
        sys.exit(2)
    destfile = sys.argv[1]
    id_cntr = 1
    srcfiles = {}
    for elem in sys.argv[2:]:
        srcfiles[id_cntr] = elem
        id_cntr += 1
    pack_tilesets_from_files(srcfiles, destfile)
    m.quit()


def pack_backgrounds():
    m = MainLoop()
    m.init()
    if len(sys.argv) == 1:
        print("Missing arguments: destination, source files")
        sys.exit(2)
    if len(sys.argv) == 2:
        print("Missing arguments: source files")
        sys.exit(2)
    destfile = sys.argv[1]
    id_cntr = 1
    srcfiles = {}
    for elem in sys.argv[2:]:
        srcfiles[id_cntr] = elem
        id_cntr += 1
    pack_backgrounds_from_files(srcfiles, destfile)
    m.quit()


def pack_spritesheets():
    m = MainLoop()
    m.init()
    if len(sys.argv) == 1:
        print("Missing arguments: destination, source files")
        sys.exit(2)
    if len(sys.argv) == 2:
        print("Missing arguments: source files")
        sys.exit(2)
    destfile = sys.argv[1]
    id_cntr = 1
    srcfiles = {}
    for elem in sys.argv[2:]:
        srcfiles[id_cntr] = elem
        id_cntr += 1
    pack_spritesheets_from_files(srcfiles, destfile)
    m.quit()


def pack_audio():
    m = MainLoop()
    m.init()
    if len(sys.argv) == 1:
        print("Missing arguments: destination, source files")
        sys.exit(2)
    if len(sys.argv) == 2:
        print("Missing arguments: source files")
        sys.exit(2)
    destfile = sys.argv[1]
    pack_audio_from_files(sys.argv[2:], destfile)
    m.quit()
