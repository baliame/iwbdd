from .screen import eofc_read, Screen
from .tileset import Tileset
import struct


class World:
    def __init__(self, source=None):
        self.screens = {}
        self.tileset = None
        self.starting_screen_id = 0
        self.start_x = 0
        self.start_y = 0
        if source is not None:
            self.read_from(source)

    # Format: (HEADER, [SCREEN])
    # Header: (<4> Number of screens, <4> Tileset ID, <4> Starting screen ID, <1> Starting tile X, <1> Starting tile Y)
    # Screen: see screen.py
    def read_from(self, source):
        with open(source, 'rb') as f:
            screen_cnt = struct.unpack('<L', eofc_read(f, 4))[0]
            tileset_id = struct.unpack('<L', eofc_read(f, 4))[0]
            self.starting_screen_id = struct.unpack('<L', eofc_read(f, 4))[0]
            self.start_x = struct.unpack('B', eofc_read(f, 1))[0]
            self.start_y = struct.unpack('B', eofc_read(f, 1))[0]
            self.tileset = Tileset.find(tileset_id)
            for i in range(screen_cnt):
                s = Screen(self, f)
                self.screens[s.screen_id] = s

    def write_to(self, dest):
        with open(dest, 'wb') as f:
            f.write(struct.pack('<L', len(self.screens)))
            f.write(struct.pack('<L', self.tileset.tileset_id))
            f.write(struct.pack('<L', self.starting_screen_id))
            f.write(struct.pack('B', self.start_x))
            f.write(struct.pack('B', self.start_y))
            for scrn_id in self.screens:
                self.screens[scrn_id].write_tile_data(f)
