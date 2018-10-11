from .common import eofc_read
import struct
import pygame
import tempfile
import os.path
# from io import BytesIO


# DATA FORMAT: (HEADER, [AUDIO])
# HEADER: (<4> Number of audio files)
# AUDIO: (<2> Original audio name length, <LEN> Name, <4> Audio data byte length, <LEN> Raw data)
def read_audio(source):
    with open(source, 'rb') as f:
        audio_cnt = struct.unpack('<L', eofc_read(f, 4))[0]
        for i in range(audio_cnt):
            t = Audio(f)
            Audio.audio_by_name[t.audio_name] = t


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
    audio_temp_dir = None

    @classmethod
    def play_by_name(cls, name, channel=None, loops=0):
        if channel is None:
            channel = pygame.mixer.find_channel()
        if channel is not None:
            channel.play(cls.audio_by_name[name].sound, loops=loops)
        else:
            print("No channel.")

    @staticmethod
    def cleanup_temp():
        if Audio.audio_temp_dir is not None:
            Audio.audio_temp_dir.cleanup()
            Audio.audio_temp_dir = None

    def __init__(self, reader=None):
        self.audio_name = ""
        self.sound = None
        if Audio.audio_temp_dir is None:
            Audio.audio_temp_dir = tempfile.TemporaryDirectory()
            pygame.register_quit(Audio.cleanup_temp)
        if reader is not None:
            self.read_audio_data(reader)

    def read_audio_data(self, reader):
        audio_name_len = struct.unpack('<H', eofc_read(reader, 2))[0]
        self.audio_name = eofc_read(reader, audio_name_len).decode('ascii')
        data_len = struct.unpack('<L', eofc_read(reader, 4))[0]
        raw_data = eofc_read(reader, data_len)
        temp_aud = os.path.join(Audio.audio_temp_dir.name, self.audio_name)
        with open(temp_aud, 'wb') as f:
            f.write(raw_data)
        # self.sound = pygame.mixer.Sound(buffer=raw_data)
        self.sound = pygame.mixer.Sound(file=temp_aud)
        self.sound.set_volume(0.3)

    def play(self, channel=None, loops=0):
        if channel is None:
            channel = pygame.mixer.find_channel()
        if channel is not None:
            channel.play(self.sound, loops=loops)
