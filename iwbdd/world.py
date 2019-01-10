from .screen import eofc_read, Screen
from .tileset import Tileset
from .audio_data import Audio
from .bossfight import Bossfight, Boss
import struct


class World:
    def __init__(self, source=None):
        self.screens = {}
        self.tileset = None
        self.starting_screen_id = 0
        self.start_x = 0
        self.start_y = 0
        self.background_music = None
        self.bossfight_spec = None
        self.bossfight = None
        if source is not None:
            self.read_from(source)

    def change_tileset(self, ntsid):
        self.tileset = Tileset.find(ntsid)
        for sid, scr in self.screens.items():
            scr.dirty = True

    def start_simulation(self, ctrl):
        scr = self.screens[self.bossfight_spec[1]]
        self.bossfight = Bossfight(self, scr, ctrl)
        self.bossfight.attach_boss(Boss.available_bosses[self.bossfight_spec[0]](scr, self.bossfight_spec[2], self.bossfight_spec[3]))
        ctrl.bossfight = self.bossfight

    # Format: (HEADER, [SCREEN])
    # Header: (<4> Number of screens, <4> Tileset ID, <4> Starting screen ID, <1> Starting tile X, <1> Starting tile Y)
    # Screen: see screen.py
    def read_from(self, source, legacy=False):
        with open(source, 'rb') as f:
            if legacy:
                return self._read_from_v1(f)
            else:
                ver = struct.unpack("<H", eofc_read(f, 2))[0]
                if ver == 2:
                    return self._read_from_v2(f)
                elif ver == 3:
                    return self._read_from_v3(f)
                elif ver == 4:
                    return self._read_from_v4(f)

    def write_to(self, dest):
        with open(dest, 'wb') as f:
            f.write(struct.pack('<H', 4))
            f.write(struct.pack('<L', len(self.screens)))
            f.write(struct.pack('<L', self.tileset.tileset_id))
            f.write(struct.pack('<L', self.starting_screen_id))
            f.write(struct.pack('<H', self.start_x))
            f.write(struct.pack('<H', self.start_y))
            if self.bossfight_spec is None:
                f.write(struct.pack('<H', 0))
            else:
                bnbytes = self.bossfight_spec[0].encode('ascii')
                f.write(struct.pack('<H', len(bnbytes)))
                f.write(bnbytes)
                f.write(struct.pack('<H', self.bossfight_spec[1]))
                f.write(struct.pack('<H', self.bossfight_spec[2]))
                f.write(struct.pack('<H', self.bossfight_spec[3]))
            f.write(struct.pack('<H', len(self.background_music.audio_name)))
            f.write(self.background_music.audio_name.encode('ascii'))
            for scrn_id in self.screens:
                self.screens[scrn_id].write_tile_data(f)

    def _read_from_v1(self, f):
        screen_cnt = struct.unpack('<L', eofc_read(f, 4))[0]
        tileset_id = struct.unpack('<L', eofc_read(f, 4))[0]
        self.starting_screen_id = struct.unpack('<L', eofc_read(f, 4))[0]
        self.start_x = struct.unpack('B', eofc_read(f, 1))[0]
        self.start_y = struct.unpack('B', eofc_read(f, 1))[0]
        self.tileset = Tileset.find(tileset_id)
        self.background_music = None
        for i in range(screen_cnt):
            s = Screen(self, f)
            self.screens[s.screen_id] = s

    def _read_from_v2(self, f):
        screen_cnt = struct.unpack('<L', eofc_read(f, 4))[0]
        tileset_id = struct.unpack('<L', eofc_read(f, 4))[0]
        self.starting_screen_id = struct.unpack('<L', eofc_read(f, 4))[0]
        self.start_x = struct.unpack('<H', eofc_read(f, 2))[0]
        self.start_y = struct.unpack('<H', eofc_read(f, 2))[0]
        self.tileset = Tileset.find(tileset_id)
        self.background_music = None
        for i in range(screen_cnt):
            s = Screen(self, f)
            self.screens[s.screen_id] = s

    def _read_from_v3(self, f):
        screen_cnt = struct.unpack('<L', eofc_read(f, 4))[0]
        tileset_id = struct.unpack('<L', eofc_read(f, 4))[0]
        self.starting_screen_id = struct.unpack('<L', eofc_read(f, 4))[0]
        self.start_x = struct.unpack('<H', eofc_read(f, 2))[0]
        self.start_y = struct.unpack('<H', eofc_read(f, 2))[0]
        bgm_len = struct.unpack('<H', eofc_read(f, 2))[0]
        self.background_music = Audio.audio_by_name[eofc_read(f, bgm_len).decode('ascii')]
        self.tileset = Tileset.find(tileset_id)
        for i in range(screen_cnt):
            s = Screen(self, f)
            self.screens[s.screen_id] = s

    def _read_from_v4(self, f):
        screen_cnt = struct.unpack('<L', eofc_read(f, 4))[0]
        tileset_id = struct.unpack('<L', eofc_read(f, 4))[0]
        self.starting_screen_id = struct.unpack('<L', eofc_read(f, 4))[0]
        self.start_x = struct.unpack('<H', eofc_read(f, 2))[0]
        self.start_y = struct.unpack('<H', eofc_read(f, 2))[0]
        boss_cn_len = struct.unpack('<H', eofc_read(f, 2))[0]
        if boss_cn_len != 0:
            boss_cn = eofc_read(f, boss_cn_len).decode('ascii')
            boss_scrid = struct.unpack('<H', eofc_read(f, 2))[0]
            boss_x = struct.unpack('<H', eofc_read(f, 2))[0]
            boss_y = struct.unpack('<H', eofc_read(f, 2))[0]
            self.bossfight_spec = (boss_cn, boss_scrid, boss_x, boss_y)
        bgm_len = struct.unpack('<H', eofc_read(f, 2))[0]
        self.background_music = Audio.audio_by_name[eofc_read(f, bgm_len).decode('ascii')]
        self.tileset = Tileset.find(tileset_id)
        for i in range(screen_cnt):
            s = Screen(self, f)
            self.screens[s.screen_id] = s
