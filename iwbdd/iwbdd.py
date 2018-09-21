from .pygame_oo.window import Window
from .pygame_oo.main_loop import MainLoop
from pygame.locals import *
from .tileset import pack_tilesets_from_files, read_tilesets
from .background import pack_backgrounds_from_files, read_backgrounds
from .spritesheet import pack_spritesheets_from_files, read_spritesheets
from .editor import Editor
import sys


def ml_exit_handler(event, ml):
    ml.break_main_loop()


def main():
    m = MainLoop()
    m.init()

    w = Window(1024, 768, "IWBDD")
    m.set_window(w)
    m.set_keydown_handler(K_ESCAPE, ml_exit_handler)
    m.start()

    m.quit()


def editor():
    m = MainLoop()
    m.init()
    if len(sys.argv) == 1:
        print("Missing argument: world file")
        sys.exit(2)

    w = Window(1600, 768, "IWBDD Editor")
    m.set_window(w)

    read_tilesets("tilesets.tls")
    read_backgrounds("backgrounds.bgs")
    read_spritesheets("spritesheets.sss")

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
