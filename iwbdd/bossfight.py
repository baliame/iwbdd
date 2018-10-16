from .object import Object
import copy
import pygame
from .audio_data import Audio
from random import choice


class BossfightObject(Object):
    exclude_from_object_editor = True
    saveable = False

    def activate_cutscene(self):
        pass

    def activate_fight(self):
        pass

    def deactivate(self):
        pass

    def cutscene_tick(self):
        pass

    def fight_tick(self):
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
                    obj.activate_fight()
        self.state = 2

    def skip_intro(self):
        if self.state == 1:
            self._start_fight()

    def tick(self):
        if self.state > 0:
            curr_call = pygame.time.get_ticks()
            if self.state == 1:
                self.ready_timer -= curr_call - self.last_call
                if self.ready_timer <= 0:
                    self._start_fight()
                self.boss.cutscene_tick()
            elif self.state == 2:
                self.boss.fight_tick()
                self.fight_cycle_timer = curr_call
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

    def __init__(self, screen, x=0, y=0, init_dict=None):
        super().__init__(screen, x, y, init_dict)
        self.phases = []
        self.phase_idx = 0
        self.health = 160

    def activate_fight(self):
        phc = self.phases.copy()
        phi = []
        for el in phc:
            phi.append(el(self))
        self.phases = phi

    def advance_phase(self):
        self.phase_idx += 1
        if self.phase_idx >= len(self.phases):
            self.phase_idx = len(self.phases) - 1
        self.phases[self.phase_idx].start_cycle()

    def on_damage(self):
        pass


class CycleElement:
    def __init__(self, phase):
        self.duration = 0
        self.phase = phase

    def start_cycle_element(self):
        pass

    def end_cycle_element(self):
        pass

    def on_tick(self):
        pass


class RandomCycleElement:
    def __init__(self, *args):
        self.elements = args

    def __call__(self, phase):
        return choice(self.elements)(phase)


class Phase:
    def __init__(self, boss):
        self.boss = boss
        self.cycle = []
        self.idx = 0
        self.next_cycle_element = 0

    def start_cycle(self):
        self.restart_cycle()
        self.start_new_cycle_element()

    def start_new_cycle_element(self):
        self.current_cycle[self.idx].start_cycle_element()
        self.next_cycle_element = self.current_cycle[self.idx].duration

    def on_tick(self):
        pass

    def end_current_cycle_element(self):
        self.current_cycle[self.idx].end_cycle_element()
        self.idx += 1
        if self.idx >= len(self.current_cycle):
            self.restart_cycle()

    def tick(self):
        self.on_tick()
        self.current_cycle[self.idx].on_tick()
        self.next_cycle_element -= 1
        if self.next_cycle_element <= 0:
            self.end_current_cycle_element()
            self.start_new_cycle_element()

    def restart_cycle(self):
        self.current_cycle = []
        for el in self.cycle:
            self.current_cycle.append(el(self))
        self.idx = 0
