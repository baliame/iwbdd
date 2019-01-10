from .common import CollisionTest
from .object import Object, ExplosionEffect, generate_rectangle_hitbox
from .spritesheet import Spritesheet
import copy
import pygame
from .audio_data import Audio
from random import choice, randint
from collections import OrderedDict


class BossfightObject(Object):
    exclude_from_object_editor = True
    saveable = False
    destroy_as_annoyance = False

    def __init__(self, screen, x=0, y=0, init_dict=None):
        super().__init__(screen, x, y, init_dict)

    def create(self, cyc):
        self.screen.objects.append(self)
        self.cycle_el = cyc

    def cleanup(self):
        if self in self.screen.objects:
            self.screen.objects.remove(self)

    def activate_cutscene(self):
        pass

    def activate_fight(self):
        pass

    def deactivate(self):
        pass

    def cutscene_tick(self, diff):
        pass

    def fight_tick(self):
        pass


class Barrier(BossfightObject):
    exclude_from_object_editor = False
    saveable = True
    object_name = "Barrier (activated on boss fight trigger)"
    editor_frame_size = (26, 146)

    def __init__(self, screen, x=0, y=0, init_dict=None):
        super().__init__(screen, x, y, init_dict)
        self.hidden = True
        self.hitbox = generate_rectangle_hitbox(24, 144)
        self.hitbox_type = CollisionTest.SOLID
        self.spritesheet = Spritesheet.spritesheets_byname['ss_boss_barrier-24-144.png']
        self.states = {
            "default": (True, 0.1, [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0)], True),
        }
        self.state = "default"

    def activate_cutscene(self):
        self.hidden = False
        self.screen.objects_dirty = True

    def deactivate(self):
        self.hidden = True
        self.screen.objects_dirty = True


class Bossfight:
    def __init__(self, world, screen, ctrl):
        self.boss = None
        self.screen = screen
        self.world = world
        self.ctrl = ctrl

        self.triggered = False
        self.pre_start_frames = 18
        self.state = 0
        self.last_call = 0
        self.ready_timer = 0
        self.boss_channel_num = 0

        self.dev_mode = False

        self.font = pygame.font.SysFont('Courier New', 12)
        ctrl.ml.add_render_callback(self.dev_render)

    def skip(self):
        if self.state == 1:
            self.ready_timer = 1
            self.ctrl.boss_channels[0].stop()
            self.ctrl.boss_channels[1].stop()

    def dev_render(self, wnd):
        if self.dev_mode and self.state > 0:
            p = self.boss.phases[self.boss.phase_idx]
            draw_color = (0, 0, 0)
            wnd.display.blit(self.font.render(p.__class__.phase_name, True, draw_color, 0), (0, 0))
            if self.state > 1:
                c_n = p.current_cycle[p.idx].__class__.cycle_el_name
                n_c = p.next_cycle_element
                wnd.display.blit(self.font.render("{0} [{1}]".format(c_n, n_c), True, draw_color, 0), (0, 16))
                wnd.display.blit(self.font.render("{0}/{1}".format(self.boss.health, self.boss.initial_health), True, draw_color, 0), (0, 32))

    def attach_boss(self, boss):
        self.boss_template = boss
        self.boss = copy.copy(boss)

    def reset(self):
        if self.boss in self.screen.objects:
            self.screen.objects.remove(self.boss)
        self.boss = copy.copy(self.boss_template)
        self.last_call = 0
        self.ready_timer = 0
        self.state = 0
        self.triggered = False
        self.pre_start_frames = 18

    def start(self):
        if self.screen is not None:
            self.screen.objects.append(self.boss)
            for obj in self.screen.objects.copy():
                if isinstance(obj, BossfightObject):
                    obj.activate_cutscene()
        self.ctrl.music(self.boss.intro_music)
        self.state = 1
        self.last_call = pygame.time.get_ticks()

    def _start_fight(self):
        if self.screen is not None:
            for obj in self.screen.objects.copy():
                if isinstance(obj, BossfightObject):
                    obj.activate_fight()
        self.ctrl.music(self.boss.boss_music)
        self.state = 2

    def skip_intro(self):
        if self.state == 1:
            self._start_fight()

    def tick(self):
        if self.triggered and self.pre_start_frames > 0:
            self.pre_start_frames -= 1
            if self.pre_start_frames == 0:
                self.start()
            return
        if self.state > 0:
            curr_call = pygame.time.get_ticks()
            if self.state == 1:
                self.ready_timer -= curr_call - self.last_call
                if self.ready_timer <= 0:
                    self._start_fight()
                self.boss.cutscene_tick(curr_call - self.last_call)
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

    def destroy_mechanics(self):
        for obj in self.screen.objects.copy():
            if isinstance(obj, BossfightObject):
                if obj.__class__.destroy_as_annoyance:
                    obj.cleanup()

    def boss_dead(self):
        for obj in self.screen.objects.copy():
            if isinstance(obj, BossfightObject):
                obj.deactivate()


