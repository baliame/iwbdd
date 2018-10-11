import os
from shutil import copyfile
from .pygame_oo.window import Window
from .pygame_oo.main_loop import MainLoop
from pygame.locals import *
from .tileset import pack_tilesets_from_files, read_tilesets
from .background import pack_backgrounds_from_files, read_backgrounds
from .spritesheet import pack_spritesheets_from_files, read_spritesheets
from .audio_data import pack_audio_from_files, read_audio
from .editor import Editor
from .object import Object
from . import object_importer
from .game import Controller
import time
import sys
import cProfile as profile


def ml_exit_handler(event, ml):
    ml.break_main_loop()


def main():
    m = MainLoop()
    m.init()
    Object.enumerate_objects(Object)
    w = Window(1008, 768, "IWBDD")
    m.set_window(w)
    m.set_keydown_handler(K_ESCAPE, ml_exit_handler)

    read_tilesets("tilesets.tls")
    read_backgrounds("backgrounds.bgs")
    read_spritesheets("spritesheets.sss")
    read_audio("audio.dat")

    c = Controller(m)
    c.load_world_from_file(sys.argv[1])
    c.create_player()
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


def editor():
    m = MainLoop()
    m.init()
    if len(sys.argv) == 1:
        print("Missing argument: world file")
        sys.exit(2)

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

    copyfile(sys.argv[1], "backups/{0}.{1}".format(sys.argv[1], time.strftime("%Y%m%d.%H%M%S")))

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


def world_tester():
    m = MainLoop()
    m.init()
    if len(sys.argv) == 1:
        print("Missing argument: world file")
        sys.exit(2)

    w = Window(1024, 768, "IWBDD World Test")
    m.set_window(w)

    read_tilesets("tilesets.tls")
    read_backgrounds("backgrounds.bgs")
    read_spritesheets("spritesheets.sss")
    read_audio("audio.dat")

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
