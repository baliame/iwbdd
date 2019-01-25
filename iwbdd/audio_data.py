from .common import eofc_read
import struct
from pygame import mixer
import tempfile
import os.path
from io import BytesIO


# DATA FORMAT: (HEADER, [AUDIO])
# HEADER: (<4> Number of audio files)
# AUDIO: (<2> Original audio name length, <LEN> Name, <4> Audio data byte length, <LEN> Raw data)
def read_audio(source):
    with open(source, 'rb') as f:
        audio_cnt = struct.unpack('<L', eofc_read(f, 4))[0]
        for i in range(audio_cnt):
            t = Audio(f)
            Audio.audio_by_name[t.audio_name] = t
    Audio.pre_equalizer()


def pack_audio_from_files(files, dest):
    with open(dest, 'wb') as d:
        d.write(struct.pack('<L', len(files)))
        for fn in files:
            d.write(struct.pack('<H', len(fn)))
            d.write(fn.encode('ascii'))
            with open(fn, 'rb') as f:
                data = f.read()
                d.write(struct.pack('<L', len(data)))
                d.write(data)


class Audio:
    audio_by_name = {}
    # audio_temp_dir = None

    @classmethod
    def pre_equalizer(cls):
        Audio.audio_by_name["opening_curly_bracket.ogg"].sound.set_volume(0.6)
        Audio.audio_by_name["opening_curly_bracket_2.ogg"].sound.set_volume(0.6)
        Audio.audio_by_name["opening_square_bracket.ogg"].sound.set_volume(0.6)
        Audio.audio_by_name["opening_square_bracket_2.ogg"].sound.set_volume(0.6)
        Audio.audio_by_name["opening_parentheses.ogg"].sound.set_volume(0.6)
        Audio.audio_by_name["opening_parentheses_2.ogg"].sound.set_volume(0.6)
        Audio.audio_by_name["closing_curly_bracket.ogg"].sound.set_volume(0.6)
        Audio.audio_by_name["closing_curly_bracket_2.ogg"].sound.set_volume(0.6)
        Audio.audio_by_name["closing_square_bracket.ogg"].sound.set_volume(0.6)
        Audio.audio_by_name["closing_square_bracket_2.ogg"].sound.set_volume(0.6)
        Audio.audio_by_name["closing_parentheses.ogg"].sound.set_volume(0.6)
        Audio.audio_by_name["closing_parentheses_2.ogg"].sound.set_volume(0.6)
        Audio.audio_by_name["at.ogg"].sound.set_volume(0.6)
        Audio.audio_by_name["ats_27.ogg"].sound.set_volume(0.6)
        Audio.audio_by_name["ats_64.ogg"].sound.set_volume(0.6)
        Audio.audio_by_name["prepare_to_die.ogg"].sound.set_volume(0.6)
        Audio.audio_by_name["prepare_to_die_2.ogg"].sound.set_volume(0.6)
        Audio.audio_by_name['distant_thunder.ogg'].sound.set_volume(0.5)
        Audio.audio_by_name['quack.ogg'].sound.set_volume(0.1)
        Audio.audio_by_name['quack2.ogg'].sound.set_volume(0.1)
        Audio.audio_by_name['omen.ogg'].sound.set_volume(0.2)
        Audio.audio_by_name['donation.ogg'].sound.set_volume(0.6)
        Audio.audio_by_name['bits.ogg'].sound.set_volume(0.5)
        Audio.audio_by_name['hit.ogg'].sound.set_volume(0.2)
        Audio.audio_by_name['explosion.ogg'].sound.set_volume(0.5)

    @classmethod
    def play_by_name(cls, name, channel=None, loops=0):
        if name not in cls.audio_by_name:
            print("Audio missing: {0}".format(name))
            return
        if channel is None:
            channel = mixer.find_channel()
        if channel is not None:
            channel.play(cls.audio_by_name[name].sound, loops=loops)

    def __init__(self, reader=None):
        self.audio_name = ""
        self.sound = None
        if reader is not None:
            self.read_audio_data(reader)

    def read_audio_data(self, reader):
        audio_name_len = struct.unpack('<H', eofc_read(reader, 2))[0]
        self.audio_name = eofc_read(reader, audio_name_len).decode('ascii')
        data_len = struct.unpack('<L', eofc_read(reader, 4))[0]
        raw_data = eofc_read(reader, data_len)
        temp_aud = BytesIO(raw_data)
        self.sound = mixer.Sound(file=temp_aud)

    def play(self, channel=None, loops=0):
        if channel is None:
            channel = mixer.find_channel()
        if channel is not None:
            channel.play(self.sound, loops=loops)
