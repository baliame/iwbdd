from .object import Object
import copy
import pygame
from .audio_data import Audio


class BossfightObject(Object):
    exclude_from_object_editor = True
    saveable = False

    def activate_cutscene(self):
        pass

    def activate_fight(self):
        pass

    def deactivate(self):
        pass


class Bossfight:
    def __init__(self, world, screen, ctrl):
        self.boss = None
        self.screen = screen
        self.world = world
        self.ctrl = ctrl

        self.state = 0
        self.last_call = 0
        self.ready_timer = 0
        self.boss_channel_num = 0

    def attach_boss(self, boss):
        self.boss_template = boss
        self.boss = copy.copy(boss)

    def reset(self):
        self.boss = copy.copy(self.boss_template)
        self.last_call = 0
        self.ready_timer = 0
        self.state = 0

    def start(self):
        if self.screen is not None:
            for obj in self.screen.objects:
                if isinstance(obj, BossfightObject):
                    obj.activate_cutscene()
        if self.ctrl is not None:
            self.ctrl.bossfight = self
        self.state = 1
        self.last_call = pygame.time.get_ticks()

    def _start_fight(self):
        if self.screen is not None:
            for obj in self.screen.objects:
                if isinstance(obj, BossfightObject):
                    obj.activate_cutscene()
        if self.ctrl is not None:
            self.ctrl.bossfight = self
        self.state = 1

    def tick(self):
        if self.state > 0:
            curr_call = pygame.time.get_ticks()
            if self.state == 1:
                self.ready_timer -= curr_call - self.last_call
                if self.ready_timer <= 0:
                    self._start_fight()
            self.last_call = curr_call

    def need_ready(self, t):
        self.ready_timer = self.ready_timer if t < self.ready_timer else t

    def boss_audio(self, name):
        chan = self.ctrl.boss_channels[self.boss_channel_num]
        self.boss_channel_num = (self.boss_channel_num + 1) % len(self.ctrl.boss_channels)
        Audio.play_by_name(name, channel=chan)

    def ambient_audio(self, name):
        Audio.play_by_name(name)


class Boss(BossfightObject):
    exclude_from_object_editor = True
    saveable = False


class TTSBoss(Boss):
    def __init__(self, screen, x=0, y=0, init_dict=None):
        super().__init__(screen, x, y, init_dict)
        self.fight_controller = screen.world.bossfight

    def activate_cutscene(self):
        self.fight_controller.boss_audio("donation.ogg")
        self.fight_controller.need_ready(9000)