class Boss(BossfightObject):
    exclude_from_object_editor = True
    saveable = False
    available_bosses = OrderedDict({})

    @classmethod
    def enumerate_bosses(cls):
        for o in cls.__subclasses__():
            cls.available_bosses[o.__name__] = o

    def __init__(self, screen, x=0, y=0, init_dict=None):
        super().__init__(screen, x, y, init_dict)
        self.phases = []
        self.phase_idx = 0
        self.health = 160
        self.intro_music = None
        self.boss_music = None
        self.fight_controller = screen.world.bossfight
        self.invulnerable = False
        self.dead = False
        self.death_frames = 0

    def on_end_cycle_element(self):
        pass

    def activate_cutscene(self):
        phc = self.phases.copy()
        phi = []
        for el in phc:
            phi.append(el(self))
        self.phases = phi
        self.phase_idx = 0

    def activate_fight(self):
        self.phases[0].start_cycle()

    def advance_phase(self):
        self.phase_idx += 1
        if self.phase_idx >= len(self.phases):
            self.phase_idx = len(self.phases) - 1
        self.phases[self.phase_idx].start_cycle()

    def on_damage(self):
        pass

    def create_explosion_on_self(self):
        dxmin = -24
        dxmax = len(self.hitbox) - 24
        dymin = -24
        dymax = len(self.hitbox[0]) - 24
        e = ExplosionEffect(self.screen, self.x + randint(dxmin, dxmax), self.y + randint(dymin, dymax))
        e.start(self.fight_controller.ctrl)

    def fight_tick(self):
        if self.dead:
            if self.death_frames > 0:
                self.death_frames -= 1
                if self.death_frames % 5 == 0:
                    self.create_explosion_on_self()
                if self.death_frames <= 0:
                    self.fight_controller.ctrl.music(self.fight_controller.ctrl.current_world.background_music)
                    self.fight_controller.boss_dead()
                    self.hidden = True
            return
        self.phases[self.phase_idx].tick()

    def interact(self, ctrl):
        if self.dead:
            return
        if self.fight_controller is not None and self.fight_controller.state >= 2:
            ctrl.source_bullet.cleanup_self()
            ctrl.ambience("hit.ogg")
            if not self.invulnerable:
                self.health -= 1
                if self.health <= 0:
                    self.die()

    def die(self):
        if not self.dead:
            self.hitbox_type = CollisionTest.PASSABLE
            self.dead = True
            self.death_frames = 600
            self.fight_controller.destroy_mechanics()
            self.fight_controller.ctrl.music(None)


class CycleElement:
    cycle_el_name = "Unknown move"

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
    phase_name = "Unknown phase"

    def __init__(self, boss):
        self.boss = boss
        self.cycle = []
        self.current_cycle = []
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
        self.boss.on_end_cycle_element()
        self.idx += 1
        if self.idx >= len(self.current_cycle):
            self.restart_cycle()

    def tick(self):
        self.on_tick()
        self.current_cycle[self.idx].on_tick()
        self.next_cycle_element -= 1
        if self.next_cycle_element <= 0:
            self.end_current_cycle_element()
            if self == self.boss.phases[self.boss.phase_idx]:
                self.start_new_cycle_element()

    def restart_cycle(self):
        self.current_cycle = []
        for el in self.cycle:
            self.current_cycle.append(el(self))
        self.idx = 0
